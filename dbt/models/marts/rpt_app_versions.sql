-- App quality by version and platform: volume, average with a 95% interval, low-star share, category mix, and the
-- change against the previous version on the same platform. A drop is actionable when there are enough reviews and
-- its 95% interval excludes zero.
with r as (
    select * from {{ ref('fct_reviews') }} where product_id = 'APP-CONNECT'
), v as (
    select app_version, platform, count(*) as reviews, avg(stars) as avg_stars, stddev_samp(stars) as sd_stars,
           count(*) filter (where stars <= 2) / count(*) as low_star_share,
           count(*) filter (where category = 'pairing') / count(*) as pairing_share,
           count(*) filter (where category = 'uncategorised') / count(*) as uncategorised_share,
           min(posted_date) as first_review
    from r group by all
), c as (
    select *,
           avg_stars - 1.96 * sd_stars / sqrt(reviews) as ci_low,
           avg_stars + 1.96 * sd_stars / sqrt(reviews) as ci_high,
           avg_stars - lag(avg_stars) over (partition by platform order by app_version) as change_vs_previous,
           sqrt(sd_stars ^ 2 / reviews + lag(sd_stars ^ 2 / reviews) over (partition by platform order by app_version)) as se_change
    from v
)
select *,
       case
           when change_vs_previous is null then 'no baseline'
           when change_vs_previous > -{{ var('rating_drop_threshold') }} then 'no change'
           when reviews >= {{ var('actionable_min_reviews') }} and change_vs_previous + 1.96 * se_change < 0 then 'actionable'
           else 'weak signal'
       end as signal
from c
