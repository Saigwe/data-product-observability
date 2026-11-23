-- What the change from report_views v1 (all accounts) to v2 (member accounts) does to each report, last 28 days.
select r.report_key, r.report_name, r.views_28d_all_accounts as views_v1, r.views_28d as views_v2,
       1 - r.views_28d / nullif(r.views_28d_all_accounts, 0) as share_removed_by_v2,
       (select version from {{ ref('metric_registry') }} where metric_id = 'report_views' and status = 'current') as current_version
from {{ ref('rpt_adoption_28d') }} r
where r.views_28d_all_accounts > 0
