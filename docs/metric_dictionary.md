# Metric dictionary

Versioned definitions live in `dbt/seeds/metric_registry.csv` and are shown on the Data checks page. A change of
definition is a new version with an effective date, never a silent edit.

| Metric | Definition | Grain | Never |
|---|---|---|---|
| **Report views (v2)** | View events on a report by member accounts | report x period | mixed with viewers in one total |
| Report views (v1, retired) | View events by any account, including service accounts | report x period | used after 1 Jul 2026 |
| **Distinct active viewers** | Distinct member accounts with at least one view in the period | report x period, or platform x period | summed across reports or periods |
| **Weekly repeat viewers** | Member accounts that viewed the report in the week and in the week before | report x week | greater than distinct viewers |
| **Report coverage** | Live catalogued reports with at least one member view in the period, over live catalogued reports | platform x week | counts deleted reports in the denominator |
| **Freshness SLA compliance** | Scheduled checks at which the dataset held data through the end of the previous day, over scheduled checks | dataset or report x 90 days | measured in days of data instead of checks |
| **Views on stale data** | Member views of a report between its due time and the moment its dataset became current, on a missed check | report x check | counted on a passed check |
| **SLA priority** | Average weekly viewers x missed checks, last 90 days | report | ranked on delay length alone |
| **Average star rating** | Mean stars over reviews in the period | product or app version x period | shown without its review count |
| **Shrunk weekly rating** | (reviews x average + 20 x baseline) / (reviews + 20); baseline = previous eight weeks | product x market x week | compared without volume |
| **Rating signal, product week** | Raw drop of 0.4+ stars against the baseline: `actionable` with 30+ reviews; with fewer, `weak signal` if still 0.25+ below after shrinking, else `noise`. Otherwise `no change` or `no baseline` | product x market x week | escalated when weak |
| **Rating signal, app version** | Drop of 0.4+ stars against the previous version on the same platform: `actionable` with 30+ reviews and a 95% interval that excludes no change, else `weak signal` | app version x platform | compared across platforms |
| **Sell-through exception** | API and SFTP units for one retailer-day differ by more than 1%, or one source is missing | retailer x sales date | netted across retailers |

Time zone: all timestamps UTC. As-of time: 23 November 2026, 08:00.
