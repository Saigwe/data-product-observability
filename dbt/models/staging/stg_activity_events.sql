-- One row per event: the first extract that delivered it wins. The API changed its activity names on 2026-09-15
-- (schema version 2); both versions map to one activity type here. User principal names are replaced by a salted
-- hash and never leave this model.
with e as (
    select e.*, x.extracted_at
    from {{ source('raw', 'activity_events') }} e
    join {{ source('raw', 'activity_extracts') }} x using (extract_id)
    where x.extracted_at <= timestamp '{{ var("as_of") }}'
)
select
    event_id,
    cast(event_time as timestamp) as event_time,
    cast(ingested_at as timestamp) as ingested_at,
    extracted_at as first_extracted_at,
    count(*) over (partition by event_id) as times_delivered,
    md5('{{ var("pii_salt") }}' || lower(user_upn)) as user_key,
    report_id,
    report_name as report_name_at_event,
    workspace,
    activity as source_activity,
    case
        when activity in ('ViewReport', 'ReportViewed') then 'view'
        when activity in ('ExportReport', 'ReportExported') then 'export'
        else 'unknown'
    end as activity_type,
    schema_version,
    consumption_method,
    date_diff('minute', cast(event_time as timestamp), cast(ingested_at as timestamp)) / 60.0 as ingest_lag_hours,
    cast(extracted_at as date) > cast(event_time as date) + interval 1 day as arrived_late
from e
qualify row_number() over (partition by event_id order by extracted_at) = 1
