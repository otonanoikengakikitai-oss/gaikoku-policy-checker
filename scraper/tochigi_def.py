"""栃木県の外国人特化予算の定義 — キュレーション方式（汎用 build_pref.py 用）

一次ソースは栃木県財政課「当初予算案の概要」（全体版・重点戦略PDF。事業名＋金額＋部局の
行内連結）と「予算規模」PDF（一般会計総額）。令和6年度資料は百万円単位、
令和7・8年度は万円単位。令和5年度は特徴資料に外国人施策の金額記載を特定できず
事業未収録（一般会計総額のみ GA_HISTORY に収録）。
"""

GOVERNMENT = "栃木県"
OUT_NAME = "tochigi.json"

_B = "https://www.pref.tochigi.lg.jp/b01"
_R6_ALL = {"label": "栃木県 令和6年度当初予算案の概要（全体版）", "url": _B + "/pref/zaiseijinji/yosan/2024tousyo/documents/00all_r6.pdf"}
_R7_ALL = {"label": "栃木県 令和7年度当初予算案の概要（全体版）", "url": _B + "/documents/00zentai_r7_2.pdf"}
_R8_S3 = {"label": "栃木県 令和8年度当初予算案 重点戦略（健康・共生戦略）", "url": _B + "/pref/zaiseijinji/yosan/2026tousyo/documents/03jyuutennsennryaku3.pdf"}
_R8_KIBO = {"label": "栃木県 令和8年度当初予算 予算規模", "url": _B + "/pref/zaiseijinji/yosan/2026tousyo/documents/01yosannkibo_r8.pdf"}
_R5_KIBO = {"label": "栃木県 令和5年度当初予算 予算規模", "url": _B + "/pref/zaiseijinji/yosan/2023tousyo/documents/01thought_r5.pdf"}

_D_KATSU = "外国人労働者の就労環境整備・高度外国人材の県内企業への確保（海外大学と連携した日本語教育・インターンシップ・ジョブフェア等）。"

YEARS = [
    {
        "fiscal_year": 2024, "fiscal_year_label": "令和6年度", "source": _R6_ALL,
        "items": [{
            "name": "外国人材活用強化事業費", "name_evidence": "外国人材活用強化事業費",
            "doc": _R6_ALL["url"], "doc_type": "pdf", "category": "外国人材", "bureau": "産業労働観光部",
            "amount_yen": 20000000, "amount_evidence": "○2外国人材活用強化事業費20(産業労働観光部)",
            "desc": _D_KATSU + "資料単位は百万円（20百万円）。",
        }],
        "general_account": {"amount_yen": 932800000000, "amount_label": "9,328億円",
            "evidence": "一般会計9,328億円", "label": "令和6年度 一般会計 当初予算", "source": _R6_ALL},
    },
    {
        "fiscal_year": 2025, "fiscal_year_label": "令和7年度", "source": _R7_ALL,
        "items": [
            {"name": "外国人材活用強化事業費", "name_evidence": "外国人材活用強化事業費",
             "doc": _R7_ALL["url"], "doc_type": "pdf", "category": "外国人材", "bureau": "産業労働観光部",
             "amount_yen": 44950000, "amount_evidence": "○3外国人材活用強化事業費4,495万円(産業労働観光部)",
             "desc": _D_KATSU},
            {"name": "多文化共生推進事業費", "name_evidence": "多文化共生推進事業費",
             "doc": _R7_ALL["url"], "doc_type": "pdf", "category": "多文化共生", "bureau": "生活文化スポーツ部",
             "amount_yen": 32170000, "amount_evidence": "○7多文化共生推進事業費3,217万円(生活文化スポーツ部)",
             "desc": "多文化共生の推進（外国人県民の生活支援等）。"},
        ],
        "general_account": {"amount_yen": 924200000000, "amount_label": "9,242億円",
            "evidence": "一般会計9,242億円", "label": "令和7年度 一般会計 当初予算", "source": _R7_ALL},
    },
    {
        "fiscal_year": 2026, "fiscal_year_label": "令和8年度", "source": _R8_S3,
        "items": [{
            "name": "外国人材活用強化事業費", "name_evidence": "外国人材活用強化事業費",
            "doc": _R8_S3["url"], "doc_type": "pdf", "category": "外国人材", "bureau": "産業労働観光部",
            "amount_yen": 65110000, "amount_evidence": "○15外国人材活用強化事業費6,511万円(産業労働観光部)",
            "desc": _D_KATSU + "令和8年度は多文化共生推進事業費が重点戦略資料に掲載されておらず未収録。",
        }],
        "general_account": {"amount_yen": 960680000000, "amount_label": "9,606億8,000万円",
            "evidence": "一般会計9,606億8,000万円", "label": "令和8年度 一般会計 当初予算", "source": _R8_KIBO},
    },
]

GA_HISTORY = [
    {"fiscal_year": 2023, "fiscal_year_label": "令和5年度", "amount_yen": 978600000000,
     "amount_label": "9,786億円", "evidence": "一般会計9,786億円", "source": _R5_KIBO,
     "note": "令和5年度は特徴資料に外国人施策の金額記載を特定できず事業は未収録（一般会計総額のみ）。"},
]

BASIS_NOTE = (
    "栃木県の外国人特化予算（財政課「当初予算案の概要」の重点戦略・特徴資料に事業名と金額が"
    "明記され、行内連結証跡で検証を通過した外国人特化事業）。重点施策ベースのため網羅ではなく、"
    "掲載は年度により異なる（令和8年度は多文化共生推進事業費の掲載なし）。"
    "金額単位は令和6年度=百万円、令和7・8年度=万円。令和5年度は事業未収録（一般会計総額のみ）。"
)
TREND_NOTE = (
    "栃木県の外国人材活用強化事業費は令和6年度2,000万円→令和8年度6,511万円へ3.3倍に拡大"
    "（高度外国人材の確保・定着支援）。それでも県一般会計（9,600億円規模）の約0.007%であり、"
    "『莫大な税金で外国人を優遇』という言説と実際の予算スケールには歴然とした差がある。"
)
