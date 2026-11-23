-- Distinct member viewers by department and report, last 28 days. Groups smaller than min_group_size are suppressed.
with f as (
    select * from {{ ref('fct_report_activity') }}
    where event_time >= timestamp '{{ var("as_of") }}' - interval 28 day and event_time < timestamp '{{ var("as_of") }}'
      and not is_service and activity_type = 'view'
), g as (
    select report_key, department, count(distinct user_key) as n from f group by all
)
select report_key, department,
       case when n >= {{ var('min_group_size') }} then n end as viewers_28d,
       n < {{ var('min_group_size') }} as is_suppressed
from g
