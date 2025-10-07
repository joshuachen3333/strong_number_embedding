# Advanced Highlighting Functions Todo

## 6 Potential Advanced Highlighting Functions

**A** - Cross-reader word highlighting improvements
**B** - Strong's number highlighting enhancements
**C** - Verse-level highlighting features
**D** - Search-based highlighting
**E** - Multi-word phrase highlighting
**F** - Contextual highlighting based on Strong's relationships

## Current User Wishes

### **A - Cross-reader word highlighting improvements (保守且精準策略)**

**現狀分析**：
- ✅ 現有點擊精確度很好
- ✅ 左側橘色高亮機制正常運作
- ✅ 字詞偵測邏輯已經存在
- ❌ 右側藍色高亮有兩個問題需修復

**A1** - 修復右側基本高亮缺失：確保右側至少高亮被點擊的單個字 (最小修改現有機制)
**A2** - 新增詞彙邊界擴展：從單字擴展到完整詞 (起→起初, 創→創造, 上→上帝)
**A3** - [保留] Right→Left smart highlighting: Click right term → left highlights text+SN, click right SN → left highlights SN only
**A4** - [保留] Left→Right smart highlighting: Click left term → right highlights text+SN, click left SN → right highlights SN only
**A5** - [保留] Shift+Click manual correction: Purple highlighting for manually corrected mappings with verse background
**A6** - [保留] Smart algorithm learning: Improve auto-mapping algorithm instead of rigid overrides
**A7** - [保留] Human feedback learning data: Record corrections for future AI training and pattern analysis

**實施原則**：
- 🔒 **嚴格禁止**：添加新的 click 事件監聽器到 contentArea
- 🔒 **嚴格禁止**：使用重度 DOM 分析 (TreeWalker, caretRangeFromPoint)
- ✅ **允許**：修改現有高亮邏輯
- ✅ **允許**：增強現有字詞偵測算法
- ✅ **優先**：保持點擊精確性

### **B - Strong's number highlighting enhancements**
*(No wishes added yet)*

### **C - Verse-level highlighting features**
**C1** - Whole verse background highlighting: Very light blue (clicked side) / very light orange (cross-highlighted side)
**C2** - Consistent color scheme: Clicked=Blue theme, Non-clicked=Orange theme (regardless of left/right reader)

### **D - Search-based highlighting**
*(No wishes added yet)*

### **E - Multi-word phrase highlighting**
*(No wishes added yet)*

### **F - Contextual highlighting based on Strong's relationships**
*(No wishes added yet)*

## Implementation Status
- **Ready for coding**: Awaiting "That's all, go coding now" signal
- **Current wish count**: 7 A-items, 2 C-items
