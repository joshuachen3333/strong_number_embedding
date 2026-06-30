"""obe_bus — minimal /obe2 event-bus helper: validate + append-only per-dog logs.

The /obe2 protocol (LOCKED spec: ``docs/obe2_similarity_to_CANBUS.md`` §5) shares
content through per-dog append-only logs forming a ``parents ∪ depends_on`` causal
DAG, instead of a central chair-digest. This module is the MINIMAL scaffold:

  - ``validate_event``  — enforce the §9 minimum schema rules (kind set, no ``ack``,
    event_id↔dog prefix, roster_change↔null meeting_id, visibility, membership).
  - ``append_event``    — validate, then append the JSON line to
    ``logs/<dog>.jsonl`` and mirror a pointer into ``topics/<topic>.jsonl``.

Canonical truth is the per-dog log; the topic index is a derived pointer file.
Fancy derived-index rebuild / cursor materialization is intentionally OMITTED
(grow it when a real multi-dog meeting needs it). Pure stdlib, no deps.
"""
from __future__ import annotations

import json
import os

# /obe2 §5: the event kinds. There is deliberately NO `ack` kind — an ack is a
# wire-layer terminator, not a knowledge event, and must never enter the bus.
EVENT_KINDS = frozenset({
    "position", "review", "thread_open", "thread_msg", "thread_close",
    "digest", "decision", "roster_change",
})

# /obe2 §5: C11 visibility tiers. cross_cwd never shares the bus (pointer only).
VISIBILITY = frozenset({"same_cwd", "chair_only", "cross_cwd_pointer", "private"})

# Required on every event. `depends_on`, `seq`, `content_ref` are optional.
_REQUIRED = ("event_id", "dog", "topic", "epoch", "kind", "parents")

BUS_ROOT = os.path.dirname(os.path.abspath(__file__))


def validate_event(ev: dict, *, members=None) -> dict:
    """Validate one event against the /obe2 §9 minimum rules. Raise ValueError on
    any violation; return the (unchanged) event on success.

    ``members`` (optional): the frozen roster of the event's epoch. When given, a
    *normal* event's ``dog`` must be in it (a retired/foreign writer is illegal).
    """
    if not isinstance(ev, dict):
        raise ValueError("event must be a dict")
    for f in _REQUIRED:
        if f not in ev:
            raise ValueError(f"missing required field: {f}")

    kind = ev["kind"]
    if kind == "ack":
        raise ValueError("`ack` is a wire terminator, not a bus event — never append it")
    if kind not in EVENT_KINDS:
        raise ValueError(f"unknown kind: {kind!r} (allowed: {sorted(EVENT_KINDS)})")

    for edge_field in ("parents", "depends_on"):
        if edge_field in ev and not isinstance(ev[edge_field], list):
            raise ValueError(f"{edge_field} must be a list of event_ids")
    if not isinstance(ev["parents"], list):
        raise ValueError("parents must be a list of event_ids")

    # event_id format `<dog>:<epoch>:<seq>` and its prefix must equal `dog`
    eid = ev["event_id"]
    if not isinstance(eid, str) or eid.count(":") < 2:
        raise ValueError(f"event_id must look like '<dog>:<epoch>:<seq>': {eid!r}")
    if eid.split(":", 1)[0] != ev["dog"]:
        raise ValueError(f"event_id prefix must equal dog {ev['dog']!r}: {eid!r}")

    vis = ev.get("visibility", "same_cwd")
    if vis not in VISIBILITY:
        raise ValueError(f"unknown visibility: {vis!r} (allowed: {sorted(VISIBILITY)})")

    # roster_change is a membership control event: it belongs to no normal meeting.
    # Every normal event MUST carry a meeting_id.
    if kind == "roster_change":
        if ev.get("meeting_id") is not None:
            raise ValueError("roster_change must have meeting_id == null")
    else:
        if not ev.get("meeting_id"):
            raise ValueError(f"normal event ({kind}) requires a meeting_id")
        if members is not None and ev["dog"] not in members:
            raise ValueError(
                f"writer {ev['dog']!r} not in epoch roster {sorted(members)} "
                "(retired/foreign writer -> quarantine, not bus)"
            )
    return ev


# /obe2 m02 design + m03 live-run hardening: onboarding is one-shot, and its single
# proof event must be MECHANICALLY verifiable by the chair (no eyeballing). The live run
# showed `validate_event` alone is too weak — erha's event passed validate yet typoed the
# topic ("onboard") and carried the checkpoint answers in a letter instead of inline, so
# the comprehension proof was unverifiable. `check_onboarding` is the onboarding-specific
# gate: one call decides pass/bounce.
ONBOARDING_TOPIC = "onboarding"
_CHECKPOINTS = ("a_wire", "a_canonical")


def check_onboarding(ev: dict, *, dog: str, parent_digest: str, members=None) -> dict:
    """Verify a one-shot onboarding proof event (ONBOARDING.md Part C). Raise ValueError
    on the first failure; return the event on full pass. Checks, in order:

      1. passes the base schema (`validate_event`, incl. roster membership if given);
      2. is *this* dog's event (``dog`` + event_id prefix) — you can't onboard as another;
      3. topic is exactly ``"onboarding"`` (catches erha's "onboard" typo);
      4. ``parents == [parent_digest]`` — links back to the meeting's onboard digest
         (proves causal-DAG traversal);
      5. both inline checkpoint answers (``a_wire``, ``a_canonical``) are present and
         non-blank (proves comprehension lives in the verifiable artifact, not a letter).
    """
    if ev.get("dog") != dog:
        raise ValueError(f"onboarding event dog {ev.get('dog')!r} != expected {dog!r}")
    validate_event(ev, members=members)  # also enforces event_id prefix == dog
    if ev.get("topic") != ONBOARDING_TOPIC:
        raise ValueError(
            f"onboarding topic must be exactly {ONBOARDING_TOPIC!r}, got {ev.get('topic')!r}"
        )
    if ev.get("parents") != [parent_digest]:
        raise ValueError(
            f"onboarding parents must be [{parent_digest!r}] (link to the onboard "
            f"digest), got {ev.get('parents')!r}"
        )
    for field in _CHECKPOINTS:
        val = ev.get(field)
        if not isinstance(val, str) or not val.strip():
            raise ValueError(
                f"onboarding checkpoint {field!r} must be a non-empty inline answer "
                "(put it IN the event, not in a letter)"
            )
    return ev


def append_event(ev: dict, *, root: str = BUS_ROOT, members=None) -> dict:
    """Validate ``ev`` then append it to ``logs/<dog>.jsonl`` and mirror a pointer
    into ``topics/<topic>.jsonl``. The per-dog log is the canonical record; the
    topic file is a derived index of pointers (rebuildable from the logs)."""
    validate_event(ev, members=members)

    logs_dir = os.path.join(root, "logs")
    topics_dir = os.path.join(root, "topics")
    os.makedirs(logs_dir, exist_ok=True)
    os.makedirs(topics_dir, exist_ok=True)

    line = json.dumps(ev, ensure_ascii=False, sort_keys=True)
    with open(os.path.join(logs_dir, f"{ev['dog']}.jsonl"), "a", encoding="utf-8") as fh:
        fh.write(line + "\n")

    pointer = {
        "event_id": ev["event_id"],
        "dog": ev["dog"],
        "kind": ev["kind"],
        "meeting_id": ev.get("meeting_id"),
        "content_ref": ev.get("content_ref"),
    }
    topic_path = os.path.join(topics_dir, f"{ev['topic']}.jsonl")
    with open(topic_path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(pointer, ensure_ascii=False, sort_keys=True) + "\n")
    return ev


def _last_event(path):
    """Return the last JSON event on a .jsonl log (for onboard-check on a dog's log)."""
    last = None
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                last = json.loads(line)
    if last is None:
        raise ValueError(f"no events in {path}")
    return last


def _main(argv) -> int:  # pragma: no cover - thin CLI
    if len(argv) >= 2 and argv[1] == "onboard-check":
        # usage: obe_bus.py onboard-check <logs/<dog>.jsonl> <dog> <parent_digest>
        if len(argv) != 5:
            print("usage: obe_bus.py onboard-check <log.jsonl> <dog> <parent_digest>")
            return 2
        ev = _last_event(argv[2])
        check_onboarding(ev, dog=argv[3], parent_digest=argv[4])
        print(f"OK onboarded: {ev.get('event_id')} (topic, parent, both checkpoints verified)")
        return 0
    if len(argv) != 3 or argv[1] not in ("validate", "append"):
        print("usage: obe_bus.py {validate|append} <event.json>")
        print("       obe_bus.py onboard-check <log.jsonl> <dog> <parent_digest>")
        return 2
    with open(argv[2], encoding="utf-8") as fh:
        ev = json.load(fh)
    if argv[1] == "validate":
        validate_event(ev)
        print(f"OK valid: {ev.get('event_id')}")
    else:
        append_event(ev)
        print(f"OK appended: {ev.get('event_id')} -> logs/{ev['dog']}.jsonl")
    return 0


if __name__ == "__main__":  # pragma: no cover
    import sys
    raise SystemExit(_main(sys.argv))
