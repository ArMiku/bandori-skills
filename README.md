<div align="center">

# BanG Dream Skill

### 用于查询BangDream官网相关企划信息的 Agent Skill。

[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-Standard-green)](https://agentskills.io)
[![Runtime-Claude Code](https://img.shields.io/badge/Runtime-Claude%20Code-blueviolet)](#安装)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

<br>

**帮你在[bang-dream官网](https://bang-dream.com) 查询相关信息的 Agent Skill。**

你可以用它来查询某场live、某个专辑发售的相关信息。

可以提供给 OpenClaw 和 Hermes 等个人助手的定时任务进行调用。

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

## 未来使用场景

loading...

---

## 安装

loading...

### 依赖

- Python(可选)
- Tavily MCP(建议)

---

### 注意事项

- 当前已知在 `claude code` 下使用 `mimo` 系列模型(如`mimo-v2.5-pro`)时必须指定 `/bangdream-live-query` 使用 skill，不会根据 query 自动加载。

---

## 路线图

已实现 / 当前版本：

- live / event 页面查询

计划中：

- news 页面查询
- discographies 页面查询
- schedule 页面查询

