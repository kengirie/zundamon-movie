---
name: zundamon-shorts
description: ずんだもんのナレーション（VOICEVOX）と立ち絵（口パク・揺れ・ジャンプつき）で、YouTube Shorts 用の縦型動画（1080x1920/30fps/mp4）を作る。テーマを解説する「解説モード」と、Hacker News・はてなブックマークで話題の技術ニュースをまとめる「ニュース番組モード」がある。「ずんだもんで〇〇の解説動画を作って」「今日のテックニュースを動画にして」「ショート動画にして」などで使う。
---

# ずんだもん Shorts 動画

このリポジトリの `make_video.py` と `zmovie/` を使い、原稿ファイル（`<project>/script.py`）を書くだけで動画を作る。
コードを一から書き直さないこと。足りない表現だけ `zmovie/` に追加する。

## 0. 環境を準備する（毎回最初に）

```bash
bash .claude/skills/zundamon-shorts/scripts/setup.sh
```

ffmpeg・Noto Sans CJK JP・Python ライブラリ（pillow numpy scipy fonttools）・VOICEVOX Engine（Docker の `voicevox/voicevox_engine:cpu-latest`、ポート 50021）・立ち絵 3 枚（`assets/tachie/`）をそろえる。
クラウド環境は作り直されると Docker が止まっているので、そのたびに実行する。Docker の起動に許可が必要な環境ならユーザーに聞く。

## 1. 原稿を書く

- 解説モード：`<テーマ名>/script.py` を新しく作る。見本は `nostr/script.py`
- ニュース番組モード：まず [reference/news-mode.md](reference/news-mode.md) の手順でニュースを集め、`news/script.py` を書き換える（日付・`OUTPUT_NAME`・テロップ・各ニュース）

書き方（シーン・要素・色・座標・読み方）は [reference/script-format.md](reference/script-format.md) を読む。要点：

- 長さの目安は 80〜100 秒。シーンは「つかみ → 本編 → まとめ」
- 口調はずんだもん（語尾「〜なのだ」）。ただし毎文には付けない。1 シーンに 1〜2 回まで
- ナレーションを `|` 相当の区切り（parts）に分け、その区切りが読まれた瞬間に画面の要素を出す。強調語を読む瞬間に出したいときは `delay` ではなく区切りを細かくする
- 英字・数字・略語は `READINGS` で読みを指定する。カタカナで「ノ／スター」のように変に切れるときはひらがなにする（例：`Nostr→のすたー`、`GitHub→ぎっとはぶ`、`日本→にほん`）

## 2. ナレーションを作って確認する

```bash
python make_video.py voice --project <project>
```

- シーンごとの長さの表と合計を見る
- 各区切りのカナ（VOICEVOX の読み）を全部読み、読み間違いがあれば `READINGS` か原稿を直す（例：「年25万台」→「トシ」と読まれたので「年間25万台」に）
- 区切りの時刻が原稿の切れ目と合っているか見る
- 長さが目標を超えたら、意味を変えずに次の順で直し、何をしたか報告する：①原稿の余計な読点や重複表現を削る → ②`--pause`（pauseLengthScale）を下げる → ③`--speed` を上げる（1.3 まで）。②③は `--max-sec` を超えると自動で行われる
- 話速・間を変えたら `build/<project>/settings.json` を消してから再実行する

## 3. 静止画で検査する

```bash
python make_video.py check --project <project>
```

各シーンの一番情報が多い瞬間を `build/<project>/check/*.png` に出し、自動で次を検査する：
文字どうしの重なり、画面外へのはみ出し、下 380px と右 150px（Shorts の UI）への重なり、カードからの文字のはみ出し、ずんだもんとの重なり（ジャンプの最高点も）、フォントに無い文字（豆腐 □）。

**「問題なし」でも必ず画像を一覧にして目で見る。** 一覧の作り方は script-format.md の末尾にある。直し方の定番：
- カードの文字がはみ出す → 文言を短くする／文字を小さくする／行を分ける
- ずんだもんに当たる → 要素を上に詰める、左寄せ（`align="left", x=110`）にする、そのシーンではジャンプしない
- 縦が足りない → `y` を詰める。本文は y≈1100 まで、それより下は x<600（ずんだもんの左）だけ使える

## 4. 書き出す

```bash
python make_video.py render --project <project>
```

`output/<OUTPUT_NAME>.mp4` ができる（4 並列で 1 分弱）。音量は自動で -14 LUFS に合わせる。

## 5. 最終確認

```bash
python make_video.py verify --project <project>
```

確認すること：映像と音声の長さが一致（差 0ms）、-14 LUFS 前後、0.3 秒以上の無音なし、ナレーションの重なりなし、BGM が途中で無音にならない。
口パクは `build/<project>/lips/sheet.png` を目で見て、開き・半開き・閉じが切り替わっているか確かめる。必要なら `ffmpeg -ss <秒> -i <mp4> -frames:v 1 x.png` でコマを切り出して見る。

## 6. 仕上げ

- 完成した mp4 はユーザーに送る（SendUserFile が使えれば使う）
- 原稿と mp4 をコミットしてプッシュする（ユーザーの指定ブランチへ）
- 報告には、シーンごとの長さの表、直した読み、静止画で直したこと、最終確認の結果を入れる

## 守ること

- 画面の下 380px・右 150px には重要な文字を置かない（右上のクレジットとテロップは例外）
- 右上のクレジット「VOICEVOX:ずんだもん」「立ち絵：坂本アヒル」は消さない（`TACHIE_CREDIT`）
- 立ち絵は `assets/source/zundamon_sakamoto_ahiru.png`（坂本アヒル氏作）。別の絵を使うときは `python -m zmovie.tachie --image <画像> --mouth x,y,w,h` で作り直し、クレジットと README の出典も変える
- 効果音の使い分け：文字が出る＝小さな音（tick）、強調＝ポン（pon）、成功＝キラン（kiran）、失敗＝低いブー（boo）
- 事実は確認できた情報源の範囲で書く。不確かな数字は「〜とされる」「〜そうなのだ」にする
