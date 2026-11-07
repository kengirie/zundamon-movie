"""Pillow でフレームを描く。"""
import json
import math
import os
import re
from functools import lru_cache

import numpy as np
from fontTools.ttLib import TTCollection
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
SAFE_R = W - 150          # 右 150px は Shorts のボタン列
SAFE_B = H - 380          # 下 380px は Shorts の説明文など
X0, X1 = 70, SAFE_R - 10  # 文字を置く左右の範囲
CX = (X0 + X1) // 2

BG_TOP = (12, 20, 48)
BG_BOT = (20, 32, 72)
COLORS = {
    "w": (245, 247, 255), "y": (255, 216, 77), "c": (92, 214, 255), "p": (255, 111, 174),
    "g": (91, 227, 125), "r": (255, 90, 90), "m": (150, 162, 200),
}
FONT_DIR = "/usr/share/fonts/opentype/noto"
FONT_FILES = {False: f"{FONT_DIR}/NotoSansCJK-Medium.ttc", True: f"{FONT_DIR}/NotoSansCJK-Bold.ttc"}
if not os.path.exists(FONT_FILES[False]):
    FONT_FILES[False] = f"{FONT_DIR}/NotoSansCJK-Regular.ttc"

# ---------------------------------------------------------------- 立ち絵の配置
TACHIE_SCALE = 0.56
TACHIE_X = 618            # 体の右端が x≈920（ボタン列の手前）に来る位置
TACHIE_BOTTOM_OVERHANG = 60  # 足元は画面の下に少しはみ出してよい


def _jp_index(path):
    """TTC の中から「Noto Sans CJK JP」の番号を探す。"""
    for i, f in enumerate(TTCollection(path).fonts):
        if "JP" in f["name"].getDebugName(1):
            return i
    return 0


_IDX = {b: _jp_index(p) for b, p in FONT_FILES.items()}
_CMAP = TTCollection(FONT_FILES[True]).fonts[_IDX[True]].getBestCmap()


@lru_cache(None)
def font(size, bold=False):
    return ImageFont.truetype(FONT_FILES[bold], size, index=_IDX[bold])


def missing_glyphs(text):
    return sorted({ch for ch in text if ch not in "\n" and ord(ch) not in _CMAP})


# ---------------------------------------------------------------- リッチテキスト
def parse(text, default="w"):
    """'[y]黄[/]と白' → 行ごとの [(文字, 色)]"""
    lines = []
    for raw in text.split("\n"):
        segs, color, pos = [], default, 0
        for m in re.finditer(r"\[(\w)\]|\[/\]", raw):
            if m.start() > pos:
                segs.append((raw[pos:m.start()], color))
            color = m.group(1) if m.group(1) else default
            pos = m.end()
        if pos < len(raw):
            segs.append((raw[pos:], color))
        lines.append(segs)
    return lines


def plain(text):
    return re.sub(r"\[(\w)\]|\[/\]", "", text)


def draw_rich(lines, size, bold=False, align="center", line_gap=1.25, shadow=True):
    """リッチテキストを透明画像に描いて返す。"""
    f = font(size, bold)
    widths = [sum(f.getlength(s) for s, _ in segs) for segs in lines]
    lh = int(size * line_gap)
    w = int(max(widths) + size * 0.2) + 8
    h = lh * (len(lines) - 1) + int(size * 1.35) + 8
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for li, segs in enumerate(lines):
        x = 4 if align == "left" else (w - widths[li]) / 2
        y = 4 + li * lh
        for s, c in segs:
            if shadow:
                d.text((x + 3, y + 4), s, font=f, fill=(0, 0, 0, 140))
            d.text((x, y), s, font=f, fill=COLORS[c])
            x += f.getlength(s)
    return im


# ---------------------------------------------------------------- 要素ごとの画像
def rounded_box(w, h, border, fill=(32, 46, 96, 235), r=28, bw=5):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], r, fill=fill, outline=COLORS[border] + (255,), width=bw)
    return im


def icon_key(size, color):
    s = size
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = COLORS[color]
    lw = max(4, s // 10)
    d.ellipse([s * 0.05, s * 0.3, s * 0.45, s * 0.7], outline=c, width=lw)
    d.line([s * 0.43, s * 0.5, s * 0.95, s * 0.5], fill=c, width=lw)
    d.line([s * 0.8, s * 0.5, s * 0.8, s * 0.72], fill=c, width=lw)
    d.line([s * 0.66, s * 0.5, s * 0.66, s * 0.66], fill=c, width=lw)
    return im


def icon_check(size):
    s = size
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([0, 0, s - 1, s - 1], fill=COLORS["g"])
    d.line([s * 0.25, s * 0.52, s * 0.43, s * 0.7, s * 0.76, s * 0.32], fill=(20, 40, 30), width=max(4, s // 9), joint="curve")
    return im


def make_layer(it):
    """要素を描いた画像と、画面上の左上座標を返す（最終状態）。"""
    k = it["kind"]
    if k == "text":
        im = draw_rich(parse(it["text"], it["color"]), it["size"], it["bold"], it["align"])
        x = it["x"] if it["align"] == "left" and it["x"] is not None else CX - im.width // 2
        return im, (x, it["y"])
    if k == "card":
        w, h = X1 - X0, it["h"]
        im = rounded_box(w, h, it["border"])
        txt = draw_rich(parse("\n".join(it["lines"])), it["size"], False,
                        "left" if it["icon"] else "center", line_gap=1.3)
        avail = w - 60 - ((40 + int(it["size"] * 1.3) + 20) if it["icon"] else 0)
        it["overflow"] = txt.width > avail
        if it["icon"]:
            ic = icon_key(int(it["size"] * 1.3), "c") if it["icon"] == "key" else icon_check(int(it["size"] * 1.1))
            im.alpha_composite(ic, (30, (h - ic.height) // 2))
            im.alpha_composite(txt, (40 + ic.width + 20, (h - txt.height) // 2))
        else:
            im.alpha_composite(txt, ((w - txt.width) // 2, (h - txt.height) // 2))
        return im, (X0, it["y"])
    if k == "counter":
        im = counter_img(it, it["n"])
        return im, (CX - im.width // 2, it["y"])
    if k == "strike":
        im = draw_rich(parse(it["text"], "m"), it["size"])
        return im, (it["x"], it["y"])
    if k == "fig":
        im = FIGS[it["name"]](it["stage"], it["h"], 0.0)
        return im, (X0, it["y"])
    raise ValueError(k)


def counter_img(it, v):
    return draw_rich(parse(f"{it['prefix']}[{it['color']}]{v}[/]{it['suffix']}"), it["size"], True)


# ---------------------------------------------------------------- 図：リレー
def fig_relays(stage, h, t):
    """stage1: あなた→リレー→みんな / stage2: リレー3つ / stage3: 1つ落ちる"""
    w = X1 - X0
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx = w // 2
    you = (cx, 80)
    fol = (cx, h - 110)
    xs = [cx] if stage == 1 else [cx - 270, cx, cx + 270]
    ry = h // 2 - 20
    dead = 1 if stage == 3 else None
    f_lab = font(40, True)

    def arrow(p, q, color, width=6):
        d.line([p, q], fill=color, width=width)
        ang = math.atan2(q[1] - p[1], q[0] - p[0])
        for s in (-1, 1):
            a = ang + math.pi + s * 0.45
            d.line([q, (q[0] + 26 * math.cos(a), q[1] + 26 * math.sin(a))], fill=color, width=width)

    def packets(p, q, color):
        for k in range(2):
            u = (t * 0.9 + k * 0.5) % 1.0
            x = p[0] + (q[0] - p[0]) * u
            y = p[1] + (q[1] - p[1]) * u
            d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=color)

    for i, x in enumerate(xs):
        ok = (i != dead)
        col = COLORS["w"] + (230,) if ok else (90, 100, 130, 255)
        p1, q1 = (you[0], you[1] + 75), (x, ry - 62)
        p2, q2 = (x, ry + 62), (fol[0], fol[1] - 78)
        arrow(p1, q1, col)
        arrow(p2, q2, col)
        if ok:
            packets(p1, q1, COLORS["y"])
            packets(p2, q2, COLORS["y"])
    for i, x in enumerate(xs):
        ok = (i != dead)
        bw, bh = 220, 110
        box = [x - bw // 2, ry - bh // 2, x + bw // 2, ry + bh // 2]
        d.rounded_rectangle(box, 20, fill=(32, 46, 96, 255),
                            outline=(COLORS["y"] if ok else (90, 100, 130)) + (255,), width=5)
        name = "リレー" if stage == 1 else f"リレー{'ABC'[i]}"
        tw = f_lab.getlength(name)
        d.text((x - tw / 2, ry - 30), name, font=f_lab, fill=COLORS["y"] if ok else (110, 118, 150))
        if not ok:
            for s in (-1, 1):
                d.line([x - 70, ry - 70 * s, x + 70, ry + 70 * s], fill=COLORS["r"], width=14)
    for (px, py), label, col in [(you, "あなた", "p"), (fol, "みんな", "g")]:
        d.ellipse([px - 75, py - 75, px + 75, py + 75], fill=(32, 46, 96, 255), outline=COLORS[col], width=6)
        tw = f_lab.getlength(label)
        d.text((px - tw / 2, py - 30), label, font=f_lab, fill=COLORS["w"])
    return im


FIGS = {"relays": fig_relays}


# ---------------------------------------------------------------- 固定部分
@lru_cache(None)
def background():
    y = np.linspace(0, 1, H)[:, None, None]
    top, bot = np.array(BG_TOP), np.array(BG_BOT)
    arr = (top * (1 - y) + bot * y).repeat(W, axis=1).astype(np.uint8)
    im = Image.fromarray(arr, "RGB").convert("RGBA")
    d = ImageDraw.Draw(im)
    for gy in range(0, H, 60):
        for gx in range(0, W, 60):
            d.point((gx, gy), fill=(60, 80, 140, 255))
    return im


@lru_cache(None)
def credit_img(text):
    lines = text.split("\n")
    f = font(24)
    w = int(max(f.getlength(l) for l in lines)) + 8
    im = Image.new("RGBA", (w, 34 * len(lines) + 6), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, l in enumerate(lines):
        d.text((w - f.getlength(l) - 4, 2 + i * 34), l, font=f, fill=(200, 208, 235, 230))
    return im


@lru_cache(None)
def chip_img(n, total):
    f = font(36, True)
    s = f"{n} / {total}"
    w = int(f.getlength(s)) + 48
    im = Image.new("RGBA", (w, 60), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, 59], 30, fill=(255, 216, 77, 255))
    d.text((24, 4), s, font=f, fill=(20, 28, 60))
    return im


@lru_cache(None)
def title_img(text):
    return draw_rich(parse(text), 78, True)


# ---------------------------------------------------------------- 立ち絵
class Tachie:
    def __init__(self, folder):
        self.imgs = {}
        for k in ("open", "half", "closed"):
            im = Image.open(os.path.join(folder, f"{k}.png")).convert("RGBA")
            self.imgs[k] = im.resize((int(im.width * TACHIE_SCALE), int(im.height * TACHIE_SCALE)), Image.LANCZOS)
        self.w, self.h = self.imgs["open"].size
        meta = json.load(open(os.path.join(folder, "meta.json")))
        self.mouth = [int(v * TACHIE_SCALE) for v in meta["mouth"]]  # 縮小後の口の位置 x,y,w,h
        self.y = H - self.h + TACHIE_BOTTOM_OVERHANG

    def pos(self, gt, jumps, enter_t):
        dy = 6 * math.sin(2 * math.pi * gt / 3.2)  # 呼吸
        for jt in jumps:
            u = (gt - jt) / 0.42
            if 0 <= u <= 1:
                dy -= 80 * math.sin(math.pi * u)
        if enter_t is not None:  # 下から登場
            u = (gt - enter_t) / 0.7
            if u < 1:
                dy += (1 - ease_out(max(0.0, u))) * (self.h + 100)
        return TACHIE_X, int(self.y + dy)

    def mask_at(self, x, y):
        """画面全体での立ち絵のアルファ（検査用）"""
        m = Image.new("L", (W, H), 0)
        m.paste(self.imgs["open"].getchannel("A"), (x, y))
        return np.array(m) > 40


# ---------------------------------------------------------------- 1 コマの合成
def ease_out(u):
    return 1 - (1 - u) ** 3


def back_out(u):
    c = 1.7
    return 1 + (c + 1) * (u - 1) ** 3 + c * (u - 1) ** 2


def place(frame, im, xy, alpha=1.0, scale=1.0, dy=0):
    if alpha <= 0:
        return
    if scale != 1.0:
        nw, nh = max(1, int(im.width * scale)), max(1, int(im.height * scale))
        cx, cy = xy[0] + im.width / 2, xy[1] + im.height / 2
        im = im.resize((nw, nh), Image.BILINEAR)
        xy = (cx - nw / 2, cy - nh / 2)
    if alpha < 1.0:
        im = im.copy()
        im.putalpha(Image.eval(im.getchannel("A"), lambda a: int(a * alpha)))
    frame.alpha_composite(im, (int(xy[0]), int(xy[1] + dy)))


def compose(scene, t, gt, total, tachie, mouth, jumps, enter_t, credit, nchips):
    """scene: 計算済みシーン, t: シーン内時刻, gt: 全体時刻"""
    fr = background().copy()
    d = ImageDraw.Draw(fr)
    # 進行バー
    d.rectangle([0, 0, W, 12], fill=(40, 52, 96))
    d.rectangle([0, 0, int(W * min(1, gt / total)), 12], fill=COLORS["y"])
    if scene["chip"]:
        fr.alpha_composite(chip_img(scene["chip"], nchips), (X0, 44))
    cr = credit_img(credit)
    fr.alpha_composite(cr, (W - cr.width - 24, 34))
    if scene["title"]:
        u = min(1, t / 0.3)
        place(fr, title_img(scene["title"]), (CX - title_img(scene["title"]).width // 2, 128),
              alpha=u, dy=(1 - ease_out(u)) * 30)

    # 同じ名前の図は最後に出たものだけ表示
    latest_fig = {}
    for it in scene["items"]:
        if it["kind"] == "fig" and t >= it["t"]:
            latest_fig[it["name"]] = it
    for it in scene["items"]:
        if t < it["t"]:
            continue
        u = min(1, (t - it["t"]) / 0.3)
        im, xy = it["layer"], it["xy"]
        if it["kind"] == "fig":
            if latest_fig[it["name"]] is not it:
                continue
            im = FIGS[it["name"]](it["stage"], it["h"], t)
            place(fr, im, xy, alpha=1.0 if it["stage"] > 1 else u)
            continue
        if it["kind"] == "counter":
            v = int(round(it["n"] * ease_out(min(1, (t - it["t"]) / 0.8))))
            im = counter_img(it, v)
            xy = (CX - im.width // 2, it["y"])
        if it["kind"] == "strike":
            place(fr, im, xy)
            p = min(1, max(0, (t - it["t"]) / 0.3))
            x0, y0 = xy[0] + 6, xy[1] + im.height * 0.5
            d.line([x0, y0, x0 + (im.width - 12) * p, y0], fill=COLORS["r"], width=10)
            continue
        if it["anim"] == "pop":
            place(fr, im, xy, alpha=min(1, u * 2), scale=0.6 + 0.4 * back_out(u))
        else:
            place(fr, im, xy, alpha=u, dy=(1 - ease_out(u)) * 30)

    x, y = tachie.pos(gt, jumps, enter_t)
    if y < H:
        fr.alpha_composite(tachie.imgs[mouth], (x, y))
    return fr
