# Runbook

For whoever is on call for the BI platform. Every alert below comes from a gold mart and appears on the dashboards.

## 1. A freshness check failed

1. **Is it a priority?** Open Reliability, *SLA priority*. A report in the top five, or any Executive-tier report, is an
   incident; the rest go to the backlog with the dataset owner.
2. **What is late?** `rpt_freshness_checks` shows the dataset, the due time and when it became current. Check
   `fct_pipeline_runs` for failed runs and `rpt_sftp_timeliness` for late source files.
3. **Tell users before they ask.** Post the expected time on the report's banner and the platform channel. Views while
   stale are counted in `rpt_report_health`; the number goes in the incident note.
4. **Fix the cause.** A failed run: rerun. A late retailer file: decide with the dataset owner whether to refresh without
   it (with a completeness note) or wait.
5. **Close.** Record start, end, views on stale data and cause. Repeated misses from the same source go to the
   supplier-performance review.

## 2. A sell-through exception opened

1. Open Reliability, *exception queue*. Each row has a type, units at stake, owner and age.
2. **mismatch:** compare raw API and SFTP rows for the retailer-day. An exact 2x means duplicated API pages; ask the
   connector owner to replay the day.
3. **missing_sftp / missing_api:** check the arrival log; request a resend.
4. An exception older than five days is escalated to the data-platform lead.

## 3. Views dropped or jumped

1. Check *Data checks* for a schema change, duplicate surge or late-event surge first.
2. Compare v1 and v2 views (`rpt_metric_versions`): a jump only in v1 is a service account.
3. A report that disappeared may have been migrated or renamed: check `stg_report_lineage` and `stg_report_names`.

## 4. A rating moved

1. Read the signal, not the average. `actionable` opens a ticket with the product or app team, with review count,
   interval and top categories. `weak signal` is watched for two more weeks. `noise` needs nothing.
2. If "uncategorised" grows, read a sample and add a rule to `dbt/seeds/review_rules.csv` in a pull request.

## 5. The build failed

`make ci` runs contracts, dbt tests and pytest. A contract failure names the table and column: the source changed
shape, so update the contract and staging together. A dbt test failure names the rule; never relax a test to pass a build.
