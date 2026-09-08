---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: af7db8f58dc33f8012dc8f88fcfd980c_46138532aa6e11f190de525400461939
    ReservedCode1: wpJax1SVxXmaipydB93QTPZENPGpNv1DuT07PLE05w+YGxZyDagB5o4p+bCW2ydSgOLbXeCdV4Wf7WIUdO9IED2IATCBFeAhS2UMtnE98+Yi4ZvWuuQ9scfHq/F5z2H1HQZhKBWiTg4AcbqY0tOWPqoEGbBWimRzzFxPUafSeoBhuenXsVhh3vKdotw=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: af7db8f58dc33f8012dc8f88fcfd980c_46138532aa6e11f190de525400461939
    ReservedCode2: wpJax1SVxXmaipydB93QTPZENPGpNv1DuT07PLE05w+YGxZyDagB5o4p+bCW2ydSgOLbXeCdV4Wf7WIUdO9IED2IATCBFeAhS2UMtnE98+Yi4ZvWuuQ9scfHq/F5z2H1HQZhKBWiTg4AcbqY0tOWPqoEGbBWimRzzFxPUafSeoBhuenXsVhh3vKdotw=
---

# 矩阵AI日报 · 自动生成推送系统

每天早 8:00 自动在云端采集 AI 资讯，由大模型生成三刊简报，并推送到微信：

- 主刊《矩阵AI日报》：今日速报 + 对生意的启示 + 一分钟讲透
- 续刊《矩阵AI日报·续》：机会雷达 + 新工具速试 + 风险预警 + 深度拆解
- 南京专刊《矩阵AI日报·南京》：本地政策速递 + 训练营与活动 + AI培训机会（仅南京本地，联网实时搜索）

面向中小企业家、高管、深度AI爱好者，每条内容用「发生了什么 / 意味着什么 / 和你有什么关系」三段式，让读者一眼看懂、知道和自己生意的关系。

## 整体架构

```
GitHub Actions（每天 UTC 00:00 = 北京 08:00 触发，免费）
   → src/main.py 采集 AI 新闻（Hacker News）+ AI 论文（arXiv）
   → 调 DeepSeek 大模型生成主刊、续刊
   → 调通义千问（联网搜索）生成南京专刊
   → 解析 Markdown 为结构化数据，渲染赛博风 PNG 长图（src/parser.py + src/render.py）
   → 上传图片到本仓库 images/（jsDelivr CDN 加速）
   → Server酱推送微信（图片 + 文字双轨）
```

无需自己开电脑，全部在 GitHub 云端运行。

## 目录结构

```
matrix-ai-daily/
├── .github/workflows/daily.yml   # 每天8点定时任务
├── assets/logo.jpg               # 报头 Matrix 立方体 logo
├── src/main.py                   # 主程序（采集+生成+推送）
├── src/parser.py                 # Markdown -> 结构化 JSON 解析器
├── src/render.py                 # 赛博风长图渲染器
├── requirements.txt              # 依赖
└── README.md
```

## 部署前需要准备三把钥匙

### 1. DeepSeek API Key（大模型写日报用）
1. 打开 https://platform.deepseek.com 注册登录
2. 充值少量金额（几块钱够跑很久）
3. 进入「API Keys」→ 创建新 Key，复制保存

### 2. 通义千问 API Key（南京专刊联网搜索用）
1. 打开 https://bailian.console.aliyun.com 用支付宝/淘宝账号登录
2. 进入「模型广场」，开通「通义千问 qwen-plus」（开启联网搜索 enable_search）
3. 充值 10 元即可（按 token 计费，量很小）
4. 右上角头像 → API-KEY → 创建新 Key，复制保存

### 3. Server酱 SendKey（推送到微信用）
1. 手机/电脑打开 https://sct.ftqq.com ，用微信扫码登录
2. 登录后复制页面上的 SendKey

## 部署步骤（GitHub）

1. 在 GitHub 新建一个私有仓库，命名为 `matrix-ai-daily`
2. 把本目录所有文件推送到仓库（main 分支）
3. 仓库页面 → Settings → Secrets and variables → Actions → New repository secret
   - `DEEPSEEK_API_KEY`：粘贴 DeepSeek Key
   - `DASHSCOPE_API_KEY`：粘贴通义千问 Key
   - `SERVERCHAN_SENDKEY`：粘贴 Server酱 SendKey
4. **把仓库改为 Public**（图片版必须：日报图片存在仓库 images/ 目录，微信通过 jsDelivr CDN 加载，私有仓库的图片无法公开访问）
   - Settings → 拉到最底部 Danger Zone → Change visibility → Make public
5. 到 Actions 标签页，点「Run workflow」手动跑一次验证
6. 验证通过后，每天早 8:00 会自动运行（三刊连推，微信收到的是可长按保存转发的电子期刊长图）

## 本地测试（可选）

```bash
pip install -r requirements.txt
export DEEPSEEK_API_KEY=你的key
export DASHSCOPE_API_KEY=你的key
export SERVERCHAN_SENDKEY=你的SendKey
python src/main.py
```

## 常见问题

- **推送没收到**：先在 Actions 运行日志里看是否报错，再检查 SendKey 是否与微信扫码账号匹配
- **微信只收到文字、没收到图片**：多半是仓库还是 Private，去 Settings 改成 Public；改完后再 Run workflow 一次
- **图片加载慢/加载不出**：图片走 jsDelivr CDN，国内一般 1~2 秒加载；如仍不行，可在仓库 Secrets 加 `IMAGE_BASE_URL` 指向自己的图床/OSS 前缀（不填则默认 jsDelivr）
- **南京专刊没推送**：检查 `DASHSCOPE_API_KEY` 是否已配置、是否开启了 qwen-plus 的联网搜索权限
- **想改推送时间**：编辑 `.github/workflows/daily.yml` 里的 cron（UTC 时间 = 北京时间 - 8 小时）
- **想加栏目/改风格**：改 `src/main.py` 里 `generate_main` / `generate_sub` / `generate_nanjing` 的写作要求即可；想调整图片版式改 `src/render.py`
*（内容由AI生成，仅供参考）*
