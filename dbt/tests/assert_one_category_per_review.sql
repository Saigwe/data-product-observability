select review_id, count(*) from {{ ref('int_review_categories') }} group by 1 having count(*) <> 1
