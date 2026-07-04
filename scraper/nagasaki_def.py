"""長崎県の外国人特化予算の定義 — キュレーション方式（汎用 build_pref.py 用）

第九波（47都道府県コンプリート）で追加。一次ソース・収録範囲は BASIS_NOTE を参照。
"""

GOVERNMENT = "長崎県"
OUT_NAME = "nagasaki.json"

_DOCS = {
    "HOSEI6": {"label": "長崎県 令和8年度6月補正予算（案）の概要（肉付け予算）", "url": "https://www.pref.nagasaki.jp/fs/2/1/9/4/5/_/__8__6_____________.pdf"},
    "GAIYO": {"label": "長崎県 令和8年度当初予算（案）の概要", "url": "https://www.pref.nagasaki.jp/fs/4/0/8/5/_/__8____________.pdf"},
}


def _item(name, name_ev, dockey, cat, bureau, yen, ev, desc):
    return {"name": name, "name_evidence": name_ev, "doc": _DOCS[dockey]["url"], "doc_type": "pdf",
            "category": cat, "bureau": bureau, "amount_yen": yen, "amount_evidence": ev, "desc": desc}


YEARS = [
    {
        "fiscal_year": 2026,
        "fiscal_year_label": "令和8年度",
        "source": _DOCS["HOSEI6"],
        "items": [
            _item('宿泊事業における外国人雇用の促進', '宿泊事業における外国人雇用の促進', 'HOSEI6', '外国人材', '観光振興部門', 27000000, '宿泊事業における外国人雇用の促進27百万円',
                  '人手不足の県内宿泊事業者への外国人雇用相談・受入環境整備支援（令和8年度は知事改選年の骨格予算のため6月補正〔肉付け〕で計上。金額は資料表記どおり百万円単位の概数）。'),
        ],
        "general_account": {
            "amount_yen": 708963230000,
            "amount_label": "7,089億6,323万円",
            "evidence": '一般会計7,089億6,323万円',
            "label": "令和8年度 一般会計 当初予算",
            "source": _DOCS["GAIYO"],
        },
    },
]

BASIS_NOTE = (
    '長崎県の外国人特化予算。令和8年度は知事改選年の骨格予算（当初概要に外国人施策の記載なし）のため、政策的事業は6月補正（肉付け予算）で計上されており、6月補正概要に明記された外国人特化事業を「肉付け計上」と明示のうえ収録。一般会計総額は当初（骨格）ベース。過年度資料はサイト改修で移設されており追加調査で拡張予定。'
)
TREND_NOTE = (
    '長崎県の外国人特化予算（令和8年度・確認可能分）は宿泊業の外国人雇用促進2,700万円（6月肉付け計上・新規）で、県一般会計（7,090億円・骨格）比では約0.004%。『莫大な税金で外国人を優遇』という言説と実際の予算スケールには歴然とした差がある。'
)
