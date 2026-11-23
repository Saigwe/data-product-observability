"""Count definitions hold: viewers are distinct, views and viewers are never mixed, groups are suppressed."""
from conftest import one


def test_platform_viewers_are_distinct_not_summed(con):
    w = one(con, "select max(week_start) from gold.rpt_adoption_overall")[0]
    platform = one(con, f"select distinct_viewers from gold.rpt_adoption_overall where week_start = date '{w}'")[0]
    summed = one(con, f"select sum(distinct_viewers) from gold.rpt_adoption_weekly where week_start = date '{w}'")[0]
    assert platform < summed


def test_views_at_least_viewers(con):
    assert one(con, "select count(*) from gold.rpt_adoption_weekly where member_views < distinct_viewers or repeat_viewers > distinct_viewers")[0] == 0


def test_events_counted_once(con):
    raw = one(con, "select count(distinct event_id) from silver.stg_activity_events")[0]
    assert one(con, "select count(*) from gold.fct_report_activity")[0] == raw
    assert one(con, "select max(times_delivered) from gold.fct_report_activity")[0] > 1


def test_no_personal_identifiers_in_gold(con):
    cols = con.execute("select column_name from information_schema.columns where table_schema = 'gold'").fetchall()
    assert not [c for (c,) in cols if any(s in c.lower() for s in ("upn", "email", "handle"))]
    assert one(con, "select count(*) from gold.fct_report_activity where user_key like '%@%' or length(user_key) <> 32")[0] == 0


def test_department_groups_below_threshold_are_suppressed(con):
    assert one(con, "select count(*) from gold.rpt_department_usage where is_suppressed and viewers_28d is not null")[0] == 0
    assert one(con, "select min(viewers_28d) from gold.rpt_department_usage")[0] >= 5


def test_freshness_compliance_is_checks_not_days_of_data(con):
    c, m = one(con, "select checks, missed from gold.rpt_sla_priority where report_key = 'R-001'")
    assert c == 90 and 0 < m < c


def test_every_review_has_one_category(con):
    n, cats = one(con, "select count(*), count(distinct category) from gold.fct_reviews")
    assert n == one(con, "select count(*) from silver.stg_reviews")[0] and cats >= 8


def test_rating_always_reported_with_volume(con):
    assert one(con, "select count(*) from gold.rpt_ratings_weekly where reviews is null or reviews = 0")[0] == 0
    assert one(con, "select count(*) from gold.rpt_product_ratings where reviews <> stars_1 + stars_2 + stars_3 + stars_4 + stars_5")[0] == 0
