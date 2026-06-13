"use strict";

const state = {
  years: [],
  year: null,
  yearData: {},
  projects: [],
  meta: null,
  q: "",
  ministry: "",
  keyword: "",
  highOnly: true,
  sort: "budget",
  shown: 20,
};

const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

function fmtYen(n) {
  if (n == null) return "—";
  const sign = n < 0 ? "−" : "";
  const a = Math.abs(n);
  if (a >= 1e12) return sign + (a / 1e12).toLocaleString("ja-JP", { maximumFractionDigits: 2 }) + "兆円";
  if (a >= 1e8) return sign + (a / 1e8).toLocaleString("ja-JP", { maximumFractionDigits: 1 }) + "億円";
  if (a >= 1e4) return sign + Math.round(a / 1e4).toLocaleString("ja-JP") + "万円";
  return sign + a.toLocaleString("ja-JP") + "円";
}

const X_LOGO =
  '<svg viewBox="0 0 24 24" width="12" height="12" fill="currentColor" aria-hidden="true"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>';

function xIntent(text, url) {
  return `https://x.com/intent/post?text=${encodeURIComponent(text)}&url=${encodeURIComponent(url)}`;
}

function shareBtn(text, url, label) {
  return `<a class="share-x" href="${esc(xIntent(text, url))}" target="_blank" rel="noopener" aria-label="${esc(label)}をXで共有">${X_LOGO}共有</a>`;
}

function projectTweet(p) {
  return {
    text: [
      `【${p.name}】`,
      `FY${p.fiscal_year} 当初予算 ${fmtYen(p.budget_yen)}（所管: ${p.ministry}）`,
      `※事業全体の当初予算額。出典は行政事業レビュー（リンク先）`,
    ].join("\n"),
    url: p.source_url,
  };
}

function claimTweet(c, verdictLabel) {
  const fact = c.fact.length > 60 ? c.fact.slice(0, 60) + "…" : c.fact;
  return { text: [`「${c.claim}」`, `→ 判定: ${verdictLabel}`, fact].join("\n"), url: c.sources[0].url };
}

function budgetTweet(pb) {
  const cur = pb.initial_budget_series.find((s) => s.year === 2026);
  const y = pb.yoy_2025_2026;
  return {
    text: [
      `令和8年度（2026年度）の外国人政策の関係予算（総合的対応策関連・当初）は約${fmtYen(cur.amount_yen)}。`,
      `前年度比 約${y.delta_yen >= 0 ? "+" : ""}${fmtYen(y.delta_yen)}。`,
      `※増額の大半は会議体改組に伴うオーバーツーリズム対策等（国交省）の新規計上による。`,
    ].join("\n"),
    url: pb.primary_source.url,
  };
}

function comparisonTweet(comp, fy) {
  const sides = comp.sides.map((s) => `・${s.name}: ${fmtYen(s.budget_yen)}`).join("\n");
  return {
    text: [comp.title, sides, `（FY${fy} 当初予算・事業全体額。対象規模・条件は異なる）`].join("\n"),
    url: "https://rssystem.go.jp/",
  };
}

function projDelta(p) {
  const cur = p.budgets.find((b) => b.year === p.fiscal_year);
  const prev = p.budgets.find((b) => b.year === p.fiscal_year - 1);
  if (!cur || !prev || cur.amount_yen == null || !prev.amount_yen) return null;
  const abs = cur.amount_yen - prev.amount_yen;
  return { abs, pct: (abs / prev.amount_yen) * 100 };
}

function deltaBadge(d, extraClass = "") {
  if (!d || Math.round(d.pct) === 0) return "";
  const up = d.pct > 0;
  const cls = up ? "up" : "down";
  const surge = up && d.pct >= 50 ? " surge" : ""; // 大幅な膨張は警告色＋グローで強調
  const arrow = up ? "▲" : "▼";
  const sign = up ? "+" : "";
  const num = Math.abs(d.pct) >= 100 ? Math.round(d.pct) : d.pct.toFixed(1);
  return `<span class="delta ${cls}${surge} ${extraClass}" title="前年度当初予算比"><span class="delta-arr" aria-hidden="true">${arrow}</span>${sign}${num}%</span>`;
}

function filtered() {
  const q = state.q.trim();
  const rows = state.projects.filter((p) => {
    if (state.highOnly && p.relevance !== "high") return false;
    if (state.ministry && p.ministry !== state.ministry) return false;
    if (state.keyword && !p.keywords.includes(state.keyword)) return false;
    if (q && !(p.name.includes(q) || p.overview.includes(q) || p.ministry.includes(q))) return false;
    return true;
  });
  if (state.sort !== "budget") {
    const key = state.sort === "deltaPct" ? "pct" : "abs";
    rows.sort((a, b) => {
      const da = projDelta(a);
      const db = projDelta(b);
      if (!da && !db) return 0;
      if (!da) return 1;
      if (!db) return -1;
      return db[key] - da[key];
    });
  }
  return rows;
}

function sumDelta(projects, fy) {
  let cur = 0;
  let prev = 0;
  for (const p of projects) {
    if (p.relevance !== "high") continue;
    const c = p.budgets.find((b) => b.year === fy);
    const v = p.budgets.find((b) => b.year === fy - 1);
    if (c && v && c.amount_yen != null && v.amount_yen) {
      cur += c.amount_yen;
      prev += v.amount_yen;
    }
  }
  return prev > 0 ? { pct: ((cur - prev) / prev) * 100, abs: cur - prev } : null;
}

function renderYearTabs() {
  document.getElementById("year-tabs").innerHTML = state.years
    .map((y) => `<button class="year-tab ${y === state.year ? "on" : ""}" data-year="${y}">FY${y}</button>`)
    .join("");
}

function renderKpi() {
  const m = state.meta;
  const high = state.projects.filter((p) => p.relevance === "high");
  const sumHigh = high.reduce((a, p) => a + (p.budget_yen || 0), 0);
  const ministries = new Set(state.projects.map((p) => p.ministry)).size;
  const d = sumDelta(state.projects, m.fiscal_year);
  document.getElementById("kpi").innerHTML = `
    <div class="kpi"><div class="label">関連事業数（自動抽出）</div>
      <div class="value"><span data-count="${high.length}" data-fmt="int">${high.length}</span><small> 件</small></div>
      <div class="sub">概要・目的まで含めると ${state.projects.length} 件 / 走査 ${m.total_projects_scanned.toLocaleString("ja-JP")} 事業</div></div>
    <div class="kpi"><div class="label">当初予算 合算 ※事業全体額</div>
      <div class="value"><span data-count="${sumHigh}" data-fmt="yen">${fmtYen(sumHigh)}</span> ${d ? deltaBadge(d, "big") : ""}</div>
      <div class="sub">FY${m.fiscal_year}・事業名ヒット分の単純合算${d ? `。前年比は同一事業ベース（${fmtYen(d.abs)}）` : ""}</div></div>
    <div class="kpi"><div class="label">所管府省庁</div>
      <div class="value"><span data-count="${ministries}" data-fmt="int">${ministries}</span><small> 機関</small></div></div>
    <div class="kpi"><div class="label">データ年度</div>
      <div class="value">FY${m.fiscal_year}</div>
      <div class="sub">出典: ${esc(m.source.name)}</div></div>`;
  observeReveals(document.getElementById("kpi"));
}

let POLICY = null;
let minSort = "amount";

function ministryRowsHtml() {
  const list = POLICY.fy2026.by_ministry.filter((m) => m.amount_yen > 0).slice();
  if (minSort === "name") list.sort((a, b) => a.ministry.localeCompare(b.ministry, "ja"));
  else list.sort((a, b) => b.amount_yen - a.amount_yen);
  const top = list.slice(0, 6);
  const minMax = Math.max(...top.map((m) => m.amount_yen), 1);
  return top
    .map(
      (m) => `<div class="min-row">
      <span class="min-name">${esc(m.ministry)}</span>
      <span class="min-track"><span class="min-fill" style="width:${Math.max((m.amount_yen / minMax) * 100, 2)}%"></span></span>
      <span class="min-val">${fmtYen(m.amount_yen)}</span>
    </div>`
    )
    .join("");
}

function renderMinistryList() {
  const el = document.getElementById("budget-min-list");
  if (el) el.innerHTML = ministryRowsHtml();
  document.querySelectorAll("#budget-min-sort .sort-btn").forEach((b) => b.classList.toggle("on", b.dataset.min === minSort));
}

function renderPolicyBudget(pb) {
  POLICY = pb;
  const series = pb.initial_budget_series;
  const max = Math.max(...series.map((s) => s.amount_yen), 1);
  const cur = series.find((s) => s.year === 2026) || series[series.length - 1];
  const y = pb.yoy_2025_2026;
  const t = budgetTweet(pb);
  const bars = series
    .map((s) => {
      const hot = s.year === 2026;
      return `<div class="budget-bar-row">
      <div class="budget-bar-label">FY${s.year}<span class="budget-bar-sub">${esc(s.label)}</span></div>
      <div class="budget-bar-track"><div class="budget-bar-fill ${hot ? "hot" : ""}" style="width:${Math.max((s.amount_yen / max) * 100, 1.5)}%"></div></div>
      <div class="budget-bar-val ${hot ? "hot" : ""}">${fmtYen(s.amount_yen)}<a class="src-mini" href="${esc(s.source.url)}" target="_blank" rel="noopener" aria-label="FY${s.year}の出典">出典↗</a></div>
    </div>`;
    })
    .join("");
  const mins = ministryRowsHtml();
  const items = pb.fy2026.top_items
    .slice(0, 5)
    .map(
      (it) => `<li><span class="ti-amt">${fmtYen(it.amount_yen)}</span><span class="tag">${esc(it.ministry)}</span> ${esc(it.desc)}</li>`
    )
    .join("");
  document.getElementById("policy-budget").innerHTML = `
  <div class="budget-hero">
    <div class="budget-hero-main">
      <div class="budget-hero-label">令和8年度 当初予算（総合的対応策 関係予算 合計）</div>
      <div class="budget-hero-num" data-count="${cur.amount_yen}" data-fmt="yen">${fmtYen(cur.amount_yen)}</div>
      <div class="budget-hero-delta">前年度比 <span class="delta up surge big"><span class="delta-arr" aria-hidden="true">▲</span>${y.delta_yen >= 0 ? "+" : ""}${fmtYen(y.delta_yen)}（${y.pct >= 0 ? "+" : ""}${y.pct}%）</span></div>
      <div class="budget-hero-supp">うち令和7年度補正予算 関連: ${fmtYen(pb.fy2026.supplementary_r7_yen)}</div>
    </div>
    ${shareBtn(t.text, t.url, "令和8年度 外国人政策 関係予算")}
  </div>
  <div class="budget-trend">${bars}</div>
  <p class="pair-note budget-caveat"><i>!</i> ${esc(pb.scope_note)}</p>
  <div class="budget-cols">
    <div class="budget-col">
      <div class="budget-col-h">FY2026 主管省庁別（当初予算）
        <span class="sort-seg mini" id="budget-min-sort" role="group" aria-label="省庁の並び替え">
          <button type="button" class="sort-btn on" data-min="amount">予算順</button>
          <button type="button" class="sort-btn" data-min="name">省庁名順</button>
        </span>
      </div>
      <div id="budget-min-list">${mins}</div>
      <div class="budget-col-foot">※施策の主管（筆頭）省庁で集計。複数省庁施策は筆頭省庁に計上。最大の国土交通省は観光・オーバーツーリズム対策が中心。</div>
    </div>
    <div class="budget-col">
      <div class="budget-col-h">FY2026 主な施策（金額順）</div>
      <ul class="budget-items">${items}</ul>
    </div>
  </div>
  <p class="budget-basis">${esc(pb.basis_note)} 出典: <a href="${esc(pb.primary_source.url)}" target="_blank" rel="noopener">${esc(pb.primary_source.label)} ↗</a></p>`;
}

function renderComparisons(compData) {
  document.getElementById("compare").innerHTML = compData.comparisons
    .map((comp) => {
      const max = Math.max(...comp.sides.map((s) => s.budget_yen || 0), 1);
      const t = comparisonTweet(comp, compData.fiscal_year);
      const sides = comp.sides
        .map(
          (s) => `
    <div class="side">
      <div class="side-target">${esc(s.target)}</div>
      <div class="side-name">${esc(s.name)}</div>
      <div class="side-amount">${fmtYen(s.budget_yen)}<span class="side-fy">FY${compData.fiscal_year} 当初予算</span></div>
      <div class="bar-track"><div class="bar" style="width:${s.budget_yen ? Math.max((s.budget_yen / max) * 100, 1) : 0}%"></div></div>
      ${s.per_person.length ? `<div class="pp">${s.per_person.map((p) => `<span class="tag pp-tag">${esc(p.label)}: ${esc(p.text)}</span>`).join("")}</div>` : ""}
      <div class="meta">
        <span class="tag">${esc(s.ministry)}</span>
        <a class="src-link" href="${esc(s.rs_source_url)}" target="_blank" rel="noopener">レビューシート ↗</a>
        ${s.per_person_source ? `<a class="src-link" href="${esc(s.per_person_source.url)}" target="_blank" rel="noopener">${esc(s.per_person_source.label)} ↗</a>` : ""}
      </div>
    </div>`
        )
        .join("");
      return `<article class="pair">
  <div class="pair-head"><h3>${esc(comp.title)}</h3>${shareBtn(t.text, t.url, comp.title)}</div>
  <div class="pair-grid">${sides}</div>
  <p class="pair-note">注記: ${esc(comp.context_note)}</p>
</article>`;
    })
    .join("");
}

function sparkline(series, w = 220, h = 46) {
  const vals = series.map((s) => s.value);
  const min = Math.min(...vals);
  const max = Math.max(...vals);
  const pts = series
    .map((s, i) => {
      const x = (i / (series.length - 1)) * (w - 4) + 2;
      const y = h - 3 - ((s.value - min) / (max - min || 1)) * (h - 8);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
  return `<svg class="spark" viewBox="0 0 ${w} ${h}" width="${w}" height="${h}" aria-hidden="true"><polyline points="${pts}" fill="none" stroke="var(--accent)" stroke-width="2"/></svg>`;
}

function renderStats(statsData) {
  const z = statsData.indicators.zairyu_total;
  const zs = z.series;
  const first = zs[0];
  const latest = z.latest;
  const share = statsData.derived.zairyu_share_pct;
  const srcUrl = statsData.source.url;
  document.getElementById("stats").innerHTML = `
    <div class="kpi stat-card">
      <div class="label">${esc(z.name)}（全国・${latest.year}年）</div>
      <div class="value">${(latest.value / 1e4).toLocaleString("ja-JP", { maximumFractionDigits: 1 })}<small> 万人</small></div>
      ${sparkline(zs)}
      <div class="sub">${first.year}年 ${(first.value / 1e4).toFixed(0)}万人 → ${latest.year}年 ${(latest.value / 1e4).toFixed(0)}万人（${zs.length}年分の推移）</div>
      <div class="sub"><a href="${esc(srcUrl)}" target="_blank" rel="noopener">出典: e-Stat 統計ダッシュボード ↗</a></div>
    </div>
    <div class="kpi stat-card">
      <div class="label">総人口に占める割合（${share.year}年）</div>
      <div class="value">${share.value}<small> %</small></div>
      <div class="sub">${esc(share.note)}</div>
      <div class="sub"><a href="${esc(srcUrl)}" target="_blank" rel="noopener">出典: e-Stat 統計ダッシュボード ↗</a></div>
    </div>`;
}

function renderControls() {
  const ministries = [...new Set(state.projects.map((p) => p.ministry))].sort();
  if (state.ministry && !ministries.includes(state.ministry)) state.ministry = "";
  document.getElementById("ministry").innerHTML =
    `<option value="">すべての府省庁</option>` +
    ministries.map((mi) => `<option value="${esc(mi)}" ${mi === state.ministry ? "selected" : ""}>${esc(mi)}</option>`).join("");
  document.getElementById("kw-chips").innerHTML = state.meta.keywords
    .map((k) => `<button class="chip-btn ${k === state.keyword ? "on" : ""}" data-kw="${esc(k)}">${esc(k)}</button>`)
    .join("");
}

function renderList() {
  const rows = filtered();
  const max = Math.max(...rows.map((p) => p.budget_yen || 0), 1);
  const slice = rows.slice(0, state.shown);
  document.getElementById("list").innerHTML =
    slice
      .map((p, i) => {
        const w = p.budget_yen ? Math.max((p.budget_yen / max) * 100, 0.5) : 0;
        const t = projectTweet(p);
        const d = projDelta(p);
        return `<article class="item">
  <div class="item-top">
    <div class="item-name"><span class="rank">${i + 1}</span>${esc(p.name)}</div>
    <div class="amount ${p.budget_yen == null ? "na" : ""}">${fmtYen(p.budget_yen)}${deltaBadge(d)}</div>
  </div>
  <div class="bar-track"><div class="bar" style="width:${w}%"></div></div>
  <div class="meta">
    <span class="tag">${esc(p.ministry)}</span>
    ${p.keywords.map((k) => `<span class="tag kw">${esc(k)}</span>`).join("")}
    ${p.sheet_type === "FS" ? `<span class="tag">基金</span>` : ""}
    <a class="src-link" href="${esc(p.source_url)}" target="_blank" rel="noopener">レビューシート原文 ↗</a>
    ${shareBtn(t.text, t.url, p.name)}
  </div>
  ${p.overview ? `<details><summary>事業概要</summary>${esc(p.overview)}</details>` : ""}
</article>`;
      })
      .join("") || `<p class="muted">該当する事業がありません。</p>`;
  const more = document.getElementById("more");
  more.hidden = rows.length <= state.shown;
  more.textContent = `さらに表示（残り ${Math.max(rows.length - state.shown, 0)} 件）`;
  applyGlossary(document.getElementById("list"));
  observeReveals(document.getElementById("list"));
}

function renderClaims(claimsData) {
  const labels = { true: "事実", false: "誤り", conditional: "条件付き" };
  document.getElementById("claims").innerHTML = claimsData.claims
    .map((c) => {
      const label = labels[c.verdict] || c.verdict;
      const t = claimTweet(c, label);
      return `<article class="claim-card">
  <div class="claim-head"><span class="verdict ${esc(c.verdict)}">${label}</span>${shareBtn(t.text, t.url, c.claim)}</div>
  <p class="claim-text">「${esc(c.claim)}」</p>
  <p class="fact">${esc(c.fact)}</p>
  <div class="claim-sources">
    ${c.sources.map((s) => `<a href="${esc(s.url)}" target="_blank" rel="noopener">出典: ${esc(s.label)} ↗</a>`).join("")}
    <span class="muted">出典生存確認: ${esc(c.checked_at)}</span>
  </div>
</article>`;
    })
    .join("");
}

function setYear(y) {
  state.year = y;
  state.meta = state.yearData[y];
  state.projects = state.meta.projects;
  state.shown = 20;
  document.getElementById("fy-label").textContent =
    `FY${state.meta.fiscal_year} 当初予算・自動抽出 ${state.projects.length} 事業`;
  renderYearTabs();
  renderKpi();
  renderControls();
  renderList();
}

/* ===== 用語解説ツールチップ ===== */
let GLOSSARY = [];
let glossPop = null;
let glossPinned = null;

function ensureGlossPop() {
  if (glossPop) return glossPop;
  glossPop = document.createElement("div");
  glossPop.id = "gloss-pop";
  glossPop.setAttribute("role", "tooltip");
  glossPop.hidden = true;
  document.body.appendChild(glossPop);
  document.addEventListener("click", (e) => {
    if (glossPinned && !e.target.closest(".gloss") && !e.target.closest("#gloss-pop")) hideGloss(true);
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") hideGloss(true);
  });
  window.addEventListener("resize", () => hideGloss(true));
  return glossPop;
}

function showGloss(el) {
  const pop = ensureGlossPop();
  const g = GLOSSARY.find((x) => x.term === el.dataset.term);
  if (!g) return;
  pop.innerHTML = `<span class="gp-term">${esc(g.term)}${g.reading && g.reading !== g.term ? `<span class="gp-read">${esc(g.reading)}</span>` : ""}</span>${esc(g.def)}`;
  pop.hidden = false;
  const r = el.getBoundingClientRect();
  const pw = Math.min(pop.offsetWidth, window.innerWidth - 16);
  pop.style.width = pw + "px";
  let left = r.left + r.width / 2 - pw / 2;
  left = Math.max(8, Math.min(left, window.innerWidth - pw - 8));
  let top = r.bottom + 8;
  if (top + pop.offsetHeight > window.innerHeight - 8) top = r.top - pop.offsetHeight - 8;
  pop.style.left = left + "px";
  pop.style.top = Math.max(8, top) + "px";
}

function hideGloss(force) {
  if (!glossPop) return;
  if (glossPinned && !force) return;
  glossPop.hidden = true;
  if (force && glossPinned) {
    glossPinned.setAttribute("aria-expanded", "false");
    glossPinned = null;
  }
}

function makeGloss(term) {
  const span = document.createElement("span");
  span.className = "gloss";
  span.dataset.term = term;
  span.tabIndex = 0;
  span.setAttribute("role", "button");
  span.setAttribute("aria-label", `${term} の用語解説`);
  span.setAttribute("aria-expanded", "false");
  span.append(document.createTextNode(term));
  const q = document.createElement("span");
  q.className = "gloss-q";
  q.setAttribute("aria-hidden", "true");
  q.textContent = "?";
  span.appendChild(q);
  span.addEventListener("mouseenter", () => {
    if (!glossPinned) showGloss(span);
  });
  span.addEventListener("mouseleave", () => hideGloss(false));
  span.addEventListener("focus", () => showGloss(span));
  span.addEventListener("blur", () => hideGloss(false));
  const toggle = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (glossPinned === span) {
      hideGloss(true);
    } else {
      if (glossPinned) glossPinned.setAttribute("aria-expanded", "false");
      glossPinned = span;
      span.setAttribute("aria-expanded", "true");
      showGloss(span);
    }
  };
  span.addEventListener("click", toggle);
  span.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") toggle(e);
  });
  return span;
}

function applyGlossary(root, skipSelector) {
  if (!root || !GLOSSARY.length) return;
  const skip = skipSelector ? [...root.querySelectorAll(skipSelector)] : [];
  const terms = GLOSSARY.map((g) => g.term).sort((a, b) => b.length - a.length);
  const linked = new Set();
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
    acceptNode(n) {
      if (!n.nodeValue.trim()) return NodeFilter.FILTER_REJECT;
      let p = n.parentElement;
      while (p && p !== root) {
        const t = p.tagName;
        if (t === "A" || t === "BUTTON" || t === "ABBR" || t === "SCRIPT" || t === "STYLE" || p.classList.contains("gloss"))
          return NodeFilter.FILTER_REJECT;
        p = p.parentElement;
      }
      if (skip.some((s) => s.contains(n))) return NodeFilter.FILTER_REJECT;
      return NodeFilter.FILTER_ACCEPT;
    },
  });
  const nodes = [];
  let cur;
  while ((cur = walker.nextNode())) nodes.push(cur);
  for (const node of nodes) {
    for (const term of terms) {
      if (linked.has(term)) continue;
      const idx = node.nodeValue.indexOf(term);
      if (idx < 0) continue;
      const rest = node.splitText(idx);
      rest.splitText(term.length);
      rest.parentNode.replaceChild(makeGloss(term), rest);
      linked.add(term);
      break;
    }
  }
}

/* ===== アニメーション（カウントアップ＋スクロールリビール） ===== */
const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

function fmtBy(kind, n) {
  if (kind === "yen") return fmtYen(Math.round(n));
  return Math.round(n).toLocaleString("ja-JP");
}

function animateCount(el) {
  if (el.dataset.counted) return;
  el.dataset.counted = "1";
  const to = Number(el.dataset.count);
  const kind = el.dataset.fmt || "int";
  if (prefersReduced || !isFinite(to)) {
    el.textContent = fmtBy(kind, to);
    return;
  }
  const dur = 1100;
  const start = performance.now();
  const tick = (now) => {
    const p = Math.min((now - start) / dur, 1);
    const eased = 1 - Math.pow(1 - p, 3);
    el.textContent = fmtBy(kind, to * eased);
    if (p < 1) requestAnimationFrame(tick);
    else el.textContent = fmtBy(kind, to);
  };
  requestAnimationFrame(tick);
}

let revealObserver = null;
function observeReveals(root) {
  if (!("IntersectionObserver" in window)) return;
  if (!revealObserver) {
    revealObserver = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          if (!e.isIntersecting) continue;
          e.target.classList.add("in");
          if (e.target.matches("[data-count]")) animateCount(e.target);
          e.target.querySelectorAll("[data-count]").forEach(animateCount);
          revealObserver.unobserve(e.target);
        }
      },
      { threshold: 0.12, rootMargin: "0px 0px -36px 0px" }
    );
  }
  const sel = ".kpi, .item, .pair, .claim-card, .stat-card, .budget-hero, .budget-trend, .budget-cols, .budget-basis, .cta-inner";
  (root || document).querySelectorAll(sel).forEach((el) => {
    if (!el.classList.contains("reveal")) {
      el.classList.add("reveal");
      revealObserver.observe(el);
    }
  });
}

function bind() {
  document.getElementById("year-tabs").addEventListener("click", (e) => {
    const btn = e.target.closest("[data-year]");
    if (btn) setYear(Number(btn.dataset.year));
  });
  document.getElementById("q").addEventListener("input", (e) => {
    state.q = e.target.value;
    state.shown = 20;
    renderList();
  });
  document.getElementById("ministry").addEventListener("change", (e) => {
    state.ministry = e.target.value;
    state.shown = 20;
    renderList();
  });
  document.getElementById("sort").addEventListener("click", (e) => {
    const btn = e.target.closest("[data-sort]");
    if (!btn) return;
    state.sort = btn.dataset.sort;
    document.querySelectorAll("#sort .sort-btn").forEach((b) => b.classList.toggle("on", b === btn));
    state.shown = 20;
    renderList();
  });
  document.getElementById("budget-min-sort").addEventListener("click", (e) => {
    const btn = e.target.closest("[data-min]");
    if (!btn) return;
    minSort = btn.dataset.min;
    renderMinistryList();
  });
  document.getElementById("high-only").addEventListener("change", (e) => {
    state.highOnly = e.target.checked;
    state.shown = 20;
    renderList();
  });
  document.getElementById("kw-chips").addEventListener("click", (e) => {
    const btn = e.target.closest("[data-kw]");
    if (!btn) return;
    state.keyword = state.keyword === btn.dataset.kw ? "" : btn.dataset.kw;
    document.querySelectorAll(".chip-btn").forEach((b) => b.classList.toggle("on", b.dataset.kw === state.keyword));
    state.shown = 20;
    renderList();
  });
  document.getElementById("more").addEventListener("click", () => {
    state.shown += 30;
    renderList();
  });
}

async function main() {
  const getJson = (path) => fetch(path).then((r) => r.json());
  const [yearsMeta, claimsData, compData, statsData, policyBudget, glossary] = await Promise.all([
    getJson("data/years.json"),
    getJson("data/claims.json"),
    getJson("data/comparisons.json"),
    getJson("data/stats.json"),
    getJson("data/policy_budget.json"),
    getJson("data/glossary.json"),
  ]);
  GLOSSARY = glossary.terms || [];
  state.years = yearsMeta.years;
  await Promise.all(
    state.years.map((y) => getJson(`data/projects_${y}.json`).then((d) => (state.yearData[y] = d)))
  );
  const latestMeta = state.yearData[yearsMeta.latest];
  const updated = new Date(latestMeta.generated_at);
  document.getElementById("updated-badge").textContent =
    `自動更新 ${updated.getFullYear()}-${String(updated.getMonth() + 1).padStart(2, "0")}-${String(updated.getDate()).padStart(2, "0")}`;
  document.getElementById("amount-note").textContent = `注記: ${latestMeta.amount_note}。タグは機械抽出の理由。詳細は必ず出典のレビューシート原文を確認。`;
  document.getElementById("footer-meta").textContent =
    `データ生成: ${latestMeta.generated_at} / 出典: ${latestMeta.source.name}（${latestMeta.source.url}） / 収載年度: ${state.years.map((y) => "FY" + y).join(" / ")}`;
  renderPolicyBudget(policyBudget);
  renderComparisons(compData);
  renderStats(statsData);
  renderClaims(claimsData);
  bind();
  setYear(yearsMeta.latest);
  // #list は renderList 内で個別にツールチップ化済み。残りの静的・予算・比較・統計・言説領域を一括処理。
  applyGlossary(document.querySelector("main"), "#list");
  observeReveals(document);
}

document.documentElement.classList.add("js");
main().catch((e) => {
  document.getElementById("list").innerHTML = `<p class="muted">データの読み込みに失敗しました: ${esc(e.message)}</p>`;
});
