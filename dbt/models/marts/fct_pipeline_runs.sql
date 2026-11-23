select r.*, date_diff('minute', r.started_at, r.finished_at) as duration_minutes from {{ ref('stg_pipeline_runs') }} r
