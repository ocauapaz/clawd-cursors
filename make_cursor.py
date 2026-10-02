"""Clawd cursor set: full Windows scheme (.cur/.ani + Install.inf) -> Clawd/ and Clawd.zip.

Everything is drawn as pixel art on a 64-cell grid, then scaled to each cursor size.
"""
import io
import math
import os
import shutil
import struct
from PIL import Image, ImageDraw, ImageFilter

G = 64  # grid cells per side
COLORS = {
    "O": (217, 119, 87, 255),
    "H": (240, 158, 124, 255),
    "S": (172, 82, 56, 255),
    "E": (22, 16, 14, 255),
    "W": (252, 244, 234, 255),
    "R": (222, 64, 52, 255),
    "r": (160, 36, 30, 255),
    "g": (150, 150, 160, 255),
    "P": (240, 150, 150, 255),
}
OUTLINE = (58, 28, 20, 255)
SHADOW = (0, 0, 0, 80)
SIZES = [32, 64, 128]

CLAWD = [
    ".HHHHHHHHHH.",
    ".OOEOOOOEOO.",
    ".OOEOOOOEOO.",
    "SOOOOOOOOOOS",
    ".OOOOOOOOOO.",
    ".SSSSSSSSSS.",
    "..S.S..S.S..",
    "..S.S..S.S..",
]
CLAWD_BLINK = [CLAWD[0], ".OOOOOOOOOO.", ".OEEOOOOEEO."] + CLAWD[3:]
CLAWD_WAVE = [
    "W...........",
    "H...........",
    "OHHHHHHHHHH.",
    "SOOEOOOOEOO.",
    ".OOEOOOOEOO.",
    ".OOOOOOOOOOS",
    ".OOOOOOOOOO.",
    ".SSSSSSSSSS.",
    "..S.S..S.S..",
    "..S.S..S.S..",
]
QMARK = [".OOO.", "OO.OO", "...OO", "..OO.", "..OO.", ".....", "..OO."]
SPARK_A = ["..O..", "..O..", "OOHOO", "..O..", "..O.."]
SPARK_B = ["O...O", ".O.O.", "..H..", ".O.O.", "O...O"]


# ---------- drawing primitives (all on the 64-cell grid) ----------

def canvas():
    return Image.new("RGBA", (G, G), (0, 0, 0, 0))


def stamp(img, sprite, x0, y0, scale):
    d = ImageDraw.Draw(img)
    for y, row in enumerate(sprite):
        for x, ch in enumerate(row):
            if ch in COLORS:
                px, py = x0 + x * scale, y0 + y * scale
                d.rectangle((px, py, px + scale - 1, py + scale - 1), fill=COLORS[ch])


def beveled(draw_fn, depth=2):
    """Draw a shape in one color on its own layer, then light its top-left and shade its bottom-right edge."""
    layer = canvas()
    draw_fn(ImageDraw.Draw(layer))
    a = layer.getchannel("A").load()
    inside = lambda x, y: 0 <= x < G and 0 <= y < G and a[x, y] > 0
    px = layer.load()
    for y in range(G):
        for x in range(G):
            if not inside(x, y):
                continue
            if any(not inside(x - k, y) or not inside(x, y - k) for k in range(1, depth + 1)):
                px[x, y] = COLORS["H"]
            elif any(not inside(x + k, y) or not inside(x, y + k) for k in range(1, depth + 1)):
                px[x, y] = COLORS["S"]
            else:
                px[x, y] = COLORS["O"]
    return layer


def rotated(pts, angle, cx, cy, k=1.0):
    a = math.radians(angle)
    return [(cx + k * (x * math.cos(a) - y * math.sin(a)), cy + k * (x * math.sin(a) + y * math.cos(a))) for x, y in pts]


DOUBLE = [(0, -12), (6, -5), (2, -5), (2, 5), (6, 5), (0, 12), (-6, 5), (-2, 5), (-2, -5), (-6, -5)]
CROSS = [(0, -12), (5, -7), (1.5, -7), (1.5, 7), (5, 7), (0, 12), (-5, 7), (-1.5, 7), (-1.5, -7), (-5, -7)]
SINGLE = [(0, -12), (7, -4), (2.5, -4), (2.5, 12), (-2.5, 12), (-2.5, -4), (-7, -4)]


def arrows(*angles, shape=DOUBLE, k=1.4):
    return beveled(lambda d: [d.polygon(rotated(shape, a, 32, 32, k), fill=COLORS["O"]) for a in angles])


def ibeam():
    def draw(d):
        d.rectangle((30, 19, 33, 44), fill=COLORS["O"])
        d.rectangle((24, 16, 39, 19), fill=COLORS["O"])
        d.rectangle((24, 44, 39, 47), fill=COLORS["O"])
    return beveled(draw)


def crosshair():
    def draw(d):
        for box in ((30, 16, 33, 26), (30, 37, 33, 47), (16, 30, 26, 33), (37, 30, 47, 33)):
            d.rectangle(box, fill=COLORS["O"])
    img = beveled(draw)
    ImageDraw.Draw(img).rectangle((31, 31, 32, 32), fill=COLORS["R"])
    return img


def pencil():
    """Pencil along the up-right diagonal, graphite tip at (5, 58)."""
    tip, ang = (14, 50), -45

    def seg(u0, u1, v0=4, v1=None):
        v1 = v0 if v1 is None else v1
        u0, u1, v0, v1 = u0 * 0.6, u1 * 0.6, v0 * 0.7, v1 * 0.7
        pts = [(u0, -v0), (u1, -v1), (u1, v1), (u0, v0)]
        return [(tip[0] + u * math.cos(math.radians(ang)) - v * math.sin(math.radians(ang)),
                 tip[1] + u * math.sin(math.radians(ang)) + v * math.cos(math.radians(ang))) for u, v in pts]

    img = beveled(lambda d: d.polygon(seg(12, 44), fill=COLORS["O"]))
    d = ImageDraw.Draw(img)
    d.polygon(seg(0, 12, 0, 4.5), fill=COLORS["W"])
    d.polygon(seg(0, 5, 0, 2), fill=COLORS["E"])
    d.polygon(seg(44, 49), fill=COLORS["g"])
    d.polygon(seg(49, 56), fill=COLORS["P"])
    return img


def bubble(img, cx=51, cy=51, r=11, fill="W"):
    ImageDraw.Draw(img).ellipse((cx - r, cy - r, cx + r, cy + r), fill=COLORS[fill])


def badge_help(img):
    bubble(img)
    stamp(img, QMARK, 46, 44, 2)


def badge_no(img):
    cx, cy, r = 51, 51, 11
    bubble(img, cx, cy, r)
    d = ImageDraw.Draw(img)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=COLORS["R"], width=4)
    d.line((cx - 7, cy - 7, cx + 7, cy + 7), fill=COLORS["R"], width=4)


def badge_pin(img):
    d = ImageDraw.Draw(img)
    d.polygon([(43, 50), (59, 50), (51, 62)], fill=COLORS["R"])
    d.ellipse((42, 36, 60, 54), fill=COLORS["R"])
    d.pieslice((42, 36, 60, 54), 90, 270, fill=COLORS["r"])
    d.ellipse((47, 41, 55, 49), fill=COLORS["W"])


def badge_person(img):
    bubble(img)
    d = ImageDraw.Draw(img)
    d.ellipse((47, 41, 55, 49), fill=COLORS["O"])
    d.pieslice((42, 51, 60, 67), 180, 360, fill=COLORS["O"])
    d.rectangle((40, 59, 62, 63), fill=(0, 0, 0, 0))


# ---------- cursor definitions ----------

def clawd(sprite=CLAWD, x=2, y=2, extra=None):
    img = canvas()
    stamp(img, sprite, x, y, 4)
    if extra:
        extra(img)
    return img


def over(base, top, at=(0, 0)):
    base.alpha_composite(top, at)
    return base


def mini(img, x=38, y=46):
    stamp(img, CLAWD, x, y, 2)
    return img


def build():
    spark = lambda img, s, x, y: stamp(img, s, x, y, 2)
    wait = [
        clawd(x=8, y=24, extra=lambda i: spark(i, SPARK_A, 44, 6)),
        clawd(x=8, y=18, extra=lambda i: spark(i, SPARK_B, 44, 6)),
        clawd(x=8, y=24, extra=lambda i: spark(i, SPARK_A, 44, 6)),
        clawd(CLAWD_BLINK, x=8, y=24, extra=lambda i: spark(i, SPARK_B, 44, 6)),
    ]
    starting = [clawd(extra=lambda i, s=s: spark(i, s, 44, 42)) for s in (SPARK_A, SPARK_B)]
    return {  # dict order = Windows scheme order
        "Arrow": ([clawd()], (6, 2), None),
        "Help": ([clawd(extra=badge_help)], (6, 2), None),
        "AppStarting": (starting, (6, 2), [12, 12]),
        "Wait": (wait, (32, 32), [10, 10, 10, 10]),
        "Crosshair": ([mini(crosshair(), 38, 42)], (32, 32), None),
        "IBeam": ([mini(ibeam(), 38, 42)], (32, 32), None),
        "NWPen": ([mini(pencil(), 34, 46)], (14, 50), None),
        "No": ([clawd(extra=badge_no)], (6, 2), None),
        "SizeNS": ([arrows(0)], (32, 32), None),
        "SizeWE": ([arrows(90)], (32, 32), None),
        "SizeNWSE": ([arrows(-45)], (32, 32), None),
        "SizeNESW": ([arrows(45)], (32, 32), None),
        "SizeAll": ([arrows(0, 90, shape=CROSS, k=1.5)], (32, 32), None),
        "UpArrow": ([arrows(0, shape=SINGLE)], (32, 15), None),
        "Hand": ([clawd(CLAWD_WAVE)], (2, 2), None),
        "Pin": ([clawd(extra=badge_pin)], (6, 2), None),
        "Person": ([clawd(extra=badge_person)], (6, 2), None),
    }


# ---------- output ----------

def finish(cells, size):
    """Scale the cell art to `size`, add a dark outline and a soft drop shadow."""
    img = cells.resize((size, size), Image.NEAREST if size >= G else Image.BOX)
    k = max(1, size // 64)
    alpha = img.getchannel("A").point(lambda v: 255 if v > 60 else 0).filter(ImageFilter.MaxFilter(2 * k + 1))
    shape = Image.new("RGBA", (size, size), OUTLINE)
    shape.putalpha(alpha)
    shape.alpha_composite(img)
    shadow = Image.new("RGBA", (size, size), SHADOW)
    shadow.putalpha(alpha.point(lambda v: v * SHADOW[3] // 255).filter(ImageFilter.GaussianBlur(k)))
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.alpha_composite(shadow, (k, k))
    out.alpha_composite(shape)
    return out


def cur_bytes(cells, hot):
    """ICO container with type=2 (cursor); hotspot stored in the planes/bitcount fields."""
    blobs = []
    for size in SIZES:
        buf = io.BytesIO()
        finish(cells, size).save(buf, "PNG")
        blobs.append((size, buf.getvalue()))
    offset = 6 + 16 * len(blobs)
    head, body = struct.pack("<HHH", 0, 2, len(blobs)), b""
    for size, data in blobs:
        hx, hy = (min(size - 1, round(h * size / G)) for h in hot)
        head += struct.pack("<BBBBHHII", size % 256, size % 256, 0, 0, hx, hy, len(data), offset)
        offset += len(data)
        body += data
    return head + body


def chunk(tag, data):
    return tag + struct.pack("<I", len(data)) + data + (b"\0" if len(data) % 2 else b"")


def ani_bytes(frames, hot, rates):
    n = len(frames)
    anih = struct.pack("<9I", 36, n, n, 0, 0, 0, 0, rates[0], 1)  # AF_ICON
    fram = b"fram" + b"".join(chunk(b"icon", cur_bytes(f, hot)) for f in frames)
    body = b"ACON" + chunk(b"anih", anih) + chunk(b"rate", struct.pack(f"<{n}I", *rates)) + chunk(b"LIST", fram)
    return b"RIFF" + struct.pack("<I", len(body)) + body


INF = r"""; Clawd cursor scheme - right-click > Install
[Version]
signature="$CHICAGO$"

[DefaultInstall]
CopyFiles = Scheme.Cur
AddReg    = Scheme.Reg, Wreg

[DefaultInstall.NT]
CopyFiles = Scheme.Cur
AddReg    = Scheme.Reg, Wreg

[DestinationDirs]
Scheme.Cur = 10,"%CUR_DIR%"

[Scheme.Reg]
HKCU,"Control Panel\Cursors\Schemes","%SCHEME_NAME%",,"{scheme}"

[Wreg]
HKCU,"Control Panel\Cursors",,0x00020000,"%SCHEME_NAME%"
{values}

[Scheme.Cur]
{files}

[Strings]
CUR_DIR     = "Cursors\Clawd"
SCHEME_NAME = "Clawd"
"""


def main():
    out = "Clawd"
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out)
    cursors = build()
    files = {}
    for name, (frames, hot, rates) in cursors.items():
        fname = f"clawd_{name.lower()}.{'ani' if rates else 'cur'}"
        data = ani_bytes(frames, hot, rates) if rates else cur_bytes(frames[0], hot)
        with open(os.path.join(out, fname), "wb") as f:
            f.write(data)
        files[name] = fname
    path = lambda fn: f"%10%\\%CUR_DIR%\\{fn}"
    inf = INF.format(
        scheme=",".join(path(files[n]) for n in cursors),
        values="\n".join(f'HKCU,"Control Panel\\Cursors",{n},0x00020000,"{path(fn)}"' for n, fn in files.items()),
        files="\n".join(files.values()),
    )
    with open(os.path.join(out, "Install.inf"), "w", newline="\r\n") as f:
        f.write(inf)

    # preview: every cursor at 64px (top) and 32px (bottom), light and dark backgrounds
    names = list(cursors)
    cols, cw = 9, 84
    rows = math.ceil(len(names) / cols)
    prev = Image.new("RGBA", (cols * cw + 10, rows * 200), (245, 240, 232, 255))
    for i, n in enumerate(names):
        x, y = 10 + (i % cols) * cw, (i // cols) * 200
        prev.alpha_composite(Image.new("RGBA", (cw, 100), (30, 30, 34, 255)), (x - 10, y + 100))
        for dy in (0, 100):
            prev.alpha_composite(finish(cursors[n][0][0], 64), (x, y + dy + 4))
            prev.alpha_composite(finish(cursors[n][0][0], 32), (x + 16, y + dy + 68))
    prev.save("preview.png")

    shutil.make_archive("Clawd", "zip", ".", out)
    assert open(os.path.join(out, files["Wait"]), "rb").read(4) == b"RIFF"
    assert len(files) == 17
    print("ok", len(files))


if __name__ == "__main__":
    main()
