"""金陵厚生原版 · 逐字复刻渲染器 v2
严格照抄原版内容/栏目/排版/色彩，仅将品牌名「金陵厚生」替换为「矩阵AI日报」并换用用户 logo。
页面：1080 x 2400（与原版一致）
"""
import os
from PIL import Image, ImageDraw, ImageFont
PW = 2160
PAGE_H = 4800
MARGIN = 108
CARD_R = 36
AV_W = PW - 2 * MARGIN
LOGO = '/Users/youngai/Library/Application Support/com.tencent.mac.marvis/MarvisData/User/oAN1i2R6cU4WnS15-fO54Hfy8UcU/workspace/conv_3bc6d2779401443fb3595a655bed47cf/temp/logo.png'
BG = (13, 13, 13)
CARD = (28, 28, 28)
CARD_IN = (26, 26, 26)
NAV = (26, 26, 18)
GOLD = (242, 209, 141)
GOLD_DIM = (201, 173, 110)
GOLD_TEXT = (236, 204, 147)
WHITE = (255, 255, 255)
GREY = (176, 176, 176)
GREY_DIM = (136, 136, 136)
GREY_LINE = (58, 58, 58)
BROWN_BAR = (42, 34, 21)
BLUE = (0, 191, 255)
RED = (225, 40, 45)
YELLOW = (242, 209, 141)
GREEN = (22, 163, 74)
PURPLE = (139, 92, 246)
YELLOW_TX = (20, 20, 20)
FB = '/System/Library/Fonts/STHeiti Medium.ttc'
FR = '/System/Library/Fonts/STHeiti Light.ttc'
_fcache = {}
S = 1.0

def font(size, bold=False):
    size = int(size * S)
    key = (size, bold)
    if key not in _fcache:
        _fcache[key] = ImageFont.truetype(FB if bold else FR, size)
    return _fcache[key]

def rounded(d, box, r, fill):
    d.rounded_rectangle(box, radius=r, fill=fill)

def tw(d, text, f):
    return d.textlength(text, font=f)

def wrap(text, d, f, max_w):
    lines, cur = ([], '')
    for ch in text:
        if ch == '\n':
            lines.append(cur)
            cur = ''
            continue
        if tw(d, cur + ch, f) > max_w:
            lines.append(cur)
            cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines

def draw_lines(d, lines, x, y, f, fill, leading=None, max_w=None):
    if leading is None:
        leading = int(f.size * 1.5)
    if max_w is not None:
        out = []
        for ln in lines:
            out.extend(wrap(ln, d, f, max_w))
        lines = out
    for ln in lines:
        d.text((x, y), ln, font=f, fill=fill)
        y += leading
    return y

def _logo_paste(canvas, d, lx, y, size):
    try:
        logo = Image.open(LOGO).convert('RGBA').resize((size, size), Image.LANCZOS)
        canvas.paste(logo, (int(lx), int(y)), logo)
        return
    except Exception:
        pass
    rounded(d, (lx, y, lx + size, y + size), 12, (16, 26, 48))
    d.text((lx + (size - tw(d, '01', font(int(size * 0.42), True))) / 2, y + size * 0.26), '01', font=font(int(size * 0.42), True), fill=GOLD)

def draw_header(canvas, d, page_no, total, simple=False, cont_title=None):
    if not simple:
        y = 168
        logo_size = 104
        title = '矩阵Ai 情报'
        tf = font(56, True)
        tw_ = tw(d, title, tf)
        logo_w = logo_size + 48
        total_w = logo_w + tw_
        lx = (PW - total_w) / 2
        _logo_paste(canvas, d, lx, y - 12, logo_size)
        d.text((int(lx + logo_w), int(y)), title, font=tf, fill=GOLD)
        y += 204
        s3 = '每天8分钟，AI助力OPC创业者'
        d.text(((PW - tw(d, s3, font(30))) / 2, y), s3, font=font(30), fill=GREY)
        y += 104
        s4 = '2026年9月9日 · 星期三 · 北京时间'
        d.text(((PW - tw(d, s4, font(24))) / 2, y), s4, font=font(24), fill=GREY_DIM)
        y += 108
        d.line((MARGIN, y, PW - MARGIN, y), fill=GREY_LINE, width=4)
        return y
    else:
        y = 112
        logo_size = 52
        brand = '矩阵Ai 情报'
        bf = font(28, True)
        _logo_paste(canvas, d, MARGIN, y + 4, logo_size)
        d.text((int(MARGIN + logo_size + 20), int(y + 4)), brand, font=bf, fill=GOLD)
        s2 = '2026年9月9日 · 星期三'
        d.text((PW - MARGIN - tw(d, s2, font(22)), y + 44), s2, font=font(22), fill=GREY_DIM)
        y += 184
        d.line((MARGIN, y, PW - MARGIN, y), fill=GREY_LINE, width=4)
        return y

def draw_nav(canvas, d, y, items):
    h = 256
    box = (MARGIN, y, PW - MARGIN, y + h)
    rounded(d, box, 16, NAV)
    n = len(items)
    col_w = AV_W / n
    for i, (num, label) in enumerate(items):
        cx = MARGIN + col_w * i + col_w / 2
        d.text((cx - tw(d, num, font(40, True)) / 2, y + 32), num, font=font(40, True), fill=GOLD)
        d.text((cx - tw(d, label, font(24)) / 2, y + 148), label, font=font(24), fill=(158, 158, 158))
        if i < n - 1:
            vx = int(MARGIN + col_w * (i + 1))
            d.line((vx, y + 56, vx, y + h - 56), fill=(60, 54, 38), width=4)
    return y + h

def section_title(d, x, y, w, num, title):
    lh = 88
    d.rectangle((x, y + 4, x + 8, y + 4 + lh), fill=GOLD)
    c = 60
    cx = x + 36
    cy = y + 18
    d.ellipse((cx - 2, cy - 2, cx + c + 2, cy + c + 2), outline=(255, 255, 255), width=6)
    d.ellipse((cx, cy, cx + c, cy + c), outline=GOLD, width=4)
    numf = font(19, True)
    d.text((cx + (c - tw(d, num, numf)) / 2, cy + 10), num, font=numf, fill=GOLD)
    tx = cx + c + 28
    d.text((tx, y + 16), title, font=font(30, True), fill=GOLD)
    return y + 100

def tag(d, x, y, text, bg, fg=WHITE, h=68, fsz=40):
    f = font(fsz, True)
    w = tw(d, text, f) + 40
    rounded(d, (x, y, x + w, y + h), 9, bg)
    d.text((x + 20, y + 14), text, font=f, fill=fg)
    return (x + w + 24, y + h)

def news_card(d, x, y, w, item, idx, insight_title='与我何关'):
    """速报/投资卡：标签+HOT+标题+来源+正文+解读框"""
    tags, title, src, body, insight, hot = item
    pad = 40
    x1 = x + pad
    xw = w - 2 * pad
    ft = font(30, True)
    fb = font(23)
    fi = font(21)
    lines_t = wrap(title, d, ft, xw - 80)
    lines_b = wrap(body, d, fb, xw)
    ti_h = len(lines_t) * int(ft.size * 1.42)
    bo_h = len(lines_b) * int(fb.size * 1.52)
    card_h = pad + 80 + ti_h + 16 + 52 + bo_h + pad
    if insight:
        ins_lines = wrap(insight, d, fi, xw - 40)
        card_h += 28 + 80 + len(ins_lines) * int(fi.size * 1.5) + 32
    rounded(d, (x, y, x + w, y + card_h), CARD_R, CARD)
    tagc = tags[0][1] if tags else BLUE
    d.rounded_rectangle((x, y, x + w, y + 18), radius=CARD_R, fill=tagc)
    cy = y + pad + 18
    c = 56
    d.ellipse((x1, cy, x1 + c, cy + c), outline=GOLD, width=6)
    d.text((x1 + (c - tw(d, str(idx + 1), font(18, True))) / 2, cy + 6), str(idx + 1), font=font(18, True), fill=GOLD)
    tx = x1 + c + 28
    for t, bg in tags:
        tx, _ = tag(d, tx, cy - 4, t, bg)
    if hot:
        tag(d, tx, cy - 4, 'HOT', YELLOW, YELLOW_TX)
    cy += 96
    cy = draw_lines(d, lines_t, x1, cy, ft, WHITE, leading=int(ft.size * 1.42))
    cy += 16
    if src:
        d.text((x1, cy), src, font=font(19), fill=GREY_DIM)
        cy += 52
    cy = draw_lines(d, lines_b, x1, cy, fb, GREY, leading=int(fb.size * 1.52))
    if insight:
        cy += 28
        bh = 28 + 80 + len(ins_lines) * int(fi.size * 1.5) + 28
        rounded(d, (x1, cy, x + w - pad, cy + bh), 12, BROWN_BAR)
        d.rounded_rectangle((x1, cy, x1 + 14, cy + bh), radius=6, fill=GOLD)
        d.text((x1 + 44, cy + 20), insight_title, font=font(23, True), fill=GOLD)
        draw_lines(d, ins_lines, x1 + 44, cy + 88, fi, (210, 200, 175), leading=int(fi.size * 1.5))
        cy += bh
    return y + card_h

def kepu_card(d, x, y, w, title, body_lines):
    """今日小白科普：标题 + 编号正文"""
    pad = 40
    x1 = x + pad
    xw = w - 2 * pad
    ft = font(30, True)
    fb = font(23)
    lines_t = wrap(title, d, ft, xw)
    all_b = []
    for ln in body_lines:
        all_b.extend(wrap(ln, d, fb, xw))
    ti_h = len(lines_t) * int(ft.size * 1.42)
    bo_h = len(all_b) * int(fb.size * 1.52)
    card_h = pad + ti_h + 24 + bo_h + pad
    rounded(d, (x, y, x + w, y + card_h), CARD_R, CARD)
    d.rounded_rectangle((x, y, x + w, y + 18), radius=CARD_R, fill=GOLD)
    cy = y + pad + 18
    cy = draw_lines(d, lines_t, x1, cy, ft, WHITE, leading=int(ft.size * 1.42))
    cy += 24
    cy = draw_lines(d, all_b, x1, cy, fb, GREY, leading=int(fb.size * 1.52))
    return y + card_h

def opc_card(d, x, y, w, tags_, items):
    """OPC 卡：2 个标签 + 2 条新闻（各自标题+正文）"""
    pad = 40
    x1 = x + pad
    xw = w - 2 * pad
    ft = font(29, True)
    fb = font(22)
    lines = []
    for t, b in items:
        lt = wrap(t, d, ft, xw)
        lb = wrap(b, d, fb, xw)
        lines.append((lt, lb))
    body_h = 0
    for i, (lt, lb) in enumerate(lines):
        body_h += len(lt) * int(ft.size * 1.4) + 20
        body_h += len(lb) * int(fb.size * 1.5)
        if i < len(lines) - 1:
            body_h += 52
    card_h = pad + 96 + body_h + pad
    rounded(d, (x, y, x + w, y + card_h), CARD_R, CARD)
    d.rounded_rectangle((x, y, x + w, y + 18), radius=CARD_R, fill=BLUE)
    cy = y + pad + 18
    tx = x1
    for t, bg in tags_:
        tx, _ = tag(d, tx, cy - 4, t, bg)
    cy += 96
    for i, (lt, lb) in enumerate(lines):
        cy = draw_lines(d, lt, x1, cy, ft, WHITE, leading=int(ft.size * 1.4))
        cy += 20
        cy = draw_lines(d, lb, x1, cy, fb, GREY, leading=int(fb.size * 1.5))
        if i < len(lines) - 1:
            cy += 24
            d.line((x1, cy, x + w - pad, cy), fill=GREY_LINE, width=4)
            cy += 28
    return y + card_h

def tip_card(d, x, y, w, item, idx):
    """实用技巧卡：3 标签 + 标题 + 步骤 + 适用场景框"""
    tags, title, steps, insight = item
    pad = 40
    x1 = x + pad
    xw = w - 2 * pad
    ft = font(30, True)
    fb = font(23)
    fi = font(21)
    lines_t = wrap(title, d, ft, xw - 80)
    all_s = []
    for ln in steps:
        all_s.extend(wrap(ln, d, fb, xw))
    ti_h = len(lines_t) * int(ft.size * 1.42)
    st_h = len(all_s) * int(fb.size * 1.52)
    card_h = pad + 80 + ti_h + 16 + st_h + pad
    if insight:
        ins_lines = wrap(insight, d, fi, xw - 40)
        card_h += 28 + 80 + len(ins_lines) * int(fi.size * 1.5) + 32
    rounded(d, (x, y, x + w, y + card_h), CARD_R, CARD)
    d.rounded_rectangle((x, y, x + w, y + 18), radius=CARD_R, fill=tags[0][1])
    cy = y + pad + 18
    c = 56
    d.ellipse((x1, cy, x1 + c, cy + c), outline=GOLD, width=6)
    d.text((x1 + (c - tw(d, str(idx + 1), font(18, True))) / 2, cy + 6), str(idx + 1), font=font(18, True), fill=GOLD)
    tx = x1 + c + 28
    for t, bg in tags:
        tx, _ = tag(d, tx, cy - 4, t, bg)
    cy += 96
    cy = draw_lines(d, lines_t, x1, cy, ft, WHITE, leading=int(ft.size * 1.42))
    cy += 16
    cy = draw_lines(d, all_s, x1, cy, fb, GREY, leading=int(fb.size * 1.52))
    if insight:
        cy += 28
        bh = 28 + 80 + len(ins_lines) * int(fi.size * 1.5) + 28
        rounded(d, (x1, cy, x + w - pad, cy + bh), 12, BROWN_BAR)
        d.rounded_rectangle((x1, cy, x1 + 14, cy + bh), radius=6, fill=GOLD)
        d.text((x1 + 44, cy + 20), '适用场景', font=font(23, True), fill=GOLD)
        draw_lines(d, ins_lines, x1 + 44, cy + 88, fi, (210, 200, 175), leading=int(fi.size * 1.5))
        cy += bh
    return y + card_h

def draw_footer(canvas, d, page_no, total, tail):
    y = PAGE_H - 336
    d.line((MARGIN, y, PW - MARGIN, y), fill=GREY_LINE, width=4)
    s = '矩阵Ai 情报'
    d.text(((PW - tw(d, s, font(28, True))) / 2, y + 52), s, font=font(28, True), fill=GOLD_TEXT)
    s2 = '每天8分钟，AI助力OPC创业者'
    d.text(((PW - tw(d, s2, font(22))) / 2, y + 148), s2, font=font(22), fill=GREY)
    if tail == 'page':
        s3 = f'— 第{page_no}/{total}页 —'
        d.text(((PW - tw(d, s3, font(22))) / 2, y + 228), s3, font=font(22), fill=GREY_DIM)
    elif tail == 'team':
        d.text(((PW - tw(d, '本期共 11 条精选：信息速递，认知加速器，行动路线图。', font(21))) / 2, y + 228), '本期共 11 条精选：信息速递，认知加速器，行动路线图。', font=font(21), fill=GREY_DIM)
        d.text(((PW - tw(d, '来源：矩阵AI日报团队', font(21))) / 2, y + 288), '来源：矩阵AI日报团队', font=font(21), fill=GREY_DIM)
NAV_P1 = [('3', 'AI速递'), ('1', '小白科普'), ('2', '实用技巧'), ('3', '投资资讯'), ('2', 'OPC动态')]
P1_AI = [([('全球·前沿', BLUE)], 'OpenAI 官宣达成"自动化研究实习生"：每位研究员身后站着 3 个 AI', 'OpenAI 官方博客 · 9月6日', 'OpenAI 披露内部数据：已实现去年承诺的"自动化研究实习生"目标——AI 能在人类指导下完成需熟练研究员数天的任务；研究部门每 1 个人类工作日对应 3.1 个 AI Agent 工作日，中位数研究员日均烧超 600 美元算力让 AI 帮手跑实验；目标 2028 年 3 月前造出自动化 AI 研究员，并坦言"尚不知如何安全走到完全自主"。', 'AI 帮忙造 AI 从概念走进实验室日常——软件、科研的迭代还会更快。对个人：越早把 AI 用成"数字同事"，越不吃亏。', True), ([('全球·安全治理', BLUE)], '微软给 AI 智能体装"刹车"：发邮件、付款前必须人工批准', '微软官方路线图 / IT之家 · 9月1-4日', '微软 9 月起在 Copilot Studio 推出强制人工审批：AI 智能体调用邮件、工单、支付等敏感工具前会暂停，弹出"它想做什么"的审批请求，由人批准、仅本次放行或拒绝——审批独立于 AI 自身判断，即使 AI 认为该做也必须等人点头；请求直接内嵌在 Teams 与 365 频道里。', '头部厂商开始给 AI 的"对外动作"设人工闸。你自己用 AI 处理发消息、转账、签文件时，同样记得留一道"发出前确认"。', False), ([('中国·民生', RED)], '"国家反诈 AI"上线：随身的 AI 反诈顾问，微信小程序也能用', '公开报道 · 9月6-7日', '国家反诈中心推出"国家反诈 AI"智能助手并上线 App，微信、支付宝小程序同步开放：可随时提问可疑链接、话术、来电，由 AI 实时识别诈骗套路并给出提示；面向 AI 换脸、声音克隆等新型骗局做专项问答，把"反诈专家"装进每个人的手机。', 'AI 诈骗越来越"以假乱真"，官方用 AI 反制 AI。给家里长辈的手机装一个，比装十个杀毒软件都实在。', False)]
P1_KEPU = ('AI 开始"造"下一代 AI 了？聊聊递归自我改进 (RSI)', ['① 概念："递归自我改进" = AI 参与研发下一代 AI，就像最优秀的毕业生回校当老师，教出来的学生可能比老师更强，再当下一任老师——如此循环，进步会越来越快。', '② 场景：OpenAI 研究员人均配 3 个 AI"实习生"写代码、跑实验；Meta 内部 93% 的代码变更由 AI 协助完成——这些还都是"人在回路"：人定方向、AI 干体力活，关键处仍需人工干预。', '③ 价值：一旦 AI 能自主研究 AI，迭代将指数加速——这正是 1100 多名大厂员工联名呼吁"慢一点"的原因。对你：AI 能力只会更新更快，越早把它变成你的第二技能，越从容。'])
P2_TIP = [([('CN 国内', GREEN), ('腾讯元宝', YELLOW), ('小白友好', GREEN)], '3 步让 AI 帮你查证："这条消息靠谱吗？"', ['① 收到可疑消息（截图/链接/文案），发给元宝问："帮我查证这条信息真假"', '② 让它列出来源与多方说法，标出"事实 / 存疑 / 不实"', '③ 关键结论再让它"用大白话复核一遍"；涉及钱的以官方渠道为准'], '适用场景：家庭群养生谣言、投资小作文、AI 换脸视频——转发之前先问 AI，少当一次传谣人'), ([('国外', GREEN), ('Gemini', YELLOW), ('中高难度', YELLOW)], '3 步在 Gemini 里用 Lyria 写一条专属 BGM', ['① Gemini 中打开音乐生成（Lyria 3.5），描述风格："轻快尤克里里+口哨，60 秒"', '② 选纯音乐/人声与模板；可传一张照片"看图作曲"，或自定义歌词', '③ 试听不满意可换描述重生成，满意导出到视频/短视频；商用前确认授权条款'], '适用场景：短视频与探店 BGM、小店宣传片、活动暖场——一句话快速出 demo（需 Gemini 账号，Lyria 面向全球用户开放）')]
P2_INV = [([('海外·融资', PURPLE), ('AI搜索', PURPLE)], 'Perplexity 新一轮融资估值将超 300 亿美元：英伟达洽谈参投', '来源：The Information / 投中网 · 9月5日', 'AI 搜索明星公司 Perplexity 正完成新一轮数十亿美元融资，英伟达洽谈参投；投后估值预计超 300 亿美元，较上轮 200 亿增逾 50%。公司成立仅四年、创始团队含 3 名 90 后，2025 年底 C 轮融资并代言；产品已从"对话搜索"扩展到可自动操作电脑的智能体。', '冷静解读：英伟达正把"算力客户"升级为"股权绑定"，深度渗透一级市场——AI 搜索赛道估值再上一个台阶。', False), ([('国内·融资', PURPLE), ('AI硬件', PURPLE)], '兴芯半导体完成超百亿元融资：宁德时代系领投 GaN MicroLED', '来源：93913 / AISeng · 9月6日', '武汉兴芯半导体完成超 100 亿元人民币新一轮融资，宁德时代旗下普川资本领投，美团龙珠、国泰海通及多家地方国资参投；公司专注 8 英寸硅基 GaN MicroLED 技术，瞄准 AR 近眼显示与 AI 算力光互连两大增长场景。', '冷静解读：AI 军备竞赛烧到"显示与光互连"硬件层——产业资本+地方国资合力，押注看得见的制造闭环。', False), ([('国内·资本', PURPLE), ('平台布局', PURPLE)], '知乎拟出资 15 亿元认购 AI 股权投资基金：内容社区下场当"金主"', '来源：知乎公告（港交所）· 9月6日', '知乎公告拟出资 15 亿元人民币认购天津丽思新晟股权投资合伙企业份额、持股不超 30%，基金将投向境内早期至成长期 AI 企业，尚待股东大会批准——内容社区用财务投资换"技术生态入场券"。', '冷静解读：AI 融资的"金主"越来越多元——热钱越多，越考验项目成色，别被估值泡沫晃了眼。', False)]
P2_OPC = [([('北京·东城', BLUE), ('上海·长宁', BLUE)], [('东城首家 OPC 产业社区"和平·in"正式开张', '北京东城首家 OPC 产业社区"和平·in"9/1 在玖安广场迎来首批企业签约入驻，覆盖智能体应用、企业合规、数字营销、大健康等 AI 及 AI+ 方向；社区 7 月揭牌、9 月进入实质运营，定位首都核心区 AI 产业承载地，配套"悦·思享 / 悦·创营 / 悦·投会"活动矩阵，从"出租空间"转向产业服务与生态运营。'), ('市场监管局把"一人公司最怕什么"讲进注册窗口', '上海长宁区市场监管局面向 OPC 创业者厘清风险：按新《公司法》第 23 条第 3 款，一人公司股东若不能证明公司财产独立于个人财产，需对公司债务承担连带责任——公私账户不分、个人卡收公司款都可能"击穿"公司防线。一线城市 OPC 服务正从"帮你快办好"细化到"帮你别在第一步埋雷"。')])]
P3_OPC = [([('南京·在期', RED), ('OPC训战班', PURPLE)], 'OPC AI超体个体训战班：首期南京，9/15 截止报名', '中国生产力促进中心协会 · 2026年9-12月', '中国生产力促进中心协会主办，面向OPC创业者与转型者，课程覆盖零预算内容矩阵、个人IP冷启动、私域自动化运营等低成本获客策略，含真实项目路演与园区、投资人一对一点评资源对接；通过考核获权威证书。首期地点南京，小班教学≤40人，2026年9月15日12:00前提交报名回执并完成缴费。', '报名：按协会官网通知填写报名回执、缴费（培训费5800元/人，含学费/资料/3天线下茶歇）。', True), ([('9月·浦口', RED), ('OPC训练营', PURPLE)], 'OPC训练营：从AI办公到AI开发——WorkBuddy入门与进阶实战', '南京创业服务月 · 09/10 浦口', '南京9月创业服务活动之一，面向OPC创业者与在职者，实战演练从AI办公到AI开发的进阶路径，WorkBuddy入门与进阶上手；9月10日在浦口区同心大学生创业园举办，现场可对接创业服务资源。', '报名：咨询电话 18068839079（名额有限，先到先得）。', False)]
P3_COURSES = [([('9月·南京', RED), ('大模型应用工程师', YELLOW)], '工信部电子标准院《人工智能大模型应用工程师》培训班·南京站', '中国电子技术标准化研究院 · 第一期 09/15-18', '依据 SJ/T 11805-2022《人工智能从业人员能力要求》开设，线下授课，聚焦大模型应用与智能体开发核心技术实践；面向技术负责人、AI 工程师、产品经理、数据工程师等；第一期 2026 年 9 月 15-18 日（15 日报到）在南京开课，后续西安/重庆/南昌滚动开班，结业考核可获行业认证。', '报名：中国电子技术标准化研究院官网（www.cesi.cn）查看通知。', False), ([('9月·南京', RED), ('省人社厅', BLUE)], '南师大《大模型与智能体赋能教育教学》高级研修班', '南京师范大学继续教育学院 · 09/15-18', '由省人社厅主办、南京师范大学承办的 2026 省级高级研修项目；面向全省教师与教育管理者，聚焦大模型与智能体在教学场景的落地应用；9 月 15-18 日在南京师范大学仙林校区开班，9/12 前报名，设线上直播免费通道。', '报名：南师大继续教育学院官网（jxjy.njnu.edu.cn）查看通知。', False), ([('9月·江宁', RED), ('公益免费', GREEN)], '江宁 AI 夜校 9 月免费课：亲子教育 / AI影视 / 数字营销', '江宁区总工会/人社局 · 09/11、09/14', '江宁区免费 AI 夜校 9 月在期课程：AI家庭成长规划（9/11 19:00 江宁职工服务中心310教室，限30人）、AI影视制作与商业落地（9/14 18:30 麒麟科技城）、AIGC数字营销（区人社局联办）；面向家长、创业者与小店店主，晚间开课、零基础可学。', '报名：关注"江宁发布"公众号推文扫码，公益免费名额有限。', False)]

def measure(fn, args):
    probe = Image.new('RGB', (PW, 8000), BG)
    pd = ImageDraw.Draw(probe)
    return fn(pd, MARGIN, 0, AV_W, *args)

def render():
    OUT = '/Users/youngai/Library/Application Support/com.tencent.mac.marvis/MarvisData/User/oAN1i2R6cU4WnS15-fO54Hfy8UcU/workspace/conv_3bc6d2779401443fb3595a655bed47cf/output/matrix-ai-daily/images'
    os.makedirs(OUT, exist_ok=True)
    FOOT = 336
    HEAD_H1 = 564
    NAV_H = 256 + 16
    HEAD_H2 = 208
    GAP = 20
    b1 = PAGE_H - FOOT - HEAD_H1 - NAV_H
    b2 = PAGE_H - FOOT - HEAD_H2
    p1_sections = [('1', '今日AI速递', [(news_card, (it, i)) for i, it in enumerate(P1_AI)]), ('2', '今日小白科普', [(kepu_card, (P1_KEPU[0], P1_KEPU[1]))])]
    p2_sections = [('3', '实用技巧·本期：腾讯元宝/Gemini', [(tip_card, (it, i)) for i, it in enumerate(P2_TIP)]), ('4', 'AI投资领域新资讯', [(news_card, (it, i)) for i, it in enumerate(P2_INV)]), ('5', 'OPC新发展', [(opc_card, (P2_OPC[0][0], P2_OPC[0][1]))])]
    p3_sections = [('6', '南京 OPC 动态', [(news_card, (it, i)) for i, it in enumerate(P3_OPC)]), ('7', '9月 AI 线下课 · 报名中', [(news_card, (it, i)) for i, it in enumerate(P3_COURSES)])]
    for pi, (sections, budget, tail, cont_title) in enumerate([(p1_sections, b1, 'page', None), (p2_sections, b2, 'team', None), (p3_sections, b2, 'page', 'AI 日报 · 南京专刊')]):
        global S
        S = 1.54 if pi == 1 else 2.0
        canvas = Image.new('RGB', (PW, PAGE_H), BG)
        d = ImageDraw.Draw(canvas)
        hs = []
        total_h = 0
        for si, (num, title, blocks) in enumerate(sections):
            total_h += 100
            for fn, args in blocks:
                h = measure(fn, args)
                total_h += h
            total_h += GAP * (len(blocks) + (1 if si else 0))
        total_h -= GAP
        print(f'page{pi + 1} blocks_h={total_h} budget={budget}')
        if total_h > budget:
            print(f'  WARN: overflow {total_h - budget}px')
        y = 0
        if pi == 0:
            y = draw_header(canvas, d, pi + 1, 3, simple=False)
            y = draw_nav(canvas, d, y + 20, NAV_P1) + 20
        else:
            y = draw_header(canvas, d, pi + 1, 3, simple=True, cont_title=cont_title)
        y += 12
        for si, (num, title, blocks) in enumerate(sections):
            y = section_title(d, MARGIN, y, AV_W, num, title) + GAP
            for fn, args in blocks:
                y = fn(d, MARGIN, y, AV_W, *args) + GAP
        draw_footer(canvas, d, pi + 1, 3, tail)
        out = os.path.join(OUT, f'daily-jinhua-20260909-p{pi + 1}.png')
        canvas.save(out, 'PNG')
        print('OK', os.path.basename(out), canvas.size, os.path.getsize(out))
if __name__ == '__main__':
    render()