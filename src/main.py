#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
矩阵AI日报 · 自动生成推送系统（图片版）
主刊《矩阵AI日报》 + 续刊《矩阵AI日报·续》 + 本地专刊《矩阵AI日报·南京》
流程：采集AI资讯 -> 大模型生成三刊(Markdown) -> 解析为结构化数据 -> 渲染赛博风PNG长图
      -> 上传图片到仓库 -> Server酱推送微信（图片+文字）
"""

import os
import sys
import base64
import datetime
import tempfile
import xml.etree.ElementTree as ET

import requests

# ---------------- 配置（从环境变量读取，GitHub Secrets 注入） ----------------
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "").strip()
DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY", "").strip()
SERVERCHAN_SENDKEY = os.environ.get("SERVERCHAN_SENDKEY", "").strip()
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY", "").strip()
IMAGE_BASE_URL = os.environ.get("IMAGE_BASE_URL", "").strip()  # 可选：自定义图床/CDN前缀

DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"
DASHSCOPE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
DASHSCOPE_MODEL = "qwen3.7-plus"
HN_API = "https://hacker-news.firebaseio.com/v0"
ARXIV_API = "https://export.arxiv.org/api/query"

BRAND_MAIN = "矩阵AI日报"
BRAND_SUB = "矩阵AI日报·续"
BRAND_NANJING = "矩阵AI日报·南京"

# 项目根目录（本文件位于 src/ 下）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO_PATH = os.path.join(BASE_DIR, "assets", "logo.jpg")
IMG_DIR = os.path.join(tempfile.gettempdir(), "matrix-ai-daily-images")
os.makedirs(IMG_DIR, exist_ok=True)

# 栏目 -> 英文提示（渲染报头副标）
EN_MAP = {
    "今日速报": "TODAY'S BRIEF",
    "对生意的启示": "INSIGHTS FOR YOUR BUSINESS",
    "一分钟讲透": "60-SECOND DEEP DIVE",
    "机会雷达": "OPPORTUNITY RADAR",
    "新工具速试": "TOOLS TO TRY TODAY",
    "风险预警": "RISK ALERT",
    "深度拆解": "DEEP DIVE",
    "本地政策速递": "LOCAL POLICY",
    "训练营与活动": "CAMPS & EVENTS",
    "AI培训机会": "AI TRAINING",
}

AI_KEYWORDS = [
    "ai", "artificial intelligence", "gpt", "openai", "anthropic", "claude",
    "gemini", "llm", "large language model", "machine learning", "deep learning",
    "agent", "copilot", "chatbot", "diffusion", "nvidia", "semiconductor",
    "chip", "robotics", "robot", "autonomous", "multimodal", "neural",
]

TODAY = datetime.date.today().strftime("%Y-%m-%d")


# ---------------- 采集：Hacker News（Algolia 单次请求） ----------------
def fetch_hacker_news(limit=15):
    news = []
    try:
        params = {
            "tags": "story",
            "query": "AI",
            "hitsPerPage": str(limit),
            "numericFilters": "points>50",
        }
        resp = requests.get("https://hn.algolia.com/api/v1/search", params=params, timeout=20)
        for hit in resp.json().get("hits", []):
            title = (hit.get("title") or "").strip()
            if not title:
                continue
            url = hit.get("url") or hit.get("story_url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
            news.append({"title": title, "url": url, "score": hit.get("points", 0)})
    except Exception as e:
        print("[采集] HN 失败:", e)
    return news[:limit]


# ---------------- 采集：arXiv AI 论文 ----------------
def fetch_arxiv(limit=5):
    papers = []
    try:
        params = {
            "search_query": "cat:cs.AI",
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": str(limit),
        }
        resp = requests.get(ARXIV_API, params=params, timeout=20)
        root = ET.fromstring(resp.text)
        ns = {"a": "http://www.w3.org/2005/Atom"}
        for entry in root.findall("a:entry", ns)[:limit]:
            title = entry.find("a:title", ns).text.strip().replace("\n", " ")
            link = entry.find("a:id", ns).text.strip()
            papers.append({"title": title, "url": link})
    except Exception as e:
        print("[采集] arXiv 失败:", e)
    return papers


def format_materials(news, papers):
    lines = ["【今日AI新闻(Hacker News)】"]
    for n in news:
        lines.append(f"- {n['title']} ({n['url']})")
    lines.append("【今日AI论文(arXiv)】")
    for p in papers:
        lines.append(f"- {p['title']} ({p['url']})")
    return "\n".join(lines)


# ---------------- 生成：调用 DeepSeek ----------------
def call_deepseek(system_prompt, user_content):
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.7,
        "max_tokens": 2000,
    }
    resp = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


# ---------------- 生成：通义千问（带联网搜索，用于南京本地专刊） ----------------
def call_dashscope(system_prompt, user_content):
    headers = {
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": DASHSCOPE_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "enable_search": True,  # 开启联网搜索
        "temperature": 0.7,
    }
    resp = requests.post(DASHSCOPE_URL, headers=headers, json=payload, timeout=180)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def generate_nanjing():
    system = (
        "你是《矩阵AI日报·南京》主编，面向南京的中小企业家、高管、AI爱好者与OPC创业者，严谨专业，绝不忽悠。"
        "请联网搜索南京本地最新信息，用中文撰写本地专刊，Markdown格式，结构固定为：\n"
        "# 矩阵AI日报·南京 | 本地专刊\n"
        "## 本地政策速递\n"
        "南京及江北新区、栖霞、建邺等区的AI、OPC相关政策动态1-3条\n"
        "## 训练营与活动\n"
        "南京OPC训练营、AI相关活动、路演、招募、论坛等1-3条\n"
        "## AI培训机会\n"
        "南京本地的AI技能培训、证书班、公开课、讲座等1-3条\n"
        "要求：只写南京本地相关内容；每条用【发生了什么】【意味着什么】【和你有什么关系】三段式；"
        "某类信息当天确实没有就写'今日暂无'，严禁编造。"
    )
    return call_dashscope(
        system,
        f"今天是{TODAY}。请联网搜索南京本地今天及近期最新的OPC/AI相关政策、活动与培训信息，生成《矩阵AI日报·南京》专刊。",
    )


def generate_main(news, papers):
    system = (
        "你是《矩阵AI日报》主编，面向中小企业家、高管、深度AI爱好者，严谨专业，绝不忽悠。"
        "请基于用户提供的当日素材，用中文撰写简报，Markdown格式，结构固定为：\n"
        "# 矩阵AI日报 | 老板内参版\n"
        "开篇导语一句：每天5分钟，AI世界发生的事，条条和你的生意有关。\n"
        "## 今日速报\n"
        "当日最重要的3-5条事件，每条一行，格式：**标题**——一句话事实【影响谁】\n"
        "## 对生意的启示\n"
        "挑2-3条最有商业价值的事件，每条严格用三段式：\n"
        "【发生了什么】一句话\n"
        "【意味着什么】1-2句点破背后的信号\n"
        "【和你有什么关系】明确说影响哪类人/什么决策/可以做什么\n"
        "## 一分钟讲透\n"
        "挑当天最值得关注的一个概念，用大白话讲清，200字左右\n"
        "要求：只基于素材，不编造事实；素材不足时宁缺毋滥；每一条都要让读者知道和自己有什么关系。"
    )
    return call_deepseek(system, f"今天是{TODAY}，以下是今日采集到的AI资讯素材：\n{format_materials(news, papers)}")


def generate_sub(news, papers):
    system = (
        "你是《矩阵AI日报·续》主编，面向中小企业家、高管、深度AI爱好者，严谨专业，绝不忽悠。"
        "请基于用户提供的当日素材，用中文撰写简报续刊，Markdown格式，结构固定为：\n"
        "# 矩阵AI日报·续 | 老板内参版\n"
        "## 机会雷达\n"
        "整理素材中融资、并购、上市、企业商业动作相关的内容2-3条，每条格式：\n"
        "【发生了什么】一句话\n"
        "【传递的信号】1句解读\n"
        "【中小企业能蹭到什么】1句可落地的想法；素材中没有相关动态就写'今日暂无重点机会'\n"
        "## 新工具速试\n"
        "给出2-3个今天就能上手的AI工具或技巧，每条格式：工具/方法——拿来做什么，怎么开始，花多少钱\n"
        "## 风险预警\n"
        "整理与政策、合规、AI陷阱相关的内容1-2条，讲怎么避开；素材中没有就写'今日暂无重点风险'\n"
        "## 深度拆解\n"
        "挑素材里最有话题性的一个点，给深度爱好者挖深一点，末尾附上对应的原文链接\n"
        "要求：只基于素材，不编造事实；素材不足时如实写'今日暂无'。"
    )
    return call_deepseek(system, f"今天是{TODAY}，以下是今日采集到的AI资讯素材：\n{format_materials(news, papers)}")


# ---------------- 图片渲染：Markdown -> 结构化 -> PNG ----------------
def build_issue_image(markdown, brand, subtitle, filename, en_hint):
    """解析 Markdown 并渲染为 PNG，返回 (data, img_path)"""
    import parser
    from render import render_issue

    data = parser.md_to_data(markdown, brand=brand, subtitle=subtitle, date=TODAY, issue=TODAY)
    for sec in data.get("sections", []):
        sec["en"] = EN_MAP.get(sec.get("title", ""), "")

    img_path = os.path.join(IMG_DIR, filename)
    try:
        render_issue(data, img_path, LOGO_PATH if os.path.exists(LOGO_PATH) else None)
        print(f"[图片] 渲染完成: {img_path} ({os.path.getsize(img_path)} bytes)")
        return data, img_path
    except Exception as e:
        print("[图片] 渲染失败:", e)
        return data, None


# ---------------- 图片上传：GitHub API + jsDelivr CDN ----------------
def image_public_url(remote_path):
    if IMAGE_BASE_URL:
        return IMAGE_BASE_URL.rstrip("/") + "/" + remote_path
    return f"https://cdn.jsdelivr.net/gh/{GITHUB_REPOSITORY}@main/{remote_path}"


def upload_image(local_path, remote_path):
    """上传图片到仓库指定路径，返回公网 URL；失败返回 None"""
    if not GITHUB_TOKEN or not GITHUB_REPOSITORY:
        print("[图片] 缺少 GITHUB_TOKEN/GITHUB_REPOSITORY，跳过上传")
        return None
    if not local_path or not os.path.exists(local_path):
        return None
    with open(local_path, "rb") as f:
        content_b64 = base64.b64encode(f.read()).decode()

    url = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/contents/{remote_path}"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}
    try:
        r = requests.get(url, headers=headers, timeout=20)
        sha = r.json().get("sha") if r.status_code == 200 else None
        payload = {"message": f"daily issue image: {remote_path}", "content": content_b64}
        if sha:
            payload["sha"] = sha
        r = requests.put(url, headers=headers, json=payload, timeout=60)
        if r.status_code not in (200, 201):
            print(f"[图片] 上传失败: HTTP {r.status_code} {r.text[:200]}")
            return None
        public = image_public_url(remote_path)
        print(f"[图片] 已上传: {public}")
        return public
    except Exception as e:
        print("[图片] 上传异常:", e)
        return None


def purge_jsdelivr(remote_path):
    """刷新 jsDelivr CDN 缓存，确保微信立即可见新图"""
    if not GITHUB_REPOSITORY or IMAGE_BASE_URL:
        return
    try:
        requests.post(
            "https://purge.jsdelivr.net/",
            json={"paths": [f"/gh/{GITHUB_REPOSITORY}@main/{remote_path}"]},
            timeout=20,
        )
        print("[图片] jsDelivr 缓存已刷新")
    except Exception as e:
        print("[图片] jsDelivr 刷新失败:", e)


# ---------------- 推送：Server酱 -> 微信 ----------------
def push_wechat(title, content, image_url=None):
    if not SERVERCHAN_SENDKEY:
        print("[推送] 未配置 SERVERCHAN_SENDKEY，跳过推送")
        return False
    if image_url:
        content = f"![{title}]({image_url})\n\n{content}"
    url = f"https://sctapi.ftqq.com/{SERVERCHAN_SENDKEY}.send"
    resp = requests.post(url, data={"title": title, "desp": content}, timeout=30)
    ok = resp.status_code == 200 and "success" in resp.text
    print(f"[推送] {title} -> {'成功' if ok else '失败'} ({resp.status_code})")
    return ok


def publish_issue(brand, subtitle, markdown, filename, en_hint=""):
    """一键：渲染 -> 上传 -> 推送（图片版 + 文字版双轨）"""
    data, img_path = build_issue_image(markdown, brand, subtitle, filename, en_hint)
    img_url = None
    if img_path:
        img_url = upload_image(img_path, f"images/{filename}")
        if img_url:
            purge_jsdelivr(f"images/{filename}")
    push_wechat(f"{brand} | {TODAY}", markdown, img_url)
    return data, img_url


def main():
    if not DEEPSEEK_API_KEY:
        print("错误：缺少 DEEPSEEK_API_KEY，请先在 GitHub Secrets 中配置")
        return 1

    print("[1/5] 开始采集AI资讯...")
    news = fetch_hacker_news()
    papers = fetch_arxiv()
    print(f"      采集完成：新闻 {len(news)} 条，论文 {len(papers)} 篇")

    print("[2/5] 生成并发布《矩阵AI日报》（主刊）...")
    main_content = generate_main(news, papers)
    publish_issue(BRAND_MAIN, "MATRIX AI DAILY · 把AI翻译成生意", main_content, "daily-main.png")

    print("[3/5] 生成并发布《矩阵AI日报·续》（续刊）...")
    sub_content = generate_sub(news, papers)
    publish_issue(BRAND_SUB, "MATRIX AI DAILY EXTRA · 老板内参版", sub_content, "daily-sub.png")

    print("[4/5] 生成并发布《矩阵AI日报·南京》（本地专刊）...")
    if DASHSCOPE_API_KEY:
        nanjing_content = generate_nanjing()
        publish_issue(BRAND_NANJING, "NANJING LOCAL EDITION · 本地专刊", nanjing_content, "daily-nanjing.png")
    else:
        print("[推送] 未配置 DASHSCOPE_API_KEY，跳过南京专刊")

    print("[5/5] 三刊图片版已发布，完成")
    return 0


if __name__ == "__main__":
    sys.exit(main())
