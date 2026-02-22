# Scene Runtime Blocker Report Contract (M14.3)

## Goal

Convert runtime probe output into an actionable blocker report so runtime-track
decisions are deterministic and non-repetitive.

## Scope

1. Input: runtime probe summary JSON
2. Output: blocker report JSON
3. For each runtime track:
   - ready/blocked status
   - blocker list
   - recommended action list
4. Global summary:
   - `ready_count`
   - `blocked_count`
   - `next_recommended_runtime` (priority-based)

## Code Paths

- Core:
  - `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/runtime_blockers.py`
- Runner:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/run_scene_runtime_blocker_report.py`
- Validation:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_run_scene_runtime_blocker_report.py`

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_run_scene_runtime_blocker_report.py
```

## Acceptance

M14.3 is accepted only if:

1. blocker report schema is deterministic from probe input
2. blocked tracks include actionable recommendations
3. `next_recommended_runtime` resolves from priority order among ready tracks
