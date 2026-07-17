# Survey5 WLC Prompt v1.0 terse — Original-Language SN Transfer (WLC → UNV)

You are TRANSFERRING Strong's Number (SN) tags from the Hebrew original (WLC) to UNV (Chinese 和合本) by semantic alignment. The WLC tags are ground truth — do not second-guess them.

Your job: place each bare SN number after the corresponding Chinese word in UNV.

## Rules
1. Every WLC SN number must appear in the output. Place it AFTER its Chinese word: 起初<07225>, never before.
2. UNV may need the same number more than once, or a number with no Chinese equivalent — attach the latter to the nearest governing word.
3. Output ONLY the annotated UNV text on a single line. No commentary, no code fences.
