# zundamon-movie

ずんだもんのナレーションと立ち絵つきで、YouTube Shorts 用の縦型解説動画（1080x1920 / 30fps / H.264 + AAC）を作るスクリプト。

- `output/nostr_shorts.mp4` … 「Nostr 解説（日本のアクティブユーザー約200人）」の完成動画（約93秒）
- `output/tech_news_20261107.mp4` … ニュース番組風「ずんだもんテックニュース 2026/11/7」（約97秒。Hacker News とはてブの話題から5本）

## 必要なもの

- Python 3 + `pillow numpy scipy fonttools`
- ffmpeg
- フォント Noto Sans CJK JP（`apt-get install fonts-noto-cjk`）
- VOICEVOX Engine（`docker run -d -p 50021:50021 voicevox/voicevox_engine:cpu-latest`）

## 作り方

```bash
# 0. 立ち絵を口パク用の3枚（開き・半開き・閉じ）に分ける。立ち絵画像はリポジトリに入れない
#    --mouth は元画像での口の範囲 x,y,w,h（口の線を含む）
python -m zmovie.tachie --image zundamon.png --mouth 464,474,64,62

python make_video.py voice    # 1. ナレーション合成・長さの表・カナと文字のタイミング確認
python make_video.py check    # 2. 各シーンの静止画を build/check/ に出して自動検査
python make_video.py render   # 3. output/<名前>.mp4 に書き出し
python make_video.py verify   # 4. 長さ・音量（-14 LUFS）・無音・口パクを確認
```

どの原稿を使うかは `--project` で選ぶ（`nostr` / `news`）。例：`python make_video.py render --project news`

話速などを変えたときは `build/<project>/settings.json` を消してから実行する（`--speed 1.25 --pause 1.0 --max-sec 100`）。

原稿の `THEME = dict(style="news", ...)` でニュース番組風（番組ロゴ・速報テロップ・NEWS バッジ・見出し帯・出典欄・ジングル・ニュース風 BGM）になる。

## ファイル

| ファイル | 中身 |
|---|---|
| `nostr/script.py` | Nostr 解説の原稿と画面構成（シーンごとのナレーションと画面要素、読み方の置き換え） |
| `news/script.py` | テックニュース 2026/11/7 の原稿と画面構成 |
| `zmovie/voice.py` | VOICEVOX で合成し、アクセント句ごとのタイミングから文字を出す時刻を求める |
| `zmovie/render.py` | Pillow で1コマずつ描く（文字・カード・図・進行バー・立ち絵） |
| `zmovie/audio.py` | ローファイ調 BGM と効果音（文字・ポン・キラン・ブー）をプログラムで合成 |
| `zmovie/tachie.py` | 立ち絵の背景抜き・切り離し・口パク用3枚の生成 |
| `make_video.py` | 全体の手順 |

クレジット: VOICEVOX:ずんだもん / 立ち絵：坂本アヒル
