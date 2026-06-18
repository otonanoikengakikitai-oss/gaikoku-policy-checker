"""埼玉・川口（トレンド焦点）の外国人特化予算の定義 — キュレーション方式・多年度

川口市の一次ソース（各年度の「当初予算のポイント」PDF）から、外国人特化予算の実額を
人手で検証して記録する。build が各年度ごとに:
  1. その年度の出典PDFが lg.jp で生存していること
  2. 各事業の「事業名（name_evidence）」がその年度のPDF本文に現存すること
  3. 各金額の「実額表記（amount_evidence）」がその年度のPDF本文に現存すること
  4. 対比に使う市の一般会計総額の表記もその年度のPDFに現存すること
を満たした年度・事業のみ公開する（捏造・転記ミス・年度混入の防止）。

※全市民向けのインフラ予算等は混ぜない。外国人特化（多文化共生）のみ。
"""

GOVERNMENT = "埼玉県川口市"
REGION_LABEL = "埼玉県＋川口市（焦点）"

# ===== メイン：埼玉県（県全体）の外国人特化予算 =====
# 出典: 埼玉県「議会提出予算説明書」（款項目別の本年度予算額・千円単位）。
# 外国人特化の「目」= 多文化共生推進事業費（多言語相談・日本語教育・地域づくり等）＋
# 外国人地域生活支援事業費（外国人総合相談センター）。全県民向けの事業は含まない。
# 一般会計総額は各年度「当初予算案の概要」PDFの実額表記で対比する。
PREF_GOVERNMENT = "埼玉県"
PREF_BASIS_NOTE = (
    "埼玉県の外国人特化予算（県民生活部国際課の「多文化共生推進事業費」＋「外国人地域生活支援事業費」の"
    "目別当初予算額）。多言語相談・日本語教育・外国人総合相談センター等で、全県民向けのインフラ・福祉等は含まない。"
    "金額は千円単位の予算説明書ベース。"
)
PREF_TREND_NOTE = (
    "埼玉県は外国人住民数が全国有数で、多文化共生を県の重点施策に位置づける。だが県の一般会計（2兆円規模）に対し、"
    "外国人特化予算は数千万円規模に過ぎない。令和7年度に多文化共生推進事業費が一時的に増えたが、内容は相談体制・"
    "日本語教育・地域づくり等の情報・体制整備であり、『莫大な外国人優遇』という通説と実スケールには歴然とした差がある。"
)

PREF_YEARS = [
    {
        "fiscal_year": 2024,
        "fiscal_year_label": "令和6年度",
        "source": {
            "label": "埼玉県 令和6年度 議会提出予算説明書",
            "url": "https://www.pref.saitama.lg.jp/documents/243477/r6-tosyo-yosetu-2.pdf",
        },
        "items": [
            {"name": "多文化共生推進事業費", "name_evidence": "多文化共生推進事業費", "bureau": "県民生活部 国際課", "category": "多文化共生", "amount_yen": 17166000, "amount_evidence": "17,166", "desc": "多言語による行政・生活情報の提供、地域日本語教育、多文化共生の地域づくり、ボランティア育成等。"},
            {"name": "外国人地域生活支援事業費", "name_evidence": "外国人地域生活支援事", "bureau": "県民生活部 国際課", "category": "外国人相談", "amount_yen": 17568000, "amount_evidence": "17,568", "desc": "外国人総合相談センター埼玉の運営（多言語・やさしい日本語による生活相談）。"},
        ],
        "general_account": {
            "amount_yen": 2119744000000,
            "amount_evidence": "2兆1,197億4,400万円",
            "label": "令和6年度 一般会計 当初予算",
            "source": {"label": "埼玉県 令和6年度 当初予算案の概要", "url": "https://www.pref.saitama.lg.jp/documents/243477/00-r6-02-siryo2-2.pdf"},
        },
    },
    {
        "fiscal_year": 2025,
        "fiscal_year_label": "令和7年度",
        "source": {
            "label": "埼玉県 令和7年度 議会提出予算説明書",
            "url": "https://www.pref.saitama.lg.jp/documents/260021/r7-yosetu.pdf",
        },
        "items": [
            {"name": "多文化共生推進事業費", "name_evidence": "多文化共生推進事業費", "bureau": "県民生活部 国際課", "category": "多文化共生", "amount_yen": 56468000, "amount_evidence": "56,468", "desc": "多言語による行政・生活情報の提供、地域日本語教育、多文化共生の地域づくり等（令和7年度は拡充）。"},
            {"name": "外国人地域生活支援事業費", "name_evidence": "外国人地域生活支援事", "bureau": "県民生活部 国際課", "category": "外国人相談", "amount_yen": 17782000, "amount_evidence": "17,782", "desc": "外国人総合相談センター埼玉の運営（多言語・やさしい日本語による生活相談）。"},
        ],
        "general_account": {
            "amount_yen": 2230890000000,
            "amount_evidence": "2兆2,308億9,000万円",
            "label": "令和7年度 一般会計 当初予算",
            "source": {"label": "埼玉県 令和7年度 当初予算案の概要", "url": "https://www.pref.saitama.lg.jp/documents/260021/03_r7-02-siryou2.pdf"},
        },
    },
    {
        "fiscal_year": 2026,
        "fiscal_year_label": "令和8年度",
        "source": {
            "label": "埼玉県 令和8年度 議会提出予算説明書",
            "url": "https://www.pref.saitama.lg.jp/documents/274057/yosetur8.pdf",
        },
        "items": [
            {"name": "多文化共生推進事業費", "name_evidence": "多文化共生推進事業費", "bureau": "県民生活部 国際課", "category": "多文化共生", "amount_yen": 27036000, "amount_evidence": "27,036", "desc": "多言語による行政・生活情報の提供（外国人の生活ガイド）、地域日本語教育、多文化共生の地域づくり、災害時の外国人支援、ボランティア育成等。"},
            {"name": "外国人地域生活支援事業費", "name_evidence": "外国人地域生活支援事", "bureau": "県民生活部 国際課", "category": "外国人相談", "amount_yen": 17782000, "amount_evidence": "17,782", "desc": "外国人総合相談センター埼玉の運営（13言語＋やさしい日本語による生活相談）。"},
        ],
        "general_account": {
            "amount_yen": 2434865000000,
            "amount_evidence": "2兆4,348億6,500万円",
            "label": "令和8年度 一般会計 当初予算",
            "source": {"label": "埼玉県 令和8年度 当初予算案の概要", "url": "https://www.pref.saitama.lg.jp/documents/274057/03-r8-02-siryou2.pdf"},
        },
    },
]

YEARS = [
    {
        "fiscal_year": 2024,
        "fiscal_year_label": "令和6年度",
        "source": {
            "label": "川口市 令和6年度 当初予算のポイント",
            "url": "https://www.city.kawaguchi.lg.jp/material/files/group/9/r6tousyoyosannpointo.pdf",
        },
        "items": [
            {
                "name": "多文化共生推進事業（継続）",
                "name_evidence": "多文化共生推進事業",
                "bureau": "協働推進課",
                "category": "多文化共生",
                "amount_yen": 23966000,
                "amount_evidence": "2,396万6千円",
                "desc": "外国人住民への多言語による情報提供・生活支援等を実施。",
            }
        ],
        "city_general_account": {
            "amount_yen": 255460000000,
            "amount_evidence": "2,554億6,000万円",
            "label": "令和6年度 一般会計 当初予算",
        },
        "population": {
            "foreign": 44441,
            "total": 607279,
            "as_of": "令和6年4月1日現在",
            "source": {
                "label": "川口市 統計月報（令和6年4月）",
                "url": "https://www.city.kawaguchi.lg.jp/material/files/group/7/R0604.pdf",
            },
        },
    },
    {
        "fiscal_year": 2025,
        "fiscal_year_label": "令和7年度",
        "source": {
            "label": "川口市 令和7年度 当初予算のポイント",
            "url": "https://www.city.kawaguchi.lg.jp/material/files/group/9/r7tousyoyosannpointo.pdf",
        },
        "items": [
            {
                "name": "多文化共生推進事業（拡充）",
                "name_evidence": "多文化共生推進事業",
                "bureau": "協働推進課",
                "category": "多文化共生",
                "amount_yen": 29665000,
                "amount_evidence": "2,966万5千円",
                "desc": "多言語による対応支援の拡充（テレビ電話通訳サービス）や、外国人向けポータルサイト「川口市外国人生活ガイド」等による生活支援を実施。",
            }
        ],
        "city_general_account": {
            "amount_yen": 273720000000,
            "amount_evidence": "2,737億2,000万円",
            "label": "令和7年度 一般会計 当初予算",
        },
        "population": {
            "foreign": 49464,
            "total": 607943,
            "as_of": "令和7年4月1日現在",
            "source": {
                "label": "川口市 統計月報（令和7年4月）",
                "url": "https://www.city.kawaguchi.lg.jp/material/files/group/7/R0704.pdf",
            },
        },
    },
    {
        "fiscal_year": 2026,
        "fiscal_year_label": "令和8年度",
        "source": {
            "label": "川口市 令和8年度 当初予算のポイント",
            "url": "https://www.city.kawaguchi.lg.jp/material/files/group/9/r8tousyoyosannpointo.pdf",
        },
        "items": [
            {
                "name": "多文化共生推進事業（継続）",
                "name_evidence": "多文化共生推進事業",
                "bureau": "協働推進課",
                "category": "多文化共生",
                "amount_yen": 27897000,
                "amount_evidence": "2,789万7千円",
                "desc": "外国人向けポータルサイト「川口市外国人生活ガイド」（税金・ごみ出しルール・健康保険等の情報を掲載）等による生活支援を実施。",
            },
            {
                "name": "多文化共生指針策定事業（臨時）",
                "name_evidence": "多文化共生指針策定事業",
                "bureau": "協働推進課",
                "category": "多文化共生",
                "amount_yen": 2398000,
                "amount_evidence": "239万8千円",
                "desc": "第2次多文化共生指針改訂版（令和5年度～9年度）に基づく取組の推進等。",
            },
        ],
        "city_general_account": {
            "amount_yen": 256970000000,
            "amount_evidence": "2,569億7,000万円",
            "label": "令和8年度 一般会計 当初予算",
        },
        "population": {
            "foreign": 55012,
            "total": 609493,
            "as_of": "令和8年4月1日現在",
            "source": {
                "label": "川口市 統計月報（令和8年4月）",
                "url": "https://www.city.kawaguchi.lg.jp/material/files/group/7/R0804.pdf",
            },
        },
    },
]

BASIS_NOTE = (
    "川口市の外国人特化予算（協働推進課の多文化共生関連事業）の各年度当初予算。主要事業ベースで、"
    "1円単位の細目は予算書を参照。全市民向けのインフラ・福祉等の予算は含まない。"
)
TREND_NOTE = (
    "SNSでは『川口市は外国人（クルド人等）の対応に莫大な市民の税金を投入して優遇している』との言説が拡散している。"
    "しかし一次ソースで外国人特化の実額を切り分けると、市の一般会計（数千億円規模）に対し、多文化共生関連は"
    "数千万円規模に過ぎず、内容も外国人生活ガイドや多言語相談・指針策定等の情報・体制整備である。"
    "感情論の『莫大』と、行政予算の実スケールには歴然とした差がある。"
)
