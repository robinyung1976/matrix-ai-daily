#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
矩阵AI日报 · 赛博风电子期刊渲染器
输入：结构化 JSON（见 render_issue 的 data 说明）
输出：PNG 长图（手机可直接长按保存转发）
兼容：GitHub Actions (Ubuntu, fonts-noto-cjk) / macOS 本地
"""

import os
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ---------------- 字体自适应 ----------------
FONT_CANDIDATES = {
    "cn": [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",   # Ubuntu fonts-noto-cjk
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",               # macOS
        "/System/Library/Fonts/PingFang.ttc",
    ],
    "mono": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",      # Ubuntu 自带
        "/System/Library/Fonts/Menlo.ttc",                          # macOS
    ],
}


def _find_font(candidates):
    for p in candidates:
        if os.path.exists(p):
            return p
    # 兜底：让 PIL 返回默认字体（仅英文）
    return None


CN_FONT_PATH = _find_font(FONT_CANDIDATES["cn"])
MONO_FONT_PATH = _find_font(FONT_CANDIDATES["mono"])

_font_cache = {}


def font(size, bold=False):
    key = (size, bold, CN_FONT_PATH)
    if key in _font_cache:
        return _font_cache[key]
    if CN_FONT_PATH:
        f = ImageFont.truetype(CN_FONT_PATH, size)
    else:
        f = ImageFont.load_default()
    _font_cache[key] = f
    return f


def mono(size):
    key = ("m", size, MONO_FONT_PATH)
    if key in _font_cache:
        return _font_cache[key]
    if MONO_FONT_PATH:
        f = ImageFont.truetype(MONO_FONT_PATH, size)
    else:
        f = ImageFont.load_default()
    _font_cache[key] = f
    return f


# ---------------- 配色（赛博风） ----------------
BG_TOP = (5, 12, 40)
BG_BOT = (2, 4, 18)
CARD = (12, 24, 66)
CARD2 = (10, 20, 56)
NEON = (0, 240, 255)
CYAN = (60, 220, 255)
PURPLE = (140, 90, 255)
GREEN = (120, 255, 160)
WHITE = (228, 240, 255)
GREY = (150, 172, 208)

W = 800
MARGIN = 36

_random = random.Random(7)


# ---------------- 基础绘制 ----------------
def _tw(draw, txt, f):
    b = draw.textbbox((0, 0), txt, font=f)
    return b[2] - b[0]


def _wrap(draw, txt, f, max_w):
    lines, cur = [], ""
    for ch in txt:
        if _tw(draw, cur + ch, f) <= max_w:
            cur += ch
        else:
            lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    return lines


def _neon_text(canvas, xy, txt, f, core, glow_color=NEON, glow=6, stroke=0):
    """霓虹发光文字（柔和光晕 + 实心核心）"""
    x, y = xy
    for r, a in [(glow, 20), (max(glow // 2, 2), 28)]:
        tmp = Image.new("RGBA", (canvas.width, 300), (0, 0, 0, 0))
        td = ImageDraw.Draw(tmp)
        td.text((x, 0), txt, font=f, fill=(*glow_color, a))
        tmp = tmp.filter(ImageFilter.GaussianBlur(r))
        canvas.paste(tmp, (x, y), tmp)
    d = ImageDraw.Draw(canvas)
    d.text((x, y), txt, font=f, fill=core, stroke_width=stroke, stroke_fill=core)


def _circle_logo(src, size):
    im = Image.open(src).convert("RGB")
    im = im.resize((size * 4, size * 4), Image.LANCZOS)
    mask = Image.new("L", (size * 4, size * 4), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size * 4 - 1, size * 4 - 1), fill=255)
    im = im.resize((size, size), Image.LANCZOS)
    mask = mask.resize((size, size), Image.LANCZOS)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(im, (0, 0), mask)
    ring = Image.new("RGBA", (size + 12, size + 12), (0, 0, 0, 0))
    ImageDraw.Draw(ring).ellipse((1, 1, size + 10, size + 10), outline=NEON, width=2)
    ring = ring.filter(ImageFilter.GaussianBlur(2))
    ImageDraw.Draw(ring).ellipse((3, 3, size + 8, size + 8), outline=NEON, width=1)
    return out, ring


def _matrix_rain(draw, region, count=90):
    x0, y0, x1, y1 = region
    chars = "0123456789ABCDEF"
    f = mono(12)
    for _ in range(count):
        x = _random.randint(x0, x1)
        y = _random.randint(y0, y1)
        ch = _random.choice(chars)
        col = (0, _random.randint(120, 220), _random.randint(180, 255), _random.randint(14, 40))
        draw.text((x, y), ch, font=f, fill=col)


def _grid_lines(draw, region, step=64, color=(40, 90, 180, 26)):
    x0, y0, x1, y1 = region
    for gx in range(x0, x1, step):
        draw.line((gx, y0, gx, y1), fill=color)
    for gy in range(y0, y1, step):
        draw.line((x0, gy, x1, gy), fill=color)


# ---------------- 区块布局 ----------------
class Layout:
    def __init__(self, canvas):
        self.canvas = canvas
        self.draw = ImageDraw.Draw(canvas)
        self.y = 0


def _build_header(layout, data, logo_path):
    """报头：圆形logo + 品牌标题 + 副标题 + 日期条"""
    logo_size = 108
    if logo_path and os.path.exists(logo_path):
        logo_img, ring = _circle_logo(logo_path, logo_size)
    else:
        logo_img, ring = None, None
    top = layout.y
    logo_x, logo_y = MARGIN, top + 34
    if logo_img is not None:
        layout.canvas.paste(ring, (logo_x - 6, logo_y - 6), ring)
        layout.canvas.paste(logo_img, (logo_x, logo_y), logo_img)
    tf = font(54, bold=True)
    tx = logo_x + logo_size + 24
    ty = logo_y + 8
    brand = data.get("brand", "矩阵AI日报")
    _neon_text(layout.canvas, (tx, ty), brand, tf, core=(200, 245, 255), glow_color=NEON, glow=8, stroke=1)
    sf = font(19)
    sub = data.get("subtitle", "MATRIX AI DAILY · 把AI翻译成生意")
    layout.draw.text((tx, ty + 68), sub, font=sf, fill=CYAN)
    y_line = top + 168
    layout.draw.rectangle((MARGIN, y_line, W - MARGIN, y_line + 2), fill=NEON)
    layout.draw.rectangle((MARGIN, y_line + 3, int(W * 0.35), y_line + 4), fill=PURPLE)
    df = font(18, bold=True)
    date_txt = data.get("date", "")
    issue_txt = data.get("issue", "")
    head = "  ".join([t for t in [date_txt, issue_txt] if t])
    layout.draw.text((MARGIN, y_line + 14), head, font=df, fill=WHITE)
    en_hint = data.get("en_hint", "// DAILY INTELLIGENCE")
    ew = _tw(layout.draw, en_hint, font(14))
    layout.draw.text((W - MARGIN - ew, y_line + 16), en_hint, font=font(14), fill=PURPLE)
    layout.y = y_line + 52
    return logo_img


def _section_title(layout, title, en):
    layout.y += 20
    y = layout.y
    layout.draw.rounded_rectangle((MARGIN, y + 4, MARGIN + 6, y + 38), 3, fill=NEON)
    _neon_text(layout.canvas, (MARGIN + 20, y), title, font(28, bold=True), core=WHITE, glow_color=NEON, glow=5)
    if en:
        ew = _tw(layout.draw, en, font(14))
        layout.draw.text((W - MARGIN - ew, y + 12), en, font=font(14), fill=PURPLE)
    yy = y + 48
    for i in range(40):
        layout.draw.rectangle((MARGIN + i, yy, MARGIN + i + 1, yy + 2),
                              fill=(int(0 + 140 * i / 40), int(240 - 150 * i / 40), 255))
    layout.y = yy + 18


def _card(layout, title_txt, items, accent=NEON, fill=CARD):
    """要点列表卡片"""
    top = layout.y
    body_h = len(items) * 32
    h = 40 + body_h + 26
    layout.draw.rounded_rectangle((MARGIN, top, W - MARGIN, top + h), 16, fill=fill)
    for r, col in ((16, NEON), (14, (30, 90, 200))):
        layout.draw.rounded_rectangle((MARGIN, top, W - MARGIN, top + h), r, outline=col, width=1)
    layout.draw.rounded_rectangle((MARGIN + 16, top + 14, MARGIN + 22, top + 46), 3, fill=accent)
    layout.draw.text((MARGIN + 34, top + 15), title_txt, font=font(20, bold=True), fill=WHITE)
    yy = top + 50
    for it in items:
        layout.draw.rectangle((MARGIN + 22, yy + 7, MARGIN + 30, yy + 15), fill=NEON)
        txt = it
        # 前导符号处理
        for prefix in ("»", "•", "-"):
            if txt.startswith(prefix):
                txt = txt[1:].strip()
        for line in _wrap(layout.draw, txt, font(16), W - 2 * MARGIN - 56):
            layout.draw.text((MARGIN + 42, yy), line, font=font(16), fill=(200, 224, 255))
            yy += 32
        yy += 2
    layout.y = top + h + 16


def _block(layout, tag, title_txt, body, tag_col=NEON):
    """三段式块：标签 + 标题 + 正文"""
    top = layout.y
    f = font(15)
    body_lines = []
    for seg in body:
        body_lines += _wrap(layout.draw, seg, f, W - 2 * MARGIN - 44)
    body_h = len(body_lines) * 28
    h = 78 + body_h + 22
    layout.draw.rounded_rectangle((MARGIN, top, W - MARGIN, top + h), 16, fill=CARD2)
    for r, col in ((16, (26, 80, 190)), (14, (20, 40, 100))):
        layout.draw.rounded_rectangle((MARGIN, top, W - MARGIN, top + h), r, outline=col, width=1)
    if tag:
        lw = _tw(layout.draw, tag, font(14, bold=True)) + 22
        layout.draw.rounded_rectangle((MARGIN + 16, top + 14, MARGIN + 16 + lw, top + 44), 8, fill=tag_col)
        layout.draw.text((MARGIN + 26, top + 17), tag, font=font(14, bold=True), fill=(4, 10, 34))
    _neon_text(layout.canvas, (MARGIN + 18, top + 52), title_txt, font(19, bold=True),
               core=WHITE, glow_color=CYAN, glow=4)
    yy = top + 52 + 36
    for line in body_lines:
        layout.draw.text((MARGIN + 20, yy), line, font=f, fill=GREY)
        yy += 28
    layout.y = top + h + 16


def _footer(layout, logo_img):
    layout.y += 26
    layout.draw.rectangle((MARGIN, layout.y, W - MARGIN, layout.y + 1), fill=(40, 90, 180))
    layout.y += 22
    if logo_img is not None:
        small = logo_img.resize((42, 42), Image.LANCZOS)
        layout.canvas.paste(small, (MARGIN, layout.y), small)
    _neon_text(layout.canvas, (MARGIN + 56, layout.y + 8), "矩阵AI日报 · 每天早8点，把AI翻译成生意",
               font(16, bold=True), core=(160, 250, 255), glow_color=NEON, glow=4)
    layout.draw.text((MARGIN, layout.y + 46), "长按图片可保存转发 · 关注 Server酱 每日推送", font=font(13), fill=GREY)
    layout.y += 78


def _render_sections(layout, sections):
    """按 sections 类型渲染"""
    for sec in sections:
        stype = sec.get("type", "list")
        title = sec.get("title", "")
        en = sec.get("en", "")
        _section_title(layout, title, en)
        if stype == "list":
            items = sec.get("items", [])
            # 拆成若干卡片，每卡最多 6 条
            for i in range(0, len(items), 6):
                _card(layout, title if i == 0 else "", items[i:i + 6])
        elif stype == "blocks":
            for blk in sec.get("blocks", []):
                tag = blk.get("tag", "")
                tag_col = {"机会": NEON, "方法": PURPLE, "概念": GREEN,
                           "发生了什么": NEON, "意味着什么": PURPLE, "和你有什么关系": GREEN,
                           "传递的信号": PURPLE, "中小企业能蹭到什么": GREEN,
                           "风险预警": GREEN}.get(tag, NEON)
                _block(layout, tag, blk.get("title", ""), blk.get("body", []), tag_col)
        elif stype == "plain":
            _block(layout, "", sec.get("title", ""), sec.get("body", []), NEON)


def render_issue(data, out_path, logo_path=None, width=800):
    """
    data 结构：
    {
      "brand": str, "subtitle": str, "date": str, "issue": str, "en_hint": str,
      "sections": [
        {"title": str, "en": str, "type": "list", "items": [str, ...]},
        {"title": str, "en": str, "type": "blocks",
         "blocks": [{"tag": str, "title": str, "body": [str, ...]}, ...]},
        {"title": str, "en": str, "type": "plain", "body": [str, ...]},
      ]
    }
    """
    global W, MARGIN
    W = width
    MARGIN = int(width * 0.045)

    # 占位跑一遍算高度
    probe = Image.new("RGB", (W, 4000), (0, 0, 0))
    pl = Layout(probe)
    _build_header(pl, data, logo_path)
    _render_sections(pl, data.get("sections", []))
    _footer(pl, None)
    content_h = pl.y + 20

    # 正式画布 + 渐变背景
    canvas = Image.new("RGB", (W, content_h), (0, 0, 0))
    for yy in range(content_h):
        t = yy / content_h
        r = int(BG_TOP[0] + (BG_BOT[0] - BG_TOP[0]) * t)
        g = int(BG_TOP[1] + (BG_BOT[1] - BG_TOP[1]) * t)
        b = int(BG_TOP[2] + (BG_BOT[2] - BG_TOP[2]) * t)
        ImageDraw.Draw(canvas).line((0, yy, W, yy), fill=(r, g, b))

    canvas = canvas.convert("RGBA")
    rd = ImageDraw.Draw(canvas, "RGBA")
    _grid_lines(rd, (0, 0, W, content_h))
    _matrix_rain(rd, (0, 0, W, content_h), count=int(content_h / 6))
    glow = Image.new("RGBA", (W, content_h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((W // 2 - 320, -260, W // 2 + 320, 160), fill=(0, 90, 255, 70))
    gd.ellipse((W // 2 - 220, -200, W // 2 + 220, 100), fill=(90, 60, 255, 60))
    glow = glow.filter(ImageFilter.GaussianBlur(100))
    canvas = Image.alpha_composite(canvas, glow).convert("RGB")

    layout = Layout(canvas)
    logo_img = _build_header(layout, data, logo_path)
    _render_sections(layout, data.get("sections", []))
    _footer(layout, logo_img)

    canvas = canvas.crop((0, 0, W, min(content_h, layout.y + 8)))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    canvas.save(out_path, "PNG")
    return out_path
