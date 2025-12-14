# [SUBDIR]/CLAUDE.md Template

**Usage**: Copy this template to `[your-subdir]/CLAUDE.md` and customize.

---

# [SUBDIR]/CLAUDE.md

**MUST READ** this file before modifying any code in `[SUBDIR]/`.

## Component Index

Quick reference of all functions by file. Use this to find existing solutions before adding new code.

### [file1.js] — [Brief Description]
| Function | Purpose |
|----------|---------|
| `functionName(params)` | One-line description |
| `anotherFunction()` | One-line description |

### [file2.js] — [Brief Description]
| Function | Purpose |
|----------|---------|
| `functionName(params)` | One-line description |

---

## Design Patterns

### Pattern 1: [Pattern Name]

**Problem**: [What problem does this solve?]

**Solution**: [How does the code solve it?]

```javascript
// CORRECT example
correctCode();

// WRONG example
wrongCode();
```

**Where Applied**: [List files/functions that use this pattern]

---

## Anti-Patterns (禁止事項)

### 1. 疊床架屋 (Redundant Components)

**FORBIDDEN**: Adding new functions when existing ones can be extended.

Before adding ANY new function, ask:
1. "Does another component already solve this?"
2. "Can I compare how similar code works elsewhere?"
3. "Is the fix just passing the correct parameters?"

### 2. [Another Anti-Pattern]

**FORBIDDEN**: [Description]

```javascript
// WRONG
wrongApproach();

// CORRECT
correctApproach();
```

---

## Pre-Task Checklist

Before fixing ANY bug:

- [ ] **Search for similar code**: `grep -r "functionName" [SUBDIR]/`
- [ ] **Check this CLAUDE.md**: Is there an existing function that does this?
- [ ] **If Version B is broken but Version A works**: Compare how A and B call the same function
- [ ] **Before adding new function**: Explain why existing functions cannot solve it

---

## Maintenance Rule (維護規則)

**本文件必須與程式碼同步。** 這不是建議，是強制要求。

### 機制一：Git Pre-Commit Hook

安裝 `hooks/pre-commit`，當你修改 `[SUBDIR]/*.js` 但沒有同時修改 `[SUBDIR]/CLAUDE.md` 時，commit 會被阻止。

### 機制二：Session 結束前檢查

**Claude 必須在每次 session 結束前執行：**

如果本次 session 修改了 `[SUBDIR]/*.js`，回答以下問題：

| 檢查項目 | 是/否 | 若「是」的動作 |
|---------|------|---------------|
| 新增了函數？ | | 加到 Component Index 表格 |
| 刪除了函數？ | | 從 Component Index 移除 |
| 改變了函數簽名或行為？ | | 更新對應描述 |
| 發現了新的設計模式？ | | 加到 Design Patterns |
| 踩到了新的坑（反模式）？ | | 加到 Anti-Patterns |

**任一項為「是」但未更新本文件 → 不得結束 session 或 commit。**

---

## Quick Debugging Commands

```bash
# Find all uses of a function
grep -rn "functionName" [SUBDIR]/

# Compare implementations
grep -A5 "functionA\|functionB" [SUBDIR]/[file].js
```
