"""佐賀県の外国人特化予算の定義 — キュレーション方式（汎用 build_pref.py 用）

第九波（47都道府県コンプリート）で追加。一次ソース・収録範囲は BASIS_NOTE を参照。
"""

GOVERNMENT = "佐賀県"
OUT_NAME = "saga.json"

_DOCS = {
    "SHUYO": {"label": "佐賀県 令和7年度（当初予算）主要事項一覧", "url": "https://www.pref.saga.lg.jp/kiji003111639/3_111639_342714_up_epgdoys2.pdf"},
    "GAIYO7": {"label": "佐賀県 令和7年度当初予算案の概要", "url": "https://www.pref.saga.lg.jp/kiji003111639/3_111639_343157_up_beha22ms.pdf"},
    "GAIYO8": {"label": "佐賀県 令和8年度当初予算案の概要", "url": "https://www.pref.saga.lg.jp/kiji003117971/3_117971_379678_up_ywjgjpd3.pdf"},
}


def _item(name, name_ev, dockey, cat, bureau, yen, ev, desc):
    return {"name": name, "name_evidence": name_ev, "doc": _DOCS[dockey]["url"], "doc_type": "pdf",
            "category": cat, "bureau": bureau, "amount_yen": yen, "amount_evidence": ev, "desc": desc}


YEARS = [
    {
        "fiscal_year": 2024,
        "fiscal_year_label": '令和6年度',
        "source": {"label": '佐賀県 令和6年度当初予算案の概要', "url": 'https://www.pref.saga.lg.jp/kiji003101039/3_101039_307124_up_vaiqwdhd.pdf'},
        "items": [],
        "empty_note": '※令和6年度は主要資料に外国人特化事業の記載（金額明記）が確認できないため事業は未収録（一般会計総額のみ収録）。',
        "general_account": {
            "amount_yen": 520556000000,
            "amount_label": '5,205億5,600万円',
            "evidence": '一般会計:5,205億56百万円(対前年度当初比159億88百万円減)',
            "label": "令和6年度 一般会計 当初予算",
            "source": {"label": '佐賀県 令和6年度当初予算案の概要', "url": 'https://www.pref.saga.lg.jp/kiji003101039/3_101039_307124_up_vaiqwdhd.pdf'},
        },
    },
    {
        "fiscal_year": 2026,
        "fiscal_year_label": "令和8年度",
        "source": _DOCS["GAIYO8"],
        "items": [],
        "empty_note": '※令和8年度は主要事項一覧・概要に外国人特化事業の金額記載が確認できないため事業は未収録（一般会計総額のみ収録）。',
        "general_account": {
            "amount_yen": 547066000000,
            "amount_label": "5,470億6,600万円",
            "evidence": '一般会計:5,470億66百万円(対前年度当初比340億45百万円増)',
            "label": "令和8年度 一般会計 当初予算",
            "source": _DOCS["GAIYO8"],
        },
    },
    {
        "fiscal_year": 2025,
        "fiscal_year_label": "令和7年度",
        "source": _DOCS["SHUYO"],
        "items": [
            _item('佐賀県外国人材雇用サポート事業費', '佐賀県外国人材雇用サポート事業費', 'SHUYO', '外国人材', '産業労働部 産業人材課', 16595000, '佐賀県外国人材雇用サポート事業費一般財源16,595',
                  '県内企業と外国人からの雇用相談にワンストップで対応する外国人雇用相談窓口の設置・運営（佐賀商工ビル・令和7年度新規）。'),
        ],
        "general_account": {
            "amount_yen": 513021000000,
            "amount_label": "5,130億2,100万円",
            "evidence": '一般会計:5,130億21百万円(対前年度当初比75億35百万円減)',
            "label": "令和7年度 一般会計 当初予算",
            "source": _DOCS["GAIYO7"],
        },
    },
]

# 事業データの無い年度の一般会計総額（証跡照合のうえ参考収録）
GA_HISTORY = [
    {"fiscal_year": 2026, "fiscal_year_label": '令和8年度', "amount_yen": 547066000000,
     "amount_label": '5,470億6,600万円', "evidence": '一般会計:5,470億66百万円(対前年度当初比340億45百万円増)', "source": _DOCS['GAIYO8'],
     "note": '令和8年度の主要事項一覧には外国人特化事業の金額記載がないため事業は未収録（一般会計総額のみ）。'},
]

BASIS_NOTE = (
    '佐賀県の外国人特化予算（「主要事項一覧」に事業名と金額が明記され、連結証跡で検証を通過した外国人特化事業）。令和8年度の主要事項一覧・概要には外国人特化事業の金額記載がなく未収録（一般会計総額のみ参考収録）＝掲載がないこと自体が「莫大な優遇」言説への反証となる。金額は千円単位。'
)
TREND_NOTE = (
    '佐賀県の外国人特化予算（主要事項ベース・確認可能分）は令和7年度の外国人材雇用サポート事業1,660万円（新規・ワンストップ相談窓口）で、県一般会計（5,130億円）の約0.003%。令和8年度は主要資料への金額掲載自体がなく、『莫大な税金で外国人を優遇』という言説と実際の予算スケールには歴然とした差がある。'
)
