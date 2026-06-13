"""東京都の外国人政策予算（令和8年度）の定義 — キュレーション方式

実額は東京都財務局「令和8年度 主要事業」PDF（一次ソース）から人手で検証して記録する。
build_tokyo.py が毎回:
  1. 出典PDFが lg.jp で生存していることを確認
  2. 各事業の「事業名（name_evidence）」がPDF本文に現存することを確認
  3. 増減チェックサム（amount_yen − prev_yen == delta_yen）が成立することを確認
  4. 金額の連結（R8R7の数字列）がPDF本文に現存することを確認
を満たした事業のみ公開する。1つでも崩れたら当該事業は非公開（捏造・転記ミスを防ぐ）。

金額は百万円単位（amount_man）で記録し、build側で円（amount_yen = amount_man * 1,000,000）に変換する。
出典PDFのURLは年度の日付を含むため、翌年度はURLと金額を更新する（国の関係予算と同様）。
"""

SOURCE = {
    "label": "東京都財務局 令和8年度 主要事業",
    "url": "https://www.zaimu1.metro.tokyo.lg.jp/zaisei/20260130_reiwa8nendo_tokyotoyosanangaiyou/8shuyouzigyou.pdf",
}

# amount_man / prev_man / delta_man は百万円。delta は増額を正、減額を負で記録。
ITEMS = [
    {
        "name": "多文化共生社会の実現に向けた取組",
        "name_evidence": "多文化共生社会の実現に向けた取組",
        "bureau": "生活文化局",
        "category": "多文化共生",
        "amount_man": 690,
        "prev_man": 579,
        "delta_man": 111,
        "sub_programs": [
            "（新）在住外国人への情報発信ルートづくり事業",
            "（新）地域日本語教育に係る調査",
            "（新）多文化キッズ支援者研修",
            "（新）秩序ある多文化共生社会実現に向けた情報発信強化 等",
        ],
    },
    {
        "name": "つながり創生財団助成（多文化共生・コミュニティ活性化）",
        "name_evidence": "つながり創生財団",
        "bureau": "生活文化局",
        "category": "多文化共生",
        "amount_man": 367,
        "prev_man": 195,
        "delta_man": 172,
        "sub_programs": ["多文化共生や共助社会を目指し、コミュニティの活性化を支援する財団の管理運営費を助成"],
    },
    {
        "name": "中小企業の外国人材受入支援事業",
        "name_evidence": "外国人材受入支援事業",
        "bureau": "産業労働局",
        "category": "外国人材",
        "amount_man": 531,
        "prev_man": 548,
        "delta_man": -17,
        "sub_programs": ["中小企業における外国人材の受入れ・定着を支援"],
    },
    {
        "name": "外国人社員への日本語教育等支援事業",
        "name_evidence": "外国人社員への日本語教育",
        "bureau": "産業労働局",
        "category": "外国人材",
        "amount_man": 92,
        "prev_man": 92,
        "delta_man": 0,
        "sub_programs": ["外国人社員への日本語教育等支援に加え、受入側の中小企業社員の英語力向上を支援"],
    },
]

# 観光・インバウンド予算（同じ主要事業PDFの大項目「観光産業の振興」）。
# 外国人政策（多文化共生・外国人材）との規模対比に用いる。
# sub_items は大項目の内訳（一部）であり、headlineの amount_man に内包される（合算しない）。
TOURISM = {
    "name": "観光産業の振興",
    "name_evidence": "観光産業の振興",
    "bureau": "産業労働局",
    "amount_man": 37605,
    "prev_man": 37241,
    "delta_man": 364,
    "sub_items": [
        {"name": "魅力を高める観光資源の開発", "name_evidence": "魅力を高める観光資源の開発", "amount_man": 14385, "prev_man": 13598, "delta_man": 787},
        {"name": "観光インフラ整備支援事業", "name_evidence": "観光インフラ整備支援事業", "amount_man": 3493, "prev_man": 5119, "delta_man": -1626},
        {"name": "自然と調和した観光", "name_evidence": "自然と調和した観光", "amount_man": 1994, "prev_man": 2021, "delta_man": -27},
    ],
}

# 文脈注記（国と同様、東京都もインバウンド・観光対策に多額を計上している点を明示）
TOURISM_NOTE = (
    "東京都も国と同様、インバウンド・観光対策に外国人政策（多文化共生・外国人材）をはるかに上回る予算を計上している"
    "（観光産業の振興 376億円 vs 外国人政策 16.8億円）。本対比は「外国人優遇でばらまき」という通説に対し、"
    "金額規模ではむしろ観光・インフラが圧倒的に大きいという事実を示す。"
)
BASIS_NOTE = (
    "東京都の外国人政策（多文化共生・外国人材）の主要事業の令和8年度予算。国の関係予算（総合的対応策）"
    "とは集計範囲・主体が異なる。金額は百万円単位の主要事業ベースで、1円単位の内訳は予算説明書を参照。"
)
