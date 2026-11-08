# zundamon-movie

ずんだもんのナレーションと立ち絵つきで、YouTube Shorts 用の縦型解説動画（1080x1920 / 30fps / H.264 + AAC）を作るスクリプト。

- `output/nostr_shorts.mp4` … 「Nostr 解説（日本のアクティブユーザー約200人）」の完成動画（約93秒）
- `output/tech_news_20261107.mp4` … ニュース番組風「ずんだもんテックニュース 2026/11/7」（約97秒。Hacker News とはてブの話題から5本）

## 必要なもの

- Python 3 + `pillow numpy scipy fonttools`
- ffmpeg
- フォント Noto Sans CJK JP（`apt-get install fonts-noto-cjk`）
- VOICEVOX Engine（`docker run -d -p 50021:50021 voicevox/voicevox_engine:cpu-latest`）

## Claude Code のスキル

`.claude/skills/zundamon-shorts/` にスキルがある。Claude Code でこのリポジトリを開き、「ずんだもんで〇〇の解説動画を作って」「今日のテックニュースを動画にして」と頼むと、環境の準備から書き出し・確認まで同じ手順で進める。

- `SKILL.md` … 全体の手順
- `reference/script-format.md` … 原稿ファイルの書き方（要素・色・座標・読み方）
- `reference/news-mode.md` … ニュース番組モード（Hacker News・はてブからニュースを選ぶ手順と構成）
- `scripts/setup.sh` … ffmpeg・フォント・Python ライブラリ・VOICEVOX・立ち絵を準備する

## 作り方

```bash
# 0. 環境の準備（VOICEVOX の起動、立ち絵の口パク用3枚の生成など）
bash .claude/skills/zundamon-shorts/scripts/setup.sh

#    立ち絵を別の画像で作り直すとき（--mouth は元画像での口の範囲 x,y,w,h、口の線を含む）
python -m zmovie.tachie --image assets/source/zundamon_sakamoto_ahiru.png --mouth 464,474,64,62

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
| `assets/source/zundamon_sakamoto_ahiru.png` | 立ち絵の元画像（坂本アヒル氏作） |
| `assets/tachie/` | 元画像から作った口パク用3枚（開き・半開き・閉じ）と口の位置 |
| `make_video.py` | 全体の手順 |

## リファレンス（出典）

| 素材 | 出典 | 動画内の表記 |
|---|---|---|
| 立ち絵（`assets/source/zundamon_sakamoto_ahiru.png` と、そこから作った `assets/tachie/`） | ずんだもん立ち絵素材 / 作：坂本アヒル | 立ち絵：坂本アヒル |
| ナレーション音声 | VOICEVOX（https://voicevox.hiroshiba.jp/）・音声ライブラリ「ずんだもん」 | VOICEVOX:ずんだもん |
| キャラクター「ずんだもん」 | 東北ずん子・ずんだもんプロジェクト（https://zunko.jp/）。利用はキャラクター利用ガイドライン（https://zunko.jp/guideline.html）に従う | － |
| 日本語フォント | Noto Sans CJK JP（Google / Adobe、SIL Open Font License） | － |
| BGM・効果音 | `zmovie/audio.py` でプログラム生成（外部素材なし） | － |

動画を公開するときは、右上のクレジット（「VOICEVOX:ずんだもん」「立ち絵：坂本アヒル」）を消さないこと。立ち絵を他の絵に替えた場合は、この表と原稿の `TACHIE_CREDIT` を書き換える。
