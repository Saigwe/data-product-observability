-- Grain: one activity event. Reports are keyed by report_key, which survives the workspace migration.
select
    e.event_id, e.event_time, cast(e.event_time as date) as event_date,
    cast(date_trunc('week', e.event_time) as date) as week_start,
    e.user_key, a.department, a.is_service,
    e.report_id, k.report_key, e.report_name_at_event,
    e.activity_type, e.schema_version, e.ingest_lag_hours, e.arrived_late, e.times_delivered
from {{ ref('stg_activity_events') }} e
join {{ ref('int_report_keys') }} k using (report_id)
join {{ ref('dim_account') }} a using (user_key)
