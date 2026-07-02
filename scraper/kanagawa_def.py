"""神奈川県の外国人特化予算の定義 — キュレーション方式（汎用 build_pref.py 用）

一次ソースは神奈川県の局別「当初予算 主要施策の概要」PDF（令和6年度=国際文化観光局、
令和7・8年度=組織再編後の文化スポーツ観光局。事業名と予算額を記載。令和6年度は万円単位、
令和7・8年度は千円単位）。一般会計総額は年度により資料形式が異なるため、
テキスト照合可能な資料（令和8年度=記者発表資料、令和6年度以前=県財政のあらまし）を使い分ける。

【重要・収録範囲の制約】令和5年度は局別「主要施策の概要」の所在を特定できておらず、
議案・予算説明書PDFは画像形式のため、鉄の掟（照合できない数値は掲載しない）に従い
事業は未収録（一般会計総額のみ GA_HISTORY に収録）。OCRによる推測転記は行わない。
令和7年度の全庁「当初予算案の概要」PDFは CIDフォントで機械照合不能のため、
一般会計総額は令和8年度記者発表資料の前年併記欄（当年+前年の連結証跡）を用いる。
"""

GOVERNMENT = "神奈川県"
OUT_NAME = "kanagawa.json"

_KOKU_R6 = {
    "label": "神奈川県 令和6年度当初予算 主要施策の概要（国際文化観光局）",
    "url": "https://www.pref.kanagawa.jp/documents/3847/04_6nendotousho_kokubun.pdf",
}
_BUN_R7 = {
    "label": "神奈川県 令和7年度当初予算 主要施策の概要（文化スポーツ観光局）",
    "url": "https://www.pref.kanagawa.jp/documents/3847/04reiwa7nendobunsukan.pdf",
}
_BUN_R8 = {
    "label": "神奈川県 令和8年度当初予算 主要施策の概要（文化スポーツ観光局）",
    "url": "https://www.pref.kanagawa.jp/documents/3847/04_reiwa8nendobunsukan.pdf",
}
_PRS_R8 = {
    "label": "神奈川県 令和8年度当初予算案の概要（記者発表資料）",
    "url": "https://www.pref.kanagawa.jp/documents/131969/2026020503.pdf",
}
_ARA_2024 = {
    "label": "県財政のあらまし（2024年1号）",
    "url": "https://www.pref.kanagawa.jp/documents/4316/2024-1.pdf",
}
_ARA_2023 = {
    "label": "県財政のあらまし（2023年1号）",
    "url": "https://www.pref.kanagawa.jp/documents/4316/2023-1.pdf",
}

YEARS = [
    {
        "fiscal_year": 2024,
        "fiscal_year_label": "令和6年度",
        "source": _KOKU_R6,
        "items": [
            {
                "name": "多言語情報支援事業",
                "name_evidence": "多言語情報支援事業",
                "doc": _KOKU_R6["url"],
                "doc_type": "pdf",
                "category": "外国人相談",
                "bureau": "国際文化観光局",
                "amount_yen": 61140000,
                "amount_evidence": "6,114万円",
                "desc": "外国籍県民向けの多言語による生活情報の提供・相談支援。",
            },
            {
                "name": "多文化共生推進事業費",
                "name_evidence": "多文化共生推進事業費",
                "doc": _KOKU_R6["url"],
                "doc_type": "pdf",
                "category": "多文化共生",
                "bureau": "国際文化観光局",
                "amount_yen": 10580000,
                "amount_evidence": "1,058万円",
                "desc": "多文化共生の地域社会づくりの推進。",
            },
            {
                "name": "地域日本語教育の総合的な体制づくり推進事業",
                "name_evidence": "地域日本語教育の総合的な体制づくり推進事業",
                "doc": _KOKU_R6["url"],
                "doc_type": "pdf",
                "category": "日本語教育",
                "bureau": "国際文化観光局",
                "amount_yen": 48430000,
                "amount_evidence": "4,843万円",
                "desc": "外国人住民向け地域日本語教育の県域体制づくり（文化庁補助事業スキーム）。",
            },
            {
                "name": "地域日本語教育の総合的な体制づくり推進事業費補助",
                "name_evidence": "地域日本語教育の総合的な体制づくり推進事業費補助",
                "doc": _KOKU_R6["url"],
                "doc_type": "pdf",
                "category": "日本語教育",
                "bureau": "国際文化観光局",
                "amount_yen": 8430000,
                "amount_evidence": "843万円",
                "desc": "市町村が行う地域日本語教育の体制づくりへの補助。",
            },
            {
                "name": "（公財）かながわ国際交流財団補助金",
                "name_evidence": "かながわ国際交流財団補助金",
                "doc": _KOKU_R6["url"],
                "doc_type": "pdf",
                "category": "多文化共生",
                "bureau": "国際文化観光局",
                "amount_yen": 102000000,
                "amount_evidence": "1億200万円",
                "desc": "多文化共生・外国籍県民支援を担う（公財）かながわ国際交流財団への補助。",
            },
            {
                "name": "医療通訳派遣システム事業費",
                "name_evidence": "医療通訳派遣システム事業費",
                "doc": _KOKU_R6["url"],
                "doc_type": "pdf",
                "category": "外国人相談",
                "bureau": "国際文化観光局",
                "amount_yen": 4080000,
                "amount_evidence": "408万円",
                "desc": "外国籍県民が安心して医療を受けられるための医療通訳派遣。",
            },
            {
                "name": "外国籍県民施策推進事業費",
                "name_evidence": "外国籍県民施策推進事業費",
                "doc": _KOKU_R6["url"],
                "doc_type": "pdf",
                "category": "多文化共生",
                "bureau": "国際文化観光局",
                "amount_yen": 3470000,
                "amount_evidence": "347万円",
                "desc": "外国籍県民かながわ会議の運営等、外国籍県民施策の推進。",
            },
            {
                "name": "留学生支援事業費",
                "name_evidence": "留学生支援事業費",
                "doc": _KOKU_R6["url"],
                "doc_type": "pdf",
                "category": "外国人材",
                "bureau": "国際文化観光局",
                "amount_yen": 54040000,
                "amount_evidence": "5,404万円",
                "desc": "外国人留学生の生活・就学支援。",
            },
            {
                "name": "留学生就職支援事業費",
                "name_evidence": "留学生就職支援事業費",
                "doc": _KOKU_R6["url"],
                "doc_type": "pdf",
                "category": "外国人材",
                "bureau": "国際文化観光局",
                "amount_yen": 23310000,
                "amount_evidence": "2,331万円",
                "desc": "外国人留学生の県内企業への就職支援。",
            },
        ],
        "general_account": {
            "amount_yen": 2104500000000,
            "amount_label": "2兆1,045億円",
            # 県財政のあらまし2024年1号 p1「令和6年度当初予算の規模は、一般会計で2兆1,045億円」
            "evidence": "一般会計で2兆1,045億円",
            "label": "令和6年度 一般会計 当初予算",
            "source": _ARA_2024,
        },
    },
    {
        "fiscal_year": 2025,
        "fiscal_year_label": "令和7年度",
        "source": _BUN_R7,
        "items": [
            {
                "name": "多文化共生推進事業費",
                "name_evidence": "多文化共生推進事業費",
                "doc": _BUN_R7["url"],
                "doc_type": "pdf",
                "category": "多文化共生",
                "bureau": "文化スポーツ観光局",
                "amount_yen": 11523000,
                "amount_evidence": "11,523千円",
                "desc": "多文化共生の地域社会づくりの推進（組織再編により文化スポーツ観光局へ移管）。",
            },
            {
                "name": "多言語情報支援事業",
                "name_evidence": "多言語情報支援事業",
                "doc": _BUN_R7["url"],
                "doc_type": "pdf",
                "category": "外国人相談",
                "bureau": "文化スポーツ観光局",
                "amount_yen": 65101000,
                "amount_evidence": "65,101千円",
                "desc": "外国籍県民向けの多言語による生活情報の提供・相談支援。",
            },
            {
                "name": "地域日本語教育の総合的な体制づくり推進事業",
                "name_evidence": "地域日本語教育の総合的な体制づくり推進事業",
                "doc": _BUN_R7["url"],
                "doc_type": "pdf",
                "category": "日本語教育",
                "bureau": "文化スポーツ観光局",
                "amount_yen": 59744000,
                "amount_evidence": "59,744千円",
                "desc": "外国人住民向け地域日本語教育の県域体制づくり。",
            },
            {
                "name": "医療通訳派遣システム事業費",
                "name_evidence": "医療通訳派遣システム事業費",
                "doc": _BUN_R7["url"],
                "doc_type": "pdf",
                "category": "外国人相談",
                "bureau": "文化スポーツ観光局",
                "amount_yen": 4081000,
                "amount_evidence": "4,081千円",
                "desc": "外国籍県民が安心して医療を受けられるための医療通訳派遣。",
            },
            {
                "name": "グローバル人材支援事業費",
                "name_evidence": "グローバル人材支援事業費",
                "doc": _BUN_R7["url"],
                "doc_type": "pdf",
                "category": "外国人材",
                "bureau": "文化スポーツ観光局",
                "amount_yen": 77354000,
                "amount_evidence": "77,354千円",
                "desc": "外国人留学生等の支援・県内定着の促進（令和8年度は留学生支援事業費に改称・同額）。",
            },
        ],
        "general_account": {
            "amount_yen": 2215800000000,
            "amount_label": "2兆2,158億円",
            # 令和8年度記者発表資料 p2「一般会計 2兆3,759億円 2兆2,158億円 107.2%」（当年+前年の連結＝チェックサム内蔵）
            "evidence": "2兆3,759億円2兆2,158億円",
            "label": "令和7年度 一般会計 当初予算",
            "source": _PRS_R8,
        },
    },
    {
        "fiscal_year": 2026,
        "fiscal_year_label": "令和8年度",
        "source": _BUN_R8,
        "items": [
            {
                "name": "留学生支援事業費",
                "name_evidence": "留学生支援事業費",
                "doc": _BUN_R8["url"],
                "doc_type": "pdf",
                "category": "外国人材",
                "bureau": "文化スポーツ観光局",
                "amount_yen": 77354000,
                "amount_evidence": "77,354千円",
                "desc": "外国人留学生等の支援・県内定着の促進（令和7年度グローバル人材支援事業費から改称・同額）。",
            },
            {
                "name": "多言語情報支援事業費",
                "name_evidence": "多言語情報支援事業費",
                "doc": _BUN_R8["url"],
                "doc_type": "pdf",
                "category": "外国人相談",
                "bureau": "文化スポーツ観光局",
                "amount_yen": 67360000,
                "amount_evidence": "67,360千円",
                "desc": "外国籍県民向けの多言語による生活情報の提供・相談支援。",
            },
            {
                "name": "地域日本語教育の総合的な体制づくり推進事業費",
                "name_evidence": "地域日本語教育の総合的な体制づくり推進事業費",
                "doc": _BUN_R8["url"],
                "doc_type": "pdf",
                "category": "日本語教育",
                "bureau": "文化スポーツ観光局",
                "amount_yen": 62968000,
                "amount_evidence": "62,968千円",
                "desc": "外国人住民向け地域日本語教育の県域体制づくり。",
            },
            {
                "name": "医療通訳派遣システム事業費",
                "name_evidence": "医療通訳派遣システム事業費",
                "doc": _BUN_R8["url"],
                "doc_type": "pdf",
                "category": "外国人相談",
                "bureau": "文化スポーツ観光局",
                "amount_yen": 4069000,
                "amount_evidence": "4,069千円",
                "desc": "外国籍県民が安心して医療を受けられるための医療通訳派遣。",
            },
            {
                "name": "多文化共生推進事業費",
                "name_evidence": "多文化共生推進事業費",
                "doc": _BUN_R8["url"],
                "doc_type": "pdf",
                "category": "多文化共生",
                "bureau": "文化スポーツ観光局",
                "amount_yen": 2188000,
                "amount_evidence": "2,188千円",
                "desc": "多文化共生の推進（令和8年度は住宅入居支援・同行支援等に機能を限定した再編後の額）。",
            },
        ],
        "general_account": {
            "amount_yen": 2375900000000,
            "amount_label": "2兆3,759億円",
            # 記者発表資料 p1「令和8年度一般会計当初予算額2兆3,759億円」
            "evidence": "令和8年度一般会計当初予算額2兆3,759億円",
            "label": "令和8年度 一般会計 当初予算",
            "source": _PRS_R8,
        },
    },
]

# 事業データの無い年度の一般会計総額（証跡照合のうえ参考収録）
GA_HISTORY = [
    {
        "fiscal_year": 2023,
        "fiscal_year_label": "令和5年度",
        "amount_yen": 2261600000000,
        "amount_label": "2兆2,616億円",
        # 県財政のあらまし2023年1号 p1「令和5年度当初予算の規模は、一般会計で2兆2,616億円」
        "evidence": "一般会計で2兆2,616億円",
        "source": _ARA_2023,
        "note": "令和5年度は局別主要施策資料を特定できていないため、事業は未収録（一般会計総額のみ）。",
    },
]

BASIS_NOTE = (
    "神奈川県の外国人特化予算（局別『当初予算 主要施策の概要』に事業名と金額が明記された"
    "外国人特化事業。令和6年度=国際文化観光局、令和7・8年度=組織再編後の文化スポーツ観光局）。"
    "金額は資料の表記単位（令和6年度=万円、令和7・8年度=千円）を円換算。"
    "掲載粒度は年度の資料により異なる（令和6年度は財団補助・市町村補助等も個別掲載）。"
    "※令和5年度は局別主要施策資料を特定できていないため事業は未収録（一般会計総額のみ参考収録）。"
    "全県民向け事業や国際文化交流（ベトナム友好交流等）は含まない。"
)
TREND_NOTE = (
    "神奈川県の外国人特化予算は年2〜3億円規模で、県一般会計（2兆円超）の約0.001%。"
    "多文化共生推進事業費の令和8年度の急減（11,523→2,188千円）は住宅入居・同行支援等への"
    "機能限定・再編によるもので、多言語相談・日本語教育・医療通訳・留学生支援の基幹事業は"
    "ほぼ横ばいで継続している。『莫大な税金で外国人を優遇』という言説と実際の予算スケールには"
    "歴然とした差がある。"
)
