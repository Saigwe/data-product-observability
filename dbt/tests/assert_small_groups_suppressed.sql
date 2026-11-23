select * from {{ ref('rpt_department_usage') }} where viewers_28d < {{ var('min_group_size') }}
