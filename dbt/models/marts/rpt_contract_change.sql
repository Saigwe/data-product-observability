-- Daily view events around the activity API's schema change, counted with the mapping in staging and with a naive
-- filter on the old activity name. The naive count drops to zero on the change date; the mapped count does not.
select cast(e.event_time as date) as event_date,
       any_value(e.schema_version) as schema_version,
       count(*) filter (where e.activity_type = 'view') as views_mapped,
       count(*) filter (where e.source_activity = 'ViewReport') as views_naive_filter
from {{ ref('stg_activity_events') }} e
group by all
