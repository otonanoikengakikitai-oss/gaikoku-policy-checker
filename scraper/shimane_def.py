"""島根県の外国人特化予算の定義 — キュレーション方式（汎用 build_pref.py 用）

第八波（東北・中国四国コンプリート）で追加。一次ソース・収録範囲は BASIS_NOTE を参照。
"""

GOVERNMENT = "島根県"
OUT_NAME = "shimane.json"

_DOCS = {
    "SESAKU": {"label": "島根県 令和8年度当初予算等 施策集", "url": "https://www.pref.shimane.lg.jp/admin/seisaku/zaisei/yosan/yosanr8/r8gaiyou.data/zenpage_sesakushur8.pdf"},
    "GAIYO": {"label": "島根県 令和8年度当初予算の概要", "url": "https://www.pref.shimane.lg.jp/admin/seisaku/zaisei/yosan/yosanr8/r8gaiyou.data/02r8yosanangaiyou.pdf"},
}


def _item(name, name_ev, dockey, cat, bureau, yen, ev, desc):
    return {"name": name, "name_evidence": name_ev, "doc": _DOCS[dockey]["url"], "doc_type": "pdf",
            "category": cat, "bureau": bureau, "amount_yen": yen, "amount_evidence": ev, "desc": desc}


YEARS = [
    {
        "fiscal_year": 2024, "fiscal_year_label": "令和6年度", "source": {"label": "島根県 令和7年度当初予算の概要", "url": "https://www.pref.shimane.lg.jp/admin/seisaku/zaisei/yosan/yosanr7/r7gaiyou.data/r7yosanangaiyou.pdf"},
        "items": [], "empty_note": '※令和6年度は主要資料に外国人特化事業の記載（金額明記）が確認できないため事業は未収録（一般会計総額のみ収録）。',
        "general_account": {"amount_yen": 461700000000, "amount_label": "4,617億円",
            "evidence": '当初予算A4,7204,617103+2.2%', "label": "令和6年度 一般会計 当初予算", "source": {"label": "島根県 令和7年度当初予算の概要", "url": "https://www.pref.shimane.lg.jp/admin/seisaku/zaisei/yosan/yosanr7/r7gaiyou.data/r7yosanangaiyou.pdf"}},
    },
    {
        "fiscal_year": 2025,
        "fiscal_year_label": "令和7年度",
        "source": _DOCS["GAIYO"],
        "items": [],
        "empty_note": '※令和7年度は主要資料に外国人特化事業の記載（金額明記）が確認できないため事業は未収録（一般会計総額のみ収録）。',
        "general_account": {
            "amount_yen": 472000000000,
            "amount_label": "4,720億円",
            "evidence": '当初予算A4,9244,720204',
            "label": "令和7年度 一般会計 当初予算",
            "source": _DOCS["GAIYO"],
        },
    },
    {
        "fiscal_year": 2026,
        "fiscal_year_label": "令和8年度",
        "source": _DOCS["SESAKU"],
        "items": [
            _item('外国人の受入れ・共生事業', '外国人の受入れ・', 'SESAKU', '多文化共生', '環境生活部 文化国際課', 378089000, '外国人の受入れ・378,089',
                  '外国人住民が安心して暮らせる生活環境づくり・日本人住民との相互理解の促進等（拡充）。'),
            _item('帰国・外国人児童生徒等教育の推進', '帰国・外国人児童', 'SESAKU', '日本語教育', '教育委員会 学校企画課', 247417000, '帰国・外国人児童247,417',
                  '日本語指導が必要な児童生徒等への支援。'),
        ],
        "general_account": {
            "amount_yen": 492400000000,
            "amount_label": "4,924億円",
            "evidence": '当初予算A4,9244,720204',
            "label": "令和8年度 一般会計 当初予算",
            "source": _DOCS["GAIYO"],
        },
    },
]

BASIS_NOTE = (
    '島根県の外国人特化予算（「施策集」に事業名と金額が明記され、連結証跡で検証を通過した外国人特化事業2件）。観光インバウンドは含まない。一般会計総額は「4,924（R8）4,720（R7）204（増減）」の前年併記＋増減チェックサム内蔵。令和5〜7年度は追加調査で拡張予定のため未収録。金額は千円単位。'
)
TREND_NOTE = (
    '島根県の外国人特化予算（令和8年度・確認可能分）は約6.3億円と人口比では全国的に高水準（外国人の受入れ・共生3.8億円、帰国・外国人児童生徒教育2.5億円）で、人口減少県の外国人受入戦略を反映している。それでも県一般会計（4,924億円）の約0.13%であり、『莫大な税金で外国人を優遇』という言説とはなお2桁の開きがある。'
)
