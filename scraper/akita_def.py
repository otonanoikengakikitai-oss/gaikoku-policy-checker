"""秋田県の外国人特化予算の定義 — キュレーション方式（汎用 build_pref.py 用）

第八波（東北・中国四国コンプリート）で追加。一次ソース・収録範囲は BASIS_NOTE を参照。
"""

GOVERNMENT = "秋田県"
OUT_NAME = "akita.json"

_DOCS = {
    "GAIYO": {"label": "秋田県 令和8年度当初予算（案）概要", "url": "https://www.pref.akita.lg.jp/uploads/public/archive_0000093875_00/%E4%BB%A4%E5%92%8C%EF%BC%98%E5%B9%B4%E5%BA%A6%E5%BD%93%E5%88%9D%E4%BA%88%E7%AE%97(%E6%A1%88)%E6%A6%82%E8%A6%81.pdf"},
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
            _item('外国人材受入サポートセンター事業', '外国人材受入サポートセンター事業', 'GAIYO', '外国人材', '産業労働部', 23661000, '(16)外国人材受入サポートセンター事業23,661',
                  '外国人材受入サポートセンターの運営（9,439千円）・外国人材受入加速化（10,000千円）等（拡充）。'),
            _item('多文化共生推進事業', '多文化共生推進事業', 'GAIYO', '多文化共生', '観光文化スポーツ部', 17497000, '(1)多文化共生推進事業17,497',
                  '外国人支援ネットワーク構築（5,042千円）・あきた多文化共生支援（6,264千円）等。'),
        ],
        "general_account": {
            "amount_yen": 604100000000,
            "amount_label": "6,041億円",
            "evidence": '○一般会計予算額は6,041億円',
            "label": "令和8年度 一般会計 当初予算",
            "source": _DOCS["GAIYO"],
        },
    },
]

BASIS_NOTE = (
    '秋田県の外国人特化予算（「当初予算（案）概要」に事業名と金額が明記され、連結証跡で検証を通過した外国人特化事業2件）。一般会計総額の対前年比は令和7年度の肉付け後予算比（知事改選年）。令和5〜7年度は追加調査で拡張予定のため未収録。金額は千円単位。'
)
TREND_NOTE = (
    '秋田県の外国人特化予算（令和8年度・確認可能分）は約4,100万円で、外国人材受入サポートセンター（拡充）と多文化共生推進が二本柱。県一般会計（6,041億円）の約0.007%であり、『莫大な税金で外国人を優遇』という言説と実際の予算スケールには歴然とした差がある。'
)
