select md5('{{ var("pii_salt") }}' || lower(user_upn)) as user_key, department, region, account_type
from {{ source('raw', 'directory') }}
