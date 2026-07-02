"""福岡県の外国人特化予算の定義 — キュレーション方式・多年度（汎用 build_pref.py 用）

一次ソースは福岡県「当初予算の編成概要」PDF（財政課・事項名と予算額を千円単位で記載、
前年度当初予算額が括弧で併記される）。R8版とR7版の2文書で3年分＋年度間チェックサムが成立:
  R8版: R8額 ＋ (R7額)   /  R7版: R7額 ＋ (R6額)
build が毎回、①lg.jp生存 ②事項名の現存 ③当年額・前年括弧額の現存 ④年度間チェックサム
（R8版の括弧=R7版の当年額 等）を照合する。国際交流一般・姉妹都市交流・国連支援等は含めない。
"""

GOVERNMENT = "福岡県"
OUT_NAME = "fukuoka.json"

_R8_PDF = {"label": "福岡県 令和8年度当初予算の編成概要", "url": "https://www.pref.fukuoka.lg.jp/uploaded/attachment/278127.pdf"}
_R7_PDF = {"label": "福岡県 令和7年度当初予算の編成概要", "url": "https://www.pref.fukuoka.lg.jp/uploaded/attachment/256820.pdf"}

_POP_BASIS = (
    "総務省「住民基本台帳に基づく人口」（各年1月1日現在・外国人住民）。"
    "国の在留外国人統計（年末・在留資格ベース）とは統計の種類・基準日が異なる。"
)
_SOUMU_R6 = {"label": "総務省 住民基本台帳に基づく人口（令和6年1月1日現在）", "url": "https://www.soumu.go.jp/main_content/000959269.pdf"}
_SOUMU_R7 = {"label": "総務省 住民基本台帳に基づく人口（令和7年1月1日現在）", "url": "https://www.soumu.go.jp/main_content/000892947.pdf"}

YEARS = [
    {
        "fiscal_year": 2024,
        "fiscal_year_label": "令和6年度",
        "source": _R7_PDF,  # R6の金額はR7版の前年度欄（括弧）を証跡とする
        "items": [
            {
                "name": "外国人材受入対策費",
                "name_evidence": "外国人材受入対策費",
                "doc": _R7_PDF["url"],
                "doc_type": "pdf",
                "category": "多文化共生",
                "bureau": "国際政策課",
                "amount_yen": 4153000,
                "amount_evidence": "(4,153)",
                "desc": "福岡県外国人材受入対策協議会の運営、市町村等が実施する日本語教室の運営支援等。",
            },
            {
                "name": "海外人材活躍推進費",
                "name_evidence": "海外人材活躍推進費",
                "doc": _R7_PDF["url"],
                "doc_type": "pdf",
                "category": "外国人材",
                "bureau": "国際政策課",
                "amount_yen": 74220000,
                "amount_evidence": "(74,220)",
                "desc": "FUKUOKA IS OPENセンターの運営、海外人材の就労促進に向けた企業開拓・留学生等の支援等。",
            },
        ],
        "general_account": {
            "amount_yen": 2132060720000,
            "amount_label": "2兆1,320億6,072万円",
            # R7版の予算規模行「一般会計 2,187,782,708 2,132,060,720 55,721,988」（当年+前年+増減の連結＝チェックサム内蔵）
            "evidence": "一般会計2,187,782,7082,132,060,72055,721,988",
            "label": "令和6年度 一般会計 当初予算",
            "source": _R7_PDF,
        },
        "population": {
            "foreign": 98130,
            "total": 5095379,
            "as_of": "令和6年1月1日現在",
            "total_as_of": "令和6年1月1日現在",
            "metric_label": "外国人住民数",
            "foreign_evidence": "福岡県98,130",
            "total_evidence": "福岡県5,095,379",
            "basis": _POP_BASIS,
            "source": _SOUMU_R6,
            "total_source": _SOUMU_R6,
        },
    },
    {
        "fiscal_year": 2025,
        "fiscal_year_label": "令和7年度",
        "source": _R7_PDF,
        "items": [
            {
                "name": "外国人材受入対策費",
                "name_evidence": "外国人材受入対策費",
                "doc": _R7_PDF["url"],
                "doc_type": "pdf",
                "category": "多文化共生",
                "bureau": "国際政策課",
                "amount_yen": 4159000,
                "amount_evidence": "4,159",
                "prev_yen": 4153000,
                "prev_evidence": "(4,153)",
                "desc": "福岡県外国人材受入対策協議会の運営、市町村等が実施する日本語教室の運営支援等。",
            },
            {
                "name": "海外人材活躍推進費",
                "name_evidence": "海外人材活躍推進費",
                "doc": _R7_PDF["url"],
                "doc_type": "pdf",
                "category": "外国人材",
                "bureau": "国際政策課",
                "amount_yen": 54999000,
                "amount_evidence": "54,999",
                "prev_yen": 74220000,
                "prev_evidence": "(74,220)",
                "desc": "FUKUOKA IS OPENセンターの運営、海外人材の就労促進、在留外国人への相談体制の強化（令和7年度新規）等。",
            },
        ],
        "general_account": {
            "amount_yen": 2187782708000,
            "amount_label": "2兆1,877億8,270万8千円",
            "evidence": "一般会計2,187,782,7082,132,060,720",
            "label": "令和7年度 一般会計 当初予算",
            "source": _R7_PDF,
        },
        "population": {
            "foreign": 111461,
            "total": 5086957,
            "as_of": "令和7年1月1日現在",
            "total_as_of": "令和7年1月1日現在",
            "metric_label": "外国人住民数",
            "foreign_evidence": "福岡県111,461",
            "total_evidence": "福岡県5,086,957",
            "basis": _POP_BASIS,
            "source": _SOUMU_R7,
            "total_source": _SOUMU_R7,
        },
    },
    {
        "fiscal_year": 2026,
        "fiscal_year_label": "令和8年度",
        "source": _R8_PDF,
        "items": [
            {
                "name": "外国人との相互理解促進費",
                "name_evidence": "外国人との相互理解",
                "doc": _R8_PDF["url"],
                "doc_type": "pdf",
                "category": "多文化共生",
                "bureau": "国際政策課",
                "amount_yen": 8591000,
                "amount_evidence": "8,591",
                "prev_yen": 0,
                "prev_evidence": "(0)",
                "desc": "外国人との共生社会の形成に向けた相互理解の促進に要する経費（令和8年度新規）。",
            },
            {
                "name": "外国人材受入対策費",
                "name_evidence": "外国人材受入対策費",
                "doc": _R8_PDF["url"],
                "doc_type": "pdf",
                "category": "多文化共生",
                "bureau": "国際政策課",
                "amount_yen": 4172000,
                "amount_evidence": "4,172",
                "prev_yen": 4159000,
                "prev_evidence": "(4,159)",
                "desc": "福岡県外国人材受入対策協議会の運営、市町村等が実施する日本語教室の運営支援等。",
            },
            {
                "name": "海外人材活躍推進費",
                "name_evidence": "海外人材活躍推進費",
                "doc": _R8_PDF["url"],
                "doc_type": "pdf",
                "category": "外国人材",
                "bureau": "国際政策課",
                "amount_yen": 58419000,
                "amount_evidence": "58,419",
                "prev_yen": 54999000,
                "prev_evidence": "(54,999)",
                "desc": "FUKUOKA IS OPENセンター運営、海外人材の就労促進に向けた企業開拓・留学生等の支援、外国人からの相談への対応能力向上（新規）等。",
            },
        ],
        "general_account": {
            "amount_yen": 2300027028000,
            "amount_label": "2兆3,000億2,702万8千円",
            "evidence": "一般会計2,300,027,0282,187,782,708",
            "label": "令和8年度 一般会計 当初予算",
            "source": _R8_PDF,
        },
        "population": {
            "foreign": 111461,
            "total": 5086957,
            "as_of": "令和7年1月1日現在（令和8年1月1日現在の公表前のため取得可能な最新実績）",
            "total_as_of": "令和7年1月1日現在",
            "metric_label": "外国人住民数",
            "foreign_evidence": "福岡県111,461",
            "total_evidence": "福岡県5,086,957",
            "basis": _POP_BASIS,
            "source": _SOUMU_R7,
            "total_source": _SOUMU_R7,
        },
    },
]

BASIS_NOTE = (
    "福岡県の外国人特化予算（国際政策課の外国人特化事業＝外国人との相互理解促進費・外国人材受入対策費・"
    "海外人材活躍推進費の当初予算額）。出典は財政課「当初予算の編成概要」で、前年度当初予算額の括弧併記により"
    "年度間チェックサムを毎回照合。国際交流一般・姉妹都市交流・国連機関支援・旅券事務や、"
    "全県民向けのインフラ・福祉等は含まない。金額は千円単位の編成概要ベース。"
)
TREND_NOTE = (
    "福岡県の外国人住民数は令和7年1月1日で111,461人（総人口の約2.2%）と増加傾向だが、県の外国人特化予算は"
    "年6,000万〜8,000万円規模で、県一般会計（2兆円台）の約0.003%に過ぎない。内容も相談窓口（FUKUOKA IS OPEN"
    "センター）・日本語教室支援・就労促進といった情報・体制整備が中心であり、『莫大な税金で外国人を優遇』"
    "という言説と行政予算の実スケールには歴然とした差がある。"
)
