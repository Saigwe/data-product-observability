select retailer_id, cast(sales_date as date) as sales_date, file_name, cast(due_at as timestamp) as due_at, cast(arrived_at as timestamp) as arrived_at,
       date_diff('minute', cast(due_at as timestamp), cast(arrived_at as timestamp)) / 60.0 as hours_after_due
from {{ source('raw', 'sftp_arrivals') }}
