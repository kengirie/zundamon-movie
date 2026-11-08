# 原稿ファイル（`<project>/script.py`）の書き方

見本：解説モード `nostr/script.py`、ニュース番組モード `news/script.py`。

## ファイルの中身

```python
from zmovie.items import T, Card, Counter, Strike, Fig

OUTPUT_NAME = "nostr_shorts"            # output/<これ>.mp4
TACHIE_CREDIT = "立ち絵：坂本アヒル"     # 右上のクレジット（2 行目）
READINGS = {"Nostr": "のすたー"}         # VOICEVOX に渡す前に置き換える。上から順に置き換えるので長い語を先に
THEME = dict(style="news", ...)         # 省略すると解説モードの見た目
SCENES = [ ... ]
```

## シーン（dict）

| キー | 意味 |
|---|---|
| `name` | 英字の短い名前（静止画のファイル名に使う） |
| `parts` | `[("ナレーション", [要素, ...]), ...]`。各要素はその区切りが読まれ始めた瞬間に出る |
| `title` | 上部の見出し（マークアップ可）。`None` で無し |
| `chip` | 解説モードの「n / 本編数」チップの n。つかみ・まとめは `None` |
| `enter` | `True` で最初のシーンにずんだもんが下から登場する |
| `news_no`, `category`, `cat_color`, `headline`, `source` | ニュース番組モード用（news-mode.md） |
| `jingle` | `True` でシーン頭にジングル（ニュースのオープニング用） |

シーンの長さ = 0.3 秒 + ナレーション + 0.8 秒（自動）。

## 要素

共通の引数：`se`（効果音 `"tick"`/`"pon"`/`"kiran"`/`"boo"`/`None`、既定は tick）、`jump=True`（出た瞬間にずんだもんが跳ねる）、`anim`（`"fade_up"` か `"pop"`）、`delay`（秒。基本は使わず区切りを細かくする）。

| 関数 | 用途 | 主な引数 |
|---|---|---|
| `T(text, y, size=60, align="center", x=None, bold=False, color="w")` | 文字。`\n` で改行 | `align="left"` のときは `x` を指定 |
| `Card(lines, y, h, size=56, border="w", icon=None)` | 角丸の箱に入った文字（幅は x=70〜920 固定） | `icon="key"`/`"check"`、`lines` は行のリスト |
| `Counter(n, y, size=150, prefix="", suffix="", color="p", comma=False)` | 0 から n まで数え上げる数字 | `comma=True` で 10,000 表記 |
| `Strike(text, y, size=80, x=100)` | グレーの文字に赤い取り消し線（「~~過疎~~→アットホーム」など） | 隣の文字とは 40px 以上空ける |
| `Fig(name, stage, y, h)` | `zmovie/render.py` の `FIGS` に登録した図。同じ name は後の stage に置き換わる | 新しい図は `FIGS` に関数を追加 |

## 色のマークアップ

`"[y]Nostr[/]ってなに？"` のように書く。

| 記号 | 色 | 使い方の例 |
|---|---|---|
| `y` | 黄 | 用語・固有名詞 |
| `c` | 水色 | 鍵・数字・データ |
| `p` | ピンク | 強調 |
| `g` | 緑 | 成功・よい知らせ |
| `r` | 赤 | 失敗・危険・悪い知らせ |
| `m` | グレー | 補足・用語の説明 |
| `w` | 白 | 既定 |

テーマごとに決めた色分けは原稿の先頭の docstring に書いておく。

## 画面の座標（1080x1920）

```
y=0    進行バー(12px)
       解説: チップ(y=44) / タイトル(y=128)       ニュース: ロゴ(y=22)・テロップ(y=98〜150)
       右上にクレジット                            NEWSバッジ(y=172)・見出し帯(y=246〜約430)
y≈280  本文はここから（ニュースは y≈470 から）
 :     x=70〜920 が使える（右 150px は Shorts のボタン列）
y≈1100 ここまで全幅を使える
 :     ずんだもん：x≈618〜920、頭のてっぺん y≈1150（跳ねると 80px 上がる）
 :     この範囲は x<600 だけ使える（ニュースの出典欄は y=1190）
y=1540 これより下（380px）は Shorts の UI。文字を置かない
```

文字の大きさの目安：見出し 76〜78、本文 50〜64、大きな数字 100〜170、補足 40〜44。
全角 1 文字 ≒ 文字サイズ px の幅。幅 850px に収まる文字数 = 850 / サイズ（例：56px なら約 15 文字、アイコン付きカードはさらに 2 文字少ない）。

## 読み方の注意（VOICEVOX）

- `make_video.py voice` が出すカナを必ず全部読む
- これまでに直したもの：`Nostr→のすたー`、`日本→にほん`（ニッポン防止）、`GitHub→ぎっとはぶ`、`Git→ぎっと`、`10.6p2→じゅってんろくぴーつー`、`OpenSSH→オープンエスエスエイチ`、`musl→マッスル`、`ISUCON→アイスコン`、「年25万台」→「年間25万台」
- `SNS` はそのままで正しく読める（「エスエヌエス」と書くと逆に変に切れる）

## 静止画の一覧を作る

```bash
python3 -c "
from PIL import Image, ImageDraw; import glob
fs=sorted(glob.glob('build/<project>/check/*.png')); cols=5
s=Image.new('RGB',(cols*432,((len(fs)+cols-1)//cols)*768))
for i,f in enumerate(fs):
  im=Image.open(f).resize((432,768)); d=ImageDraw.Draw(im)
  d.line([(372,0),(372,768)],fill=(255,0,0)); d.line([(0,616),(432,616)],fill=(255,0,0))  # UI の境界
  s.paste(im,((i%cols)*432,(i//cols)*768))
s.save('build/<project>/check/sheet.png')"
```

赤線の右と下は Shorts の UI に隠れる範囲。
