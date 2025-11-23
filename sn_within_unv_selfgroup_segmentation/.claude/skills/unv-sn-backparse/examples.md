# UNV+SN Backparse Examples

## Example 1: Single Verse Parsing

**User Request**: "Parse Genesis 1:1"

**Execution**:
```bash
python run_parser_temp.py 1 1
```

**Expected Output** (Genesis 1:1):
```
Parsed and Formatted Text Section:
<09002><07225> — 介系詞片語「起初」
<0430> — 名詞「神」
<01254>(8804) — 動詞「創造」 *1
<0853> — 受詞記號
<08064> — 名詞「天」
<0853> — 受詞記號
<0776> — 名詞「地」

Raw UNV+SN Source Text Section:
起初<WAH09002><WH07225>，　神<WH0430>創造<WH01254><WTH8804>{<WH0853>}天<WH08064>{<WH0853>}地<WH0776>。

Morphology Notes Section:
*1: 動詞，Qal 完成式 3 單陽 (Verb, Qal Perfect 3rd ms)
```

---

## Example 2: Batch Chapter Parsing

**User Request**: "Parse all verses in Genesis chapter 2"

**Execution Steps**:

1. Create todo list:
   - Create output directory
   - Determine verse count (25 verses)
   - Parse all verses
   - Verify results

2. Create directory:
   ```bash
   mkdir -p output/Gen/2
   ```

3. Batch parse:
   ```bash
   for verse in {1..25}; do python run_parser_temp.py 2 $verse; done
   ```

4. Verify:
   ```bash
   ls -1 output/Gen/2/ | wc -l  # Should show: 25
   ls -1 output/Gen/2/ | grep "_uncertain"  # Should show: 0 (ideally)
   ```

5. Show sample output (verse 1):
   ```
   Parsed and Formatted Text Section:
   <08064> — 冠詞 הַ + 名詞「天」
   <0776> — 連接詞 וְ + 冠詞 הַ + 名詞「地、邦國、疆界」
   <06635> — 名詞「軍隊、戰爭、服役」
   <03605> — 連接詞 וְ + 名詞「全部、整個、各」
   <03615>(8792) — 動詞「Qal 完成、結束、停止，Pi'el 完成、毀壞、根除」 *1

   Raw UNV+SN Source Text Section:
   天<WH08064>地<WH0776>萬物<WH06635>都<WAH03605>造齊了<WH03615><WTH8792>。

   Morphology Notes Section:
   *1: 動詞，Pu'al 敘述式 3 複陽
   ```

6. Report:
   "Successfully parsed Genesis 2:1-25. All 25 verses processed with 0 uncertain files."

---

## Example 3: Parsing with Uncertainty

**User Request**: "Parse Exodus 3:14"

**Scenario**: Verse has ambiguous brace preposition attachment

**Expected Output**:
```
Parsed and Formatted Text Section:
[... normal parsing ...]

Raw UNV+SN Source Text Section:
[... raw text ...]

Morphology Notes Section:
[... morphology notes ...]

--- UNCERTAINTY NOTES ---
Ambiguous brace preposition attachment detected at {<04480>}.
Could not determine if it should attach to preceding verb or following noun.
qp.php data does not show pronoun suffix, and right-side context is ambiguous.
```

**File naming**: `output/Exo/3/14_uncertain`

---

## Example 4: Brace Preposition Decision Tree

### Case A: Object Marker (Always Right-Attach)

**Input**: `... {<0853>}<0216> ...` (light)

**Rule**: Exception 2 - `{<0853>}` always right-attaches to noun

**Output**:
```json
{
  "core": "0216",
  "pre_brace": ["0853"],
  "post_brace": []
}
```

### Case B: Verb Left-Attach Exception

**Input**: `... <0398>(8800){<04480>} ...` (eating + from)

**Context**: `qp.wform` shows "מִמֶּנּוּ" (from-it, pronoun suffix)

**Rule**: Exception 1 - Pronoun suffix → left-attach to verb

**Output**:
```json
{
  "core": "0398",
  "morph": ["8800"],
  "post_brace": ["04480"]
}
```

### Case C: General Right-Attach to Noun

**Input**: `... {<05921>}<06440> ...` (upon + face)

**Context**: Right-side is noun

**Rule**: General case - Right-attach to noun

**Output**:
```json
{
  "core": "06440",
  "pre_brace": ["05921"],
  "post_brace": []
}
```

---

## Example 5: 900x Prefix Attachment with Skipping

**Input**: `<09001>{<0853>}{8804}<0216>` (ל־ + object marker + morph + light)

**Processing**:
1. `<09001>` enters `prefix_buffer`
2. Skip over `{<0853>}` (brace preposition)
3. Skip over `{8804}` (morphology)
4. Attach to `<0216>` (core token)

**Output**:
```json
{
  "core": "0216",
  "prefixes": ["09001"],
  "morph": ["8804"],
  "pre_brace": ["0853"]
}
```

---

## Example 6: Complex Verse with Multiple Features

**Genesis 1:2 - Demonstrates**:
- Brace prepositions
- Construct state linking
- Multiple morphology codes
- Prefix attachments

**Parsed Output** (selected groups):
```
<01961>(8804) — 動詞「是、成為」 *1
<08414> — 名詞「空虛」
<0922> — 連接詞 וְ + 名詞「空」
<02822> — 名詞「黑暗」
<05921><06440> — 介系詞片語「在…面上」
<08415> — 冠詞 הַ + 名詞「深淵」
<07307> — 名詞「靈、風」
<0430> — 名詞「神」
<07363>(8764) — 動詞「盤旋、徘徊」 *2
<05921><06440> — 介系詞片語「在…面上」
<04325> — 冠詞 הַ + 名詞「水」
```

**Features Highlighted**:
- `{<05921>}<06440>` - Brace prep right-attaches to noun
- `<06440>` construct state links to `<08415>` and `<04325>`
- Multiple morphology codes with references (*1, *2)

---

## Example 7: Viewing Output Without Writing

**User Request**: "Show me what Genesis 3:5 would look like parsed"

**Execution**:
```bash
python run_parser_temp.py --no-write 3 5
```

**Use Case**: Preview parsing before committing to file system

---

## Example 8: Verification After Batch Parse

**After parsing Genesis chapters 1-3**:

```bash
# Check total verses
find output/Gen -type f | wc -l

# Check for uncertain files
find output/Gen -name "*_uncertain"

# Verify specific chapter
ls -1 output/Gen/1/ | wc -l  # Should be 31 for Genesis 1

# Spot check sample outputs
cat output/Gen/1/1
cat output/Gen/2/7
cat output/Gen/3/15
```

---

## Example 9: Error Handling - Missing API Data

**Scenario**: `qb.php` returns Strong's number not in `qp.php`

**Detection**: During parsing, `qb_qp_core_mismatch` warning

**Output File**: `{verse}_uncertain`

**Uncertainty Note**:
```
--- UNCERTAINTY NOTES ---
Strong's number <01234> from qb.php does not appear in qp.php record.
Cannot verify word form or part of speech.
Proceeding with qb.php data only.
```

---

## Example 10: Book Abbreviation Mapping

**Supported Formats**:

```bash
# Using English abbreviation
./fetch_text.sh --engs Gen --chap 1 --sec 1
./fetch_text.sh --engs 1Sam --chap 17 --sec 45

# Using Chinese abbreviation
./fetch_text.sh --chineses 創 --chap 1 --sec 1
./fetch_text.sh --chineses 撒上 --chap 17 --sec 45

# List all 66 book mappings
./fetch_text.sh --list
```

**Common Mappings**:
- Genesis ↔ 創
- Exodus ↔ 出
- Matthew ↔ 太
- John ↔ 約
- 1 Samuel ↔ 撒上
- Psalms ↔ 詩

---

## Tips for Best Results

1. **Always create directories first**: `mkdir -p output/{Book}/{Chapter}/`
2. **Use todo lists for multi-step operations**: Track progress through batch parsing
3. **Verify outputs immediately**: Check file count and uncertain files after batch
4. **Show samples to user**: Display 1-2 parsed verses for confirmation
5. **Present output correctly**: All three sections without inserted commentary
6. **Handle uncertainties transparently**: Report any `_uncertain` files and explain issues
