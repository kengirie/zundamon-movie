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
# 白い帯の上で使う濃い色（ニュースの見出し用）
COLORS_ON_WHITE = {
    "w": (20, 28, 60), "y": (196, 110, 0), "c": (0, 120, 190), "p": (214, 40, 120),
    "g": (20, 150, 60), "r": (210, 40, 40), "m": (100, 110, 140),
}
THEME = {}  # make_video.py がプロジェクトの THEME を入れる。style="news" でニュース番組風
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


def draw_rich(lines, size, bold=False, align="center", line_gap=1.25, shadow=True, palette=None):
    """リッチテキストを透明画像に描いて返す。"""
    pal = palette or COLORS
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
            d.text((x, y), s, font=f, fill=pal[c])
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
    num = f"{v:,}" if it.get("comma") else str(v)
    return draw_rich(parse(f"{it['prefix']}[{it['color']}]{num}[/]{it['suffix']}"), it["size"], True)


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


def fig_phone_flow(stage, h, t):
    """stage1: リレーから目次 / 2: Blossom から実体 / 3: 指紋チェック / 4: スマホ内で表示"""
    w = X1 - X0
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    dim = (90, 100, 130)
    f_big, f_mid, f_small = font(44, True), font(32), font(24)

    def ctext(x, y, s, f, fill):
        d.text((x - f.getlength(s) / 2, y), s, font=f, fill=fill)

    def arrow(p, q, color, width=6):
        d.line([p, q], fill=color, width=width)
        ang = math.atan2(q[1] - p[1], q[0] - p[0])
        for sg in (-1, 1):
            a = ang + math.pi + sg * 0.45
            d.line([q, (q[0] + 24 * math.cos(a), q[1] + 24 * math.sin(a))], fill=color, width=width)

    def packets(p, q, color):
        for k in range(2):
            u = (t * 0.9 + k * 0.5) % 1.0
            x, y = p[0] + (q[0] - p[0]) * u, p[1] + (q[1] - p[1]) * u
            d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=color)

    # 上の 2 つの置き場所
    srcs = [(200, "リレー", "目次", "y", 1), (650, "Blossom", "実体（ファイル）", "c", 2)]
    px, py, pw, ph = w // 2, 280, 270, 400  # スマホ（上端中央の座標）
    for x, name, sub, col, st in srcs:
        on = stage >= st
        c = COLORS[col] if on else dim
        d.rounded_rectangle([x - 160, 10, x + 160, 160], 22, fill=(32, 46, 96, 255), outline=c, width=5)
        ctext(x, 30, name, f_big, c)
        ctext(x, 95, sub, f_mid, COLORS["w"] if on else dim)
        p, q = (x, 168), (px + (-70 if st == 1 else 70), py - 8)
        arrow(p, q, (COLORS["w"] + (230,)) if on else dim)
        if on and stage <= 2:
            packets(p, q, c)
    # スマホ
    d.rounded_rectangle([px - pw // 2, py, px + pw // 2, py + ph], 36, fill=(18, 24, 50, 255),
                        outline=COLORS["w"], width=6)
    sx0, sy0, sx1, sy1 = px - pw // 2 + 18, py + 40, px + pw // 2 - 18, py + ph - 40
    d.rounded_rectangle([sx0, sy0, sx1, sy1], 12, fill=(40, 54, 104, 255))
    if stage in (1, 2):
        for k, line in enumerate(["/index.html", "/style.css", "/logo.png"]):
            d.text((sx0 + 14, sy0 + 16 + k * 36), line, font=f_small, fill=COLORS["y"])
        if stage == 2:
            for k in range(3):
                x0 = sx0 + 20 + k * 70
                d.rectangle([x0, sy0 + 150, x0 + 50, sy0 + 210], outline=COLORS["c"], width=4)
                d.line([x0 + 10, sy0 + 170, x0 + 40, sy0 + 170], fill=COLORS["c"], width=3)
                d.line([x0 + 10, sy0 + 185, x0 + 40, sy0 + 185], fill=COLORS["c"], width=3)
    elif stage == 3:
        cx, cy, r = px, sy0 + 120, 70
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=COLORS["g"])
        d.line([cx - 35, cy + 2, cx - 8, cy + 30, cx + 38, cy - 28], fill=(20, 40, 30), width=14, joint="curve")
        ctext(px, sy0 + 210, "指紋OK", f_mid, COLORS["g"])
    else:  # 組み立てたサイト
        d.rectangle([sx0, sy0, sx1, sy0 + 50], fill=COLORS["p"])
        d.rectangle([sx0 + 20, sy0 + 70, sx1 - 20, sy0 + 170], fill=(92, 214, 255, 255))
        for k in range(3):
            d.line([sx0 + 20, sy0 + 195 + k * 26, sx1 - 20 - k * 40, sy0 + 195 + k * 26], fill=COLORS["w"], width=8)
    # 下のキャプション
    caps = {1: ("① 目次をもらう", "y"), 2: ("② 実体を集める", "c"),
            3: ("③ 指紋で本物か確認", "g"), 4: ("④ スマホ内で組み立て表示", "p")}
    s, col = caps[stage]
    ctext(w // 2, py + ph + 24, s, font(50, True), COLORS[col])
    return im


FIGS = {"relays": fig_relays, "phone_flow": fig_phone_flow}


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


# ---------------------------------------------------------------- ニュース番組風の部品
def is_news():
    return THEME.get("style") == "news"


def title_y():
    return 172 if is_news() else 128


@lru_cache(None)
def logo_img(program):
    f = font(40, True)
    w = int(f.getlength(program)) + 56
    im = Image.new("RGBA", (w, 66), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, 65], 14, fill=(96, 176, 56, 255))
    d.rectangle([0, 58, w - 1, 65], fill=COLORS["y"])
    d.text((28, 2), program, font=f, fill=(255, 255, 255))
    return im


TICKER_Y, TICKER_H = 98, 52


@lru_cache(None)
def ticker_img(text):
    f = font(32, True)
    w = int(f.getlength(text)) + 40
    im = Image.new("RGBA", (w, TICKER_H), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((0, 4), text, font=f, fill=COLORS["y"])
    return im


@lru_cache(None)
def ticker_label(text):
    f = font(30, True)
    w = int(f.getlength(text)) + 40
    im = Image.new("RGBA", (w + 16, TICKER_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(0, 0), (w, 0), (w + 16, TICKER_H // 2), (w, TICKER_H), (0, TICKER_H)], fill=(220, 40, 60))
    d.text((20, 5), text, font=f, fill=(255, 255, 255))
    return im


@lru_cache(None)
def news_badge(no, total, cat, cat_color):
    f = font(34, True)
    a = f"NEWS {no} / {total}"
    wa = int(f.getlength(a)) + 44
    wc = int(f.getlength(cat)) + 44
    im = Image.new("RGBA", (wa + 16 + wc, 60), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, wa - 1, 59], 12, fill=(220, 40, 60))
    d.text((22, 4), a, font=f, fill=(255, 255, 255))
    d.rounded_rectangle([wa + 16, 0, wa + 16 + wc - 1, 59], 12, outline=COLORS[cat_color], width=4,
                        fill=(20, 30, 70))
    d.text((wa + 16 + 22, 4), cat, font=f, fill=COLORS[cat_color])
    return im


@lru_cache(None)
def headline_img(text, cat_color):
    """テレビのテロップ風の白い見出し帯。"""
    txt = draw_rich(parse(text), 52, True, "left", line_gap=1.3, shadow=False, palette=COLORS_ON_WHITE)
    w, h = X1 - X0, txt.height + 36
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([8, 8, w - 1, h - 1], fill=(0, 0, 0, 110))
    d.rectangle([0, 0, w - 9, h - 9], fill=(244, 246, 252))
    d.rectangle([0, 0, 16, h - 9], fill=COLORS[cat_color])
    im.alpha_composite(txt, (36, (h - 8 - txt.height) // 2))
    return im


@lru_cache(None)
def source_img(text):
    txt = draw_rich(parse(text, "m"), 32, False, "left", line_gap=1.35, shadow=False)
    w, h = max(440, txt.width + 40), txt.height + 28
    im = rounded_box(w, h, "m", fill=(10, 16, 40, 220), r=16, bw=2)
    im.alpha_composite(txt, (20, 14))
    return im


def static_elements(scene, nchips):
    """シーンに固定で出る要素 [(名前, 画像, 座標)]。描画と検査の両方で使う。"""
    els = []
    if is_news() and scene.get("news_no"):
        els.append(("NEWSバッジ", news_badge(scene["news_no"], nchips, scene["category"], scene["cat_color"]),
                    (X0, 172)))
        els.append(("見出し", headline_img(scene["headline"], scene["cat_color"]), (X0, 246)))
        els.append(("出典", source_img(scene["source"]), (X0, 1190)))
    elif scene.get("chip"):
        els.append(("チップ", chip_img(scene["chip"], nchips), (X0, 44)))
    if scene.get("title"):
        im = title_img(scene["title"])
        els.append(("タイトル", im, (CX - im.width // 2, title_y())))
    return els


def draw_header(fr, gt, total, credit):
    d = ImageDraw.Draw(fr)
    if is_news():
        fr.alpha_composite(logo_img(THEME["program"]), (20, 22))
        d.rectangle([0, TICKER_Y, W, TICKER_Y + TICKER_H], fill=(6, 10, 28))
        tk = ticker_img(THEME["ticker"])
        x = 200 - int(gt * 150) % tk.width
        while x < W:
            fr.alpha_composite(tk, (x, TICKER_Y + 4))
            x += tk.width
        fr.alpha_composite(ticker_label(THEME["date_short"]), (0, TICKER_Y))
        d.line([0, TICKER_Y, W, TICKER_Y], fill=COLORS["y"], width=2)
        d.line([0, TICKER_Y + TICKER_H, W, TICKER_Y + TICKER_H], fill=COLORS["y"], width=2)
    d.rectangle([0, 0, W, 12], fill=(40, 52, 96))
    d.rectangle([0, 0, int(W * min(1, gt / total)), 12], fill=COLORS["y"])
    cr = credit_img(credit)
    fr.alpha_composite(cr, (W - cr.width - 24, 22 if is_news() else 34))


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
    draw_header(fr, gt, total, credit)
    for k, (_, im, xy) in enumerate(static_elements(scene, nchips)):
        u = min(1, max(0, (t - 0.08 * k) / 0.3))
        if is_news() and scene.get("news_no"):  # 見出し帯は左からスライドイン
            place(fr, im, (xy[0] - (1 - ease_out(u)) * 120, xy[1]), alpha=u)
        else:
            place(fr, im, xy, alpha=u, dy=(1 - ease_out(u)) * 30)

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
