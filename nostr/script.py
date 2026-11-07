"""Nostr 解説ショート動画の原稿と画面構成。

各シーンは parts のリスト。part = (ナレーション, [その区切りで画面に出す要素...])。
要素はナレーションのその区切りが読まれ始めた瞬間（アクセント句のタイミング）に出る。

文字の色分け（マークアップ [色]文字[/]）:
  y = 黄  : Nostr まわりの用語
  c = 水色: 鍵（公開鍵・秘密鍵）
  p = ピンク: 強調
  g = 緑  : 成功
  r = 赤  : 失敗・危険
  m = グレー: 補足
"""
from zmovie.items import T, Card, Counter, Strike, Fig

OUTPUT_NAME = "nostr_shorts"
TACHIE_CREDIT = "立ち絵：坂本アヒル"

# VOICEVOX に渡す前に置き換える読み
READINGS = {
    "Nostr": "のすたー",   # 「ノスター」だと「ノ／スター」と切れて読まれる
    "Zap": "ザップ",
    "日本": "にほん",       # 「ニッポン」と読まれるのを防ぐ
}

SCENES = [
    # 0. つかみ
    dict(
        name="hook", chip=None, title=None, jump_at_start=False, enter=True,
        parts=[
            ("運営会社がいないSNS、", [
                T("運営会社がいないSNS", y=250, size=58),
            ]),
            ("Nostrを知ってるのだ？", [
                T("[y]Nostr[/]", y=320, size=210, bold=True, anim="pop", se="pon"),
                T("（ノスター）", y=585, size=44, color="m"),
            ]),
            ("日本のアクティブユーザーは、およそ200人。", [
                T("日本のアクティブユーザー", y=660, size=56),
                Counter(200, prefix="約", suffix="人", y=735, size=150, color="p", se="pon"),
            ]),
            ("ほぼ学年集会なのだ。", [
                Card(["ほぼ[p]学年集会[/]レベル"], y=960, h=120, size=62),
            ]),
        ],
    ),
    # 1. Nostr ってなに
    dict(
        name="what", chip=1, title="[y]Nostr[/]ってなに？",
        parts=[
            ("Nostrは、", [
                T("[y]N[/]otes and", y=290, size=74, align="left", x=130),
                T("[y]O[/]ther [y]S[/]tuff", y=380, size=74, align="left", x=130),
                T("[y]T[/]ransmitted by", y=470, size=74, align="left", x=130),
                T("[y]R[/]elays", y=560, size=74, align="left", x=130),
            ]),
            ("リレーで運ばれるメモやいろいろ、という英語の略なのだ。", [
                T("＝[y]リレー[/]で運ばれる\n　メモとかいろいろ", y=690, size=56, align="left", x=110),
            ]),
            ("会社のサービスではなく、通信の約束ごと、つまりプロトコルなのだ。", [
                Card(["会社のサービスじゃなくて", "[p]通信の約束ごと[/]（[y]プロトコル[/]）"],
                     y=880, h=200, size=52),
            ]),
        ],
    ),
    # 2. アカウント＝鍵
    dict(
        name="keys", chip=2, title="アカウント＝[c]鍵[/]のペア",
        parts=[
            ("アカウントは、鍵のペアでできているのだ。", []),
            ("公開鍵は、みんなに見せる名札。", [
                Card(["[c]公開鍵[/]　[m]npub1…[/]", "みんなに見せる[c]名札[/]"],
                     y=290, h=230, size=52, border="c", icon="key"),
            ]),
            ("秘密鍵は自分だけのハンコで、絶対ナイショ。", [
                Card(["[c]秘密鍵[/]　[m]nsec1…[/]", "[p]絶対ナイショ[/]の[c]ハンコ[/]"],
                     y=570, h=230, size=52, border="c", icon="key"),
            ]),
            ("メールアドレスも電話番号もいらないのだ。", [
                T("メアドも電話番号も[p]いらない[/]", y=880, size=58, anim="pop", se="pon"),
            ]),
        ],
    ),
    # 3. リレー
    dict(
        name="relay", chip=3, title="投稿は[y]リレー[/]へ",
        parts=[
            ("投稿は、リレーと呼ばれるサーバーに送るのだ。", [
                Fig("relays", stage=1, y=290, h=720),
            ]),
            ("しかも、いくつものリレーに同時にばらまく。", [
                Fig("relays", stage=2, y=290, h=720, se="tick"),
            ]),
            ("ひとつが落ちても、ほかのリレーが届けてくれるのだ。", [
                Fig("relays", stage=3, y=290, h=720, se=None),
                T("[g]ひとつ落ちても平気[/]", y=1030, size=60, anim="pop", se="pon", delay=0.9),
            ]),
        ],
    ),
    # 4. いいところ
    dict(
        name="good", chip=4, title="いいところ",
        parts=[
            ("いいところは、運営に凍結されないこと。", [
                Card(["運営に[p]凍結されない[/]"], y=300, h=170, size=62, icon="check"),
            ]),
            ("アプリを好きに選べて、", [
                Card(["アプリを[p]自由に選べる[/]"], y=510, h=170, size=62, icon="check"),
            ]),
            ("Zapという、ビットコインの投げ銭もできるのだ。", [
                Card(["[y]Zap[/]で[p]投げ銭[/]できる", "[m]（ビットコインで）[/]"], y=720, h=200, size=58,
                     icon="check", jump=True),
            ]),
        ],
    ),
    # 5. 落とし穴（失敗）
    dict(
        name="trap", chip=5, title="最大の[r]落とし穴[/]",
        parts=[
            ("ただし、秘密鍵をなくしたら、", [
                T("[c]秘密鍵[/]をなくすと…", y=320, size=66),
            ]),
            ("アカウントは二度と戻らないのだ。", [
                T("[r]二度と戻らない[/]", y=460, size=116, bold=True, anim="pop", se="boo"),
            ]),
            ("パスワードリセットなんて、ない。", [
                T("パスワードリセット：[r]なし[/]", y=700, size=60),
            ]),
            ("漏れたら乗っ取られ放題なのだ。", [
                T("漏れたら[r]乗っ取られ放題[/]", y=850, size=66, anim="pop", se="pon"),
            ]),
        ],
    ),
    # 6. 日本語圏のいま（場末）
    dict(
        name="local", chip=6, title="日本語圏の[p]いま[/]",
        parts=[
            ("日本のアクティブユーザーは、約200人。", [
                Counter(200, prefix="約", suffix="人", y=280, size=170, color="p", se="pon"),
                T("アクティブユーザー", y=500, size=50, color="m"),
            ]),
            ("タイムラインは、ほぼ全員顔見知り。", [
                T("タイムラインは\n[p]ほぼ全員 顔見知り[/]", y=600, size=58),
            ]),
            ("新人が来ると、ちょっとしたお祭りなのだ。", [
                T("新人が来たら[y]お祭り騒ぎ[/]", y=790, size=58),
            ]),
            ("これは過疎ではなく、アットホームと呼ぶのだ。", [
                Strike("過疎", y=900, size=80, x=130),
                T("→ [p]アットホーム[/]", y=900, size=80, align="left", x=350,
                  anim="pop", se="pon", delay=0.7, jump=True),
            ]),
        ],
    ),
    # 7. はじめかた（成功）
    dict(
        name="start", chip=7, title="はじめかた",
        parts=[
            ("始め方は簡単。", []),
            ("アプリを入れて、", [T("① アプリを入れる", y=290, size=60, align="left", x=120)]),
            ("鍵を作って、", [T("② [c]鍵[/]を作る", y=410, size=60, align="left", x=120)]),
            ("秘密鍵を安全にメモしたら、", [T("③ [c]秘密鍵[/]を安全にメモ", y=530, size=60, align="left", x=120)]),
            ("もう投稿できるのだ。", [T("④ 投稿する！", y=650, size=60, align="left", x=120)]),
            ("おめでとう、201人目なのだ！", [
                T("[g]祝・201人目[/]", y=800, size=120, bold=True, anim="pop", se="kiran", jump=True),
            ]),
        ],
    ),
    # 8. まとめ
    dict(
        name="summary", chip=None, title="まとめ",
        parts=[
            ("まとめ。", []),
            ("Nostrは運営のいないSNS。", [T("・運営のいない[y]分散型SNS[/]", y=300, size=60, align="left", x=110)]),
            ("秘密鍵が命。", [T("・[c]秘密鍵[/]が命", y=420, size=60, align="left", x=110)]),
            ("人は少ないけど、あったかいのだ。", [T("・人は少ないけど[p]あったかい[/]", y=540, size=60, align="left", x=110)]),
            ("202人目は、きみなのだ。", [
                Card(["[p]202人目[/]は、きみなのだ"], y=720, h=170, size=70, jump=True, se="pon"),
            ]),
        ],
    ),
]
