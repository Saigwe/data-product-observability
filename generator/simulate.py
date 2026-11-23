"""Synthetic data-product telemetry for Brightwater Electronics, a fictional consumer-electronics company.

Writes, as each source would deliver it:
  activity_events       report activity from a BI platform's activity API, one row per event per extract. Extracts
                        look back three days, so most events arrive more than once; some arrive a day or more late. On
                        2026-09-15 the API changes its schema (activity names, a new field)
  activity_extracts     one row per daily API extract
  directory             accounts: department, region, member or service account (no names)
  reports, report_lineage, report_names   the report catalogue, a workspace migration and a rename history
  datasets, pipeline_runs                 refresh runs with the source watermark each one loaded
  sellthrough_api, sellthrough_sftp, sftp_arrivals   the same retailer sell-through from two routes
  reviews                                 app-store and reseller reviews with star ratings, as scraped
  answer_key.json                         what was planted, for the tests

Planted:
  * Executive Sales Scorecard, the most-used report, misses its 07:00 freshness SLA on nine days in October because
    the largest retailer's SFTP file arrives late.
  * A service account exports Ad-hoc Export Pack every ten minutes overnight: thousands of views, one viewer.
  * Returns Dashboard moves workspace on 2026-08-03 and gets a new report ID; Weekly Sales Flash is renamed
    Sales Flash on 2026-09-01; Legacy Sales Cube is deleted on 2026-08-15.
  * The activity API renames ViewReport to ReportViewed on 2026-09-15.
  * Retailer RT-04's SFTP file for 2026-10-14 never arrives; RT-07's API feed double-counts 8 to 10 September.
  * App version 5.2.0 (6 October) breaks Bluetooth pairing on Android: hundreds of one- and two-star reviews.
    5.2.1 fixes it on 2 November. A new complaint about subscriptions starts in 5.1.0 that no category rule knows.
  * Arc Speaker Mini in Japan gets three poor reviews in one week: a dip on almost no volume.
Every name and number is invented.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 23
START = date(2026, 5, 4)
AS_OF = datetime(2026, 11, 23, 8, 0)
END = date(2026, 11, 22)                       # last full day
CONTRACT_CHANGE = date(2026, 9, 15)
SALES_INCIDENT = (date(2026, 10, 5), date(2026, 10, 23))
# RT-02's SFTP file for these sales dates lands this many hours after its 04:00 due time
LATE_FILES = {date(2026, 10, d): hrs for d, hrs in ((5, 4.5), (6, 6.0), (8, 3.8), (12, 7.5), (13, 5.0), (15, 8.5), (19, 4.2), (20, 6.8), (22, 3.6))}

DEPTS = {"Executive": 24, "Sales": 120, "Supply Chain": 100, "Operations": 80, "Finance": 40, "Marketing": 60, "Analytics": 30}
REGIONS = ["Americas", "Europe", "Asia Pacific"]
# report_id, name, tier, dataset, owner, created, ended, departments that use it, daily view propensity
REPORTS = [
    ("R-001", "Executive Sales Scorecard", "Executive", "DS-SALES", "Commercial analytics", None, None, {"Executive": 0.85, "Sales": 0.7, "Finance": 0.35, "Marketing": 0.3, "Supply Chain": 0.1}),
    ("R-002", "S&OP Executive Scorecard", "Executive", "DS-PLAN", "Planning analytics", None, None, {"Executive": 0.35, "Supply Chain": 0.3, "Operations": 0.15}),
    ("R-003", "Order Reliability", "Operational", "DS-ORDERS", "Supply chain analytics", None, None, {"Supply Chain": 0.45, "Operations": 0.35}),
    ("R-004", "Inventory Daily", "Operational", "DS-INV", "Supply chain analytics", None, None, {"Supply Chain": 0.5, "Operations": 0.4, "Sales": 0.1}),
    ("R-005", "Market Share Weekly", "Executive", "DS-MARKET", "Commercial analytics", None, None, {"Executive": 0.2, "Marketing": 0.35, "Sales": 0.15}),
    ("R-006", "Pricing and Promotions", "Self-serve", "DS-MARKET", "Commercial analytics", None, None, {"Marketing": 0.25, "Sales": 0.1}),
    ("R-007", "Returns Dashboard", "Operational", "DS-RETURNS", "Supply chain analytics", None, "2026-08-02", {"Operations": 0.25, "Finance": 0.15}),
    ("R-008", "Forecast Accuracy", "Operational", "DS-PLAN", "Planning analytics", None, None, {"Supply Chain": 0.25, "Analytics": 0.2}),
    ("R-009", "Warehouse Performance", "Operational", "DS-ORDERS", "Supply chain analytics", None, None, {"Operations": 0.3}),
    ("R-010", "Supplier OTIF", "Operational", "DS-ORDERS", "Supply chain analytics", None, None, {"Supply Chain": 0.2, "Finance": 0.05}),
    ("R-011", "App Reviews", "Self-serve", "DS-REVIEWS", "Consumer insights", None, None, {"Marketing": 0.15, "Analytics": 0.1}),
    ("R-012", "Review and Star Rating", "Self-serve", "DS-REVIEWS", "Consumer insights", None, None, {"Marketing": 0.2, "Sales": 0.05}),
    ("R-013", "Capacity Utilisation", "Operational", "DS-PLAN", "Planning analytics", None, None, {"Operations": 0.15, "Supply Chain": 0.1}),
    ("R-014", "Weekly Sales Flash", "Executive", "DS-SALES", "Commercial analytics", None, None, {"Executive": 0.3, "Sales": 0.3}),
    ("R-015", "Sell-through Data Quality", "Self-serve", "DS-SELLTHRU", "Data platform", None, None, {"Analytics": 0.35}),
    ("R-016", "BI Usage Monitor", "Self-serve", "DS-USAGE", "Data platform", None, None, {"Analytics": 0.25}),
    ("R-017", "Channel Margin", "Executive", "DS-SALES", "Finance analytics", None, None, {"Finance": 0.4, "Executive": 0.15}),
    ("R-018", "Post-Purchase Experience", "Self-serve", "DS-REVIEWS", "Consumer insights", None, None, {"Marketing": 0.08}),
    ("R-019", "Labour Planning", "Operational", "DS-PLAN", "Planning analytics", None, None, {"Operations": 0.2}),
    ("R-020", "Purchase Price Variance", "Operational", "DS-FIN", "Finance analytics", None, None, {"Finance": 0.3}),
    ("R-021", "Store Performance", "Self-serve", "DS-SALES", "Commercial analytics", None, None, {"Sales": 0.2}),
    ("R-022", "Legacy Sales Cube", "Self-serve", "DS-SALES", "Commercial analytics", None, "2026-08-14", {"Sales": 0.03, "Finance": 0.03}),
    ("R-023", "Promo Planner", "Self-serve", "DS-MARKET", "Commercial analytics", None, None, {"Marketing": 0.006, "Sales": 0.002, "Finance": 0.004}),
    ("R-024", "Ad-hoc Export Pack", "Self-serve", "DS-SALES", "Commercial analytics", None, None, {"Sales": 0.02}),
    ("R-025", "Regional Trade Terms", "Self-serve", "DS-FIN", "Finance analytics", None, None, {}),     # catalogued, never opened
    ("R-031", "Returns Dashboard", "Operational", "DS-RETURNS", "Supply chain analytics", "2026-08-03", None, {"Operations": 0.25, "Finance": 0.15}),
]
RENAME = ("R-014", "Sales Flash", date(2026, 9, 1))
# dataset_id, name, cadence, due hour UTC, run start hour UTC
DATASETS = [
    ("DS-SALES", "Sales and sell-through", "daily", 7, 5), ("DS-PLAN", "Planning snapshots", "weekly", 9, 6),
    ("DS-ORDERS", "Orders and fulfilment", "daily", 6, 4), ("DS-INV", "Inventory positions", "daily", 6, 4),
    ("DS-MARKET", "Market panel", "weekly", 12, 8), ("DS-RETURNS", "Returns", "daily", 8, 5),
    ("DS-REVIEWS", "Reviews and ratings", "daily", 9, 6), ("DS-SELLTHRU", "Sell-through reconciliation", "daily", 7, 5),
    ("DS-USAGE", "BI activity", "daily", 6, 3), ("DS-FIN", "Finance actuals", "daily", 8, 5),
]
RETAILERS = [("RT-01", 0.22), ("RT-02", 0.26), ("RT-03", 0.14), ("RT-04", 0.10), ("RT-05", 0.09), ("RT-06", 0.08), ("RT-07", 0.06), ("RT-08", 0.05)]
VERSIONS = [("4.8.0", date(2026, 4, 20)), ("4.9.0", date(2026, 6, 15)), ("5.0.0", date(2026, 8, 3)), ("5.1.0", date(2026, 9, 7)),
            ("5.2.0", date(2026, 10, 6)), ("5.2.1", date(2026, 11, 2))]
APP_MARKETS = {"US": 0.40, "UK": 0.15, "DE": 0.18, "FR": 0.12, "JP": 0.15}
PRODUCTS = [  # product_id, brand, name, listing aliases at resellers, base stars, daily reviews
    ("P-ARC-MINI", "Brightwater", "Arc Speaker Mini", ["Brightwater Arc Speaker Mini", "Arc Mini Speaker", "Arc Mini (Renewed)"], 4.4, 1.6),
    ("P-ARC", "Brightwater", "Arc Speaker", ["Brightwater Arc Speaker", "Arc Speaker Bluetooth"], 4.5, 2.2),
    ("P-PULSE-HP", "Brightwater", "Pulse Headphones", ["Brightwater Pulse Headphones", "Pulse Over-Ear"], 4.3, 3.0),
    ("P-PULSE-EB", "Brightwater", "Pulse Earbuds", ["Brightwater Pulse Earbuds", "Pulse True Wireless"], 4.05, 4.0),
    ("C-SOLO-EB", "Competitor", "Solo Earbuds", ["Solo Earbuds", "Solo True Wireless"], 4.3, 4.5),
    ("C-WAVE-SPK", "Competitor", "Wave Speaker", ["Wave Speaker"], 4.35, 2.5),
    ("C-HALO-HP", "Competitor", "Halo Headphones", ["Halo Headphones"], 4.2, 2.8),
]
RESELLERS = ["Reseller A", "Reseller B", "Reseller C"]
TEXT = {  # category -> review sentences; the classifier rules in dbt/seeds/review_rules.csv key on these words
    "pairing": ["Won't pair with my phone since the update.", "Bluetooth keeps disconnecting every few minutes.", "Pairing fails, had to reset twice."],
    "battery": ["Battery drains fast now.", "Battery life is shorter than advertised."],
    "sound": ["Great sound and the EQ is easy to use.", "Bass is muddy at high volume.", "Sound quality is excellent."],
    "firmware": ["Firmware update got stuck at 80%.", "The firmware update took forever."],
    "ui": ["The new layout is confusing.", "Menus are hard to find in the app."],
    "login": ["Can't log in to my account.", "Login loops back to the start screen."],
    "crash": ["App crashes on launch.", "Keeps crashing when I open settings."],
    "praise": ["Love it, works perfectly.", "Does exactly what I need.", "Five stars, no complaints."],
    "subscription": ["Why do I now need to pay monthly for features I had?", "Premium plan pop-up every time I open it."],
    "other": ["Okay I guess.", "Gift for my son.", "Arrived on time.", "Not sure yet."],
}


def days(a: date, b: date) -> list[date]:
    return [a + timedelta(days=i) for i in range((b - a).days + 1)]


def h(s: str) -> str:
    return hashlib.sha1(s.encode()).hexdigest()[:12]


def simulate(out: Path) -> dict:
    rng = np.random.default_rng(SEED)
    out.mkdir(parents=True, exist_ok=True)
    cal = days(START, END)

    # ---- directory: accounts only, no names
    acc = []
    n = 0
    for dept, k in DEPTS.items():
        for _ in range(k):
            n += 1
            acc.append((f"u{n:04d}@brightwater.example", dept, REGIONS[rng.integers(0, 3)], "member"))
    acc.append(("svc-export-01@brightwater.example", "Data platform", "Europe", "service"))
    directory = pd.DataFrame(acc, columns=["user_upn", "department", "region", "account_type"])

    # ---- activity: per report, users x days Bernoulli, then a Poisson number of views
    members = directory[directory.account_type == "member"].reset_index(drop=True)
    engagement = rng.lognormal(0, 0.5, len(members))
    ev = []
    for rid, name, tier, ds, owner, created, ended, use in REPORTS:
        if not use:
            continue
        c0 = date.fromisoformat(created) if created else START
        c1 = date.fromisoformat(ended) if ended else END
        p_user = members.department.map(use).fillna(0.0).to_numpy() * engagement
        for d in days(c0, c1):
            wk = 0.12 if d.weekday() >= 5 else 1.0
            if rid in ("R-001", "R-014") and d.weekday() == 0:
                wk *= 1.4                                    # Monday trading meetings
            p = np.clip(p_user * wk, 0, 0.95)
            who = np.nonzero(rng.random(len(members)) < p)[0]
            nviews = 1 + rng.poisson(0.6, len(who))
            for u, k in zip(who, nviews):
                for _ in range(k):
                    t = datetime.combine(d, datetime.min.time()) + timedelta(hours=float(np.clip(rng.normal(10, 2.5), 0, 23.9)))
                    act = "ExportReport" if rng.random() < 0.06 else "ViewReport"
                    ev.append((t, members.user_upn[u], rid, act))
    for d in cal:   # the service account: an export every ten minutes from 01:00 to 05:00
        for m in range(0, 240, 10):
            ev.append((datetime.combine(d, datetime.min.time()) + timedelta(hours=1, minutes=m), "svc-export-01@brightwater.example", "R-024", "ExportReport"))
            if m % 30 == 0:
                ev.append((datetime.combine(d, datetime.min.time()) + timedelta(hours=1, minutes=m, seconds=5), "svc-export-01@brightwater.example", "R-024", "ViewReport"))
    events = pd.DataFrame(ev, columns=["event_time", "user_upn", "report_id", "activity"]).sort_values(["event_time", "user_upn"]).reset_index(drop=True)
    events["event_id"] = [h(f"{t}|{u}|{r}|{i}") for i, (t, u, r) in enumerate(zip(events.event_time, events.user_upn, events.report_id))]
    lag_h = np.where(rng.random(len(events)) < 0.04, rng.uniform(26, 44, len(events)), rng.exponential(0.5, len(events)))
    events["ingested_at"] = events.event_time + pd.to_timedelta(lag_h, unit="h")
    name_at = {r[0]: r[1] for r in REPORTS}
    events["report_name"] = [RENAME[1] if r == RENAME[0] and t.date() >= RENAME[2] else name_at[r] for r, t in zip(events.report_id, events.event_time)]
    events["workspace"] = np.where(events.report_id == "R-031", "Supply Chain (new)", "Shared")

    # extracts: at 02:00 each day, events with event_time in the previous three days and already ingested
    ext_rows, x = [], []
    for d in days(START + timedelta(days=1), END + timedelta(days=1)):
        at = datetime.combine(d, datetime.min.time()) + timedelta(hours=2)
        if at > AS_OF:
            break
        w0, w1 = at - timedelta(hours=74), datetime.combine(d, datetime.min.time())
        eid = f"EXT-{d:%Y%m%d}"
        ext_rows.append((eid, at, w0, w1, 2 if d >= CONTRACT_CHANGE else 1))
        sel = events[(events.event_time >= w0) & (events.event_time < w1) & (events.ingested_at <= at)].copy()
        sel["extract_id"] = eid
        sel["schema_version"] = 2 if d >= CONTRACT_CHANGE else 1
        x.append(sel)
    extracts = pd.DataFrame(ext_rows, columns=["extract_id", "extracted_at", "window_start", "window_end", "schema_version"])
    act = pd.concat(x, ignore_index=True)
    v2 = act.schema_version == 2
    act.loc[v2, "activity"] = act.loc[v2, "activity"].map({"ViewReport": "ReportViewed", "ExportReport": "ReportExported"})
    act["consumption_method"] = np.where(v2, np.where(act.user_upn.str.startswith("svc"), "API", "Browser"), None)
    activity = act[["extract_id", "schema_version", "event_id", "event_time", "ingested_at", "user_upn", "report_id", "report_name",
                    "workspace", "activity", "consumption_method"]]

    reports = pd.DataFrame([(r[0], r[1] if r[0] != RENAME[0] else RENAME[1], r[2], r[3], r[4], r[5] or "2025-01-01", r[6])
                            for r in REPORTS], columns=["report_id", "report_name", "tier", "dataset_id", "owner_team", "created_on", "deleted_on"])
    reports.loc[reports.report_id == "R-007", "deleted_on"] = "2026-08-02"
    lineage = pd.DataFrame([("R-007", "R-031", "2026-08-03", "workspace migration")], columns=["old_report_id", "new_report_id", "effective_on", "reason"])
    names = pd.DataFrame([("R-014", "Weekly Sales Flash", "2025-01-01", "2026-08-31"), ("R-014", "Sales Flash", "2026-09-01", None)],
                         columns=["report_id", "report_name", "valid_from", "valid_to"])

    # ---- sell-through by retailer and day, by two routes, and SFTP arrival times
    api, sftp, arr = [], [], []
    for d in cal:
        base = 42000 * (0.75 if d.weekday() >= 5 else 1.0) * (1.6 if date(2026, 11, 20) <= d else 1.0)
        for r, share in RETAILERS:
            u = int(base * share * rng.lognormal(0, 0.08))
            a = u * 2 if r == "RT-07" and date(2026, 9, 8) <= d <= date(2026, 9, 10) else int(round(u * (1 + rng.normal(0, 0.002))))
            api.append((d, r, a, datetime.combine(d + timedelta(days=1), datetime.min.time()) + timedelta(hours=1, minutes=int(rng.integers(0, 30)))))
            if r == "RT-04" and d == date(2026, 10, 14):
                continue
            due = datetime.combine(d + timedelta(days=1), datetime.min.time()) + timedelta(hours=4)
            late = 0.0
            if r == "RT-02" and d in LATE_FILES:
                late = LATE_FILES[d]
            arrived = due - timedelta(minutes=int(rng.integers(20, 90))) + timedelta(hours=late)
            sftp.append((d, r, u, f"{r}_{d:%Y%m%d}.csv"))
            arr.append((r, d, f"{r}_{d:%Y%m%d}.csv", due, arrived))
    sellthrough_api = pd.DataFrame(api, columns=["sales_date", "retailer_id", "units", "received_at"])
    sellthrough_sftp = pd.DataFrame(sftp, columns=["sales_date", "retailer_id", "units", "file_name"])
    sftp_arrivals = pd.DataFrame(arr, columns=["retailer_id", "sales_date", "file_name", "due_at", "arrived_at"])

    # ---- pipeline runs: a refresh waits for its inputs; DS-SALES waits for every SFTP file
    last_arrival = sftp_arrivals.groupby("sales_date").arrived_at.max()
    runs = []
    for dsid, _, cadence, due_h, start_h in DATASETS:
        for d in days(START + timedelta(days=1), END + timedelta(days=1)):
            if cadence == "weekly" and d.weekday() != 0:
                continue
            start = datetime.combine(d, datetime.min.time()) + timedelta(hours=start_h, minutes=int(rng.integers(0, 20)))
            if dsid == "DS-SALES":
                start = max(start, last_arrival.get(d - timedelta(days=1), start).to_pydatetime() + timedelta(minutes=10))
            if start > AS_OF:
                continue
            wm = datetime.combine(d, datetime.min.time()) - timedelta(seconds=1)   # data through the end of the previous day
            dur = timedelta(minutes=int(rng.integers(15, 55)))
            fail = rng.random() < 0.015
            rid = f"{dsid}-{d:%Y%m%d}"
            if fail:
                runs.append((rid + "-1", dsid, start, start + dur, "failed", 0, None))
                start = start + dur + timedelta(minutes=60)
                rid = rid + "-2"
            else:
                rid = rid + "-1"
            if start + dur <= AS_OF:
                runs.append((rid, dsid, start, start + dur, "succeeded", int(rng.integers(50_000, 400_000)), wm))
    pipeline_runs = pd.DataFrame(runs, columns=["run_id", "dataset_id", "started_at", "finished_at", "status", "rows_loaded", "source_watermark"])
    datasets = pd.DataFrame([(d[0], d[1], d[2], d[3]) for d in DATASETS], columns=["dataset_id", "dataset_name", "cadence", "due_hour_utc"])

    # ---- reviews
    rv = []

    def text_for(cat):
        opts = TEXT[cat]
        return opts[rng.integers(0, len(opts))]

    def add(src, product, market, platform, version, t, stars, cat, alias=None):
        rv.append((src, product, alias, market, platform, version, t, int(stars), text_for(cat), f"reviewer_{rng.integers(1, 10**6)}"))

    def cur_version(d):
        v = VERSIONS[0][0]
        for name, rel in VERSIONS:
            if d >= rel:
                v = name
        return v

    for d in cal:
        for plat, vol in (("iOS", 9), ("Android", 11)):
            for m, w in APP_MARKETS.items():
                k = rng.poisson(vol * w)
                v = cur_version(d)
                for _ in range(k):
                    bug = plat == "Android" and v == "5.2.0"
                    r = rng.random()
                    if bug and r < 0.55:
                        cat, stars = "pairing", rng.choice([1, 2], p=[0.7, 0.3])
                    else:
                        cat = rng.choice(["praise", "sound", "battery", "ui", "login", "crash", "firmware", "pairing", "other", "subscription"],
                                         p=[0.31, 0.15, 0.08, 0.06, 0.05, 0.04, 0.04, 0.04, 0.10, 0.13] if v >= "5.1.0" else
                                           [0.40, 0.17, 0.08, 0.07, 0.05, 0.04, 0.04, 0.04, 0.11, 0.00])
                        stars = {"praise": 5, "sound": rng.choice([4, 5]), "other": rng.choice([3, 4, 5])}.get(cat, rng.choice([1, 2, 3], p=[0.3, 0.4, 0.3]))
                    add("App store" if plat == "iOS" else "Play store", "APP-CONNECT", m, plat, v, d, stars, cat)
        for pid, brand, pname, aliases, base, vol in PRODUCTS:
            for m in ("US", "UK", "DE", "JP"):
                k = rng.poisson(vol * {"US": 0.45, "UK": 0.2, "DE": 0.2, "JP": 0.15}[m])
                if pid == "P-ARC-MINI" and m == "JP" and date(2026, 11, 9) <= d <= date(2026, 11, 15):
                    k = 1 if d.weekday() in (0, 2, 4) else 0
                for _ in range(k):
                    alias = aliases[rng.integers(0, len(aliases))]
                    if pid == "P-ARC-MINI" and m == "JP" and date(2026, 11, 9) <= d <= date(2026, 11, 15):
                        stars, cat, alias = (1 if d.weekday() == 2 else 2), "sound", aliases[0]
                    else:
                        stars = int(np.clip(np.round(rng.normal(base, 0.9)), 1, 5))
                        cat = "praise" if stars >= 5 else "sound" if stars == 4 else rng.choice(["battery", "pairing", "sound", "other"])
                    add(RESELLERS[rng.integers(0, 3)], None, m, None, None, d, stars, cat, alias)
    reviews = pd.DataFrame(rv, columns=["source", "app_id", "listing_name", "market", "platform", "app_version", "review_date", "stars", "review_text", "reviewer_handle"])
    reviews["posted_at"] = pd.to_datetime(reviews.review_date) + pd.to_timedelta(rng.integers(0, 86400, len(reviews)), unit="s")
    reviews["scraped_at"] = reviews.posted_at + pd.to_timedelta(rng.uniform(1, 30, len(reviews)), unit="h")
    reviews = reviews[reviews.scraped_at <= AS_OF].reset_index(drop=True)
    reviews["review_id"] = [h(f"{s}|{p}|{i}") for i, (s, p) in enumerate(zip(reviews.source, reviews.posted_at))]
    reviews = reviews[["review_id", "source", "app_id", "listing_name", "market", "platform", "app_version", "posted_at", "scraped_at",
                       "stars", "review_text", "reviewer_handle"]]

    tables = {
        "activity_events": activity, "activity_extracts": extracts, "directory": directory, "reports": reports,
        "report_lineage": lineage, "report_names": names, "datasets": datasets, "pipeline_runs": pipeline_runs,
        "sellthrough_api": sellthrough_api, "sellthrough_sftp": sellthrough_sftp, "sftp_arrivals": sftp_arrivals, "reviews": reviews,
    }
    for name, df in tables.items():
        df.to_parquet(out / f"{name}.parquet", index=False)
    key = {
        "as_of": AS_OF.isoformat(), "contract_change": CONTRACT_CHANGE.isoformat(),
        "hot_report_missed_sla": {"report_id": "R-001", "dataset_id": "DS-SALES", "from": SALES_INCIDENT[0].isoformat(), "to": SALES_INCIDENT[1].isoformat(), "late_retailer": "RT-02", "late_file_dates": sorted(x.isoformat() for x in LATE_FILES)},
        "service_account_report": "R-024", "migrated": {"old": "R-007", "new": "R-031"}, "renamed": RENAME[0], "deleted": "R-022", "never_used": "R-025",
        "sftp_missing": {"retailer_id": "RT-04", "sales_date": "2026-10-14"},
        "api_double_count": {"retailer_id": "RT-07", "from": "2026-09-08", "to": "2026-09-10"},
        "app_bug": {"version": "5.2.0", "platform": "Android", "category": "pairing", "fixed_in": "5.2.1"},
        "new_topic": {"keyword": "subscription", "from_version": "5.1.0"},
        "weak_signal": {"product_id": "P-ARC-MINI", "market": "JP", "week": "2026-11-09"},
        "unmapped_alias": "Arc Mini (Renewed)",
        "distinct_events": int(events.event_id.nunique()),
        "rows": {k: len(v) for k, v in tables.items()},
    }
    (out / "answer_key.json").write_text(json.dumps(key, indent=1), encoding="utf-8")
    return key


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/raw")
    a = ap.parse_args()
    key = simulate(Path(a.out))
    print("wrote", ", ".join(f"{k} {v:,}" for k, v in key["rows"].items()))


if __name__ == "__main__":
    main()
