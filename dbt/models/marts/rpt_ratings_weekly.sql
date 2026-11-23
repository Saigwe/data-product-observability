-- Weekly rating by product and market, always with its review count. The baseline is the product-market's rating over
-- the previous eight weeks; the shrunk rating pulls a thin week toward that baseline with a prior of rating_prior_weight
-- reviews. A drop is actionable only with enough reviews; a drop that mostly disappears once shrunk is a weak signal.
with w as (
    select product_id, market, week_start, count(*) as reviews, avg(stars) as avg_stars, stddev_samp(stars) as sd_stars
    from {{ ref('fct_reviews') }}
    where is_mapped and product_id <> 'APP-CONNECT' and week_start < cast(date_trunc('week', timestamp '{{ var("as_of") }}') as date)
    group by all
), b as (
    select w.*,
           sum(avg_stars * reviews) over prior / nullif(sum(reviews) over prior, 0) as baseline_stars,
           sum(reviews) over prior as baseline_reviews
    from w
    window prior as (partition by product_id, market order by week_start rows between 8 preceding and 1 preceding)
), s as (
    select b.*,
           (avg_stars * reviews + baseline_stars * {{ var('rating_prior_weight') }}) / (reviews + {{ var('rating_prior_weight') }}) as shrunk_stars
    from b
)
select s.*,
       avg_stars - baseline_stars as change_vs_baseline,
       shrunk_stars - baseline_stars as shrunk_change,
       case
           when baseline_stars is null then 'no baseline'
           when avg_stars - baseline_stars > -{{ var('rating_drop_threshold') }} then 'no change'
           when reviews >= {{ var('actionable_min_reviews') }} then 'actionable'
           when shrunk_stars - baseline_stars <= -{{ var('weak_signal_shrunk_drop') }} then 'weak signal'
           else 'noise'
       end as signal
from s
