# /obe2 onboarding — meeting `wlc_phaseB-20260630-m01`

**Chair**: obe (survey1_prompt_evolving, window 1314)
**Primer (READ FIRST)**: `docs/obe_bus/ONBOARDING.md` (Parts A/B/C/D — prerequisite
knowledge + the one-shot step + pre-answered FAQ; reading it kills the clarification round)
**Bus root**: `/Users/joshua/work/strong_number_embedding/docs/obe_bus/`

## Frozen roster (epoch e0001 — TTP membership, frozen for the meeting)
| dog | backend | window | role |
|---|---|---|---|
| obe | claude/opus | 1314 | chair + leg |
| lala | codex | 5555 | leg |
| erha | agy / Gemini 3.1 Pro | 32672 | leg (cwd = survey1_prompt_evolving) |

N=3. Manifest: `docs/obe_bus/epochs/e0001/manifest.json`.
**Bus paths below are ABSOLUTE** (lala and erha have different cwds — use them verbatim).

## Your one-shot onboarding (Part C) — ONE action, no clarification round
Each non-chair dog (lala, erha):

1. **Read** `/Users/joshua/work/strong_number_embedding/docs/obe_bus/ONBOARDING.md` (Parts A–D).
2. **Append exactly ONE `position` proof event** to your own log
   `…/docs/obe_bus/logs/<dog>.jsonl` — use the helper (absolute path, works from any cwd):
   `python3 /Users/joshua/work/strong_number_embedding/docs/obe_bus/obe_bus.py append <your_event.json>`
   with this shape (fill `<dog>` = `lala` or `erha`):
   ```json
   {"event_id":"<dog>:e0001:0001","dog":"<dog>","topic":"onboarding","epoch":"e0001",
    "kind":"position","parents":["obe:e0001:0001"],
    "meeting_id":"wlc_phaseB-20260630-m01","visibility":"same_cwd","seq":1,
    "a_wire":"<in YOUR OWN words: where does an ack live, and does it ever enter the bus?>",
    "a_canonical":"<in YOUR OWN words: what is canonical vs derived, and the event_id↔dog rule?>"}
   ```
   - **PARENT** = `obe:e0001:0001` (cite it in `parents`).
   - **MEETING** = `wlc_phaseB-20260630-m01`.
   - Write `a_wire` / `a_canonical` in your **own words** (don't copy the primer's
     example strings) — they prove you understand the *semantics*, not just the schema.
3. **Inject a 1-line `[ACK]`** back to obe (window 1314) citing your `event_id`.

## Chair gate (mechanical, one shot)
obe runs `python3 docs/obe_bus/obe_bus.py onboard-check docs/obe_bus/logs/<dog>.jsonl <dog> obe:e0001:0001`
— validates the event, checks topic==onboarding, parents==[obe:e0001:0001], both
checkpoints present+non-blank, event_id prefix==dog. Wrong on one item → that one item
bounced; never a second round.

## After both dogs are onboarded
obe opens round **R-1** of topic `wlc_phase_b` with 4 decision letters (the agenda
below). Each dog reads the letter, appends its own `position` event (with reasoning +
a recommendation), citing the chair's agenda event as parent. obe synthesizes; Joshua
adjudicates ties; then `/workflows` executes.

### Agenda preview (R-1 topics)
1. **Q1 methodology_divergence write** — auto-append to `FHL_DIVERGENCE_LOG` vs human-confirm.
2. **Q2 evidence stage** — WLC evidence at R3-only vs also R2-debate.
3. **Q3 override gate** — `wlc_corrected` needs 2/3 vs unanimous to override consensus toward WLC.
4. **Q4 Gen 1:1–21 mixed-state** — accept / re-run past 1:21 / revert to old gold.
