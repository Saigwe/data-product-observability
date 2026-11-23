-- Matched sell-through in the reconciliation equals the source totals for each route.
with r as (select sum(api_units) as a, sum(sftp_units) as s from {{ ref('rpt_sellthrough_recon') }}),
     a as (select sum(units) as a from {{ ref('stg_sellthrough_api') }}),
     s as (select sum(units) as s from {{ ref('stg_sellthrough_sftp') }})
select * from r, a, s where r.a <> a.a or r.s <> s.s
