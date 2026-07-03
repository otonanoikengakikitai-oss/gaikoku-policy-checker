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
  shisaku: { q: "", ministry: "", zeroOnly: false, sort: "budget" }, // FY2026 施策一覧の絞り込み・並び替え
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

/* ===== 年度表記の統一: 全タブ・全データを「FY202X（令和X年度）」に統合 ===== */
const REIWA_OFFSET = 2018; // 令和元年 = 2019年度
function waLabel(year) {
  const r = year - REIWA_OFFSET;
  return `令和${r === 1 ? "元" : r}年度`;
}
function fyTag(year) {
  return `FY${year}（${waLabel(year)}）`;
}

/* ===== 国・東京都・川口で共通のリッチ部品（同一CSS・同一情報密度） ===== */
// カテゴリ→色（地方タブの内訳バー・積み上げで使用）
const CAT_COLORS = {
  多文化共生: "#7aa7ff",
  外国人材: "#34d399",
  日本語教育: "#f0997b",
  外国人相談: "#c084fc",
};
const LOCAL_PALETTE = ["#7aa7ff", "#34d399", "#fbbf24", "#f0997b", "#c084fc", "#f87171"];
const catColor = (c, i = 0) => CAT_COLORS[c] || LOCAL_PALETTE[i % LOCAL_PALETTE.length];

// 多年度トレンドの横バー（国の budget-trend と同一CSS）。rows: [{year, amount_yen, sourceUrl?}]
function trendChartHtml(rows, hotYear) {
  if (!rows || rows.length < 2) return ""; // 1年度のみならトレンドは描かない
  const max = Math.max(...rows.map((r) => r.amount_yen), 1);
  const body = rows
    .map((r) => {
      const hot = r.year === hotYear;
      return `<div class="budget-bar-row">
      <div class="budget-bar-label">FY${r.year}<span class="budget-bar-sub">${esc(waLabel(r.year))}</span></div>
      <div class="budget-bar-track"><div class="budget-bar-fill ${hot ? "hot" : ""}" style="width:${Math.max((r.amount_yen / max) * 100, 1.5)}%"></div></div>
      <div class="budget-bar-val ${hot ? "hot" : ""}">${fmtYen(r.amount_yen)}${r.sourceUrl ? `<a class="src-mini" href="${esc(r.sourceUrl)}" target="_blank" rel="noopener" aria-label="FY${r.year}の出典">出典↗</a>` : ""}<span class="exact-sub">${exactSource(r.amount_yen)}</span></div>
    </div>`;
    })
    .join("");
  return `<div class="budget-trend">${body}</div>`;
}

// ヒーロー内の前年度比デルタ（国の budget-hero-delta と同一表示）。前年度が無ければ空。
function heroDeltaHtml(cur, prev) {
  if (prev == null || prev <= 0) return "";
  const d = cur - prev;
  const pct = Math.round((d / prev) * 1000) / 10;
  const up = d >= 0;
  return `<div class="budget-hero-delta">前年度比 <span class="delta ${up ? "up" : "down"} big" title="前年度予算比"><span class="delta-arr" aria-hidden="true">${up ? "▲" : "▼"}</span>${up ? "+" : ""}${fmtYen(d)}（${up ? "+" : ""}${pct}%）</span></div>
    <div class="budget-hero-supp">前年比 実額：${exactSource(d)}</div>`;
}

// 横バー一覧（国の省庁別 min-item と同一CSS）。rows: [{name, amount_yen, color?}]
function barListHtml(rows) {
  const max = Math.max(...rows.map((r) => r.amount_yen), 1);
  return rows
    .map(
      (r) => `<div class="min-item"><div class="min-row">
      <span class="min-name">${esc(r.name)}</span>
      <span class="min-track"><span class="min-fill" style="width:${Math.max((r.amount_yen / max) * 100, 2)}%${r.color ? `;background:${r.color}` : ""}"></span></span>
      <span class="min-val">${fmtYen(r.amount_yen)}</span></div>${exactTag(r.amount_yen)}</div>`
    )
    .join("");
}

// 100%積み上げ割合バー＋凡例（国の bd-bar/bd-legend と同一CSS）。segs: [{name, amount_yen, color}]
function stackedBreakdownHtml(segs, total, minLegendRatio = 0.001) {
  const bar = segs
    .map((s) => `<span class="bd-seg" style="width:${(s.amount_yen / total) * 100}%;background:${s.color}" title="${esc(s.name)} ${fmtYen(s.amount_yen)}"></span>`)
    .join("");
  const legend = segs
    .filter((s) => s.amount_yen / total >= minLegendRatio)
    .map((s) => {
      const pct = (s.amount_yen / total) * 100;
      const pctTxt = pct >= 1 ? Math.round(pct) : pct.toFixed(2);
      return `<span class="bd-leg"><span class="bd-dot" style="background:${s.color}"></span>${esc(s.name)} ${pctTxt}%（${fmtYen(s.amount_yen)}）</span>`;
    })
    .join("");
  return `<div class="bd-bar">${bar}</div><div class="bd-legend">${legend}</div>`;
}

/* ===== 広告プレースホルダー（AdSense用・控えめな静的枠） ===== */
const AD_SLOT_AFTER = 3; // 事業一覧リストで何件目の下に挿入するか
function adSlotHtml(extra = "") {
  return `<aside class="ad-slot ${extra}" aria-label="広告枠"><span class="ad-slot-label">スポンサーリンク</span><div class="ad-slot-space"></div></aside>`;
}
// リストHTML配列の中間（AD_SLOT_AFTER件目の下）に広告枠を挿入。件数が少なければ末尾。
function insertAdSlot(htmlArr, wrapTag = "") {
  if (!htmlArr.length) return htmlArr;
  const ad = wrapTag ? `<${wrapTag} class="ad-slot-li">${adSlotHtml()}</${wrapTag}>` : adSlotHtml();
  const pos = Math.min(AD_SLOT_AFTER, htmlArr.length);
  return [...htmlArr.slice(0, pos), ad, ...htmlArr.slice(pos)];
}

/* ===== 検索・絞り込み・並び替え付きリストUI（国の予算事業ランキングと同じ高度UIを全タブに） ===== */
const LIST_FILTERS = {
  tokyo: { q: "", cat: "", sort: "budget" },
  hokkaido: { q: "", cat: "", sort: "budget" },
  aichi: { q: "", cat: "", sort: "budget" },
  osaka: { q: "", cat: "", sort: "budget" },
  fukuoka: { q: "", cat: "", sort: "budget" },
  kanagawa: { q: "", cat: "", sort: "budget" },
  kyoto: { q: "", cat: "", sort: "budget" },
  miyagi: { q: "", cat: "", sort: "budget" },
  hiroshima: { q: "", cat: "", sort: "budget" },
  okayama: { q: "", cat: "", sort: "budget" },
  saitama: { q: "", cat: "", sort: "budget" },
  kawaguchi: { q: "", cat: "", sort: "budget" },
};

// 同名事業を前年度と突き合わせて各事業に前年比 _delta {abs,pct} を付与（ソート・バッジ用）。
// 川口市等は年度で「（継続）（拡充）（臨時）（新規）」の状態サフィックスが変わるため、
// 正規化除去してから突合する（同一事業の年度間マッチを取りこぼさない）。
function normEventName(name) {
  return String(name || "").replace(/（(継続|拡充|臨時|新規|新)）/g, "").trim();
}
function attachDeltas(items, prevItems) {
  const prevByName = {};
  (prevItems || []).forEach((p) => {
    prevByName[normEventName(p.name)] = p.amount_yen;
  });
  return items.map((it) => {
    const pv = prevByName[normEventName(it.name)];
    const _delta = pv != null && pv > 0 && it.amount_yen != null ? { abs: it.amount_yen - pv, pct: ((it.amount_yen - pv) / pv) * 100 } : null;
    return { ...it, _delta };
  });
}

// 検索ボックス＋カテゴリ絞り込み＋並び替えトグル＋件数＋リスト容器（国のランキングUIと同一デザイン）
function listControlsHtml(prefix, categories, filter, total, fyL) {
  const cats = [...new Set(categories)];
  const catSel =
    cats.length > 1
      ? `<select id="${prefix}-cat" aria-label="カテゴリで絞り込み"><option value="">すべてのカテゴリ</option>${cats
          .map((c) => `<option value="${esc(c)}" ${c === filter.cat ? "selected" : ""}>${esc(c)}</option>`)
          .join("")}</select>`
      : "";
  const sort = filter.sort || "budget";
  const sb = (key, label) => `<button type="button" class="sort-btn ${sort === key ? "on" : ""}" data-lsort="${prefix}:${key}">${label}</button>`;
  return `<div class="budget-col-h">事業一覧（検索・絞り込み・並び替え／${esc(fyL)}・全${total}件）</div>
    <div class="shisaku-controls">
      <input id="${prefix}-q" type="search" placeholder="事業名・本文で検索" aria-label="事業を検索" value="${esc(filter.q)}">
      ${catSel}
    </div>
    <div class="sort-seg" role="group" aria-label="並び替え">
      <span class="sort-lbl">並び替え</span>
      ${sb("budget", "予算額が大きい順")}${sb("deltaPct", "前年比 増加率順")}${sb("deltaAbs", "前年比 増加額順")}
    </div>
    <div class="shisaku-count" id="${prefix}-count"></div>
    <ul class="budget-items" id="${prefix}-ul"></ul>`;
}

// 現在のフィルタ・並び順で items を描画（入力欄は再生成しないのでフォーカスは保持）
function renderFilteredList(prefix, items, textOf, cardOf) {
  const f = LIST_FILTERS[prefix];
  let rows = items.filter((it) => {
    if (f.cat && it.category !== f.cat) return false;
    const q = f.q.trim();
    if (q && !textOf(it).includes(q)) return false;
    return true;
  });
  const sort = f.sort || "budget";
  if (sort === "deltaPct" || sort === "deltaAbs") {
    const key = sort === "deltaPct" ? "pct" : "abs";
    rows = rows.slice().sort((a, b) => {
      const da = a._delta, db = b._delta;
      if (!da && !db) return (b.amount_yen || 0) - (a.amount_yen || 0);
      if (!da) return 1;
      if (!db) return -1;
      return db[key] - da[key];
    });
  } else {
    rows = rows.slice().sort((a, b) => (b.amount_yen || 0) - (a.amount_yen || 0));
  }
  const sum = rows.reduce((a, it) => a + (it.amount_yen || 0), 0);
  const countEl = document.getElementById(prefix + "-count");
  if (countEl) countEl.textContent = `${rows.length} / ${items.length} 事業${rows.length ? `・絞り込み合計 ${fmtYen(sum)}` : ""}`;
  const ul = document.getElementById(prefix + "-ul");
  if (ul) {
    ul.innerHTML = insertAdSlot(rows.map(cardOf), "li").join("") || `<li class="muted" style="border:none">該当する事業がありません。</li>`;
    applyGlossary(ul);
  }
}

// 4つのサマリーカード（国の #kpi と同一デザイン）。地方タブにも国と同じKPI帯を表示する。
function localKpiHtml(cards) {
  return (
    `<div class="kpi-grid local-kpi">` +
    cards
      .map(
        (c) => `<div class="kpi">
      <div class="label">${esc(c.label)}</div>
      <div class="value${c.fy ? " fy-value" : ""}">${c.value}${c.unit ? `<small> ${esc(c.unit)}</small>` : ""}${c.badge || ""}</div>
      ${c.exact || ""}
      ${c.sub ? `<div class="sub">${c.sub}</div>` : ""}
    </div>`
      )
      .join("") +
    `</div>`
  );
}

// 合計の前年比デルタを deltaBadge 用の {abs,pct} に整形（前年が無ければ null）
function totalDelta(cur, prev) {
  return prev ? { abs: cur - prev, pct: ((cur - prev) / prev) * 100 } : null;
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

function yearTabHtml(year, on, opts = {}) {
  // 全タブ共通の年度ボタン: 「FY202X」を主、「令和X年度」を副ラベルで2段表示（表記統一）
  const extra = opts.budget ? " budget-tab" : "";
  const latest = opts.latest ? `<span class="tab-latest">最新</span>` : "";
  return `<button class="year-tab${extra} ${on ? "on" : ""}" data-year="${year}"><span class="yt-main"><span class="yt-fy">FY${year}</span><span class="yt-wa">${esc(waLabel(year))}</span></span>${latest}</button>`;
}

function renderYearTabs() {
  const tabs = state.years.map((y) => yearTabHtml(y, y === state.year));
  tabs.push(yearTabHtml(FY_BUDGET, state.year === FY_BUDGET, { budget: true, latest: true }));
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
      <div class="value fy-value">${fyTag(m.fiscal_year)}</div>
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
  // 並び替え（関係予算は単年度スナップショットのため前年比ではなく予算額/省庁/施策名で）
  const sk = state.shisaku.sort || "budget";
  if (sk === "ministry") rows.sort((a, b) => (a.ministry || "").localeCompare(b.ministry || "", "ja") || b.amount_yen - a.amount_yen);
  else if (sk === "name") rows.sort((a, b) => (a.title || a.desc || "").localeCompare(b.title || b.desc || "", "ja"));
  else rows.sort((a, b) => b.amount_yen - a.amount_yen);
  const sumYen = rows.reduce((a, it) => a + it.amount_yen, 0);
  document.getElementById("shisaku-count").textContent =
    `${rows.length} / ${all.length} 施策${rows.length ? `・絞り込み合計 ${fmtYen(sumYen)}` : ""}`;
  document.getElementById("budget-items").innerHTML =
    insertAdSlot(
      rows.map((it) => {
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
      }),
      "li"
    ).join("") || `<li class="muted" style="border:none">該当する施策がありません。</li>`;
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
      <div class="budget-hero-label">${esc(fyTag(cur.year))} 当初予算（総合的対応策 関係予算 合計）</div>
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
      <div class="budget-col-h">FY2026 施策一覧（検索・絞り込み・並び替え・全文・全${pb.fy2026.top_items.length}件）</div>
      <div class="shisaku-controls">
        <input id="shisaku-q" type="search" placeholder="施策名・省庁・本文で検索（例: 観光 / 在留 / 技能実習）" aria-label="施策を検索" value="${esc(state.shisaku.q)}">
        <select id="shisaku-ministry" aria-label="省庁で絞り込み">
          <option value="">すべての省庁</option>
          ${shisakuMinistries.map((m) => `<option value="${esc(m)}" ${m === state.shisaku.ministry ? "selected" : ""}>${esc(m)}</option>`).join("")}
        </select>
        <label class="toggle"><input type="checkbox" id="shisaku-zero" ${state.shisaku.zeroOnly ? "checked" : ""}> 0円のみ</label>
      </div>
      <div class="sort-seg" id="shisaku-sort" role="group" aria-label="並び替え">
        <span class="sort-lbl">並び替え</span>
        <button type="button" class="sort-btn ${state.shisaku.sort === "budget" ? "on" : ""}" data-ssort="budget">予算額が大きい順</button>
        <button type="button" class="sort-btn ${state.shisaku.sort === "ministry" ? "on" : ""}" data-ssort="ministry">所管省庁順</button>
        <button type="button" class="sort-btn ${state.shisaku.sort === "name" ? "on" : ""}" data-ssort="name">施策名順</button>
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
  const sortSeg = document.getElementById("shisaku-sort");
  if (sortSeg)
    sortSeg.addEventListener("click", (e) => {
      const b = e.target.closest("[data-ssort]");
      if (!b) return;
      state.shisaku.sort = b.dataset.ssort;
      sortSeg.querySelectorAll(".sort-btn").forEach((x) => x.classList.toggle("on", x === b));
      renderShisakuList();
    });
}

/* ===== 東京都ビュー（国⇔東京都トグル・多年度） ===== */
let TOKYO = null; // tokyo.json 全体（years[] を含む）。source は data 直下で共通。
let TOKYO_PB = null; // 参考表示用の国の関係予算
let TOKYO_YEAR = null; // 東京都ビューで選択中の年度（他自治体と独立管理）

function tokyoTweet(it, fyLabel) {
  return {
    text: [
      `【東京都 ${fyLabel || "外国人政策予算"}】`,
      `${it.name}: ${fmtYen(it.amount_yen)}（${it.bureau}）`,
      it.delta_yen != null ? `前年比 ${it.delta_yen >= 0 ? "+" : ""}${fmtYen(it.delta_yen)}` : "",
      `※主要事業ベース。出典は東京都財務局（リンク先）`,
    ].filter(Boolean).join("\n"),
    url: (TOKYO && TOKYO.source.url) || "https://www.zaimu.metro.tokyo.lg.jp/",
  };
}

function renderTokyo(tk, pb) {
  TOKYO = tk;
  TOKYO_PB = pb;
  const govTokyoBtn = document.querySelector('.gov-btn[data-gov="tokyo"]');
  if (!tk || !tk.years || !tk.years.length) {
    if (govTokyoBtn) { govTokyoBtn.hidden = true; govTokyoBtn.dataset.empty = "1"; } // データ未取得時はトグルを隠す
    return;
  }
  TOKYO_YEAR = tk.latest; // 既定は最新年度
  renderTokyoYearTabs();
  renderTokyoYear(TOKYO_YEAR);
}

function tokyoYear(fy) {
  return (TOKYO && TOKYO.years.find((y) => y.fiscal_year === fy)) || null;
}

function renderTokyoYearTabs() {
  const tabs = document.getElementById("tokyo-year-tabs");
  if (!tabs || !TOKYO) return;
  const years = TOKYO.years.slice().sort((a, b) => b.fiscal_year - a.fiscal_year); // 新しい年度を左に
  tabs.innerHTML = years
    .map((y) => yearTabHtml(y.fiscal_year, y.fiscal_year === TOKYO_YEAR, { latest: y.fiscal_year === TOKYO.latest }))
    .join("");
}

function renderTokyoYear(fy) {
  const yr = tokyoYear(fy);
  const host = document.getElementById("tokyo");
  if (!yr) {
    if (host) host.innerHTML = `<p class="muted">この年度の東京都データは未収録です。</p>`;
    return;
  }
  TOKYO_YEAR = fy;
  renderTokyoYearTabs();
  const tk = TOKYO; // data 直下の共通フィールド（source / basis_note / tourism_note）
  const fyL = fyTag(fy); // 統一表記 FY202X（令和X年度）
  const natTotal = (TOKYO_PB && TOKYO_PB.fy2026 && TOKYO_PB.fy2026.initial_total_yen) || null;
  // 前年度の総額（YoY用）。データに前年度があれば総額、無ければ事業別 prev_yen の合算でフォールバック。
  const prevYr = tokyoYear(fy - 1);
  let prevTotal = prevYr ? prevYr.total_yen : null;
  if (prevTotal == null && yr.items.every((it) => it.prev_yen != null)) {
    prevTotal = yr.items.reduce((a, it) => a + it.prev_yen, 0);
  }
  // 多年度トレンド（国の budget-trend と同一）
  const trendRows = TOKYO.years
    .slice()
    .sort((a, b) => a.fiscal_year - b.fiscal_year)
    .map((y) => ({ year: y.fiscal_year, amount_yen: y.total_yen, sourceUrl: tk.source.url }));
  // 事業別の横バー（国の省庁別 min-item と同一）。カテゴリ色で割合可視化。
  const itemRows = yr.items
    .slice()
    .sort((a, b) => b.amount_yen - a.amount_yen)
    .map((it) => ({ name: it.name, amount_yen: it.amount_yen, color: catColor(it.category) }));
  const itemBars = barListHtml(itemRows);
  // カテゴリ別 100% 積み上げ（多文化共生 vs 外国人材）
  const catMap = {};
  for (const it of yr.items) catMap[it.category] = (catMap[it.category] || 0) + it.amount_yen;
  const catSegs = Object.entries(catMap)
    .sort((a, b) => b[1] - a[1])
    .map(([name, amount_yen]) => ({ name, amount_yen, color: catColor(name) }));
  const catLead = catSegs[0];
  const catLeadPct = Math.round((catLead.amount_yen / yr.total_yen) * 100);
  // 4つのサマリーカード（国 #kpi と同一デザイン。所管府省庁→担当局に読み替え）
  const bureaus = [...new Set(yr.items.map((i) => i.bureau))];
  const tokyoKpi = localKpiHtml([
    { label: "関連事業数（主要事業）", value: yr.items.length, unit: "件", sub: "多文化共生・外国人材の4重検証済み事業" },
    {
      label: "当初予算 合算（外国人政策）",
      value: fmtYen(yr.total_yen),
      badge: prevTotal ? " " + deltaBadge(totalDelta(yr.total_yen, prevTotal), "big") : "",
      exact: exactTag(yr.total_yen),
      sub: `${esc(fyL)}・主要事業ベース`,
    },
    { label: "担当局", value: bureaus.length, unit: "局", sub: esc(bureaus.join("・")) },
    { label: "データ年度", value: esc(fyL), fy: true, sub: "出典: 東京都財務局 主要事業" },
  ]);
  document.getElementById("tokyo").innerHTML = `
  <div class="budget-hero">
    <div class="budget-hero-main">
      <div class="budget-hero-label">東京都 ${esc(fyL)} 外国人政策（多文化共生・外国人材）予算 合計</div>
      <div class="budget-hero-num" data-count="${yr.total_yen}" data-fmt="yen">${fmtYen(yr.total_yen)}</div>
      ${exactTag(yr.total_yen)}
      ${heroDeltaHtml(yr.total_yen, prevTotal)}
      ${natTotal ? `<div class="budget-hero-supp">参考: 国の関係予算（総合的対応策）は ${fmtYen(natTotal)}。集計範囲・主体が異なる（国は全省庁横断、都は多文化共生・外国人材に限定）。</div>` : ""}
    </div>
    ${shareBtn(`【東京都 ${fyL} 外国人政策予算】多文化共生・外国人材の主要事業で計${fmtYen(yr.total_yen)}（生活文化局・産業労働局）。出典は東京都財務局。`, tk.source.url, "東京都 外国人政策予算")}
  </div>
  ${trendChartHtml(trendRows, fy)}
  ${yr.tourism ? tokyoContrastHtml(yr, fyL) : ""}
  <div class="breakdown">
    <div class="bd-head">外国人政策予算の中身 — カテゴリ別の割合（${esc(fyL)}）</div>
    <div class="bd-lead"><span class="bd-lead-pct">${catLeadPct}%</span><span class="bd-lead-txt">が <b>${esc(catLead.name)}</b>。<span class="bd-lead-amt">${fmtYen(catLead.amount_yen)}</span></span></div>
    ${stackedBreakdownHtml(catSegs, yr.total_yen)}
  </div>
  <div class="budget-cols">
    <div class="budget-col">
      <div class="budget-col-h">事業別内訳（金額順・割合バー／${esc(fyL)}）</div>
      <div>${itemBars}</div>
      <div class="budget-col-foot">※東京都財務局「主要事業」PDFに名称・金額が明記され4重検証を通過した外国人政策（多文化共生・外国人材）事業のみ。金額は丸め値の下に1円単位の実額を併記。</div>
    </div>
    <div class="budget-col">
      ${listControlsHtml("tokyo", yr.items.map((i) => i.category), LIST_FILTERS.tokyo, yr.items.length, fyL)}
    </div>
  </div>
  <div class="local-kpi-band"><div class="local-kpi-h">この年度のサマリー（${esc(fyL)}）</div>${tokyoKpi}</div>
  <p class="pair-note budget-caveat"><i>!</i> ${esc(tk.tourism_note)}</p>
  ${yr.external_report ? tokyoReportHtml(yr.external_report) : ""}
  <p class="budget-basis">${esc(tk.basis_note)}${yr.source_note ? " " + esc(yr.source_note) : ""} 出典: <a href="${esc(tk.source.url)}" target="_blank" rel="noopener">${esc(tk.source.label)} ↗</a></p>`;
  renderTokyoItemList();
  applyGlossary(document.getElementById("tokyo"));
  renderStatsFor("tokyo", fy); // 統計の裏付けを東京都×当該年度に連動
}

function tokyoItemCard(it) {
  const t = tokyoTweet(it, fyTag(TOKYO_YEAR));
  return `<li>
      <div class="ti-head">
        <span class="ti-amt">${fmtYen(it.amount_yen)}</span>
        <span class="tag">${esc(it.bureau)}</span><span class="tag kw">${esc(it.category)}</span>
        ${it._delta ? deltaBadge(it._delta) : ""}
        ${shareBtn(t.text, t.url, it.name)}
      </div>
      ${exactTag(it.amount_yen)}
      <div class="ti-title">${esc(it.name)}</div>
      ${it.sub_programs && it.sub_programs.length ? `<div class="ti-desc">${esc(it.sub_programs.join("／"))}</div>` : ""}
    </li>`;
}

function renderTokyoItemList() {
  const yr = tokyoYear(TOKYO_YEAR);
  if (!yr) return;
  const prev = tokyoYear(TOKYO_YEAR - 1);
  const items = attachDeltas(yr.items, prev && prev.items);
  renderFilteredList(
    "tokyo",
    items,
    (it) => it.name + (it.sub_programs || []).join("") + it.bureau + it.category,
    tokyoItemCard
  );
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

function tokyoContrastHtml(yr, fyLabel) {
  const tour = yr.tourism;
  const fp = yr.total_yen;
  const max = Math.max(tour.amount_yen, fp, 1);
  const t = tokyoTweet({ name: "観光産業の振興", amount_yen: tour.amount_yen, bureau: tour.bureau, delta_yen: tour.delta_yen }, fyLabel);
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
    <div class="bd-lead"><span class="bd-lead-pct">${yr.contrast_ratio}倍</span><span class="bd-lead-txt">観光産業の振興（<b>${fmtYen(tour.amount_yen)}</b>）は、外国人政策（多文化共生・外国人材 ${fmtYen(fp)}）の約 ${yr.contrast_ratio} 倍（${esc(fyLabel)}）。</span></div>
    ${row("観光産業の振興", tour.amount_yen, "#fbbf24", exactTag(tour.amount_yen))}
    ${row("外国人政策（多文化共生・外国人材）", fp, "#7aa7ff", exactTag(fp))}
    <div class="bd-legend">${subs}</div>
    <div class="bd-note">「外国人優遇でばらまき」という通説に対し、東京都の金額規模ではむしろ観光・インフラ予算が桁違いに大きい。${shareBtn(t.text, t.url, "東京都 観光予算")}</div>
  </div>`;
}

/* ===== 埼玉県（メイン）＋川口市（焦点）ビュー・多年度 ===== */
let KAWAGUCHI = null; // saitama_kawaguchi.json 全体（prefecture + spotlight）
let KAWAGUCHI_YEAR = null; // 選択中の年度（県・市で共有）

function saitamaYear(fy) {
  return (KAWAGUCHI && KAWAGUCHI.prefecture && KAWAGUCHI.prefecture.years.find((y) => y.fiscal_year === fy)) || null;
}
function kawaguchiYear(fy) {
  return (KAWAGUCHI && KAWAGUCHI.spotlight && KAWAGUCHI.spotlight.years.find((y) => y.fiscal_year === fy)) || null;
}

function localBudgetTweet(govLabel, yr, ga, fyLabel, sourceUrl) {
  const totalLabel = yenBreakdown(yr.foreign_total_yen);
  return {
    text: [
      `【${govLabel} 外国人特化予算の実額】`,
      `${govLabel}の外国人特化（多文化共生）予算は ${fyLabel} で計${totalLabel}`,
      ga ? `一般会計 ${ga.amount_label} の約${yr.contrast_pct}%に過ぎない` : "",
      `「莫大な税金で優遇」は誇張。出典は公式の当初予算（リンク先）`,
    ].filter(Boolean).join("\n"),
    url: sourceUrl,
  };
}

// 一般会計 vs 外国人特化 の対比（県・市で共通）
function govContrastHtml(opts) {
  const { govLabel, audience, totalLabel, totalYen, ga, contrastPct, fyL, tweet, shareLabel } = opts;
  const denom = Math.round(ga.amount_yen / totalYen).toLocaleString("ja-JP");
  return `<div class="breakdown tokyo-contrast">
    <div class="bd-head">本当の予算の正体 — 「莫大な税金」の実額は${esc(govLabel)}予算の約${contrastPct}%</div>
    <div class="bd-lead"><span class="bd-lead-pct">${contrastPct}%</span><span class="bd-lead-txt">外国人特化予算（<b>${esc(totalLabel)}</b>）は、${esc(govLabel)}の一般会計（${esc(ga.amount_label)}）の<b>約${contrastPct}%（約${denom}分の1）</b>（${esc(fyL)}）。</span></div>
    <div class="cbar-row"><div class="cbar-label">一般会計（${esc(audience)}）</div><div class="cbar-track"><div class="cbar-fill" style="width:100%;background:#7aa7ff"></div></div><div class="cbar-val" style="color:#7aa7ff">${esc(ga.amount_label)}</div></div>
    <div class="cbar-exact">${exactTag(ga.amount_yen)}</div>
    <div class="cbar-row"><div class="cbar-label">外国人特化（多文化共生）</div><div class="cbar-track"><div class="cbar-fill" style="width:0.5%;min-width:3px;background:#fbbf24"></div></div><div class="cbar-val" style="color:#fbbf24">${esc(totalLabel)}</div></div>
    <div class="cbar-exact">${exactTag(totalYen)}</div>
    <div class="bd-note">SNSの『莫大な税金で優遇』という感情論に対し、一次ソースの実額では予算のごく一部（相談・多言語情報支援・日本語教育等）に過ぎない。${shareBtn(tweet.text, tweet.url, shareLabel)}</div>
  </div>`;
}

function renderKawaguchi(kw) {
  KAWAGUCHI = kw;
  const btn = document.querySelector('.gov-btn[data-gov="kawaguchi"]');
  const block = kw && (kw.prefecture || kw.spotlight);
  if (!block || !block.years || !block.years.length) {
    if (btn) { btn.hidden = true; btn.dataset.empty = "1"; } // データ未取得時はタブを隠す
    return;
  }
  KAWAGUCHI_YEAR = block.latest; // 既定は最新年度（県・市で共有）
  renderKawaguchiYearTabs();
  renderKawaguchiYear(KAWAGUCHI_YEAR);
}

function renderKawaguchiYearTabs() {
  const tabs = document.getElementById("kawaguchi-year-tabs");
  const block = KAWAGUCHI && (KAWAGUCHI.prefecture || KAWAGUCHI.spotlight);
  if (!tabs || !block) return;
  const years = block.years.slice().sort((a, b) => b.fiscal_year - a.fiscal_year); // 新しい年度を左に
  tabs.innerHTML = years
    .map((y) => yearTabHtml(y.fiscal_year, y.fiscal_year === KAWAGUCHI_YEAR, { latest: y.fiscal_year === block.latest }))
    .join("");
}

function renderKawaguchiYear(fy) {
  KAWAGUCHI_YEAR = fy;
  renderKawaguchiYearTabs();
  const sy = saitamaYear(fy);
  const ky = kawaguchiYear(fy);
  const fyL = fyTag(fy);
  const host = document.getElementById("kawaguchi");
  if (!sy && !ky) {
    host.innerHTML = `<p class="muted">この年度のデータは未収録です。</p>`;
    return;
  }
  host.innerHTML = (sy ? saitamaMainHtml(sy, fy, fyL) : "") + (ky ? kawaguchiSpotlightHtml(ky, fy, fyL) : "");
  if (sy) renderSaitamaItemList();
  if (ky) renderKawaguchiItemList();
  applyGlossary(host);
  renderStatsFor("kawaguchi", fy); // 統計の裏付けは焦点の川口市に連動
}

// メイン：埼玉県（県全体）の国と同等のリッチビュー
function saitamaMainHtml(yr, fy, fyL) {
  const PREF = KAWAGUCHI.prefecture;
  const ga = yr.general_account;
  const fTotal = yr.foreign_total_yen;
  const totalLabel = yenBreakdown(fTotal);
  const prev = saitamaYear(fy - 1);
  const prevTotal = prev ? prev.foreign_total_yen : null;
  const trendRows = PREF.years.slice().sort((a, b) => a.fiscal_year - b.fiscal_year).map((y) => ({ year: y.fiscal_year, amount_yen: y.foreign_total_yen, sourceUrl: y.source.url }));
  const itemRows = yr.items.slice().sort((a, b) => b.amount_yen - a.amount_yen).map((it, i) => ({ name: it.name, amount_yen: it.amount_yen, color: catColor(it.category, i) }));
  const itemBars = barListHtml(itemRows);
  const evLead = itemRows[0];
  const evLeadPct = evLead ? Math.round((evLead.amount_yen / fTotal) * 100) : 0;
  const evBreakdown = evLead
    ? `<div class="breakdown">
    <div class="bd-head">外国人特化予算の中身 — 事業別の割合（${esc(fyL)}）</div>
    <div class="bd-lead"><span class="bd-lead-pct">${evLeadPct}%</span><span class="bd-lead-txt">が <b>${esc(evLead.name)}</b>。<span class="bd-lead-amt">${fmtYen(evLead.amount_yen)}</span></span></div>
    ${stackedBreakdownHtml(itemRows, fTotal)}
  </div>`
    : "";
  const t = localBudgetTweet("埼玉県", yr, ga, fyL, yr.source.url);
  const contrast = ga
    ? govContrastHtml({ govLabel: "埼玉県", audience: "全県民向け", totalLabel, totalYen: fTotal, ga, contrastPct: yr.contrast_pct, fyL, tweet: t, shareLabel: "埼玉県 外国人特化予算" })
    : "";
  const bureaus = [...new Set(yr.items.map((i) => i.bureau))];
  const kpi = localKpiHtml([
    { label: "関連事業数（外国人特化）", value: yr.items.length, unit: "件", sub: "県民生活部 国際課の多文化共生関連" },
    { label: "当初予算 合算（外国人特化）", value: esc(totalLabel), badge: prevTotal ? " " + deltaBadge(totalDelta(fTotal, prevTotal), "big") : "", exact: exactTag(fTotal), sub: `${esc(fyL)}・予算説明書ベース` },
    { label: "担当課", value: bureaus.length, unit: "課", sub: esc(bureaus.join("・")) },
    { label: "データ年度", value: esc(fyL), fy: true, sub: "出典: 埼玉県 予算説明書" },
  ]);
  return `
  <div class="budget-hero">
    <div class="budget-hero-main">
      <div class="budget-hero-label">埼玉県 ${esc(fyL)} 外国人特化予算（多文化共生関連）合計</div>
      <div class="budget-hero-num">${esc(totalLabel)}</div>
      ${exactTag(fTotal)}
      ${heroDeltaHtml(fTotal, prevTotal)}
      ${ga ? `<div class="budget-hero-supp">参考: 埼玉県の${esc(ga.label)}は ${esc(ga.amount_label)}。外国人特化はその約${yr.contrast_pct}%。</div>` : ""}
    </div>
    ${shareBtn(t.text, t.url, "埼玉県 外国人特化予算")}
  </div>
  ${trendChartHtml(trendRows, fy)}
  ${contrast}
  ${evBreakdown}
  <div class="budget-cols">
    <div class="budget-col">
      <div class="budget-col-h">事業別内訳（金額順・割合バー／${esc(fyL)}）</div>
      <div>${itemBars}</div>
      <div class="budget-col-foot">※埼玉県「議会提出予算説明書」に計上された外国人特化（県民生活部国際課の多文化共生推進事業費・外国人地域生活支援事業費）のみ。全県民向けのインフラ・福祉等は含まない。金額は丸め値の下に1円単位の実額を併記。</div>
    </div>
    <div class="budget-col">
      ${listControlsHtml("saitama", yr.items.map((i) => i.category), LIST_FILTERS.saitama, yr.items.length, fyL)}
    </div>
  </div>
  <div class="local-kpi-band"><div class="local-kpi-h">この年度のサマリー（埼玉県・${esc(fyL)}）</div>${kpi}</div>
  <p class="budget-basis">${esc(PREF.basis_note)} 出典: <a href="${esc(yr.source.url)}" target="_blank" rel="noopener">${esc(yr.source.label)} ↗</a>${ga && ga.source ? ` ／ 一般会計: <a href="${esc(ga.source.url)}" target="_blank" rel="noopener">${esc(ga.source.label)} ↗</a>` : ""}</p>`;
}

// 焦点（Spotlight）：川口市 — 県の中でこの市がいかに特異な注目を浴びているかを対比
function kawaguchiSpotlightHtml(yr, fy, fyL) {
  const SPOT = KAWAGUCHI.spotlight;
  const ga = yr.city_general_account;
  const fTotal = yr.foreign_total_yen;
  const totalLabel = yenBreakdown(fTotal);
  const prev = kawaguchiYear(fy - 1);
  const prevTotal = prev ? prev.foreign_total_yen : null;
  const trendRows = SPOT.years.slice().sort((a, b) => a.fiscal_year - b.fiscal_year).map((y) => ({ year: y.fiscal_year, amount_yen: y.foreign_total_yen, sourceUrl: y.source.url }));
  const itemRows = yr.items.slice().sort((a, b) => b.amount_yen - a.amount_yen).map((it, i) => ({ name: it.name, amount_yen: it.amount_yen, color: catColor(it.category, i) }));
  const itemBars = barListHtml(itemRows);
  const t = localBudgetTweet("埼玉県川口市", yr, ga, fyL, yr.source.url);
  const contrast = ga
    ? govContrastHtml({ govLabel: "川口市", audience: "全市民向け", totalLabel, totalYen: fTotal, ga, contrastPct: yr.contrast_pct, fyL, tweet: t, shareLabel: "川口市 外国人特化予算" })
    : "";
  const bureaus = [...new Set(yr.items.map((i) => i.bureau))];
  const kpi = localKpiHtml([
    { label: "関連事業数（外国人特化）", value: yr.items.length, unit: "件", sub: "協働推進課の多文化共生関連" },
    { label: "当初予算 合算（外国人特化）", value: esc(totalLabel), badge: prevTotal ? " " + deltaBadge(totalDelta(fTotal, prevTotal), "big") : "", exact: exactTag(fTotal), sub: `${esc(fyL)}・当初予算ベース` },
    { label: "担当課", value: bureaus.length, unit: "課", sub: esc(bureaus.join("・")) },
    { label: "データ年度", value: esc(fyL), fy: true, sub: "出典: 川口市 当初予算のポイント" },
  ]);
  return `
  <div class="spotlight-band">
    <div class="spotlight-head"><span class="spotlight-badge">焦点 SPOTLIGHT</span> 川口市 — 県内で最も注目される「ホットスポット」</div>
    <p class="spotlight-lead">SNSで「外国人（クルド人等）に莫大な税金」と名指しされる川口市。だが県の多文化共生予算の中で見ると、市単独でも外国人特化は市一般会計のごく一部に過ぎない。県全体（上）と対比して、この一都市への注目がいかに突出しているかを示す。</p>
  </div>
  <div class="budget-hero">
    <div class="budget-hero-main">
      <div class="budget-hero-label">川口市 ${esc(fyL)} 外国人特化予算（多文化共生関連）合計</div>
      <div class="budget-hero-num">${esc(totalLabel)}</div>
      ${exactTag(fTotal)}
      ${heroDeltaHtml(fTotal, prevTotal)}
      ${ga ? `<div class="budget-hero-supp">参考: 川口市の${esc(ga.label)}は ${esc(ga.amount_label)}。外国人特化はその約${yr.contrast_pct}%。</div>` : ""}
    </div>
    ${shareBtn(t.text, t.url, "川口市 外国人特化予算")}
  </div>
  ${trendChartHtml(trendRows, fy)}
  ${contrast}
  <div class="report-note">
    <div class="rn-head"><i class="rn-i">!</i> トレンド焦点 — SNSの言説 vs 一次ソースの実額</div>
    <p class="rn-body">${esc(SPOT.trend_note)}</p>
  </div>
  <div class="budget-cols">
    <div class="budget-col">
      <div class="budget-col-h">事業別内訳（金額順・割合バー／${esc(fyL)}）</div>
      <div>${itemBars}</div>
      <div class="budget-col-foot">※川口市「当初予算のポイント」PDFに名称・金額が明記された外国人特化（協働推進課・多文化共生）事業のみ。金額は丸め値の下に1円単位の実額を併記。</div>
    </div>
    <div class="budget-col">
      ${listControlsHtml("kawaguchi", yr.items.map((i) => i.category), LIST_FILTERS.kawaguchi, yr.items.length, fyL)}
    </div>
  </div>
  <div class="local-kpi-band"><div class="local-kpi-h">この年度のサマリー（川口市・${esc(fyL)}）</div>${kpi}</div>
  <p class="budget-basis">${esc(SPOT.basis_note)} 出典: <a href="${esc(yr.source.url)}" target="_blank" rel="noopener">${esc(yr.source.label)} ↗</a></p>`;
}

function localItemCard(it) {
  return `<li>
      <div class="ti-head">
        <span class="ti-amt">${esc(it.amount_label || fmtYen(it.amount_yen))}</span>
        <span class="tag">${esc(it.bureau)}</span><span class="tag kw">${esc(it.category)}</span>
        ${it._delta ? deltaBadge(it._delta) : ""}
      </div>
      ${exactTag(it.amount_yen)}
      <div class="ti-title">${esc(it.name)}</div>
      ${it.desc ? `<div class="ti-desc">${esc(it.desc)}</div>` : ""}
    </li>`;
}

function renderSaitamaItemList() {
  const yr = saitamaYear(KAWAGUCHI_YEAR);
  if (!yr) return;
  const prev = saitamaYear(KAWAGUCHI_YEAR - 1);
  const items = attachDeltas(yr.items, prev && prev.items);
  renderFilteredList("saitama", items, (it) => it.name + (it.desc || "") + it.bureau + it.category, localItemCard);
}

function renderKawaguchiItemList() {
  const yr = kawaguchiYear(KAWAGUCHI_YEAR);
  if (!yr) return;
  const prev = kawaguchiYear(KAWAGUCHI_YEAR - 1);
  const items = attachDeltas(yr.items, prev && prev.items);
  renderFilteredList("kawaguchi", items, (it) => it.name + (it.desc || "") + it.bureau + it.category, localItemCard);
}

/* ===== 都道府県ビュー（汎用・多年度・国クオリティ）: 大阪/北海道/愛知/福岡 → 47都道府県へ拡張 ===== */
const PREF_CONFIG = {
  hokkaido: {
    label: "北海道", audience: "全道民向け", heroCat: "多文化共生・外国人材",
    deptSub: "各部施策の概要の外国人特化事業", kpiSrc: "出典: 北海道 予算の概要",
    listFoot: "※北海道「予算の概要（各部施策の概要）」に事業名・金額が明記され検証を通過した外国人特化事業のみ。令和6・7年度は道の公表PDFが画像形式のため証跡照合ができず非収録（捏造防止の運用方針）。",
    file: "data/hokkaido.json",
  },
  aichi: {
    label: "愛知県", audience: "全県民向け", heroCat: "多文化共生・外国人相談・外国人材",
    deptSub: "多文化共生施策とりまとめの主要事業", kpiSrc: "出典: 愛知県 予算の概要 参考資料",
    listFoot: "※愛知県「予算の概要 参考資料」の多文化共生施策とりまとめに名称・金額が明記され、事業名＋金額の連結証跡で検証を通過した外国人特化の主要事業のみ（とりまとめ総額の全内訳ではない）。",
    file: "data/aichi.json",
  },
  osaka: {
    label: "大阪府", audience: "全府民向け", heroCat: "多文化共生・外国人相談・外国人材",
    deptSub: "都市魅力創造局国際課の外国人特化事業", kpiSrc: "出典: 大阪府 予算編成過程公表",
    listFoot: "※大阪府「予算編成過程公表」の事業別ページに名称・金額（査定額＝当初予算額）が明記され、年度間チェックサム等の4重検証を通過した外国人特化事業のみ。日本人向け国際化事業や姉妹都市交流・旅券事務は含まない。",
    file: "data/osaka.json",
  },
  fukuoka: {
    label: "福岡県", audience: "全県民向け", heroCat: "多文化共生・外国人材",
    deptSub: "国際政策課の外国人特化事業", kpiSrc: "出典: 福岡県 当初予算の編成概要",
    listFoot: "※福岡県「当初予算の編成概要」に事項名・金額が明記され、前年度括弧額との年度間チェックサム等の検証を通過した外国人特化事業のみ。国際交流一般・姉妹都市交流等は含まない。",
    file: "data/fukuoka.json",
  },
  kanagawa: {
    label: "神奈川県", audience: "全県民向け", heroCat: "多文化共生・日本語教育・外国人材",
    deptSub: "局別主要施策の概要の外国人特化事業", kpiSrc: "出典: 神奈川県 当初予算 主要施策の概要",
    listFoot: "※神奈川県の局別「当初予算 主要施策の概要」に事業名・金額が明記され検証を通過した外国人特化事業のみ（令和6年度=国際文化観光局、令和7・8年度=組織再編後の文化スポーツ観光局）。掲載粒度は年度の資料により異なる。ベトナム友好交流等の国際文化交流は含まない。",
    file: "data/kanagawa.json",
  },
  kyoto: {
    label: "京都府", audience: "全府民向け", heroCat: "多文化共生",
    deptSub: "主要事項説明の外国人特化事業", kpiSrc: "出典: 京都府 当初予算 主要事項説明",
    listFoot: "※京都府の部局別「当初予算 主要事項説明」に事業名・金額が明記され検証を通過した外国人特化事業のみ。令和5年度は主要事項説明資料等に該当事業の記載がないため未収録。全府民向け事業は含まない。",
    file: "data/kyoto.json",
  },
  miyagi: {
    label: "宮城県", audience: "全県民向け", heroCat: "外国人材・多文化共生・日本語教育",
    deptSub: "主要事業概要の外国人特化事業", kpiSrc: "出典: 宮城県 当初予算 主要事業概要",
    listFoot: "※宮城県「当初予算主要事業概要」の一覧表に事業名・部局・金額が明記され、連結証跡で検証を通過した外国人特化事業のみ。訪日外国人観光客の誘致・周遊促進等（対象=観光客・観光事業者）は含まない。",
    file: "data/miyagi.json",
  },
  hiroshima: {
    label: "広島県", audience: "全県民向け", heroCat: "多文化共生・外国人材",
    deptSub: "当初予算事業（局別全事業一覧）の外国人特化事業", kpiSrc: "出典: 広島県 当初予算事業",
    listFoot: "※広島県「当初予算事業」の局別全事業一覧に事業名・金額が明記され、前年併記の4年連鎖チェックサムで検証を通過した外国人特化事業のみ。同名事業は局名で区別。国際交流一般は含まない。",
    file: "data/hiroshima.json",
  },
  okayama: {
    label: "岡山県", audience: "全県民向け", heroCat: "外国人材",
    deptSub: "予算説明書・あらましの外国人特化事業", kpiSrc: "出典: 岡山県 当初予算の説明・あらまし",
    listFoot: "※岡山県「当初予算の説明」（課別事業費）と「あらまし」（重点プロジェクト）のうち外国人特化と確認できたもののみ。国際交流一般と一体の混合費目（国際交流・多文化共生推進費）は水増し防止のため未計上。プロジェクトの金額は資料表記どおり0.1億円単位の概数。",
    file: "data/okayama.json",
  },
};
const PREF_DATA = {};
const PREF_YEAR = {};

function prefYearOf(gov, fy) {
  const d = PREF_DATA[gov];
  return (d && d.years.find((y) => y.fiscal_year === fy)) || null;
}

function renderPref(gov, data) {
  PREF_DATA[gov] = data;
  const btn = document.querySelector(`.gov-btn[data-gov="${gov}"]`);
  if (!data || !data.years || !data.years.length) {
    if (btn) { btn.hidden = true; btn.dataset.empty = "1"; } // データ未取得時はタブを隠す
    return;
  }
  PREF_YEAR[gov] = data.latest; // 既定は最新年度
  renderPrefYearTabs(gov);
  renderPrefYear(gov, data.latest);
}

function renderPrefYearTabs(gov) {
  const tabs = document.getElementById(gov + "-year-tabs");
  const d = PREF_DATA[gov];
  if (!tabs || !d) return;
  const years = d.years.slice().sort((a, b) => b.fiscal_year - a.fiscal_year); // 新しい年度を左に
  tabs.innerHTML = years
    .map((y) => yearTabHtml(y.fiscal_year, y.fiscal_year === PREF_YEAR[gov], { latest: y.fiscal_year === d.latest }))
    .join("");
}

function renderPrefYear(gov, fy) {
  const cfg = PREF_CONFIG[gov];
  const d = PREF_DATA[gov];
  const yr = prefYearOf(gov, fy);
  const host = document.getElementById(gov);
  if (!cfg || !d || !host) return;
  if (!yr) {
    host.innerHTML = `<p class="muted">この年度の${esc(cfg.label)}データは未収録です。</p>`;
    return;
  }
  PREF_YEAR[gov] = fy;
  renderPrefYearTabs(gov);
  const ga = yr.general_account;
  const fTotal = yr.foreign_total_yen;
  const totalLabel = yenBreakdown(fTotal);
  const fyL = fyTag(fy);
  const prev = prefYearOf(gov, fy - 1);
  const prevTotal = prev ? prev.foreign_total_yen : null;
  // 多年度トレンド（国の budget-trend と同一。1年度のみの県は自動で非表示）
  const trendRows = d.years
    .slice()
    .sort((a, b) => a.fiscal_year - b.fiscal_year)
    .map((y) => ({ year: y.fiscal_year, amount_yen: y.foreign_total_yen, sourceUrl: y.source.url }));
  // 事業別の横バー＋巨大%付き100%積み上げ（国の「主管省庁別」と同一デザイン）
  const itemRows = yr.items
    .slice()
    .sort((a, b) => b.amount_yen - a.amount_yen)
    .map((it, i) => ({ name: it.name, amount_yen: it.amount_yen, color: catColor(it.category, i) }));
  const itemBars = barListHtml(itemRows);
  const evLead = itemRows[0];
  const evLeadPct = evLead ? Math.round((evLead.amount_yen / fTotal) * 100) : 0;
  const evBreakdown = evLead
    ? `<div class="breakdown">
    <div class="bd-head">外国人特化予算の中身 — 事業別の割合（${esc(fyL)}）</div>
    <div class="bd-lead"><span class="bd-lead-pct">${evLeadPct}%</span><span class="bd-lead-txt">が <b>${esc(evLead.name)}</b>。<span class="bd-lead-amt">${fmtYen(evLead.amount_yen)}</span></span></div>
    ${stackedBreakdownHtml(itemRows, fTotal)}
  </div>`
    : "";
  const t = localBudgetTweet(cfg.label, yr, ga, fyL, yr.source.url);
  const contrast = ga
    ? govContrastHtml({ govLabel: cfg.label, audience: cfg.audience, totalLabel, totalYen: fTotal, ga, contrastPct: yr.contrast_pct, fyL, tweet: t, shareLabel: `${cfg.label} 外国人特化予算` })
    : "";
  // 4つのサマリーカード（国 #kpi と同一デザイン。所管府省庁→担当部課に読み替え）
  const bureaus = [...new Set(yr.items.map((i) => i.bureau))];
  const kpi = localKpiHtml([
    { label: "関連事業数（外国人特化）", value: yr.items.length, unit: "件", sub: esc(cfg.deptSub) },
    { label: "当初予算 合算（外国人特化）", value: esc(totalLabel), badge: prevTotal ? " " + deltaBadge(totalDelta(fTotal, prevTotal), "big") : "", exact: exactTag(fTotal), sub: `${esc(fyL)}・当初予算ベース` },
    { label: "担当部課", value: bureaus.length, unit: "部課", sub: esc(bureaus.join("・")) },
    { label: "データ年度", value: esc(fyL), fy: true, sub: esc(cfg.kpiSrc) },
  ]);
  host.innerHTML = `
  <div class="budget-hero">
    <div class="budget-hero-main">
      <div class="budget-hero-label">${esc(cfg.label)} ${esc(fyL)} 外国人特化予算（${esc(cfg.heroCat)}）合計</div>
      <div class="budget-hero-num">${esc(totalLabel)}</div>
      ${exactTag(fTotal)}
      ${heroDeltaHtml(fTotal, prevTotal)}
      ${ga ? `<div class="budget-hero-supp">参考: ${esc(cfg.label)}の${esc(ga.label)}は ${esc(ga.amount_label)}。外国人特化はその約${yr.contrast_pct}%。</div>` : ""}
    </div>
    ${shareBtn(t.text, t.url, `${cfg.label} 外国人特化予算`)}
  </div>
  ${trendChartHtml(trendRows, fy)}
  ${contrast}
  ${evBreakdown}
  <div class="report-note">
    <div class="rn-head"><i class="rn-i">!</i> トレンド焦点 — SNSの言説 vs 一次ソースの実額</div>
    <p class="rn-body">${esc(d.trend_note)}</p>
  </div>
  <div class="budget-cols">
    <div class="budget-col">
      <div class="budget-col-h">事業別内訳（金額順・割合バー／${esc(fyL)}）</div>
      <div>${itemBars}</div>
      <div class="budget-col-foot">${esc(cfg.listFoot)}</div>
    </div>
    <div class="budget-col">
      ${listControlsHtml(gov, yr.items.map((i) => i.category), LIST_FILTERS[gov], yr.items.length, fyL)}
    </div>
  </div>
  <div class="local-kpi-band"><div class="local-kpi-h">この年度のサマリー（${esc(cfg.label)}・${esc(fyL)}）</div>${kpi}</div>
  <p class="budget-basis">${esc(d.basis_note)} 出典: <a href="${esc(yr.source.url)}" target="_blank" rel="noopener">${esc(yr.source.label)} ↗</a>${ga && ga.source ? ` ／ 一般会計: <a href="${esc(ga.source.url)}" target="_blank" rel="noopener">${esc(ga.source.label)} ↗</a>` : ""}</p>`;
  renderPrefItemList(gov);
  applyGlossary(host);
  renderStatsFor(gov, fy); // 統計の裏付けを当該県×年度に連動
}

function renderPrefItemList(gov) {
  const yr = prefYearOf(gov, PREF_YEAR[gov]);
  if (!yr) return;
  const prev = prefYearOf(gov, PREF_YEAR[gov] - 1);
  const items = attachDeltas(yr.items, prev && prev.items);
  renderFilteredList(gov, items, (it) => it.name + (it.desc || "") + it.bureau + it.category, localItemCard);
}

/* ===== エリア（地方ブロック）2階層ナビ: 第1階層=エリア → 第2階層=都道府県ピル =====
   47都道府県へのスケール対応。既存の setGov / 各描画ロジックには一切手を入れず、
   エリア選択で .gov-btn の表示範囲を絞り込むだけの薄い層として実装。 */
const AREA_CONFIG = [
  { id: "national", label: "国（政府）", govs: [] }, // 単独・第2階層なし
  { id: "hokkaido-tohoku", label: "北海道・東北", govs: ["hokkaido", "miyagi"] },
  { id: "kanto", label: "関東", govs: ["tokyo", "kanagawa", "kawaguchi"] },
  { id: "chubu", label: "中部", govs: ["aichi"] },
  { id: "kinki", label: "近畿", govs: ["kyoto", "osaka"] },
  { id: "chugoku-shikoku", label: "中国・四国", govs: ["okayama", "hiroshima"] },
  { id: "kyushu-okinawa", label: "九州・沖縄", govs: ["fukuoka"] },
];
let areaMode = "national";

function setArea(areaId) {
  areaMode = areaId;
  document.querySelectorAll(".area-btn").forEach((b) => b.classList.toggle("on", b.dataset.area === areaId));
  const area = AREA_CONFIG.find((a) => a.id === areaId);
  const tg = document.getElementById("gov-toggle");
  if (!area || !area.govs.length) {
    if (tg) tg.hidden = true; // 国（政府）等は第2階層なし
    setGov("national");
    return;
  }
  // 第2階層: エリア内の自治体ピルのみ表示（データ未取得の県は data-empty で除外）
  let first = null;
  let keepCurrent = false;
  document.querySelectorAll(".gov-btn").forEach((b) => {
    const show = area.govs.includes(b.dataset.gov) && b.dataset.empty !== "1";
    b.hidden = !show;
    if (show && !first) first = b.dataset.gov;
    if (show && b.dataset.gov === govMode) keepCurrent = true;
  });
  if (tg) tg.hidden = !first;
  if (first) setGov(keepCurrent ? govMode : first);
  else setGov("national"); // エリア内に表示可能な県が無い場合のフォールバック
}

function bindArea() {
  const tg = document.getElementById("area-toggle");
  if (!tg) return;
  tg.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-area]");
    if (btn && !btn.disabled) setArea(btn.dataset.area);
  });
}

let govMode = "national";
function setGov(mode) {
  govMode = mode;
  const isNational = mode === "national";
  document.querySelectorAll(".gov-btn").forEach((b) => b.classList.toggle("on", b.dataset.gov === mode));
  // 国側の年度タブは国モードのみ表示（自治体は各自の年度タブを持つ）。
  // 「ならべて比較」「統計の裏付け」「言説チェッカー」は全タブ共通で常時表示（隠さない）。
  document.getElementById("year-tabs").hidden = !isNational;
  if (isNational) {
    setYear(state.year || FY_BUDGET); // 現在の年度タブの表示を復元（統計・比較もここで連動）
  } else {
    document.getElementById("policy-budget-section").hidden = true;
    document.getElementById("kpi").hidden = true;
    document.getElementById("amount-note").hidden = true;
    document.getElementById("ranking-section").hidden = true;
    // 統計の裏付けを選択中の自治体×年度に連動（国の最新データの残存を防止）
    if (mode === "tokyo") renderStatsFor("tokyo", TOKYO_YEAR);
    else if (PREF_CONFIG[mode]) renderStatsFor(mode, PREF_YEAR[mode]);
    else if (mode === "kawaguchi") renderStatsFor("kawaguchi", KAWAGUCHI_YEAR);
  }
  // 自治体セクションは選択したものだけ表示
  document.getElementById("tokyo-section").hidden = mode !== "tokyo";
  Object.keys(PREF_CONFIG).forEach((gov) => {
    const sec = document.getElementById(gov + "-section");
    if (sec) sec.hidden = mode !== gov;
  });
  document.getElementById("kawaguchi-section").hidden = mode !== "kawaguchi";
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
            ? `<div class="side-amount">${fmtYen(s.budget_yen)}<span class="side-fy">${esc(fy ? fyTag(fy) : "")}予算</span></div>${exactTag(s.budget_yen)}
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

let STATS = null; // 国の統計（e-Stat）。renderStatsFor が自治体×年度で出し分ける。

// 統計の裏付けを「選択中の自治体 × 選択中の年度」に連動させる単一の入口。
function renderStatsFor(gov, fy) {
  const sub = document.getElementById("stats-sub");
  if (gov === "tokyo") {
    const yr = typeof tokyoYear === "function" ? tokyoYear(fy) : null;
    const prev = typeof tokyoYear === "function" ? tokyoYear(fy - 1) : null;
    if (sub) sub.textContent = `東京都・${fyTag(fy)}・住民基本台帳`;
    renderRegionalStats("東京都", yr && yr.population, prev && prev.population);
  } else if (typeof PREF_CONFIG !== "undefined" && PREF_CONFIG[gov]) {
    const yr = prefYearOf(gov, fy);
    const prev = prefYearOf(gov, fy - 1);
    const pop = yr && yr.population;
    if (sub) sub.textContent = `${PREF_CONFIG[gov].label}・${fyTag(fy)}・${(pop && pop.metric_label) || "外国人人口"}`;
    renderRegionalStats(PREF_CONFIG[gov].label, pop, prev && prev.population);
  } else if (gov === "kawaguchi") {
    const yr = typeof kawaguchiYear === "function" ? kawaguchiYear(fy) : null;
    const prev = typeof kawaguchiYear === "function" ? kawaguchiYear(fy - 1) : null;
    if (sub) sub.textContent = `川口市・${fyTag(fy)}・住民基本台帳`;
    renderRegionalStats("川口市", yr && yr.population, prev && prev.population);
  } else {
    if (sub) sub.textContent = `全国・${fyTag(fy)}・e-Stat ＋ 出入国在留管理庁`;
    renderNationalStats(fy);
  }
}

// 自治体（東京都/大阪府/川口）の年度別 外国人人口・総人口・割合カード（国と同一デザイン）。
function renderRegionalStats(govLabel, pop, prevPop) {
  const el = document.getElementById("stats");
  if (!pop) {
    el.innerHTML = `<div class="kpi stat-card"><div class="label">${esc(govLabel)}の統計</div><div class="sub">この年度の統計は未収録です。</div></div>`;
    return;
  }
  // 前年と同一基準日（確報未公表で最新実績を代用中）のときは前年比を出さない（+0%の誤表示防止）
  const yoy =
    prevPop && prevPop.as_of !== pop.as_of
      ? { abs: pop.foreign - prevPop.foreign, pct: Math.round(((pop.foreign - prevPop.foreign) / prevPop.foreign) * 1000) / 10 }
      : null;
  const metric = pop.metric_label || "外国人住民数";
  const basis = pop.basis || `${govLabel}の住民基本台帳（${pop.as_of}）に基づく。国の在留外国人統計とは基準日・対象が異なる。`;
  const totalSrc = pop.total_source
    ? `　<a href="${esc(pop.total_source.url)}" target="_blank" rel="noopener">総人口: ${esc(pop.total_source.label)} ↗</a>`
    : "";
  el.innerHTML = `
    <div class="kpi stat-card">
      <div class="label">${esc(govLabel)}の${esc(metric)}<span class="as-of">${esc(pop.as_of)}</span></div>
      <div class="value">${(pop.foreign / 1e4).toLocaleString("ja-JP", { maximumFractionDigits: 2 })}<small> 万人</small></div>
      <span class="exact-sub">元データ：${pop.foreign.toLocaleString("ja-JP")}人</span>
      ${yoy ? `<div class="sub">前年同期比 ${yoy.abs >= 0 ? "+" : ""}${yoy.abs.toLocaleString("ja-JP")}人（${yoy.pct >= 0 ? "+" : ""}${yoy.pct}%）</div>` : ""}
      <div class="sub"><a href="${esc(pop.source.url)}" target="_blank" rel="noopener">出典: ${esc(pop.source.label)} ↗</a></div>
    </div>
    <div class="kpi stat-card">
      <div class="label">総人口に占める割合<span class="as-of">${esc(pop.total_as_of || pop.as_of)}</span></div>
      <div class="value">${pop.share_pct}<small> %</small></div>
      <span class="exact-sub">元データ：外国人 ${pop.foreign.toLocaleString("ja-JP")}人 ÷ 総人口 ${pop.total.toLocaleString("ja-JP")}人</span>
      <div class="sub">${esc(basis)}</div>
      <div class="sub"><a href="${esc(pop.source.url)}" target="_blank" rel="noopener">出典: ${esc(pop.source.label)} ↗</a>${totalSrc}</div>
    </div>`;
}

function renderNationalStats(fy) {
  const statsData = STATS;
  if (!statsData) return;
  const z = statsData.indicators.zairyu_total;
  const zs = z.series;
  const first = zs[0];
  const byFy = statsData.national_by_fy || {};
  const rec = byFy[String(fy)] || byFy[String(state.year)] || byFy[Object.keys(byFy).sort().pop()];
  if (!rec) {
    // フォールバック（national_by_fy 未取得時）: 最新実績のみ
    const la = z.latest_actual;
    const headVal = la ? la.value : z.latest.value;
    document.getElementById("stats").innerHTML = `<div class="kpi stat-card"><div class="label">${esc(z.name)}</div><div class="value">${(headVal / 1e4).toLocaleString("ja-JP", { maximumFractionDigits: 1 })}<small> 万人</small></div></div>`;
    return;
  }
  const yoy = rec.foreign_yoy;
  const fSrc = rec.foreign_source || statsData.source;
  document.getElementById("stats").innerHTML = `
    <div class="kpi stat-card">
      <div class="label">全国の${esc(z.name)}<span class="as-of">${esc(rec.foreign_as_of)}</span></div>
      <div class="value">${(rec.foreign / 1e4).toLocaleString("ja-JP", { maximumFractionDigits: 1 })}<small> 万人</small></div>
      <span class="exact-sub">元データ：${rec.foreign.toLocaleString("ja-JP")}人</span>
      ${yoy ? `<div class="sub">前年比 ${yoy.abs >= 0 ? "+" : ""}${yoy.abs.toLocaleString("ja-JP")}人（${yoy.pct >= 0 ? "+" : ""}${yoy.pct}%）</div>` : ""}
      ${sparkline(zs)}
      <div class="sub">推移（年次・e-Stat）：${first.year}年 ${first.value.toLocaleString("ja-JP")}人 → ${z.latest.year}年 ${z.latest.value.toLocaleString("ja-JP")}人</div>
      <div class="sub"><a href="${esc(fSrc.url)}" target="_blank" rel="noopener">出典: ${esc(fSrc.label || fSrc.name)} ↗</a>　<a href="${esc(statsData.source.url)}" target="_blank" rel="noopener">推移: e-Stat ↗</a></div>
    </div>
    <div class="kpi stat-card">
      <div class="label">総人口に占める割合<span class="as-of">${esc(rec.foreign_as_of)}</span></div>
      <div class="value">${rec.share_pct}<small> %</small></div>
      <span class="exact-sub">元データ：在留外国人 ${rec.foreign.toLocaleString("ja-JP")}人 ÷ 総人口 ${rec.total.toLocaleString("ja-JP")}人</span>
      <div class="sub">全国・${esc(fyTag(fy))}時点。e-Stat（総人口）＋出入国在留管理庁（在留外国人数）に基づく。${rec.foreign_provisional ? "在留外国人数は当該年度の確報が未公表のため、取得可能な最新実績を表示。" : ""}</div>
      <div class="sub"><a href="${esc((rec.total_source || statsData.source).url)}" target="_blank" rel="noopener">出典: e-Stat 統計ダッシュボード ↗</a></div>
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
    insertAdSlot(slice
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
      })).join("") || `<p class="muted">該当する事業がありません。</p>`;
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

/* ===== ニュースティッカー（外国人政策 速報）＋一覧モーダル ===== */
let NEWS = null;

function renderNewsTicker(news) {
  NEWS = news;
  const ticker = document.getElementById("news-ticker");
  const track = document.getElementById("nt-track");
  const vp = ticker && ticker.querySelector(".nt-viewport");
  if (!ticker || !track || !vp || !news || !Array.isArray(news.items) || !news.items.length) return;
  const itemHtml = (it) => `<a class="nt-item" href="${esc(it.url)}" target="_blank" rel="noopener noreferrer">
      <span class="nt-src">${esc(it.source)}</span>
      <span class="nt-title">${esc(it.title)}</span>
      ${it.published ? `<span class="nt-time">${esc(it.published)}</span>` : ""}
    </a>`;
  const baseHtml = news.items.map(itemHtml).join("");
  track.innerHTML = baseHtml; // まず1セット幅を計測
  ticker.hidden = false;
  requestAnimationFrame(() => {
    const vw = vp.clientWidth || 600;
    const baseWidth = track.scrollWidth;
    if (baseWidth <= 0) return;
    // 1ユニットがビューポート幅以上になるよう繰り返し、それを2つ並べてシームレスループ
    const reps = Math.max(1, Math.ceil((vw + 80) / baseWidth));
    const unit = baseHtml.repeat(reps);
    track.innerHTML = unit + unit;
    const unitWidth = track.scrollWidth / 2;
    track.style.animationDuration = Math.max(unitWidth / 70, 16).toFixed(1) + "s"; // 約70px/秒
  });
  renderNewsModalList();
}

function renderNewsModalList() {
  const list = document.getElementById("news-modal-list");
  if (!list || !NEWS || !Array.isArray(NEWS.items)) return;
  list.innerHTML = NEWS.items
    .map(
      (it, i) => `<a class="news-row" href="${esc(it.url)}" target="_blank" rel="noopener noreferrer">
      <div class="news-row-top">
        <span class="news-row-num">${i + 1}</span>
        <span class="nt-src">${esc(it.source)}</span>
        <span class="news-row-time">${esc(it.published || "")}</span>
      </div>
      <div class="news-row-title">${esc(it.title)} <span class="news-row-arrow" aria-hidden="true">↗</span></div>
    </a>`
    )
    .join("");
  const sub = document.getElementById("news-modal-sub");
  if (sub) {
    const updated = NEWS.generated_at ? new Date(NEWS.generated_at) : null;
    sub.textContent = `信頼できる全国大手メディア・通信社・NHK等から自動抽出した最新 ${NEWS.items.length} 件${updated ? `（更新: ${updated.toLocaleString("ja-JP")}）` : ""}`;
  }
  const foot = document.getElementById("news-modal-foot");
  if (foot) foot.textContent = NEWS.source_note || "";
}

let newsModalPrevFocus = null;
function openNewsModal() {
  const m = document.getElementById("news-modal");
  if (!m || !NEWS) return;
  renderNewsModalList();
  newsModalPrevFocus = document.activeElement;
  m.hidden = false;
  document.body.style.overflow = "hidden";
  const close = document.getElementById("news-modal-close");
  if (close) close.focus();
}
function closeNewsModal() {
  const m = document.getElementById("news-modal");
  if (!m) return;
  m.hidden = true;
  document.body.style.overflow = "";
  if (newsModalPrevFocus && newsModalPrevFocus.focus) newsModalPrevFocus.focus();
}
function bindNews() {
  const all = document.getElementById("nt-all");
  if (all) all.addEventListener("click", openNewsModal);
  const close = document.getElementById("news-modal-close");
  if (close) close.addEventListener("click", closeNewsModal);
  const bd = document.getElementById("news-modal-backdrop");
  if (bd) bd.addEventListener("click", closeNewsModal);
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !document.getElementById("news-modal").hidden) closeNewsModal();
  });
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
  renderStatsFor("national", y); // 統計を国（全国）に連動
  if (budgetMode) {
    window.scrollTo({ top: 0, behavior: "auto" });
    return;
  }
  state.meta = state.yearData[y];
  state.projects = state.meta.projects;
  state.shown = 20;
  document.getElementById("fy-label").textContent =
    `${fyTag(state.meta.fiscal_year)} 当初予算・自動抽出 ${state.projects.length} 事業`;
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
  // 予算内訳・施策一覧は国のFY2026タブ専用。必要なら国モード＋FY2026に切り替える。
  // 比較・統計は全タブ共通なので自治体モードのままでもスクロールできる。
  const needsBudget = target === "budget" || target === "shisaku";
  if (needsBudget && govMode !== "national") setGov("national");
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

function reRenderLocalList(prefix) {
  if (prefix === "tokyo") renderTokyoItemList();
  else if (PREF_CONFIG[prefix]) renderPrefItemList(prefix);
  else if (prefix === "saitama") renderSaitamaItemList();
  else if (prefix === "kawaguchi") renderKawaguchiItemList();
}

// 検索・カテゴリ・並び替えのイベントをセクションに委譲（容器が毎回再生成されてもフォーカス保持）
function bindLocalList(sectionId) {
  const sec = document.getElementById(sectionId);
  if (!sec) return;
  sec.addEventListener("input", (e) => {
    const m = (e.target.id || "").match(/^(tokyo|hokkaido|aichi|osaka|fukuoka|kanagawa|kyoto|miyagi|hiroshima|okayama|saitama|kawaguchi)-q$/);
    if (m) { LIST_FILTERS[m[1]].q = e.target.value; reRenderLocalList(m[1]); }
  });
  sec.addEventListener("change", (e) => {
    const m = (e.target.id || "").match(/^(tokyo|hokkaido|aichi|osaka|fukuoka|kanagawa|kyoto|miyagi|hiroshima|okayama|saitama|kawaguchi)-cat$/);
    if (m) { LIST_FILTERS[m[1]].cat = e.target.value; reRenderLocalList(m[1]); }
  });
  sec.addEventListener("click", (e) => {
    const b = e.target.closest("[data-lsort]");
    if (!b) return;
    const [prefix, key] = b.dataset.lsort.split(":");
    if (LIST_FILTERS[prefix]) {
      LIST_FILTERS[prefix].sort = key;
      // 国の施策ソートと同じく、押したボタンのハイライトを即時更新（リストのみ再描画のため）
      b.closest(".sort-seg").querySelectorAll(".sort-btn").forEach((x) => x.classList.toggle("on", x === b));
      reRenderLocalList(prefix);
    }
  });
}

function bind() {
  bindDrawer();
  bindArea();
  bindGov();
  bindNews();
  // 国の年度タブ（行政事業レビュー / 関係予算）。国モード以外では発火させない（混入の二重防止）。
  document.getElementById("year-tabs").addEventListener("click", (e) => {
    const btn = e.target.closest("[data-year]");
    if (btn && govMode === "national") setYear(Number(btn.dataset.year));
  });
  // 東京都の年度タブ（東京都データのみを描画。国・川口には一切触れない）
  const tokyoTabs = document.getElementById("tokyo-year-tabs");
  if (tokyoTabs)
    tokyoTabs.addEventListener("click", (e) => {
      const btn = e.target.closest("[data-year]");
      if (btn && govMode === "tokyo") renderTokyoYear(Number(btn.dataset.year));
    });
  // 都道府県（汎用）の年度タブ（各県データのみを描画。他自治体・国には一切触れない）
  Object.keys(PREF_CONFIG).forEach((gov) => {
    const tabs = document.getElementById(gov + "-year-tabs");
    if (tabs)
      tabs.addEventListener("click", (e) => {
        const btn = e.target.closest("[data-year]");
        if (btn && govMode === gov) renderPrefYear(gov, Number(btn.dataset.year));
      });
  });
  // 川口市の年度タブ（川口データのみを描画。国・東京には一切触れない）
  const kwTabs = document.getElementById("kawaguchi-year-tabs");
  if (kwTabs)
    kwTabs.addEventListener("click", (e) => {
      const btn = e.target.closest("[data-year]");
      if (btn && govMode === "kawaguchi") renderKawaguchiYear(Number(btn.dataset.year));
    });
  // 自治体の施策一覧の検索・絞り込み・並び替え（容器は再生成されるためセクションに委譲。リストのみ再描画でフォーカス保持）
  bindLocalList("tokyo-section");
  Object.keys(PREF_CONFIG).forEach((gov) => bindLocalList(gov + "-section"));
  bindLocalList("kawaguchi-section");
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
  // ファクトチェッカーとして古いキャッシュの数値を表示しないよう、データは常に再検証する（no-cache）。
  const getJson = (path) => fetch(path, { cache: "no-cache" }).then((r) => r.json());
  const [yearsMeta, claimsData, compData, statsData, policyBudget, glossary, tokyoData] = await Promise.all([
    getJson("data/years.json"),
    getJson("data/claims.json"),
    getJson("data/comparisons.json"),
    getJson("data/stats.json"),
    getJson("data/policy_budget.json"),
    getJson("data/glossary.json"),
    getJson("data/tokyo.json").catch(() => null), // best-effort: 無ければ東京都タブを隠す
  ]);
  const kawaguchiData = await getJson("data/saitama_kawaguchi.json").catch(() => null);
  // 都道府県（汎用）: best-effort読込（無ければ各県タブを隠す）
  const prefDataList = await Promise.all(
    Object.keys(PREF_CONFIG).map((gov) => getJson(PREF_CONFIG[gov].file).then((d) => [gov, d]).catch(() => [gov, null]))
  );
  getJson("data/news.json").then(renderNewsTicker).catch(() => {}); // best-effort: 速報ティッカー
  GLOSSARY = glossary.terms || [];
  state.years = yearsMeta.years;
  await Promise.all(
    state.years.map((y) => getJson(`data/projects_${y}.json`).then((d) => (state.yearData[y] = d)))
  );
  const latestMeta = state.yearData[yearsMeta.latest];
  document.getElementById("amount-note").textContent = `注記: ${latestMeta.amount_note}。タグは機械抽出の理由。詳細は必ず出典のレビューシート原文を確認。`;
  document.getElementById("footer-meta").textContent =
    `データ生成: ${latestMeta.generated_at} / 出典: ${latestMeta.source.name}（${latestMeta.source.url}） / 収載年度: ${state.years.map((y) => "FY" + y).join(" / ")}`;
  STATS = statsData; // 統計は renderStatsFor が自治体×年度で出し分ける（既定の描画は setYear で行う）
  renderPolicyBudget(policyBudget);
  renderTokyo(tokyoData, policyBudget);
  prefDataList.forEach(([gov, d]) => renderPref(gov, d));
  renderKawaguchi(kawaguchiData);
  renderComparisons(compData);
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
