# Proposal: Add Spec References to Output

## Change ID
`add-spec-references-to-output`

## Summary
Enhance the parsed verse output format to include SPECIFICATION_v1.8 version metadata in the section header and append spec rule references to multi-token groups, enabling users to trace which parsing rules were applied to each semantic group.

## Why
Users need to understand which SPECIFICATION_v1.8 rules govern each parsed group. Currently, the output shows semantic groupings but doesn't indicate which specification section (e.g., §3.3.1 for prefix attachment, §3.3.2 for morphology attachment) was applied. This makes it difficult to:
- Understand why tokens were grouped together
- Validate parser behavior against the specification
- Debug unexpected parsing results
- Learn the parsing rules through examples

## Motivation
**Current behavior:**
```
Parsed and Formatted Text Section:
<09002><07225> — 介系詞 בְּ + 名詞「開始、首要」
<0430> — 名詞「上帝、神、神明」
<01254>(8804) — 動詞「Qal 創造；Pi'el 砍伐；Hif'il 肥己」 *1
{<0853>}<08064> — 冠詞 הַ + 名詞「天」
{<0853>}<0776> — 冠詞 הַ + 名詞「地、邦國、疆界」
```

**Desired behavior:**
```
Parsed and Formatted Text Section (SPECIFICATION_v1.8)
<09002><07225> — 介系詞 בְּ + 名詞「開始、首要」                              [3.3.1]
<0430> — 名詞「上帝、神、神明」
<01254>(8804) — 動詞「Qal 創造；Pi'el 砍伐；Hif'il 肥己」 *1                 [3.3.2]
{<0853>}<08064> — 冠詞 הַ + 名詞「天」    ::{<0853>}天<08064>::               [3.3.3]
{<0853>}<0776> — 冠詞 הַ + 名詞「地、邦國、疆界」    ::{<0853>}地<0776>::     [3.3.3]
```

## User Impact
**Before:**
- No indication of specification version
- No way to trace which rule created each group
- Cannot distinguish between single-token groups (no rules applied) and multi-token groups (rules applied)

**After:**
- Section header shows `(SPECIFICATION_v1.8)` to indicate parsing spec version
- Multi-token groups (2+ Strong's Numbers) display spec section reference right-aligned at column 80 (e.g., `[3.3.1]`)
- Groups with interleaved Chinese text show original text arrangement with `::` markers (e.g., `::{<0853>}天<08064>::`)
- Single-token groups remain unchanged (no spec reference needed)

## Scope
**In Scope:**
1. Add `(SPECIFICATION_v1.8)` suffix to "Parsed and Formatted Text Section" header
2. Track which parsing rule created each group (metadata in group dict)
3. Display spec section references for multi-token groups (right-aligned at column 80)
4. Detect and display interleaved text (SN-Chinese-SN patterns) with `::` delimiters
5. Format output with proper alignment and spacing

**Out of Scope:**
- Changing existing parsing logic or rules
- Adding spec references to single-token groups
- Modifying JSON output format (text format only)
- Adding spec references to uncertainty notes or warnings
- Changing the SPECIFICATION_v1.8.md document itself

## Dependencies
- Requires SPECIFICATION_v1.8.md to remain stable (chapter numbering)
- No external dependencies
- No changes to `fetch_text.sh` or API integration

## Alternatives Considered
1. **Add spec references to all groups**: Rejected because single-token groups don't use grouping rules, so references would be meaningless
2. **Use hover tooltips in viewer**: Rejected because this is a parser output enhancement, not a viewer feature; text format is primary
3. **Create separate spec reference section**: Rejected because inline references provide better context and readability

## Risks
**Low Risk:**
- Text formatting changes only, no logic changes
- Backward compatible (existing parsers can still read output, just ignore extra annotations)

**Medium Risk:**
- Fixed column width (80) might cause alignment issues with very long Chinese descriptions
- Interleaved text extraction requires accurate position tracking in raw text

**Mitigation:**
- Make column width configurable (default 80, can adjust via constant)
- Implement robust interleaved text detection with fallback to omit if extraction fails
- Add validation tests with known verses (Gen 1:1, Gen 3:5, Gen 4:16)

## Success Criteria
1. Header shows `Parsed and Formatted Text Section (SPECIFICATION_v1.8)`
2. Multi-token groups display spec references right-aligned at column 80
3. Interleaved text (SN-Chinese-SN) displayed with `::` delimiters
4. Single-token groups show no spec reference
5. Alignment is visually clean and consistent across multiple verses
6. No changes to JSON output format
7. All existing test cases pass unchanged
