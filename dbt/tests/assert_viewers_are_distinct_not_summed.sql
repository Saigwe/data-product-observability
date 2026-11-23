-- Platform-wide weekly viewers must equal a distinct recount, and can never exceed the sum of per-report viewers.
with recount as (
    select week_start, count(distinct user_key) as n from {{ ref('fct_report_activity') }}
    where not is_service and activity_type = 'view' group by all
), per_report as (
    select week_start, sum(distinct_viewers) as s from {{ ref('rpt_adoption_weekly') }} group by all
)
select o.* from {{ ref('rpt_adoption_overall') }} o
join recount r using (week_start) join per_report p using (week_start)
where o.distinct_viewers <> r.n or o.distinct_viewers > p.s
