-- Mapped view counts must not fall off a cliff at the schema change: the week after is within 30% of the week before.
with c as (
    select sum(views_mapped) filter (where event_date between date '2026-09-08' and date '2026-09-14') as before_w,
           sum(views_mapped) filter (where event_date between date '2026-09-15' and date '2026-09-21') as after_w
    from {{ ref('rpt_contract_change') }}
)
select * from c where after_w < 0.7 * before_w or after_w > 1.3 * before_w
