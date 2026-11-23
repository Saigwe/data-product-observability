select cast(sales_date as date) as sales_date, retailer_id, units, file_name from {{ source('raw', 'sellthrough_sftp') }}
