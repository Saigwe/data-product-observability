-- Per report and complete week: member views, distinct member viewers, repeat viewers (also viewed the week before),
-- exports, and service-account views kept separately. Viewers are distinct accounts and are never summed across reports.
with f as (
    select * from {{ ref('fct_report_activity') }}
    where week_start < cast(date_trunc('week', timestamp '{{ var("as_of") }}') as date)
), uw as (
    select distinct report_key, week_start, user_key from f where not is_service and activity_type = 'view'
), rep as (
    select a.report_key, a.week_start, count(*) as repeat_viewers
    from uw a join uw b on b.report_key = a.report_key and b.user_key = a.user_key and b.week_start = a.week_start - interval 7 day
    group by all
), agg as (
    select
        report_key, week_start,
        count(*) filter (where not is_service and activity_type = 'view') as member_views,
        count(distinct user_key) filter (where not is_service and activity_type = 'view') as distinct_viewers,
        count(*) filter (where not is_service and activity_type = 'export') as member_exports,
        count(*) filter (where is_service) as service_events
    from f group by all
)
select agg.report_key, agg.week_start, agg.member_views, agg.distinct_viewers, coalesce(rep.repeat_viewers, 0) as repeat_viewers,
       agg.member_exports, agg.service_events
from agg left join rep using (report_key, week_start)
