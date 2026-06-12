"use strict";

const state = {
  projects: [],
  meta: null,
  q: "",
  ministry: "",
  keyword: "",
  highOnly: true,
  shown: 20,
};

const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

function fmtYen(n) {
  if (n == null) return "—";
  if (n >= 1e12) return (n / 1e12).toLocaleString("ja-JP", { maximumFractionDigits: 2 }) + "兆円";
  if (n >= 1e8) return (n / 1e8).toLocaleString("ja-JP", { maximumFractionDigits: 1 }) + "億円";
  if (n >= 1e4) return Math.round(n / 1e4).toLocaleString("ja-JP") + "万円";
  return n.toLocaleString("ja-JP") + "円";
}

function filtered() {
  const q = state.q.trim();
  return state.projects.filter((p) => {
    if (state.highOnly && p.relevance !== "high") return false;
    if (state.ministry && p.ministry !== state.ministry) return false;
    if (state.keyword && !p.keywords.includes(state.keyword)) return false;
    if (q && !(p.name.includes(q) || p.overview.includes(q) || p.ministry.includes(q))) return false;
    return true;
  });
}

function deltaHtml(p) {
  const cur = p.budgets.find((b) => b.year === p.fiscal_year);
  const prev = p.budgets.find((b) => b.year === p.fiscal_year - 1);
  if (!cur || !prev || !prev.amount_yen) return "";
  const pct = Math.round(((cur.amount_yen - prev.amount_yen) / prev.amount_yen) * 100);
  if (pct === 0) return "";
  const cls = pct > 0 ? "up" : "down";
  const sign = pct > 0 ? "+" : "";
  return `<span class="delta ${cls}" title="前年度当初予算比">${sign}${pct}% 前年比</span>`;
}

function renderKpi() {
  const m = state.meta;
  const high = state.projects.filter((p) => p.relevance === "high");
  const sumHigh = high.reduce((a, p) => a + (p.budget_yen || 0), 0);
  const ministries = new Set(state.projects.map((p) => p.ministry)).size;
  document.getElementById("kpi").innerHTML = `
    <div class="kpi"><div class="label">関連事業数（自動抽出）</div>
      <div class="value">${high.length}<small> 件</small></div>
      <div class="sub">概要・目的まで含めると ${state.projects.length} 件 / 走査 ${m.total_projects_scanned.toLocaleString("ja-JP")} 事業</div></div>
    <div class="kpi"><div class="label">当初予算 合算 ※事業全体額</div>
      <div class="value">${fmtYen(sumHigh)}</div>
      <div class="sub">FY${m.fiscal_year}・事業名ヒット分の単純合算</div></div>
    <div class="kpi"><div class="label">所管府省庁</div>
      <div class="value">${ministries}<small> 機関</small></div></div>
    <div class="kpi"><div class="label">データ年度</div>
      <div class="value">FY${m.fiscal_year}</div>
      <div class="sub">出典: ${esc(m.source.name)}</div></div>`;
}

function renderControls() {
  const ministries = [...new Set(state.projects.map((p) => p.ministry))].sort();
  document.getElementById("ministry").innerHTML =
    `<option value="">すべての府省庁</option>` +
    ministries.map((mi) => `<option value="${esc(mi)}">${esc(mi)}</option>`).join("");
  document.getElementById("kw-chips").innerHTML = state.meta.keywords
    .map((k) => `<button class="chip-btn" data-kw="${esc(k)}">${esc(k)}</button>`)
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
        return `<article class="item">
  <div class="item-top">
    <div class="item-name"><span class="rank">${i + 1}</span>${esc(p.name)}</div>
    <div class="amount ${p.budget_yen == null ? "na" : ""}">${fmtYen(p.budget_yen)}${deltaHtml(p)}</div>
  </div>
  <div class="bar-track"><div class="bar" style="width:${w}%"></div></div>
  <div class="meta">
    <span class="tag">${esc(p.ministry)}</span>
    ${p.keywords.map((k) => `<span class="tag kw">${esc(k)}</span>`).join("")}
    ${p.sheet_type === "FS" ? `<span class="tag">基金</span>` : ""}
    <a class="src-link" href="${esc(p.source_url)}" target="_blank" rel="noopener">レビューシート原文 ↗</a>
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
    .map(
      (c) => `<article class="claim-card">
  <span class="verdict ${esc(c.verdict)}">${labels[c.verdict] || c.verdict}</span>
  <p class="claim-text">「${esc(c.claim)}」</p>
  <p class="fact">${esc(c.fact)}</p>
  <div class="claim-sources">
    ${c.sources.map((s) => `<a href="${esc(s.url)}" target="_blank" rel="noopener">出典: ${esc(s.label)} ↗</a>`).join("")}
    <span class="muted">出典生存確認: ${esc(c.checked_at)}</span>
  </div>
</article>`
    )
    .join("");
}

function bind() {
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
  const [projectsData, claimsData] = await Promise.all([
    fetch("data/projects.json").then((r) => r.json()),
    fetch("data/claims.json").then((r) => r.json()),
  ]);
  state.meta = projectsData;
  state.projects = projectsData.projects;
  const updated = new Date(projectsData.generated_at);
  document.getElementById("updated-badge").textContent =
    `自動更新 ${updated.getFullYear()}-${String(updated.getMonth() + 1).padStart(2, "0")}-${String(updated.getDate()).padStart(2, "0")}`;
  document.getElementById("fy-label").textContent =
    `FY${projectsData.fiscal_year} 当初予算・自動抽出 ${projectsData.projects.length} 事業`;
  document.getElementById("amount-note").textContent = `注記: ${projectsData.amount_note}。タグは機械抽出の理由。詳細は必ず出典のレビューシート原文を確認。`;
  document.getElementById("footer-meta").textContent =
    `データ生成: ${projectsData.generated_at} / 出典: ${projectsData.source.name}（${projectsData.source.url}）`;
  renderKpi();
  renderControls();
  renderList();
  renderClaims(claimsData);
  bind();
}

main().catch((e) => {
  document.getElementById("list").innerHTML = `<p class="muted">データの読み込みに失敗しました: ${esc(e.message)}</p>`;
});
