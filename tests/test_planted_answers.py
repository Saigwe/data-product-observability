"""Every planted problem is found where the answer key says."""
import json

from conftest import RAW, one

KEY = json.loads((RAW / "answer_key.json").read_text(encoding="utf-8"))


def test_most_used_report_with_missed_sla_is_top_priority(con):
    k = KEY["hot_report_missed_sla"]
    top = one(con, "select report_key, missed, views_on_stale_data from gold.rpt_sla_priority where priority_rank = 1")
    assert top[0] == k["report_id"] and top[1] >= len(k["late_file_dates"]) and top[2] > 0
    most_used = one(con, "select report_key from gold.rpt_adoption_28d where is_live order by avg_weekly_viewers desc limit 1")[0]
    assert most_used == k["report_id"]


def test_missed_checks_trace_to_late_files(con):
    k = KEY["hot_report_missed_sla"]
    missed = {str(r[0]) for r in con.execute(f"""select check_date from gold.rpt_freshness_checks
                 where dataset_id = '{k["dataset_id"]}' and not is_fresh and check_date between date '{k["from"]}' and date '{k["to"]}' + interval 1 day""").fetchall()}
    late = {str(r[0]) for r in con.execute(f"""select sales_date + interval 1 day from gold.rpt_sftp_timeliness
                 where retailer_id = '{k["late_retailer"]}' and is_late""").fetchall()}
    assert missed and {m[:10] for m in missed} <= {d[:10] for d in late}


def test_service_account_inflates_views_not_viewers(con):
    r = KEY["service_account_report"]
    v1, v2, removed = one(con, f"select views_v1, views_v2, share_removed_by_v2 from gold.rpt_metric_versions where report_key = '{r}'")
    assert removed > 0.5
    assert one(con, "select max(share_removed_by_v2) from gold.rpt_metric_versions where report_key <> '" + r + "'")[0] == 0
    assert one(con, "select count(*) from gold.fct_report_activity where is_service and report_key <> '" + r + "'")[0] == 0


def test_migration_rename_and_deletion(con):
    m = KEY["migrated"]
    assert one(con, f"select count(*) from gold.fct_report_activity where report_id = '{m['old']}' and report_key = '{m['new']}'")[0] > 0
    assert one(con, f"select count(*) from gold.rpt_adoption_28d where report_key = '{m['old']}'")[0] == 0
    assert one(con, f"select report_name from gold.dim_report where report_id = '{KEY['renamed']}'")[0] == "Sales Flash"
    assert one(con, f"select is_live from gold.dim_report where report_id = '{KEY['deleted']}'")[0] is False
    assert one(con, f"select is_active from gold.rpt_adoption_28d where report_key = '{KEY['never_used']}'")[0] is False


def test_contract_change_breaks_only_the_naive_count(con):
    d = KEY["contract_change"]
    naive_after = one(con, f"select sum(views_naive_filter) from gold.rpt_contract_change where event_date >= date '{d}'")[0]
    mapped_after = one(con, f"select sum(views_mapped) from gold.rpt_contract_change where event_date >= date '{d}'")[0]
    assert naive_after < 0.01 * mapped_after


def test_reconciliation_breaks_are_exactly_the_planted_ones(con):
    rows = con.execute("select retailer_id, sales_date, exception_type from gold.rpt_exception_queue order by 2").fetchall()
    miss, dbl = KEY["sftp_missing"], KEY["api_double_count"]
    assert (miss["retailer_id"], miss["sales_date"], "missing_sftp") in [(r[0], str(r[1]), r[2]) for r in rows]
    mism = [r for r in rows if r[2] == "mismatch"]
    assert {r[0] for r in mism} == {dbl["retailer_id"]} and len(mism) == 3
    assert len(rows) == 4


def test_app_bug_is_actionable_and_fixed(con):
    b = KEY["app_bug"]
    sig, pairing = one(con, f"select signal, pairing_share from gold.rpt_app_versions where app_version = '{b['version']}' and platform = '{b['platform']}'")
    assert sig == "actionable" and pairing > 0.4
    assert one(con, f"select count(*) from gold.rpt_app_versions where signal = 'actionable'")[0] == 1
    assert one(con, f"select pairing_share from gold.rpt_app_versions where app_version = '{b['fixed_in']}' and platform = '{b['platform']}'")[0] < 0.1


def test_new_topic_shows_as_uncategorised_growth(con):
    before = one(con, "select sum(reviews) filter (where category='uncategorised') / sum(reviews) from gold.rpt_review_categories where app_version < '5.1.0'")[0]
    after = one(con, "select sum(reviews) filter (where category='uncategorised') / sum(reviews) from gold.rpt_review_categories where app_version >= '5.1.0'")[0]
    assert after > before + 0.03


def test_low_volume_dip_is_a_weak_signal(con):
    w = KEY["weak_signal"]
    sig, n = one(con, f"select signal, reviews from gold.rpt_ratings_weekly where product_id = '{w['product_id']}' and market = '{w['market']}' and week_start = date '{w['week']}'")
    assert sig == "weak signal" and n < 10
    assert one(con, "select count(*) from gold.rpt_ratings_weekly where signal = 'actionable'")[0] == 0


def test_unmapped_listing_is_kept_out_of_product_ratings(con):
    n = one(con, f"select count(*) from silver.stg_reviews where listing_name = '{KEY['unmapped_alias']}' and not is_mapped")[0]
    assert n > 0
    assert one(con, "select count(*) from gold.fct_reviews where not is_mapped and product_id is not null")[0] == 0
