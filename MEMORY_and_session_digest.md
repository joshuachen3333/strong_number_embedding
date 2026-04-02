# Claude Code 記憶系統與 Session Digest 指南

## 三層記憶機制

### 1. MEMORY.md（自動載入）

位置：`~/.claude/projects/{project}/memory/MEMORY.md`

- **每次對話開頭自動載入**（出現在系統訊息 `Contents of memory/MEMORY.md`）
- 但 MEMORY.md **只是索引**（連結），裡面指向的 `.md` 檔案**不會自動全部載入**
- Claude 看到索引後，會根據任務相關性**主動去讀**對應的 memory 檔
- 或者你可以說：「讀一下 session digest」Claude 就會去讀

### 2. CLAUDE.md（自動載入）

位置：repo root 和各子目錄的 `CLAUDE.md`

- **每次對話自動載入**
- 包含項目指令、架構說明、一句話摘要
- 是 Claude 理解 codebase 的第一手資料

### 3. Memory 檔案（手動觸發寫入）

位置：`~/.claude/projects/{project}/memory/*.md`

- **不是自動寫的** — 需要你提醒 Claude 寫入
- 結構化、重點明確、可針對性讀取
- 不受對話壓縮影響，永遠完整

## --resume vs Memory

| | --resume | Memory 檔案 |
|---|---------|------------|
| 載入什麼 | 上次對話的完整 transcript（壓縮後）| 結構化筆記 |
| 精確度 | 壓縮後細節可能丟失 | 完整保留 |
| 自動？ | 是（CLI flag） | 索引自動載入，內容按需讀取 |
| 適合 | 延續對話脈絡 | 精確數字、決定、元件位置 |

### 最佳策略

```
離開前：
  /snapshot          ← 萃取本次 session 精華到 memory（待開發 skill）
  /quit              ← 離開

下次進來：
  claude --resume    ← 載入壓縮的對話脈絡
  「讀一下 session digest，回復上次狀態」 ← 讀精確記憶
```

**兩者互補**：`--resume` 給脈絡（「我們在做什麼」），memory 給精確資訊（「數字是多少、檔案在哪」）。

## Session Digest 格式

每次重要 session 結束前，寫一份 `session_{date}_digest.md`，包含：

```markdown
# Session Digest: YYYY-MM-DD

## 時間線
- 做了什麼，順序是什麼

## 關鍵數字
- 跑分結果、比較數據

## 關鍵 bug 和修正
- 發現什麼問題、怎麼修的

## 核心元件位置
- 哪些檔案在哪裡

## 待做事項
- 下次要接著做什麼

## 用戶偏好
- 這次學到的工作風格偏好
```

## 計畫：/snapshot Skill

未來開發一個 `/snapshot` skill，每次 `/quit` 前呼叫：

1. 掃描本次對話的關鍵決定、數字、bug、檔案變動
2. 自動寫入 `memory/session_{date}_digest.md`
3. 更新 MEMORY.md 索引
4. 提示「安心 /quit」

### 為什麼需要

- 768k 的 context 裡有大量寶貴的迭代細節
- `/quit` 後 `--resume` 的壓縮會丟失精確資訊
- 手動叫 Claude 寫 memory 容易忘記
- `/snapshot` 一鍵搞定，養成習慣

## 目前的 Memory 結構（本項目）

```
~/.claude/projects/{project}/memory/
  ├── MEMORY.md                           ← 索引（自動載入）
  ├── session_20260327_0403_digest.md     ← 768k session 精華
  ├── survey_evolution_story.md           ← S4→S9 來龍去脈
  ├── survey_roadmap.md                   ← 架構總覽 + 元件表
  ├── survey9_current_state.md            ← 目前狀態 + 待做
  ├── repo_paths.md                       ← 機器路徑
  ├── cli_quota_commands.md               ← API 額度查詢
  └── ...其他 survey1 相關記憶
```
