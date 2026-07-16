# Deep Dive: Technical Decisions, Bugs, and Item Basket

This is the extended writeup behind the main [README](../README.md). It covers the reasoning behind the bigger decisions, a bug worth knowing about, and how the item basket was put together.

## Technical decisions

**Listing-grain data, not item-grain.**
Blizzard's commodities endpoint returns one row per individual auction listing, not one row per item. The raw table is keyed on `(snapshot_timestamp, auction_id)` to preserve that. An earlier version keyed on `(snapshot_timestamp, item_id)` and silently dropped almost all listings per item through `ON CONFLICT DO NOTHING`, since only one row per item per snapshot could survive the constraint. No error was thrown; row counts looked plausible until checked manually.

**Snapshot timing from the API, not local clock.**
`snapshot_timestamp` is parsed from Blizzard's `Last-Modified` response header. Local poll timing and Blizzard's own refresh cadence don't line up, so using request time would misrepresent when the data was actually current.

**Quality tier resolution.**
Some crafting materials have Silver and Gold tiers, each a separate item ID, and Blizzard's API doesn't expose which is which anywhere in the response. An initial heuristic ("higher item ID means Gold") held for most sampled items but failed on 3 of 12, so it was dropped. The working method: pull prices for both tiers at the same moment and compare against known in-game prices. Gold consistently prices higher than Silver, without exception, across every item tested.

**Outlier filtering.**
A flat 99th-percentile cutoff was tried first and failed on items with low listing counts, where percentile cutoffs get unreliable at small sample sizes. Replaced with an IQR-based bound computed per item per snapshot (`Q3 + 1.5 × IQR` for the upper end). See the Mana Lily bug below for how the lower bound was added later.

**Migration to always-on hosting.**
The pipeline ran on Windows Task Scheduler at first, which is fine until the host machine gets powered off. Two outages, including a roughly 12-hour overnight gap, made this a repeat problem rather than a one-off. Moved the whole pipeline to an Oracle Cloud instance and swapped Task Scheduler for cron. Pre-migration data is excluded from the mart rather than backfilled, since interpolating values would invent market activity that was never actually observed. The mart starts at the first confirmed, cron-triggered snapshot after the move.

**Provisioning note:** the intended Ampere (A1.Flex) shape hit repeated out-of-capacity errors in a single-availability-domain region with no fallback. Ended up on a `VM.Standard.E2.1.Micro` (1 OCPU / 1GB RAM) instead, tuned conservatively for Postgres. Reasonable sizing for a 14-item hourly job, not a compromise.

**Normalized volatility metric.**
Added `price_cv` (standard deviation divided by minimum price) alongside raw standard deviation, since raw stddev isn't comparable across items trading at very different price levels. Checked against real data: stable items sit around a CV of 0.03, volatile ones range from 0.5 to 2.4. That volatility turned out to be real market behavior (a continuous underprice-ladder pattern), not a data problem, and was left in rather than smoothed out.

**Test data exclusion.**
Early pipeline test runs, from before the item basket was finalized, are excluded from the mart through a timestamp cutoff in the staging model rather than deleted from raw history. Keeps an audit trail while keeping the analytical output clean.

## A bug worth knowing about

**The Mana Lily penny listing.**
A single quantity-1 auction priced at 0.01 gold, roughly 3,900x below the surrounding market price, made it into the price chart. The original outlier filter only checked an upper bound, so there was nothing stopping a near-zero listing from passing through. A first attempt at a lower bound (`Q1 - 1.5 × IQR`, floored at 0) still let it through, because on a skewed snapshot the raw lower bound calculates as strongly negative, the floor kicks in, and the effective bound ends up at exactly 0. Fixed with a relative floor instead: `greatest(IQR_lower_bound, Q1 × 0.10)`. Confirmed the listing is now excluded and total row counts stayed stable across all 14 items (178,172 rows).

**The Blizzard maintenance "gap."**
A multi-day check of hourly listing counts found one missing hour out of 44. Checked `ingest.log` and found both the surrounding cron runs pulled the same `snapshot_timestamp`, because Blizzard's AH servers were down for scheduled weekly maintenance at that time. Since the raw table is keyed on `(snapshot_timestamp, auction_id)`, the duplicate rows were skipped automatically with no special handling needed. 43 of 44 hours captured, and the one gap is fully explained by a predictable external event rather than a pipeline failure.

## Item basket

14 confirmed current-expansion items (Midnight, patch 12.0.x), all sourced through Blizzard's item search and commodities endpoints rather than pulled from wikis or gold guide sites.

| Item | Item ID | Tier |
|---|---|---|
| Nocturnal Lotus | 236780 | single-tier |
| Dazzling Thorium | 237366 | single-tier |
| Azeroot | 236775 | Gold |
| Sanguithorn | 236771 | Gold |
| Argentleaf | 236777 | Gold |
| Refulgent Copper Ore | 237361 | Gold |
| Bright Linen | 236965 | Gold |
| Arcanoweave | 237017 | Gold (lower ID) |
| Gloaming Alloy | 238203 | Gold |
| Sterling Alloy | 238205 | Gold |
| Mana Lily | 236779 | Gold |
| Infused Scalewoven Hide | 244633 | Gold (lower ID) |
| Sin'dorei Armor Banding | 244635 | Gold (lower ID) |
| Void-Tempered Plating | 238521 | Gold |

Three items are entered with the lower of the two item IDs as Gold tier, which is the opposite of what the ID-ordering heuristic predicted for most items. This is exactly why that heuristic was dropped in favor of price comparison.

Blizzard's item name-search endpoint occasionally fails to surface items that are otherwise valid and actively traded (Mana Lily was one case). Worked around by pulling candidate IDs from Wowhead and confirming them against the item-detail and commodities endpoints directly. Doesn't affect ingestion once an item's ID is known.

**Why the basket stayed at 14 items instead of covering the full market.**
Tier verification was done by hand for this project: pull both item IDs for a dual-tier item, compare their prices at the same moment, and confirm which one is Gold. This could be automated, since the same price-comparison logic used to verify tiers manually could run on a schedule and flag the higher-priced ID as Gold once enough snapshots rule out temporary price crossing. That script wasn't built for this project because the 1GB RAM instance is already sized tightly for the current 14-item hourly job, and adding a second recurring process wasn't worth the resource contention for a basket this size. At a larger basket, automating tier resolution would be one of the first things worth doing.

## Known limitations

- SSL is off on the Postgres connection, offset by IP allowlisting and iptables. Not a choice that would carry over to a system handling sensitive data.
- The timezone fix uses a fixed UTC offset (correct for PDT), not a DST-aware conversion.
- The instance is 1 OCPU / 1GB RAM, sized for this specific workload rather than for growth.
- The 10% relative floor used in the outlier filter is a judgment call, checked against one real case, not a statistically derived number.
- `requirements.txt` pins were relaxed from a full `pip freeze`, since some exact versions didn't correspond to any published release on the fresh instance.
- Quality tier verification is manual right now. It could be automated with a scheduled price-comparison script, but that wasn't built given the instance's resource constraints. Would be worth doing before expanding the basket much further.
