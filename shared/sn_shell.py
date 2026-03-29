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

# Common implicit SNs (Hebrew object marker, etc.)
# These SN numbers are almost always wrapped in {} in UNV
KNOWN_IMPLICIT_OT = {853}   # את (object marker)
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
            if _is_morph(n1) and _is_core(n2):
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


def strip_for_comparison(text):
    """Strip FHL tags to bare numbers for Score 1 comparison.

    Same as strip_shell but also normalizes whitespace.
    """
    return strip_shell(text).strip()
