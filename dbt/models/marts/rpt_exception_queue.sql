-- The exception queue: every reconciliation break, with age at the as-of date and the units at stake.
select
    'SELL-' || retailer_id || '-' || strftime(sales_date, '%Y%m%d') as exception_id,
    retailer_id, sales_date, status as exception_type,
    api_units, sftp_units, diff_pct,
    abs(coalesce(api_units, 0) - coalesce(sftp_units, 0)) as units_at_stake,
    date_diff('day', sales_date, cast(timestamp '{{ var("as_of") }}' as date)) as age_days,
    case status when 'missing_sftp' then 'Retailer file transfer' when 'missing_api' then 'Retailer API' else 'Data platform' end as owner
from {{ ref('rpt_sellthrough_recon') }}
where status <> 'match'
