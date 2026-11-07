"""ずんだもん解説ショート動画を作る。

  python make_video.py voice    # 1. ナレーション合成・長さの表・カナとタイミングの確認
  python make_video.py check    # 2. 各シーンの一番情報が多い瞬間を静止画にして自動検査
  python make_video.py render   # 3. 全体を書き出し
  python make_video.py verify   # 4. 長さ・音量・無音・口パクを確認

立ち絵は先に `python -m zmovie.tachie --image <画像> --mouth x,y,w,h` で作っておく。
"""
import argparse
import importlib
import json
import os
import re
import subprocess
import sys
import wave
from multiprocessing import Pool

import numpy as np
from PIL import Image

from zmovie import audio as A
from zmovie import render as R
from zmovie.voice import SR, synth_scene

ROOT = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(ROOT, "build")
TACHIE_DIR = os.path.join(ROOT, "assets", "tachie")
PAD_PRE, PAD_POST = 0.3, 0.8
SPF = SR // R.FPS  # 1 コマあたりのサンプル数

ap = argparse.ArgumentParser()
ap.add_argument("step", choices=["voice", "check", "render", "verify", "all"])
ap.add_argument("--project", default="nostr")
ap.add_argument("--speed", type=float, default=1.25)
ap.add_argument("--pause", type=float, default=1.0)
ap.add_argument("--max-sec", type=float, default=100.0)
ARGS = ap.parse_args() if __name__ == "__main__" else None

_TL = None


# ---------------------------------------------------------------- タイムライン
def load_project(name):
    return importlib.import_module(f"{name}.script")


def build_timeline(project, speed, pause):
    P = load_project(project)
    scenes, gt = [], 0.0
    for si, sc in enumerate(P.SCENES):
        v = synth_scene([p[0] for p in sc["parts"]], P.READINGS, speed, pause,
                        os.path.join(BUILD, "voice"))
        nfr = int(round((PAD_PRE + v["dur"] + PAD_POST) * R.FPS))
        dur = nfr / R.FPS
        items = []
        for pi, (_, its) in enumerate(sc["parts"]):
            for it in its:
                it = dict(it)
                it["t"] = PAD_PRE + v["cues"][pi] + it["delay"]
                it["part"] = pi
                items.append(it)
        scenes.append(dict(idx=si, name=sc["name"], chip=sc.get("chip"), title=sc.get("title"),
                           enter=sc.get("enter", False), voice=v, nfr=nfr, dur=dur,
                           start=gt, items=items, parts=[p[0] for p in sc["parts"]]))
        gt += dur
    nchips = max(s["chip"] or 0 for s in scenes)
    return dict(scenes=scenes, total=gt, credit=f"VOICEVOX:ずんだもん\n{P.TACHIE_CREDIT}",
                nchips=nchips, output=P.OUTPUT_NAME, speed=speed, pause=pause)


def fit_length(project):
    """長さが目標を超えたら pauseLengthScale → 話速 の順に調整する。"""
    speed, pause = ARGS.speed, ARGS.pause
    log = []
    tl = build_timeline(project, speed, pause)
    while tl["total"] > ARGS.max_sec and pause > 0.5:
        pause = round(pause - 0.1, 2)
        log.append(f"pauseLengthScale を {pause} に")
        tl = build_timeline(project, speed, pause)
    while tl["total"] > ARGS.max_sec and speed < 1.3:
        speed = round(speed + 0.01, 2)
        log.append(f"話速を {speed} に")
        tl = build_timeline(project, speed, pause)
    tl["adjust_log"] = log
    return tl


def timeline():
    global _TL
    if _TL is None:
        cfg = os.path.join(BUILD, "settings.json")
        if os.path.exists(cfg):
            s = json.load(open(cfg))
            _TL = build_timeline(s["project"], s["speed"], s["pause"])
        else:
            _TL = fit_length(ARGS.project)
            os.makedirs(BUILD, exist_ok=True)
            json.dump(dict(project=ARGS.project, speed=_TL["speed"], pause=_TL["pause"]), open(cfg, "w"))
        for sc in _TL["scenes"]:
            for it in sc["items"]:
                it["layer"], it["xy"] = R.make_layer(it)
    return _TL


def all_jumps(tl):
    return [sc["start"] + it["t"] for sc in tl["scenes"] for it in sc["items"] if it.get("jump")]


def enter_time(tl):
    return 0.05 if tl["scenes"][0]["enter"] else None


# ---------------------------------------------------------------- 口パク
def mouth_states(sc):
    """シーンの各コマの口（open/half/closed）をナレーションの音量から決める。"""
    wav = sc["voice"]["wav"]
    n = sc["nfr"]
    off = int(PAD_PRE * SR)
    rms = np.zeros(n)
    for f in range(n):
        s = f * SPF - off
        seg = wav[max(0, s - SPF // 2):max(0, s + SPF)]
        rms[f] = np.sqrt(np.mean(seg ** 2)) if len(seg) else 0
    ref = np.percentile(rms[rms > 1e-3], 90) if (rms > 1e-3).any() else 1
    lv = rms / ref
    out = []
    for x in lv:
        out.append("open" if x > 0.45 else "half" if x > 0.15 else "closed")
    return out


# ---------------------------------------------------------------- 音
def scene_audio(sc):
    n = sc["nfr"] * SPF
    a = np.zeros(n, np.float32)
    v = sc["voice"]["wav"]
    off = int(PAD_PRE * SR)
    a[off:off + len(v)] += v[:n - off]
    for it in sc["items"]:
        se = it.get("se")
        if se:
            x = A.SFX[se]() * A.SFX_GAIN[se]
            s = int(it["t"] * SR)
            a[s:s + len(x)] += x[:max(0, n - s)]
    return a


def write_wav(path, x):
    pcm = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def measure(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=true",
                        "-f", "null", "-"], capture_output=True, text=True).stderr
    summ = r[r.rfind("Summary:"):]
    lufs = float(re.search(r"I:\s+(-?[\d.]+) LUFS", summ).group(1))
    peak = float(re.search(r"Peak:\s+(-?[\d.inf]+) dBFS", summ).group(1))
    return lufs, peak


# ---------------------------------------------------------------- 描画（シーンごと）
def render_scene(si):
    tl = timeline()
    sc = tl["scenes"][si]
    tachie = R.Tachie(TACHIE_DIR)
    mouths = mouth_states(sc)
    jumps, ent = all_jumps(tl), enter_time(tl)
    os.makedirs(os.path.join(BUILD, "scenes"), exist_ok=True)
    wav_path = os.path.join(BUILD, "scenes", f"{si:02d}.wav")
    write_wav(wav_path, scene_audio(sc) * 0.8)
    out = os.path.join(BUILD, "scenes", f"{si:02d}.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{R.W}x{R.H}", "-r", str(R.FPS), "-i", "-", "-i", wav_path,
           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(sc["nfr"]):
        t = f / R.FPS
        fr = R.compose(sc, t, sc["start"] + t, tl["total"], tachie, mouths[f], jumps, ent,
                       tl["credit"], tl["nchips"])
        p.stdin.write(fr.convert("RGB").tobytes())
    p.stdin.close()
    p.wait()
    return out


# ---------------------------------------------------------------- 各ステップ
def step_voice():
    tl = timeline()
    print("| # | シーン | 音声(秒) | シーン長(秒) |")
    print("|---|---|---|---|")
    for sc in tl["scenes"]:
        print(f"| {sc['idx']} | {sc['name']} | {sc['voice']['dur']:.2f} | {sc['dur']:.2f} |")
    print(f"| | 合計 | | **{tl['total']:.2f}** |")
    print(f"\n話速 {tl['speed']} / pauseLengthScale {tl['pause']}")
    if tl.get("adjust_log"):
        print("長さ調整:", " → ".join(tl["adjust_log"]))
    print("\n## カナと文字を出すタイミング")
    for sc in tl["scenes"]:
        print(f"\n[{sc['idx']}] {sc['name']}")
        for pi, (txt, kana) in enumerate(zip(sc["parts"], sc["voice"]["kana"])):
            t = PAD_PRE + sc["voice"]["cues"][pi]
            n_it = sum(1 for it in sc["items"] if it["part"] == pi)
            print(f"  {t:5.2f}s 要素{n_it}個  {txt}\n           {kana}")


def info_max_time(sc):
    last = max([it["t"] for it in sc["items"]] + [0.3])
    return min(sc["dur"] - 1 / R.FPS, last + 0.9)


def step_check():
    tl = timeline()
    tachie = R.Tachie(TACHIE_DIR)
    os.makedirs(os.path.join(BUILD, "check"), exist_ok=True)
    problems = []
    # 文字化け（フォントに無い記号）
    texts = [sc["title"] or "" for sc in tl["scenes"]] + [tl["credit"]]
    for sc in tl["scenes"]:
        for it in sc["items"]:
            texts += [it.get("text", ""), *it.get("lines", []), it.get("prefix", ""), it.get("suffix", "")]
    miss = R.missing_glyphs(R.plain("".join(texts)) + "0123456789/リレーABCあなたみんな")
    if miss:
        problems.append(f"フォントに無い文字: {miss}")
    jumps, ent = all_jumps(tl), enter_time(tl)
    for sc in tl["scenes"]:
        t = info_max_time(sc)
        gt = sc["start"] + t
        fr = R.compose(sc, t, gt, tl["total"], tachie, "open", [], None, tl["credit"], tl["nchips"])
        path = os.path.join(BUILD, "check", f"{sc['idx']:02d}_{sc['name']}.png")
        fr.convert("RGB").save(path)
        # 検査する要素（画面座標でのインクのマスク）
        els = []
        if sc["title"]:
            im = R.title_img(sc["title"])
            els.append(("タイトル", im, (R.CX - im.width // 2, 128)))
        latest = {}
        for it in sc["items"]:
            if it["kind"] == "fig" and it["t"] <= t:
                latest[it["name"]] = it
        for it in sc["items"]:
            if it["t"] > t or (it["kind"] == "fig" and latest[it["name"]] is not it):
                continue
            label = R.plain(it.get("text") or " ".join(it.get("lines", [])) or it.get("name", "") or str(it.get("n")))
            els.append((label.replace("\n", " "), it["layer"], it["xy"]))
            if it.get("overflow"):
                problems.append(f"[{sc['idx']}] カードから文字がはみ出す: {label}")
        masks = []
        for label, im, (x, y) in els:
            m = np.zeros((R.H, R.W), bool)
            a = np.array(im.getchannel("A")) > 60
            h, w = a.shape
            y0, x0 = max(0, y), max(0, x)
            y1, x1 = min(R.H, y + h), min(R.W, x + w)
            m[y0:y1, x0:x1] = a[y0 - y:y1 - y, x0 - x:x1 - x]
            if y + h > R.H or x + w > R.W or x < 0 or y < 0:
                problems.append(f"[{sc['idx']}] はみ出し（画面外）: {label}")
            if m[:, R.SAFE_R:].any():
                problems.append(f"[{sc['idx']}] 右 150px（ボタン列）に重なる: {label}")
            if m[R.SAFE_B:, :].any():
                problems.append(f"[{sc['idx']}] 下 380px に重なる: {label}")
            masks.append((label, m))
        for i in range(len(masks)):
            for j in range(i + 1, len(masks)):
                ov = (masks[i][1] & masks[j][1]).sum()
                if ov > 30:
                    problems.append(f"[{sc['idx']}] 文字の重なり: 「{masks[i][0]}」と「{masks[j][0]}」({ov}px)")
        tx, ty = tachie.pos(gt, [], None)
        tm = tachie.mask_at(tx, ty)
        for label, m in masks:
            ov = (m & tm).sum()
            if ov > 30:
                problems.append(f"[{sc['idx']}] ずんだもんと重なる: 「{label}」({ov}px)")
        # ジャンプの最高点でも頭が文字に当たらないか
        for jt in jumps:
            if sc["start"] <= jt < sc["start"] + sc["dur"]:
                jx, jy = tachie.pos(jt + 0.21, jumps, ent)
                jm = tachie.mask_at(jx, jy)
                for label, m in masks:
                    if (m & jm).sum() > 30:
                        problems.append(f"[{sc['idx']}] ジャンプ中のずんだもんと重なる: 「{label}」")
    print("静止画:", os.path.join(BUILD, "check"))
    print("問題なし" if not problems else "\n".join(problems))
    return problems


def step_render():
    tl = timeline()
    n = len(tl["scenes"])
    with Pool(min(4, os.cpu_count() or 1)) as pool:
        outs = pool.map(render_scene, range(n))
    lst = os.path.join(BUILD, "concat.txt")
    with open(lst, "w") as f:
        for o in outs:
            f.write(f"file '{o}'\n")
    concat = os.path.join(BUILD, "concat.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
                    "-c", "copy", concat], check=True)
    # 音声は全体をまとめて作る（BGM をシーンをまたいで途切れさせないため）
    voice = np.concatenate([scene_audio(sc) for sc in tl["scenes"]])
    total_n = len(voice)
    music = A.bgm(total_n / SR)[:total_n]
    music = np.pad(music, (0, total_n - len(music)))
    intervals = [(sc["start"] + PAD_PRE, sc["start"] + PAD_PRE + sc["voice"]["dur"]) for sc in tl["scenes"]]
    music *= A.duck_envelope(total_n, intervals, -8) * A.db(-17)
    mix = voice + music
    tmp = os.path.join(BUILD, "mix.wav")
    gain = 0.5
    for _ in range(4):
        y = np.tanh(mix * gain * 1.1) / 1.1  # やわらかいリミッター
        write_wav(tmp, y)
        lufs, peak = measure(tmp)
        if abs(lufs + 14) < 0.3:
            break
        gain *= A.db(-14 - lufs)
    print(f"ミックス: {lufs:.1f} LUFS, ピーク {peak:.1f} dBFS")
    np.save(os.path.join(BUILD, "music_level.npy"), music * gain)
    os.makedirs(os.path.join(ROOT, "output"), exist_ok=True)
    out = os.path.join(ROOT, "output", f"{tl['output']}.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", concat, "-i", tmp, "-map", "0:v",
                    "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", str(SR),
                    "-movflags", "+faststart", out], check=True)
    print("書き出し:", out)
    return out


def ffprobe_dur(path, stream):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", stream, "-show_entries",
                        "stream=duration", "-of", "csv=p=0", path], capture_output=True, text=True)
    return float(r.stdout.strip())


def step_verify():
    tl = timeline()
    out = os.path.join(ROOT, "output", f"{tl['output']}.mp4")
    vd, ad = ffprobe_dur(out, "v:0"), ffprobe_dur(out, "a:0")
    print(f"映像 {vd:.3f}s / 音声 {ad:.3f}s / 差 {abs(vd - ad) * 1000:.0f}ms / タイムライン {tl['total']:.3f}s")
    lufs, peak = measure(out)
    print(f"音量: {lufs:.1f} LUFS（目標 -14）, ピーク {peak:.1f} dBFS")
    # BGM が途中で無音になっていないか（0.5 秒ごとの BGM の音量）
    m = np.load(os.path.join(BUILD, "music_level.npy"))
    win = SR // 2
    lv = [20 * np.log10(np.sqrt(np.mean(m[i:i + win] ** 2)) + 1e-9) for i in range(SR, len(m) - 2 * SR, win)]
    print(f"BGM の音量（最初の1秒・最後の2秒のフェード以外）: 最小 {min(lv):.1f} dBFS, 最大 {max(lv):.1f} dBFS")
    # 書き出した動画の音声に途切れ（無音）がないか
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", out, "-af",
                        "silencedetect=noise=-50dB:d=0.3", "-f", "null", "-"], capture_output=True, text=True).stderr
    sil = re.findall(r"silence_start: ([\d.]+)", r)
    print("0.3 秒以上の無音:", sil if sil else "なし")
    # ナレーションの重なり：シーン内で 1 本、シーンの間は余白で区切られている
    ov = [i for i, sc in enumerate(tl["scenes"]) if PAD_PRE + sc["voice"]["dur"] > sc["dur"]]
    print("ナレーションのはみ出し・重なり:", ov if ov else "なし")
    # 口パク：動画からコマを切り出し、口のまわりの画素の変化を見る
    os.makedirs(os.path.join(BUILD, "lips"), exist_ok=True)
    tachie = R.Tachie(TACHIE_DIR)
    sc = tl["scenes"][2]
    times = [sc["start"] + 0.3 + 0.1 * k for k in range(24)]
    crops = []
    for k, tt in enumerate(times):
        p = os.path.join(BUILD, "lips", f"{k:02d}.png")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{tt:.3f}", "-i", out, "-frames:v", "1", p], check=True)
        x, y = tachie.pos(tt, all_jumps(tl), enter_time(tl))
        mx, my, mw, mh = tachie.mouth
        cx, cy = x + mx + mw // 2, y + my + mh // 2
        crops.append(Image.open(p).crop((cx - 90, cy - 60, cx + 90, cy + 60)))
    sheet = Image.new("RGB", (180 * 8, 120 * 3))
    for k, c in enumerate(crops):
        sheet.paste(c, ((k % 8) * 180, (k // 8) * 120))
    sp = os.path.join(BUILD, "lips", "sheet.png")
    sheet.save(sp)
    arr = [np.asarray(c, float) for c in crops]
    diffs = [np.abs(arr[i] - arr[i - 1]).mean() for i in range(1, len(arr))]
    print(f"口のまわりのコマ間の差（平均）: {np.mean(diffs):.2f}、変化したコマ {sum(d > 1 for d in diffs)}/{len(diffs)}")
    print("口パクの確認画像:", sp)


if __name__ == "__main__":
    s = ARGS.step
    if s in ("voice", "all"):
        step_voice()
    if s in ("check", "all"):
        step_check()
    if s in ("render", "all"):
        step_render()
    if s in ("verify", "all"):
        step_verify()
