# Web E2E Graph Audit Quick-Apply Coupling + Safe Reset Affordances (M17.43)

## Goal

Improve operator reliability by coupling quick-apply with restore scope state and guarding reset actions.

1. couple quick-apply and restore-scope state with optional sync mode
2. expose active quick-apply scope match for visibility
3. add safe reset affordances that require explicit arming

Implementation:

- quick-apply coupling + safe reset controls:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`

## Behavior Contract

- quick-apply/restore coupling:
  - state/computed:
    - `filterImportAuditQuickApplySyncRestoreChecked`
    - `activeFilterImportAuditQuickApplyOptionId`
  - UI keys:
    - `co_filter_import_audit_apply_quick_sync`
    - `co_filter_import_audit_apply_quick_active`
  - behavior:
    - quick-apply buttons show active selection when current restore toggles match a quick scope
    - when `sync->restore` is enabled, successful quick apply updates restore toggles to the quick scope
    - restore scope hint now includes quick/sync tokens
- safe reset affordances:
  - arm state:
    - `filterImportAuditResetArmedChecked`
  - UI keys:
    - `co_filter_import_audit_safe_reset_controls`
    - `co_filter_import_audit_reset_arm`
    - `co_filter_import_audit_reset_restore_scope`
    - `co_filter_import_audit_reset_pin_context`
    - `co_filter_import_audit_reset_operator_context`
    - `co_filter_import_audit_reset_hint`
  - guard behavior:
    - reset actions are blocked until arm is enabled
    - blocked status: `reset blocked: arm reset first`
    - reset actions emit explicit statuses per reset scope

## Validation

Backend regression:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Frontend smoke:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_web_e2e_orchestrator_api.py --host 127.0.0.1 --port 8151 --repo-root /Users/seongcheoljeong/Documents/Codex_test --store-root /Users/seongcheoljeong/Documents/Codex_test/data/web_e2e
python3 -m http.server 8171
curl -s "http://127.0.0.1:8151/health"
curl -s "http://127.0.0.1:8171/frontend/graph_lab/panels.mjs" | rg -n "filterImportAuditQuickApplySyncRestore|activeFilterImportAuditQuickApplyOptionId|co_filter_import_audit_apply_quick_sync|co_filter_import_audit_apply_quick_active|co_filter_import_audit_safe_reset_controls|co_filter_import_audit_reset_arm|co_filter_import_audit_reset_restore_scope|co_filter_import_audit_reset_pin_context|co_filter_import_audit_reset_operator_context|co_filter_import_audit_reset_hint|reset blocked: arm reset first|audit restore scope reset|audit pin context reset|audit operator context reset|sync:|quick:"
```

Pass criteria:

1. backend regression remains pass
2. quick-apply coupling tokens are present
3. safe reset tokens are present
4. reset guard status is present
