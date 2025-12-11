# Proposal: Enlarge SN Dictionary Tooltip Font

## Summary
Increase the font size of the SN Dictionary tooltip for better readability, with proportionally larger tooltip dimensions and reduced line spacing.

## Motivation
The original tooltip font sizes (12-14px) were difficult to read, especially for the Chinese definition text. Enlarging the fonts and proportionally scaling the tooltip container improves the user reading experience.

## Final Implementation (User Specified)

| 元素 | CSS Class | 原始值 | 最終值 |
|------|-----------|--------|--------|
| 容器最大寬度 | max-width | 420px | 500px |
| 容器最大高度 | max-height | 400px | 480px |
| 容器最小寬度 | min-width | 280px | 340px |
| 內距 | padding | 12px 16px | 15px 20px |
| 基本字體 | font-size | 13px | 18px |
| 基本行距 | line-height | 1.5 | 1.3 |
| SN 編號 | .tooltip-sn | 14px | 19px |
| 希伯來/希臘文 | .tooltip-word | 20px | 26px |
| 音譯 | .tooltip-translit | 13px | 18px |
| 詞性/TWOT | .tooltip-meta | 12px | 16px |
| 定義列表 | .tooltip-def-list | 13px, 1.7 | 18px, 1.5 |
| 子定義 | .tooltip-subdef | 12px | 16px |
| 定義 | .tooltip-def | 13px, 1.6 | 18px, 1.4 |

## Impact
- CSS-only change in `viewer_v2/css/styles.css`
- No JavaScript changes required
- Improved readability for all users
- Tighter line spacing for better content density
