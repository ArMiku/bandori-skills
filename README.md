<div align="center">

# BanG Dream Skill

### 一组用于查询 BanG Dream! 官网企划信息的 Agent Skill。

[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-Standard-green)](https://agentskills.io)
[![Runtime-Claude Code](https://img.shields.io/badge/Runtime-Claude%20Code-blueviolet)](#安装)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

<br>

**帮你在 [bang-dream 官网](https://bang-dream.com) 查询 Live / News / 官方推文相关信息的 Agent Skill 集合。**

涵盖三个相互独立、按需加载的 Skill：

| Skill | 能力 |
|-------|------|
| [`bangdream-live`](./skills/bangdream-live) | Live / Event 票务、抽选、场馆、场贩、特典等 |
| [`bangdream-news`](./skills/bangdream-news) | 官网 News 资讯查询 + RSS 增量推送 |
| [`bangdream-tweet`](./skills/bangdream-tweet) | 官方 X（[@bang_dream_info](https://x.com/bang_dream_info)）推文查询 + RSS 增量推送 |

对话中直接提问即可调用；定时推送脚本输出宿主中立 JSON，可对接 OpenClaw / Hermes / cron 等调度器。

[效果示例](#效果示例) · [使用场景](#使用场景) · [安装](#安装) · [注意事项](#注意事项) · [路线图](#路线图)

<br>

</div>

---

## 效果示例

**用户**：

> roselia最新的live是哪个

**Claude**：

技能自动访问 `bang-dream.com/events/?artist[]=roselia&event_tag=live`，按开催日降序排列，第一条即为最新：

```
## Roselia 最新的 Live

**Roselia「Lehre der Rose」**
— Roselia 10th Anniversary Best Album「Lehre der Rose」リリース記念ライブ

| 项目 | 内容 |
|------|------|
| 開催日 | 2026年8月29日(土)・30日(日) |
| 場所 | 有明アリーナ |
```

**用户**：

> 需要。我社畜没时间关注这些信息，你替我看一下告诉我

**Claude**：

技能自动完成以下步骤：

1. 从列表页 HTML 提取详情页 URL → `https://bang-dream.com/events/lehre-der-rose/`
2. 抓取详情页全文（Tavily extract）
3. 下载座位图 + 特典图（需带浏览器 UA，否则被 404 挡回）
4. 用视觉模型识别图片内容

输出完整报告（节选关键部分）：

---

> ## 🌹 Roselia「Lehre der Rose」
>
> *10th Anniversary Best Album「Lehre der Rose」发行纪念 Live（单独 2DAYS）*
>
> | | |
> |---|---|
> | **日期** | 2026年8月29日(土)・30日(日) |
> | **场地** | 有明アリーナ（东京江东区） |
> | **出演** | Roselia |
> | **时间** | DAY1 開場16:30／開演18:00　DAY2 開場15:30／開演17:00 |
>
> ### ⚠️ 票务现状（重点）
>
> 页面列出的 **两轮售票都已截止**，目前**没有在售的票**：
>
> | 轮次 | 受付期间 | 状态 |
> |---|---|---|
> | 最速先行抽选（CD申込券） | 4/29 ~ 5/31 | ✅ 已结束 |
> | プレイガイド先行 | 6/12 ~ 7/3 | ✅ 已结束 |
> | **一般发售** | — | ❌ **尚未公布** |
>
> 👉 **盯紧 eplus.jp/roselia-lehre-der-rose/ 等一般发售公告。**
>
> 票价（税込）：プレミアムシート 22,000円 | 一般指定席(含特典) 15,400円 | 一般指定席 9,900円
>
> ### 🎁 购票特典
>
> - **DAY1**：特製湯呤 — 黑白文字排版陶瓷茶杯（约270ml）
> - **DAY2**：特製暖簾 — 黑白门帘（1200×800mm），五位成员群像插画
> - 到场当天领取，事后不补发
>
> ### 🪑 座位布局
>
> 舞台 → プレミアムシート → 一般指定席【アリーナ】 → 一般指定席【スタンド】
>
> ### 📞 问询
>
> - 公演：クリエイティブマン 03-3499-6669（月水金 12:00~16:00）
> - 票务：eplus 支持 support-qa.eplus.jp

## 使用场景

- **交互式对话**：在 Claude Code / Codex / Hermes / OpenClaw 等 Agent 中直接问「roselia 最近的 live」「这两天有什么 news」「官方推特发了啥」，Skill 会按 `description` 自动加载；也可用 `/bangdream-live`、`/bangdream-news`、`/bangdream-tweet` 斜杠命令显式触发。
- **定时 / 推送**：`scan_news.py`、`scan_tweets.py` 只负责「抓 RSS → 比对 state 去重 → 吐 JSON」，不绑渲染、不绑调度器。由 cron / OpenClaw / Hermes 等常驻服务拉起，自行把 JSON 渲染成 markdown / 飞书卡片 / webhook 推送。`count=0` 表示无更新，是否静默由调用方决定。

---

## 安装

### 前置依赖

| 依赖 | 用途 | 是否必需 |
|------|------|---------|
| 网页抓取 MCP（[Tavily](https://tavily.com) / web-reader 等） | live / news SOP 抓取详情页：自带浏览器 UA、返回干净 markdown、省 token | ⬜ 可选 |
| Python 3.8+ | 仅定时推送脚本（`scan_news.py` / `scan_tweets.py`）需要；纯标准库，无需 `pip install` | ⬜ 仅推送场景 |
| [Scrapling](https://github.com/D4Vinci/Scrapling) + camoufox | 仅 tweet 深度搜索（`search_tweets.py` 过 nitter 反爬）需要；不装则自动回退 RSS 过滤 | ⬜ 可选 |

### 安装 Skill

Skill 文件位于仓库 `skills/` 下，每个子目录就是一个独立 Skill（含 `SKILL.md` + `scripts/` + `reference/`）。把它放进 Claude Code 的 Skill 目录即可被识别。

**方式一：克隆 + 拷贝（最简单）**

```bash
git clone https://github.com/ArMiku/bandori-skills.git
cd bandori-skills

# 安装到个人目录（所有项目可用）
cp -r skills/* ~/.claude/skills/

# 或只装到当前项目
mkdir -p .claude/skills && cp -r skills/* .claude/skills/
```

**方式二：软链接（便于 `git pull` 跟随上游更新）**

```bash
git clone https://github.com/ArMiku/bandori-skills.git
cd bandori-skills
for s in bangdream-live bangdream-news bangdream-tweet; do
  ln -sf "$(pwd)/skills/$s" ~/.claude/skills/$s
done
```

**可选：安装 Scrapling（仅 tweet 深度搜索需要）**

```bash
pip install scrapling "camoufox[geoip]"
python -m camoufox fetch   # 下载 Camoufox 浏览器内核（约 320MB）
```

### 验证

定时推送脚本可单独验证：

```bash
python skills/bangdream-news/scripts/scan_news.py scan
python skills/bangdream-tweet/scripts/scan_tweets.py scan
```

首次运行会自动在 `~/.bangdream-news/`、`~/.bangdream-tweet/` 下生成 `state.json` 去重状态文件（可用 `--state-file` 或同名环境变量覆盖路径）。

---

## 注意事项

- 已知在 Claude Code 下使用 `mimo` 系列模型（如 `mimo-v2.5-pro`）时，**不会按 query 自动加载 Skill**，需用 `/bangdream-live` 等斜杠命令显式触发。
- bang-dream.com 与 nitter 的站点策略可能随时间变化；抓取层以各 Skill 的 `reference/fetch-strategy.md` 为准（标注了验证日期）。

---

## 路线图

**已实现：**

- ✅ Live / Event 页面查询
- ✅ News 页面查询 + RSS 增量推送
- ✅ 官方推文查询 + RSS 增量推送

**计划中：**

- ⬜ Discographies 页面查询
- ⬜ Schedule 页面查询
