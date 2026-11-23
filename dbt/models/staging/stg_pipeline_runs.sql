select run_id, dataset_id, cast(started_at as timestamp) as started_at, cast(finished_at as timestamp) as finished_at,
       status, rows_loaded, cast(source_watermark as timestamp) as source_watermark
from {{ source('raw', 'pipeline_runs') }}
where cast(finished_at as timestamp) <= timestamp '{{ var("as_of") }}'
