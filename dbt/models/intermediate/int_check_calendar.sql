-- One scheduled freshness check per dataset and day (Mondays for weekly datasets), at the due hour, up to the as-of time.
-- A check passes if the dataset holds data through the end of the previous day.
with d as (
    select cast(t as date) as check_date
    from generate_series(timestamp '2026-05-05', timestamp '{{ var("as_of") }}', interval 1 day) g(t)
)
select ds.dataset_id, d.check_date,
       d.check_date + interval (ds.due_hour_utc) hour as check_at,
       cast(d.check_date as timestamp) - interval 1 second as expected_watermark
from {{ ref('stg_datasets') }} ds
cross join d
where (ds.cadence = 'daily' or dayofweek(d.check_date) = 1)
  and d.check_date + interval (ds.due_hour_utc) hour <= timestamp '{{ var("as_of") }}'
