# Design decisions

**Deduplicate on the event ID, keep the first delivery.** The activity API is extracted daily with a three-day lookback
so late events are not lost; the cost is that most events arrive up to three times. Staging keeps the earliest extract's
copy and records `times_delivered`. A wider lookback would catch later events for more duplicates; the check page counts
both.

**Hash accounts in staging, with a salt.** Gold holds a 32-character key per account and directory attributes
(department, region, account type), never a name or address. The salt is a dbt var here only to show the pattern; in
production it is a secret. Department breakdowns under five viewers are suppressed, not rounded.

**Viewers and views are different measures, in different columns.** Distinct viewers are recomputed at every grain from
events (platform-wide weekly viewers are a separate mart), never added up. Repeat viewers come from a join of consecutive
weeks, not from counts.

**Service accounts are kept, flagged, and excluded by a versioned metric.** Deleting them would hide automated load on
the platform; counting them inflates one report's views by two thirds. The registry records the change as v2.

**Stable report keys.** A lineage table maps a migrated report to its successor so its history carries over. Names are
effective-dated; everything joins on ID. Deleted reports stay in the dimension with `is_live = false`.

**Map the schema change in staging, test it in gold.** Both activity vocabularies map to `view` and `export`. A
contract lists the allowed values per schema version, so an unannounced third version fails the build.

**Freshness is measured at the due time, against what was in the warehouse.** A check passes if, at its due hour, the
dataset's latest successful run had loaded data through the end of the previous day. Compliance counts checks, not days
of data, so one late morning is one miss.

**Usage sets priority.** A missed check is weighted by the report's average weekly viewers, and the cost is shown as views
that landed on stale data. This is what moves the executive scorecard above reports with the same compliance.

**Deterministic review categories.** Keyword rules in a seed, lowest priority number wins; no match is "uncategorised".
Rules are reviewable in a pull request and stable between builds. A new topic surfaces as uncategorised growth, which is
watched, instead of being absorbed by a model's nearest guess.

**Shrink sparse ratings toward a baseline.** A weekly rating is pulled toward the product's previous eight weeks with a
prior of 20 reviews. A thin week can be flagged as a weak signal but never as an incident; incidents need 30 reviews and
an interval that excludes no change.

**Reconcile two feeds of the same fact.** API and SFTP sell-through are compared per retailer-day within 1%. Breaks go to
an exception queue with an owner and age, rather than being averaged away.
