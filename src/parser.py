# -*- coding: utf-8 -*-
"""Markdown -> 结构化 JSON 解析器（针对三刊固定结构）"""
import re


def split_sections(md):
    """按 '## ' 标题切分，返回 [(title, [raw_lines]), ...]"""
    sections = []
    cur_title, cur_lines = None, []
    for line in md.splitlines():
        s = line.strip()
        if s.startswith("## "):
            if cur_title:
                sections.append((cur_title, cur_lines))
            cur_title = s[3:].strip()
            cur_lines = []
        else:
            cur_lines.append(line)
    if cur_title:
        sections.append((cur_title, cur_lines))
    return sections


def clean_line(s):
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
    s = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s)
    s = s.replace("*", "").replace("`", "").replace("#", "").strip()
    return s


def _is_item(s):
    return bool(s) and not s.startswith(("#", ">", "---")) and len(s) > 1


def parse_list(lines):
    items = []
    for line in lines:
        s = clean_line(line)
        if _is_item(s):
            s = s.lstrip("-•·*1234567890. )")
            items.append(s)
    return [i for i in items if i]


def parse_blocks(lines):
    """
    把【标签】驱动的行解析成 blocks（每个【标签】行独立成块）。
    规则：
      - 遇到【标签】行即开新块：tag=标签，title=行内内容
      - 非【标签】行：若当前无块则开新块（tag=""，title=该行），否则追加到当前块 body
    这样三段式【发生了什么】【意味着什么】【和你有什么关系】会渲染成三个分色块。
    """
    blocks = []
    cur = None

    def flush():
        nonlocal cur
        if cur:
            cur["body"] = [b for b in cur["body"] if b.strip()]
            blocks.append(cur)
        cur = None

    for line in lines:
        s = line.strip()
        m = re.match(r"^【(.+?)】\s*(.*)$", s)
        if m:
            flush()
            tag = m.group(1).strip()
            rest = m.group(2).strip()
            cur = {"tag": tag, "title": clean_line(rest) if rest else "", "body": []}
        else:
            cs = clean_line(line)
            if _is_item(cs):
                if cur is None:
                    cur = {"tag": "", "title": cs, "body": []}
                else:
                    cur["body"].append(cs)
    flush()
    # 空 title 兜底：取 body 第一条作 title
    for b in blocks:
        if not b.get("title") and b.get("body"):
            b["title"] = b["body"][0]
            b["body"] = b["body"][1:]
    return blocks


def parse_plain(lines):
    out = []
    for line in lines:
        cs = clean_line(line)
        if _is_item(cs):
            out.append(cs)
    return out


def classify(title):
    """按栏目名判定渲染类型：速报/工具速试 -> list；讲透 -> plain；其余 -> blocks"""
    if title in ("今日速报", "新工具速试"):
        return "list"
    if "讲透" in title:
        return "plain"
    return "blocks"


def md_to_data(md, brand="", subtitle="", date="", issue=""):
    data = {"brand": brand, "subtitle": subtitle, "date": date, "issue": issue, "sections": []}
    for title, lines in split_sections(md):
        stype = classify(title)
        sec = {"title": title, "type": stype}
        if stype == "list":
            sec["items"] = parse_list(lines)
        elif stype == "blocks":
            sec["blocks"] = parse_blocks(lines)
        else:
            sec["body"] = parse_plain(lines)
        data["sections"].append(sec)
    return data


def data_to_markdown(data):
    """结构化数据 -> 推送用 Markdown（保持可读）"""
    out = []
    brand = data.get("brand") or "矩阵AI日报"
    out.append(f"# {brand}")
    for sec in data.get("sections", []):
        out.append(f"## {sec['title']}")
        stype = sec.get("type")
        if stype == "list":
            for it in sec.get("items", []):
                out.append(f"- {it}")
        elif stype == "blocks":
            for b in sec.get("blocks", []):
                tag = b.get("tag", "")
                t = b.get("title", "")
                head = f"**【{tag}】** {t}" if tag else f"**{t}**"
                out.append(head)
                for line in b.get("body", []):
                    out.append(f"- {line}")
                out.append("")
        else:
            for line in sec.get("body", []):
                out.append(line)
    return "\n".join(out)
