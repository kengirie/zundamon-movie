"""ずんだもんテックニュース 2026年11月7日（土）

情報源: Hacker News トップページ / はてなブックマーク テクノロジー人気エントリー（2026-11-07 取得）

色分け: y=黄（用語・固有名詞） c=水色（数字・データ） p=ピンク（強調） g=緑（よい知らせ） r=赤（悪い知らせ） m=グレー（補足）
"""
from zmovie.items import T, Card, Counter

OUTPUT_NAME = "tech_news_20261107"
TACHIE_CREDIT = "立ち絵：坂本アヒル"
THEME = dict(
    style="news",
    program="ずんだもん テックニュース",
    date="2026年11月7日（土）",
    date_short="11/7（土）",
    ticker="Hacker News・はてなブックマークで話題の技術ニュース　◆　libghostty 1.0 公開　◆　"
           "GitHub が Git 保存基盤を刷新　◆　OpenSSH に認証回避の脆弱性　◆　"
           "ISUCON2026 で AI が無人優勝　◆　テスラ、サイバートラック生産終了へ　◆　",
)

READINGS = {
    "libghostty": "リブゴーストティー",
    "Ghostty": "ゴーストティー",
    "JetBrains": "ジェットブレインズ",
    "IDE": "アイディーイー",
    "Neovim": "ネオヴィム",
    "GitHub": "ぎっとはぶ",   # カタカナだと「ギッ／トハブ」と切れる
    "Git": "ぎっと",
    "OpenSSH": "オープンエスエスエイチ",
    "10.6p2": "じゅってんろくぴーつー",
    "Alpine Linux": "アルパインリナックス",
    "musl": "マッスル",
    "ISUCON": "アイスコン",
    "Claude Code": "クロードコード",
    "SSH": "エスエスエイチ",
}

SCENES = [
    # 0. オープニング
    dict(
        name="opening", chip=None, title=None, enter=True, jingle=True,
        parts=[
            ("おはようございます。ずんだもんテックニュースなのだ。", [
                Card(["[y]ずんだもん[/]", "テックニュース"], y=300, h=300, size=96, border="y",
                     anim="pop", se=None),
                T("2026年11月7日（土）", y=630, size=52, color="m", se=None),
            ]),
            ("今日のひとこと。", [
                T("[p]今日のひとこと[/]", y=760, size=56, anim="pop", se="pon"),
            ]),
            ("道具がどんどん、AIエージェント向けに作り直されているのだ。", [
                T("道具がどんどん\n[y]AIエージェント[/]向けに", y=860, size=60),
            ]),
        ],
    ),
    # 1. libghostty
    dict(
        name="ghostty", news_no=1, category="開発", cat_color="y",
        headline="ターミナルの心臓部\n「[y]libghostty[/]」が1.0に",
        source="出典：mitchellh.com\n[y]HN 888pt[/]・はてブで話題",
        parts=[
            ("まずは開発。", []),
            ("人気ターミナルGhosttyの中身を切り出した「libghostty」が、1.0になったのだ。", [
                T("[y]libghostty[/] 1.0", y=470, size=88, bold=True, anim="pop", se="pon"),
                T("[m]アプリに組み込める\nターミナルの部品（Cライブラリ）[/]", y=600, size=44),
            ]),
            ("JetBrainsのIDEやNeovimも採用。", [
                Card(["採用：[y]JetBrains[/]のIDE", "　　　[y]Neovim[/]・KDE など"], y=760, h=170, size=50),
            ]),
            ("4コアのサーバーでターミナル1万個が動く軽さなのだ。", [
                Counter(10000, prefix="", suffix="個", y=960, size=96, color="c", comma=True,
                        se="pon"),
            ]),
        ],
    ),
    # 2. GitHub
    dict(
        name="github", news_no=2, category="インフラ", cat_color="c",
        headline="[y]GitHub[/]、AIエージェント時代の\nGit保存基盤を新設計",
        source="出典：GitHub Blog\n[y]HN 193pt[/]・はてブで話題",
        parts=[
            ("続いてインフラ。", []),
            ("GitHubが、Gitのデータ保存の仕組みを作り直したのだ。", [
                T("コードの保存場所を\n[p]丸ごと作り直し[/]", y=470, size=64),
            ]),
            ("AIエージェントが一斉に書き込む時代への備えで、", [
                T("[y]AIエージェント[/]が一斉に書き込む時代へ", y=650, size=46),
            ]),
            ("社内テストでは5000体が毎秒7200回プッシュしても、さばけたそうなのだ。", [
                Card(["[c]5,000[/]体のエージェントが", "毎秒[c]7,200[/]回プッシュ"], y=760, h=200, size=60,
                     anim="pop", se="pon"),
                T("[m]一般提供は来年はじめの予定[/]", y=990, size=40),
            ]),
        ],
    ),
    # 3. OpenSSH（悪い知らせ）
    dict(
        name="openssh", news_no=3, category="セキュリティ", cat_color="r",
        headline="[y]OpenSSH[/]に認証回避の\n脆弱性「[r]*sshole[/]」",
        source="出典：piyolog ほか\n[y]はてブ[/]で話題",
        parts=[
            ("次はセキュリティ。", []),
            ("OpenSSHに、長いパスワードを送るだけで", [
                T("[c]257[/]バイト超のパスワードで", y=470, size=58),
            ]),
            ("ログインできてしまう脆弱性が見つかったのだ。", [
                T("[r]ログイン素通り[/]", y=560, size=100, bold=True, anim="pop", se="boo"),
            ]),
            ("影響はAlpine Linuxなど、muslを使う環境。", [
                Card(["影響：[y]Alpine Linux[/] など", "[y]musl[/] を使う環境", "[m]musl＝小さなC標準ライブラリ[/]"],
                     y=730, h=240, size=46),
            ]),
            ("10.6p2で修正済み。すぐ更新するのだ！", [
                T("対策：[g]10.6p2 に更新[/]", y=1000, size=62, anim="pop", se="pon"),
            ]),
        ],
    ),
    # 4. ISUCON（よい知らせ）
    dict(
        name="isucon", news_no=4, category="AI", cat_color="p",
        headline="[y]ISUCON[/]2026、\nAIエージェントが無人で優勝",
        source="出典：laiso（sizu.me）\n[y]はてブ 89[/]",
        parts=[
            ("AIの話題。", []),
            ("サーバーを速くする競技ISUCONで、", [
                T("[y]ISUCON[/]", y=470, size=88, bold=True),
                T("[m]Webサービスを制限時間内に速くする競技[/]", y=600, size=40),
            ]),
            ("Claude Codeを使ったチームが、人の手を借りず約8時間動き続けて、", [
                T("約[c]8[/]時間 [p]人の介入なし[/]", y=700, size=62),
            ]),
            ("優勝したそうなのだ。", [
                T("[g]優勝[/]", y=800, size=120, bold=True, anim="pop", se="kiran", jump=True),
            ]),
            ("決め手は、3か月かけた事前の準備なのだ。", [
                T("決め手は[c]3[/]か月の下準備", y=990, size=56),
            ]),
        ],
    ),
    # 5. テスラ（悪い知らせ）
    dict(
        name="tesla", news_no=5, category="テック業界", cat_color="g",
        headline="テスラ、[y]サイバートラック[/]の\n生産を終了へ",
        source="出典：NBC News\n[y]HN 1101pt[/]・コメント1961件",
        parts=[
            ("最後は、ハッカーニュースで一番の反響。", []),
            ("テスラが、サイバートラックの生産を2027年半ばにやめると発表したのだ。", [
                T("[c]2027[/]年半ばに[r]生産終了[/]", y=470, size=66),
            ]),
            ("去年の米国での販売は約2万台で、", [
                T("2025年 米国販売 [c]20,237[/]台", y=600, size=54),
            ]),
            ("前の年より48%減。", [
                Counter(48, prefix="前年比 ", suffix="%減", y=690, size=100, color="r", se="boo"),
            ]),
            ("発売前の予想、年間25万台には遠く及ばなかったのだ。", [
                Card(["発売前の予想は [c]年25万台[/]…"], y=900, h=140, size=56),
            ]),
        ],
    ),
    # 6. エンディング
    dict(
        name="ending", chip=None, title="今日のニュース",
        parts=[
            ("以上、今日のテックニュースでした。", [
                T("1 [y]libghostty[/] 1.0", y=290, size=50, align="left", x=110),
                T("2 [y]GitHub[/] 保存基盤を刷新", y=375, size=50, align="left", x=110),
                T("3 [y]OpenSSH[/] [r]*sshole[/]", y=460, size=50, align="left", x=110),
                T("4 [y]ISUCON[/] AIが無人優勝", y=545, size=50, align="left", x=110),
                T("5 [y]サイバートラック[/] 生産終了", y=630, size=50, align="left", x=110),
            ]),
            ("足元の道具が、どんどんエージェント向けに変わっていくのだ。", [
                Card(["足元の道具が", "[y]AIエージェント[/]向けに"], y=760, h=200, size=60),
            ]),
            ("また明日なのだ！", [
                T("[p]また明日！[/]", y=990, size=90, bold=True, align="left", x=110, anim="pop", se="pon", jump=True),
            ]),
        ],
    ),
]
