#!/usr/bin/env bash
# ずんだもん動画づくりの環境を準備する（何度実行しても安全）。
# 使い方: bash .claude/skills/zundamon-shorts/scripts/setup.sh
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

# 1. ffmpeg
command -v ffmpeg >/dev/null || { apt-get update -qq && apt-get install -y -qq ffmpeg >/dev/null; }

# 2. 日本語フォント Noto Sans CJK JP
fc-list | grep -q "Noto Sans CJK JP" || { apt-get install -y -qq fonts-noto-cjk >/dev/null 2>&1 \
  || { apt-get update -qq && apt-get install -y -qq fonts-noto-cjk >/dev/null; }; }

# 3. Python ライブラリ
python3 -c "import PIL, numpy, scipy, fontTools" 2>/dev/null || pip install -q pillow numpy scipy fonttools

# 4. VOICEVOX Engine（Docker）
if ! curl -s -m 3 localhost:50021/version >/dev/null; then
  if ! docker info >/dev/null 2>&1; then
    (dockerd >/tmp/dockerd.log 2>&1 &)
    for _ in $(seq 30); do docker info >/dev/null 2>&1 && break; sleep 1; done
  fi
  docker start voicevox >/dev/null 2>&1 \
    || docker run -d --name voicevox -p 50021:50021 voicevox/voicevox_engine:cpu-latest >/dev/null
  for _ in $(seq 120); do curl -s -m 2 localhost:50021/version >/dev/null && break; sleep 1; done
fi
echo "VOICEVOX: $(curl -s -m 3 localhost:50021/version)"

# 5. 立ち絵（口パク用 3 枚）。無ければ同梱の元画像から作る
if [ ! -f assets/tachie/open.png ]; then
  python3 -m zmovie.tachie --image assets/source/zundamon_sakamoto_ahiru.png --mouth 464,474,64,62
fi
echo "準備完了"
