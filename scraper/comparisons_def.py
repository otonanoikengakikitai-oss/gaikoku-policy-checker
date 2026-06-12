"""ならべて比較の定義（コードとして管理する）

- 各サイドの事業予算は build_comparisons.py がRSシステムの取得済みデータから
  事業名の完全一致で自動取得する（rs_project_name）
- 一人あたり金額（per_person）は、出典ページに証跡文字列（evidence）が
  現存することを毎回照合し、消えていれば公開しない
- context_note（条件差の注記）が無い比較は品質ゲートで公開不可
"""

COMPARISONS = [
    {
        "id": "ryugakusei-shien",
        "title": "返済不要の修学支援 — 来日外国人留学生 vs 国内学生",
        "context_note": (
            "対象規模・選抜方式・所得要件がまったく異なる。国費外国人留学生は大使館推薦・大学推薦等の"
            "選抜制で対象が限定される一方、修学支援新制度は所得要件（住民税非課税世帯等）を満たす"
            "広範な学生が対象。個人が受け取る額と事業予算規模の単純比較はできない。"
            "金額は各事業全体の当初予算額。"
        ),
        "sides": [
            {
                "name": "国費外国人留学生制度",
                "target": "外国人留学生（外国籍のみ・大使館推薦/大学推薦等の選抜制）",
                "rs_project_name": "国費外国人留学生制度",
                "per_person": [
                    {"label": "奨学金（研究留学生）", "text": "月額143,000〜145,000円", "evidence": "143,000円"},
                    {"label": "奨学金（学部留学生）", "text": "月額117,000円", "evidence": "117,000円"},
                    {"label": "授業料", "text": "不徴収", "evidence": "不徴収"},
                ],
                "per_person_source": {
                    "label": "Study in Japan（政府公式）文部科学省奨学金",
                    "url": "https://www.studyinjapan.go.jp/ja/planning/scholarships/mext-scholarships/",
                },
            },
            {
                "name": "高等教育修学支援新制度（給付奨学金＋授業料減免）",
                "target": "国内の学生（日本国籍・特別永住者・永住者等／住民税非課税世帯等の所得要件）",
                "rs_project_name": "大学等における修学支援に必要な経費",
                "per_person": [
                    {"label": "給付奨学金（私立・自宅外・第1区分）", "text": "月額75,800円", "evidence": "75,800円"},
                ],
                "per_person_source": {
                    "label": "JASSO 給付奨学金の支給額",
                    "url": "https://www.jasso.go.jp/shogakukin/about/kyufu/kingaku.html",
                },
            },
        ],
    },
    {
        "id": "ryugaku-direction",
        "title": "国費による留学支援の方向 — 外国人を日本へ vs 日本人を海外へ",
        "context_note": (
            "どちらも文部科学省所管の留学支援事業。受入れ（国費外国人留学生）と送り出し"
            "（日本人学生等の海外留学支援）で支援の方向が逆になる。制度設計・支援単価・対象人数が"
            "異なるため、予算額の差がそのまま個人の待遇差を意味するわけではない。"
            "金額は各事業全体の当初予算額。"
        ),
        "sides": [
            {
                "name": "国費外国人留学生制度",
                "target": "来日する外国人留学生（外国籍のみ）",
                "rs_project_name": "国費外国人留学生制度",
                "per_person": [],
                "per_person_source": None,
            },
            {
                "name": "大学等の海外留学支援制度",
                "target": "海外留学する日本人学生等",
                "rs_project_name": "大学等の海外留学支援制度",
                "per_person": [],
                "per_person_source": None,
            },
        ],
    },
]
