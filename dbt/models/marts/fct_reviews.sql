-- Grain: one review. No reviewer handle. Category from deterministic rules; unmapped listings kept and flagged.
select r.review_id, r.source, r.product_id, p.brand, p.product_name, p.product_type, p.comparable_group, r.is_mapped,
       r.market, r.platform, r.app_version,
       cast(r.posted_at as date) as posted_date, cast(date_trunc('week', r.posted_at) as date) as week_start,
       r.stars, c.category, c.rule_id
from {{ ref('stg_reviews') }} r
join {{ ref('int_review_categories') }} c using (review_id)
left join {{ ref('products') }} p using (product_id)
