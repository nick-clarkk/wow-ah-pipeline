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
        round(stddev(unit_price_gold)::numeric, 4) as price_stddev,
        round(stddev(unit_price_gold)::numeric / nullif(min(unit_price_gold), 0), 4) as price_cv
    from stg
    group by item_id, snapshot_timestamp
),
lookup as (
    select * from {{ ref('item_lookup') }}
)
select
    a.item_id,
    l.item_name,
    a.snapshot_timestamp,
    a.min_price_gold,
    a.total_quantity,
    a.listing_count,
    a.price_stddev,
    a.price_cv
from aggregated a
left join lookup l
    on a.item_id = l.item_id