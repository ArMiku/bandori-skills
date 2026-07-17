# Discography 页面筛选说明

> 数据来源：<https://bang-dream.com/discographies/>（WordPress 站点，服务端渲染，主题 `bangdream-portal`）。
> 本文基于对该页面 HTML 筛选表单的实际抓取与服务端返回验证（验证日期：2026-07-17）。站点改版后需复核。

## 筛选表单概览

页面筛选由**一个 GET 表单**实现：

- 表单：`<form class="p-discography-form__form" method="get" action="https://bang-dream.com/discographies/">`
- 提交方式为 GET，所有筛选项以**查询参数**形式附加到 `/discographies/` URL 上。

五个控件维度：

| 维度 | 参数名 | 控件类型 | 默认值 | 说明 |
|------|--------|---------|--------|------|
| アーティスト（企划/乐队） | `artist[]` | 多选 checkbox（数组） | `all`（すべて） | 多选时参数重复出现 |
| カテゴリ（类型） | `category` | 单选 radio | `all`（すべて） | CD / Blu-ray / 音楽配信 / LP / 夢ノ結唱 |
| 発売年 | `year` | 下拉 select | `all`（年） | 不限 |
| 発売月 | `month` | 下拉 select | `all`（月） | 不限 |
| キーワード検索 | `s` | 文本输入 | 空 | 匹配作品名/描述 |

> ⚠️ **与 Live 的参数差异**：Live 用 `event_tag` 表示类型；**Discography 用 `category`**。其余 `artist[]` / `year` / `month` / `s` 一致。
>
> 默认状态（不传任何参数）= 全部 artist、全部类型、全部年月，按発売日**降序（新→旧）**排列。未筛选时全站共 **24 页**。

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

### カテゴリ `category`（单选）

| value | 显示名 |
|-------|--------|
| `all` | すべて（默认） |
| `cd` | CD |
| `bluray` | Blu-ray |
| `lp` | LP |
| `streaming` | 音楽配信 |
| `yumeno-kessho` | 夢ノ結唱 |

### 発売年 `year`

`all`（默认，不限）或具体年份。页面当前列出范围 `2016`–`2027`，会随企划活动向上扩展。

### 発売月 `month`

`all`（默认，不限）或 `1`–`12`。年、月各自独立可选：可只选年、只选月或同时指定。

### キーワード `s`

自由文本，匹配作品名称 / 描述。日文需按需做 URL 编码。

## URL 构造规则

**第 1 页**：筛选参数直接挂在 `/discographies/` 之后：

```
https://bang-dream.com/discographies/?artist[]=roselia&category=all&year=all&month=all&s=
```

**第 N 页（N ≥ 2）**：分页为**路径段** `/page/N/`，筛选查询串原样追加在后面：

```
https://bang-dream.com/discographies/page/2/?artist[]=roselia
https://bang-dream.com/discographies/page/4/?artist[]=roselia
```

> ⚠️ **关键点**：分页是路径式 `/page/N/`，**不是** `?page=N`。带上筛选条件时，筛选查询串要拼到分页路径之后。第 1 页用 `/discographies/?{filters}`（不存在 `/page/1/`）。

常用示例：

| 目标 | URL |
|------|-----|
| 只看 Roselia 的作品 | `/discographies/?artist[]=roselia` |
| 只看 CD 类 | `/discographies/?category=cd` |
| 只看 Blu-ray 类 | `/discographies/?category=bluray` |
| 只看 2026 年 | `/discographies/?year=2026` |
| Roselia 的 CD，第 2 页 | `/discographies/page/2/?artist[]=roselia&category=cd` |
| 关键词「Fear Nothing」 | `/discographies/?s=Fear Nothing` |

## 详情页 URL

列表卡片链接形如 `https://bang-dream.com/discographies/<数字ID>/`（如 `/4178/`、`/4218/`），**ID 为纯数字**（非 slug）。采集时从卡片 `href` 取 ID 拼详情页。

## 默认排序

按発売日**降序**（最新 / 近期在前）。例：未筛选首页前几张依次为 2026 年 12 月 → 10 月 → 9 月。

## 与采集相关的注意点

- **抓取前提**：本站为服务端渲染（SSR）——带浏览器 UA 实测，列表页/详情页 HTML 中 `p-discography-form`、`artist[]`、`category`、`発売日`、`収録内容` 等 SSR 标记全部命中，`curl`/py 抓回即可解析，无需 JS 渲染。但**必带浏览器 UA，否则 404 空桩页**——抓取纪律（UA 门禁实测、curl/py 骨架、工具优先级）统一见 [网页抓取策略](./fetch-strategy.md)。
- **务必翻完分页**：未筛选共 **24 页**；筛选后页数减少（实测 `artist[]=roselia` → **4 页**）。采集时遍历所有 `/page/N/`，避免漏取（对应 SKILL.md「页面有分页逻辑」）。
- **筛选后分页拼接**：第 2 页起为 `/discographies/page/N/?{原筛选查询串}`，构造时保留全部筛选参数。
- **artist 多选**：URL 中 `artist[]` 同名出现多次，按数组处理，勿后值覆盖前值。
- **`[]` 无需编码**：查询串中保留字面 `[]` 已验证可被服务端识别（返回 200 且对应选项回显 `checked`）。浏览器中显示为 `%5B%5D` 是 URL 编码，两种写法等价。
- **多企划合辑跨企划命中**：「ガールズバンドパーティ！カバーコレクション」等合辑被打上多个 artist 标签，**按任一参与企划筛选都会出现**。按 Roselia 筛出现 ppp/ag 参与的合辑属正常，勿误判。
- **卡片信息有限**：列表卡片仅含类型标签（CD/Blu-ray/音楽配信/LP/夢ノ結唱）+ 标题 + 発売日 + アーティスト，详细信息（収録内容/特典/価格/品番/購入リンク）需进入卡片链接的详情页（见 SKILL.md 步骤 2 起）。
