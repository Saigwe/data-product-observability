-- The same sell-through by two routes, compared by retailer and day.
select
    coalesce(a.sales_date, s.sales_date) as sales_date,
    coalesce(a.retailer_id, s.retailer_id) as retailer_id,
    a.units as api_units, s.units as sftp_units,
    case when a.units is not null and s.units is not null then a.units / s.units - 1 end as diff_pct,
    case
        when s.units is null then 'missing_sftp'
        when a.units is null then 'missing_api'
        when abs(a.units / s.units - 1) > {{ var('recon_tolerance') }} then 'mismatch'
        else 'match'
    end as status
from {{ ref('stg_sellthrough_api') }} a
full join {{ ref('stg_sellthrough_sftp') }} s using (sales_date, retailer_id)
