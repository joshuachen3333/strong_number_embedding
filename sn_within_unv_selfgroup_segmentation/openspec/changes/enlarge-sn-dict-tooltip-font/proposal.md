# Proposal: Enlarge SN Dictionary Tooltip Font

## Summary
Increase the font size of the SN Dictionary tooltip for better readability, with proportionally larger tooltip dimensions.

## Motivation
The current tooltip font sizes (12-14px) can be difficult to read, especially for the Chinese definition text. Enlarging the fonts and proportionally scaling the tooltip container will improve the user reading experience.

## Current State
- Container: 420px max-width, 400px max-height, 13px base font
- Hebrew/Greek word: 20px
- Definition text: 12-13px
- Padding: 12px 16px

## Proposed Changes
Proportionally enlarge all font sizes by 20%:

| Element | Current | Proposed (+20%) |
|---------|---------|-----------------|
| Container max-width | 420px | 500px |
| Container max-height | 400px | 480px |
| Container min-width | 280px | 340px |
| Padding | 12px 16px | 15px 20px |
| Base font | 13px | 16px |
| SN code | 14px | 17px |
| Hebrew/Greek word | 20px | 24px |
| Transliteration | 13px | 16px |
| Meta (詞性/TWOT) | 12px | 14px |
| Definition list | 13px | 16px |
| Sub-definition | 12px | 14px |

## Impact
- CSS-only change in `viewer_v2/css/styles.css`
- No JavaScript changes required
- Improved readability for all users
