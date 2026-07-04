"""山形県の外国人特化予算の定義 — キュレーション方式（汎用 build_pref.py 用）

第八波（東北・中国四国コンプリート）で追加。一次ソース・収録範囲は BASIS_NOTE を参照。
"""

GOVERNMENT = "山形県"
OUT_NAME = "yamagata.json"

_DOCS = {
    "SHUYO": {"label": "山形県 令和8年度当初予算 主要事業の概要", "url": "https://www.pref.yamagata.jp/documents/50798/r8_shuyojigyo.pdf"},
    "KEISU": {"label": "山形県 令和8年度一般会計当初予算の概要", "url": "https://www.pref.yamagata.jp/documents/50798/r8_gaiyo_keisu.pdf"},
}


def _item(name, name_ev, dockey, cat, bureau, yen, ev, desc):
    return {"name": name, "name_evidence": name_ev, "doc": _DOCS[dockey]["url"], "doc_type": "pdf",
            "category": cat, "bureau": bureau, "amount_yen": yen, "amount_evidence": ev, "desc": desc}


YEARS = [
    {
        "fiscal_year": 2023, "fiscal_year_label": "令和5年度", "source": {"label": "山形県 令和6年度一般会計当初予算の概要", "url": "https://www.pref.yamagata.jp/documents/38672/r6toushogaiyou.pdf"},
        "items": [], "empty_note": '※令和5年度は主要資料に外国人特化事業の記載（金額明記）が確認できないため事業は未収録（一般会計総額のみ収録）。',
        "general_account": {"amount_yen": 681573000000, "amount_label": "6,815億7,300万円",
            "evidence": '1予算規模649,783百万円(△31,790百万円)(△4.7%)681,573百万円', "label": "令和5年度 一般会計 当初予算", "source": {"label": "山形県 令和6年度一般会計当初予算の概要", "url": "https://www.pref.yamagata.jp/documents/38672/r6toushogaiyou.pdf"}},
    },
    {
        "fiscal_year": 2024, "fiscal_year_label": "令和6年度", "source": {"label": "山形県 令和6年度一般会計当初予算の概要", "url": "https://www.pref.yamagata.jp/documents/38672/r6toushogaiyou.pdf"},
        "items": [], "empty_note": '※令和6年度は主要資料に外国人特化事業の記載（金額明記）が確認できないため事業は未収録（一般会計総額のみ収録）。',
        "general_account": {"amount_yen": 649783000000, "amount_label": "6,497億8,300万円",
            "evidence": '1予算規模649,783百万円(△31,790百万円)(△4.7%)681,573百万円', "label": "令和6年度 一般会計 当初予算", "source": {"label": "山形県 令和6年度一般会計当初予算の概要", "url": "https://www.pref.yamagata.jp/documents/38672/r6toushogaiyou.pdf"}},
    },
    {
        "fiscal_year": 2025,
        "fiscal_year_label": "令和7年度",
        "source": _DOCS["KEISU"],
        "items": [],
        "empty_note": '※令和7年度は主要資料に外国人特化事業の記載（金額明記）が確認できないため事業は未収録（一般会計総額のみ収録）。',
        "general_account": {
            "amount_yen": 675419000000,
            "amount_label": "6,754億1,900万円",
            "evidence": '1予算規模700,284百万円(24,865百万円)(3.7%)675,419百万円',
            "label": "令和7年度 一般会計 当初予算",
            "source": _DOCS["KEISU"],
        },
    },
    {
        "fiscal_year": 2026,
        "fiscal_year_label": "令和8年度",
        "source": _DOCS["SHUYO"],
        "items": [
            _item('「外国人材採用支援デスク」の運営', '「外国人材採用支援デスク」の運営', 'SHUYO', '外国人材', 'みらい企画創造部 多文化共生・国際交流推進課', 12876000, '「外国人材採用支援デスク」の運営12,876千円',
                  '専任コーディネーターによる伴走型の外国人材採用支援・マッチング支援。'),
            _item('日本語教育コーディネーターの配置', '日本語教育コーディネーターの配置', 'SHUYO', '日本語教育', 'みらい企画創造部 多文化共生・国際交流推進課', 4615000, '日本語教育コーディネーターの配置4,615千円',
                  '総括・地域コーディネーターによる日本語教室の開催支援・オンライン日本語教室等。'),
            _item('地域の多文化共生推進の取組みに対する支援', '地域の多文化共生推進の取組みに対する支援', 'SHUYO', '多文化共生', 'みらい企画創造部 多文化共生・国際交流推進課', 2607000, '地域の多文化共生推進の取組みに対する支援2,607千円',
                  '外国人も安心して暮らせる環境整備・日本人住民との交流事業への助成。'),
            _item('日本語教室開催への助成', '日本語教室開催への助成', 'SHUYO', '日本語教育', 'みらい企画創造部 多文化共生・国際交流推進課', 1300000, '日本語教室開催への助成1,300千円',
                  '日本語教室開催等に対する経費の一部助成。'),
        ],
        "general_account": {
            "amount_yen": 700284000000,
            "amount_label": "7,002億8,400万円",
            "evidence": '1予算規模700,284百万円(24,865百万円)(3.7%)675,419百万円',
            "label": "令和8年度 一般会計 当初予算",
            "source": _DOCS["KEISU"],
        },
    },
]

BASIS_NOTE = (
    '山形県の外国人特化予算（「主要事業の概要」の「外国人材の受入拡大・定着及び多文化共生社会の推進」（44,138千円）の内訳のうち外国人特化の4項目のみ収録。同まとめ額には米国コロラド州との交流（16,127千円・国際交流一般）が含まれるため不採用＝水増し防止）。一般会計総額は前年併記＋増減チェックサム内蔵。令和5〜7年度は追加調査で拡張予定のため未収録。金額は千円単位。'
)
TREND_NOTE = (
    '山形県の外国人特化予算（令和8年度・確認可能分）は約2,100万円で、外国人材採用支援デスクと日本語教育が中心。県一般会計（7,003億円）比では約0.003%であり、『莫大な税金で外国人を優遇』という言説と実際の予算スケールには歴然とした差がある。'
)
