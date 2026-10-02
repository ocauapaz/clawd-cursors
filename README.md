# Clawd Cursors

A full Windows cursor scheme featuring Clawd, the pixel-art pet from Claude Code.

![preview](preview.png)

17 cursors (normal, help, text, link, animated busy, resize, and more) at 32, 64 and 128 px.

## Install

1. Download `Clawd.zip` from [Releases](../../releases) and extract it.
2. Right-click `Install.inf` and choose **Install** (on Windows 11 it may be under **Show more options**).
3. `Win+R` → `main.cpl` → **Pointers** tab → pick the **Clawd** scheme → **Apply**.

## Rebuild

```bash
pip install pillow
python make_cursor.py
```

Generates the `Clawd/` folder, `Clawd.zip` and `preview.png`.

---

Fan-made project, not affiliated with Anthropic. Claude and Clawd belong to Anthropic.
