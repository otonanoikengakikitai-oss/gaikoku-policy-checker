"""沖縄県の外国人特化予算の定義 — キュレーション方式（汎用 build_pref.py 用）

一次ソースは沖縄県財政課「当初予算説明資料（主な事業）」PDF（事業行が
「事業名＋当年千円(前年千円)＋（部:課）」の連結＝前年併記チェックサム内蔵）と
「当初予算概要」PDF（一般会計総額）。

【収録範囲の制約】説明資料は「主な事業」の抜粋であり、外国人施策の掲載は年度により
異なる（令和5年度=特定技能外国人マッチング支援のみ、令和6年度=金額掲載なし、
令和7・8年度=外国人材受入支援事業）。令和6年度の外国人材受入支援事業の額は
令和7年度資料の前年併記から取得。一般会計総額の令和6・7年度は資料表記が
「約」付きの概数（億円）。
"""

GOVERNMENT = "沖縄県"
OUT_NAME = "okinawa.json"

_B = "https://www.pref.okinawa.jp/_res/projects/default_project/_page_/001/015/235"
_SETSU = {
    2023: {"label": "沖縄県 令和5年度当初予算 説明資料", "url": _B + "/r5_tousyoyosan_setumeisiryou.pdf"},
    2025: {"label": "沖縄県 令和7年度当初予算 説明資料", "url": _B + "/r7toushoyosansetsumeishiryou.pdf"},
    2026: {"label": "沖縄県 令和8年度当初予算 説明資料", "url": _B + "/r8tousyoyosan_siryo_resize.pdf"},
}
_GAIYO = {
    2023: {"label": "沖縄県 令和5年度当初予算 概要", "url": _B + "/r5_tousyoyosan_gaiyou.pdf"},
    2024: {"label": "沖縄県 令和6年度当初予算 概要", "url": _B + "/r6toushoyosangaiyou0328.pdf"},
    2025: {"label": "沖縄県 令和7年度当初予算 概要", "url": _B + "/r7toushoyosan_gaiyou.pdf"},
    2026: {"label": "沖縄県 令和8年度当初予算 概要", "url": _B + "/r8toushoyosan_gaiyou.pdf"},
}

_D_UKEIRE = "外国人材活用のための企業向けオンライン相談窓口の設置、セミナー、留学生等とのマッチング支援。"


YEARS = [
    {
        "fiscal_year": 2023,
        "fiscal_year_label": "令和5年度",
        "source": _SETSU[2023],
        "items": [
            {
                "name": "特定技能1号外国人のマッチング支援事業", "name_evidence": "特定技能1号外国人のマッチング支援事業",
                "doc": _SETSU[2023]["url"], "doc_type": "pdf",
                "category": "外国人材", "bureau": "子ども生活福祉部 高齢者福祉介護課",
                "amount_yen": 11500000,
                "amount_evidence": "特定技能1号外国人のマッチング支援事業11,500(0)",  # 当年+前年(0=新規)の連結
                "desc": "県内介護施設等と特定技能1号外国人介護人材の就労希望者等とのマッチング支援（令和5年度新規）。",
            },
        ],
        "general_account": {
            "amount_yen": 861400000000,
            "amount_label": "8,614億円",
            "evidence": "令和5年度沖縄県一般会計当初予算8,614億円",
            "label": "令和5年度 一般会計 当初予算",
            "source": _GAIYO[2023],
        },
    },
    {
        "fiscal_year": 2024,
        "fiscal_year_label": "令和6年度",
        "source": _SETSU[2025],
        "items": [
            {
                "name": "外国人材受入支援事業", "name_evidence": "外国人材受入支援事業",
                "doc": _SETSU[2025]["url"], "doc_type": "pdf",
                "category": "外国人材", "bureau": "商工労働部 雇用政策課",
                "amount_yen": 17699000,
                "amount_evidence": "外国人材受入支援事業17,699(17,699)",  # 令和7年度資料の前年併記（括弧＝R6額）
                "desc": _D_UKEIRE + "（令和7年度資料の前年併記より）。",
            },
        ],
        "general_account": {
            "amount_yen": 842100000000,
            "amount_label": "約8,421億円",
            "evidence": "令和6年度沖縄県一般会計当初予算約8,421億円",
            "label": "令和6年度 一般会計 当初予算（資料表記は概数）",
            "source": _GAIYO[2024],
        },
    },
    {
        "fiscal_year": 2025,
        "fiscal_year_label": "令和7年度",
        "source": _SETSU[2025],
        "items": [
            {
                "name": "外国人材受入支援事業", "name_evidence": "外国人材受入支援事業",
                "doc": _SETSU[2025]["url"], "doc_type": "pdf",
                "category": "外国人材", "bureau": "商工労働部 雇用政策課",
                "amount_yen": 17699000,
                "amount_evidence": "外国人材受入支援事業17,699(17,699)",
                "prev_yen": 17699000,
                "desc": _D_UKEIRE,
            },
        ],
        "general_account": {
            "amount_yen": 889400000000,
            "amount_label": "8,894億円",
            # 令和8年度概要の前年併記「R7当初8,894億円、対前年度+574億円」（8,894+574=9,468のチェックサム内蔵）
            "evidence": "R7当初8,894億円、対前年度+574億円",
            "label": "令和7年度 一般会計 当初予算",
            "source": _GAIYO[2026],
        },
    },
    {
        "fiscal_year": 2026,
        "fiscal_year_label": "令和8年度",
        "source": _SETSU[2026],
        "items": [
            {
                "name": "外国人材受入支援事業", "name_evidence": "外国人材受入支援事業",
                "doc": _SETSU[2026]["url"], "doc_type": "pdf",
                "category": "外国人材", "bureau": "商工労働部 雇用政策課",
                "amount_yen": 19200000,
                "amount_evidence": "外国人材受入支援事業19,200(17,699)",
                "prev_yen": 17699000,
                "desc": _D_UKEIRE,
            },
        ],
        "general_account": {
            "amount_yen": 946800000000,
            "amount_label": "9,468億円",
            "evidence": "9,468R8当初予算額億円(R7当初8,894億円、対前年度+574億円",
            "label": "令和8年度 一般会計 当初予算",
            "source": _GAIYO[2026],
        },
    },
]

BASIS_NOTE = (
    "沖縄県の外国人特化予算（財政課「当初予算説明資料（主な事業）」に事業名と金額が明記され、"
    "当年＋前年括弧の連結証跡で検証を通過した外国人特化事業）。説明資料は主な事業の抜粋のため"
    "網羅ではなく、掲載は年度により異なる（令和5年度=特定技能外国人マッチング支援、"
    "令和7・8年度=外国人材受入支援事業。令和6年度は令和7年度資料の前年併記より取得）。"
    "一般会計総額の令和6年度は資料表記が「約」付きの概数。金額は千円単位。"
)
TREND_NOTE = (
    "沖縄県の外国人特化予算（主な事業ベース）は、外国人材受入支援事業が令和6〜7年度の"
    "1,770万円から令和8年度1,920万円へ微増した程度で、県一般会計（9,468億円）の約0.002%。"
    "『莫大な税金で外国人を優遇』という言説と実際の予算スケールには歴然とした差がある。"
)
