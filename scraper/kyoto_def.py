"""京都府の外国人特化予算の定義 — キュレーション方式（汎用 build_pref.py 用）

一次ソースは京都府「当初予算 主要事項説明」の部局別PDF（総合政策環境部。事業名と金額が
千円単位で記載）と「歳入内訳」PDF（一般会計の当初予算額。補正+当初=計の行内チェックサム内蔵）。

【重要・収録範囲の制約】令和5年度は全部局（知事直轄組織・政策企画部・府民環境部・
文化スポーツ部・商工労働観光部等）の主要事項説明資料を走査したが該当事業の記載がないため
未収録（一般会計総額のみ GA_HISTORY に収録）。OCRによる推測転記は行わない。
"""

GOVERNMENT = "京都府"
OUT_NAME = "kyoto.json"

_SEISAKU_R6 = {
    "label": "京都府 令和6年度当初予算 主要事項説明（総合政策環境部）",
    "url": "https://www.pref.kyoto.jp/yosan/documents/0604-2seisakutatedayo.pdf",
}
_SEISAKU_R7 = {
    "label": "京都府 令和7年度当初予算 主要事項説明（総合政策環境部）",
    "url": "https://www.pref.kyoto.jp/yosan/documents/r7tosyo_tate_seisaku.pdf",
}
_SEISAKU_R8 = {
    "label": "京都府 令和8年度当初予算 主要事項説明（総合政策環境部）",
    "url": "https://www.pref.kyoto.jp/yosan/documents/r8tosyo_tate_seisaku.pdf",
}
_SAINYU_R6 = {
    "label": "京都府 令和6年度当初予算 歳入内訳",
    "url": "https://www.pref.kyoto.jp/yosan/documents/0601sainyuu.pdf",
}
_SAINYU_R7 = {
    "label": "京都府 令和7年度当初予算 歳入内訳",
    "url": "https://www.pref.kyoto.jp/yosan/documents/r7_p1_sainyu.pdf",
}
_SAINYU_R8 = {
    "label": "京都府 令和8年度当初予算 歳入内訳",
    "url": "https://www.pref.kyoto.jp/yosan/documents/r8_p1_sainyu.pdf",
}
_SAINYU_R5 = {
    "label": "京都府 令和5年度当初予算 歳入内訳",
    "url": "https://www.pref.kyoto.jp/yosan/documents/r5tosyo_sainyu.pdf",
}

YEARS = [
    {
        "fiscal_year": 2024,
        "fiscal_year_label": "令和6年度",
        "source": _SEISAKU_R6,
        "items": [
            {
                "name": "多文化共生推進事業費",
                "name_evidence": "多文化共生推進事業費",
                "doc": _SEISAKU_R6["url"],
                "doc_type": "pdf",
                "category": "多文化共生",
                "bureau": "総合政策環境部",
                "amount_yen": 9605000,
                "amount_evidence": "多文化共生推進事業費9,605千円",  # 事業名＋金額の連結（対応ずれを排除）
                "desc": "外国人住民に対する生活情報の提供・相談を行う窓口の運営や「やさしい日本語」の行政機関での活用と府民への普及の促進等。",
            },
        ],
        "general_account": {
            "amount_yen": 995031000000,
            "amount_label": "9,950億3,100万円",
            # 歳入内訳「合計」行の「2月補正 9,445 ＋ 当初 995,031 ＝ 計 1,004,476」（百万円・行内チェックサム内蔵）
            "evidence": "9,445995,0311,004,476",
            "label": "令和6年度 一般会計 当初予算",
            "source": _SAINYU_R6,
        },
    },
    {
        "fiscal_year": 2025,
        "fiscal_year_label": "令和7年度",
        "source": _SEISAKU_R7,
        "items": [
            {
                "name": "多文化共生推進事業費",
                "name_evidence": "多文化共生推進事業費",
                "doc": _SEISAKU_R7["url"],
                "doc_type": "pdf",
                "category": "多文化共生",
                "bureau": "総合政策環境部",
                "amount_yen": 29725000,
                "amount_evidence": "多文化共生推進事業費拡充29,725千円",  # 資料上の【拡充】表記込みの連結
                "desc": "外国人住民への生活情報提供・相談窓口の運営、「やさしい日本語」普及等の多文化共生推進（令和7年度に拡充）。",
            },
        ],
        "general_account": {
            "amount_yen": 1029881000000,
            "amount_label": "1兆298億8,100万円",
            # 歳入内訳「合計」行の「30,618 ＋ 1,029,881 ＝ 1,060,499」（百万円・行内チェックサム内蔵）
            "evidence": "30,6181,029,8811,060,499",
            "label": "令和7年度 一般会計 当初予算",
            "source": _SAINYU_R7,
        },
    },
    {
        "fiscal_year": 2026,
        "fiscal_year_label": "令和8年度",
        "source": _SEISAKU_R8,
        "items": [
            {
                "name": "多文化共生推進事業費",
                "name_evidence": "多文化共生推進事業費",
                "doc": _SEISAKU_R8["url"],
                "doc_type": "pdf",
                "category": "多文化共生",
                "bureau": "総合政策環境部",
                "amount_yen": 31565000,
                "amount_evidence": "多文化共生推進事業費31,565千円",
                "desc": "外国人住民への生活情報提供・相談窓口の運営、「やさしい日本語」普及等の多文化共生推進。",
            },
        ],
        "general_account": {
            "amount_yen": 1043260000000,
            "amount_label": "1兆432億6,000万円",
            # 歳入内訳「合計」行の「14,847 ＋ 1,043,260 ＝ 1,058,107」（百万円・行内チェックサム内蔵）
            "evidence": "14,8471,043,2601,058,107",
            "label": "令和8年度 一般会計 当初予算",
            "source": _SAINYU_R8,
        },
    },
]

# 事業データの無い年度の一般会計総額（証跡照合のうえ参考収録）
GA_HISTORY = [
    {
        "fiscal_year": 2023,
        "fiscal_year_label": "令和5年度",
        "amount_yen": 1030220000000,
        "amount_label": "1兆302億2,000万円",
        # 歳入内訳「合計」行の「2,543 ＋ 1,030,220 ＝ 1,032,763」（百万円・行内チェックサム内蔵）
        "evidence": "2,5431,030,2201,032,763",
        "source": _SAINYU_R5,
        "note": "令和5年度は主要事項説明資料等に該当事業の記載がないため未収録（一般会計総額のみ）。",
    },
]

BASIS_NOTE = (
    "京都府の外国人特化予算（部局別『当初予算 主要事項説明』に事業名と金額が明記された"
    "外国人特化事業＝多文化共生推進事業費〔総合政策環境部〕）。"
    "外国人住民への生活情報提供・相談窓口の運営と「やさしい日本語」の普及等。"
    "※令和5年度は主要事項説明資料等に該当事業の記載がないため未収録（一般会計総額のみ参考収録）。"
    "全府民向け事業は含まない。金額は千円単位。"
)
TREND_NOTE = (
    "京都府の多文化共生推進事業費は令和6年度9,605千円→令和7年度29,725千円（拡充）→"
    "令和8年度31,565千円と3年で約3.3倍に増えたが、それでも府一般会計（約1兆円）の約0.003%。"
    "増額の中身は相談窓口の運営や「やさしい日本語」普及といった共生の基盤整備であり、"
    "『莫大な税金で外国人を優遇』という言説と実際の予算スケールには歴然とした差がある。"
)
