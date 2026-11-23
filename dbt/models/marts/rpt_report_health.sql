-- Per report and check date: was its dataset fresh at the due time, and how many member views landed while it was stale.
with chk as (
    select r.report_key, r.report_id, c.*,
           coalesce(c.fresh_at, timestamp '{{ var("as_of") }}') as stale_until
    from {{ ref('dim_report') }} r
    join {{ ref('rpt_freshness_checks') }} c using (dataset_id)
    where c.check_date >= r.created_on and (r.deleted_on is null or c.check_date <= r.deleted_on)
)
select chk.report_key, chk.report_id, chk.dataset_id, chk.check_date, chk.check_at, chk.is_fresh, chk.fresh_at,
       case when not chk.is_fresh then date_diff('minute', chk.check_at, chk.stale_until) / 60.0 else 0 end as hours_stale,
       count(f.event_id) filter (where not chk.is_fresh and f.event_time between chk.check_at and chk.stale_until) as views_on_stale_data,
       count(distinct f.user_key) filter (where not chk.is_fresh and f.event_time between chk.check_at and chk.stale_until) as viewers_on_stale_data
from chk
left join {{ ref('fct_report_activity') }} f
  on f.report_id = chk.report_id and f.event_date = chk.check_date and not f.is_service and f.activity_type = 'view'
group by all
