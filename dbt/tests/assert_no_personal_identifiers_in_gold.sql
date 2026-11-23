-- No principal names, e-mail addresses or reviewer handles may reach the gold layer, as columns or as values.
select table_name, column_name from information_schema.columns
where table_schema = 'gold' and (column_name ilike '%upn%' or column_name ilike '%email%' or column_name ilike '%handle%')
union all
select 'fct_report_activity', 'user_key' from {{ ref('fct_report_activity') }} where user_key like '%@%' limit 1
