select report_id, report_name, cast(valid_from as date) as valid_from, cast(valid_to as date) as valid_to from {{ source('raw', 'report_names') }}
