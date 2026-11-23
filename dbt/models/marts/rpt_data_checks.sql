select 'Activity rows delivered more than once by overlapping extracts' as check_name,
       (select count(*) from {{ source('raw', 'activity_events') }}) - (select count(*) from {{ ref('stg_activity_events') }}) as value,
       'Deduplicated on event_id; first delivery wins' as handling
union all select 'Events that arrived a day or more late', (select count(*) from {{ ref('stg_activity_events') }} where arrived_late),
       'Picked up by the three-day extract lookback'
union all select 'Events on the old activity schema (v1)', (select count(*) from {{ ref('stg_activity_events') }} where schema_version = 1),
       'ViewReport and ReportViewed both map to view'
union all select 'Service-account events', (select count(*) from {{ ref('fct_report_activity') }} where is_service),
       'Kept, but excluded from views and viewers (report_views v2)'
union all select 'Events on a report that moved workspace, carried to its new key',
       (select count(*) from {{ ref('fct_report_activity') }} where report_id <> report_key), 'Report lineage maps the old ID to the new one'
union all select 'Events recorded under a report name that has since changed',
       (select count(*) from {{ ref('fct_report_activity') }} f join {{ ref('dim_report') }} d using (report_id) where f.report_name_at_event <> d.report_name),
       'Keyed by report ID, so history is kept'
union all select 'Department groups suppressed (fewer than 5 viewers)', (select count(*) from {{ ref('rpt_department_usage') }} where is_suppressed),
       'Shown as suppressed, never as a count'
union all select 'Freshness checks missed', (select count(*) from {{ ref('rpt_freshness_checks') }} where not is_fresh),
       'Prioritised by usage in rpt_sla_priority'
union all select 'Sell-through exceptions', (select count(*) from {{ ref('rpt_exception_queue') }}),
       'In the exception queue with owner and age'
union all select 'Reviews from listings not in the product map', (select count(*) from {{ ref('fct_reviews') }} where not is_mapped),
       'Kept as unmapped; excluded from product ratings'
union all select 'App reviews no category rule matched', (select count(*) from {{ ref('fct_reviews') }} where category = 'uncategorised' and product_id = 'APP-CONNECT'),
       'Reported as uncategorised; watched for growth'
