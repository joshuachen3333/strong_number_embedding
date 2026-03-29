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

def restore_shell_guess(stripped_text, testament="OT"):
    """Restore bare numbers (no markers) to FHL format by guessing type.

    Used in 方案 B where LLM outputs only <number> without markers.
    Guessing rules:
        9000-9999 → <WAH09xxx> (900x prefix)
        8000-8999 → <WTH8xxx> or <WTG5xxx> (morphology) — AMBIGUOUS with core SN
        others    → <WHxxxx> or <WGxxxx> (core SN)
        No way to guess implicit {} — all output as bare tags

    Note: 8xxx ambiguity (e.g. 8064=天 is core, 8804 is morphology) means
    Score 2 will be lower than Score 1. This gap measures the cost of
    not having markers.
    """
    def _replace(m):
        num_str = m.group(1)
        clean = num_str.rstrip('abcdefghijklmnopqrstuvwxyz')
        suffix = num_str[len(clean):]
        try:
            num = int(clean)
        except ValueError:
            return f"<{num_str}>"

        lang = "H" if testament == "OT" else "G"

        if 9000 <= num <= 9999:
            return f"<WAH{num_str}>"
        elif 8000 <= num <= 8999:
            # Guess morphology (most 8xxx in practice are morphology)
            prefix = f"WT{lang}"
            return f"<{prefix}{clean}>"
        else:
            prefix = f"W{lang}"
            return f"<{prefix}{num_str}>"

    return re.sub(r'<(\d+[a-z]?)>', _replace, stripped_text)


def strip_for_comparison(text):
    """Strip FHL tags to bare numbers for Score 1 comparison.

    Same as strip_shell but also normalizes whitespace.
    """
    return strip_shell(text).strip()
