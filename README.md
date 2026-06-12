# 外国人政策・補助金チェッカー

外国人政策に関連する国の予算事業を毎週自動収集し、ネットで流れる言説を官公庁の一次ソースだけで検証する、完全無料・全自動運用のデータベース。

- **データ**: [行政事業レビュー見える化サイト（RSシステム）](https://rssystem.go.jp/) の公開APIから対象年度の全予算事業（約6,400件）を取得し、キーワード照合で関連事業を機械抽出
- **ならべて比較**: 条件・対象・出典つきの制度比較。事業予算はRSデータから自動解決、一人あたり金額は出典ページに証跡文字列が現存することを毎回照合
- **統計の裏付け**: e-Stat 統計ダッシュボードAPI（キー不要）から在留外国人数・総人口の全国時系列を自動取得
- **言説チェッカー**: ネットで流布する言説を、go.jp / lg.jp の一次ソースのみで検証
- **X共有**: 全カードにXポストボタン。文面は事実ベース固定（制度名・金額・注記・一次ソースURL）
- **運用コスト**: 0円（GitHub Actions 週次cron + GitHub Pages 静的配信、外部依存ライブラリなし）

## 運営原則（コードで強制）

1. **一次ソース限定** — 全レコードの出典URLは go.jp / lg.jp ドメインに限定。まとめサイト等の二次情報は収集しない。違反データは `scraper/validate.py` の品質ゲートが公開前に弾く（CIが exit 1）。
2. **文脈の併記必須** — 金額は各事業全体の当初予算額であり、外国人対象分のみの切り出し額ではない。この注記（`amount_note`）が無いデータは品質ゲートで公開不可。抽出理由（ヒットしたキーワード）も全カードに表示する。
3. **全自動・無選別** — 抽出はキーワード照合のみ。人手による恣意的な取捨選択は行わない。

## 構成

```
scraper/
  common.py           HTTPユーティリティ（標準ライブラリのみ）
  rs_system.py        行政事業レビューAPIアダプタ → docs/data/projects.json
  comparisons_def.py  ならべて比較の定義（コードとして管理）
  build_comparisons.py 比較の組み立て・証跡照合 → docs/data/comparisons.json
  stats.py            e-Stat統計ダッシュボードAPIアダプタ → docs/data/stats.json
  claims_def.py       言説チェッカーの定義（コードとして管理）
  build_claims.py     言説の出典検証 → docs/data/claims.json
  validate.py         品質ゲート（一次ソース・必須項目をCIで強制）
  run.py              一括実行
docs/                 静的ダッシュボード（GitHub Pages 配信ルート）
  data/               生成されたJSON（コミットされる）
.github/workflows/update.yml  週次自動更新
```

## 実行

```bash
cd scraper
python3 run.py              # 最新年度を自動検出して全パイプライン実行
python3 run.py --year 2024  # 年度指定
python3 run.py --use-cache  # 開発時: cache/ の生レスポンスを再利用
```

Python 3.10+ のみ。pip install は不要。

## 公開（GitHub Pages）

リポジトリの Settings → Pages → 「Deploy from a branch」で `main` / `docs/` を指定するだけ。
週次の自動更新は `.github/workflows/update.yml` が `docs/data/` を再生成してコミットする。

## 免責

- 抽出はキーワード照合による機械処理であり、外国人「のみ」を対象としない事業も含まれる。
- 金額・内容の正確な判断は、各カードから直接リンクされるレビューシート原文（rssystem.go.jp）で行うこと。
