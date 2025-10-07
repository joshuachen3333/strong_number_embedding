# Development Criteria & Guidelines

## 前言
此文檔記錄從慘痛經驗中學到的開發準則。**每次進行任何程式碼修改、功能擴展、除錯或架構調整前，必須先通過此檢查清單。**

---

## 核心開發準則

### 1. 架構一致性檢查
**問題：** 這個修改符合系統的設計模式嗎？

**檢查點：**
- [ ] 是否符合 Mediator 模式的事件發布/訂閱機制？
- [ ] 是否遵循現有的模組職責劃分？
- [ ] 是否保持與現有 API 介面的一致性？
- [ ] 是否符合既有的程式碼風格和命名慣例？

**系統特定模式：**
- MockMediator 為中央事件協調器
- Reader 元件通過事件通信，不直接調用
- Strong's 功能跨元件整合通過標準化事件

### 2. 依賴關係完整性
**問題：** 會破壞現有的初始化順序或事件流嗎？

**檢查點：**
- [ ] 初始化順序：DOM → 事件監聽器 → 狀態同步 → 內容載入
- [ ] 事件流：用戶操作 → 事件發布 → Mediator 協調 → 目標響應
- [ ] 依賴鏈：DOM 元素 → JavaScript 變數 → 功能邏輯
- [ ] 時序敏感操作是否正確使用 setTimeout/Promise

**關鍵依賴：**
- HTML DOM 元素必須在 JavaScript 變數初始化前存在
- 左右 reader 的 follow 狀態互斥關係
- Edit mode 啟用前必須確保 main reader 角色分配

### 3. 狀態管理合理性
**問題：** 是否引入新的狀態不一致？

**檢查點：**
- [ ] JavaScript 變數與 DOM 狀態是否同步？
- [ ] 多個狀態變數之間是否有衝突？
- [ ] 狀態變更是否通過正確的管道？
- [ ] 是否有單一真實來源 (Single Source of Truth)？

**系統狀態映射：**
- `isEditMode` ↔ `editModeToggle.checked`
- Main/Follower 角色 ↔ Follow checkbox 狀態
- Strong's 顯示 ↔ `strongToggle.checked`
- Content 狀態 ↔ localStorage/API 數據

### 4. 功能邊界清晰性
**問題：** 是否違反了模組的職責劃分？

**檢查點：**
- [ ] 左右 reader 是否保持獨立性？
- [ ] MockMediator 是否只負責協調，不處理業務邏輯？
- [ ] Strong's 功能是否正確分散在各元件？
- [ ] localStorage 管理是否集中在適當位置？

**職責邊界：**
- **Left Reader**: 顯示參考內容，提供 Strong's 映射源
- **Right Reader**: 編輯功能，Strong's 建議，localStorage 管理
- **MockMediator**: 事件協調，數據緩存，角色管理
- **App**: 全局設定，語言切換，UI 協調

### 5. 向後相容性
**問題：** 會破壞現有的 API 或介面嗎？

**檢查點：**
- [ ] 現有函數簽名是否保持不變？
- [ ] localStorage 數據格式是否相容？
- [ ] 事件名稱和參數是否一致？
- [ ] CSS 類名和 DOM 結構是否穩定？

### 6. 用戶交互精確性
**問題：** 會干擾用戶的精確點擊和游標定位嗎？

**檢查點：**
- [ ] 是否在 contentArea 添加了 click 事件監聽器？
- [ ] 事件處理是否會延遲或攔截原生游標定位？
- [ ] 是否使用了重度 DOM 分析（TreeWalker、caretRangeFromPoint）？
- [ ] 功能是否提供非侵入性激活方式（雙擊、修飾鍵、開關）？
- [ ] 是否測試了精確游標定位的流暢性？

---

## 系統特定架構要素

### Mediator 模式實現
```javascript
// 正確：通過 Mediator 通信
MockMediator.publish('eventName', data);

// 錯誤：直接調用其他元件
leftReader.someFunction();
```

### 三層載入優先級
```javascript
// 優先級：JSON → localStorage → API
1. 檢查本地 JSON 檔案
2. 檢查 localStorage 儲存
3. 最後才 API 調用
```

### Main/Follower 動態系統
```javascript
// Follow checkbox 邏輯：checked = follower, unchecked = main
// 最後操作的 reader 成為 main，其他成為 follower
```

### Strong's 功能整合點
- **左 reader**: `attachStrongsEventListeners()` - 只讀點擊
- **右 reader**: `attachStrongsEventListenersSecondReader()` - 編輯整合
- **跨 reader**: `WordMappingEngine` - 自動映射

### Edit Mode 狀態管理
```javascript
// 狀態同步順序
1. HTML checkbox 為 Single Source of Truth
2. JavaScript 變數在初始化時同步
3. 狀態變更通過事件處理器
```

---

## 修改前檢查流程

### Step 1: 問題分析
- [ ] 明確定義要解決的具體問題
- [ ] 分析問題的根本原因，不只是表面症狀
- [ ] 確認問題的影響範圍和優先級

### Step 2: 架構審查
- [ ] 檢查上述 5 個核心準則
- [ ] 識別可能受影響的系統元件
- [ ] 評估是否有更符合現有架構的解決方案

### Step 3: 設計方案
- [ ] 設計最小影響的實現方案
- [ ] 確認修改的原子性（可獨立測試和回滾）
- [ ] 準備測試驗證計劃

### Step 4: 實施檢查
- [ ] 一次只修改一個邏輯概念
- [ ] 每次修改後立即測試驗證
- [ ] 確認未破壞既有功能

### Step 5: 完整性驗證
- [ ] 測試修改是否解決了原問題
- [ ] 驗證未引入新的問題
- [ ] 確認系統整體功能正常

---

## 反面案例記錄

### 案例 1: localStorage 直接載入錯誤
**錯誤做法：** 跳過 API 載入，直接從 localStorage 建立頁面
**問題：** 破壞了完整的初始化流程，丟失 Strong's 功能
**正確做法：** 先 API 載入完整功能，再用 restoreEditedContent 覆蓋

### 案例 2: 狀態不同步錯誤
**錯誤做法：** HTML checkbox checked=true，JavaScript isEditMode=false
**問題：** 狀態不一致導致條件判斷錯誤
**正確做法：** 初始化時同步狀態：isEditMode = editModeToggle.checked

### 案例 3: 缺少函數錯誤
**錯誤做法：** 調用不存在的 addVerseEditingListeners()
**問題：** 破壞了 localStorage 恢復流程
**正確做法：** 使用既有的事件監聽器機制

### 案例 4: 點擊事件干擾精確游標定位錯誤
**錯誤做法：** 在 contentArea 添加 click 事件監聽器進行功能擴展（如 A1/A2 高亮系統）
**問題：** JavaScript 事件處理干擾瀏覽器原生游標定位，導致點擊定位變得不精確和遲鈍
**技術原因：**
- 事件委託攔截所有點擊事件
- DOM 遍歷和結構解析增加處理延遲
- caretRangeFromPoint 和 TreeWalker 分析造成性能開銷
- 自定義事件處理與瀏覽器原生行為衝突
**正確做法：**
- 使用非侵入性激活方式（雙擊、修飾鍵、特殊模式）
- 實施輕量級檢測邏輯，避免重度 DOM 處理
- 讓瀏覽器先處理游標定位，再添加功能邏輯
- 提供功能開關，允許用戶關閉干擾性功能

---

## 核心架構元素清單 (CRITICAL ARCHITECTURE INVENTORY)

### 不可違背的關鍵函數

#### MockMediator 核心協調函數
```javascript
// 事件系統 - 所有跨元件通信的基礎
subscribe(eventName, callback)    // 事件訂閱機制
publish(eventName, data)          // 事件發布機制，含錯誤處理
events 物件結構                   // pub/sub 模式的核心

// 數據管理 - 三層載入系統
fetchChapter(book, chapter, version, strong)  // API 整合與快取
_bookDataCache                               // 防止重複 API 呼叫
clearCache()                                // 版本切換時的快取失效

// 同步協調 - Main/Follower 系統
syncPosition(payload)                       // 章節級同步
setMainReader(readerType, interaction)      // 角色管理
getMainReader() / getFollowerReader()       // 角色狀態查詢
registerLeftReaderUpdateCallback(callback)  // 左 reader 回調註冊
registerRightReaderUpdateCallback(callback) // 右 reader 回調註冊

// 關鍵狀態變數
_mainReader        // 'left' 或 'right'，預設 'right'
_currentSynchedVerse  // 全局章節位置狀態
```

#### Reader 初始化函數 (不可更動順序)
```javascript
// 左 Reader
loadLeftPassage(book, chapter, verse)  // Mediator 同步回調
initializeLeftReaderDefaults()         // UNV、Strong's ON、跟隨右 reader
loadChapterContent()                   // 主要內容載入

// 右 Reader
loadPassage(book, chapter, verse)      // Mediator 同步回調
loadChapterContent()                   // 三層載入系統
displaySyncedContent()                 // 跟隨者內容同步
initializeRightReaderDefaults()        // LCC、Edit Mode ON
```

#### 三層載入系統 (Critical Priority Order)
```javascript
// 優先級順序 - 絕對不可改變
1. 本地 JSON 檔案 (${book}_${chapter}_${version}_edited.json)
2. localStorage 快取
3. API 調用 (bible.fhl.net)

// 關鍵載入函數
loadFromJsonFile(jsonData)    // JSON 檔案處理
restoreEditedContent()        // localStorage 恢復 (僅在 renderChapter 後)
MockMediator.fetchChapter()   // API 整合與快取
```

#### Strong's Number 系統函數
```javascript
// 解析函數 (兩個 reader 必須同步)
parseStrongsNumbers(text)           // 4 種格式轉換為可點擊 span
// 格式: {<WH1234>}, {H1234}, <WH1234>, (H1234)

// 事件函數
attachStrongsEventListeners()       // 左 reader - 唯讀點擊
attachStrongsEventListenersSecondReader()  // 右 reader - 編輯整合
// 發布 'strongsNumberClicked' 事件到 MockMediator
```

#### Edit Mode 函數 (右 Reader 專有)
```javascript
// 狀態管理
isEditMode                 // 與 editModeToggle.checked 同步
currentEditingVerse        // 當前編輯的 verse
handleEditModeToggle()     // Edit mode 切換處理

// 自動儲存系統
saveEditedContent()        // localStorage 持久化
autoSaveTimer             // 定時自動儲存
hasUnsavedChanges         // 變更追蹤標記

// Undo/Redo 系統
undoStack / redoStack     // 編輯歷史堆疊
isUndoRedoAction          // 防止無限迴圈標記
```

### 不可破壞的核心元件

#### 關鍵 DOM 元素 (ID 選擇器)
```javascript
// Reader 容器
'left-reader-content-area', 'right-reader-content-area'
'left-reader-book', 'right-reader-book'
'left-reader-chapter', 'right-reader-chapter'
'left-reader-version-select', 'right-reader-version-select'
'left-reader-strong-toggle', 'right-reader-strong-toggle'

// Follow 系統 checkbox (Main/Follower 邏輯的核心)
'left-reader-follow-scroll', 'left-reader-follow-selection'
'right-reader-follow-scroll', 'right-reader-follow-selection'

// Edit Mode (右 reader 專有)
'right-reader-edit-mode'
'right-reader-strong-controls'
'strong-number-input', 'insert-strong-btn'
```

#### 功能性 Data 屬性
```javascript
data-verse="${verseNum}"        // Verse 識別，滾動同步用
data-book="${bookChinese}"      // Book 識別，API 調用用
data-chapter="${chapterNum}"    // Chapter 識別
data-strong="${strongsId}"      // Strong's number 識別
data-original="${content}"      // 編輯變更追蹤用
```

#### 功能性 CSS 類別
```javascript
.verse              // Verse 容器類別
.verse-number       // Verse 編號 span
.strongs-number     // 可點擊 Strong's number span
.verse-highlighted  // 同步滾動高亮
```

### 不可違背的關鍵關係

#### Main/Follower 系統 (最脆弱的架構)
```javascript
// Follow Checkbox 邏輯 - 絕對不可更動
Parent-Child 關係: Follow Text Selection (父) → Follow Verse Scroll (子)
Last Checkbox Wins: 任何 follow checkbox 被勾選 → 該 reader 變成 follower
Cross-Reader 更新: 勾選 follow → 自動取消其他 reader 的 follow
即時同步: follower 立即同步到 main reader 當前位置

// 角色決定規則
兩個 follow checkbox 都未勾選 = MAIN reader
任一 follow checkbox 勾選 = FOLLOWER reader
不可能兩個 reader 同時為 follower
```

#### 事件系統架構
```javascript
// 核心事件名稱 (不可更動)
'leftReaderChapterChanged'   // 左 reader 章節導航
'rightReaderChapterChanged'  // 右 reader 章節導航
'mainReaderChanged'          // Main/Follower 角色變更
'strongsNumberClicked'       // Strong's number 互動

// 事件數據結構 (必須保持格式)
Chapter Change: {book, chapter, version, internalVersionValue, strong, verses}
Main Reader Change: {newMain, newFollower, interaction}
Sync Position: {book, chapter, verse, mainReaderVersion}
```

#### Strong's 整合點
```javascript
// 跨元件依賴關係
解析函數在兩個 reader 中必須同步
事件發布只從 main reader 發出
Word mapping 依賴 edit mode 狀態
Click handlers 在 renderChapter() 時附加
```

### 不可更動的初始化序列
```javascript
1. DOM Ready → 所有 reader 的 DOMContentLoaded 監聽器
2. Book 下拉選單填充 → 兩個 reader 的相同 book 陣列
3. MockMediator 回調註冊 → readers 註冊 update callbacks
4. 預設初始化 → 左 reader 設定預設值，右 reader 等待
5. 事件監聽器附加 → 所有控制項監聽器
6. 初始內容載入 → 左 reader 載入創世記 1 章

// 順序依賴關係 (不可顛倒)
MockMediator 必須在 readers 之前載入 (index.html script 順序)
Book 陣列必須在任何 book 選擇前填充
回調註冊必須在任何同步前發生
Follow checkbox 邏輯必須在用戶互動前完全初始化
```

### 狀態同步模式
```javascript
// 單一真實來源模式
HTML checkbox 狀態 → JavaScript 變數狀態
editModeToggle.checked → isEditMode
followCheckbox.checked → Main/Follower 角色

// 狀態變更流程
用戶互動 → DOM 事件 → 狀態更新 → MockMediator 協調 → 跨元件同步
```

---

## 文檔更新要求

此文檔應隨著系統複雜度增長而持續更新：
- 每次發現新的架構問題，添加到反面案例
- 系統新增主要功能時，更新架構要素
- 開發準則經過實踐驗證後，優化檢查流程

**更新原則：** 從實際錯誤中學習，不斷完善開發標準。