select r.report_id, k.report_key, coalesce(cur.report_name, r.report_name) as report_name, r.tier, r.dataset_id, r.owner_team,
       r.created_on, r.deleted_on, r.deleted_on is null as is_live
from {{ ref('stg_reports') }} r
join {{ ref('int_report_keys') }} k using (report_id)
left join {{ ref('stg_report_names') }} cur on cur.report_id = r.report_id and cur.valid_to is null
