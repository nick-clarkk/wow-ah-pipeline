with stg as (
    select * from {{ ref('stg_auction_commodities') }}
),

aggregated as (
    select
        item_id,
        snapshot_timestamp,
        min(unit_price_gold) as min_price_gold,
        sum(quantity) as total_quantity,
        count(distinct auction_id) as listing_count,
        stddev(unit_price_gold) as price_stddev
    from stg
    group by item_id, snapshot_timestamp
)

select * from aggregated