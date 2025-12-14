# Claude Code Documentation Templates

這些模板用於建立「程式碼與文件同步」的強制機制，防止 Claude 疊床架屋。

## 背景

2024-12-14 的教訓：一個簡單的 bug（KJV 高亮問題）本可一行修復（複用 UNV 的參數），但因為沒有查閱現有元件索引，Claude 寫了三個不必要的函數。

**解決方案**：強制 Claude 在修改程式碼前讀取元件索引，修改後更新索引。

## 檔案說明

| 檔案 | 用途 |
|------|------|
| `COMPONENT_INDEX_TEMPLATE.md` | CLAUDE.md 模板，包含元件索引、設計模式、維護規則 |
| `pre-commit-hook-template.sh` | Git hook 模板，阻止未更新文件的 commit |

## 如何套用到新專案

### Step 1: 建立目錄結構

```bash
mkdir -p your-subdir/hooks
```

### Step 2: 複製並客製化 CLAUDE.md

```bash
cp .claude/templates/COMPONENT_INDEX_TEMPLATE.md your-subdir/CLAUDE.md
```

編輯 `your-subdir/CLAUDE.md`：
1. 把 `[SUBDIR]` 換成你的目錄名
2. 填入實際的 Component Index（函數列表）
3. 加入專案特有的 Design Patterns
4. 加入專案特有的 Anti-Patterns

### Step 3: 複製並客製化 pre-commit hook

```bash
cp .claude/templates/pre-commit-hook-template.sh your-subdir/hooks/pre-commit
chmod +x your-subdir/hooks/pre-commit
```

編輯 `your-subdir/hooks/pre-commit`：
```bash
SOURCE_DIR="your-subdir"             # 改成你的目錄
SOURCE_EXT="py"                       # 改成你的副檔名
CLAUDE_MD="your-subdir/CLAUDE.md"    # 改成你的 CLAUDE.md 路徑
```

### Step 4: 安裝 hook

```bash
ln -sf ../../your-subdir/hooks/pre-commit .git/hooks/pre-commit
```

### Step 5: 更新主 CLAUDE.md

在專案根目錄的 `CLAUDE.md` 加入：

```markdown
## Subdirectory Documentation

**When modifying `your-subdir/`**:
- **MUST READ** `your-subdir/CLAUDE.md` first
```

## 兩道防線

### 防線一：Pre-Commit Hook（技術強制）

- 當 `*.js` 有變更但 `CLAUDE.md` 沒變更 → commit 被阻止
- 只能用 `--no-verify` 繞過（應僅限緊急情況）

### 防線二：Session 結束檢查（流程強制）

Claude 在每次 session 結束前必須回答：

| 檢查項目 | 若「是」的動作 |
|---------|---------------|
| 新增了函數？ | 加到 Component Index |
| 刪除了函數？ | 從 Component Index 移除 |
| 改變了函數行為？ | 更新描述 |
| 發現新設計模式？ | 加到 Design Patterns |
| 踩到新坑？ | 加到 Anti-Patterns |

## 為什麼這麼嚴格？

因為「以後再更新」= 永遠不會更新。

文件與程式碼同步是避免重複造輪子的基礎。
