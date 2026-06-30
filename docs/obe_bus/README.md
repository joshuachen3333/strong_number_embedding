# obe_bus — /obe2 decentralized event bus (scaffold)

This is the **scaffold** for `/obe2`, the CAN-bus-grade evolution of `/obe`. It
replaces the star-topology chair-digest with a **decentralized event-sourced topic
bus**: every dog writes its own append-only log, content is shared by *pull* (read
the logs), and causal order is a `parents ∪ depends_on` DAG — no single chair is
the sole truth source or compressor.

- **Design-of-record (rationale + fieldbus lineage)**: `../obe2_similarity_to_CANBUS.md`
- **LOCKED spec**: that file, §5.
- **Discussion trail**: `../20260629_obe_topology_thread.md` + `../20260629_from_{lala,erha}_obe_topology{,_r2,_r3}.md`

## Layout

```
docs/obe_bus/
  obe_bus.py          # minimal validate + append helper (this scaffold)
  logs/<dog>.jsonl    # CANONICAL: each dog's append-only event log (never segmented)
  topics/<topic>.jsonl# DERIVED: pointer index per topic (rebuildable from logs)
  cursors/<reader>/   # DERIVED: per-reader read positions (discardable)
  meetings/<id>/      # per-meeting manifest + (derived) event/external-ref slices
  rounds/<id>/<r>/    # per-round cut.json frontier + contested.jsonl
  epochs/<id>/        # epoch manifest, base_cut, final_cut, roster_change, quarantine
```

**Canonical** = `logs/*.jsonl`, epoch `manifest.json`, round `cut.json`.
**Derived** (safe to delete + rebuild) = topic index, meeting slices, cursors.

## Helper

`obe_bus.py` is pure stdlib. It does the two load-bearing things and nothing fancy:

```python
from obe_bus import validate_event, append_event

append_event({
    "event_id": "lala:e0004:0007", "dog": "lala", "topic": "obe_topology",
    "epoch": "e0004", "kind": "position",
    "meeting_id": "obe_topology-20260629-m03",
    "parents": ["obe:e0004:0001"], "depends_on": ["erha:e0003:0019"],
    "visibility": "same_cwd", "content_ref": "docs/from_lala_x.md",
})
```

CLI: `python obe_bus.py validate event.json` / `python obe_bus.py append event.json`.

It enforces the §9 minimum rules: kind ∈ the allowed set (**no `ack`** — ack is a
wire terminator, never a bus event), `event_id` prefix == `dog`, `roster_change`
has `meeting_id == null` while normal events require one, known `visibility`, and
(optionally) writer ∈ the epoch roster. It appends to `logs/<dog>.jsonl` and
mirrors a pointer into `topics/<topic>.jsonl`.

**Deliberately omitted** (grow when a real multi-dog meeting needs it): topic-index
rebuild, cursor materialization, lease/round-cut tooling, epoch manifest boot.
Tests: `tests/test_obe_bus.py`.

**Known soft spot — derived topic index under concurrency** (erha, onboard-m01): the
canonical truth is each dog's single-writer `logs/<dog>.jsonl` (ARINC-429 single-source
→ zero contention). `topics/<topic>.jsonl` is a *derived, fully-rebuildable* pointer
view — its truth is the union of all logs, so it is a cache, never authoritative. The
current helper has every dog append to the *shared* `topics/<topic>.jsonl`, so two dogs
posting to the same topic concurrently can interleave that derived file. Because it is
derived, the resolution is **not locking** — it is "treat as cache, rebuild from logs
when needed." The clean fix (deferred per the grow-when-needed policy): per-dog topic
shards `topics/<topic>/<dog>.jsonl`, restoring single-writer-per-file; the read path
merges shards. Canonical logs are never at risk either way.

## Iron rule reminder (from `/obe`)

Driving erha/lala defaults to the **HEAD (interactive, injectable)** session.
Headless (`codex exec` / agy headless) only on an **injection barrier** (then直接,
不請示) or an **explicit human request**. Never headless by default.
