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
)

select * from cleaned