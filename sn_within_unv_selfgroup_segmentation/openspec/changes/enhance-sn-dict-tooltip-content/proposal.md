# Proposal: Enhance SN Dictionary Tooltip Content

## Summary
Expand the Strong's Number dictionary tooltip to display more content and increase its visual size for better readability.

## Problem Statement
The current SN Dict tooltip shows minimal information:
- Hebrew/Greek word (orig)
- Basic transliteration
- Only the first definition line (e.g., "1) 分開, 隔開")

The dictionary data contains much richer content that would benefit users:
- Part of speech (詞性: 名詞、動詞、形容詞等)
- TWOT reference number
- Full numbered definitions with sub-definitions
- Etymology/root references

Additionally, the tooltip area is relatively small, making it difficult to display extended content.

## Proposed Solution

### 1. Increase Tooltip Size
- Increase `max-width` from 280px to 400px
- Increase `max-height` to allow more content (with scrolling if needed)
- Add proper padding and spacing for readability

### 2. Extract and Display More Content
Modify the dictionary content extraction to include:
- **Part of Speech** (詞性): Extract from patterns like "陽性名詞", "動詞", "形容詞"
- **TWOT Reference**: Extract from "TWOT - XXX" pattern
- **Full Definitions**: Show all numbered definitions (1), 2), etc.) not just the first
- **Sub-definitions**: Include 1a), 1b), etc. with proper indentation

### 3. Improved Layout
Structure the tooltip content in sections:
```
H07225 רֵאשִׁית
ray-sheeth'
────────────────
詞性: 陰性名詞
TWOT: 2097e
────────────────
1) 首先, 起頭, 最好的, 首領
   1a) 起初
   1b) 首先
   1c) 首領
   1d) 上好的部份
```

## Scope
- **In Scope**: CSS styling changes, JavaScript extraction logic enhancement
- **Out of Scope**: Dictionary data format changes, adding new data sources

## Success Criteria
1. Tooltip displays part of speech when available
2. Tooltip displays TWOT reference when available
3. Tooltip displays full definitions (up to reasonable limit)
4. Tooltip has adequate size for content display
5. Content remains readable with proper typography hierarchy
