with source as (
    select * from {{ source('raw', 'raw_auction_commodities') }}
),
cleaned as (
    select
        auction_id,
        item_id,
        unit_price::numeric / 10000.0 as unit_price_gold,
        quantity::integer as quantity,
        snapshot_timestamp::timestamptz as snapshot_timestamp,
        date_trunc('hour', snapshot_timestamp::timestamptz) as snapshot_hour
    from source
    where item_id is not null
      and unit_price is not null
      and snapshot_timestamp >= '2026-07-14 00:03:11+00'-- Migrated from unreliable
      -- local Task Scheduler (unplanned shutdown gaps) to always-on Oracle Cloud
      -- + cron on 2026-07-14. Pre-migration data excluded rather than backfilled,
      -- since gaps reflect expected missing observations, not a data quality issue
      -- to patch.
),
thresholds as (
    select
        item_id,
        snapshot_timestamp,
        percentile_cont(0.25) within group (order by unit_price_gold) as q1_price_gold,
        percentile_cont(0.75) within group (order by unit_price_gold) as q3_price_gold
    from cleaned
    group by item_id, snapshot_timestamp
),
bounds as (
    select
        item_id,
        snapshot_timestamp,
        q3_price_gold + 1.5 * (q3_price_gold - q1_price_gold) as upper_bound_gold,
        -- Pure IQR lower bound can go negative (or near-zero) on right-skewed
        -- snapshots, letting mispriced near-zero listings slip through.
        -- Floor at 10% of Q1 as a practical backstop against that failure mode.
        greatest(
            q1_price_gold - 1.5 * (q3_price_gold - q1_price_gold),
            q1_price_gold * 0.1
        ) as lower_bound_gold
    from thresholds
)
select
    c.auction_id,
    c.item_id,
    c.unit_price_gold,
    c.quantity,
    c.snapshot_timestamp,
    c.snapshot_hour
from cleaned c
join bounds b
    on c.item_id = b.item_id
    and c.snapshot_timestamp = b.snapshot_timestamp
where c.unit_price_gold <= b.upper_bound_gold
  and c.unit_price_gold >= b.lower_bound_gold