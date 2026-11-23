-- SFTP file arrival against the 04:00 due time, by retailer and day: the upstream cause of late sales refreshes.
select retailer_id, sales_date, due_at, arrived_at, hours_after_due, hours_after_due > 0 as is_late
from {{ ref('stg_sftp_arrivals') }}
