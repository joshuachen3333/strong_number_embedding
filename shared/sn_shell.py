"""SN Shell — strip and restore FHL Strong's Number format.

Strip (去殼): <WH07225> → <7225>, {<WH0853>} → <853>, <WTH8804> → <8804>
Restore (加殼): <7225> → <WH07225>, <853> → {<WH0853>} (with rules)

Angle brackets are preserved as delimiters to prevent number merging.
Only the prefix (WH, WAH, WTH, WTG), zero-padding, and braces are stripped.

Used by survey8 and potentially survey4/5/6 with --simplest flag.
"""

import re


# Regex to match any FHL SN tag (with optional braces)
# Matches: <WH07225>, <WAH09002>, <WTH8804>, {<WH0853>}, <WG3588>, <WG1980a>, etc.
_TAG_RE = re.compile(r'\{?<W[ATG]*[HG]\d+[a-z]?>\}?')

# Extract just the number (and optional letter suffix) from a tag
_NUM_RE = re.compile(r'(\d+[a-z]?)')


def strip_shell(text, markers=True):
    """Strip FHL SN tags to simplified format in angle brackets.

    markers=True (方案 A): preserves type markers for perfect roundtrip
        <WH07225> → <7225>, <WAH09002> → <P9002>, <WTH8804> → <M8804>,
        {<WH0853>} → <I853>, <WAH0430> → <A430>

    markers=False (方案 B): bare numbers only, LLM simplest possible
        <WH07225> → <7225>, <WAH09002> → <9002>, <WTH8804> → <8804>,
        {<WH0853>} → <853>, <WAH0430> → <430>
    """
    def _replace(m):
        tag = m.group(0)
        num_match = _NUM_RE.search(tag)
        if not num_match:
            return tag
        num = num_match.group(1)

        if not markers:
            return f"<{num}>"

        # Determine marker from tag structure
        is_braced = tag.startswith('{')
        is_morph = 'WT' in tag          # WTH or WTG
        is_wah = 'WAH' in tag or 'WAG' in tag
        raw_num = int(num.rstrip('abcdefghijklmnopqrstuvwxyz') or '0')

        if is_braced and is_morph:
            return f"<IM{num}>"
        elif is_braced and is_wah and 9000 <= raw_num <= 9999:
            return f"<IP{num}>"
        elif is_braced and is_wah:
            return f"<IA{num}>"
        elif is_braced:
            return f"<I{num}>"
        elif is_morph:
            return f"<M{num}>"
        elif is_wah and 9000 <= raw_num <= 9999:
            return f"<P{num}>"
        elif is_wah:
            return f"<A{num}>"
        else:
            return f"<{num}>"

    return _TAG_RE.sub(_replace, text)


def extract_bare_numbers(text):
    """Extract all bare SN numbers from stripped text, in order.

    Returns list of strings: ['7225', '430', '1254', '8804', '853', ...]
    """
    # After strip_shell, numbers are in <number>, <Mnumber>, <IAnumber> etc.
    return re.findall(r'<((?:IA|IP|IM|[MPIA])?\d+[a-z]?)>', text)


def build_shell_lookup(unv_sn_text):
    """Build lookup: bare number -> original FHL tag from UNV+SN (zero-loss).

    Maps each source tag's stripped bare number to its full original tag, e.g.
    {'07225': '<WH07225>', '09002': '<WAH09002>', '0853': '{<WH0853>}',
     '8804': '<WTH8804>'}. Used to restore shells by table lookup with no
    guessing — the source UNV+SN already prints every SN's original shell.

    First occurrence wins: if the same number appears with two different shells
    (§2.1 boundary, e.g. once <WH0853> once {<WH0853>}), the first is kept.
    Callers doing golden work should flag such same-number-different-shell
    nodes for human review.
    """
    lookup = {}
    for m in _TAG_RE.finditer(unv_sn_text):
        raw = m.group(0)
        num = strip_shell(raw, markers=False).strip("<>")
        if num not in lookup:
            lookup[num] = raw
    return lookup


def restore_shell_lookup(stripped_text, lookup):
    """Restore bare <number> tags to original FHL format via table lookup.

    Zero-loss counterpart to restore_shell_guess(): each <number> is replaced
    by its original tag from `lookup` (built by build_shell_lookup). A number
    absent from the table is deliberately left bare (<number>) — that is a red
    flag (LLM emitted an SN not present in the source UNV+SN) for a judge or
    human to catch, rather than masking it with a plausible guessed shell.
    """
    def _replace(m):
        return lookup.get(m.group(1), m.group(0))
    return re.sub(r'<(\d+[a-z]?)>', _replace, stripped_text)


def _zero_pad(num_int, testament="OT", orig_digits=None):
    """Apply FHL zero-padding rule.

    OT: preserve original digit count from FHL tag.
        Common patterns: 0430 (4-digit), 07225 (5-digit), 00 (2-digit), 068 (3-digit)
        Fallback: < 1000 → 4 digits, >= 1000 → 5 digits
    NT: no padding (746, 1722, 3056)
    """
    if testament == "NT":
        return str(num_int)
    if orig_digits is not None:
        return f"{num_int:0{orig_digits}d}"
    if num_int < 1000:
        return f"{num_int:04d}"
    else:
        return f"{num_int:05d}"


def restore_tag(tagged_num, testament="OT"):
    """Restore a simplified tag to FHL format.

    Args:
        tagged_num: simplified tag content, e.g. '7225', 'M8804', 'P9002', 'I853', 'A430'
        testament: 'OT' or 'NT'

    Returns:
        FHL tag string, e.g. '<WH07225>', '<WTH8804>', '<WAH09002>', '{<WH0853>}'

    Markers:
        (none) = core SN
        M = morphology (WTH/WTG)
        P = 900x prefix (WAH09xxx)
        I = implicit ({<WH>})
        A = WAH non-900x
    """
    marker = ""
    num_str = tagged_num
    # Check for two-letter markers first (IA, IP, IM)
    if tagged_num[:2] in ("IA", "IP", "IM"):
        marker = tagged_num[:2]
        num_str = tagged_num[2:]
    elif tagged_num and tagged_num[0] in "MPIA":
        marker = tagged_num[0]
        num_str = tagged_num[1:]

    # Handle letter suffix (NT variant lemma)
    suffix = ""
    clean = num_str
    if num_str and num_str[-1].isalpha():
        suffix = num_str[-1]
        clean = num_str[:-1]

    try:
        num = int(clean)
    except ValueError:
        return f"<{tagged_num}>"  # fallback

    lang = "H" if testament == "OT" else "G"

    # For restore, use the original digit string (preserves leading zeros)
    # num_str still has the original form (e.g. '07225', '0430', '00', '068')
    num_orig = f"{clean}{suffix}"  # recombine digits + optional letter suffix

    if marker == "IM":
        prefix = f"WT{lang}"
        return "{" + f"<{prefix}{clean}>" + "}"
    elif marker == "IP":
        return "{" + f"<WAH{num_orig}>" + "}"
    elif marker == "IA":
        prefix = f"WA{lang}"
        return "{" + f"<{prefix}{num_orig}>" + "}"
    elif marker == "P":
        return f"<WAH{num_orig}>"
    elif marker == "M":
        prefix = f"WT{lang}"
        return f"<{prefix}{clean}>"
    elif marker == "I":
        prefix = f"W{lang}"
        return "{" + f"<{prefix}{num_orig}>" + "}"
    elif marker == "A":
        prefix = f"WA{lang}"
        return f"<{prefix}{num_orig}>"
    else:
        prefix = f"W{lang}"
        return f"<{prefix}{num_orig}>"


def restore_shell(stripped_text, testament="OT"):
    """Restore <number> tags in text back to FHL tag format.

    Args:
        stripped_text: text with <number> tags (output from LLM or strip_shell)
        testament: 'OT' or 'NT'

    Returns:
        text with FHL-formatted tags

    Note: This basic version does NOT handle:
    - Implicit markers {} (all tags are bare, no braces added)
    - WAH vs WH distinction for non-900x tags
    These require additional context (per-SN statistics or ground truth patterns).
    """
    def _replace(m):
        num_str = m.group(1)
        return restore_tag(num_str, testament)

    # Match <number>, <Mnumber>, <IAnumber>, <IPnumber>, <IMnumber>, etc.
    return re.sub(r'<((?:IA|IP|IM|[MPIA])?\d+[a-z]?)>', _replace, stripped_text)


# --- Scoring helpers ---

# Implicit SN analysis (2026-03-30, full Bible 31103 verses):
# No SN exceeds 90% braced rate. Highest: 1161(δέ)=65%, 853(את)=59%.
# Implicit braces depend on CONTEXT, not SN number alone.
# → KNOWN_IMPLICIT strategy abandoned. Production uses UNV+SN lookup instead.
KNOWN_IMPLICIT_OT = set()
KNOWN_IMPLICIT_NT = set()


def restore_shell_guess(stripped_text, testament="OT", core_sns=None):
    """Restore bare numbers (no markers) to FHL format by guessing type.

    Used in 方案 B where LLM outputs only <number> without markers.

    Args:
        stripped_text: text with <number> tags from LLM
        testament: 'OT' or 'NT'
        core_sns: set of SN numbers (int) from qp.php for this verse.
            If provided, any 8xxx number IN this set is core SN,
            any 8xxx number NOT in this set is morphology.
            Without this, all 8xxx are guessed as morphology (lossy).

    Guessing rules:
        9000-9999 → <WAH09xxx> (900x prefix)
        8000-8999 → core if in core_sns, else morphology
        in KNOWN_IMPLICIT → {<WHxxxx>} (implicit)
        others → <WHxxxx> or <WGxxxx> (core SN)
    """
    known_implicit = KNOWN_IMPLICIT_OT if testament == "OT" else KNOWN_IMPLICIT_NT

    def _replace(m):
        num_str = m.group(1)
        clean = num_str.rstrip('abcdefghijklmnopqrstuvwxyz')
        suffix = num_str[len(clean):]
        try:
            num = int(clean)
        except ValueError:
            return f"<{num_str}>"

        lang = "H" if testament == "OT" else "G"

        # 900x prefix
        if 9000 <= num <= 9999:
            return f"<WAH{num_str}>"

        # 8xxx: use core_sns to disambiguate
        if 8000 <= num <= 8999:
            if core_sns and num in core_sns:
                # It's a core SN (e.g. 8064=heaven), not morphology
                prefix = f"W{lang}"
                return f"<{prefix}{num_str}>"
            else:
                # Morphology
                prefix = f"WT{lang}"
                return f"<{prefix}{clean}>"

        # Known implicit
        if num in known_implicit:
            prefix = f"W{lang}"
            return "{" + f"<{prefix}{num_str}>" + "}"

        # Core SN
        prefix = f"W{lang}"
        return f"<{prefix}{num_str}>"

    return re.sub(r'<(\d+[a-z]?)>', _replace, stripped_text)


def fix_placement(text, core_sns=None):
    """Fix obvious placement errors in stripped SN output.

    Rule-based corrections that are structurally universal (not verse-specific):

    1. Morphology after core SN:
       8xxx (not in core_sns) must follow a core SN, never precede it.
       <8804><1254> → <1254><8804>

    2. 900x prefix before core SN:
       9xxx must precede a core SN, never follow it.
       <7225><9002> → <9002><7225>

    Args:
        text: stripped text with <number> tags
        core_sns: set of core SN numbers (int) from qp.php. If None,
            8000-8999 are assumed morphology, 9000-9999 are prefix.

    Returns:
        text with corrected tag order
    """
    def _is_morph(num_str):
        clean = num_str.rstrip('abcdefghijklmnopqrstuvwxyz')
        try:
            n = int(clean)
        except ValueError:
            return False
        if 8000 <= n <= 8999:
            return not (core_sns and n in core_sns)
        return False

    def _is_prefix(num_str):
        clean = num_str.rstrip('abcdefghijklmnopqrstuvwxyz')
        try:
            n = int(clean)
        except ValueError:
            return False
        return 9000 <= n <= 9999

    def _is_core(num_str):
        return not _is_morph(num_str) and not _is_prefix(num_str)

    # Find all tag positions
    tag_pattern = re.compile(r'<(\d+[a-z]?)>')
    result = text
    changed = True

    # Iterate until no more swaps (max 5 passes to avoid infinite loop)
    for _ in range(5):
        changed = False
        tags = list(tag_pattern.finditer(result))

        for i in range(len(tags) - 1):
            t1 = tags[i]
            t2 = tags[i + 1]

            # Check adjacency (no Chinese chars between them)
            between = result[t1.end():t2.start()]
            if between.strip():
                continue  # there's text between, not adjacent tags

            n1 = t1.group(1)
            n2 = t2.group(1)

            swap = False

            # Rule 1: morphology should follow core, not precede
            # BUT only if the morph doesn't already follow a core (i.e. morph is orphaned)
            if _is_morph(n1) and _is_core(n2):
                # Check if morph already has a core before it
                has_core_before = False
                if i > 0:
                    prev_between = result[tags[i-1].end():t1.start()]
                    if not prev_between.strip() and _is_core(tags[i-1].group(1)):
                        has_core_before = True
                if not has_core_before:
                    swap = True

            # Rule 2: prefix should precede core, not follow
            if _is_core(n1) and _is_prefix(n2):
                swap = True

            if swap:
                # Swap the two tags
                result = result[:t1.start()] + t2.group(0) + t1.group(0) + result[t2.end():]
                changed = True
                break  # restart scan after swap

        if not changed:
            break

    return result


def fix_coverage(text, input_tags, core_sns=None):
    """Insert missing tags back into LLM output.

    Version history:
      v1 (commit dabe8fa): 900x prefix only
      v2 (current): 900x prefix + morphology (using input pairing)

    Compares input_tags (from UNV+SN stripped) with output tags.
    Missing tags are inserted using input pairing (not guessing):
      - 900x prefix → before its paired core SN (from input adjacency)
      - morphology → after its paired core SN (from input adjacency)
      - core SN / implicit → not auto-inserted (leave for human/consensus)

    Args:
        text: LLM output (stripped format with <number> tags)
        input_tags: list of bare number strings from UNV+SN stripped
        core_sns: set of core SN numbers (int) from qp.php

    Returns:
        text with missing 900x/morphology tags inserted
    """
    from collections import Counter

    def _num_val(s):
        try:
            return int(s.rstrip('abcdefghijklmnopqrstuvwxyz'))
        except ValueError:
            return 0

    def _is_morph(num_str):
        n = _num_val(num_str)
        if 8000 <= n <= 8999:
            return not (core_sns and n in core_sns)
        return False

    def _is_prefix(num_str):
        return 9000 <= _num_val(num_str) <= 9999

    # Count input vs output tags
    output_tags = extract_bare_numbers(text)
    input_counter = Counter(input_tags)
    output_counter = Counter(output_tags)

    # Find missing tags
    missing = []
    for tag, count in input_counter.items():
        diff = count - output_counter.get(tag, 0)
        for _ in range(diff):
            missing.append(tag)

    if not missing:
        return text

    # For each missing tag, find insertion point
    tag_pattern = re.compile(r'<(\d+[a-z]?)>')
    result = text

    for mtag in missing:
        if _is_prefix(mtag):
            # Find the core SN that follows this prefix in the input
            paired_core = None
            for idx, itag in enumerate(input_tags):
                if itag == mtag:
                    # Look for next non-prefix tag in input
                    for j in range(idx + 1, len(input_tags)):
                        if not _is_prefix(input_tags[j]):
                            paired_core = input_tags[j]
                            break
                    break

            if paired_core:
                # Find paired_core in output, insert prefix before it
                tags = list(tag_pattern.finditer(result))
                for t in tags:
                    if t.group(1) == paired_core:
                        result = result[:t.start()] + f"<{mtag}>" + result[t.start():]
                        break

        elif _is_morph(mtag):
            # v2: Find the core SN that this morphology follows in the input
            paired_core = None
            for idx in range(len(input_tags) - 1, -1, -1):
                if input_tags[idx] == mtag:
                    # Look backwards for the preceding core SN in input
                    for j in range(idx - 1, -1, -1):
                        if not _is_morph(input_tags[j]) and not _is_prefix(input_tags[j]):
                            paired_core = input_tags[j]
                            break
                    break

            if paired_core:
                # Find paired_core in output, insert morphology right after it
                tags = list(tag_pattern.finditer(result))
                for t in tags:
                    if t.group(1) == paired_core:
                        pos = t.end()
                        result = result[:pos] + f"<{mtag}>" + result[pos:]
                        break

        # core SN, implicit — don't auto-insert
        # (position depends on semantic alignment, leave for human/consensus)

    return result


def fix_pipeline(text, input_tags, core_sns=None, max_rounds=3):
    """Run fix_coverage + fix_placement in a loop until stable.

    Version history:
      v1 (commit dabe8fa): fix_coverage 900x only + fix_placement
      v2 (current): fix_coverage 900x + morphology (input pairing) + fix_placement

    Args:
        text: LLM output (stripped)
        input_tags: list of bare number strings from UNV+SN
        core_sns: set of core SN numbers from qp.php
        max_rounds: escape hatch — stop after this many rounds

    Returns:
        (fixed_text, rounds_used)
    """
    result = text
    for round_num in range(1, max_rounds + 1):
        prev = result
        result = fix_coverage(result, input_tags, core_sns)
        result = fix_placement(result, core_sns)
        if result == prev:
            return result, round_num
    return result, max_rounds  # hit escape limit


def strip_for_comparison(text):
    """Strip FHL tags to bare numbers for Score 1 comparison.

    Same as strip_shell but also normalizes whitespace.
    """
    return strip_shell(text).strip()
