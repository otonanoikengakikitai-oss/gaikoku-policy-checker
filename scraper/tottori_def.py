"""鳥取県の外国人特化予算の定義 — キュレーション方式（汎用 build_pref.py 用）

第八波（東北・中国四国コンプリート）で追加。一次ソース・収録範囲は BASIS_NOTE を参照。
"""

GOVERNMENT = "鳥取県"
OUT_NAME = "tottori.json"

_DOCS = {
    "SHUYO": {"label": "鳥取県 令和8年度当初予算案 主要事業一覧", "url": "https://www.pref.tottori.lg.jp/secure/1417694/R8tousyosyuyouzigyou.pdf"},
    "BUNSEKI": {"label": "鳥取県 令和8年度当初予算案の概要・分析", "url": "https://www.pref.tottori.lg.jp/secure/1417694/R8tousyogaiyoubunseki.pdf"},
}


def _item(name, name_ev, dockey, cat, bureau, yen, ev, desc):
    return {"name": name, "name_evidence": name_ev, "doc": _DOCS[dockey]["url"], "doc_type": "pdf",
            "category": cat, "bureau": bureau, "amount_yen": yen, "amount_evidence": ev, "desc": desc}


YEARS = [
    {
        "fiscal_year": 2023,
        "fiscal_year_label": '令和5年度',
        "source": {"label": '鳥取県 令和5年度当初予算案の概要', "url": 'https://www.pref.tottori.lg.jp/secure/1313232/01-3_R5toushoyosanangaiyou.pdf'},
        "items": [],
        "empty_note": '※令和5年度は主要資料に外国人特化事業の記載（金額明記）が確認できないため事業は未収録（一般会計総額のみ収録）。なお令和6年度は一般会計総額の機械可読なテキスト証跡を公開資料から特定できなかったため未収録（画像確認要）。',
        "general_account": {
            "amount_yen": 335026692000,
            "amount_label": '3,350億2,669万2千円',
            "evidence": '合計335,026,692100.0364,005,675100.0△28,978,98392.0',
            "label": "令和5年度 一般会計 当初予算",
            "source": {"label": '鳥取県 令和5年度当初予算案の概要', "url": 'https://www.pref.tottori.lg.jp/secure/1313232/01-3_R5toushoyosanangaiyou.pdf'},
        },
    },
    {
        "fiscal_year": 2025,
        "fiscal_year_label": "令和7年度",
        "source": _DOCS["BUNSEKI"],
        "items": [],
        "empty_note": '※令和7年度は主要資料に外国人特化事業の記載（金額明記）が確認できないため事業は未収録（一般会計総額のみ収録）。',
        "general_account": {
            "amount_yen": 365000000000,
            "amount_label": "3,650億円",
            "evidence": '予算規模:3,961億円(前年度当初予算:3,650億円、+310億円、+8.5%)',
            "label": "令和7年度 一般会計 当初予算",
            "source": _DOCS["BUNSEKI"],
        },
    },
    {
        "fiscal_year": 2026,
        "fiscal_year_label": "令和8年度",
        "source": _DOCS["SHUYO"],
        "items": [
            _item('介護分野で働く外国人材受入・定着促進事業', '介護分野で働く外国人材受', 'SHUYO', '外国人材', '福祉保健部 長寿社会課', 47518000, '外国人介護人材の参入促進及び定着を図る47,518',
                  '介護事業所における外国人介護人材の就労支援・受入環境整備（拡充）。'),
            _item('ともにくらす多文化共生推進事業', 'ともにくらす多文化共生推進', 'SHUYO', '多文化共生', '輝く鳥取創造本部 交流推進課', 44531000, '災害時における多言語支援体制44,531',
                  '多文化共生の新たな指針の策定・災害時多言語支援体制の構築・情報発信強化（拡充）。'),
            _item('外国人材と共に働くとっとり推進事業', '外国人材と共に働くとっと', 'SHUYO', '外国人材', '商工労働部 雇用・働き方政策課', 12400000, '環境づくりを推進するため、12,400',
                  '外国人材受入支援セミナーの開催・新規雇用企業への支援（拡充）。'),
        ],
        "general_account": {
            "amount_yen": 396100000000,
            "amount_label": "3,961億円",
            "evidence": '予算規模:3,961億円(前年度当初予算:3,650億円、+310億円、+8.5%)',
            "label": "令和8年度 一般会計 当初予算",
            "source": _DOCS["BUNSEKI"],
        },
    },
]

BASIS_NOTE = (
    '鳥取県の外国人特化予算（「主要事業一覧」に事業名・部局・金額が明記され、連結証跡で検証を通過した外国人特化事業3件）。介護職の魅力発信等を含む全対象の人材確保事業は混合のため未収録（水増し防止）。観光インバウンドは含まない。一般会計総額は前年併記＋増減チェックサム内蔵。令和5〜7年度は追加調査で拡張予定のため未収録。金額は千円単位。'
)
TREND_NOTE = (
    '鳥取県の外国人特化予算（令和8年度・確認可能分）は約1億円で、介護外国人材（4,752万円）と多文化共生推進（4,453万円・災害時多言語支援）が中心。県一般会計（3,961億円）の約0.026%であり、『莫大な税金で外国人を優遇』という言説と実際の予算スケールには歴然とした差がある。'
)
