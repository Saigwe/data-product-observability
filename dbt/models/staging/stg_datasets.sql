select dataset_id, dataset_name, cadence, due_hour_utc from {{ source('raw', 'datasets') }}
