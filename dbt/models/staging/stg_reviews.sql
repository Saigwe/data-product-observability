-- Reviews without the reviewer's handle. App reviews carry the app's product ID; reseller reviews are mapped from
-- their listing name through product_aliases, and an unknown listing stays unmapped rather than guessed.
select
    r.review_id,
    r.source,
    coalesce(r.app_id, a.product_id) as product_id,
    r.listing_name,
    r.app_id is not null or a.product_id is not null as is_mapped,
    r.market,
    r.platform,
    r.app_version,
    cast(r.posted_at as timestamp) as posted_at,
    cast(r.scraped_at as timestamp) as scraped_at,
    r.stars,
    r.review_text
from {{ source('raw', 'reviews') }} r
left join {{ ref('product_aliases') }} a using (listing_name)
where cast(r.scraped_at as timestamp) <= timestamp '{{ var("as_of") }}'
