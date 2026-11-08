"""ずんだもんの立ち絵を口パク用の 3 枚（open / half / closed）に分ける。

使い方:
  # 立ち絵画像から作る（背景つきでも可）。口の位置は x,y,w,h（元画像のピクセル、口の線を含む）
  python -m zmovie.tachie --image assets/source/zundamon_sakamoto_ahiru.png --mouth 464,474,64,62

出力先: assets/tachie/{open,half,closed}.png と meta.json（口の位置）
元画像: assets/source/zundamon_sakamoto_ahiru.png（坂本アヒル氏作。出典は README を参照）
"""
import argparse
import json
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "tachie")


# ---------------------------------------------------------------- 実画像から
def remove_background(img, tol=40):
    """四隅とつながっている背景色の領域を透明にする（背景つき画像用）。"""
    rgba = np.array(img.convert("RGBA"))
    if (rgba[..., 3] < 250).mean() > 0.05:
        return rgba  # すでに透過している
    rgb = rgba[..., :3].astype(int)
    h, w = rgb.shape[:2]
    corners = [rgb[0, 0], rgb[0, -1], rgb[-1, 0], rgb[-1, -1]]
    bg = np.zeros((h, w), bool)
    for c in corners:
        close = np.abs(rgb - c).sum(-1) < tol
        lab, _ = ndimage.label(close)
        for yx in [(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)]:
            if lab[yx]:
                bg |= lab == lab[yx]
    alpha = np.where(bg, 0, 255).astype(np.uint8)
    alpha = np.array(Image.fromarray(alpha).filter(ImageFilter.GaussianBlur(1)))
    rgba[..., 3] = np.minimum(rgba[..., 3], alpha)
    return rgba


def keep_largest(rgba):
    """他の絵と重なって写っている場合に備え、いちばん大きな塊だけ残す。"""
    mask = rgba[..., 3] > 20
    lab, n = ndimage.label(mask)
    if n > 1:
        sizes = ndimage.sum(mask, lab, range(1, n + 1))
        keep = lab == (int(np.argmax(sizes)) + 1)
        keep = ndimage.binary_dilation(keep, iterations=2)
        rgba[..., 3] = np.where(keep, rgba[..., 3], 0)
    ys, xs = np.nonzero(rgba[..., 3] > 20)
    return rgba[ys.min():ys.max() + 1, xs.min():xs.max() + 1], (xs.min(), ys.min())


def mouth_variants(open_img, box, lip=13):
    """元の絵（開き）から半開き・閉じを作る。box = (x, y, w, h)、口の線を含む範囲。

    半開き: 口を縦 55% に縮める（上くちびるの位置は固定）。
    閉じ  : 口の中を肌色で塗り、上くちびるの線（上から lip px）だけ残す。
    """
    x, y, w, h = box
    arr = np.array(open_img)
    skin = tuple(int(v) for v in np.median(
        arr[max(0, y - 10):y - 2, x:x + w].reshape(-1, 4), axis=0))
    region = Image.fromarray(arr[y:y + h, x:x + w])

    def blank():
        im = open_img.copy()
        ImageDraw.Draw(im).rectangle([x, y, x + w - 1, y + h - 1], fill=skin)
        return im

    half = blank()
    hh = max(lip + 2, int(h * 0.55))
    half.alpha_composite(region.resize((w, hh), Image.LANCZOS), (x, y))

    closed = blank()
    # 各列で、上から最初に出てくる濃い線（上くちびる）だけを残す
    reg = np.array(region)
    dark = reg[..., :3].astype(int).sum(-1) < 330
    keep = np.zeros_like(dark)
    for cx in range(w):
        col = np.nonzero(dark[:lip, cx])[0]
        if len(col):
            top = col[0]
            k = top
            while k < h and dark[k, cx] and k - top < 7:
                keep[k, cx] = True
                k += 1
    line = np.zeros_like(reg)
    line[keep] = reg[keep]
    closed.alpha_composite(Image.fromarray(line).filter(ImageFilter.SMOOTH), (x, y))
    return half, closed


def from_image(path, mouth):
    img = Image.open(path)
    rgba = remove_background(img)
    rgba, (ox, oy) = keep_largest(rgba)
    base = Image.fromarray(rgba)
    mx, my, mw, mh = mouth
    box = (int(mx - ox), int(my - oy), mw, mh)
    half, closed = mouth_variants(base, box)
    return (base, half, closed), box


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--mouth", required=True, help="x,y,w,h（元画像のピクセル、口の線を含む範囲）")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    imgs, box = from_image(a.image, [int(v) for v in a.mouth.split(",")])
    src = os.path.basename(a.image)
    for name, im in zip(("open", "half", "closed"), imgs):
        im.save(os.path.join(OUT, f"{name}.png"))
    with open(os.path.join(OUT, "meta.json"), "w") as f:
        json.dump(dict(source=src, size=imgs[0].size, mouth=box), f)
    print("saved", OUT, imgs[0].size)


if __name__ == "__main__":
    main()
