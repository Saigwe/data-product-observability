-- Each report over the last 28 days to the as-of date, under the current metric definitions.
with f as (
    select * from {{ ref('fct_report_activity') }}
    where event_time >= timestamp '{{ var("as_of") }}' - interval 28 day and event_time < timestamp '{{ var("as_of") }}'
), w as (
    select report_key, avg(distinct_viewers) as avg_weekly_viewers, sum(repeat_viewers) / nullif(sum(distinct_viewers), 0) as repeat_rate
    from {{ ref('rpt_adoption_weekly') }}
    where week_start >= cast(date_trunc('week', timestamp '{{ var("as_of") }}') as date) - interval 28 day
    group by all
), d as (
    select report_key, any_value(report_name) filter (where is_live) as report_name, any_value(tier) as tier,
           any_value(dataset_id) as dataset_id, bool_or(is_live) as is_live, any_value(owner_team) as owner_team
    from {{ ref('dim_report') }} group by all
)
select
    d.report_key, d.report_name, d.tier, d.dataset_id, d.owner_team, d.is_live,
    count(distinct f.user_key) filter (where not f.is_service and f.activity_type = 'view') as viewers_28d,
    count(*) filter (where not f.is_service and f.activity_type = 'view') as views_28d,
    count(*) filter (where f.activity_type = 'view') as views_28d_all_accounts,
    count(*) filter (where f.is_service) as service_events_28d,
    coalesce(w.avg_weekly_viewers, 0) as avg_weekly_viewers,
    w.repeat_rate,
    count(*) filter (where not f.is_service and f.activity_type = 'view') > 0 as is_active
from d
left join f using (report_key)
left join w using (report_key)
group by all
