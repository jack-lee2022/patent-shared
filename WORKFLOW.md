# Patent Skills — Five-Skill Workflow Guide

本文件說明五個專利分析技能的分工架構、三條標準作業路徑，以及各技能之間的資料交接方式。

---

## 技能生態系架構

```
┌──────────────────────────────────────────────────────────────────┐
│                     資料收集層 (Collection)                        │
│                                                                  │
│  [1] pro-patent-search          [4] patent-downloader           │
│      廣域搜尋 100–500 件              針對性下載 1–20 件 PDF        │
│      輸出：Patent_List.csv           輸出：PDF 全文 + 附圖          │
└──────────────────┬───────────────────────────┬───────────────────┘
                   │                           │
┌──────────────────▼───────────┐ ┌─────────────▼───────────────────┐
│     宏觀分析層 (Macro)         │ │     微觀分析層 (Micro)             │
│                              │ │                                  │
│  [2] patent-mapping          │ │  [5] patent-structured-analysis │
│      9 張策略圖表               │ │      權利要求樹 + FTO + 迴避設計   │
│      Blue Ocean 識別           │ │      輸出：結構化分析報告 .md       │
└──────────────────┬───────────┘ └─────────────────────────────────┘
                   │                           ▲
┌──────────────────▼───────────┐               │
│      策略決策層 (Strategy)      │───────────────┘
│                              │   觸發深度精讀
│  [3] patent-deployment       │
│      五大佈局模式                │──────────────▶ 第二輪搜尋
│      輸出：佈局矩陣              │               回流 [1]
└──────────────────────────────┘
```

---

## 各技能角色一覽

| # | 技能 | 層次 | 處理規模 | 核心輸入 | 核心輸出 |
|---|------|------|---------|---------|---------|
| 1 | **pro-patent-search** | 資料收集（廣） | 100–500 件 | 關鍵字 / IPC / 公司名 | `Patent_List.csv` + 審計報告 |
| 2 | **patent-mapping** | 宏觀分析 | 全量 CSV | `Patent_List.csv` | 9 張策略圖表 |
| 3 | **patent-deployment** | 策略決策 | — | 圖表分析結果 | 佈局模式 + 佈局矩陣 |
| 4 | **patent-downloader** | 資料收集（精） | 1–20 件 | 專利號 / URL | PDF 全文 + 附圖 |
| 5 | **patent-structured-analysis** | 微觀分析 | 單篇精讀 | PDF 全文 | 結構化分析報告（.md） |

---

## 路徑選擇指南

```
需要做什麼？
│
├─ 只需了解技術格局 → 路徑 A
│   （哪些技術已有人占，哪些空白，競爭者態勢）
│
├─ 需要對特定競爭專利做 FTO 或迴避設計 → 路徑 B
│   （我的產品是否侵權？如何設計繞道？）
│
└─ 需要從格局到行動，決定要申請什麼、怎麼卡位 → 路徑 C
    （完整 IP 策略，包含佈局決策與驗證）
```

---

## 路徑 A：技術地圖 + 佈局決策

**適用情境：** 進入新技術領域前的全局掃描；技術地圖報告；競爭者消長分析。

**所用技能：** `pro-patent-search` → `patent-mapping` → `patent-deployment`

```
Step 1  pro-patent-search
        python patent_search_runner.py --topic "霧化器" --outdir "D:\patent\run1"
        輸出：nebulizer_Patent_List.csv + 審計報告
              │
              ▼
Step 2  patent-mapping
        python scripts/advanced/visualizer.py \
            --csv nebulizer_Patent_List.csv \
            --outdir D:\patent\run1\charts \
            --enrich
        輸出：9 張策略圖（技術功效矩陣、競爭者雷達、技術演進時間軸...）
              │
              ▼
Step 3  patent-deployment
        分析圖表輸出 → 選擇佈局模式 → 輸出佈局矩陣
        例：發現「網孔振動 × 藥物精準投遞」為 Blue Ocean
            → 堡壘式：搶先申請廣域專利
            + 斷路式：在競爭者弱項 IPC 維度預埋卡位
```

**各圖表對應的佈局決策：**

| patent-mapping 輸出 | patent-deployment 用途 |
|---|---|
| 技術功效矩陣 Blue Ocean 格 | 堡壘式 / 圍牆式的卡位目標 |
| 競爭者雷達圖（弱項輻軸） | 斷路式的瓶頸點 |
| 技術演進時間軸 | 地毯式時機 / 防禦式放棄衰退分支 |
| 申請人×年度熱圖 | 偵測競爭者突然沉寂（可能轉向） |
| 引證網路（根節點） | 基石專利：授權 or 迴避 or 下游卡位 |
| IPC Treemap | 地毯式覆蓋成本評估 |

---

## 路徑 B：競爭專利精讀 + FTO 評估

**適用情境：** 產品即將上市，需確認是否侵害特定競爭者專利；需要設計迴避方案。

**所用技能：** `pro-patent-search` → `patent-downloader` → `patent-structured-analysis`

```
Step 1  pro-patent-search
        # 找出競爭者核心件（以公司名搜尋）
        python patent_search_runner.py \
            --topic "assignee:Lunatech vibrating mesh" \
            --outdir "D:\patent\fto_run"
        輸出：競爭者專利清單 CSV
              │
              ▼
Step 2  patent-downloader
        # 下載重點競爭專利全文
        python scripts/google_patents_collector.py \
            --query "US10123456B2" --enrich --max 1 --no-tor
        輸出：US10123456B2.pdf + US10123456B2_figures/
              │
              ▼
Step 3  patent-structured-analysis
        # 提供 PDF 路徑，自動執行 5 步分析流程
        「請分析 D:\patent\fto_run\downloads\US10123456B2.pdf」
        輸出：US10123456B2_analysis.md
               ├── 權利要求層次結構（Mermaid Claim Tree）
               ├── 技術組件清單（必要 vs 選用）
               └── FTO / 迴避設計建議
```

**`claim_chart_gen.py`（批次）vs `patent-structured-analysis`（精讀）的選擇：**

| 需求 | 建議工具 |
|------|---------|
| 快速掃描 10+ 件，找出哪些有風險 | `claim_chart_gen.py`（pro-patent-search） |
| 對 1–3 件高風險專利做深度分析、找迴避方案 | `patent-structured-analysis` |

---

## 路徑 C：完整 IP 策略（五技能全用）

**適用情境：** 新技術進入市場前的完整 IP 盡職調查；需要從格局分析到具體申請策略的一站式輸出。

**所用技能：** 全部五個，含兩個回流環

```
Step 1  pro-patent-search（廣域搜尋）
        python patent_search_runner.py --topic "醫療霧化器" --outdir "D:\patent\run1"
              │
              ▼
Step 2  patent-mapping（宏觀分析）
        python scripts/advanced/visualizer.py --csv ... --outdir ... --enrich
              │
              ├── 識別高引用基石專利（引證網路根節點）
              │         │
              │         ▼
              │   Step 3a  patent-downloader（下載基石專利）
              │         │
              │         ▼
              │   Step 3b  patent-structured-analysis（精讀基石專利）
              │            → 確認申請範圍、找迴避空間
              │
              ▼
Step 4  patent-deployment（策略決策）
        依圖表選擇佈局模式，建立佈局矩陣
              │
              ├── 選定圍牆式 ──▶ Step 5a  pro-patent-search（第二輪）
              │                           搜尋 5–10 個周邊技術分支
              │
              ├── 選定斷路式 ──▶ Step 5b  pro-patent-search（競爭者 Assignee）
              │                    │
              │                    ▼
              │               patent-downloader → patent-structured-analysis
              │               確認對手必經瓶頸的具體申請範圍
              │
              └── 選定堡壘式 ──▶ Step 5c  pro-patent-search（無效搜尋）
                                           確認目標 Blue Ocean 格無先前技術
```

---

## 技能間資料交接規格

| 交接點 | 傳遞內容 | 格式要求 |
|--------|---------|---------|
| pro-patent-search → patent-mapping | 專利清單 | CSV，含 `publication_number`, `title`, `assignee`, `year`, `country`, `ipc` |
| patent-mapping → patent-deployment | 圖表分析結果 | PNG 圖表 + Blue Ocean 格清單（`results['blue_ocean']`） |
| patent-mapping → patent-downloader | 目標專利號 | `publication_number` 清單（引證網路根節點或競爭者核心件） |
| patent-downloader → patent-structured-analysis | PDF 全文 + 附圖 | `{PatentNo}.pdf` + `{PatentNo}_figures/` 資料夾 |
| patent-structured-analysis → patent-deployment | 迴避設計建議 | `.md` 報告中的 FTO 節（第 6 節）內容 |
| patent-deployment → pro-patent-search（第二輪） | 針對性搜尋主題 | 技術關鍵字 / Assignee 名稱 / 優先權日條件 |

---

## 快速情境對照表

| 你的問題 | 使用路徑 | 起點技能 |
|---------|---------|---------|
| 「這個技術領域誰在做，哪裡有機會？」 | 路徑 A | pro-patent-search |
| 「我的產品會不會侵害 Lunatech 的專利？」 | 路徑 B | pro-patent-search |
| 「我要怎麼為這個技術做完整的專利布局？」 | 路徑 C | pro-patent-search |
| 「下載並分析這份專利的獨立項」 | 路徑 B（縮短版） | patent-downloader |
| 「幫我畫技術功效矩陣，找 Blue Ocean」 | 路徑 A（從 Step 2）| patent-mapping |
| 「我已有地圖，現在要決定要申請什麼」 | 路徑 A（從 Step 3）| patent-deployment |

---

*本文件由 patent-shared 集中維護。各技能詳細 SOP 請參閱各 repo 的 `SKILL.md`。*