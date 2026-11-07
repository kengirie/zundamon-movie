"""BGM（ローファイ調）と効果音をプログラムで合成する。すべて 48kHz モノラル float32。"""
import numpy as np
from scipy import signal

SR = 48000
rng = np.random.default_rng(7)


def _t(dur):
    return np.arange(int(dur * SR)) / SR


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def lowpass(x, fc, order=2):
    b, a = signal.butter(order, fc / (SR / 2), "low")
    return signal.lfilter(b, a, x)


def highpass(x, fc, order=2):
    b, a = signal.butter(order, fc / (SR / 2), "high")
    return signal.lfilter(b, a, x)


def bandpass(x, lo, hi, order=2):
    b, a = signal.butter(order, [lo / (SR / 2), hi / (SR / 2)], "band")
    return signal.lfilter(b, a, x)


def db(x):
    return 10 ** (x / 20)


# ------------------------------------------------------------------ 効果音
def sfx_tick():
    """文字が出るときの小さな音。"""
    t = _t(0.05)
    return (np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 90) * 0.25).astype(np.float32)


def sfx_pon():
    """強調表示の「ポン」。"""
    t = _t(0.28)
    f = 760 + 260 * np.exp(-t * 40)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = (np.sin(ph) + 0.35 * np.sin(2 * ph)) * np.exp(-t * 16)
    x *= np.minimum(1, t / 0.003)
    return (x * 0.55).astype(np.float32)


def sfx_kiran():
    """成功の「キラン」。高い音のきらきらした上昇アルペジオ。"""
    out = np.zeros(int(0.9 * SR))
    for i, n in enumerate([84, 88, 91, 96, 100]):
        t = _t(0.9 - i * 0.05)
        f = midi(n)
        x = (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 2.01 * t)) * np.exp(-t * 6)
        x *= np.minimum(1, t / 0.004)
        st = int(i * 0.05 * SR)
        out[st:st + len(x)] += x * 0.22
    t = _t(0.9)
    out += highpass(rng.standard_normal(len(t)), 6000) * np.exp(-t * 8) * 0.05
    return out.astype(np.float32)


def sfx_boo():
    """失敗の低い「ブー」。"""
    t = _t(0.65)
    f = 125 - 20 * t
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = signal.sawtooth(ph) * 0.6 + np.sin(ph) * 0.4
    x = lowpass(x, 900)
    env = np.minimum(1, t / 0.01) * np.minimum(1, (0.65 - t) / 0.12)
    return (x * env * 0.5).astype(np.float32)


SFX = {"tick": sfx_tick, "pon": sfx_pon, "kiran": sfx_kiran, "boo": sfx_boo}
SFX_GAIN = {"tick": db(-12), "pon": db(-4), "kiran": db(-3), "boo": db(-3)}


# ------------------------------------------------------------------ BGM
def bgm(duration, bpm=76):
    """ゆったりしたローファイ調。4 小節のコード進行をくり返す。途中で無音にならない。"""
    beat = 60 / bpm
    bar = beat * 4
    n = int((duration + 1) * SR)
    out = np.zeros(n)
    # Fmaj7 - Em7 - Dm7 - Cmaj7
    chords = [[53, 57, 60, 64], [52, 55, 59, 62], [50, 53, 57, 60], [48, 52, 55, 59]]
    roots = [41, 40, 38, 36]

    def add(x, start):
        s = int(start * SR)
        if s >= n:
            return
        e = min(n, s + len(x))
        out[s:e] += x[:e - s]

    # エレピ風の和音（各小節頭と 3 拍目裏）＋ずっと鳴っているパッド
    k = 0
    tb = 0.0
    while tb < duration + 1:
        ch = chords[k % 4]
        for hit, ln, vel in [(0.0, bar, 1.0), (beat * 2.5, bar - beat * 2.5, 0.6)]:
            t = _t(ln + 0.4)
            env = np.exp(-t * 1.6) * np.minimum(1, t / 0.01)
            for i, m in enumerate(ch):
                f = midi(m + 12) * (1 + 0.0015 * (i - 1.5))
                x = np.sin(2 * np.pi * f * t + 0.6 * np.sin(2 * np.pi * f * 2 * t) * np.exp(-t * 4))
                add(x * env * 0.055 * vel, tb + hit + i * 0.012)
        t = _t(bar + 0.3)
        penv = np.minimum(1, t / 0.4) * np.minimum(1, (bar + 0.3 - t) / 0.3)
        for m in ch:
            f = midi(m)
            add((np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 2 * t)) * penv * 0.03, tb)
        # ベース
        for hit, ln in [(0, beat * 1.5), (beat * 1.5, beat * 0.5), (beat * 2, beat * 2)]:
            t = _t(ln)
            f = midi(roots[k % 4])
            x = np.tanh(1.5 * np.sin(2 * np.pi * f * t)) * np.minimum(1, t / 0.01) * np.exp(-t * 1.2)
            x *= np.minimum(1, (ln - t) / 0.05)
            add(x * 0.16, tb + hit)
        # ドラム
        for b in range(4):
            bt = tb + b * beat
            if b in (0, 2):
                t = _t(0.35)
                f = 50 + 70 * np.exp(-t * 30)
                add(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9) * 0.32, bt)
            if b == 2:
                t = _t(0.3)
                f = 50 + 70 * np.exp(-t * 30)
                add(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 12) * 0.18, bt + beat * 0.5)
            if b in (1, 3):
                t = _t(0.25)
                x = bandpass(rng.standard_normal(len(t)), 900, 5000) * np.exp(-t * 18)
                x += np.sin(2 * np.pi * 190 * t) * np.exp(-t * 25) * 0.5
                add(x * 0.12, bt)
            for e in range(2):
                swing = 0.0 if e == 0 else beat * 0.58
                t = _t(0.06)
                x = highpass(rng.standard_normal(len(t)), 7000) * np.exp(-t * 70)
                add(x * (0.05 if e == 0 else 0.03), bt + swing)
        tb += bar
        k += 1

    # レコードのノイズ
    out += lowpass(rng.standard_normal(n), 3000) * 0.004
    clicks = np.zeros(n)
    idx = rng.integers(0, n, int(duration * 3))
    clicks[idx] = rng.uniform(0.05, 0.2, len(idx)) * rng.choice([-1, 1], len(idx))
    out += lowpass(clicks, 2500)
    out = lowpass(out, 4500)
    out = out[:int(duration * SR)]
    t = np.arange(len(out)) / SR
    out *= np.minimum(1, t / 1.0) * np.minimum(1, (duration - t) / 1.5)
    out /= np.max(np.abs(out)) + 1e-9
    return out.astype(np.float32)


def duck_envelope(n, intervals, depth_db=-8, ramp=0.15):
    """ナレーションが鳴っている区間 [(start, end), ...] で depth_db 下げるゲイン曲線。"""
    g = np.ones(n, np.float32)
    on = np.zeros(n, np.float32)
    for s, e in intervals:
        on[int(s * SR):int(e * SR)] = 1
    k = int(ramp * SR)
    on = np.convolve(on, np.ones(k) / k, mode="same")
    g = 1 - (1 - db(depth_db)) * np.clip(on, 0, 1)
    return g.astype(np.float32)


# ------------------------------------------------------------------ ニュース番組風
def sfx_jingle():
    """オープニングのジングル。明るい和音を駆け上がって最後に伸ばす。"""
    out = np.zeros(int(2.2 * SR))
    seq = [(0.00, [60, 64, 67]), (0.16, [62, 65, 69]), (0.32, [64, 67, 72]), (0.56, [65, 69, 72, 77])]
    for i, (st, notes) in enumerate(seq):
        last = i == len(seq) - 1
        ln = 1.6 if last else 0.3
        t = _t(ln)
        env = np.minimum(1, t / 0.008) * np.exp(-t * (1.8 if last else 9))
        for m in notes:
            f = midi(m + 12)
            ph = 2 * np.pi * f * t
            x = signal.sawtooth(ph) * 0.4 + np.sin(ph) * 0.6 + 0.2 * np.sin(2 * ph)
            s = int(st * SR)
            out[s:s + len(t)] += lowpass(x, 5000) * env * 0.12
    t = _t(0.5)  # ティンパニ風の低い一打
    out[:len(t)] += np.sin(2 * np.pi * (70 + 40 * np.exp(-t * 20)) * t) * np.exp(-t * 6) * 0.5
    return out.astype(np.float32)


def sfx_whoosh():
    """ニュースが切り替わるときの「シュッ」。"""
    t = _t(0.45)
    x = rng.standard_normal(len(t))
    out = np.zeros_like(x)
    # 周波数を上げていくバンドパスを短い区間ごとにかける
    seg = SR // 50
    for k in range(0, len(x), seg):
        u = k / len(x)
        fc = 400 + 5000 * u
        out[k:k + seg] = bandpass(x[k:k + seg + 200], fc * 0.6, fc * 1.4)[:len(out[k:k + seg])]
    env = np.sin(np.pi * np.minimum(1, t / 0.45)) ** 2
    return (out * env * 0.5).astype(np.float32)


SFX["jingle"] = sfx_jingle
SFX["whoosh"] = sfx_whoosh
SFX_GAIN["jingle"] = db(-2)
SFX_GAIN["whoosh"] = db(-8)


def bgm_news(duration, bpm=112):
    """ニュース番組風の BGM。4 つ打ち＋8 分音符のシンセ＋パッド。途中で無音にならない。"""
    beat = 60 / bpm
    bar = beat * 4
    n = int((duration + 1) * SR)
    out = np.zeros(n)
    chords = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]  # Am F C G
    roots = [45, 41, 36, 43]

    def add(x, start):
        s = int(start * SR)
        if s >= n:
            return
        e = min(n, s + len(x))
        out[s:e] += x[:e - s]

    k, tb = 0, 0.0
    while tb < duration + 1:
        ch = chords[k % 4]
        t = _t(bar + 0.2)
        penv = np.minimum(1, t / 0.2) * np.minimum(1, (bar + 0.2 - t) / 0.2)
        for m in ch:  # パッド
            f = midi(m)
            add((signal.sawtooth(2 * np.pi * f * t) * 0.3 + np.sin(2 * np.pi * f * 1.003 * t)) * penv * 0.03, tb)
        for e in range(8):  # 8 分音符のシンセ
            m = ch[[0, 1, 2, 1, 0, 2, 1, 2][e]] + 12
            t = _t(beat * 0.45)
            f = midi(m)
            x = (signal.square(2 * np.pi * f * t, 0.3) * 0.3 + np.sin(2 * np.pi * f * t)) * np.exp(-t * 14)
            add(lowpass(x, 3500) * 0.05, tb + e * beat / 2)
        for e in range(8):  # ベース
            t = _t(beat * 0.45)
            f = midi(roots[k % 4])
            x = np.tanh(2 * np.sin(2 * np.pi * f * t)) * np.minimum(1, t / 0.005) * np.exp(-t * 6)
            add(x * 0.12, tb + e * beat / 2)
        for b in range(4):  # 4 つ打ち＋ハイハット＋2・4 拍のクラップ
            bt = tb + b * beat
            t = _t(0.3)
            f = 48 + 80 * np.exp(-t * 35)
            add(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 11) * 0.28, bt)
            t = _t(0.05)
            add(highpass(rng.standard_normal(len(t)), 8000) * np.exp(-t * 80) * 0.05, bt + beat / 2)
            if b in (1, 3):
                t = _t(0.18)
                add(bandpass(rng.standard_normal(len(t)), 1000, 4000) * np.exp(-t * 25) * 0.1, bt)
        tb += bar
        k += 1
    out += lowpass(rng.standard_normal(n), 2000) * 0.002
    out = lowpass(out, 6000)[:int(duration * SR)]
    t = np.arange(len(out)) / SR
    out *= np.minimum(1, t / 0.5) * np.minimum(1, (duration - t) / 1.5)
    out /= np.max(np.abs(out)) + 1e-9
    return out.astype(np.float32)
