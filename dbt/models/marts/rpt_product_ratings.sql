-- Product ratings with volume and the star distribution, own products beside comparable competitors.
select product_id, any_value(brand) as brand, any_value(product_name) as product_name, any_value(comparable_group) as comparable_group,
       count(*) as reviews, avg(stars) as avg_stars,
       count(*) filter (where stars = 1) as stars_1, count(*) filter (where stars = 2) as stars_2, count(*) filter (where stars = 3) as stars_3,
       count(*) filter (where stars = 4) as stars_4, count(*) filter (where stars = 5) as stars_5
from {{ ref('fct_reviews') }}
where is_mapped and product_id <> 'APP-CONNECT'
group by product_id
