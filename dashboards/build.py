"""Write the six dashboard pages and data.js. Run export.py first.

Usage: python dashboards/build.py [--data dashboards/site/data.json] [--site dashboards/site]
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ECHARTS = "https://cdn.jsdelivr.net/npm/echarts@5.5.1/dist/echarts.min.js"
REPO = "https://github.com/Saigwe/data-product-observability"

PAGES = [
    ("index.html", "overview", "Overview"),
    ("adoption.html", "adoption", "Adoption"),
    ("reliability.html", "reliability", "Reliability"),
    ("feedback.html", "feedback", "App feedback"),
    ("ratings.html", "ratings", "Product ratings"),
    ("checks.html", "checks", "Data checks"),
]


def card(cid: str, title: str, sub: str, src: str = "", wide: bool = False, tall: bool = False, chart: bool = True,
         extra: str = "") -> str:
    return f'''
    <section class="card{' wide' if wide else ''}" id="{cid}">
      <header><div><h2>{title}</h2><p class="sub">{sub}</p></div>{'<button class="tbl-btn" type="button" aria-pressed="false">Table</button>' if chart else ''}</header>
      {extra}{f'<div class="chart{" tall" if tall else ""}" role="img" aria-label="{title}"></div>' if chart else ''}
      <div class="table-view" hidden></div>
      <p class="src">{src or "Source: dbt gold marts on DuckDB"}</p>
    </section>'''


def scope(text: str) -> str:
    return f'\n  <div class="filters"><span class="scope">{text}</span></div>'


GRID_OPEN, GRID_CLOSE = '\n  <div class="tiles" id="tiles"></div>\n  <div class="grid">', '\n  </div>'

BODIES = {
    "overview": ("Data products: used, healthy, and what users say",
                 "Which reports people actually use, whether the data behind them was fresh when they looked, and what customers are reporting about the products.",
                 scope("Brightwater Electronics (fictional). Activity, pipeline runs and reviews from May to 22 November 2026; as of 23 November, 08:00 UTC. "
                       "Views and viewers are member accounts only. Simulated SLA and adoption metrics. Synthetic data.") + GRID_OPEN +
                 card("ov-stories", "An incident, a real regression and a weak signal", "Each links to the page with the evidence.", "Computed from every page",
                      wide=True, chart=False, extra='<ul class="insights" id="insights"></ul>') +
                 card("ov-priority", "Where a missed SLA hurts most", "Priority score: average weekly viewers x missed freshness checks, last 90 days") +
                 card("ov-app", "App rating by version, Android and iOS", "Average stars by version; intervals and review counts in the table") +
                 GRID_CLOSE),
    "adoption": ("Adoption",
                 "Which reports people use, how often they come back, and what counts as a view.",
                 scope("Viewers: distinct member accounts, never summed across reports or weeks. Views: view events by member accounts "
                       "(report_views v2). Service accounts are kept but counted separately. Departments with fewer than five viewers are suppressed.") + GRID_OPEN +
                 card("ad-top", "Average weekly viewers, last four complete weeks", "Live reports, by tier", wide=True, tall=True) +
                 card("ad-overall", "Platform-wide weekly viewers and report coverage", "Distinct viewers across all reports; coverage = live reports viewed that week") +
                 card("ad-repeat", "Weekly repeat rate, top reports", "Viewers who also viewed the week before") +
                 card("ad-metricv", "What excluding service accounts changes", "Views in the last 28 days under report_views v1 (all accounts) and v2 (members)") +
                 card("ad-dept", "Viewers by department, last 28 days", "Suppressed below five viewers", chart=False, extra='<div id="dept" class="table-view"></div>') +
                 GRID_CLOSE),
    "reliability": ("Reliability",
                    "Was each dataset fresh at its due time, which missed checks matter, and what broke upstream.",
                    scope("A check passes if the dataset holds data through the end of the previous day at its due hour (UTC). Priority = average "
                          "weekly viewers x missed checks, last 90 days. Sell-through arrives by API and by SFTP file and is reconciled daily within 1%.") + GRID_OPEN +
                 card("rl-priority", "SLA priority by report", "Missed checks and views that landed on stale data, last 90 days", wide=True, chart=False,
                      extra='<div id="priority" class="table-view"></div>') +
                 card("rl-incident", "Executive Sales Scorecard in October: hours stale at 07:00", "Bars: hours after the due time until the data was current. Line: views while stale") +
                 card("rl-sftp", "Root cause: the largest retailer's SFTP file", "Hours after the 04:00 due time, by sales date") +
                 card("rl-matrix", "Freshness by dataset and week", "Missed checks per week", wide=True) +
                 card("rl-queue", "Sell-through exception queue", "API against SFTP, outside 1% or missing", wide=True, chart=False, extra='<div id="queue" class="table-view"></div>') +
                 GRID_CLOSE),
    "feedback": ("App feedback",
                 "Reviews of the companion app by version, platform and category: what changed, and is it real?",
                 scope("Categories come from deterministic keyword rules (dbt/seeds/review_rules.csv); a review no rule matches is "
                       "'uncategorised', so a new topic shows up as uncategorised growth. Intervals are 95%.") + GRID_OPEN +
                 card("fb-version", "Average stars by version", "Android and iOS, 95% interval in the table") +
                 card("fb-low", "Share of one- and two-star reviews", "By version and platform") +
                 card("fb-cats", "What Android reviews are about", "Share of reviews by category and version", wide=True) +
                 card("fb-uncat", "Uncategorised share by version", "A rise means a topic the rules do not know yet") +
                 card("fb-table", "Version summary", "Change against the previous version on the same platform", chart=False, extra='<div id="versions" class="table-view"></div>') +
                 GRID_CLOSE),
    "ratings": ("Product ratings",
                "Reseller ratings for own and competitor products, always with the number of reviews behind them.",
                scope("Ratings from three resellers, mapped from listing names to products (an unknown listing stays unmapped). Weekly "
                      "ratings are shrunk toward the previous eight weeks with a prior of 20 reviews; fewer than 30 reviews is never an incident.") + GRID_OPEN +
                card("rt-compare", "Own against comparable competitor products", "Average stars; review count in brackets", wide=True) +
                card("rt-weak", "Arc Speaker Mini, Japan: weekly rating", "Raw average, shrunk average and review count") +
                card("rt-dist", "Star distribution by product", "Share of reviews at each star") +
                card("rt-signals", "Weeks flagged", "Raw drop of 0.4 stars or more", wide=True, chart=False, extra='<div id="signals" class="table-view"></div>') +
                GRID_CLOSE),
    "checks": ("Data checks",
               "What the pipeline found and handled, the metric registry, and the rules enforced on every build.",
               scope("dbt staging and tests, source contracts and pytest run on every push.") + GRID_OPEN +
               card("ck-list", "Checks on the latest build", "From rpt_data_checks", wide=True, chart=False, extra='<div id="checks"></div>') +
               card("ck-contract", "Activity API schema change, 15 September", "Daily views: mapped in staging against a filter on the old activity name") +
               card("ck-registry", "Metric registry", "Versioned definitions (dbt/seeds/metric_registry.csv)", chart=False, extra='<div id="registry" class="table-view"></div>') +
               card("ck-rules", "Rules this warehouse enforces", "Where each is tested", wide=True, chart=False, extra='<div id="rules"></div>') +
               GRID_CLOSE),
}


def ver(site: Path) -> str:
    h = hashlib.sha1()
    for f in ("assets/style.css", "assets/charts.js", "assets/pages.js", "data.js"):
        h.update((site / f).read_bytes())
    return h.hexdigest()[:10]


def page(key: str, v: str = "") -> str:
    title, lede, body = BODIES[key]
    nav = "".join(f'<a href="{f}"{" aria-current=page" if k == key else ""}>{label}</a>' for f, k, label in PAGES)
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title.replace("&amp;", "&")} · Data-product observability</title>
<meta name="description" content="Report adoption, freshness SLAs prioritised by usage, cross-source reconciliation and product feedback for a fictional company, on synthetic data.">
<link rel="stylesheet" href="assets/style.css?v={v}">
<script src="{ECHARTS}" defer></script>
<script src="assets/charts.js?v={v}" defer></script>
<script src="data.js?v={v}" defer></script>
<script src="assets/pages.js?v={v}" defer></script>
</head>
<body class="viz-root" data-page="{key}">
<div class="top"><div class="wrap">
  <div class="brand">Brightwater Electronics <span>· data-product observability · synthetic data</span></div>
  <nav class="tabs" aria-label="Dashboards">{nav}</nav>
  <button class="theme-btn" type="button">Dark mode</button>
</div></div>
<main class="wrap">
  <div class="page-head"><h1>{title}</h1><p>{lede}</p></div>
{body}
  <p class="footnote">Brightwater Electronics, its reports, accounts, retailers, products, competitors and every number here are invented.
  Demo results, not any company's figures. Built from dbt marts on DuckDB, rebuilt by CI on every change.
  Code: <a href="{REPO}">data-product-observability</a>. Built by <a href="https://saigwe.github.io">Stanley Igwe</a>.</p>
</main>
</body>
</html>
'''


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(HERE / "site" / "data.json"))
    ap.add_argument("--site", default=str(HERE / "site"))
    a = ap.parse_args()
    site = Path(a.site)
    data = json.loads(Path(a.data).read_text(encoding="utf-8"))
    (site / "data.js").write_text("window.DASH = " + json.dumps(data, separators=(",", ":")) + ";\n", encoding="utf-8")
    v = ver(site)
    for fname, key, _ in PAGES:
        (site / fname).write_text(page(key, v), encoding="utf-8", newline="\n")
    print(f"wrote {len(PAGES)} pages to {site}")


if __name__ == "__main__":
    main()
