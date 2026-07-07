-- Raw landing table for Blizzard Auction House commodities data.
-- One row per (snapshot, item). snapshot_timestamp comes from Blizzard's
-- Last-Modified header on the commodities response, not our poll time.

CREATE TABLE IF NOT EXISTS raw_auction_commodities (
    id                  BIGSERIAL PRIMARY KEY,
    snapshot_timestamp  TIMESTAMPTZ NOT NULL,
    auction_id          BIGINT NOT NULL,   -- Blizzard's own per-listing id
    item_id             INTEGER NOT NULL,
    quantity            BIGINT,
    unit_price          BIGINT,     -- in copper; commodities are buyout-only, no bids
    loaded_at           TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_snapshot_auction UNIQUE (snapshot_timestamp, auction_id)
);

CREATE INDEX IF NOT EXISTS idx_raw_ah_item_id      ON raw_auction_commodities (item_id);
CREATE INDEX IF NOT EXISTS idx_raw_ah_snapshot_ts  ON raw_auction_commodities (snapshot_timestamp);
