"""VOICEVOX でナレーションを合成し、アクセント句ごとのタイミングを返す。"""
import hashlib
import io
import json
import os
import urllib.parse
import urllib.request
import wave

import numpy as np

HOST = os.environ.get("VOICEVOX_HOST", "http://127.0.0.1:50021")
SPEAKER = 3  # ずんだもん（ノーマル）
SR = 48000


def _post(path, params, body=None):
    url = f"{HOST}{path}?{urllib.parse.urlencode(params)}"
    data = json.dumps(body).encode() if body is not None else b""
    req = urllib.request.Request(url, data=data, method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def audio_query(text):
    return json.loads(_post("/audio_query", {"text": text, "speaker": SPEAKER}))


def apply_readings(text, readings):
    for k, v in readings.items():
        text = text.replace(k, v)
    return text


def mora_count(query):
    return sum(len(ap["moras"]) for ap in query["accent_phrases"])


def phrase_times(query):
    """各アクセント句の (開始, 終了, カナ) を秒で返す（話速込み）。"""
    sp = query["speedScale"]
    pls = query.get("pauseLengthScale", 1.0)
    t = query["prePhonemeLength"]
    out = []
    for ap in query["accent_phrases"]:
        st = t
        for m in ap["moras"]:
            t += (m.get("consonant_length") or 0) + m["vowel_length"]
        en = t
        if ap.get("pause_mora"):
            t += ap["pause_mora"]["vowel_length"] * pls
        kana = "".join(m["text"] for m in ap["moras"])
        out.append((st / sp, en / sp, kana))
    total = (t + query["postPhonemeLength"]) / sp
    return out, total


def synth_scene(parts, readings, speed, pause_scale, cache_dir):
    """parts: ナレーション文字列のリスト（区切りごと）。

    戻り値: dict(wav=np.float32 配列, dur=秒, cues=[各区切りの開始秒], kana=..., phrases=...)
    """
    texts = [apply_readings(p, readings) for p in parts]
    full = "".join(texts)
    q = audio_query(full)
    q.update(speedScale=speed, pauseLengthScale=pause_scale, volumeScale=1.0,
             prePhonemeLength=0.1, postPhonemeLength=0.1,
             outputSamplingRate=SR, outputStereo=False)

    key = hashlib.sha1(json.dumps(q, sort_keys=True).encode()).hexdigest()[:16]
    os.makedirs(cache_dir, exist_ok=True)
    path = os.path.join(cache_dir, f"{key}.wav")
    if not os.path.exists(path):
        with open(path, "wb") as f:
            f.write(_post("/synthesis", {"speaker": SPEAKER}, q))
    with wave.open(path) as w:
        assert w.getframerate() == SR
        pcm = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
    wav = pcm.astype(np.float32) / 32768.0

    phrases, total = phrase_times(q)
    # 区切りごとのモーラ数を数え、全体のアクセント句の境界に対応づける
    starts_m = [0]
    acc = 0
    for tx in texts[:-1]:
        acc += mora_count(audio_query(tx)) if tx.strip() else 0
        starts_m.append(acc)
    ph_start_m = []
    acc = 0
    for ap in q["accent_phrases"]:
        ph_start_m.append(acc)
        acc += len(ap["moras"])
    cues = []
    cue_idx = []
    for m in starts_m:
        i = int(np.argmin([abs(x - m) for x in ph_start_m]))
        cue_idx.append(i)
        cues.append(phrases[i][0] if m > 0 else 0.0)
    kana_parts = []
    for k, i in enumerate(cue_idx):
        j = cue_idx[k + 1] if k + 1 < len(cue_idx) else len(phrases)
        kana_parts.append("/".join(p[2] for p in phrases[i:j]))
    return dict(wav=wav, dur=len(wav) / SR, calc_dur=total, cues=cues,
                kana=kana_parts, phrases=phrases, text=full)
