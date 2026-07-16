# Live / Event 页面筛选说明

> 数据来源：<https://bang-dream.com/events>（WordPress 站点，服务端渲染，主题 `bangdream-portal`）。
> 本文基于对该页面 HTML 筛选表单的实际抓取与服务端返回验证（验证日期：2026-07-16）。站点改版后需复核。

## 筛选表单概览

页面筛选由**一个 GET 表单**实现：

- 表单：`<form method="get" action="https://bang-dream.com/events/">`
- 提交按钮：「この条件で検索」
- 提交方式为 GET，所有筛选项以**查询参数**形式附加到 `/events/` URL 上。

五个控件维度：

| 维度 | 参数名 | 控件类型 | 默认值 | 说明 |
|------|--------|---------|--------|------|
| アーティスト（企划/乐队） | `artist[]` | 多选 checkbox（数组） | `all`（すべて） | 多选时参数重复出现 |
| カテゴリ（类型） | `event_tag` | 单选 radio | `all`（すべて） | Live / Event 区分 |
| 開催年 | `year` | 下拉 select | `all`（年） | 不限 |
| 開催月 | `month` | 下拉 select | `all`（月） | 不限 |
| キーワード検索 | `s` | 文本输入 | 空 | 匹配名称/描述 |

> 默认状态（不传任何参数）= 全部 artist、全部类型、全部年月，按開催日**降序（新→旧）**排列。未筛选时全站共 **16 页**。

## 各筛选项取值

### アーティスト `artist[]`（多选）

传参方式：`artist[]=value`，多选则重复该参数：`artist[]=roselia&artist[]=mygo`。

默认 `all` = 不按 artist 过滤。**不需要该维度时建议完全不传 `artist[]`**，不要把 `all` 与具体值混用。

| value | 显示名（常用简称） |
|-------|------------------|
| `poppinparty` | Poppin'Party（ppp） |
| `afterglow` | Afterglow（ag） |
| `pastel-palettes` | Pastel＊Palettes（pp） |
| `roselia` | Roselia（萝） |
| `hello-happy-world` | ハロー、ハッピーワールド！（hhw） |
| `morfonica` | Morfonica（蝶团） |
| `raise-a-suilen` | RAISE A SUILEN（RAS） |
| `mygo` | MyGO!!!!!（狗） |
| `avemujica` | Ave Mujica（鸡） |
| `yumemita` | 夢限大みゅーたいぷ（梦团） |
| `millsage` | millsage |
| `ikka-dumb-rock` | 一家Dumb Rock! |
| `shuffle` | シャッフルユニット |
| `other` | その他 |

### カテゴリ `event_tag`（单选）

| value | 显示名 |
|-------|--------|
| `all` | すべて（默认） |
| `live` | ライブ（Live） |
| `event` | イベント（Event） |
| `other` | その他 |

### 開催年 `year`

`all`（默认，不限）或具体年份。页面当前列出范围 `2016`–`2027`，会随企划活动向上扩展。

### 開催月 `month`

`all`（默认，不限）或 `1`–`12`。年、月各自独立可选：可只选年、只选月或同时指定。

### キーワード `s`

自由文本，匹配演出名称 / 描述。日文需按需做 URL 编码。

## URL 构造规则

**第 1 页**：筛选参数直接挂在 `/events/` 之后：

```
https://bang-dream.com/events/?event_tag=live&artist[]=roselia&year=2026&month=7&s=東京
```

**第 N 页（N ≥ 2）**：分页为**路径段** `/page/N/`，筛选查询串原样追加在后面：

```
https://bang-dream.com/events/page/2/?event_tag=live
https://bang-dream.com/events/page/11/?event_tag=live
```

> ⚠️ **关键点**：分页是路径式 `/page/N/`，**不是** `?page=N`。带上筛选条件时，筛选查询串要拼到分页路径之后。第 1 页用 `/events/?{filters}`（不存在 `/page/1/`）。

常用示例：

| 目标 | URL |
|------|-----|
| 只看 Roselia 的 Live | `/events/?artist[]=roselia&event_tag=live` |
| 只看 2026 年 7 月 | `/events/?year=2026&month=7` |
| 关键词「東京」 | `/events/?s=東京` |
| Roselia + MyGO 的 Event，第 2 页 | `/events/page/2/?artist[]=roselia&artist[]=mygo&event_tag=event` |

## 默认排序

按開催日**降序**（最新 / 近期在前）。例：未筛选首页前几张依次为 2026 年 8 月 → 7 月 → 6 月。

## 与采集相关的注意点

- **抓取前提**：本站为服务端渲染（SSR）——带浏览器 UA 实测，列表页/详情页 HTML 中 `artist[]`、`event_tag`、`公演`、`チケット` 等 SSR 标记全部命中，`curl`/py 抓回即可解析，无需 JS 渲染。但**必带浏览器 UA，否则 404 空桩页**——抓取纪律（UA 门禁实测、curl/py 骨架、工具优先级）统一见 [网页抓取策略](./fetch-strategy.md)。
- **务必翻完分页**：未筛选共 16 页；筛选后页数减少（如 `event_tag=live` 为 11 页）。采集时遍历所有 `/page/N/`，避免漏取（对应 SKILL.md「页面有分页逻辑」）。
- **筛选后分页拼接**：第 2 页起为 `/events/page/N/?{原筛选查询串}`，构造时保留全部筛选参数。
- **artist 多选**：URL 中 `artist[]` 同名出现多次，按数组处理，勿后值覆盖前值。
- **`[]` 无需编码**：查询串中保留字面 `[]` 已验证可被服务端识别（返回 200 且对应选项回显 `checked`）。
- **卡片信息有限**：列表卡片仅含类型标签（ライブ/イベント/その他）+ 名称 + 可能的開催日时 / 場所，详细信息需进入卡片链接的详情页（见 SKILL.md 步骤 2 起）。
