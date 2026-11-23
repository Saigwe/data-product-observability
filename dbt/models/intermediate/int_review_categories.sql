-- Deterministic rules: the matching rule with the lowest priority number wins; no match is 'uncategorised'.
with m as (
    select r.review_id, ru.rule_id, ru.category, ru.priority
    from {{ ref('stg_reviews') }} r
    join {{ ref('review_rules') }} ru on regexp_matches(lower(r.review_text), ru.pattern)
)
select r.review_id,
       coalesce(m.category, 'uncategorised') as category,
       m.rule_id
from {{ ref('stg_reviews') }} r
left join m using (review_id)
qualify row_number() over (partition by r.review_id order by m.priority nulls last) = 1
