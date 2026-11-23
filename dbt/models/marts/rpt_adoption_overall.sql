-- Platform-wide, per complete week: distinct member viewers across all reports (counted once, not summed per report),
-- total member views, and report coverage (live reports with at least one member view that week).
with f as (
    select * from {{ ref('fct_report_activity') }}
    where week_start < cast(date_trunc('week', timestamp '{{ var("as_of") }}') as date) and not is_service and activity_type = 'view'
), live as (
    select w.week_start, count(distinct r.report_key) as live_reports
    from (select distinct week_start from f) w
    join {{ ref('dim_report') }} r on r.created_on <= w.week_start + interval 6 day and (r.deleted_on is null or r.deleted_on >= w.week_start)
    group by all
)
select f.week_start,
       count(distinct f.user_key) as distinct_viewers,
       count(*) as member_views,
       count(distinct f.report_key) as reports_viewed,
       any_value(live.live_reports) as live_reports,
       count(distinct f.report_key) / any_value(live.live_reports) as report_coverage
from f join live using (week_start)
group by f.week_start
