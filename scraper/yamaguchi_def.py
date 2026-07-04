"""山口県の外国人特化予算の定義 — キュレーション方式（汎用 build_pref.py 用）

第八波（東北・中国四国コンプリート）で追加。一次ソース・収録範囲は BASIS_NOTE を参照。
"""

GOVERNMENT = "山口県"
OUT_NAME = "yamaguchi.json"

_DOCS = {
    "SHUYO": {"label": "山口県 令和8年度当初予算 主要事業の概要", "url": "https://www.pref.yamaguchi.lg.jp/uploaded/attachment/232227.pdf"},
    "GAIYO": {"label": "山口県 令和8年度当初予算の概要（一般会計）", "url": "https://www.pref.yamaguchi.lg.jp/uploaded/attachment/232229.pdf"},
}


def _item(name, name_ev, dockey, cat, bureau, yen, ev, desc):
    return {"name": name, "name_evidence": name_ev, "doc": _DOCS[dockey]["url"], "doc_type": "pdf",
            "category": cat, "bureau": bureau, "amount_yen": yen, "amount_evidence": ev, "desc": desc}


YEARS = [
    {
        "fiscal_year": 2023, "fiscal_year_label": "令和5年度", "source": {"label": "山口県 令和5年度当初予算の概要（一般会計）", "url": "https://www.pref.yamaguchi.lg.jp/uploaded/attachment/142420.pdf"},
        "items": [], "empty_note": '※令和5年度は主要資料に外国人特化事業の記載（金額明記）が確認できないため事業は未収録（一般会計総額のみ収録）。',
        "general_account": {"amount_yen": 794013000000, "amount_label": "7,940億1,300万円",
            "evidence": '当初予算額7,940億13百万円(対前年度比+1.0%)', "label": "令和5年度 一般会計 当初予算", "source": {"label": "山口県 令和5年度当初予算の概要（一般会計）", "url": "https://www.pref.yamaguchi.lg.jp/uploaded/attachment/142420.pdf"}},
    },
    {
        "fiscal_year": 2024, "fiscal_year_label": "令和6年度", "source": {"label": "山口県 令和6年度当初予算の概要（一般会計）", "url": "https://www.pref.yamaguchi.lg.jp/uploaded/attachment/172217.pdf"},
        "items": [], "empty_note": '※令和6年度は主要資料に外国人特化事業の記載（金額明記）が確認できないため事業は未収録（一般会計総額のみ収録）。',
        "general_account": {"amount_yen": 744021000000, "amount_label": "7,440億2,100万円",
            "evidence": '当初予算額7,440億21百万円(対前年度比▲6.3%)', "label": "令和6年度 一般会計 当初予算", "source": {"label": "山口県 令和6年度当初予算の概要（一般会計）", "url": "https://www.pref.yamaguchi.lg.jp/uploaded/attachment/172217.pdf"}},
    },
    {
        "fiscal_year": 2026,
        "fiscal_year_label": "令和8年度",
        "source": _DOCS["SHUYO"],
        "items": [
            _item('外国人介護人材確保支援事業', '外国人介護人材確保支援事業', 'SHUYO', '外国人材', '健康福祉部', 22000000, '(22,000千円)',
                  '外国人介護人材の確保支援（令和8年度新規）。'),
        ],
        "general_account": {
            "amount_yen": 786295000000,
            "amount_label": "7,862億9,500万円",
            "evidence": '当初予算額7,862億95百万円(対前年度比+6.3%)',
            "label": "令和8年度 一般会計 当初予算",
            "source": _DOCS["GAIYO"],
        },
    },
]

BASIS_NOTE = (
    '山口県の外国人特化予算（「主要事業の概要」に事業名と金額が明記され検証を通過した外国人特化事業）。主要事業ベースのため網羅ではない。令和5〜7年度は追加調査で拡張予定のため未収録。金額は千円単位。'
)
TREND_NOTE = (
    '山口県の外国人特化予算（令和8年度・主要事業の確認可能分）は外国人介護人材確保支援2,200万円で、県一般会計（7,863億円）の約0.003%。『莫大な税金で外国人を優遇』という言説と実際の予算スケールには歴然とした差がある。'
)
