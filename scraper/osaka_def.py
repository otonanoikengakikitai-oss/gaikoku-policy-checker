"""大阪府の外国人特化予算の定義 — キュレーション方式・多年度

一次ソースは「大阪府予算編成過程公表」システム（openf.pref.osaka.lg.jp）の事業別ページ。
各事業ページには 前年度当初・要求額・査定額（＝当初予算額）が千円単位で明記される。
build_osaka.py が毎回、4重検証:
  1. 出典（lg.jp）が生存していること
  2. 事業名（name_evidence）が当該事業ページに現存すること
  3. 当年度査定額（amount_evidence）と前年度当初（prev_evidence）が同ページに現存すること
  4. 年度間チェックサム: 当年ページの「前年度当初」＝前年度の査定額（数値照合）
を満たした事業のみ公開する。一般会計総額・人口統計も証跡文字列の現存を毎回照合する。

※日本人向け国際化事業（グローバル人材育成・高校生海外進学等）や姉妹都市交流・旅券事務は
  外国人特化ではないため含めない。
"""

GOVERNMENT = "大阪府"
BUREAU = "都市魅力創造局 国際課"

# 事業別ページURL（年度・査定区分で異なる）
def _cover(year, proc, bizcd):
    return (
        f"https://openf.pref.osaka.lg.jp/yosan/cover/index.php?year={year}&acc=1&form=01&proc={proc}&ykst=2&bizcd={bizcd}&seq=1"
    )


def _bizlist(year):
    return f"https://openf.pref.osaka.lg.jp/yosan/bizlist/index.php?year={year}&acc=1&form=01&proc=&bucd=22000&syocd=11466"


YEARS = [
    {
        "fiscal_year": 2024,
        "fiscal_year_label": "令和6年度",
        "source": {"label": "大阪府 予算編成過程公表（令和6年度・都市魅力創造局国際課）", "url": _bizlist(2024)},
        "items": [
            {
                "name": "外国人受入環境整備事業費",
                "name_evidence": "外国人受入環境整備事業費",
                "url": _cover(2024, 6, 20190141),
                "category": "外国人相談",
                "amount_yen": 20324000,
                "amount_evidence": "20,324",
                "prev_yen": 22179000,
                "prev_evidence": "22,179",
                "desc": "外国人が生活・就労等の情報に速やかに到達できるよう、一元的相談窓口の運営等を実施（国の総合的対応策を踏まえた受入環境整備・国庫補助あり）。",
            },
            {
                "name": "外国人留学生就職支援事業費",
                "name_evidence": "外国人留学生就職支援事業費",
                "url": _cover(2024, 6, 20180482),
                "category": "外国人材",
                "amount_yen": 2178000,
                "amount_evidence": "2,178",
                "prev_yen": 2186000,
                "prev_evidence": "2,186",
                "desc": "大学・経済団体と連携し、外国人留学生の日本での就職活動を支援。",
            },
        ],
        "general_account": {
            "amount_yen": 3197200000000,
            "amount_label": "3兆1,972億円",
            # 資料1の予算規模表「一 般 会 計 36,421 31,972」（前年→当年の連結・億円）
            "amount_evidence": "一般会計36,42131,972",
            "label": "令和6年度 一般会計 当初予算",
            "source": {"label": "大阪府 令和6年度当初予算(案)について（資料1）", "url": "https://www.pref.osaka.lg.jp/documents/62990/shiryou1.pdf"},
        },
        "population": {
            "foreign": 333564,
            "total": 8769534,
            "as_of": "令和6年末（2024年12月末）現在",
            "total_as_of": "令和7年1月1日現在",
            "metric_label": "在留外国人数",
            "foreign_evidence": "大阪府333,564人",
            "total_evidence": "人口総数8,769,534人",
            "basis": "在留外国人数は出入国在留管理庁の在留外国人統計（都道府県別・年末）、総人口は大阪府毎月推計人口。国・東京都・川口とは統計の種類・基準日が異なる。",
            "source": {"label": "出入国在留管理庁 令和6年末現在における在留外国人数について", "url": "https://www.moj.go.jp/isa/publications/press/13_00052.html"},
            "total_source": {"label": "大阪府 毎月推計人口（令和7年1月1日現在）", "url": "https://www.pref.osaka.lg.jp/documents/12055/jk20250101.pdf"},
        },
    },
    {
        "fiscal_year": 2025,
        "fiscal_year_label": "令和7年度",
        "source": {"label": "大阪府 予算編成過程公表（令和7年度・都市魅力創造局国際課）", "url": _bizlist(2025)},
        "items": [
            {
                "name": "外国人受入環境整備事業費",
                "name_evidence": "外国人受入環境整備事業費",
                "url": _cover(2025, 0, 20190141),
                "category": "外国人相談",
                "amount_yen": 20000000,
                "amount_evidence": "20,000",
                "prev_yen": 20324000,
                "prev_evidence": "20,324",
                "desc": "外国人が生活・就労等の情報に速やかに到達できるよう、一元的相談窓口の運営等を実施（国の総合的対応策を踏まえた受入環境整備・国庫補助あり）。",
            },
            {
                "name": "外国人相談対応力強化事業費",
                "name_evidence": "外国人相談対応力強化事業費",
                "url": _cover(2025, 6, 20250053),
                "category": "外国人相談",
                "amount_yen": 17908000,
                "amount_evidence": "17,908",
                "prev_yen": 0,
                "prev_evidence": "0",
                "desc": "外国人支援専門員の育成・受入側の相談対応力向上の研修等（令和7年度新規・宿泊税を一部財源）。訪日外国人対応と在住外国人対応の双方を含み、公表資料では内訳は切り分けられていない。",
            },
            {
                "name": "外国人留学生就職支援事業費",
                "name_evidence": "外国人留学生就職支援事業費",
                "url": _cover(2025, 0, 20180482),
                "category": "外国人材",
                "amount_yen": 2177000,
                "amount_evidence": "2,177",
                "prev_yen": 2178000,
                "prev_evidence": "2,178",
                "desc": "大学・経済団体と連携し、外国人留学生の日本での就職活動を支援。",
            },
        ],
        "general_account": {
            "amount_yen": 3271400000000,
            "amount_label": "3兆2,714億円",
            # 資料1の予算規模表「一 般 会 計 31,972 32,714 742」（前年→当年→増減の連結＝チェックサム内蔵）
            "amount_evidence": "一般会計31,97232,714742",
            "label": "令和7年度 一般会計 当初予算",
            "source": {"label": "大阪府 令和7年度当初予算(案)について（資料1）", "url": "https://www.pref.osaka.lg.jp/documents/102542/shiryou1_teiseigo2.pdf"},
        },
        "population": {
            "foreign": 375319,
            "total": 8773375,
            "as_of": "令和7年末（2025年12月末）現在",
            "total_as_of": "令和8年1月1日現在",
            "metric_label": "在留外国人数",
            "foreign_evidence": "大阪府375,319人",
            "total_evidence": "人口総数8,773,375人",
            "basis": "在留外国人数は出入国在留管理庁の在留外国人統計（都道府県別・年末）、総人口は大阪府毎月推計人口。国・東京都・川口とは統計の種類・基準日が異なる。",
            "source": {"label": "出入国在留管理庁 令和7年末現在における在留外国人数について", "url": "https://www.moj.go.jp/isa/publications/press/13_00062.html"},
            "total_source": {"label": "大阪府 毎月推計人口（令和8年1月1日現在）", "url": "https://www.pref.osaka.lg.jp/documents/12055/jk20260101.pdf"},
        },
    },
    {
        "fiscal_year": 2026,
        "fiscal_year_label": "令和8年度",
        "source": {"label": "大阪府 予算編成過程公表（令和8年度・都市魅力創造局国際課）", "url": _bizlist(2026)},
        "items": [
            {
                "name": "外国人受入環境整備事業費",
                "name_evidence": "外国人受入環境整備事業費",
                "url": _cover(2026, 0, 20190141),
                "category": "外国人相談",
                "amount_yen": 20000000,
                "amount_evidence": "20,000",
                "prev_yen": 20000000,
                "prev_evidence": "20,000",
                "desc": "外国人が生活・就労等の情報に速やかに到達できるよう、一元的相談窓口の運営等を実施（国の総合的対応策を踏まえた受入環境整備・国庫補助あり）。",
            },
            {
                "name": "外国人相談対応力強化事業費",
                "name_evidence": "外国人相談対応力強化事業費",
                "url": _cover(2026, 6, 20250053),
                "category": "外国人相談",
                "amount_yen": 17823000,
                "amount_evidence": "17,823",
                "prev_yen": 17908000,
                "prev_evidence": "17,908",
                "desc": "外国人支援専門員の育成・受入側の相談対応力向上の研修等（宿泊税を一部財源）。訪日外国人対応と在住外国人対応の双方を含み、公表資料では内訳は切り分けられていない。",
            },
            {
                "name": "外国人留学生就職支援事業費",
                "name_evidence": "外国人留学生就職支援事業費",
                "url": _cover(2026, 0, 20180482),
                "category": "外国人材",
                "amount_yen": 2177000,
                "amount_evidence": "2,177",
                "prev_yen": 2177000,
                "prev_evidence": "2,177",
                "desc": "大学・経済団体と連携し、外国人留学生の日本での就職活動を支援。",
            },
        ],
        "general_account": {
            "amount_yen": 3921600000000,
            "amount_label": "3兆9,216億円",
            # 令和8年度当初予算案（概要）の対比表「3兆2,714億円 → 3兆9,216億円」の連結
            "amount_evidence": "3兆2,714億円3兆9,216億円",
            "label": "令和8年度 一般会計 当初予算",
            "source": {"label": "大阪府 令和8年度当初予算案（概要）", "url": "https://www.pref.osaka.lg.jp/documents/126017/080218.pdf"},
        },
        "population": {
            "foreign": 375319,
            "total": 8773375,
            "as_of": "令和7年末（2025年12月末）現在（令和8年の確報は未公表のため取得可能な最新実績）",
            "total_as_of": "令和8年1月1日現在",
            "metric_label": "在留外国人数",
            "foreign_evidence": "大阪府375,319人",
            "total_evidence": "人口総数8,773,375人",
            "basis": "在留外国人数は出入国在留管理庁の在留外国人統計（都道府県別・年末）、総人口は大阪府毎月推計人口。国・東京都・川口とは統計の種類・基準日が異なる。",
            "source": {"label": "出入国在留管理庁 令和7年末現在における在留外国人数について", "url": "https://www.moj.go.jp/isa/publications/press/13_00062.html"},
            "total_source": {"label": "大阪府 毎月推計人口（令和8年1月1日現在）", "url": "https://www.pref.osaka.lg.jp/documents/12055/jk20260101.pdf"},
        },
    },
]

BASIS_NOTE = (
    "大阪府の外国人特化予算（都市魅力創造局国際課の外国人特化3事業＝外国人受入環境整備・外国人相談対応力強化・"
    "外国人留学生就職支援の当初予算額〔査定額〕。款・項・目は総務費・府民文化費・国際交流費）。"
    "日本人向け国際化事業（グローバル人材育成・高校生海外進学等）や姉妹都市交流・旅券事務は含まない。"
    "外国人相談対応力強化事業費は訪日外国人対応分を含む（公表資料で在住外国人分と切り分け不能）。金額は千円単位の予算編成過程公表ベース。"
)
TREND_NOTE = (
    "大阪府の在留外国人数は令和7年末で375,319人と全国有数だが、府の外国人特化予算は年2,000万〜4,000万円規模で、"
    "府一般会計（3兆円台）の約0.001%に過ぎない。内容も一元的相談窓口・相談対応力研修・留学生就職支援といった"
    "情報・体制整備が中心であり、『莫大な税金で外国人を優遇』という言説と行政予算の実スケールには歴然とした差がある。"
)
