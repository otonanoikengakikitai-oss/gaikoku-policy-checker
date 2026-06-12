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
  const cls = d.pct > 0 ? "up" : "down";
  const sign = d.pct > 0 ? "+" : "";
  return `<span class="delta ${cls} ${extraClass}" title="前年度当初予算比">${sign}${d.pct.toFixed(d.pct >= 100 ? 0 : 1)}%</span>`;
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
      <div class="value">${high.length}<small> 件</small></div>
      <div class="sub">概要・目的まで含めると ${state.projects.length} 件 / 走査 ${m.total_projects_scanned.toLocaleString("ja-JP")} 事業</div></div>
    <div class="kpi"><div class="label">当初予算 合算 ※事業全体額</div>
      <div class="value">${fmtYen(sumHigh)} ${d ? deltaBadge(d, "big") : ""}</div>
      <div class="sub">FY${m.fiscal_year}・事業名ヒット分の単純合算${d ? `。前年比は同一事業ベース（${fmtYen(d.abs)}）` : ""}</div></div>
    <div class="kpi"><div class="label">所管府省庁</div>
      <div class="value">${ministries}<small> 機関</small></div></div>
    <div class="kpi"><div class="label">データ年度</div>
      <div class="value">FY${m.fiscal_year}</div>
      <div class="sub">出典: ${esc(m.source.name)}</div></div>`;
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
  document.getElementById("sort").addEventListener("change", (e) => {
    state.sort = e.target.value;
    state.shown = 20;
    renderList();
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
  const [yearsMeta, claimsData, compData, statsData] = await Promise.all([
    getJson("data/years.json"),
    getJson("data/claims.json"),
    getJson("data/comparisons.json"),
    getJson("data/stats.json"),
  ]);
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
  renderComparisons(compData);
  renderStats(statsData);
  renderClaims(claimsData);
  bind();
  setYear(yearsMeta.latest);
}

main().catch((e) => {
  document.getElementById("list").innerHTML = `<p class="muted">データの読み込みに失敗しました: ${esc(e.message)}</p>`;
});
