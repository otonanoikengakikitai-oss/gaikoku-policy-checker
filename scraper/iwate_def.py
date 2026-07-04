"""岩手県の外国人特化予算の定義 — キュレーション方式（汎用 build_pref.py 用）

第八波（東北・中国四国コンプリート）で追加。一次ソース・収録範囲は BASIS_NOTE を参照。
"""

GOVERNMENT = "岩手県"
OUT_NAME = "iwate.json"

_DOCS = {
    "POINT": {"label": "岩手県 令和8年度一般会計当初予算（案）のポイント", "url": "https://www.pref.iwate.jp/_res/projects/default_project/_page_/001/090/331/r8yosanpointo2.pdf"},
}


def _item(name, name_ev, dockey, cat, bureau, yen, ev, desc):
    return {"name": name, "name_evidence": name_ev, "doc": _DOCS[dockey]["url"], "doc_type": "pdf",
            "category": cat, "bureau": bureau, "amount_yen": yen, "amount_evidence": ev, "desc": desc}


YEARS = [
    {
        "fiscal_year": 2024,
        "fiscal_year_label": '令和6年度',
        "source": {"label": '岩手県 令和7年度一般会計当初予算（案）のポイント', "url": 'https://www.pref.iwate.jp/_res/projects/default_project/_page_/001/077/880/r7yosanpointo2.pdf'},
        "items": [],
        "empty_note": '※令和6年度は主要資料に外国人特化事業の記載（金額明記）が確認できないため事業は未収録（一般会計総額のみ収録）。',
        "general_account": {
            "amount_yen": 732200000000,
            "amount_label": '7,322億円',
            "evidence": '7,3297,32270.1',
            "label": "令和6年度 一般会計 当初予算",
            "source": {"label": '岩手県 令和7年度一般会計当初予算（案）のポイント', "url": 'https://www.pref.iwate.jp/_res/projects/default_project/_page_/001/077/880/r7yosanpointo2.pdf'},
        },
    },
    {
        "fiscal_year": 2025,
        "fiscal_year_label": "令和7年度",
        "source": _DOCS["POINT"],
        "items": [],
        "empty_note": '※令和7年度は主要資料に外国人特化事業の記載（金額明記）が確認できないため事業は未収録（一般会計総額のみ収録）。',
        "general_account": {
            "amount_yen": 732900000000,
            "amount_label": "7,329億円",
            "evidence": '7,7427,3294135.6',
            "label": "令和7年度 一般会計 当初予算",
            "source": _DOCS["POINT"],
        },
    },
    {
        "fiscal_year": 2026,
        "fiscal_year_label": "令和8年度",
        "source": _DOCS["POINT"],
        "items": [
            _item('外国人材受入支援事業費', '外国人材受入支援事業費', 'POINT', '外国人材', '商工労働観光部', 3000000, '新○外国人材受入支援事業費3百万円[商工労働観光部]',
                  '外国人材の受入支援（令和8年度新規）。資料単位は百万円（3百万円）。'),
        ],
        "general_account": {
            "amount_yen": 774200000000,
            "amount_label": "7,742億円",
            "evidence": '7,7427,3294135.6',
            "label": "令和8年度 一般会計 当初予算",
            "source": _DOCS["POINT"],
        },
    },
]

BASIS_NOTE = (
    '岩手県の外国人特化予算（財政課「当初予算のポイント」に事業名と金額が明記され、連結証跡で検証を通過した外国人特化事業）。ポイント資料ベースのため網羅ではない。一般会計総額は「7,742（R8）7,329（R7）413 5.6%」の前年併記＋増減チェックサム内蔵。令和5〜7年度は追加調査で拡張予定のため未収録。'
)
TREND_NOTE = (
    '岩手県の外国人特化予算（令和8年度・ポイント資料の確認可能分）は外国人材受入支援300万円で、県一般会計（7,742億円）比では極小。『莫大な税金で外国人を優遇』という言説と実際の予算スケールには歴然とした差がある。'
)
