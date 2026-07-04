"""高知県の外国人特化予算の定義 — キュレーション方式（汎用 build_pref.py 用）

第八波（東北・中国四国コンプリート）で追加。一次ソース・収録範囲は BASIS_NOTE を参照。
"""

GOVERNMENT = "高知県"
OUT_NAME = "kochi.json"

_DOCS = {
    "GAIYO": {"label": "高知県 令和8年度一般会計当初予算の概要", "url": "https://www.pref.kochi.lg.jp/doc/2026031700182/file_contents/file_20263253104423_1.pdf"},
}


def _item(name, name_ev, dockey, cat, bureau, yen, ev, desc):
    return {"name": name, "name_evidence": name_ev, "doc": _DOCS[dockey]["url"], "doc_type": "pdf",
            "category": cat, "bureau": bureau, "amount_yen": yen, "amount_evidence": ev, "desc": desc}


YEARS = [
    {
        "fiscal_year": 2026,
        "fiscal_year_label": "令和8年度",
        "source": _DOCS["GAIYO"],
        "items": [
            _item('外国人材の受入促進（外国人受入環境整備事業費）', '外国人材の受入促進', 'GAIYO', '外国人材', '商工政策課', 112000000, '●拡外国人材の受入促進112百万円[商工政策課]',
                  '外国人材の受入れを行う事業者への支援強化等（拡充）。資料単位は百万円（112百万円）。'),
            _item('多文化共生社会の推進', '多文化共生社会の推進', 'GAIYO', '多文化共生', '国際交流課', 34000000, '●拡多文化共生社会の推進34百万円[国際交流課]',
                  '多文化共生の推進（地域の交流拠点づくり等・拡充）。資料単位は百万円（34百万円）。'),
        ],
        "general_account": {
            "amount_yen": 507100000000,
            "amount_label": "5,071億円",
            "evidence": '5,071',
            "label": "令和8年度 一般会計 当初予算",
            "source": _DOCS["GAIYO"],
        },
    },
]

BASIS_NOTE = (
    '高知県の外国人特化予算（「一般会計当初予算の概要」に事業名と金額が明記され、連結証跡で検証を通過した外国人特化事業2件）。一般会計総額5,071億円は同資料の「一般会計当初予算額」（対前年度比+330億円、+7.0%＝前年4,741億円との加算チェックサム整合）。令和5〜7年度は追加調査で拡張予定のため未収録。金額は資料表記どおり百万円単位。'
)
TREND_NOTE = (
    '高知県の外国人特化予算（令和8年度・確認可能分）は約1.5億円で、外国人材の受入促進（1.12億円・拡充）が中心。県一般会計（5,071億円）の約0.029%であり、『莫大な税金で外国人を優遇』という言説と実際の予算スケールには歴然とした差がある。'
)
