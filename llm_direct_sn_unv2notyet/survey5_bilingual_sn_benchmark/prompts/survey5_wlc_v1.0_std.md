# Survey5 WLC Prompt v1.0 std — Original-Language SN Transfer (WLC → UNV)

## Task
Project Strong's Number annotations from the tagged Hebrew original (WLC) onto the plain Chinese Union Version (UNV) by meaning-based word alignment. The Hebrew SN numbers are authoritative ground truth.

## How
For each Hebrew word `<number>`, find the Chinese word in UNV that expresses the same meaning and place `<number>` immediately AFTER it.

## Rules
1. Coverage: every SN number in the WLC source must appear in the output. A missing number is a failure.
2. Position: the tag goes AFTER the Chinese word — 神<0430>創造<01254>, never <0430>神.
3. Repetition: if one Chinese word covers two Hebrew words, place both numbers after it, source order preserved.
4. No-equivalent numbers (Hebrew particles with no Chinese surface word): attach to the nearest governing Chinese word.
5. Output ONLY the annotated UNV text on one line. No explanation, no code fences, no extra whitespace.
