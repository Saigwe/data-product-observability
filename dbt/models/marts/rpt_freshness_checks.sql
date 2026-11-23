-- Each scheduled check: was the dataset's data current at the due time, and if not, when did it become current?
with ok as (
    select dataset_id, finished_at, source_watermark from {{ ref('stg_pipeline_runs') }} where status = 'succeeded'
)
select
    c.dataset_id, c.check_date, c.check_at, c.expected_watermark,
    exists (select 1 from ok where ok.dataset_id = c.dataset_id and ok.finished_at <= c.check_at and ok.source_watermark >= c.expected_watermark) as is_fresh,
    (select min(finished_at) from ok where ok.dataset_id = c.dataset_id and ok.source_watermark >= c.expected_watermark) as fresh_at,
    (select count(*) from {{ ref('stg_pipeline_runs') }} p where p.dataset_id = c.dataset_id and p.status = 'failed'
       and cast(p.started_at as date) = c.check_date) as failed_runs
from {{ ref('int_check_calendar') }} c
