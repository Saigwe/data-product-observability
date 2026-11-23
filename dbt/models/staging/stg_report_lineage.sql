select old_report_id, new_report_id, cast(effective_on as date) as effective_on, reason from {{ source('raw', 'report_lineage') }}
