# Report spec (Power BI or Tableau)

The static dashboards are the reference build. A BI version over the same gold marts follows this spec.

| Page | Visuals | Measures | Filters |
|---|---|---|---|
| Overview | Five KPI cards; SLA priority bar; app rating by version | Distinct Viewers, SLA Compliance, Average Stars with Review Count | Date (week) |
| Adoption | Viewers by report (bar); platform viewers and coverage (line); repeat rate; v1 against v2 views; department matrix | Distinct Viewers, Repeat Viewers, Member Views, All Views (v1), Report Coverage, Distinct Viewers (Safe) | Tier, department, week |
| Reliability | SLA priority table; report health timeline; source-file timeliness; dataset x week matrix; exception queue | SLA Compliance, Missed Checks | Dataset, report, date |
| App feedback | Stars by version and platform; low-star share; category share (stacked); uncategorised share | Average Stars, Low Star Share, Review Count | Platform, version |
| Product ratings | Own against competitor; weekly rating with shrunk line; star distribution; flagged weeks | Average Stars (Shown), Review Count | Product, market, reseller |

Rules: viewers and views never share an axis; every rating visual shows its review count in the label or tooltip;
department visuals use the safe measure; row-level security on department if the model is shared beyond the data team.
