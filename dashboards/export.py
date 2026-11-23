"""Collect what the dashboard pages show into one JSON document, from the gold marts.

Usage: python dashboards/export.py --db warehouse/observability.duckdb --out dashboards/site/data.json
"""
from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from pathlib import Path

import duckdb

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def rows(con, sql: str) -> list[dict]:
    cur = con.execute(sql)
    cols = [d[0] for d in cur.description]
    out = []
    for r in cur.fetchall():
        rec = {}
        for k, v in zip(cols, r):
            if isinstance(v, datetime):
                v = v.isoformat(sep=" ")[:16]
            elif isinstance(v, date):
                v = v.isoformat()[:10]
            elif isinstance(v, float):
                v = round(v, 6)
            elif v is not None and not isinstance(v, (int, str, bool)):
                v = float(v)
            rec[k] = v
        out.append(rec)
    return out


def collect(con) -> dict:
    d: dict = {}
    d["adoption"] = rows(con, "select * from gold.rpt_adoption_28d order by avg_weekly_viewers desc")
    d["weekly"] = rows(con, "select * from gold.rpt_adoption_weekly order by week_start, report_key")
    d["overall"] = rows(con, "select * from gold.rpt_adoption_overall order by week_start")
    d["dept"] = rows(con, "select * from gold.rpt_department_usage order by report_key, department")
    d["metricv"] = rows(con, "select * from gold.rpt_metric_versions order by share_removed_by_v2 desc")
    d["contract"] = rows(con, "select * from gold.rpt_contract_change where event_date between date '2026-08-24' and date '2026-10-11' order by event_date")
    d["priority"] = rows(con, "select * from gold.rpt_sla_priority order by priority_rank")
    d["checks_fresh"] = rows(con, "select * from gold.rpt_freshness_checks order by check_date, dataset_id")
    d["health"] = rows(con, """select * from gold.rpt_report_health where report_key = 'R-001'
                               and check_date between date '2026-09-28' and date '2026-10-31' order by check_date""")
    d["sftp"] = rows(con, """select * from gold.rpt_sftp_timeliness where sales_date between date '2026-09-27' and date '2026-10-30'
                             and retailer_id = 'RT-02' order by sales_date""")
    d["recon"] = rows(con, "select sales_date, sum(api_units) as api_units, sum(sftp_units) as sftp_units from gold.rpt_sellthrough_recon group by 1 order by 1")
    d["queue"] = rows(con, "select * from gold.rpt_exception_queue order by sales_date")
    d["app"] = rows(con, "select * from gold.rpt_app_versions order by platform, app_version")
    d["cats"] = rows(con, "select * from gold.rpt_review_categories order by app_version, platform, category")
    d["ratings"] = rows(con, "select * from gold.rpt_ratings_weekly order by product_id, market, week_start")
    d["products"] = rows(con, "select * from gold.rpt_product_ratings order by comparable_group, brand, product_id")
    d["checks"] = rows(con, "select * from gold.rpt_data_checks")
    d["registry"] = rows(con, "select * from silver.metric_registry order by metric_id, version")
    d["datasets"] = rows(con, "select * from silver.stg_datasets order by dataset_id")
    return d


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(ROOT / "warehouse" / "observability.duckdb"))
    ap.add_argument("--out", default=str(HERE / "site" / "data.json"))
    ap.add_argument("--dbt-results", default=str(ROOT / "dbt" / "target" / "run_results.json"))
    a = ap.parse_args()
    with duckdb.connect(a.db, read_only=True) as con:
        data = collect(con)
    rr = Path(a.dbt_results)
    if rr.exists():
        results = json.loads(rr.read_text(encoding="utf-8"))["results"]
        data["dbt"] = {"nodes": len(results), "passed": sum(r["status"] in ("pass", "success") for r in results),
                       "tests": sum(r["unique_id"].startswith("test.") for r in results)}
    Path(a.out).write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {a.out} ({Path(a.out).stat().st_size / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()
