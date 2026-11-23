select cast(sales_date as date) as sales_date, retailer_id, units, cast(received_at as timestamp) as received_at
from {{ source('raw', 'sellthrough_api') }}
