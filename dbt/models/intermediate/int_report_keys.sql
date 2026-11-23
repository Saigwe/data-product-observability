-- A stable report key across a workspace migration: the old report ID maps to its successor.
select r.report_id, coalesce(l.new_report_id, r.report_id) as report_key
from {{ ref('stg_reports') }} r
left join {{ ref('stg_report_lineage') }} l on l.old_report_id = r.report_id
