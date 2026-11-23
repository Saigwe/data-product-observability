/* Page renderers. Data: window.DASH (data.js, written by dashboards/build.py). */
(function () {
  "use strict";
  const D = window.DASH;
  const { line, bar, heatmap, card, table, fmt, esc } = window.Viz;
  const uniq = (a) => [...new Set(a)];
  const day = (s) => new Date(s.slice(0, 10) + "T00:00:00").toLocaleDateString("en-GB", { day: "numeric", month: "short" });
  const dayY = (s) => new Date(s.slice(0, 10) + "T00:00:00").toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
  const mon = (s) => new Date(s.slice(0, 10) + "T00:00:00").toLocaleDateString("en-GB", { month: "short", year: "2-digit" });
  const RN = Object.fromEntries(D.adoption.map((r) => [r.report_key, r.report_name]));
  const PN = Object.fromEntries(D.products.map((p) => [p.product_id, p.product_name]));
  const live = D.adoption.filter((r) => r.is_live);
  const appv = (v, p) => D.app.find((r) => r.app_version === v && r.platform === p) || {};
  const stars = (v) => (v == null ? "–" : Number(v).toFixed(2));

  function tiles(list) {
    const el = document.getElementById("tiles");
    if (!el) return;
    el.replaceChildren(...list.map((t) => {
      const d = document.createElement("div"); d.className = "tile";
      const k = document.createElement("div"); k.className = "k"; k.textContent = t.k;
      const v = document.createElement("div"); v.className = "v"; v.textContent = t.v;
      d.append(k, v);
      if (t.d) { const s = document.createElement("div"); s.className = "d"; s.textContent = t.d; d.append(s); }
      return d;
    }));
  }
  const insights = (items) => {
    document.getElementById("insights").innerHTML = items.map(([cls, label, text, href, where]) =>
      `<li><span class="status ${cls}"><i aria-hidden="true">${cls === "good" ? "✓" : "!"}</i>${label}</span><span>${text} <a class="where" href="${href}">${where} →</a></span></li>`).join("");
  };

  /* ---------- Overview ---------- */
  function overview() {
    const top = D.priority[0], bug = D.app.find((r) => r.signal === "actionable"), prev = D.app.find((r) => r.platform === bug.platform && r.app_version < bug.app_version && D.app.filter((x) => x.platform === bug.platform && x.app_version < bug.app_version).every((x) => x.app_version <= r.app_version));
    const weak = D.ratings.find((r) => r.product_id === "P-ARC-MINI" && r.market === "JP" && r.signal === "weak signal");
    const ov = D.overall[D.overall.length - 1];
    const sales = D.checks_fresh.filter((r) => r.dataset_id === top.dataset_id && !r.is_fresh && r.check_date >= "2026-10-01" && r.check_date < "2026-11-01");
    const late = D.sftp.filter((r) => r.is_late);
    tiles([
      { k: "Distinct viewers last week", v: fmt.int(ov.distinct_viewers), d: `${fmt.pct(0)(ov.report_coverage)} of live reports opened` },
      { k: "Most-used report", v: top.report_name, d: `${fmt.int(top.avg_weekly_viewers)} viewers a week` },
      { k: "Its freshness SLA, 90 days", v: fmt.pct(0)(top.sla_compliance), d: `${top.missed} checks missed` },
      { k: `App ${bug.app_version} on ${bug.platform}`, v: stars(bug.avg_stars) + " ★", d: `${fmt.int(bug.reviews)} reviews, ${stars(bug.change_vs_previous)} vs previous` },
      { k: "Arc Speaker Mini, Japan", v: stars(weak.avg_stars) + " ★", d: `${weak.reviews} reviews: a weak signal` },
    ]);
    insights([
      ["critical", "Incident", `<b>${esc(top.report_name)}, the most-used report (${fmt.int(top.avg_weekly_viewers)} viewers a week), was stale at its 07:00 check on ${sales.length} days in October.</b> ${fmt.int(top.views_on_stale_data)} views in the last 90 days landed before the data was current. The cause is upstream: the largest retailer's SFTP file arrived after its 04:00 due time on ${late.length} days. Fix the file delivery first; it ranks first because of its usage, not the length of the delay.`, "reliability.html", "Reliability"],
      ["critical", "Act", `<b>App ${bug.app_version} broke Bluetooth pairing on ${bug.platform}.</b> ${fmt.int(bug.reviews)} reviews average ${stars(bug.avg_stars)} stars, ${stars(-bug.change_vs_previous)} below ${esc(prev ? prev.app_version : "the previous version")}, and ${fmt.pct(0)(bug.pairing_share)} mention pairing. The interval excludes no change, so it is actionable. ${esc(appv("5.2.1", bug.platform).app_version || "")} recovered to ${stars(appv("5.2.1", bug.platform).avg_stars)}.`, "feedback.html", "App feedback"],
      ["warning", "Weak signal", `<b>Arc Speaker Mini in Japan fell to ${stars(weak.avg_stars)} stars in the week of ${day(weak.week_start)}, on ${weak.reviews} reviews.</b> Shrunk toward its recent baseline (${stars(weak.baseline_stars)}) it is ${stars(weak.shrunk_stars)}. Watch the next weeks before acting; do not open an incident on three reviews.`, "ratings.html", "Product ratings"],
      ["warning", "Read with care", `<b>Uncategorised app reviews rose from version 5.1.0.</b> Reading them shows a new complaint about a subscription plan that no category rule covers yet; add a rule rather than letting it hide in 'other'.`, "feedback.html", "App feedback"],
      ["good", "Checked", `<b>Counts are defined, not assumed.</b> Viewers are distinct accounts, never summed; one service account's ${fmt.int(D.metricv[0].views_v1 - D.metricv[0].views_v2)} automated views are excluded from v2; the API's schema change on 15 September would have zeroed views under a naive filter.`, "checks.html", "Data checks"],
    ]);
    const pr = D.priority.slice(0, 10);
    card("ov-priority", (el) => bar(el, { horizontal: true, x: pr.map((r) => r.report_name), yFmt: fmt.int, series: [{ name: "Priority (viewers x missed checks)", data: pr.map((r) => r.priority_score), colors: pr.map((r, i) => (i === 0 ? 1 : 0)), labels: true }] }),
      { cols: [{ key: "report_name", label: "Report" }, { key: "avg_weekly_viewers", label: "Weekly viewers", fmt: fmt.int }, { key: "missed", label: "Missed" }, { key: "sla_compliance", label: "SLA", fmt: fmt.pct(1) }, { key: "priority_score", label: "Priority", fmt: fmt.int }], rows: D.priority });
    const vs = uniq(D.app.map((r) => r.app_version)).sort();
    card("ov-app", (el) => bar(el, { x: vs, yFmt: (v) => Number(v).toFixed(1), yMin: 1, yMax: 5, series: ["Android", "iOS"].map((p, i) => ({ name: p, data: vs.map((v) => appv(v, p).avg_stars ?? null), color: i })) }),
      { cols: [{ key: "app_version", label: "Version" }, { key: "platform", label: "Platform" }, { key: "reviews", label: "Reviews", fmt: fmt.int }, { key: "avg_stars", label: "Stars", fmt: stars }, { key: "ci_low", label: "95% low", fmt: stars }, { key: "ci_high", label: "95% high", fmt: stars }, { key: "signal", label: "Signal" }], rows: D.app });
  }

  /* ---------- Adoption ---------- */
  function adoption() {
    const ov = D.overall[D.overall.length - 1];
    const svc = D.metricv[0];
    tiles([
      { k: "Distinct viewers, last week", v: fmt.int(ov.distinct_viewers), d: "across all reports, counted once" },
      { k: "Member views, last week", v: fmt.int(ov.member_views), d: "views, not viewers" },
      { k: "Report coverage", v: fmt.pct(0)(ov.report_coverage), d: `${ov.reports_viewed} of ${ov.live_reports} live reports opened` },
      { k: "Views removed by excluding services", v: fmt.pct(0)(svc.share_removed_by_v2), d: `of ${esc(svc.report_name)}'s views` },
    ]);
    const tiers = { Executive: 1, Operational: 0, "Self-serve": 2 };
    const lv = live.slice().sort((a, b) => b.avg_weekly_viewers - a.avg_weekly_viewers);
    card("ad-top", (el) => bar(el, { horizontal: true, x: lv.map((r) => r.report_name), yFmt: fmt.int, barMax: 14, gap: "20%", series: [{ name: "Average weekly viewers", data: lv.map((r) => r.avg_weekly_viewers), colors: lv.map((r) => tiers[r.tier]), labels: true }] }),
      { cols: [{ key: "report_name", label: "Report" }, { key: "tier", label: "Tier" }, { key: "avg_weekly_viewers", label: "Weekly viewers", fmt: fmt.int }, { key: "viewers_28d", label: "Viewers 28d", fmt: fmt.int }, { key: "views_28d", label: "Views 28d", fmt: fmt.int }, { key: "repeat_rate", label: "Repeat", fmt: fmt.pct(0) }, { key: "is_active", label: "Active", fmt: (v) => (v ? "yes" : "no") }], rows: lv });
    const wk = D.overall.map((r) => r.week_start);
    card("ad-overall", (el) => line(el, { x: wk, xFmt: day, yFmt: fmt.int, yMin: 0, series: [{ name: "Distinct viewers", data: D.overall.map((r) => r.distinct_viewers), color: 0 }] }),
      { cols: [{ key: "week_start", label: "Week" }, { key: "distinct_viewers", label: "Viewers", fmt: fmt.int }, { key: "member_views", label: "Views", fmt: fmt.int }, { key: "reports_viewed", label: "Reports viewed" }, { key: "live_reports", label: "Live" }, { key: "report_coverage", label: "Coverage", fmt: fmt.pct(0) }], rows: D.overall });
    const topk = lv.slice(0, 4).map((r) => r.report_key);
    const ww = uniq(D.weekly.map((r) => r.week_start)).sort();
    card("ad-repeat", (el) => line(el, { x: ww, xFmt: day, yFmt: fmt.pct(0), yMin: 0, yMax: 1, series: topk.map((k, i) => ({ name: RN[k], data: ww.map((w) => { const r = D.weekly.find((x) => x.report_key === k && x.week_start === w); return r && r.distinct_viewers ? r.repeat_viewers / r.distinct_viewers : null; }), color: i })) }),
      { cols: [{ key: "week_start", label: "Week" }, { key: "report_key", label: "Report", fmt: (k) => RN[k] }, { key: "distinct_viewers", label: "Viewers" }, { key: "repeat_viewers", label: "Repeat" }], rows: D.weekly.filter((r) => topk.includes(r.report_key)) });
    const mv = D.metricv.filter((r) => r.share_removed_by_v2 > 0).concat(D.metricv.filter((r) => r.share_removed_by_v2 === 0).slice(0, 3));
    card("ad-metricv", (el) => bar(el, { horizontal: true, x: mv.map((r) => r.report_name), yFmt: fmt.int, series: [{ name: "v1: all accounts", data: mv.map((r) => r.views_v1), color: 1 }, { name: "v2: member accounts", data: mv.map((r) => r.views_v2), color: 0 }] }),
      { cols: [{ key: "report_name", label: "Report" }, { key: "views_v1", label: "v1", fmt: fmt.int }, { key: "views_v2", label: "v2", fmt: fmt.int }, { key: "share_removed_by_v2", label: "Removed", fmt: fmt.pct(0) }], rows: D.metricv });
    const depts = uniq(D.dept.map((r) => r.department)).sort();
    const rowsD = lv.filter((r) => r.is_active).map((r) => Object.assign({ report: r.report_name }, Object.fromEntries(depts.map((d) => { const x = D.dept.find((y) => y.report_key === r.report_key && y.department === d); return [d, x ? (x.is_suppressed ? "<5" : fmt.int(x.viewers_28d)) : ""]; }))));
    table(document.getElementById("dept"), [{ key: "report", label: "Report" }].concat(depts.map((d) => ({ key: d, label: d }))), rowsD);
  }

  /* ---------- Reliability ---------- */
  function reliability() {
    const top = D.priority[0], q = D.queue;
    tiles([
      { k: "Top priority", v: top.report_name, d: `${top.missed} missed checks, ${fmt.int(top.views_on_stale_data)} views on stale data` },
      { k: "Checks missed, all datasets", v: String(D.checks_fresh.filter((r) => !r.is_fresh).length), d: "of " + fmt.int(D.checks_fresh.length) + " since May" },
      { k: "Late files from the largest retailer", v: String(D.sftp.filter((r) => r.is_late).length), d: "in October" },
      { k: "Open sell-through exceptions", v: String(q.length), d: fmt.int(q.reduce((a, r) => a + r.units_at_stake, 0)) + " units at stake" },
    ]);
    table(document.getElementById("priority"), [{ key: "priority_rank", label: "#" }, { key: "report_name", label: "Report" }, { key: "tier", label: "Tier" }, { key: "dataset_id", label: "Dataset" },
      { key: "avg_weekly_viewers", label: "Weekly viewers", fmt: fmt.int }, { key: "missed", label: "Missed checks" }, { key: "sla_compliance", label: "SLA", fmt: fmt.pct(1) },
      { key: "views_on_stale_data", label: "Views on stale data", fmt: fmt.int }, { key: "priority_score", label: "Priority", fmt: fmt.int }], D.priority.filter((r) => r.missed > 0));
    const h = D.health;
    card("rl-incident", (el) => bar(el, { x: h.map((r) => r.check_date), xFmt: day, yFmt: (v) => fmt.num(1)(v), series: [
      { name: "Hours stale after 07:00", data: h.map((r) => r.hours_stale), color: 1 },
      { name: "Views while stale", data: h.map((r) => r.views_on_stale_data / 10), color: 0 }] }),
      { cols: [{ key: "check_date", label: "Date" }, { key: "is_fresh", label: "Fresh at 07:00", fmt: (v) => (v ? "yes" : "no") }, { key: "fresh_at", label: "Current from" }, { key: "hours_stale", label: "Hours stale", fmt: fmt.num(1) }, { key: "views_on_stale_data", label: "Views while stale", fmt: fmt.int }, { key: "viewers_on_stale_data", label: "Viewers while stale", fmt: fmt.int }], rows: h });
    card("rl-sftp", (el) => bar(el, { x: D.sftp.map((r) => r.sales_date), xFmt: day, yFmt: (v) => fmt.num(1)(v) + " h", series: [{ name: "Hours after due", data: D.sftp.map((r) => r.hours_after_due), colors: D.sftp.map((r) => (r.is_late ? 1 : 0)) }] }),
      { cols: [{ key: "sales_date", label: "Sales date" }, { key: "due_at", label: "Due" }, { key: "arrived_at", label: "Arrived" }, { key: "hours_after_due", label: "Hours after due", fmt: fmt.num(1) }], rows: D.sftp });
    const ds = D.datasets.map((r) => r.dataset_id);
    const weeks = uniq(D.checks_fresh.map((r) => { const d = new Date(r.check_date + "T00:00:00"); d.setDate(d.getDate() - ((d.getDay() + 6) % 7)); return d.toISOString().slice(0, 10); })).sort();
    const wkOf = (s) => { const d = new Date(s + "T00:00:00"); d.setDate(d.getDate() - ((d.getDay() + 6) % 7)); return d.toISOString().slice(0, 10); };
    const cells = [];
    ds.forEach((d, yi) => weeks.forEach((w, xi) => cells.push([xi, yi, D.checks_fresh.filter((r) => r.dataset_id === d && wkOf(r.check_date) === w && !r.is_fresh).length])));
    card("rl-matrix", (el) => heatmap(el, { x: weeks, y: ds, cells, min: 0, max: 5, fmt: (v) => fmt.int(v) + " missed", xLabel: day, yLabel: (v) => v }),
      { cols: [{ key: "dataset_id", label: "Dataset" }, { key: "check_date", label: "Check date" }, { key: "check_at", label: "Due" }, { key: "fresh_at", label: "Current from" }, { key: "failed_runs", label: "Failed runs" }], rows: D.checks_fresh.filter((r) => !r.is_fresh) });
    table(document.getElementById("queue"), [{ key: "exception_id", label: "Exception" }, { key: "retailer_id", label: "Retailer" }, { key: "sales_date", label: "Sales date" }, { key: "exception_type", label: "Type" },
      { key: "api_units", label: "API", fmt: fmt.int }, { key: "sftp_units", label: "SFTP", fmt: fmt.int }, { key: "diff_pct", label: "Difference", fmt: fmt.rel(0) }, { key: "units_at_stake", label: "Units at stake", fmt: fmt.int },
      { key: "age_days", label: "Age (days)" }, { key: "owner", label: "Owner" }], q);
  }

  /* ---------- App feedback ---------- */
  function feedback() {
    const bug = D.app.find((r) => r.signal === "actionable");
    const vs = uniq(D.app.map((r) => r.app_version)).sort();
    tiles([
      { k: `${bug.platform} ${bug.app_version}`, v: stars(bug.avg_stars) + " ★", d: `${stars(bug.change_vs_previous)} vs previous, ${fmt.int(bug.reviews)} reviews` },
      { k: "Mention pairing", v: fmt.pct(0)(bug.pairing_share), d: `against ${fmt.pct(0)(D.app.filter((r) => r !== bug).reduce((a, r) => a + r.pairing_share * r.reviews, 0) / D.app.filter((r) => r !== bug).reduce((a, r) => a + r.reviews, 0))} in other versions` },
      { k: `${bug.platform} 5.2.1`, v: stars(appv("5.2.1", bug.platform).avg_stars) + " ★", d: "the fix" },
      { k: "Uncategorised, 5.1.0 on", v: fmt.pct(0)(D.cats.filter((r) => r.app_version >= "5.1.0" && r.category === "uncategorised").reduce((a, r) => a + r.reviews, 0) / D.cats.filter((r) => r.app_version >= "5.1.0").reduce((a, r) => a + r.reviews, 0)), d: "a topic the rules do not know" },
    ]);
    card("fb-version", (el) => line(el, { x: vs, yFmt: (v) => Number(v).toFixed(1), yMin: 1, yMax: 5, series: ["Android", "iOS"].map((p, i) => ({ name: p, data: vs.map((v) => appv(v, p).avg_stars ?? null), color: i })) }),
      { cols: [{ key: "app_version", label: "Version" }, { key: "platform", label: "Platform" }, { key: "reviews", label: "Reviews", fmt: fmt.int }, { key: "avg_stars", label: "Stars", fmt: stars }, { key: "ci_low", label: "95% low", fmt: stars }, { key: "ci_high", label: "95% high", fmt: stars }], rows: D.app });
    card("fb-low", (el) => bar(el, { x: vs, yFmt: fmt.pct(0), series: ["Android", "iOS"].map((p, i) => ({ name: p, data: vs.map((v) => appv(v, p).low_star_share ?? null), color: i })) }),
      { cols: [{ key: "app_version", label: "Version" }, { key: "platform", label: "Platform" }, { key: "low_star_share", label: "1-2 stars", fmt: fmt.pct(1) }], rows: D.app });
    const groups = [["Pairing", ["pairing"], 1], ["Other complaints", ["crash", "login", "firmware", "battery", "ui", "sound"], "--text-muted"], ["Praise", ["praise"], 0], ["Uncategorised", ["uncategorised"], 3]];
    const and = D.cats.filter((r) => r.platform === "Android");
    card("fb-cats", (el) => bar(el, { x: vs, yFmt: fmt.pct(0), yMax: 1, stack: true, series: groups.map(([name, cs, color]) => ({ name, color, data: vs.map((v) => and.filter((r) => r.app_version === v && cs.includes(r.category)).reduce((a, r) => a + r.share, 0)) })) }),
      { cols: [{ key: "app_version", label: "Version" }, { key: "category", label: "Category" }, { key: "reviews", label: "Reviews", fmt: fmt.int }, { key: "share", label: "Share", fmt: fmt.pct(1) }], rows: and });
    card("fb-uncat", (el) => line(el, { x: vs, yFmt: fmt.pct(0), yMin: 0, series: ["Android", "iOS"].map((p, i) => ({ name: p, data: vs.map((v) => appv(v, p).uncategorised_share ?? null), color: i })) }),
      { cols: [{ key: "app_version", label: "Version" }, { key: "platform", label: "Platform" }, { key: "uncategorised_share", label: "Uncategorised", fmt: fmt.pct(1) }], rows: D.app });
    table(document.getElementById("versions"), [{ key: "platform", label: "Platform" }, { key: "app_version", label: "Version" }, { key: "first_review", label: "From" }, { key: "reviews", label: "Reviews", fmt: fmt.int },
      { key: "avg_stars", label: "Stars", fmt: stars }, { key: "change_vs_previous", label: "Change", fmt: (v) => (v == null ? "–" : (v >= 0 ? "+" : "") + v.toFixed(2)) }, { key: "pairing_share", label: "Pairing", fmt: fmt.pct(0) }, { key: "signal", label: "Signal" }], D.app);
  }

  /* ---------- Product ratings ---------- */
  function ratings() {
    const weak = D.ratings.filter((r) => r.product_id === "P-ARC-MINI" && r.market === "JP");
    const w = weak.find((r) => r.signal === "weak signal");
    const own = D.products.filter((p) => p.brand === "Brightwater"), comp = D.products.filter((p) => p.brand !== "Brightwater");
    tiles([
      { k: "Arc Speaker Mini, Japan", v: stars(w.avg_stars) + " ★", d: `${w.reviews} reviews in the week of ${day(w.week_start)}` },
      { k: "Shrunk toward its baseline", v: stars(w.shrunk_stars) + " ★", d: `baseline ${stars(w.baseline_stars)}` },
      { k: "Own products", v: stars(own.reduce((a, p) => a + p.avg_stars * p.reviews, 0) / own.reduce((a, p) => a + p.reviews, 0)) + " ★", d: fmt.int(own.reduce((a, p) => a + p.reviews, 0)) + " reviews" },
      { k: "Competitors", v: stars(comp.reduce((a, p) => a + p.avg_stars * p.reviews, 0) / comp.reduce((a, p) => a + p.reviews, 0)) + " ★", d: fmt.int(comp.reduce((a, p) => a + p.reviews, 0)) + " reviews" },
    ]);
    const ps = D.products;
    card("rt-compare", (el) => bar(el, { horizontal: true, x: ps.map((p) => `${p.product_name} (${fmt.int(p.reviews)})`), yFmt: (v) => Number(v).toFixed(2), series: [{ name: "Average stars", data: ps.map((p) => p.avg_stars), colors: ps.map((p) => (p.brand === "Brightwater" ? 0 : 1)), labels: true }] }),
      { cols: [{ key: "product_name", label: "Product" }, { key: "brand", label: "Brand" }, { key: "comparable_group", label: "Group" }, { key: "reviews", label: "Reviews", fmt: fmt.int }, { key: "avg_stars", label: "Stars", fmt: stars }], rows: ps });
    card("rt-weak", (el) => line(el, { x: weak.map((r) => r.week_start), xFmt: day, yFmt: (v) => Number(v).toFixed(1), yMin: 1, yMax: 5, series: [
      { name: "Raw average", data: weak.map((r) => r.avg_stars), color: 1 },
      { name: "Shrunk", data: weak.map((r) => r.shrunk_stars), color: 0 },
      { name: "Baseline", data: weak.map((r) => r.baseline_stars), color: 2, dashed: true }] }),
      { cols: [{ key: "week_start", label: "Week" }, { key: "reviews", label: "Reviews" }, { key: "avg_stars", label: "Raw", fmt: stars }, { key: "shrunk_stars", label: "Shrunk", fmt: stars }, { key: "baseline_stars", label: "Baseline", fmt: stars }, { key: "signal", label: "Signal" }], rows: weak });
    card("rt-dist", (el) => bar(el, { horizontal: true, stack: true, x: ps.map((p) => p.product_name), yFmt: fmt.pct(0), series: [1, 2, 3, 4, 5].map((s, i) => ({ name: s + "★", data: ps.map((p) => p["stars_" + s] / p.reviews), color: ["--critical", "--serious", "--text-muted", 1, 0][i] })) }),
      { cols: [{ key: "product_name", label: "Product" }].concat([1, 2, 3, 4, 5].map((s) => ({ key: "stars_" + s, label: s + "★", fmt: fmt.int }))), rows: ps });
    table(document.getElementById("signals"), [{ key: "product_id", label: "Product", fmt: (p) => PN[p] || p }, { key: "market", label: "Market" }, { key: "week_start", label: "Week" }, { key: "reviews", label: "Reviews" },
      { key: "avg_stars", label: "Raw", fmt: stars }, { key: "baseline_stars", label: "Baseline", fmt: stars }, { key: "shrunk_stars", label: "Shrunk", fmt: stars }, { key: "signal", label: "Signal" }],
      D.ratings.filter((r) => r.signal === "weak signal" || r.signal === "actionable").concat(D.ratings.filter((r) => r.signal === "noise").slice(-8)));
  }

  /* ---------- Checks ---------- */
  function checks() {
    tiles([
      { k: "dbt models and tests", v: D.dbt ? `${D.dbt.passed} / ${D.dbt.nodes}` : "–", d: "passing" },
      { k: "Duplicate API rows removed", v: fmt.int((D.checks[0] || {}).value), d: "overlapping extracts" },
      { k: "Metric definitions", v: String(uniq(D.registry.map((r) => r.metric_id)).length), d: "versioned in the registry" },
    ]);
    document.getElementById("checks").innerHTML = `<ul class="insights">${D.checks.map((r) => {
      const warn = /missed|exceptions|not in the product map|no category/.test(r.check_name) && r.value > 0;
      return `<li><span class="status ${warn ? "warning" : "good"}"><i aria-hidden="true">${warn ? "!" : "✓"}</i>${warn ? "Flagged" : "Handled"}</span><span><b>${esc(r.check_name)}:</b> ${fmt.int(r.value)}. ${esc(r.handling)}.</span></li>`;
    }).join("")}</ul>`;
    card("ck-contract", (el) => line(el, { x: D.contract.map((r) => r.event_date), xFmt: day, yFmt: fmt.int, yMin: 0, series: [
      { name: "Mapped in staging", data: D.contract.map((r) => r.views_mapped), color: 0 },
      { name: "Filter on 'ViewReport'", data: D.contract.map((r) => r.views_naive_filter), color: 1, dashed: true }] }),
      { cols: [{ key: "event_date", label: "Date" }, { key: "schema_version", label: "Schema" }, { key: "views_mapped", label: "Mapped", fmt: fmt.int }, { key: "views_naive_filter", label: "Naive", fmt: fmt.int }], rows: D.contract });
    table(document.getElementById("registry"), [{ key: "metric_name", label: "Metric" }, { key: "version", label: "v" }, { key: "definition", label: "Definition" }, { key: "excludes", label: "Excludes" }, { key: "status", label: "Status" }], D.registry);
    const rules = [
      ["Each event is counted once, however many extracts delivered it", "stg_activity_events; test_events_counted_once"],
      ["Viewers are distinct accounts and are never summed across reports or weeks", "assert_viewers_are_distinct_not_summed; test_platform_viewers_are_distinct_not_summed"],
      ["Service accounts are excluded from views and viewers (report_views v2)", "rpt_metric_versions; test_service_account_inflates_views_not_viewers"],
      ["Both activity API schema versions map to one activity type", "assert_contract_change_keeps_views; contracts/sources.yml"],
      ["A migrated report keeps its history under one key; renamed reports keep theirs by ID", "assert_migrated_report_keeps_history"],
      ["No principal names, e-mail addresses or reviewer handles reach gold", "assert_no_personal_identifiers_in_gold; test_no_personal_identifiers_in_gold"],
      ["Department groups under five viewers are suppressed", "assert_small_groups_suppressed"],
      ["Every review has exactly one category; no match is 'uncategorised'", "assert_one_category_per_review"],
      ["A rating is always shown with its review count; thin weeks are never incidents", "rpt_ratings_weekly; test_low_volume_dip_is_a_weak_signal"],
      ["Reconciliation totals equal each source's totals", "assert_recon_reconciles_to_sources"],
      ["Rebuilding from the same seed reproduces every mart", "make rebuild (analysis/fingerprint.py)"],
    ];
    document.getElementById("rules").innerHTML = `<ul class="insights">${rules.map(([r, w]) => `<li><span class="status good"><i aria-hidden="true">✓</i>Tested</span><span><b>${esc(r)}.</b> <code>${esc(w)}</code></span></li>`).join("")}</ul>`;
  }

  const PAGES = { overview, adoption, reliability, feedback, ratings, checks };
  document.addEventListener("DOMContentLoaded", () => {
    if (!window.echarts) { document.querySelector("main").insertAdjacentHTML("afterbegin", '<p class="callout critical">Charts could not load (no network to the chart library). Tables still work.</p>'); }
    PAGES[document.body.dataset.page]();
  });
})();
