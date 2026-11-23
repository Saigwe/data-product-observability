-- Events on the old report ID are carried to the new key, and the old ID never appears as a key.
select * from {{ ref('fct_report_activity') }} f
join {{ ref('stg_report_lineage') }} l on f.report_id = l.old_report_id
where f.report_key <> l.new_report_id
