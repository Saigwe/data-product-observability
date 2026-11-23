-- Category counts by app version and platform; 'uncategorised' is a category, so a new topic shows up as its growth.
with c as (
    select app_version, platform, category, count(*) as reviews
    from {{ ref('fct_reviews') }}
    where product_id = 'APP-CONNECT'
    group by all
)
select *, reviews / sum(reviews) over (partition by app_version, platform) as share from c
