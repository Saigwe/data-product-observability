-- Which missed SLAs matter: SLA compliance by report, weighted by how many people use the report.
-- Priority = average weekly viewers x missed checks in the last 90 days.
with h as (
    select report_key, count(*) as checks, count(*) filter (where not is_fresh) as missed,
           sum(views_on_stale_data) as views_on_stale_data, sum(viewers_on_stale_data) as viewer_days_on_stale_data, sum(hours_stale) as hours_stale
    from {{ ref('rpt_report_health') }}
    where check_date > cast(timestamp '{{ var("as_of") }}' as date) - interval 90 day
    group by all
)
select a.report_key, a.report_name, a.tier, a.dataset_id, a.avg_weekly_viewers, a.viewers_28d,
       h.checks, h.missed, 1 - h.missed / h.checks as sla_compliance, h.views_on_stale_data, h.viewer_days_on_stale_data, h.hours_stale,
       a.avg_weekly_viewers * h.missed as priority_score,
       rank() over (order by a.avg_weekly_viewers * h.missed desc, a.avg_weekly_viewers desc) as priority_rank
from {{ ref('rpt_adoption_28d') }} a
join h using (report_key)
where a.is_live
