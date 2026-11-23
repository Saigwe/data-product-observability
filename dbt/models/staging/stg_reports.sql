select report_id, report_name, tier, dataset_id, owner_team, cast(created_on as date) as created_on, cast(deleted_on as date) as deleted_on
from {{ source('raw', 'reports') }}
