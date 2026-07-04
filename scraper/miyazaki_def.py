"""宮崎県の外国人特化予算の定義 — キュレーション方式（汎用 build_pref.py 用）

第九波（47都道府県コンプリート）で追加。一次ソース・収録範囲は BASIS_NOTE を参照。
"""

GOVERNMENT = "宮崎県"
OUT_NAME = "miyazaki.json"

_DOCS = {
    "GAIYO": {"label": "宮崎県 令和8年度当初予算案の概要", "url": "https://www.pref.miyazaki.lg.jp/documents/106626/106626_20260208115631-1.pdf"},
}


def _item(name, name_ev, dockey, cat, bureau, yen, ev, desc):
    return {"name": name, "name_evidence": name_ev, "doc": _DOCS[dockey]["url"], "doc_type": "pdf",
            "category": cat, "bureau": bureau, "amount_yen": yen, "amount_evidence": ev, "desc": desc}


YEARS = [
    {
        "fiscal_year": 2025,
        "fiscal_year_label": "令和7年度",
        "source": _DOCS["GAIYO"],
        "items": [],
        "empty_note": '※令和7年度は主要資料に外国人特化事業の記載（金額明記）が確認できないため事業は未収録（一般会計総額のみ収録）。',
        "general_account": {
            "amount_yen": 667960000000,
            "amount_label": "6,679億6,000万円",
            "evidence": '一般会計6,899.56,679.6219.93.3',
            "label": "令和7年度 一般会計 当初予算",
            "source": _DOCS["GAIYO"],
        },
    },
    {
        "fiscal_year": 2026,
        "fiscal_year_label": "令和8年度",
        "source": _DOCS["GAIYO"],
        "items": [
            _item('海外連携強化による外国人材確保事業', '海外連携強化による外国人材確保事業', 'GAIYO', '外国人材', '商工観光労働部', 24000000, '海外連携強化による外国人材確保事業2,400万円',
                  '宮崎県外国人材受入・定着支援センターの運営・海外との連携による外国人材のマッチング支援。資料単位は万円（2,400万円）。'),
            _item('農業外国人材「育成就労制度」体制構築事業', '農業外国人材「育成就労制度」体制構築事業', 'GAIYO', '外国人材', '農政水産部', 18000000, '農業外国人材「育成就労制度」体制構築事業1,800万円',
                  '育成就労制度に対応した農業分野の外国人材受入体制の構築。資料単位は万円（1,800万円）。'),
        ],
        "general_account": {
            "amount_yen": 689950000000,
            "amount_label": "6,899億5,000万円",
            "evidence": '一般会計6,899.56,679.6219.93.3',
            "label": "令和8年度 一般会計 当初予算",
            "source": _DOCS["GAIYO"],
        },
    },
]

BASIS_NOTE = (
    '宮崎県の外国人特化予算（「当初予算案の概要」に事業名と金額が明記され、連結証跡で検証を通過した外国人特化事業2件）。一般会計総額は「6,899.5（R8）6,679.6（R7）219.9（増減）3.3%」の前年併記＋増減チェックサム内蔵（億円）。令和5〜7年度は追加調査で拡張予定のため未収録。'
)
TREND_NOTE = (
    '宮崎県の外国人特化予算（令和8年度・確認可能分）は約4,200万円で、外国人材受入・定着支援センターと農業の育成就労対応が中心。県一般会計（6,900億円）の約0.006%であり、『莫大な税金で外国人を優遇』という言説と実際の予算スケールには歴然とした差がある。'
)
