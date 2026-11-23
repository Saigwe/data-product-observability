-- Hashed key and attributes only. No names, no principal names.
select user_key, department, region, account_type, account_type = 'service' as is_service from {{ ref('stg_accounts') }}
