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
  shisaku: { q: "", ministry: "", zeroOnly: false }, // FY2026 施策一覧の絞り込み
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

// 一次ソースの厳密な実額（1円単位）を、丸めず億・万・円の内訳で返す
function yenBreakdown(yen) {
  const neg = yen < 0;
  let a = Math.abs(Math.round(yen));
  const oku = Math.floor(a / 1e8);
  a %= 1e8;
  const man = Math.floor(a / 1e4);
  a %= 1e4;
  const en = a;
  let s = "";
  if (oku) s += oku.toLocaleString("ja-JP") + "億";
  if (man) s += man.toLocaleString("ja-JP") + "万";
  if (en || s === "") s += en.toLocaleString("ja-JP");
  s += "円";
  return (neg ? "−" : "") + s;
}

// 出典記載の単位（千円単位なら千円表記）＋ 円内訳。例: 150,769,762千円（1,507億6,976万2,000円）
function exactSource(yen) {
  const r = Math.round(yen);
  const head = r % 1000 === 0 ? (r / 1000).toLocaleString("ja-JP") + "千円" : r.toLocaleString("ja-JP") + "円";
  return `${head}（${yenBreakdown(r)}）`;
}

// 丸め値の直下に併記する厳密実額の行
function exactTag(yen, label = "元データ") {
  if (yen == null) return "";
  return `<span class="exact-sub">${label}：${exactSource(yen)}</span>`;
}

const X_LOGO =
  '<svg viewBox="0 0 24 24" width="12" height="12" fill="currentColor" aria-hidden="true"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>';

function xIntent(text, url) {
  return `https://x.com/intent/post?text=${encodeURIComponent(text)}&url=${encodeURIComponent(url)}`;
}

function shareBtn(text, url, label, btnText) {
  const t = btnText || "共有";
  const cls = btnText && btnText !== "共有" ? "share-x share-rebut" : "share-x";
  return `<a class="${cls}" href="${esc(xIntent(text, url))}" target="_blank" rel="noopener" aria-label="${esc(label)}をXで共有">${X_LOGO}${esc(t)}</a>`;
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
  const fact = c.fact.length > 90 ? c.fact.slice(0, 90) + "…" : c.fact;
  return {
    text: ["【一次ソースで論破】", `言説：「${c.claim}」`, `→ 判定: ${verdictLabel}`, `ファクト：${fact}`, `出典は一次ソース（リンク先）`].join(
      "\n"
    ),
    url: c.sources[0].url,
  };
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
  const sides = comp.sides
    .map((s) => `・${s.name}: ${s.budget_yen != null ? fmtYen(s.budget_yen) : s.budget_note || "単価で比較"}`)
    .join("\n");
  const src = (comp.sides.find((s) => s.budget_source) || {}).budget_source;
  return {
    text: [comp.title, sides, `（令和8年度予算・一次ソース。対象規模・条件は異なる）`].join("\n"),
    url: (src && src.url) || "https://www.mext.go.jp/",
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

const FY_BUDGET = 2026; // 総合的対応策 関係予算（行政事業レビューとは別データ）の専用タブ

function renderYearTabs() {
  const tabs = state.years.map(
    (y) => `<button class="year-tab ${y === state.year ? "on" : ""}" data-year="${y}">FY${y}</button>`
  );
  tabs.push(
    `<button class="year-tab budget-tab ${state.year === FY_BUDGET ? "on" : ""}" data-year="${FY_BUDGET}">FY${FY_BUDGET}<span class="tab-latest">最新</span></button>`
  );
  document.getElementById("year-tabs").innerHTML = tabs.join("");
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
      ${exactTag(sumHigh)}
      <div class="sub">FY${m.fiscal_year}・事業名ヒット分の単純合算${d ? `。前年比は同一事業ベース（${fmtYen(d.abs)}／実額 ${exactSource(d.abs)}）` : ""}</div></div>
    <div class="kpi"><div class="label">所管府省庁</div>
      <div class="value"><span data-count="${ministries}" data-fmt="int">${ministries}</span><small> 機関</small></div></div>
    <div class="kpi"><div class="label">データ年度</div>
      <div class="value">FY${m.fiscal_year}</div>
      <div class="sub">出典: ${esc(m.source.name)}</div></div>`;
  observeReveals(document.getElementById("kpi"));
}

let POLICY = null;
let minSort = "amount";

// 省庁→色（増額の正体バー用）。国土交通省＝観光・オーバーツーリズムを金色で強調
const MIN_COLORS = {
  国土交通省: "#fbbf24",
  法務省: "#7aa7ff",
  厚生労働省: "#34d399",
  文部科学省: "#f87171",
  経済産業省: "#c084fc",
  警察庁: "#f0997b",
};
const minColor = (m) => MIN_COLORS[m] || "#5f5e5a";

// 個別施策のXシェア（事実ベース固定・出典つき）
function shisakuTweet(it) {
  const amt = it.amount_yen === 0 ? "0円（既存予算内での対応・他事業の内数）" : fmtYen(it.amount_yen);
  return {
    text: [
      `【令和8年度 外国人政策 関係予算】`,
      `${it.title || it.desc.slice(0, 24)}`,
      `${amt}（所管: ${it.ministry}）`,
      `※総合的対応策の関連予算。出典は内閣官房（リンク先）`,
    ].join("\n"),
    url: (POLICY && POLICY.primary_source && POLICY.primary_source.url) || "https://www.cas.go.jp/",
  };
}

function shisakuMatch(it) {
  const s = state.shisaku;
  if (s.zeroOnly && it.amount_yen !== 0) return false;
  if (s.ministry && it.ministry !== s.ministry) return false;
  const q = s.q.trim();
  if (q && !((it.title || "").includes(q) || (it.desc || "").includes(q) || it.ministry.includes(q))) return false;
  return true;
}

function renderShisakuList() {
  if (!POLICY) return;
  const all = POLICY.fy2026.top_items;
  const rows = all.filter(shisakuMatch);
  const sumYen = rows.reduce((a, it) => a + it.amount_yen, 0);
  document.getElementById("shisaku-count").textContent =
    `${rows.length} / ${all.length} 施策${rows.length ? `・絞り込み合計 ${fmtYen(sumYen)}` : ""}`;
  document.getElementById("budget-items").innerHTML =
    rows
      .map((it) => {
        const zero = it.amount_yen === 0;
        const t = shisakuTweet(it);
        return `<li>
        <div class="ti-head">
          <span class="ti-amt${zero ? " zero" : ""}">${fmtYen(it.amount_yen)}</span>
          <span class="tag">${esc(it.ministry)}</span>
          ${zero ? `<span class="zero-note">既存の通常予算内での対応、または他事業の内数</span>` : ""}
          ${shareBtn(t.text, t.url, it.title || "施策")}
        </div>
        ${zero ? "" : exactTag(it.amount_yen)}
        ${it.title ? `<div class="ti-title">${esc(it.title)}</div>` : ""}
        ${it.desc ? `<div class="ti-desc">${esc(it.desc)}</div>` : ""}
      </li>`;
      })
      .join("") || `<li class="muted" style="border:none">該当する施策がありません。</li>`;
  applyGlossary(document.getElementById("budget-items"));
}

function ministryRowsHtml() {
  const list = POLICY.fy2026.by_ministry.filter((m) => m.amount_yen > 0).slice();
  if (minSort === "name") list.sort((a, b) => a.ministry.localeCompare(b.ministry, "ja"));
  else list.sort((a, b) => b.amount_yen - a.amount_yen);
  const minMax = Math.max(...list.map((m) => m.amount_yen), 1);
  return list
    .map(
      (m) => `<div class="min-item">
      <div class="min-row">
        <span class="min-name">${esc(m.ministry)}</span>
        <span class="min-track"><span class="min-fill" style="width:${Math.max((m.amount_yen / minMax) * 100, 2)}%"></span></span>
        <span class="min-val">${fmtYen(m.amount_yen)}</span>
      </div>
      ${exactTag(m.amount_yen)}
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
      <div class="budget-bar-val ${hot ? "hot" : ""}">${fmtYen(s.amount_yen)}<a class="src-mini" href="${esc(s.source.url)}" target="_blank" rel="noopener" aria-label="FY${s.year}の出典">出典↗</a><span class="exact-sub">${exactSource(s.amount_yen)}</span></div>
    </div>`;
    })
    .join("");
  const mins = ministryRowsHtml();
  // 増額の正体: FY2026総額(検算済み)の省庁別100%積み上げバー。国交省=観光を強調。
  const byMin = pb.fy2026.by_ministry.filter((m) => m.amount_yen > 0);
  const total = pb.fy2026.initial_total_yen;
  const lead = byMin[0];
  const leadPct = Math.round((lead.amount_yen / total) * 100);
  const breakdownBar = byMin
    .map(
      (m) =>
        `<span class="bd-seg" style="width:${(m.amount_yen / total) * 100}%;background:${minColor(m.ministry)}" title="${esc(m.ministry)} ${fmtYen(m.amount_yen)}"></span>`
    )
    .join("");
  const breakdownLegend = byMin
    .filter((m) => m.amount_yen / total >= 0.03)
    .map(
      (m) =>
        `<span class="bd-leg"><span class="bd-dot" style="background:${minColor(m.ministry)}"></span>${esc(m.ministry)} ${Math.round((m.amount_yen / total) * 100)}%（${fmtYen(m.amount_yen)}）</span>`
    )
    .join("");
  const shisakuMinistries = byMin.map((m) => m.ministry);
  const zeroCount = pb.fy2026.top_items.filter((it) => it.amount_yen === 0).length;
  const itemNote = `金額順の全 ${pb.fy2026.top_items.length} 施策（合算は総額に一致）。施策名は一次ソースの階層見出し、説明文は省略せず全文表示。${zeroCount ? `うち「0円」${zeroCount} 件は当該施策に新規のR8当初予算が無い（既存予算内での対応または他事業の内数）ことを示す。` : ""}内訳の原典は出典PDFに記載。`;
  document.getElementById("policy-budget").innerHTML = `
  <div class="budget-hero">
    <div class="budget-hero-main">
      <div class="budget-hero-label">令和8年度 当初予算（総合的対応策 関係予算 合計）</div>
      <div class="budget-hero-num" data-count="${cur.amount_yen}" data-fmt="yen">${fmtYen(cur.amount_yen)}</div>
      ${exactTag(cur.amount_yen)}
      <div class="budget-hero-delta">前年度比 <span class="delta up surge big"><span class="delta-arr" aria-hidden="true">▲</span>${y.delta_yen >= 0 ? "+" : ""}${fmtYen(y.delta_yen)}（${y.pct >= 0 ? "+" : ""}${y.pct}%）</span></div>
      <div class="budget-hero-supp">前年比 実額：${exactSource(y.delta_yen)}</div>
      <div class="budget-hero-supp">うち令和7年度補正予算 関連: ${fmtYen(pb.fy2026.supplementary_r7_yen)}<span class="exact-sub">${exactSource(pb.fy2026.supplementary_r7_yen)}</span></div>
    </div>
    ${shareBtn(t.text, t.url, "令和8年度 外国人政策 関係予算")}
  </div>
  <div class="budget-trend">${bars}</div>
  <div class="breakdown">
    <div class="bd-head">増額の正体 — この${fmtYen(total)}は何に使われるのか（主管省庁別）</div>
    <div class="bd-lead"><span class="bd-lead-pct">${leadPct}%</span><span class="bd-lead-txt">が <b>${esc(lead.ministry)}</b>（観光・オーバーツーリズム対策等）。<span class="bd-lead-amt">${fmtYen(lead.amount_yen)}</span></span></div>
    <div class="bd-bar">${breakdownBar}</div>
    <div class="bd-legend">${breakdownLegend}</div>
    <div class="bd-note">前年度の関係予算 ${fmtYen(POLICY.initial_budget_series.find((s) => s.year === 2025).amount_yen)} から急増した主因は、令和8年1月の会議体改組で新規計上された観光・インフラ対策。在留外国人への給付ではない。</div>
  </div>
  <p class="pair-note budget-caveat"><i>!</i> ${esc(pb.scope_note)}</p>
  <div class="budget-cols">
    <div class="budget-col">
      <div class="budget-col-h">FY2026 主管省庁別（当初予算・全省庁）
        <span class="sort-seg mini" id="budget-min-sort" role="group" aria-label="省庁の並び替え">
          <button type="button" class="sort-btn on" data-min="amount">予算順</button>
          <button type="button" class="sort-btn" data-min="name">省庁名順</button>
        </span>
      </div>
      <div id="budget-min-list">${mins}</div>
      <div class="budget-col-foot">※施策の主管（筆頭）省庁で集計。複数省庁施策は筆頭省庁に計上。最大の国土交通省は観光・オーバーツーリズム対策が中心。金額は丸め値の下に1円単位の実額を併記。</div>
    </div>
    <div class="budget-col" id="fy2026-shisaku">
      <div class="budget-col-h">FY2026 施策一覧（金額順・全文・全${pb.fy2026.top_items.length}件）</div>
      <div class="shisaku-controls">
        <input id="shisaku-q" type="search" placeholder="施策名・省庁・本文で検索（例: 観光 / 在留 / 技能実習）" aria-label="施策を検索" value="${esc(state.shisaku.q)}">
        <select id="shisaku-ministry" aria-label="省庁で絞り込み">
          <option value="">すべての省庁</option>
          ${shisakuMinistries.map((m) => `<option value="${esc(m)}" ${m === state.shisaku.ministry ? "selected" : ""}>${esc(m)}</option>`).join("")}
        </select>
        <label class="toggle"><input type="checkbox" id="shisaku-zero" ${state.shisaku.zeroOnly ? "checked" : ""}> 0円のみ</label>
      </div>
      <div class="shisaku-count" id="shisaku-count"></div>
      <ul class="budget-items" id="budget-items"></ul>
      <div class="budget-col-foot">${itemNote}</div>
    </div>
  </div>
  <p class="budget-basis">${esc(pb.basis_note)} 出典: <a href="${esc(pb.primary_source.url)}" target="_blank" rel="noopener">${esc(pb.primary_source.label)} ↗</a></p>`;
  renderShisakuList();
  bindShisaku();
}

function bindShisaku() {
  const q = document.getElementById("shisaku-q");
  const mi = document.getElementById("shisaku-ministry");
  const zero = document.getElementById("shisaku-zero");
  if (!q || q.dataset.bound) return;
  q.dataset.bound = "1";
  q.addEventListener("input", (e) => {
    state.shisaku.q = e.target.value;
    renderShisakuList();
  });
  mi.addEventListener("change", (e) => {
    state.shisaku.ministry = e.target.value;
    renderShisakuList();
  });
  zero.addEventListener("change", (e) => {
    state.shisaku.zeroOnly = e.target.checked;
    renderShisakuList();
  });
}

/* ===== 東京都ビュー（国⇔東京都トグル） ===== */
let TOKYO = null;

function tokyoTweet(it) {
  return {
    text: [
      `【東京都 令和8年度 外国人政策予算】`,
      `${it.name}: ${fmtYen(it.amount_yen)}（${it.bureau}）`,
      `前年比 ${it.delta_yen >= 0 ? "+" : ""}${fmtYen(it.delta_yen)}`,
      `※主要事業ベース。出典は東京都財務局（リンク先）`,
    ].join("\n"),
    url: (TOKYO && TOKYO.source.url) || "https://www.zaimu.metro.tokyo.lg.jp/",
  };
}

function renderTokyo(tk, pb) {
  TOKYO = tk;
  const govTokyoBtn = document.querySelector('.gov-btn[data-gov="tokyo"]');
  if (!tk) {
    if (govTokyoBtn) govTokyoBtn.hidden = true; // データ未取得時はトグルを隠す
    return;
  }
  const natTotal = pb.fy2026.initial_total_yen;
  const maxB = Math.max(...tk.by_bureau.map((b) => b.amount_yen), 1);
  const bureauBars = tk.by_bureau
    .map(
      (b) => `<div class="min-item"><div class="min-row">
      <span class="min-name">${esc(b.bureau)}</span>
      <span class="min-track"><span class="min-fill" style="width:${Math.max((b.amount_yen / maxB) * 100, 2)}%"></span></span>
      <span class="min-val">${fmtYen(b.amount_yen)}</span></div>${exactTag(b.amount_yen)}</div>`
    )
    .join("");
  const items = tk.items
    .map((it) => {
      const d = it.prev_yen ? { abs: it.delta_yen, pct: (it.delta_yen / it.prev_yen) * 100 } : null;
      const t = tokyoTweet(it);
      return `<li>
      <div class="ti-head">
        <span class="ti-amt">${fmtYen(it.amount_yen)}</span>
        <span class="tag">${esc(it.bureau)}</span><span class="tag kw">${esc(it.category)}</span>
        ${d ? deltaBadge(d) : ""}
        ${shareBtn(t.text, t.url, it.name)}
      </div>
      ${exactTag(it.amount_yen)}
      <div class="ti-title">${esc(it.name)}</div>
      ${it.sub_programs && it.sub_programs.length ? `<div class="ti-desc">${esc(it.sub_programs.join("／"))}</div>` : ""}
    </li>`;
    })
    .join("");
  document.getElementById("tokyo").innerHTML = `
  <div class="budget-hero">
    <div class="budget-hero-main">
      <div class="budget-hero-label">東京都 令和8年度 外国人政策（多文化共生・外国人材）予算 合計</div>
      <div class="budget-hero-num" data-count="${tk.total_yen}" data-fmt="yen">${fmtYen(tk.total_yen)}</div>
      ${exactTag(tk.total_yen)}
      <div class="budget-hero-supp">参考: 国の関係予算（総合的対応策）は ${fmtYen(natTotal)}。集計範囲・主体が異なる（国は全省庁横断、都は多文化共生・外国人材に限定）。</div>
    </div>
    ${shareBtn(`【東京都 令和8年度 外国人政策予算】多文化共生・外国人材の主要事業で計${fmtYen(tk.total_yen)}（生活文化局・産業労働局）。出典は東京都財務局。`, tk.source.url, "東京都 外国人政策予算")}
  </div>
  ${tk.tourism ? tokyoContrastHtml(tk) : ""}
  <div class="budget-cols">
    <div class="budget-col">
      <div class="budget-col-h">局別内訳（令和8年度・主要事業）</div>
      <div>${bureauBars}</div>
    </div>
    <div class="budget-col">
      <div class="budget-col-h">事業一覧（金額順・全文）</div>
      <ul class="budget-items">${items}</ul>
    </div>
  </div>
  <p class="pair-note budget-caveat"><i>!</i> ${esc(tk.tourism_note)}</p>
  ${tk.external_report ? tokyoReportHtml(tk.external_report) : ""}
  <p class="budget-basis">${esc(tk.basis_note)} 出典: <a href="${esc(tk.source.url)}" target="_blank" rel="noopener">${esc(tk.source.label)} ↗</a></p>`;
}

function tokyoReportHtml(er) {
  return `<div class="report-note">
    <div class="rn-head"><i class="rn-i">!</i> 外部報道（NHK）の「8.1億円」との定義の違い</div>
    <div class="rn-bars">
      <div class="rn-bar"><span class="rn-label">NHK報道（自治体アンケート）</span><span class="rn-val">${fmtYen(er.reported_yen)}</span></div>
      <div class="rn-bar"><span class="rn-label">当アプリ（主要事業PDF・4重検証済みの外国人材）</span><span class="rn-val ours">${fmtYen(er.ours_yen)}</span></div>
    </div>
    <p class="rn-body">${esc(er.explanation)}</p>
    <p class="rn-src">報道: ${esc(er.report_label)}（テレビ報道のためURLなし）／検証根拠: <a href="${esc(TOKYO.source.url)}" target="_blank" rel="noopener">${esc(TOKYO.source.label)} ↗</a></p>
  </div>`;
}

function tokyoContrastHtml(tk) {
  const tour = tk.tourism;
  const fp = tk.total_yen;
  const max = Math.max(tour.amount_yen, fp, 1);
  const t = tokyoTweet({ name: "観光産業の振興", amount_yen: tour.amount_yen, bureau: tour.bureau, delta_yen: tour.delta_yen });
  const subs = (tour.sub_items || [])
    .map((s) => `<span class="bd-leg"><span class="bd-dot" style="background:#fbbf24"></span>${esc(s.name)} ${fmtYen(s.amount_yen)}</span>`)
    .join("");
  const row = (label, amt, color, exact) => `
    <div class="cbar-row">
      <div class="cbar-label">${esc(label)}</div>
      <div class="cbar-track"><div class="cbar-fill" style="width:${Math.max((amt / max) * 100, 0.8)}%;background:${color}"></div></div>
      <div class="cbar-val" style="color:${color}">${fmtYen(amt)}</div>
    </div>
    <div class="cbar-exact">${exact}</div>`;
  return `<div class="breakdown tokyo-contrast">
    <div class="bd-head">本当の予算の正体 — 東京都は「外国人政策」より「観光・インフラ」が圧倒的に巨大</div>
    <div class="bd-lead"><span class="bd-lead-pct">${tk.contrast_ratio}倍</span><span class="bd-lead-txt">観光産業の振興（<b>${fmtYen(tour.amount_yen)}</b>）は、外国人政策（多文化共生・外国人材 ${fmtYen(fp)}）の約 ${tk.contrast_ratio} 倍。</span></div>
    ${row("観光産業の振興", tour.amount_yen, "#fbbf24", exactTag(tour.amount_yen))}
    ${row("外国人政策（多文化共生・外国人材）", fp, "#7aa7ff", exactTag(fp))}
    <div class="bd-legend">${subs}</div>
    <div class="bd-note">「外国人優遇でばらまき」という通説に対し、東京都の金額規模ではむしろ観光・インフラ予算が桁違いに大きい（観光は前年比 ${tour.delta_yen >= 0 ? "+" : ""}${fmtYen(tour.delta_yen)}）。${shareBtn(t.text, t.url, "東京都 観光予算")}</div>
  </div>`;
}

let govMode = "national";
function setGov(mode) {
  govMode = mode;
  const tokyo = mode === "tokyo";
  document.querySelectorAll(".gov-btn").forEach((b) => b.classList.toggle("on", b.dataset.gov === mode));
  // 国側の要素
  document.getElementById("year-tabs").hidden = tokyo;
  document.getElementById("compare-section").hidden = tokyo;
  if (tokyo) {
    document.getElementById("policy-budget-section").hidden = true;
    document.getElementById("kpi").hidden = true;
    document.getElementById("amount-note").hidden = true;
    document.getElementById("ranking-section").hidden = true;
  } else {
    setYear(state.year || FY_BUDGET); // 国モードに戻すと現在の年度タブの表示を復元
  }
  // 東京都セクション
  document.getElementById("tokyo-section").hidden = !tokyo;
  window.scrollTo({ top: 0, behavior: "auto" });
}

function bindGov() {
  const tg = document.getElementById("gov-toggle");
  if (!tg) return;
  tg.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-gov]");
    if (btn && !btn.hidden) setGov(btn.dataset.gov);
  });
}

function renderComparisons(compData) {
  document.getElementById("compare").innerHTML = compData.comparisons
    .map((comp) => {
      const fy = comp.fiscal_year || compData.fiscal_year;
      const max = Math.max(...comp.sides.map((s) => s.budget_yen || 0), 1);
      const t = comparisonTweet(comp, fy);
      const sides = comp.sides
        .map((s) => {
          const amountHtml = s.budget_yen != null
            ? `<div class="side-amount">${fmtYen(s.budget_yen)}<span class="side-fy">令和8年度予算</span></div>${exactTag(s.budget_yen)}
               <div class="bar-track"><div class="bar" style="width:${Math.max((s.budget_yen / max) * 100, 1)}%"></div></div>`
            : `<div class="side-amount na">${esc(s.budget_note || "金額は単価で比較")}</div>`;
          return `
    <div class="side">
      <div class="side-target">${esc(s.target)}</div>
      <div class="side-name">${esc(s.name)}</div>
      ${amountHtml}
      ${s.per_person.length ? `<div class="pp">${s.per_person.map((p) => `<span class="tag pp-tag">${esc(p.label)}: ${esc(p.text)}</span>`).join("")}</div>` : ""}
      <div class="meta">
        ${s.budget_source ? `<a class="src-link" href="${esc(s.budget_source.url)}" target="_blank" rel="noopener">${esc(s.budget_source.label)} ↗</a>` : ""}
        ${s.per_person_source && s.per_person_source.url !== (s.budget_source || {}).url ? `<a class="src-link" href="${esc(s.per_person_source.url)}" target="_blank" rel="noopener">${esc(s.per_person_source.label)} ↗</a>` : ""}
      </div>
    </div>`;
        })
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
  const popSeries = (statsData.indicators.population_total || {}).series || [];
  const popRec = popSeries.find((s) => s.year === share.year);
  const pop = popRec ? popRec.value : null;
  const la = z.latest_actual; // ISAプレスの最新実績（年次ダッシュボードより新しい）
  const headVal = la ? la.value : latest.value;
  const headLabel = la ? `${esc(la.as_of)}・取得可能な最新実績` : `全国・${latest.year}年`;
  const yoyLine = la && la.yoy_abs != null
    ? `<div class="sub">前年${la.month === 12 ? "末" : "同期"}比 +${la.yoy_abs.toLocaleString("ja-JP")}人（+${la.yoy_pct}%）</div>`
    : "";
  document.getElementById("stats").innerHTML = `
    <div class="kpi stat-card">
      <div class="label">${esc(z.name)}<span class="as-of">${headLabel}</span></div>
      <div class="value">${(headVal / 1e4).toLocaleString("ja-JP", { maximumFractionDigits: 1 })}<small> 万人</small></div>
      <span class="exact-sub">元データ：${headVal.toLocaleString("ja-JP")}人</span>
      ${yoyLine}
      ${sparkline(zs)}
      <div class="sub">推移（年次・e-Stat）：${first.year}年 ${first.value.toLocaleString("ja-JP")}人 → ${latest.year}年 ${latest.value.toLocaleString("ja-JP")}人</div>
      <div class="sub">${la ? `<a href="${esc(la.source.url)}" target="_blank" rel="noopener">最新実績の出典: ${esc(la.source.label)} ↗</a>　` : ""}<a href="${esc(srcUrl)}" target="_blank" rel="noopener">推移: e-Stat 統計ダッシュボード ↗</a></div>
    </div>
    <div class="kpi stat-card">
      <div class="label">総人口に占める割合（${share.year}年）</div>
      <div class="value">${share.value}<small> %</small></div>
      <span class="exact-sub">元データ：在留外国人 ${z.latest.value.toLocaleString("ja-JP")}人 ÷ 総人口 ${pop ? pop.toLocaleString("ja-JP") + "人" : "—"}</span>
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
    <div class="amount ${p.budget_yen == null ? "na" : ""}">${fmtYen(p.budget_yen)}${deltaBadge(d)}${p.budget_yen != null ? exactTag(p.budget_yen) : ""}</div>
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
  const labels = { true: "事実", false: "誤り", conditional: "条件付き", misleading: "誤解・誇張" };
  document.getElementById("claims").innerHTML = claimsData.claims
    .map((c) => {
      const label = labels[c.verdict] || c.verdict;
      const t = claimTweet(c, label);
      return `<article class="claim-card">
  <div class="claim-head"><span class="verdict ${esc(c.verdict)}">${label}</span>${shareBtn(t.text, t.url, c.claim, "論破をシェア")}</div>
  <p class="claim-text"><span class="claim-tag">ネットの言説</span>「${esc(c.claim)}」</p>
  <p class="fact"><span class="fact-tag">一次ソースの実額で論破</span>${esc(c.fact)}</p>
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
  const budgetMode = y === FY_BUDGET;
  // 行政事業レビュー系（KPI・注記・ランキング）と 関係予算セクションを排他表示
  document.getElementById("policy-budget-section").hidden = !budgetMode;
  document.getElementById("kpi").hidden = budgetMode;
  document.getElementById("amount-note").hidden = budgetMode;
  document.getElementById("ranking-section").hidden = budgetMode;
  renderYearTabs();
  if (budgetMode) {
    window.scrollTo({ top: 0, behavior: "auto" });
    return;
  }
  state.meta = state.yearData[y];
  state.projects = state.meta.projects;
  state.shown = 20;
  document.getElementById("fy-label").textContent =
    `FY${state.meta.fiscal_year} 当初予算・自動抽出 ${state.projects.length} 事業`;
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
  const finalText = fmtBy(kind, to);
  if (prefersReduced || !isFinite(to)) {
    el.textContent = finalText;
    return;
  }
  const dur = 1100;
  const start = performance.now();
  const tick = (now) => {
    const p = Math.min((now - start) / dur, 1);
    const eased = 1 - Math.pow(1 - p, 3);
    el.textContent = fmtBy(kind, Math.max(0, to * eased));
    if (p < 1) requestAnimationFrame(tick);
    else el.textContent = finalText;
  };
  requestAnimationFrame(tick);
  // バックストップ: requestAnimationFrameがタブ非アクティブ等で中断しても、
  // 必ず正しい最終値（一次ソースの実額に対応する丸め値）に収束させる（誤表示の防止）
  setTimeout(() => {
    el.textContent = finalText;
  }, dur + 200);
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

/* ===== ドロワー目次（サイドバー） ===== */
function setDrawer(open) {
  const d = document.getElementById("drawer");
  const bd = document.getElementById("drawer-backdrop");
  const tg = document.getElementById("menu-toggle");
  d.hidden = !open;
  bd.hidden = !open;
  tg.setAttribute("aria-expanded", open ? "true" : "false");
  requestAnimationFrame(() => d.classList.toggle("open", open));
}

function navTo(target) {
  setDrawer(false);
  if (target === "top") {
    window.scrollTo({ top: 0, behavior: "smooth" });
    return;
  }
  // 目次の項目は国（政府）側のセクション。東京都モードなら国モードに戻す。
  if (govMode === "tokyo") setGov("national");
  // 予算内訳・施策一覧はFY2026タブ専用。必要なら先にタブを切り替える
  const needsBudget = target === "budget" || target === "shisaku";
  if (needsBudget && state.year !== FY_BUDGET) setYear(FY_BUDGET);
  const idMap = {
    budget: "policy-budget-section",
    shisaku: "fy2026-shisaku",
    compare: "compare-section",
    stats: "stats-section",
  };
  const el = document.getElementById(idMap[target]);
  if (el) requestAnimationFrame(() => el.scrollIntoView({ behavior: "smooth", block: "start" }));
}

function bindDrawer() {
  document.getElementById("menu-toggle").addEventListener("click", () => setDrawer(document.getElementById("drawer").hidden));
  document.getElementById("drawer-close").addEventListener("click", () => setDrawer(false));
  document.getElementById("drawer-backdrop").addEventListener("click", () => setDrawer(false));
  document.getElementById("drawer").addEventListener("click", (e) => {
    const a = e.target.closest("[data-nav]");
    if (!a) return;
    e.preventDefault();
    navTo(a.dataset.nav);
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !document.getElementById("drawer").hidden) setDrawer(false);
  });
}

function bind() {
  bindDrawer();
  bindGov();
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
  const [yearsMeta, claimsData, compData, statsData, policyBudget, glossary, tokyoData] = await Promise.all([
    getJson("data/years.json"),
    getJson("data/claims.json"),
    getJson("data/comparisons.json"),
    getJson("data/stats.json"),
    getJson("data/policy_budget.json"),
    getJson("data/glossary.json"),
    getJson("data/tokyo.json").catch(() => null), // best-effort: 無ければ東京都タブを隠す
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
  renderTokyo(tokyoData, policyBudget);
  renderComparisons(compData);
  renderStats(statsData);
  renderClaims(claimsData);
  bind();
  setYear(FY_BUDGET); // 既定はFY2026（最新）タブ＝関係予算ビュー
  // #list は renderList 内で個別にツールチップ化済み。残りの静的・予算・比較・統計・言説領域を一括処理。
  applyGlossary(document.querySelector("main"), "#list");
  observeReveals(document);
}

document.documentElement.classList.add("js");
main().catch((e) => {
  document.getElementById("list").innerHTML = `<p class="muted">データの読み込みに失敗しました: ${esc(e.message)}</p>`;
});
