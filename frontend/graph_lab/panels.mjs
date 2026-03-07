import {
  React,
  ReactFlow,
  Background,
  Controls,
  MiniMap,
} from "./deps.mjs";
import { NODE_TYPES } from "./constants.mjs";
import { normalizeGraphInputsPanelModel } from "./contracts.mjs";
import { normalizeRepoPath } from "./graph_helpers.mjs";
import { RuntimeConfigSection } from "./panels/runtime.mjs";
import { ArtifactInspectorPanel } from "./panels/artifact.mjs";
import { DecisionPane } from "./panels/gate.mjs";
import { ContractDiagnosticsPanel } from "./panels/audit.mjs";

const h = React.createElement;

function formatSigned(value) {
  const n = Number(value || 0);
  return `${n >= 0 ? "+" : ""}${n}`;
}

function formatTimeOfDay(timestampMs) {
  const t = Number(timestampMs || 0);
  if (!Number.isFinite(t) || t <= 0) return "-";
  try {
    return new Date(t).toLocaleTimeString();
  } catch (_) {
    return "-";
  }
}

function formatTimestampIso(timestampMs) {
  const t = Number(timestampMs || 0);
  if (!Number.isFinite(t) || t <= 0) return "-";
  try {
    return new Date(t).toISOString();
  } catch (_) {
    return "-";
  }
}

function classifyContractSeverity(row) {
  const source = String(row?.event_source || "").toLowerCase();
  const note = row?.note && typeof row.note === "object" ? row.note : {};
  const du = Number(row?.delta?.unique_warning_count || 0);
  const da = Number(row?.delta?.attempt_count_total || 0);
  if (String(note.error || "").trim()) return "high";
  if (source.includes("failed") || source.includes("error")) return "high";
  if (Boolean(note.gate_failed)) return "med";
  if (source.includes("cancel")) return "med";
  if (du > 0 || da > 0) return "med";
  return "low";
}

function severityLabel(severity) {
  if (severity === "high") return "HIGH";
  if (severity === "med") return "MED";
  return "LOW";
}

function classifyPolicyState(row) {
  const note = row?.note && typeof row.note === "object" ? row.note : {};
  if (typeof note.gate_failed === "boolean") {
    return note.gate_failed ? "hold" : "adopt";
  }
  return "none";
}

function getPolicyCorrelationTag(row, policyByRun) {
  const runId = String(row?.graph_run_id || "").trim();
  if (!runId) return "";
  const info = policyByRun.get(runId) || null;
  if (!info) return "";
  const failCount = Number(info.failure_count || 0);
  if (info.gate_failed) {
    return `policy:HOLD#${failCount}`;
  }
  return "policy:ADOPT";
}

function getFailureRuleTags(row, policyByRun) {
  const runId = String(row?.graph_run_id || "").trim();
  if (!runId) return [];
  const info = policyByRun.get(runId) || null;
  if (!info) return [];
  const rules = Array.isArray(info.failure_rules) ? info.failure_rules : [];
  return rules
    .map((x) => String(x || "").trim())
    .filter((x) => x.length > 0)
    .slice(0, 3);
}

function buildContractRowKey(row) {
  const note = row?.note && typeof row.note === "object" ? row.note : {};
  return [
    String(Number(row?.timestamp_ms || 0)),
    String(row?.event_source || "-"),
    String(row?.graph_run_id || "-"),
    String(note.policy_eval_id || "-"),
    String(note.recommendation || "-"),
  ].join("|");
}

const CONTRACT_OVERLAY_PREFS_KEY = "graph_lab_contract_overlay_prefs_v1";
const CONTRACT_OVERLAY_SHORTCUT_PROFILES_KEY = "graph_lab_contract_overlay_shortcut_profiles_v1";
const CONTRACT_OVERLAY_FILTER_PRESETS_KEY = "graph_lab_contract_overlay_filter_presets_v1";
const CONTRACT_OVERLAY_FILTER_IMPORT_HISTORY_KEY = "graph_lab_contract_overlay_filter_import_history_v1";
const CONTRACT_OVERLAY_QUICK_TELEMETRY_DRILLDOWN_PROFILES_KEY = "graph_lab_contract_overlay_quick_telemetry_drilldown_profiles_v1";
const ROW_WINDOW_SIZE_OPTIONS = ["50", "80", "120", "200", "320", "500"];
const CONTRACT_ROW_VOLUME_GUARD_TRIGGER = 1500;
const CONTRACT_ROW_VOLUME_GUARD_MAX_WINDOW = 200;
const CONTRACT_OVERLAY_DEFAULT_PREFS = {
  sourceFilter: "all",
  severityFilter: "all",
  policyFilter: "all",
  pinnedRunId: "all",
  nonZeroOnly: false,
  compactMode: false,
  gateHistoryLimit: "256",
  gateHistoryPages: "2",
  rowWindowSize: "120",
  rowVolumeGuardBypass: false,
  showShortcutHelp: false,
  activeShortcutProfile: "default",
  shortcutProfileDraft: "custom_profile",
  activeFilterPreset: "default",
  filterPresetDraft: "custom_filter",
  filterImportMode: "merge",
  filterImportAuditRowCap: "24",
  filterImportAuditPinnedPreset: "",
  filterImportAuditRestoreQuery: true,
  filterImportAuditRestorePaging: true,
  filterImportAuditRestorePinnedPreset: true,
  filterImportAuditRestoreActiveEntry: true,
  filterImportAuditQuickApplySyncRestore: false,
  filterImportAuditQuickTelemetryFailureOnly: false,
  filterImportAuditQuickTelemetryReasonQuery: "",
  quickTelemetryDrilldownImportConflictOnly: false,
  quickTelemetryDrilldownImportNameQuery: "",
  quickTelemetryDrilldownImportConflictFilter: "all",
  quickTelemetryDrilldownImportRowCap: "16",
  quickTelemetryDrilldownImportFilterBundleMode: "compat",
  quickTelemetryDrilldownStrictAdoptionSignals: null,
  quickTelemetryStrictRollbackPackageTrustPolicy: "strict_reject",
  activeQuickTelemetryDrilldownProfile: "default",
  quickTelemetryDrilldownProfileDraft: "custom_drilldown",
  filterImportAuditPinChipFilter: "all",
  detailFieldStates: null,
};
const SEVERITY_FILTER_OPTIONS = [
  { id: "all", label: "all" },
  { id: "high", label: "high" },
  { id: "med", label: "med" },
  { id: "low", label: "low" },
];
const POLICY_FILTER_OPTIONS = [
  { id: "all", label: "all" },
  { id: "hold", label: "hold" },
  { id: "adopt", label: "adopt" },
  { id: "none", label: "none" },
];
const FILTER_IMPORT_MODE_OPTIONS = [
  { id: "merge", label: "merge (overwrite same name)" },
  { id: "replace_custom", label: "replace custom presets" },
];
const DEFAULT_FILTER_PRESETS = {
  default: {
    sourceFilter: "all",
    severityFilter: "all",
    policyFilter: "all",
    pinnedRunId: "all",
    nonZeroOnly: false,
    gateHistoryLimit: "256",
    gateHistoryPages: "2",
    rowWindowSizeText: "120",
  },
  triage_hold_high: {
    sourceFilter: "all",
    severityFilter: "high",
    policyFilter: "hold",
    pinnedRunId: "all",
    nonZeroOnly: true,
    gateHistoryLimit: "128",
    gateHistoryPages: "2",
    rowWindowSizeText: "80",
  },
};
const DETAIL_FIELD_DEFS = [
  { id: "timestamp_iso", label: "time" },
  { id: "event_meta", label: "event/run" },
  { id: "delta", label: "delta" },
  { id: "snapshot", label: "snapshot" },
  { id: "baseline", label: "baseline" },
  { id: "note_json", label: "note_json" },
];
const DEFAULT_DETAIL_FIELD_STATES = {
  timestamp_iso: true,
  event_meta: true,
  delta: true,
  snapshot: false,
  baseline: false,
  note_json: false,
};
const SHORTCUT_ACTION_DEFS = [
  { id: "toggle_help", label: "help" },
  { id: "toggle_compact", label: "compact" },
  { id: "toggle_nonzero", label: "non-zero" },
  { id: "row_next", label: "next row window" },
  { id: "row_prev", label: "prev row window" },
  { id: "row_top", label: "row window top" },
  { id: "expand_visible", label: "expand visible" },
  { id: "collapse_details", label: "collapse details" },
  { id: "preset_triage", label: "preset triage" },
  { id: "preset_deep", label: "preset deep" },
  { id: "preset_reset", label: "preset reset" },
  { id: "audit_pin_toggle", label: "audit pin toggle" },
];
const DEFAULT_SHORTCUT_BINDINGS = {
  toggle_help: "h",
  toggle_compact: "c",
  toggle_nonzero: "n",
  row_next: "j",
  row_prev: "k",
  row_top: "g",
  expand_visible: "e",
  collapse_details: "x",
  preset_triage: "1",
  preset_deep: "2",
  preset_reset: "0",
  audit_pin_toggle: "p",
};
const DEFAULT_SHORTCUT_PROFILES = {
  default: DEFAULT_SHORTCUT_BINDINGS,
  ops_fast: {
    toggle_help: "h",
    toggle_compact: "v",
    toggle_nonzero: "b",
    row_next: "j",
    row_prev: "k",
    row_top: "g",
    expand_visible: "l",
    collapse_details: "x",
    preset_triage: "7",
    preset_deep: "8",
    preset_reset: "9",
    audit_pin_toggle: "p",
  },
};
const FILTER_IMPORT_HISTORY_LIMIT = 16;
const FILTER_IMPORT_AUDIT_DEEPLINK_KIND = "graph_lab_contract_overlay_filter_import_audit_deeplink";
const FILTER_IMPORT_AUDIT_DEEPLINK_SCHEMA_VERSION = 1;
const FILTER_IMPORT_AUDIT_KIND_OPTIONS = ["all", "import", "undo", "redo"];
const FILTER_IMPORT_AUDIT_MODE_OPTIONS = ["all", "merge", "replace_custom", "undo", "redo"];
const FILTER_IMPORT_AUDIT_ROW_CAP_OPTIONS = ["12", "24", "48", "96", "160", "200"];
const FILTER_IMPORT_AUDIT_QUERY_PRESETS = [
  { id: "all", label: "q:all", search: "", kind: "all", mode: "all" },
  { id: "import_merge", label: "q:merge", search: "", kind: "import", mode: "merge" },
  { id: "import_replace", label: "q:replace", search: "", kind: "import", mode: "replace_custom" },
  { id: "undo", label: "q:undo", search: "", kind: "undo", mode: "all" },
  { id: "redo", label: "q:redo", search: "", kind: "redo", mode: "all" },
];
const FILTER_IMPORT_AUDIT_RESTORE_PRESETS = [
  {
    id: "all",
    label: "restore:all",
    query: true,
    paging: true,
    pinned: true,
    entry: true,
  },
  {
    id: "query_pin",
    label: "restore:query+pin",
    query: true,
    paging: false,
    pinned: true,
    entry: false,
  },
  {
    id: "paging_entry",
    label: "restore:paging+entry",
    query: false,
    paging: true,
    pinned: false,
    entry: true,
  },
  {
    id: "query_only",
    label: "restore:query",
    query: true,
    paging: false,
    pinned: false,
    entry: false,
  },
];
const FILTER_IMPORT_AUDIT_PIN_CHIP_FILTER_OPTIONS = [
  { id: "all", label: "chips:all" },
  { id: "state", label: "chips:state" },
  { id: "context", label: "chips:context" },
  { id: "shortcut", label: "chips:shortcut" },
];
const FILTER_IMPORT_AUDIT_QUICK_APPLY_OPTIONS = [
  { id: "all", label: "apply:all", query: true, paging: true, pinned: true, entry: true },
  { id: "query", label: "apply:query", query: true, paging: false, pinned: false, entry: false },
  { id: "paging", label: "apply:paging", query: false, paging: true, pinned: false, entry: false },
  { id: "pinned", label: "apply:pinned", query: false, paging: false, pinned: true, entry: false },
  { id: "entry", label: "apply:entry", query: false, paging: false, pinned: false, entry: true },
  { id: "query_pin", label: "apply:query+pin", query: true, paging: false, pinned: true, entry: false },
  { id: "paging_entry", label: "apply:paging+entry", query: false, paging: true, pinned: false, entry: true },
];
const FILTER_IMPORT_AUDIT_QUICK_DRILLDOWN_PRESETS = [
  { id: "all", label: "drill:all", failure_only: false, reason_query: "" },
  { id: "fail_only", label: "drill:failures", failure_only: true, reason_query: "" },
  { id: "parse_error", label: "drill:parse_error", failure_only: true, reason_query: "parse_error" },
  { id: "no_scope", label: "drill:no_scope", failure_only: true, reason_query: "no_scope_enabled" },
  { id: "invalid_payload", label: "drill:invalid", failure_only: true, reason_query: "invalid_payload" },
];
const DEFAULT_FILTER_IMPORT_AUDIT_QUICK_TELEMETRY_DRILLDOWN_PROFILES = {
  default: { failure_only: false, reason_query: "" },
  fail_only: { failure_only: true, reason_query: "" },
  parse_error: { failure_only: true, reason_query: "parse_error" },
  no_scope: { failure_only: true, reason_query: "no_scope_enabled" },
  invalid_payload: { failure_only: true, reason_query: "invalid_payload" },
};
const FILTER_IMPORT_AUDIT_QUICK_TELEMETRY_LIMIT = 64;
const FILTER_IMPORT_AUDIT_QUICK_TREND_WINDOW = 8;
const FILTER_IMPORT_AUDIT_QUICK_REASON_CHIP_LIMIT = 5;
const FILTER_IMPORT_AUDIT_QUICK_REASON_QUERY_MAX = 48;
const FILTER_IMPORT_AUDIT_RESET_ARM_TIMEOUT_MS = 20_000;
const QUICK_TELEMETRY_DRILLDOWN_IMPORT_NAME_QUERY_MAX = 48;
const QUICK_TELEMETRY_DRILLDOWN_IMPORT_ROW_CAP_OPTIONS = ["8", "16", "24", "48", "96", "160"];
const QUICK_TELEMETRY_DRILLDOWN_IMPORT_FILTER_BUNDLE_KIND =
  "graph_lab_contract_overlay_quick_telemetry_drilldown_import_filter_bundle";
const QUICK_TELEMETRY_DRILLDOWN_IMPORT_FILTER_BUNDLE_SCHEMA_VERSION = 1;
const QUICK_TELEMETRY_DRILLDOWN_IMPORT_FILTER_BUNDLE_MODE_OPTIONS = [
  { id: "compat", label: "compat (legacy bare-object allowed)" },
  { id: "strict", label: "strict (wrapped payload only)" },
];
const QUICK_TELEMETRY_STRICT_ADOPTION_MIN_SUCCESS_COUNT = 3;
const QUICK_TELEMETRY_STRICT_CUTOVER_LEDGER_LIMIT = 24;
const QUICK_TELEMETRY_STRICT_CUTOVER_LEDGER_SCHEMA_VERSION = 1;
const QUICK_TELEMETRY_STRICT_CUTOVER_LEDGER_KIND =
  "graph_lab_contract_overlay_quick_telemetry_strict_cutover_timeline";
const QUICK_TELEMETRY_STRICT_ROLLBACK_DRILL_PACKAGE_SCHEMA_VERSION = 1;
const QUICK_TELEMETRY_STRICT_ROLLBACK_DRILL_PACKAGE_KIND =
  "graph_lab_contract_overlay_quick_telemetry_strict_rollback_drill_package";
const QUICK_TELEMETRY_STRICT_ROLLBACK_DRILL_PACKAGE_SOURCE_STAMP =
  "graph_lab_contract_overlay/quick_telemetry_strict_rollback_drill_package";
const QUICK_TELEMETRY_STRICT_ROLLBACK_DRILL_PACKAGE_CHECKSUM_ALGO = "fnv1a32";
const QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_POLICY_OPTIONS = [
  { id: "strict_reject", label: "trust:strict-reject" },
  { id: "compat_confirm", label: "trust:compat-confirm" },
];
const QUICK_TELEMETRY_STRICT_ROLLBACK_OVERRIDE_LOG_LIMIT = 32;
const QUICK_TELEMETRY_STRICT_ROLLBACK_OVERRIDE_LOG_SCHEMA_VERSION = 1;
const QUICK_TELEMETRY_STRICT_ROLLBACK_OVERRIDE_LOG_KIND =
  "graph_lab_contract_overlay_quick_telemetry_strict_rollback_override_log";
const QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_BUNDLE_SCHEMA_VERSION = 1;
const QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_BUNDLE_KIND =
  "graph_lab_contract_overlay_quick_telemetry_strict_rollback_trust_audit_bundle";
const QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_SCHEMA_VERSION = 1;
const QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_KIND =
  "graph_lab_contract_overlay_quick_telemetry_strict_rollback_trust_audit_bundle_apply_dry_run_handoff_package";
const QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_TIMEOUT_MS = 20_000;
const QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_LIMIT = 12;
const QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_SCHEMA_VERSION = 1;
const QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_KIND =
  "graph_lab_contract_overlay_quick_telemetry_strict_rollback_trust_audit_bundle_apply_dry_run_handoff_hydrate_confirm_activity";
const QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TIMEOUT_MS = 20_000;
const QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_LIMIT = 12;
const QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_SCHEMA_VERSION = 1;
const QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_KIND =
  "graph_lab_contract_overlay_quick_telemetry_strict_rollback_trust_audit_bundle_apply_dry_run_handoff_hydrate_confirm_activity_replay_confirm_trail";
const QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_IMPORT_CONFIRM_TIMEOUT_MS = 20_000;
const QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_IMPORT_CONFIRM_TRAIL_IMPORT_CONFIRM_TIMEOUT_MS = 20_000;
const QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_IMPORT_CONFIRM_TRAIL_LIMIT = 12;
const QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_IMPORT_CONFIRM_TRAIL_SCHEMA_VERSION = 1;
const QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_IMPORT_CONFIRM_TRAIL_KIND =
  "graph_lab_contract_overlay_quick_telemetry_strict_rollback_trust_audit_bundle_apply_dry_run_handoff_hydrate_confirm_activity_replay_confirm_trail_import_confirm_trail";
const QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_CONFIRM_TIMEOUT_MS = 20_000;
const QUICK_TELEMETRY_DRILLDOWN_IMPORT_CONFLICT_FILTER_OPTIONS = [
  { id: "all", label: "all" },
  { id: "new", label: "new" },
  { id: "overwrite_any", label: "overwrite" },
  { id: "overwrite_changed", label: "changed" },
  { id: "overwrite_same", label: "same" },
  { id: "overwrite_builtin", label: "builtin" },
  { id: "overwrite_custom", label: "custom" },
];
const QUICK_TELEMETRY_DRILLDOWN_IMPORT_FILTER_PRESETS = [
  { id: "all", label: "flt:all", conflict_only: false, conflict_filter: "all", name_query: "" },
  { id: "changed", label: "flt:changed", conflict_only: true, conflict_filter: "overwrite_changed", name_query: "" },
  { id: "builtin", label: "flt:builtin", conflict_only: true, conflict_filter: "overwrite_builtin", name_query: "" },
  { id: "custom", label: "flt:custom", conflict_only: true, conflict_filter: "overwrite_custom", name_query: "" },
  { id: "new", label: "flt:new", conflict_only: false, conflict_filter: "new", name_query: "" },
];
const QUICK_TELEMETRY_STRICT_ROLLBACK_DRILL_PRESETS = [
  { id: "parse_error", label: "drill:parse_error", failure_only: true, reason_query: "parse_error" },
  { id: "invalid_payload", label: "drill:invalid_payload", failure_only: true, reason_query: "invalid_payload" },
  { id: "no_scope", label: "drill:no_scope", failure_only: true, reason_query: "no_scope_enabled" },
];

function resolveFilterImportAuditQueryPreset(rawPresetId) {
  const pid = String(rawPresetId || "").trim();
  if (!pid) return FILTER_IMPORT_AUDIT_QUERY_PRESETS[0];
  return FILTER_IMPORT_AUDIT_QUERY_PRESETS.find((row) => String(row?.id || "") === pid)
    || FILTER_IMPORT_AUDIT_QUERY_PRESETS[0];
}

function resolveFilterImportAuditRestorePreset(rawPresetId) {
  const pid = String(rawPresetId || "").trim();
  if (!pid) return FILTER_IMPORT_AUDIT_RESTORE_PRESETS[0];
  return FILTER_IMPORT_AUDIT_RESTORE_PRESETS.find((row) => String(row?.id || "") === pid)
    || FILTER_IMPORT_AUDIT_RESTORE_PRESETS[0];
}

function resolveFilterImportAuditQuickApplyOption(rawOptionId) {
  const oid = String(rawOptionId || "").trim();
  if (!oid) return FILTER_IMPORT_AUDIT_QUICK_APPLY_OPTIONS[0];
  return FILTER_IMPORT_AUDIT_QUICK_APPLY_OPTIONS.find((row) => String(row?.id || "") === oid)
    || FILTER_IMPORT_AUDIT_QUICK_APPLY_OPTIONS[0];
}

function resolveFilterImportAuditQuickDrilldownPreset(rawPresetId) {
  const pid = String(rawPresetId || "").trim();
  if (!pid) return FILTER_IMPORT_AUDIT_QUICK_DRILLDOWN_PRESETS[0];
  return FILTER_IMPORT_AUDIT_QUICK_DRILLDOWN_PRESETS.find((row) => String(row?.id || "") === pid)
    || FILTER_IMPORT_AUDIT_QUICK_DRILLDOWN_PRESETS[0];
}

function resolveQuickTelemetryDrilldownImportFilterPreset(rawPresetId) {
  const pid = String(rawPresetId || "").trim();
  if (!pid) return QUICK_TELEMETRY_DRILLDOWN_IMPORT_FILTER_PRESETS[0];
  return QUICK_TELEMETRY_DRILLDOWN_IMPORT_FILTER_PRESETS.find((row) => String(row?.id || "") === pid)
    || QUICK_TELEMETRY_DRILLDOWN_IMPORT_FILTER_PRESETS[0];
}

function resolveQuickTelemetryStrictRollbackDrillPreset(rawPresetId) {
  const pid = String(rawPresetId || "").trim();
  if (!pid) return QUICK_TELEMETRY_STRICT_ROLLBACK_DRILL_PRESETS[0];
  return QUICK_TELEMETRY_STRICT_ROLLBACK_DRILL_PRESETS.find((row) => String(row?.id || "") === pid)
    || QUICK_TELEMETRY_STRICT_ROLLBACK_DRILL_PRESETS[0];
}

function clampInteger(raw, minValue, maxValue, fallback) {
  const n = Number(raw);
  if (!Number.isFinite(n)) return Number(fallback);
  const iv = Math.floor(n);
  return Math.max(Number(minValue), Math.min(Number(maxValue), iv));
}

function loadContractOverlayPrefs() {
  try {
    if (typeof window === "undefined" || !window.localStorage) return {};
    const raw = String(window.localStorage.getItem(CONTRACT_OVERLAY_PREFS_KEY) || "").trim();
    if (!raw) return {};
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return {};
    return parsed;
  } catch (_) {
    return {};
  }
}

function saveContractOverlayPrefs(prefs) {
  try {
    if (typeof window === "undefined" || !window.localStorage) return;
    const payload = prefs && typeof prefs === "object" ? prefs : {};
    window.localStorage.setItem(CONTRACT_OVERLAY_PREFS_KEY, JSON.stringify(payload));
  } catch (_) {
    // localStorage may be blocked; ignore and continue with in-memory state
  }
}

function normalizeShortcutToken(raw) {
  const text = String(raw || "").trim().toLowerCase();
  if (text.length === 0) return "";
  return text.slice(0, 1);
}

function normalizeShortcutProfileName(raw) {
  const text = String(raw || "").trim().toLowerCase();
  if (!text) return "";
  const compact = text
    .replace(/[^a-z0-9_-]+/g, "_")
    .replace(/_+/g, "_")
    .replace(/^_+|_+$/g, "");
  return compact.slice(0, 32);
}

function normalizeFilterPresetName(raw) {
  const text = String(raw || "").trim().toLowerCase();
  if (!text) return "";
  const compact = text
    .replace(/[^a-z0-9_-]+/g, "_")
    .replace(/_+/g, "_")
    .replace(/^_+|_+$/g, "");
  return compact.slice(0, 32);
}

function normalizeQuickTelemetryDrilldownProfileName(raw) {
  const text = String(raw || "").trim().toLowerCase();
  if (!text) return "";
  const compact = text
    .replace(/[^a-z0-9_-]+/g, "_")
    .replace(/_+/g, "_")
    .replace(/^_+|_+$/g, "");
  return compact.slice(0, 32);
}

function normalizeFilterImportMode(raw) {
  const text = String(raw || "").trim().toLowerCase();
  const allowed = new Set(FILTER_IMPORT_MODE_OPTIONS.map((x) => String(x.id || "")));
  return allowed.has(text) ? text : CONTRACT_OVERLAY_DEFAULT_PREFS.filterImportMode;
}

function normalizeFilterImportAuditPinChipFilter(raw) {
  const text = String(raw || "").trim().toLowerCase();
  const allowed = new Set(FILTER_IMPORT_AUDIT_PIN_CHIP_FILTER_OPTIONS.map((x) => String(x.id || "")));
  return allowed.has(text) ? text : CONTRACT_OVERLAY_DEFAULT_PREFS.filterImportAuditPinChipFilter;
}

function normalizeQuickTelemetryDrilldownImportConflictFilter(raw) {
  const text = String(raw || "").trim().toLowerCase();
  const allowed = new Set(QUICK_TELEMETRY_DRILLDOWN_IMPORT_CONFLICT_FILTER_OPTIONS.map((x) => String(x.id || "")));
  return allowed.has(text) ? text : CONTRACT_OVERLAY_DEFAULT_PREFS.quickTelemetryDrilldownImportConflictFilter;
}

function normalizeQuickTelemetryDrilldownImportFilterBundleMode(raw) {
  const text = String(raw || "").trim().toLowerCase();
  const allowed = new Set(QUICK_TELEMETRY_DRILLDOWN_IMPORT_FILTER_BUNDLE_MODE_OPTIONS.map((x) => String(x.id || "")));
  return allowed.has(text) ? text : CONTRACT_OVERLAY_DEFAULT_PREFS.quickTelemetryDrilldownImportFilterBundleMode;
}

function normalizeQuickTelemetryStrictRollbackPackageTrustPolicy(raw) {
  const text = String(raw || "").trim().toLowerCase();
  const allowed = new Set(QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_POLICY_OPTIONS.map((x) => String(x.id || "")));
  return allowed.has(text) ? text : CONTRACT_OVERLAY_DEFAULT_PREFS.quickTelemetryStrictRollbackPackageTrustPolicy;
}

function normalizeQuickTelemetryStrictRollbackTrustAuditProvenanceSnapshot(raw) {
  const src = raw && typeof raw === "object" && !Array.isArray(raw) ? raw : {};
  const parseStateRaw = String(src.parse_state || "").trim().toLowerCase();
  const parseState = parseStateRaw === "ready" || parseStateRaw === "error" ? parseStateRaw : "empty";
  return {
    parse_state: parseState,
    parse_error: String(src.parse_error || "").slice(0, 220),
    has_guard_issue: Boolean(src.has_guard_issue),
    missing_source_stamp: Boolean(src.missing_source_stamp),
    missing_payload_checksum: Boolean(src.missing_payload_checksum),
    source_match: Boolean(src.source_match),
    checksum_match: Boolean(src.checksum_match),
    source_stamp: String(src.source_stamp || QUICK_TELEMETRY_STRICT_ROLLBACK_DRILL_PACKAGE_SOURCE_STAMP).slice(0, 180),
    payload_checksum: String(src.payload_checksum || "").slice(0, 180),
    computed_checksum: String(src.computed_checksum || "").slice(0, 180),
    checksum_hint: String(src.checksum_hint || "").slice(0, 220),
    package_kind: String(src.package_kind || QUICK_TELEMETRY_STRICT_ROLLBACK_DRILL_PACKAGE_KIND).slice(0, 140),
    package_schema_version: clampInteger(
      src.package_schema_version,
      0,
      9_999,
      QUICK_TELEMETRY_STRICT_ROLLBACK_DRILL_PACKAGE_SCHEMA_VERSION
    ),
    package_preset_id: String(src.package_preset_id || "custom").slice(0, 80),
    package_import_mode: normalizeQuickTelemetryDrilldownImportFilterBundleMode(src.package_import_mode || "compat"),
    package_timeline_entry_count: clampInteger(src.package_timeline_entry_count, 0, 1_000_000, 0),
    package_exported_at_iso: String(src.package_exported_at_iso || "-").slice(0, 80),
  };
}

function normalizeQuickTelemetryDrilldownStrictAdoptionSignals(raw, fallback) {
  const source = raw && typeof raw === "object" && !Array.isArray(raw) ? raw : {};
  const base = fallback && typeof fallback === "object" && !Array.isArray(fallback)
    ? fallback
    : {};
  return {
    attempt_count: clampInteger(source.attempt_count ?? base.attempt_count ?? 0, 0, 1_000_000, 0),
    success_count: clampInteger(source.success_count ?? base.success_count ?? 0, 0, 1_000_000, 0),
    legacy_wrap_use_count: clampInteger(
      source.legacy_wrap_use_count ?? base.legacy_wrap_use_count ?? 0,
      0,
      1_000_000,
      0
    ),
    legacy_parse_block_count: clampInteger(
      source.legacy_parse_block_count ?? base.legacy_parse_block_count ?? 0,
      0,
      1_000_000,
      0
    ),
    last_event_ts_ms: clampInteger(source.last_event_ts_ms ?? base.last_event_ts_ms ?? 0, 0, 9_999_999_999_999, 0),
  };
}

function buildQuickTelemetryDrilldownStrictAdoptionChecklist(rawSignals, importMode) {
  const sig = normalizeQuickTelemetryDrilldownStrictAdoptionSignals(rawSignals, null);
  const modeStrict = normalizeQuickTelemetryDrilldownImportFilterBundleMode(importMode) === "strict";
  const enoughStrictAttempts = Number(sig.attempt_count || 0) >= QUICK_TELEMETRY_STRICT_ADOPTION_MIN_SUCCESS_COUNT;
  const strictSuccessStable = Number(sig.attempt_count || 0) > 0
    && Number(sig.success_count || 0) >= Number(sig.attempt_count || 0);
  const noLegacyWrapUsage = Number(sig.legacy_wrap_use_count || 0) === 0;
  const noLegacyParseBlock = Number(sig.legacy_parse_block_count || 0) === 0;
  const items = [
    { id: "mode_strict", label: "strict mode active", ok: modeStrict },
    {
      id: "strict_attempts",
      label: `strict import attempts >= ${QUICK_TELEMETRY_STRICT_ADOPTION_MIN_SUCCESS_COUNT}`,
      ok: enoughStrictAttempts,
    },
    { id: "strict_success_stable", label: "strict import success stable", ok: strictSuccessStable },
    { id: "no_legacy_wrap_usage", label: "legacy wrap helper usage = 0", ok: noLegacyWrapUsage },
    { id: "no_legacy_parse_block", label: "strict parse legacy-block count = 0", ok: noLegacyParseBlock },
  ];
  const passCount = items.filter((row) => Boolean(row.ok)).length;
  const ready = passCount === items.length;
  return {
    ready,
    pass_count: passCount,
    item_count: items.length,
    items,
    signals: sig,
    last_event_iso: formatTimestampIso(Number(sig.last_event_ts_ms || 0)),
  };
}

function normalizeQuickTelemetryDrilldownStrictCutoverLedgerEntry(raw, idx = 0) {
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) return null;
  const eventId = String(raw.event_id || "").trim().toLowerCase();
  const eventKind = eventId === "compat_fallback" ? "compat_fallback" : "apply_strict_default";
  const importMode = normalizeQuickTelemetryDrilldownImportFilterBundleMode(raw.import_mode || "compat");
  const statusRaw = String(raw.checklist_status || "").trim().toUpperCase();
  const status = statusRaw === "READY" ? "READY" : "HOLD";
  const timestampMs = clampInteger(raw.timestamp_ms, 0, 9_999_999_999_999, 0);
  return {
    id: String(raw.id || `qt_cutover_${idx}`),
    event_id: eventKind,
    import_mode: importMode,
    checklist_status: status,
    pass_count: clampInteger(raw.pass_count, 0, 128, 0),
    item_count: clampInteger(raw.item_count, 0, 128, 0),
    attempt_count: clampInteger(raw.attempt_count, 0, 1_000_000, 0),
    success_count: clampInteger(raw.success_count, 0, 1_000_000, 0),
    legacy_wrap_use_count: clampInteger(raw.legacy_wrap_use_count, 0, 1_000_000, 0),
    legacy_parse_block_count: clampInteger(raw.legacy_parse_block_count, 0, 1_000_000, 0),
    timestamp_ms: timestampMs,
    timestamp_iso: String(raw.timestamp_iso || formatTimestampIso(timestampMs)),
  };
}

function buildQuickTelemetryDrilldownStrictCutoverLedgerBundle(entries) {
  const rows = Array.isArray(entries) ? entries : [];
  const normalized = rows
    .map((row, idx) => normalizeQuickTelemetryDrilldownStrictCutoverLedgerEntry(row, idx))
    .filter(Boolean)
    .slice(0, QUICK_TELEMETRY_STRICT_CUTOVER_LEDGER_LIMIT);
  return {
    schema_version: QUICK_TELEMETRY_STRICT_CUTOVER_LEDGER_SCHEMA_VERSION,
    kind: QUICK_TELEMETRY_STRICT_CUTOVER_LEDGER_KIND,
    exported_at_iso: new Date().toISOString(),
    entry_count: normalized.length,
    entries: normalized,
  };
}

function serializeQuickTelemetryDrilldownStrictCutoverLedgerBundle(entries) {
  return JSON.stringify(buildQuickTelemetryDrilldownStrictCutoverLedgerBundle(entries), null, 2);
}

function stableStringifyForChecksum(value) {
  if (value === null || typeof value !== "object") {
    return JSON.stringify(value);
  }
  if (Array.isArray(value)) {
    return `[${value.map((row) => stableStringifyForChecksum(row)).join(",")}]`;
  }
  const keys = Object.keys(value).sort((a, b) => a.localeCompare(b));
  const pairs = keys.map((key) => `${JSON.stringify(key)}:${stableStringifyForChecksum(value[key])}`);
  return `{${pairs.join(",")}}`;
}

function computeFnv1a32Hex(text) {
  const src = String(text || "");
  let hash = 0x811c9dc5;
  for (let idx = 0; idx < src.length; idx += 1) {
    hash ^= src.charCodeAt(idx);
    hash = Math.imul(hash, 0x01000193);
  }
  return (hash >>> 0).toString(16).padStart(8, "0");
}

function computeQuickTelemetryStrictRollbackDrillPackageChecksum(packageCore) {
  const stable = stableStringifyForChecksum(packageCore);
  return `${QUICK_TELEMETRY_STRICT_ROLLBACK_DRILL_PACKAGE_CHECKSUM_ALGO}:${computeFnv1a32Hex(stable)}`;
}

function normalizeQuickTelemetryStrictRollbackDrillPackageProvenance(raw, packageCore) {
  const src = raw && typeof raw === "object" && !Array.isArray(raw) ? raw : {};
  const sourceStampRaw = String(src.source_stamp || "").trim();
  const sourceStamp = sourceStampRaw || QUICK_TELEMETRY_STRICT_ROLLBACK_DRILL_PACKAGE_SOURCE_STAMP;
  const computedChecksum = computeQuickTelemetryStrictRollbackDrillPackageChecksum(packageCore);
  const importedChecksum = String(src.payload_checksum || "").trim().toLowerCase();
  const payloadChecksum = importedChecksum || computedChecksum;
  const checksumMatch = importedChecksum ? importedChecksum === computedChecksum : true;
  const sourceMatch = sourceStamp === QUICK_TELEMETRY_STRICT_ROLLBACK_DRILL_PACKAGE_SOURCE_STAMP;
  const checksumHint = importedChecksum
    ? (
      checksumMatch
        ? `checksum ok (${computedChecksum})`
        : `checksum mismatch (imported=${importedChecksum}, computed=${computedChecksum})`
    )
    : `checksum generated (${computedChecksum})`;
  return {
    source_stamp: sourceStamp,
    source_match: sourceMatch,
    payload_checksum: payloadChecksum,
    computed_checksum: computedChecksum,
    checksum_match: checksumMatch,
    checksum_hint: checksumHint,
    has_guard_issue: !sourceMatch || !checksumMatch,
  };
}

function normalizeQuickTelemetryStrictRollbackOverrideLogEntry(raw, idx = 0) {
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) return null;
  const policy = normalizeQuickTelemetryStrictRollbackPackageTrustPolicy(raw.policy_mode || "strict_reject");
  const eventKindRaw = String(raw.event_kind || "").trim().toLowerCase();
  const eventKind = eventKindRaw === "override_replay" ? "override_replay" : "replay";
  return {
    id: String(raw.id || `qt_override_${idx}`),
    timestamp_iso: String(raw.timestamp_iso || "-"),
    event_kind: eventKind,
    policy_mode: policy,
    source_stamp: String(raw.source_stamp || "").slice(0, 160),
    payload_checksum: String(raw.payload_checksum || "").slice(0, 160),
    computed_checksum: String(raw.computed_checksum || "").slice(0, 160),
    provenance_issue: Boolean(raw.provenance_issue),
    checklist_delta: Boolean(raw.checklist_delta),
    delta_confirmed: Boolean(raw.delta_confirmed),
    override_reason: String(raw.override_reason || "").slice(0, 200),
    preset_id: String(raw.preset_id || "custom").slice(0, 64),
  };
}

function buildQuickTelemetryStrictRollbackOverrideLogBundle(entries) {
  const rows = Array.isArray(entries) ? entries : [];
  const normalized = rows
    .map((row, idx) => normalizeQuickTelemetryStrictRollbackOverrideLogEntry(row, idx))
    .filter(Boolean)
    .slice(0, QUICK_TELEMETRY_STRICT_ROLLBACK_OVERRIDE_LOG_LIMIT);
  return {
    schema_version: QUICK_TELEMETRY_STRICT_ROLLBACK_OVERRIDE_LOG_SCHEMA_VERSION,
    kind: QUICK_TELEMETRY_STRICT_ROLLBACK_OVERRIDE_LOG_KIND,
    exported_at_iso: new Date().toISOString(),
    entry_count: normalized.length,
    entries: normalized,
  };
}

function serializeQuickTelemetryStrictRollbackOverrideLogBundle(entries) {
  return JSON.stringify(buildQuickTelemetryStrictRollbackOverrideLogBundle(entries), null, 2);
}

function buildQuickTelemetryStrictRollbackTrustAuditBundle(rawBundle) {
  const src = rawBundle && typeof rawBundle === "object" && !Array.isArray(rawBundle)
    ? rawBundle
    : {};
  const overrideLog = buildQuickTelemetryStrictRollbackOverrideLogBundle(src.override_log_entries);
  return {
    schema_version: QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_BUNDLE_SCHEMA_VERSION,
    kind: QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_BUNDLE_KIND,
    exported_at_iso: new Date().toISOString(),
    trust_policy_mode: normalizeQuickTelemetryStrictRollbackPackageTrustPolicy(
      src.trust_policy_mode
    ),
    override_log: {
      schema_version: overrideLog.schema_version,
      kind: overrideLog.kind,
      entry_count: overrideLog.entry_count,
      entries: overrideLog.entries,
    },
    provenance_snapshot: normalizeQuickTelemetryStrictRollbackTrustAuditProvenanceSnapshot(
      src.provenance_snapshot
    ),
  };
}

function serializeQuickTelemetryStrictRollbackTrustAuditBundle(rawBundle) {
  return JSON.stringify(buildQuickTelemetryStrictRollbackTrustAuditBundle(rawBundle), null, 2);
}

function buildQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackage(rawPackage) {
  const src = rawPackage && typeof rawPackage === "object" && !Array.isArray(rawPackage)
    ? rawPackage
    : {};
  const summary = src.dry_run_summary && typeof src.dry_run_summary === "object" && !Array.isArray(src.dry_run_summary)
    ? src.dry_run_summary
    : {};
  const safety = src.apply_safety && typeof src.apply_safety === "object" && !Array.isArray(src.apply_safety)
    ? src.apply_safety
    : {};
  const summaryParseStateRaw = String(summary.parse_state || "").trim().toLowerCase();
  const summaryParseState = summaryParseStateRaw === "ready" || summaryParseStateRaw === "error"
    ? summaryParseStateRaw
    : "empty";
  const bundleParseStateRaw = String(src.trust_audit_bundle_parse_state || "").trim().toLowerCase();
  const bundleParseState = bundleParseStateRaw === "ready" || bundleParseStateRaw === "error"
    ? bundleParseStateRaw
    : "empty";
  const existingPolicy = normalizeQuickTelemetryStrictRollbackPackageTrustPolicy(
    summary.existing_policy
  );
  const incomingPolicy = normalizeQuickTelemetryStrictRollbackPackageTrustPolicy(
    summary.incoming_policy
  );
  return {
    schema_version: QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_SCHEMA_VERSION,
    kind: QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_KIND,
    exported_at_iso: new Date().toISOString(),
    dry_run_summary: {
      parse_state: summaryParseState,
      policy_changed: Boolean(summary.policy_changed),
      existing_policy: existingPolicy,
      incoming_policy: incomingPolicy,
      existing_override_count: clampInteger(summary.existing_override_count, 0, 1_000_000, 0),
      incoming_override_count: clampInteger(summary.incoming_override_count, 0, 1_000_000, 0),
      added_override_count: clampInteger(summary.added_override_count, 0, 1_000_000, 0),
      removed_override_count: clampInteger(summary.removed_override_count, 0, 1_000_000, 0),
      changed_override_count: clampInteger(summary.changed_override_count, 0, 1_000_000, 0),
      unchanged_override_count: clampInteger(summary.unchanged_override_count, 0, 1_000_000, 0),
      existing_latest_override_id: String(summary.existing_latest_override_id || "-").slice(0, 160),
      existing_latest_override_ts: String(summary.existing_latest_override_ts || "-").slice(0, 80),
      existing_latest_override_preset: String(summary.existing_latest_override_preset || "-").slice(0, 80),
      incoming_latest_override_id: String(summary.incoming_latest_override_id || "-").slice(0, 160),
      incoming_latest_override_ts: String(summary.incoming_latest_override_ts || "-").slice(0, 80),
      incoming_latest_override_preset: String(summary.incoming_latest_override_preset || "-").slice(0, 80),
    },
    apply_safety: {
      needs_confirm: Boolean(safety.needs_confirm),
      policy_changed: Boolean(safety.policy_changed),
      overrides_replaced: Boolean(safety.overrides_replaced),
      existing_policy: normalizeQuickTelemetryStrictRollbackPackageTrustPolicy(safety.existing_policy),
      incoming_policy: normalizeQuickTelemetryStrictRollbackPackageTrustPolicy(safety.incoming_policy),
      existing_override_count: clampInteger(safety.existing_override_count, 0, 1_000_000, 0),
      incoming_override_count: clampInteger(safety.incoming_override_count, 0, 1_000_000, 0),
      parse_state: String(safety.parse_state || "").trim().toLowerCase() === "ready" ? "ready" : "blocked",
    },
    import_preview: String(src.import_preview || "").slice(0, 400),
    trust_audit_bundle_snapshot: {
      kind: String(src.trust_audit_bundle_kind || QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_BUNDLE_KIND).slice(0, 180),
      schema_version: clampInteger(
        src.trust_audit_bundle_schema_version,
        0,
        9_999,
        QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_BUNDLE_SCHEMA_VERSION
      ),
      trust_policy_mode: normalizeQuickTelemetryStrictRollbackPackageTrustPolicy(
        src.trust_audit_bundle_policy_mode
      ),
      override_event_count: clampInteger(src.trust_audit_bundle_override_event_count, 0, 1_000_000, 0),
      parse_state: bundleParseState,
    },
  };
}

function serializeQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackage(rawPackage) {
  return JSON.stringify(buildQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackage(rawPackage), null, 2);
}

function normalizeQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityEntry(raw, idx = 0) {
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) return null;
  const timestampMs = clampInteger(raw.timestamp_ms, 0, 9_999_999_999_999, 0);
  return {
    id: String(raw.id || `qt_trust_audit_dry_run_handoff_confirm_activity_${idx}`).slice(0, 160),
    timestamp_ms: timestampMs,
    timestamp_iso: String(raw.timestamp_iso || formatTimestampIso(timestampMs)).slice(0, 80),
    event_id: String(raw.event_id || "unknown").trim().toLowerCase().slice(0, 80),
    detail: String(raw.detail || "-").slice(0, 240),
  };
}

function buildQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityBundle(entries) {
  const rows = Array.isArray(entries) ? entries : [];
  const normalized = rows
    .map((row, idx) => normalizeQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityEntry(row, idx))
    .filter(Boolean)
    .slice(0, QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_LIMIT);
  return {
    schema_version: QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_SCHEMA_VERSION,
    kind: QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_KIND,
    exported_at_iso: new Date().toISOString(),
    entry_count: normalized.length,
    entries: normalized,
  };
}

function serializeQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityBundle(entries) {
  return JSON.stringify(
    buildQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityBundle(entries),
    null,
    2
  );
}

function buildQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailBundle(entries) {
  const rows = Array.isArray(entries) ? entries : [];
  const normalized = rows
    .map((row, idx) => normalizeQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityEntry(row, idx))
    .filter(Boolean)
    .slice(0, QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_LIMIT);
  return {
    schema_version: QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_SCHEMA_VERSION,
    kind: QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_KIND,
    exported_at_iso: new Date().toISOString(),
    entry_count: normalized.length,
    entries: normalized,
  };
}

function serializeQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailBundle(entries) {
  return JSON.stringify(
    buildQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailBundle(entries),
    null,
    2
  );
}

function buildQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailBundle(entries) {
  const rows = Array.isArray(entries) ? entries : [];
  const normalized = rows
    .map((row, idx) => normalizeQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityEntry(row, idx))
    .filter(Boolean)
    .slice(0, QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_IMPORT_CONFIRM_TRAIL_LIMIT);
  return {
    schema_version: QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_IMPORT_CONFIRM_TRAIL_SCHEMA_VERSION,
    kind: QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_IMPORT_CONFIRM_TRAIL_KIND,
    exported_at_iso: new Date().toISOString(),
    entry_count: normalized.length,
    entries: normalized,
  };
}

function serializeQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailBundle(entries) {
  return JSON.stringify(
    buildQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailBundle(entries),
    null,
    2
  );
}

function parseQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityText(rawText) {
  const text = String(rawText || "").trim();
  if (!text) {
    throw new Error("empty import payload");
  }
  let parsed = null;
  try {
    parsed = JSON.parse(text);
  } catch (_) {
    throw new Error("invalid JSON");
  }
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new Error("import root must be object");
  }
  const parsedKind = String(parsed.kind || "").trim();
  if (!parsedKind) {
    throw new Error(
      `confirm activity bundle requires kind=${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_KIND}`
    );
  }
  if (parsedKind !== QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_KIND) {
    throw new Error(
      `unexpected kind (expected ${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_KIND})`
    );
  }
  if (parsed.schema_version === undefined) {
    throw new Error(
      `confirm activity bundle requires schema_version=${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_SCHEMA_VERSION}`
    );
  }
  const schemaVersion = Math.floor(Number(parsed.schema_version || 0));
  if (schemaVersion !== QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_SCHEMA_VERSION) {
    throw new Error(
      `unsupported schema_version (expected ${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_SCHEMA_VERSION})`
    );
  }
  if (!Array.isArray(parsed.entries)) {
    throw new Error("confirm activity bundle missing entries array");
  }
  const rows = parsed.entries
    .map((row, idx) => normalizeQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityEntry(row, idx))
    .filter(Boolean)
    .slice(0, QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_LIMIT);
  return {
    schema_version: schemaVersion,
    kind: parsedKind,
    exported_at_iso: String(parsed.exported_at_iso || "-"),
    entry_count: rows.length,
    entries: rows,
  };
}

function parseQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailText(rawText) {
  const text = String(rawText || "").trim();
  if (!text) {
    throw new Error("empty import payload");
  }
  let parsed = null;
  try {
    parsed = JSON.parse(text);
  } catch (_) {
    throw new Error("invalid JSON");
  }
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new Error("import root must be object");
  }
  const parsedKind = String(parsed.kind || "").trim();
  if (!parsedKind) {
    throw new Error(
      `confirm activity replay trail bundle requires kind=${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_KIND}`
    );
  }
  if (parsedKind !== QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_KIND) {
    throw new Error(
      `unexpected kind (expected ${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_KIND})`
    );
  }
  if (parsed.schema_version === undefined) {
    throw new Error(
      `confirm activity replay trail bundle requires schema_version=${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_SCHEMA_VERSION}`
    );
  }
  const schemaVersion = Math.floor(Number(parsed.schema_version || 0));
  if (schemaVersion !== QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_SCHEMA_VERSION) {
    throw new Error(
      `unsupported schema_version (expected ${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_SCHEMA_VERSION})`
    );
  }
  if (!Array.isArray(parsed.entries)) {
    throw new Error("confirm activity replay trail bundle missing entries array");
  }
  const rows = parsed.entries
    .map((row, idx) => normalizeQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityEntry(row, idx))
    .filter(Boolean)
    .slice(0, QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_LIMIT);
  return {
    schema_version: schemaVersion,
    kind: parsedKind,
    exported_at_iso: String(parsed.exported_at_iso || "-"),
    entry_count: rows.length,
    entries: rows,
  };
}

function parseQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailText(rawText) {
  const text = String(rawText || "").trim();
  if (!text) {
    throw new Error("empty import payload");
  }
  let parsed = null;
  try {
    parsed = JSON.parse(text);
  } catch (_) {
    throw new Error("invalid JSON");
  }
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new Error("import root must be object");
  }
  const parsedKind = String(parsed.kind || "").trim();
  if (!parsedKind) {
    throw new Error(
      `confirm activity replay trail import confirm trail bundle requires kind=${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_IMPORT_CONFIRM_TRAIL_KIND}`
    );
  }
  if (parsedKind !== QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_IMPORT_CONFIRM_TRAIL_KIND) {
    throw new Error(
      `unexpected kind (expected ${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_IMPORT_CONFIRM_TRAIL_KIND})`
    );
  }
  if (parsed.schema_version === undefined) {
    throw new Error(
      `confirm activity replay trail import confirm trail bundle requires schema_version=${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_IMPORT_CONFIRM_TRAIL_SCHEMA_VERSION}`
    );
  }
  const schemaVersion = Math.floor(Number(parsed.schema_version || 0));
  if (schemaVersion !== QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_IMPORT_CONFIRM_TRAIL_SCHEMA_VERSION) {
    throw new Error(
      `unsupported schema_version (expected ${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_IMPORT_CONFIRM_TRAIL_SCHEMA_VERSION})`
    );
  }
  if (!Array.isArray(parsed.entries)) {
    throw new Error("confirm activity replay trail import confirm trail bundle missing entries array");
  }
  const rows = parsed.entries
    .map((row, idx) => normalizeQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityEntry(row, idx))
    .filter(Boolean)
    .slice(0, QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_IMPORT_CONFIRM_TRAIL_LIMIT);
  return {
    schema_version: schemaVersion,
    kind: parsedKind,
    exported_at_iso: String(parsed.exported_at_iso || "-"),
    entry_count: rows.length,
    entries: rows,
  };
}

function parseQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackageText(rawText) {
  const text = String(rawText || "").trim();
  if (!text) {
    throw new Error("empty import payload");
  }
  let parsed = null;
  try {
    parsed = JSON.parse(text);
  } catch (_) {
    throw new Error("invalid JSON");
  }
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new Error("import root must be object");
  }
  const parsedKind = String(parsed.kind || "").trim();
  if (!parsedKind) {
    throw new Error(
      `dry-run handoff package requires kind=${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_KIND}`
    );
  }
  if (parsedKind !== QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_KIND) {
    throw new Error(
      `unexpected kind (expected ${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_KIND})`
    );
  }
  if (parsed.schema_version === undefined) {
    throw new Error(
      `dry-run handoff package requires schema_version=${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_SCHEMA_VERSION}`
    );
  }
  const schemaVersion = Math.floor(Number(parsed.schema_version || 0));
  if (schemaVersion !== QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_SCHEMA_VERSION) {
    throw new Error(
      `unsupported schema_version (expected ${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_SCHEMA_VERSION})`
    );
  }
  const summaryRaw = parsed.dry_run_summary;
  if (!summaryRaw || typeof summaryRaw !== "object" || Array.isArray(summaryRaw)) {
    throw new Error("dry-run handoff package missing dry_run_summary");
  }
  const safetyRaw = parsed.apply_safety;
  if (!safetyRaw || typeof safetyRaw !== "object" || Array.isArray(safetyRaw)) {
    throw new Error("dry-run handoff package missing apply_safety");
  }
  const snapshotRaw = parsed.trust_audit_bundle_snapshot;
  if (!snapshotRaw || typeof snapshotRaw !== "object" || Array.isArray(snapshotRaw)) {
    throw new Error("dry-run handoff package missing trust_audit_bundle_snapshot");
  }
  const pkg = buildQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackage({
    dry_run_summary: summaryRaw,
    apply_safety: safetyRaw,
    import_preview: parsed.import_preview,
    trust_audit_bundle_kind: snapshotRaw.kind,
    trust_audit_bundle_schema_version: snapshotRaw.schema_version,
    trust_audit_bundle_policy_mode: snapshotRaw.trust_policy_mode,
    trust_audit_bundle_override_event_count: snapshotRaw.override_event_count,
    trust_audit_bundle_parse_state: snapshotRaw.parse_state,
  });
  return {
    ...pkg,
    schema_version: schemaVersion,
    kind: parsedKind,
    exported_at_iso: String(parsed.exported_at_iso || "-"),
  };
}

function parseQuickTelemetryStrictRollbackTrustAuditBundleText(rawText) {
  const text = String(rawText || "").trim();
  if (!text) {
    throw new Error("empty import payload");
  }
  let parsed = null;
  try {
    parsed = JSON.parse(text);
  } catch (_) {
    throw new Error("invalid JSON");
  }
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new Error("import root must be object");
  }
  const parsedKind = String(parsed.kind || "").trim();
  if (!parsedKind) {
    throw new Error(
      `trust audit bundle requires kind=${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_BUNDLE_KIND}`
    );
  }
  if (parsedKind !== QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_BUNDLE_KIND) {
    throw new Error(
      `unexpected kind (expected ${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_BUNDLE_KIND})`
    );
  }
  if (parsed.schema_version === undefined) {
    throw new Error(
      `trust audit bundle requires schema_version=${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_BUNDLE_SCHEMA_VERSION}`
    );
  }
  const schemaVersion = Math.floor(Number(parsed.schema_version || 0));
  if (schemaVersion !== QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_BUNDLE_SCHEMA_VERSION) {
    throw new Error(
      `unsupported schema_version (expected ${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_BUNDLE_SCHEMA_VERSION})`
    );
  }
  const overrideLogRaw = parsed.override_log;
  if (!overrideLogRaw || typeof overrideLogRaw !== "object" || Array.isArray(overrideLogRaw)) {
    throw new Error("trust audit bundle missing override_log");
  }
  const overrideEntries = overrideLogRaw.entries;
  if (!Array.isArray(overrideEntries)) {
    throw new Error("trust audit bundle override_log.entries must be array");
  }
  const provenanceRaw = parsed.provenance_snapshot;
  if (!provenanceRaw || typeof provenanceRaw !== "object" || Array.isArray(provenanceRaw)) {
    throw new Error("trust audit bundle missing provenance_snapshot");
  }
  const overrideLog = buildQuickTelemetryStrictRollbackOverrideLogBundle(overrideEntries);
  return {
    schema_version: schemaVersion,
    kind: parsedKind,
    exported_at_iso: String(parsed.exported_at_iso || "-"),
    trust_policy_mode: normalizeQuickTelemetryStrictRollbackPackageTrustPolicy(
      parsed.trust_policy_mode
    ),
    override_log: {
      schema_version: overrideLog.schema_version,
      kind: overrideLog.kind,
      entry_count: overrideLog.entry_count,
      entries: overrideLog.entries,
    },
    provenance_snapshot: normalizeQuickTelemetryStrictRollbackTrustAuditProvenanceSnapshot(provenanceRaw),
  };
}

function buildQuickTelemetryStrictRollbackDrillPackage(rawPackage) {
  const src = rawPackage && typeof rawPackage === "object" && !Array.isArray(rawPackage)
    ? rawPackage
    : {};
  const snapshotRaw = src.preset_snapshot && typeof src.preset_snapshot === "object" && !Array.isArray(src.preset_snapshot)
    ? src.preset_snapshot
    : {};
  const checklistRaw = src.checklist_report && typeof src.checklist_report === "object" && !Array.isArray(src.checklist_report)
    ? src.checklist_report
    : {};
  const rowCapRaw = clampInteger(snapshotRaw.row_cap, 4, 200, 16);
  const rowCap = QUICK_TELEMETRY_DRILLDOWN_IMPORT_ROW_CAP_OPTIONS.includes(String(rowCapRaw))
    ? rowCapRaw
    : Number(CONTRACT_OVERLAY_DEFAULT_PREFS.quickTelemetryDrilldownImportRowCap || 16);
  const checklistItems = Array.isArray(checklistRaw.items)
    ? checklistRaw.items.slice(0, 32).map((row, idx) => ({
      id: String(row?.id || `item_${idx}`),
      label: String(row?.label || `item_${idx}`),
      ok: Boolean(row?.ok),
    }))
    : [];
  const cutoverTimeline = buildQuickTelemetryDrilldownStrictCutoverLedgerBundle(
    Array.isArray(src.cutover_timeline_entries) ? src.cutover_timeline_entries : []
  ).entries;
  const latestTimeline = cutoverTimeline[0] || {};
  const packageCore = {
    schema_version: QUICK_TELEMETRY_STRICT_ROLLBACK_DRILL_PACKAGE_SCHEMA_VERSION,
    kind: QUICK_TELEMETRY_STRICT_ROLLBACK_DRILL_PACKAGE_KIND,
    exported_at_iso: new Date().toISOString(),
    preset_snapshot: {
      preset_id: String(snapshotRaw.preset_id || "custom"),
      import_mode: normalizeQuickTelemetryDrilldownImportFilterBundleMode(snapshotRaw.import_mode || "compat"),
      failure_only: Boolean(snapshotRaw.failure_only),
      reason_query: String(snapshotRaw.reason_query || "").slice(0, FILTER_IMPORT_AUDIT_QUICK_REASON_QUERY_MAX),
      conflict_only: Boolean(snapshotRaw.conflict_only),
      conflict_filter: normalizeQuickTelemetryDrilldownImportConflictFilter(snapshotRaw.conflict_filter || "all"),
      name_query: String(snapshotRaw.name_query || "").slice(0, QUICK_TELEMETRY_DRILLDOWN_IMPORT_NAME_QUERY_MAX),
      row_cap: rowCap,
    },
    checklist_report: {
      status: String(checklistRaw.status || "").trim().toUpperCase() === "READY" ? "READY" : "HOLD",
      pass_count: clampInteger(checklistRaw.pass_count, 0, 128, 0),
      item_count: clampInteger(checklistRaw.item_count, 0, 128, 0),
      failed_visible_count: clampInteger(checklistRaw.failed_visible_count, 0, 1_000_000, 0),
      visible_count: clampInteger(checklistRaw.visible_count, 0, 1_000_000, 0),
      generated_at_iso: String(checklistRaw.generated_at_iso || new Date().toISOString()),
      items: checklistItems,
    },
    cutover_timeline_summary: {
      entry_count: cutoverTimeline.length,
      latest_event_id: String(latestTimeline.event_id || "-"),
      latest_checklist_status: String(latestTimeline.checklist_status || "HOLD"),
      latest_timestamp_iso: String(latestTimeline.timestamp_iso || "-"),
    },
    cutover_timeline_entries: cutoverTimeline,
  };
  const provenance = normalizeQuickTelemetryStrictRollbackDrillPackageProvenance(
    src.provenance,
    packageCore
  );
  return {
    ...packageCore,
    provenance: {
      source_stamp: provenance.source_stamp,
      payload_checksum: provenance.payload_checksum,
      checksum_algo: QUICK_TELEMETRY_STRICT_ROLLBACK_DRILL_PACKAGE_CHECKSUM_ALGO,
      checksum_hint: provenance.checksum_hint,
    },
  };
}

function serializeQuickTelemetryStrictRollbackDrillPackage(rawPackage) {
  return JSON.stringify(buildQuickTelemetryStrictRollbackDrillPackage(rawPackage), null, 2);
}

function parseQuickTelemetryStrictRollbackDrillPackageText(rawText) {
  const text = String(rawText || "").trim();
  if (!text) {
    throw new Error("empty import payload");
  }
  let parsed = null;
  try {
    parsed = JSON.parse(text);
  } catch (_) {
    throw new Error("invalid JSON");
  }
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new Error("import root must be object");
  }
  const parsedKind = String(parsed.kind || "").trim();
  if (!parsedKind) {
    throw new Error(
      `rollback package requires kind=${QUICK_TELEMETRY_STRICT_ROLLBACK_DRILL_PACKAGE_KIND}`
    );
  }
  if (parsedKind !== QUICK_TELEMETRY_STRICT_ROLLBACK_DRILL_PACKAGE_KIND) {
    throw new Error(
      `unexpected kind (expected ${QUICK_TELEMETRY_STRICT_ROLLBACK_DRILL_PACKAGE_KIND})`
    );
  }
  if (parsed.schema_version === undefined) {
    throw new Error(
      `rollback package requires schema_version=${QUICK_TELEMETRY_STRICT_ROLLBACK_DRILL_PACKAGE_SCHEMA_VERSION}`
    );
  }
  const schemaVersion = Math.floor(Number(parsed.schema_version || 0));
  if (schemaVersion !== QUICK_TELEMETRY_STRICT_ROLLBACK_DRILL_PACKAGE_SCHEMA_VERSION) {
    throw new Error(
      `unsupported schema_version (expected ${QUICK_TELEMETRY_STRICT_ROLLBACK_DRILL_PACKAGE_SCHEMA_VERSION})`
    );
  }
  const snapshot = parsed.preset_snapshot;
  if (!snapshot || typeof snapshot !== "object" || Array.isArray(snapshot)) {
    throw new Error("rollback package missing preset_snapshot");
  }
  const checklist = parsed.checklist_report;
  if (!checklist || typeof checklist !== "object" || Array.isArray(checklist)) {
    throw new Error("rollback package missing checklist_report");
  }
  const normalized = buildQuickTelemetryStrictRollbackDrillPackage(parsed);
  const packageCore = {
    schema_version: normalized.schema_version,
    kind: normalized.kind,
    exported_at_iso: normalized.exported_at_iso,
    preset_snapshot: normalized.preset_snapshot,
    checklist_report: normalized.checklist_report,
    cutover_timeline_summary: normalized.cutover_timeline_summary,
    cutover_timeline_entries: normalized.cutover_timeline_entries,
  };
  const provenanceRaw = parsed.provenance && typeof parsed.provenance === "object" && !Array.isArray(parsed.provenance)
    ? parsed.provenance
    : {};
  const hasSourceStamp = String(provenanceRaw.source_stamp || "").trim().length > 0;
  const hasPayloadChecksum = String(provenanceRaw.payload_checksum || "").trim().length > 0;
  const provenance = normalizeQuickTelemetryStrictRollbackDrillPackageProvenance(
    provenanceRaw,
    packageCore
  );
  return {
    ...normalized,
    provenance_guard: {
      source_stamp: provenance.source_stamp,
      payload_checksum: String(provenanceRaw.payload_checksum || "").trim().toLowerCase(),
      computed_checksum: provenance.computed_checksum,
      source_match: hasSourceStamp ? provenance.source_match : false,
      checksum_match: hasPayloadChecksum ? provenance.checksum_match : false,
      missing_source_stamp: !hasSourceStamp,
      missing_payload_checksum: !hasPayloadChecksum,
      has_guard_issue: (
        !hasSourceStamp
        || !hasPayloadChecksum
        || (hasSourceStamp && !provenance.source_match)
        || (hasPayloadChecksum && !provenance.checksum_match)
      ),
      checksum_hint: provenance.checksum_hint,
    },
  };
}

function matchQuickTelemetryDrilldownImportConflictFilter(row, filterId) {
  const rid = normalizeQuickTelemetryDrilldownImportConflictFilter(filterId);
  if (rid === "all") return true;
  const conflict = String(row?.conflict || "");
  const changed = Boolean(row?.changed);
  if (rid === "new") return conflict === "new";
  if (rid === "overwrite_any") return conflict !== "new";
  if (rid === "overwrite_changed") return conflict !== "new" && changed;
  if (rid === "overwrite_same") return conflict !== "new" && !changed;
  if (rid === "overwrite_builtin") return conflict === "overwrite_builtin";
  if (rid === "overwrite_custom") return conflict === "overwrite_custom";
  return true;
}

function normalizeShortcutBindings(raw, fallback) {
  const source = raw && typeof raw === "object" && !Array.isArray(raw) ? raw : {};
  const base = fallback && typeof fallback === "object" && !Array.isArray(fallback)
    ? fallback
    : DEFAULT_SHORTCUT_BINDINGS;
  const out = {};
  SHORTCUT_ACTION_DEFS.forEach((def) => {
    const k = String(def.id || "");
    const token = normalizeShortcutToken(source[k]);
    if (token) {
      out[k] = token;
      return;
    }
    out[k] = normalizeShortcutToken(base[k]);
  });
  return out;
}

function normalizeDetailFieldStates(raw, fallback) {
  const source = raw && typeof raw === "object" && !Array.isArray(raw) ? raw : {};
  const base = fallback && typeof fallback === "object" && !Array.isArray(fallback)
    ? fallback
    : DEFAULT_DETAIL_FIELD_STATES;
  const out = {};
  DETAIL_FIELD_DEFS.forEach((def) => {
    const k = String(def.id || "");
    if (!k) return;
    if (source[k] !== undefined) {
      out[k] = Boolean(source[k]);
      return;
    }
    out[k] = Boolean(base[k]);
  });
  if (!Object.values(out).some(Boolean)) {
    out.timestamp_iso = true;
  }
  return out;
}

function normalizeFilterPresetConfig(raw, fallback) {
  const source = raw && typeof raw === "object" && !Array.isArray(raw) ? raw : {};
  const base = fallback && typeof fallback === "object" && !Array.isArray(fallback)
    ? fallback
    : DEFAULT_FILTER_PRESETS.default;
  const allowedSev = new Set(SEVERITY_FILTER_OPTIONS.map((x) => String(x.id || "")));
  const allowedPol = new Set(POLICY_FILTER_OPTIONS.map((x) => String(x.id || "")));
  const sourceFilter = String(source.sourceFilter ?? base.sourceFilter ?? CONTRACT_OVERLAY_DEFAULT_PREFS.sourceFilter);
  const severityRaw = String(source.severityFilter ?? base.severityFilter ?? CONTRACT_OVERLAY_DEFAULT_PREFS.severityFilter);
  const policyRaw = String(source.policyFilter ?? base.policyFilter ?? CONTRACT_OVERLAY_DEFAULT_PREFS.policyFilter);
  return {
    sourceFilter,
    severityFilter: allowedSev.has(severityRaw) ? severityRaw : CONTRACT_OVERLAY_DEFAULT_PREFS.severityFilter,
    policyFilter: allowedPol.has(policyRaw) ? policyRaw : CONTRACT_OVERLAY_DEFAULT_PREFS.policyFilter,
    pinnedRunId: String(source.pinnedRunId ?? base.pinnedRunId ?? CONTRACT_OVERLAY_DEFAULT_PREFS.pinnedRunId),
    nonZeroOnly: Boolean(source.nonZeroOnly ?? base.nonZeroOnly ?? CONTRACT_OVERLAY_DEFAULT_PREFS.nonZeroOnly),
    gateHistoryLimit: String(
      clampInteger(
        source.gateHistoryLimit ?? base.gateHistoryLimit ?? CONTRACT_OVERLAY_DEFAULT_PREFS.gateHistoryLimit,
        32,
        4096,
        CONTRACT_OVERLAY_DEFAULT_PREFS.gateHistoryLimit
      )
    ),
    gateHistoryPages: String(
      clampInteger(
        source.gateHistoryPages ?? base.gateHistoryPages ?? CONTRACT_OVERLAY_DEFAULT_PREFS.gateHistoryPages,
        1,
        8,
        CONTRACT_OVERLAY_DEFAULT_PREFS.gateHistoryPages
      )
    ),
    rowWindowSizeText: String(
      clampInteger(
        source.rowWindowSizeText ?? source.rowWindowSize ?? base.rowWindowSizeText ?? base.rowWindowSize ?? CONTRACT_OVERLAY_DEFAULT_PREFS.rowWindowSize,
        20,
        500,
        CONTRACT_OVERLAY_DEFAULT_PREFS.rowWindowSize
      )
    ),
  };
}

function normalizeQuickTelemetryDrilldownProfile(raw, fallback) {
  const source = raw && typeof raw === "object" && !Array.isArray(raw) ? raw : {};
  const base = fallback && typeof fallback === "object" && !Array.isArray(fallback)
    ? fallback
    : DEFAULT_FILTER_IMPORT_AUDIT_QUICK_TELEMETRY_DRILLDOWN_PROFILES.default;
  return {
    failure_only: Boolean(
      source.failure_only !== undefined ? source.failure_only : base.failure_only
    ),
    reason_query: String(
      source.reason_query !== undefined ? source.reason_query : base.reason_query
    ).trim().toLowerCase().slice(0, FILTER_IMPORT_AUDIT_QUICK_REASON_QUERY_MAX),
  };
}

function loadShortcutProfiles() {
  const normalizedDefaults = {};
  Object.keys(DEFAULT_SHORTCUT_PROFILES).forEach((name) => {
    normalizedDefaults[String(name)] = normalizeShortcutBindings(
      DEFAULT_SHORTCUT_PROFILES[name],
      DEFAULT_SHORTCUT_BINDINGS
    );
  });
  try {
    if (typeof window === "undefined" || !window.localStorage) return normalizedDefaults;
    const raw = String(window.localStorage.getItem(CONTRACT_OVERLAY_SHORTCUT_PROFILES_KEY) || "").trim();
    if (!raw) return normalizedDefaults;
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return normalizedDefaults;
    const merged = { ...normalizedDefaults };
    Object.keys(parsed).forEach((name) => {
      const pname = String(name || "").trim();
      if (!pname) return;
      merged[pname] = normalizeShortcutBindings(parsed[name], normalizedDefaults.default);
    });
    return merged;
  } catch (_) {
    return normalizedDefaults;
  }
}

function saveShortcutProfiles(profiles) {
  try {
    if (typeof window === "undefined" || !window.localStorage) return;
    const rows = profiles && typeof profiles === "object" && !Array.isArray(profiles) ? profiles : {};
    const payload = {};
    Object.keys(rows).forEach((name) => {
      const pname = String(name || "").trim();
      if (!pname) return;
      payload[pname] = normalizeShortcutBindings(rows[pname], DEFAULT_SHORTCUT_BINDINGS);
    });
    window.localStorage.setItem(CONTRACT_OVERLAY_SHORTCUT_PROFILES_KEY, JSON.stringify(payload));
  } catch (_) {
    // localStorage may be blocked; ignore and continue with in-memory state
  }
}

function loadFilterPresets() {
  const normalizedDefaults = {};
  Object.keys(DEFAULT_FILTER_PRESETS).forEach((name) => {
    normalizedDefaults[String(name)] = normalizeFilterPresetConfig(
      DEFAULT_FILTER_PRESETS[name],
      DEFAULT_FILTER_PRESETS.default
    );
  });
  try {
    if (typeof window === "undefined" || !window.localStorage) return normalizedDefaults;
    const raw = String(window.localStorage.getItem(CONTRACT_OVERLAY_FILTER_PRESETS_KEY) || "").trim();
    if (!raw) return normalizedDefaults;
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return normalizedDefaults;
    const merged = { ...normalizedDefaults };
    Object.keys(parsed).forEach((name) => {
      const pname = normalizeFilterPresetName(name);
      if (!pname) return;
      merged[pname] = normalizeFilterPresetConfig(parsed[name], normalizedDefaults.default);
    });
    return merged;
  } catch (_) {
    return normalizedDefaults;
  }
}

function saveFilterPresets(presets) {
  try {
    if (typeof window === "undefined" || !window.localStorage) return;
    const rows = presets && typeof presets === "object" && !Array.isArray(presets) ? presets : {};
    const payload = {};
    Object.keys(rows).forEach((name) => {
      const pname = normalizeFilterPresetName(name);
      if (!pname) return;
      payload[pname] = normalizeFilterPresetConfig(rows[name], DEFAULT_FILTER_PRESETS.default);
    });
    window.localStorage.setItem(CONTRACT_OVERLAY_FILTER_PRESETS_KEY, JSON.stringify(payload));
  } catch (_) {
    // localStorage may be blocked; ignore and continue with in-memory state
  }
}

function loadQuickTelemetryDrilldownProfiles() {
  const normalizedDefaults = {};
  Object.keys(DEFAULT_FILTER_IMPORT_AUDIT_QUICK_TELEMETRY_DRILLDOWN_PROFILES).forEach((name) => {
    normalizedDefaults[String(name)] = normalizeQuickTelemetryDrilldownProfile(
      DEFAULT_FILTER_IMPORT_AUDIT_QUICK_TELEMETRY_DRILLDOWN_PROFILES[name],
      DEFAULT_FILTER_IMPORT_AUDIT_QUICK_TELEMETRY_DRILLDOWN_PROFILES.default
    );
  });
  try {
    if (typeof window === "undefined" || !window.localStorage) return normalizedDefaults;
    const raw = String(window.localStorage.getItem(CONTRACT_OVERLAY_QUICK_TELEMETRY_DRILLDOWN_PROFILES_KEY) || "").trim();
    if (!raw) return normalizedDefaults;
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return normalizedDefaults;
    const merged = { ...normalizedDefaults };
    Object.keys(parsed).forEach((name) => {
      const pname = normalizeQuickTelemetryDrilldownProfileName(name);
      if (!pname) return;
      const fallback = normalizedDefaults[pname] || normalizedDefaults.default;
      merged[pname] = normalizeQuickTelemetryDrilldownProfile(parsed[name], fallback);
    });
    return merged;
  } catch (_) {
    return normalizedDefaults;
  }
}

function saveQuickTelemetryDrilldownProfiles(profiles) {
  try {
    if (typeof window === "undefined" || !window.localStorage) return;
    const rows = profiles && typeof profiles === "object" && !Array.isArray(profiles) ? profiles : {};
    const payload = {};
    Object.keys(rows).forEach((name) => {
      const pname = normalizeQuickTelemetryDrilldownProfileName(name);
      if (!pname) return;
      const fallback = DEFAULT_FILTER_IMPORT_AUDIT_QUICK_TELEMETRY_DRILLDOWN_PROFILES[pname]
        || DEFAULT_FILTER_IMPORT_AUDIT_QUICK_TELEMETRY_DRILLDOWN_PROFILES.default;
      payload[pname] = normalizeQuickTelemetryDrilldownProfile(rows[name], fallback);
    });
    window.localStorage.setItem(CONTRACT_OVERLAY_QUICK_TELEMETRY_DRILLDOWN_PROFILES_KEY, JSON.stringify(payload));
  } catch (_) {
    // localStorage may be blocked; ignore and continue with in-memory state
  }
}

function cloneNormalizedQuickTelemetryDrilldownProfiles(profiles) {
  const rows = profiles && typeof profiles === "object" && !Array.isArray(profiles) ? profiles : {};
  const out = {};
  Object.keys(rows).forEach((name) => {
    const pname = normalizeQuickTelemetryDrilldownProfileName(name);
    if (!pname) return;
    const fallback = DEFAULT_FILTER_IMPORT_AUDIT_QUICK_TELEMETRY_DRILLDOWN_PROFILES[pname]
      || DEFAULT_FILTER_IMPORT_AUDIT_QUICK_TELEMETRY_DRILLDOWN_PROFILES.default;
    out[pname] = normalizeQuickTelemetryDrilldownProfile(rows[name], fallback);
  });
  return out;
}

function cloneNormalizedFilterPresets(presets) {
  const rows = presets && typeof presets === "object" && !Array.isArray(presets) ? presets : {};
  const out = {};
  Object.keys(rows).forEach((name) => {
    const pname = normalizeFilterPresetName(name);
    if (!pname) return;
    const fallback = DEFAULT_FILTER_PRESETS[pname] || DEFAULT_FILTER_PRESETS.default;
    out[pname] = normalizeFilterPresetConfig(rows[pname], fallback);
  });
  return out;
}

function buildFilterPresetStateSnapshot(presets, activeFilterPreset, filterPresetDraft) {
  return {
    presets: cloneNormalizedFilterPresets(presets),
    activeFilterPreset: String(activeFilterPreset || "default"),
    filterPresetDraft: String(filterPresetDraft || CONTRACT_OVERLAY_DEFAULT_PREFS.filterPresetDraft),
    captured_at_iso: new Date().toISOString(),
  };
}

function compactNameList(names, maxItems = 6) {
  const rows = Array.isArray(names) ? names.map((x) => String(x || "").trim()).filter(Boolean) : [];
  if (rows.length <= maxItems) return rows;
  return [...rows.slice(0, maxItems), `...(+${rows.length - maxItems})`];
}

function sanitizeAuditNameList(rawList, maxItems = 256) {
  const rows = Array.isArray(rawList) ? rawList : [];
  const out = [];
  rows.forEach((item) => {
    const token = String(item || "").trim();
    if (!token) return;
    out.push(token.slice(0, 64));
  });
  return out.slice(0, maxItems);
}

function normalizeFilterPresetStateSnapshot(raw) {
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) return null;
  const presets = cloneNormalizedFilterPresets(raw.presets);
  if (Object.keys(presets).length === 0) return null;
  return {
    presets,
    activeFilterPreset: String(raw.activeFilterPreset || "default"),
    filterPresetDraft: String(raw.filterPresetDraft || CONTRACT_OVERLAY_DEFAULT_PREFS.filterPresetDraft),
    captured_at_iso: String(raw.captured_at_iso || "-"),
  };
}

function normalizeFilterImportAuditEntry(raw, idx = 0) {
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) return null;
  const kindRaw = String(raw.kind || "import").toLowerCase();
  const kind = kindRaw === "undo" || kindRaw === "redo" ? kindRaw : "import";
  const modeRaw = String(raw.mode || "merge").toLowerCase();
  const mode = modeRaw === "replace_custom" || modeRaw === "undo" || modeRaw === "redo" ? modeRaw : "merge";
  const clampCount = (value) => clampInteger(value, 0, 1_000_000, 0);
  return {
    id: String(raw.id || `fia_restore_${idx}`),
    kind,
    timestamp_iso: String(raw.timestamp_iso || "-"),
    mode,
    selected_count: clampCount(raw.selected_count),
    added_count: clampCount(raw.added_count),
    changed_count: clampCount(raw.changed_count),
    removed_count: clampCount(raw.removed_count),
    new_count: clampCount(raw.new_count),
    overwrite_builtin_count: clampCount(raw.overwrite_builtin_count),
    overwrite_custom_count: clampCount(raw.overwrite_custom_count),
    selected_names: sanitizeAuditNameList(raw.selected_names),
    added_names: sanitizeAuditNameList(raw.added_names),
    removed_names: sanitizeAuditNameList(raw.removed_names),
    note: String(raw.note || "").slice(0, 240),
  };
}

function loadFilterImportHistoryState() {
  const empty = { undoStack: [], redoStack: [], auditTrail: [] };
  try {
    if (typeof window === "undefined" || !window.localStorage) return empty;
    const raw = String(window.localStorage.getItem(CONTRACT_OVERLAY_FILTER_IMPORT_HISTORY_KEY) || "").trim();
    if (!raw) return empty;
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return empty;
    const undoSource = Array.isArray(parsed.undo_stack) ? parsed.undo_stack : [];
    const redoSource = Array.isArray(parsed.redo_stack) ? parsed.redo_stack : [];
    const auditSource = Array.isArray(parsed.audit_trail) ? parsed.audit_trail : [];
    const undoStack = undoSource
      .map((row) => normalizeFilterPresetStateSnapshot(row))
      .filter(Boolean)
      .slice(-FILTER_IMPORT_HISTORY_LIMIT);
    const redoStack = redoSource
      .map((row) => normalizeFilterPresetStateSnapshot(row))
      .filter(Boolean)
      .slice(-FILTER_IMPORT_HISTORY_LIMIT);
    const auditTrail = auditSource
      .map((row, idx) => normalizeFilterImportAuditEntry(row, idx))
      .filter(Boolean)
      .slice(0, FILTER_IMPORT_HISTORY_LIMIT);
    return { undoStack, redoStack, auditTrail };
  } catch (_) {
    return empty;
  }
}

function saveFilterImportHistoryState(history) {
  try {
    if (typeof window === "undefined" || !window.localStorage) return;
    const row = history && typeof history === "object" && !Array.isArray(history) ? history : {};
    const undoSource = Array.isArray(row.undoStack) ? row.undoStack : [];
    const redoSource = Array.isArray(row.redoStack) ? row.redoStack : [];
    const auditSource = Array.isArray(row.auditTrail) ? row.auditTrail : [];
    const payload = {
      schema_version: 1,
      kind: "graph_lab_contract_overlay_filter_import_history",
      saved_at_iso: new Date().toISOString(),
      undo_stack: undoSource
        .map((x) => normalizeFilterPresetStateSnapshot(x))
        .filter(Boolean)
        .slice(-FILTER_IMPORT_HISTORY_LIMIT),
      redo_stack: redoSource
        .map((x) => normalizeFilterPresetStateSnapshot(x))
        .filter(Boolean)
        .slice(-FILTER_IMPORT_HISTORY_LIMIT),
      audit_trail: auditSource
        .map((x, idx) => normalizeFilterImportAuditEntry(x, idx))
        .filter(Boolean)
        .slice(0, FILTER_IMPORT_HISTORY_LIMIT),
    };
    window.localStorage.setItem(CONTRACT_OVERLAY_FILTER_IMPORT_HISTORY_KEY, JSON.stringify(payload));
  } catch (_) {
    // localStorage may be blocked; ignore and continue with in-memory state
  }
}

function buildFilterImportAuditExportBundle(auditTrail) {
  const rows = Array.isArray(auditTrail) ? auditTrail : [];
  const entries = rows
    .map((row, idx) => normalizeFilterImportAuditEntry(row, idx))
    .filter(Boolean);
  return {
    schema_version: 1,
    kind: "graph_lab_contract_overlay_filter_import_audit",
    exported_at_iso: new Date().toISOString(),
    entries,
  };
}

function serializeFilterImportAuditExportBundle(auditTrail) {
  return JSON.stringify(buildFilterImportAuditExportBundle(auditTrail), null, 2);
}

function buildFilterImportAuditDeepLinkBundle(payload) {
  const row = payload && typeof payload === "object" && !Array.isArray(payload) ? payload : {};
  const selectedEntry = normalizeFilterImportAuditEntry(row.activeEntry, 0);
  const visibleRows = Array.isArray(row.visibleEntries)
    ? row.visibleEntries.map((entry, idx) => normalizeFilterImportAuditEntry(entry, idx)).filter(Boolean)
    : [];
  const query = row.query && typeof row.query === "object" && !Array.isArray(row.query) ? row.query : {};
  const paging = row.paging && typeof row.paging === "object" && !Array.isArray(row.paging) ? row.paging : {};
  const deepLink = (() => {
    try {
      if (typeof window === "undefined" || !window.location) return "";
      const u = new URL(String(window.location.href || ""));
      u.hash = `audit_entry=${encodeURIComponent(String(selectedEntry?.id || ""))}`;
      return String(u.toString());
    } catch (_) {
      return "";
    }
  })();
  return {
    schema_version: FILTER_IMPORT_AUDIT_DEEPLINK_SCHEMA_VERSION,
    kind: FILTER_IMPORT_AUDIT_DEEPLINK_KIND,
    exported_at_iso: new Date().toISOString(),
    deep_link: deepLink,
    active_entry_id: String(selectedEntry?.id || ""),
    active_preset_id: String(row.activePresetId || ""),
    pinned_preset_id: String(row.pinnedPresetId || ""),
    counts: {
      trail: clampInteger(row.trailCount, 0, 1_000_000, 0),
      filtered: clampInteger(row.filteredCount, 0, 1_000_000, 0),
      visible: clampInteger(row.visibleCount, 0, 1_000_000, 0),
    },
    query: {
      search: String(query.search || ""),
      kind: String(query.kind || "all"),
      mode: String(query.mode || "all"),
    },
    paging: {
      offset: clampInteger(paging.offset, 0, 1_000_000, 0),
      cap: clampInteger(paging.cap, 1, 200, 24),
      end: clampInteger(paging.end, 0, 1_000_000, 0),
    },
    active_entry: selectedEntry,
    visible_entries: visibleRows,
  };
}

function serializeFilterImportAuditDeepLinkBundle(payload) {
  return JSON.stringify(buildFilterImportAuditDeepLinkBundle(payload), null, 2);
}

function parseFilterImportAuditDeepLinkBundleText(rawText) {
  const text = String(rawText || "").trim();
  if (!text) {
    throw new Error("empty import payload");
  }
  let parsed = null;
  try {
    parsed = JSON.parse(text);
  } catch (_) {
    throw new Error("invalid JSON");
  }
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new Error("import root must be object");
  }
  if (String(parsed.kind || "") !== FILTER_IMPORT_AUDIT_DEEPLINK_KIND) {
    throw new Error("kind mismatch: expected audit deeplink bundle");
  }
  const schemaVersionRaw = Number(parsed.schema_version);
  if (!Number.isFinite(schemaVersionRaw)) {
    throw new Error("schema_version missing");
  }
  const schemaVersion = Math.floor(schemaVersionRaw);
  if (schemaVersion !== FILTER_IMPORT_AUDIT_DEEPLINK_SCHEMA_VERSION) {
    throw new Error(`unsupported schema_version (${schemaVersion})`);
  }
  const query = parsed.query && typeof parsed.query === "object" && !Array.isArray(parsed.query)
    ? parsed.query
    : {};
  const paging = parsed.paging && typeof parsed.paging === "object" && !Array.isArray(parsed.paging)
    ? parsed.paging
    : {};
  const allowedKind = new Set(FILTER_IMPORT_AUDIT_KIND_OPTIONS.map((x) => String(x || "")));
  const allowedMode = new Set(FILTER_IMPORT_AUDIT_MODE_OPTIONS.map((x) => String(x || "")));
  const kindRaw = String(query.kind || "all");
  const modeRaw = String(query.mode || "all");
  const kind = allowedKind.has(kindRaw) ? kindRaw : "all";
  const mode = allowedMode.has(modeRaw) ? modeRaw : "all";
  const capRaw = clampInteger(paging.cap, 6, 200, 24);
  const cap = FILTER_IMPORT_AUDIT_ROW_CAP_OPTIONS.includes(String(capRaw))
    ? String(capRaw)
    : String(CONTRACT_OVERLAY_DEFAULT_PREFS.filterImportAuditRowCap || "24");
  const pinnedPresetRaw = String(parsed.pinned_preset_id || "").trim();
  const activePresetRaw = String(parsed.active_preset_id || "").trim();
  const isKnownPreset = (id) =>
    Boolean(id) && FILTER_IMPORT_AUDIT_QUERY_PRESETS.some((row) => String(row?.id || "") === id);
  return {
    schema_version: schemaVersion,
    kind: FILTER_IMPORT_AUDIT_DEEPLINK_KIND,
    query: {
      search: String(query.search || ""),
      kind,
      mode,
    },
    paging: {
      cap,
      offset: clampInteger(paging.offset, 0, 1_000_000, 0),
    },
    active_entry_id: String(parsed.active_entry_id || "").trim(),
    active_preset_id: isKnownPreset(activePresetRaw) ? activePresetRaw : "",
    pinned_preset_id: isKnownPreset(pinnedPresetRaw) ? pinnedPresetRaw : "",
  };
}

function buildFilterImportAuditDetailText(entry) {
  const row = entry && typeof entry === "object" ? entry : null;
  if (!row) return "(no audit entry selected)";
  const lines = [
    `id: ${String(row.id || "-")}`,
    `timestamp_iso: ${String(row.timestamp_iso || "-")}`,
    `kind: ${String(row.kind || "-")}`,
    `mode: ${String(row.mode || "-")}`,
    `selected_count: ${Number(row.selected_count || 0)}`,
    `added_count: ${Number(row.added_count || 0)}`,
    `changed_count: ${Number(row.changed_count || 0)}`,
    `removed_count: ${Number(row.removed_count || 0)}`,
    `new_count: ${Number(row.new_count || 0)}`,
    `overwrite_builtin_count: ${Number(row.overwrite_builtin_count || 0)}`,
    `overwrite_custom_count: ${Number(row.overwrite_custom_count || 0)}`,
    `note: ${String(row.note || "-")}`,
    "",
    "selected_names:",
    ...(sanitizeAuditNameList(row.selected_names).map((name) => `- ${name}`)),
    "",
    "added_names:",
    ...(sanitizeAuditNameList(row.added_names).map((name) => `- ${name}`)),
    "",
    "removed_names:",
    ...(sanitizeAuditNameList(row.removed_names).map((name) => `- ${name}`)),
  ];
  return lines.join("\n");
}

function normalizeFilterImportAuditQuickApplyTelemetryEntry(raw, idx = 0) {
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) return null;
  const scope = raw.scope && typeof raw.scope === "object" && !Array.isArray(raw.scope) ? raw.scope : {};
  return {
    id: String(raw.id || `fiq_${idx}`),
    timestamp_iso: String(raw.timestamp_iso || "-"),
    option_id: String(raw.option_id || "").slice(0, 48),
    restore_tag: String(raw.restore_tag || "").slice(0, 64),
    apply_ok: Boolean(raw.apply_ok),
    apply_reason: String(raw.apply_reason || "").slice(0, 160),
    schema_version: clampInteger(raw.schema_version, 0, 64, 0),
    scope: {
      query: Boolean(scope.query),
      paging: Boolean(scope.paging),
      pinned: Boolean(scope.pinned),
      entry: Boolean(scope.entry),
    },
    sync_enabled: Boolean(raw.sync_enabled),
    sync_applied: Boolean(raw.sync_applied),
    active_restore_preset_id: String(raw.active_restore_preset_id || "").slice(0, 48),
    active_query_preset_id: String(raw.active_query_preset_id || "").slice(0, 48),
    pinned_preset_id: String(raw.pinned_preset_id || "").slice(0, 48),
  };
}

function buildFilterImportAuditQuickApplyTelemetryBundle(entries) {
  const rows = Array.isArray(entries) ? entries : [];
  const normalized = rows
    .map((row, idx) => normalizeFilterImportAuditQuickApplyTelemetryEntry(row, idx))
    .filter(Boolean)
    .slice(0, FILTER_IMPORT_AUDIT_QUICK_TELEMETRY_LIMIT);
  return {
    schema_version: 1,
    kind: "graph_lab_contract_overlay_filter_import_quick_apply_telemetry",
    exported_at_iso: new Date().toISOString(),
    entry_count: normalized.length,
    entries: normalized,
  };
}

function serializeFilterImportAuditQuickApplyTelemetryBundle(entries) {
  return JSON.stringify(buildFilterImportAuditQuickApplyTelemetryBundle(entries), null, 2);
}

function buildFilterImportAuditQuickTelemetryDrilldownBundle(entries, options = {}) {
  const rows = Array.isArray(entries) ? entries : [];
  const normalized = rows
    .map((row, idx) => normalizeFilterImportAuditQuickApplyTelemetryEntry(row, idx))
    .filter(Boolean)
    .slice(0, FILTER_IMPORT_AUDIT_QUICK_TELEMETRY_LIMIT);
  const opt = options && typeof options === "object" && !Array.isArray(options) ? options : {};
  return {
    schema_version: 1,
    kind: "graph_lab_contract_overlay_filter_import_quick_apply_telemetry_drilldown",
    exported_at_iso: new Date().toISOString(),
    filter: {
      preset_id: String(opt.preset_id || ""),
      failure_only: Boolean(opt.failure_only),
      reason_query: String(opt.reason_query || "").slice(0, FILTER_IMPORT_AUDIT_QUICK_REASON_QUERY_MAX),
    },
    entry_count: normalized.length,
    entries: normalized,
  };
}

function serializeFilterImportAuditQuickTelemetryDrilldownBundle(entries, options = {}) {
  return JSON.stringify(buildFilterImportAuditQuickTelemetryDrilldownBundle(entries, options), null, 2);
}

function buildFilterPresetExportBundle(presets) {
  const rows = presets && typeof presets === "object" && !Array.isArray(presets) ? presets : {};
  const normalized = {};
  Object.keys(rows)
    .sort((a, b) => String(a).localeCompare(String(b)))
    .forEach((name) => {
      const pname = normalizeFilterPresetName(name);
      if (!pname) return;
      normalized[pname] = normalizeFilterPresetConfig(rows[name], DEFAULT_FILTER_PRESETS.default);
    });
  return {
    schema_version: 1,
    kind: "graph_lab_contract_overlay_filter_presets",
    exported_at_iso: new Date().toISOString(),
    presets: normalized,
  };
}

function serializeFilterPresetExportBundle(presets) {
  return JSON.stringify(buildFilterPresetExportBundle(presets), null, 2);
}

function parseFilterPresetImportText(rawText) {
  const text = String(rawText || "").trim();
  if (!text) {
    throw new Error("empty import payload");
  }
  let parsed = null;
  try {
    parsed = JSON.parse(text);
  } catch (_) {
    throw new Error("invalid JSON");
  }
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new Error("import root must be object");
  }
  const candidate = parsed.presets && typeof parsed.presets === "object" && !Array.isArray(parsed.presets)
    ? parsed.presets
    : parsed;
  const imported = {};
  Object.keys(candidate).forEach((name) => {
    const rawPreset = candidate[name];
    if (!rawPreset || typeof rawPreset !== "object" || Array.isArray(rawPreset)) return;
    const pname = normalizeFilterPresetName(name);
    if (!pname) return;
    imported[pname] = normalizeFilterPresetConfig(rawPreset, DEFAULT_FILTER_PRESETS.default);
  });
  if (Object.keys(imported).length === 0) {
    throw new Error("no valid filter presets found");
  }
  return imported;
}

function buildShortcutProfileExportBundle(profiles) {
  const rows = profiles && typeof profiles === "object" && !Array.isArray(profiles) ? profiles : {};
  const normalized = {};
  Object.keys(rows)
    .sort((a, b) => String(a).localeCompare(String(b)))
    .forEach((name) => {
      const pname = normalizeShortcutProfileName(name);
      if (!pname) return;
      normalized[pname] = normalizeShortcutBindings(rows[name], DEFAULT_SHORTCUT_BINDINGS);
    });
  return {
    schema_version: 1,
    kind: "graph_lab_contract_overlay_shortcut_profiles",
    exported_at_iso: new Date().toISOString(),
    profiles: normalized,
  };
}

function serializeShortcutProfileExportBundle(profiles) {
  return JSON.stringify(buildShortcutProfileExportBundle(profiles), null, 2);
}

function parseShortcutProfileImportText(rawText) {
  const text = String(rawText || "").trim();
  if (!text) {
    throw new Error("empty import payload");
  }
  let parsed = null;
  try {
    parsed = JSON.parse(text);
  } catch (_) {
    throw new Error("invalid JSON");
  }
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new Error("import root must be object");
  }
  const candidate = parsed.profiles && typeof parsed.profiles === "object" && !Array.isArray(parsed.profiles)
    ? parsed.profiles
    : parsed;
  const imported = {};
  Object.keys(candidate).forEach((name) => {
    const rawProfile = candidate[name];
    if (!rawProfile || typeof rawProfile !== "object" || Array.isArray(rawProfile)) return;
    const pname = normalizeShortcutProfileName(name);
    if (!pname) return;
    imported[pname] = normalizeShortcutBindings(rawProfile, DEFAULT_SHORTCUT_BINDINGS);
  });
  if (Object.keys(imported).length === 0) {
    throw new Error("no valid shortcut profiles found");
  }
  return imported;
}

function buildQuickTelemetryDrilldownProfileExportBundle(profiles) {
  const rows = profiles && typeof profiles === "object" && !Array.isArray(profiles) ? profiles : {};
  const normalized = {};
  Object.keys(rows)
    .sort((a, b) => String(a).localeCompare(String(b)))
    .forEach((name) => {
      const pname = normalizeQuickTelemetryDrilldownProfileName(name);
      if (!pname) return;
      const fallback = DEFAULT_FILTER_IMPORT_AUDIT_QUICK_TELEMETRY_DRILLDOWN_PROFILES[pname]
        || DEFAULT_FILTER_IMPORT_AUDIT_QUICK_TELEMETRY_DRILLDOWN_PROFILES.default;
      normalized[pname] = normalizeQuickTelemetryDrilldownProfile(rows[name], fallback);
    });
  return {
    schema_version: 1,
    kind: "graph_lab_contract_overlay_quick_telemetry_drilldown_profiles",
    exported_at_iso: new Date().toISOString(),
    profiles: normalized,
  };
}

function serializeQuickTelemetryDrilldownProfileExportBundle(profiles) {
  return JSON.stringify(buildQuickTelemetryDrilldownProfileExportBundle(profiles), null, 2);
}

function parseQuickTelemetryDrilldownProfileImportText(rawText) {
  const text = String(rawText || "").trim();
  if (!text) {
    throw new Error("empty import payload");
  }
  let parsed = null;
  try {
    parsed = JSON.parse(text);
  } catch (_) {
    throw new Error("invalid JSON");
  }
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new Error("import root must be object");
  }
  const candidate = parsed.profiles && typeof parsed.profiles === "object" && !Array.isArray(parsed.profiles)
    ? parsed.profiles
    : parsed;
  const imported = {};
  Object.keys(candidate).forEach((name) => {
    const rawProfile = candidate[name];
    if (!rawProfile || typeof rawProfile !== "object" || Array.isArray(rawProfile)) return;
    const pname = normalizeQuickTelemetryDrilldownProfileName(name);
    if (!pname) return;
    const fallback = DEFAULT_FILTER_IMPORT_AUDIT_QUICK_TELEMETRY_DRILLDOWN_PROFILES[pname]
      || DEFAULT_FILTER_IMPORT_AUDIT_QUICK_TELEMETRY_DRILLDOWN_PROFILES.default;
    imported[pname] = normalizeQuickTelemetryDrilldownProfile(rawProfile, fallback);
  });
  if (Object.keys(imported).length === 0) {
    throw new Error("no valid drilldown profiles found");
  }
  return imported;
}

function buildQuickTelemetryDrilldownImportFilterBundle(rawBundle) {
  const src = rawBundle && typeof rawBundle === "object" && !Array.isArray(rawBundle)
    ? rawBundle
    : {};
  const rowCapRaw = clampInteger(src.row_cap, 4, 200, 16);
  const rowCap = QUICK_TELEMETRY_DRILLDOWN_IMPORT_ROW_CAP_OPTIONS.includes(String(rowCapRaw))
    ? rowCapRaw
    : Number(CONTRACT_OVERLAY_DEFAULT_PREFS.quickTelemetryDrilldownImportRowCap || 16);
  const presetId = String(src.preset_id || "custom").trim() || "custom";
  return {
    schema_version: QUICK_TELEMETRY_DRILLDOWN_IMPORT_FILTER_BUNDLE_SCHEMA_VERSION,
    kind: QUICK_TELEMETRY_DRILLDOWN_IMPORT_FILTER_BUNDLE_KIND,
    exported_at_iso: new Date().toISOString(),
    filter_bundle: {
      preset_id: presetId,
      conflict_only: Boolean(src.conflict_only),
      conflict_filter: normalizeQuickTelemetryDrilldownImportConflictFilter(src.conflict_filter || "all"),
      name_query: String(src.name_query || "").slice(0, QUICK_TELEMETRY_DRILLDOWN_IMPORT_NAME_QUERY_MAX),
      row_cap: rowCap,
    },
  };
}

function serializeQuickTelemetryDrilldownImportFilterBundle(rawBundle) {
  return JSON.stringify(buildQuickTelemetryDrilldownImportFilterBundle(rawBundle), null, 2);
}

function parseQuickTelemetryDrilldownImportFilterBundleText(rawText, opts = null) {
  const text = String(rawText || "").trim();
  if (!text) {
    throw new Error("empty import payload");
  }
  const options = opts && typeof opts === "object" && !Array.isArray(opts) ? opts : {};
  const mode = normalizeQuickTelemetryDrilldownImportFilterBundleMode(options.mode || "compat");
  let parsed = null;
  try {
    parsed = JSON.parse(text);
  } catch (_) {
    throw new Error("invalid JSON");
  }
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new Error("import root must be object");
  }
  const hasFilterBundleWrapper = Boolean(
    parsed.filter_bundle
    && typeof parsed.filter_bundle === "object"
    && !Array.isArray(parsed.filter_bundle)
  );
  const parsedKind = String(parsed.kind || "").trim();
  const parsedSchemaVersion = Number(parsed.schema_version || 0);
  if (mode === "strict") {
    if (!hasFilterBundleWrapper) {
      throw new Error("strict mode requires filter_bundle wrapper");
    }
    if (parsedKind !== QUICK_TELEMETRY_DRILLDOWN_IMPORT_FILTER_BUNDLE_KIND) {
      throw new Error(`strict mode requires kind=${QUICK_TELEMETRY_DRILLDOWN_IMPORT_FILTER_BUNDLE_KIND}`);
    }
    if (parsed.schema_version === undefined) {
      throw new Error(
        `strict mode requires schema_version=${QUICK_TELEMETRY_DRILLDOWN_IMPORT_FILTER_BUNDLE_SCHEMA_VERSION}`
      );
    }
  }
  if (parsedKind && parsedKind !== QUICK_TELEMETRY_DRILLDOWN_IMPORT_FILTER_BUNDLE_KIND) {
    throw new Error(`unexpected kind (expected ${QUICK_TELEMETRY_DRILLDOWN_IMPORT_FILTER_BUNDLE_KIND})`);
  }
  if (parsed.schema_version !== undefined && parsedSchemaVersion !== QUICK_TELEMETRY_DRILLDOWN_IMPORT_FILTER_BUNDLE_SCHEMA_VERSION) {
    throw new Error(`unsupported schema_version (expected ${QUICK_TELEMETRY_DRILLDOWN_IMPORT_FILTER_BUNDLE_SCHEMA_VERSION})`);
  }
  const candidate = hasFilterBundleWrapper ? parsed.filter_bundle : parsed;
  const rowCapRaw = clampInteger(candidate.row_cap, 4, 200, 16);
  const rowCap = QUICK_TELEMETRY_DRILLDOWN_IMPORT_ROW_CAP_OPTIONS.includes(String(rowCapRaw))
    ? rowCapRaw
    : Number(CONTRACT_OVERLAY_DEFAULT_PREFS.quickTelemetryDrilldownImportRowCap || 16);
  return {
    preset_id: String(candidate.preset_id || parsed.preset_id || "custom").trim() || "custom",
    conflict_only: Boolean(candidate.conflict_only),
    conflict_filter: normalizeQuickTelemetryDrilldownImportConflictFilter(candidate.conflict_filter || "all"),
    name_query: String(candidate.name_query || "").slice(0, QUICK_TELEMETRY_DRILLDOWN_IMPORT_NAME_QUERY_MAX),
    row_cap: rowCap,
    kind: parsedKind || QUICK_TELEMETRY_DRILLDOWN_IMPORT_FILTER_BUNDLE_KIND,
    schema_version: parsedSchemaVersion || QUICK_TELEMETRY_DRILLDOWN_IMPORT_FILTER_BUNDLE_SCHEMA_VERSION,
    has_wrapper: hasFilterBundleWrapper,
    import_mode: mode,
  };
}

function buildQuickTelemetryDrilldownImportFilterBundleStrictWrapCandidate(rawText) {
  const text = String(rawText || "").trim();
  if (!text) {
    return { available: false, reason: "empty", wrapped_text: "" };
  }
  let parsed = null;
  try {
    parsed = JSON.parse(text);
  } catch (_) {
    return { available: false, reason: "invalid_json", wrapped_text: "" };
  }
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    return { available: false, reason: "import_root_not_object", wrapped_text: "" };
  }
  const hasFilterBundleWrapper = Boolean(
    parsed.filter_bundle
    && typeof parsed.filter_bundle === "object"
    && !Array.isArray(parsed.filter_bundle)
  );
  if (hasFilterBundleWrapper) {
    return { available: false, reason: "already_wrapped", wrapped_text: "" };
  }
  const wrapped = buildQuickTelemetryDrilldownImportFilterBundle(parsed);
  return {
    available: true,
    reason: "legacy_payload_detected",
    wrapped_payload: wrapped,
    wrapped_text: JSON.stringify(wrapped, null, 2),
  };
}

function isEditableElementTarget(target) {
  const t = target && typeof target === "object" ? target : null;
  if (!t) return false;
  if (Boolean(t.isContentEditable)) return true;
  const tag = String(t.tagName || "").toLowerCase();
  return tag === "input" || tag === "textarea" || tag === "select";
}

function normalizeShape(rawShape) {
  if (!Array.isArray(rawShape)) return [];
  return rawShape
    .map((x) => Number(x))
    .filter((x) => Number.isFinite(x) && x >= 0)
    .map((x) => Math.floor(x));
}

function normalizePeakList(rawPeaks, rowKey, colKey) {
  const rows = Array.isArray(rawPeaks) ? rawPeaks : [];
  return rows
    .map((peak, idx) => {
      const row = Number(peak?.[rowKey]);
      const col = Number(peak?.[colKey]);
      if (!Number.isFinite(row) || !Number.isFinite(col)) return null;
      return {
        index: Number(idx),
        row: Math.floor(row),
        col: Math.floor(col),
        power: Number(peak?.power || 0),
        relDb: Number(peak?.rel_db || 0),
      };
    })
    .filter(Boolean);
}

function clampBin(value, maxSize) {
  const maxIdx = Math.max(0, Number(maxSize || 0) - 1);
  const raw = Number(value);
  const candidate = Number.isFinite(raw) ? Math.floor(raw) : 0;
  return Math.max(0, Math.min(maxIdx, candidate));
}

function parseBinText(rawText, fallback) {
  const raw = Number(rawText);
  if (!Number.isFinite(raw)) return Number(fallback || 0);
  return Math.floor(raw);
}

function safeShapeLabel(shape) {
  return Array.isArray(shape) && shape.length > 0 ? shape.join("x") : "-";
}

function computeProbe(peaks, rowBin, colBin, shape) {
  const rows = Number(shape?.[0] || 0);
  const cols = Number(shape?.[1] || 0);
  const hasBounds = rows > 0 && cols > 0;
  const clampedRow = hasBounds ? clampBin(rowBin, rows) : Math.max(0, Number(rowBin || 0));
  const clampedCol = hasBounds ? clampBin(colBin, cols) : Math.max(0, Number(colBin || 0));
  const exact = peaks.find((peak) => peak.row === clampedRow && peak.col === clampedCol) || null;
  let nearest = null;
  let nearestDist = Number.POSITIVE_INFINITY;
  peaks.forEach((peak) => {
    const dist = Math.abs(Number(peak.row) - clampedRow) + Math.abs(Number(peak.col) - clampedCol);
    if (dist < nearestDist) {
      nearestDist = dist;
      nearest = peak;
    }
  });
  return {
    row: clampedRow,
    col: clampedCol,
    hasBounds,
    exact,
    nearest,
    nearestDist: Number.isFinite(nearestDist) ? nearestDist : null,
    rowNorm: hasBounds ? clampedRow / Math.max(rows - 1, 1) : 0,
    colNorm: hasBounds ? clampedCol / Math.max(cols - 1, 1) : 0,
  };
}

function computeRunDiffOverlay(currentSummary, compareSummary) {
  const current = currentSummary && typeof currentSummary === "object" ? currentSummary : null;
  const baseline = compareSummary && typeof compareSummary === "object" ? compareSummary : null;
  if (!current || !baseline) return null;

  const currentAdcShape = normalizeShape(current?.adc_summary?.shape);
  const currentRdShape = normalizeShape(current?.radar_map_summary?.rd_shape);
  const currentRaShape = normalizeShape(current?.radar_map_summary?.ra_shape);
  const baselineAdcShape = normalizeShape(baseline?.adc_summary?.shape);
  const baselineRdShape = normalizeShape(baseline?.radar_map_summary?.rd_shape);
  const baselineRaShape = normalizeShape(baseline?.radar_map_summary?.ra_shape);

  const currentRdPeak = normalizePeakList(current?.quicklook?.rd_top_peaks, "doppler_bin", "range_bin")[0] || null;
  const baselineRdPeak = normalizePeakList(baseline?.quicklook?.rd_top_peaks, "doppler_bin", "range_bin")[0] || null;
  const currentRaPeak = normalizePeakList(current?.quicklook?.ra_top_peaks, "angle_bin", "range_bin")[0] || null;
  const baselineRaPeak = normalizePeakList(baseline?.quicklook?.ra_top_peaks, "angle_bin", "range_bin")[0] || null;

  const currentPathCount = Number(current?.path_summary?.path_count_total || 0);
  const baselinePathCount = Number(baseline?.path_summary?.path_count_total || 0);

  const toSigned = (value) => {
    const n = Number(value || 0);
    return `${n >= 0 ? "+" : ""}${n}`;
  };

  return {
    currentGraphRunId: String(current?.graph_run_id || "-"),
    compareGraphRunId: String(baseline?.graph_run_id || "-"),
    shapeEq: {
      adc: safeShapeLabel(currentAdcShape) === safeShapeLabel(baselineAdcShape),
      rd: safeShapeLabel(currentRdShape) === safeShapeLabel(baselineRdShape),
      ra: safeShapeLabel(currentRaShape) === safeShapeLabel(baselineRaShape),
    },
    shapeText: {
      adc: `${safeShapeLabel(currentAdcShape)} vs ${safeShapeLabel(baselineAdcShape)}`,
      rd: `${safeShapeLabel(currentRdShape)} vs ${safeShapeLabel(baselineRdShape)}`,
      ra: `${safeShapeLabel(currentRaShape)} vs ${safeShapeLabel(baselineRaShape)}`,
    },
    pathCountDelta: currentPathCount - baselinePathCount,
    rdPeakDelta: currentRdPeak && baselineRdPeak ? {
      rangeBinDelta: Number(currentRdPeak.col || 0) - Number(baselineRdPeak.col || 0),
      dopplerBinDelta: Number(currentRdPeak.row || 0) - Number(baselineRdPeak.row || 0),
      relDbDelta: Number(currentRdPeak.relDb || 0) - Number(baselineRdPeak.relDb || 0),
    } : null,
    raPeakDelta: currentRaPeak && baselineRaPeak ? {
      rangeBinDelta: Number(currentRaPeak.col || 0) - Number(baselineRaPeak.col || 0),
      angleBinDelta: Number(currentRaPeak.row || 0) - Number(baselineRaPeak.row || 0),
      relDbDelta: Number(currentRaPeak.relDb || 0) - Number(baselineRaPeak.relDb || 0),
    } : null,
    toSigned,
  };
}

function ArtifactInspector({ graphRunSummary, compareGraphRunSummary, compareRunStatusText }) {
  if (!graphRunSummary) {
    return h("pre", { className: "result-box", key: "aibox_empty" }, "run graph first to inspect artifacts");
  }

  const runtimeContract = graphRunSummary?.runtime_contract_diagnostics || null;
  const rdShape = normalizeShape(
    graphRunSummary?.radar_map_summary?.rd_shape || graphRunSummary?.quicklook?.rd_shape
  );
  const raShape = normalizeShape(
    graphRunSummary?.radar_map_summary?.ra_shape || graphRunSummary?.quicklook?.ra_shape
  );
  const rdPeaks = normalizePeakList(graphRunSummary?.quicklook?.rd_top_peaks, "doppler_bin", "range_bin");
  const raPeaks = normalizePeakList(graphRunSummary?.quicklook?.ra_top_peaks, "angle_bin", "range_bin");

  const [rdRangeBinText, setRdRangeBinText] = React.useState("0");
  const [rdDopplerBinText, setRdDopplerBinText] = React.useState("0");
  const [raRangeBinText, setRaRangeBinText] = React.useState("0");
  const [raAngleBinText, setRaAngleBinText] = React.useState("0");
  const [rdPeakSelectText, setRdPeakSelectText] = React.useState("-1");
  const [raPeakSelectText, setRaPeakSelectText] = React.useState("-1");
  const [rdPeakLock, setRdPeakLock] = React.useState(false);
  const [raPeakLock, setRaPeakLock] = React.useState(false);

  React.useEffect(() => {
    const primaryRd = rdPeaks[0] || null;
    const primaryRa = raPeaks[0] || null;
    setRdRangeBinText(String(primaryRd ? primaryRd.col : 0));
    setRdDopplerBinText(String(primaryRd ? primaryRd.row : 0));
    setRaRangeBinText(String(primaryRa ? primaryRa.col : 0));
    setRaAngleBinText(String(primaryRa ? primaryRa.row : 0));
    setRdPeakSelectText(primaryRd ? "0" : "-1");
    setRaPeakSelectText(primaryRa ? "0" : "-1");
    setRdPeakLock(false);
    setRaPeakLock(false);
  }, [graphRunSummary, rdPeaks, raPeaks]);

  React.useEffect(() => {
    if (!rdPeakLock) return;
    const idx = Number(rdPeakSelectText);
    const peak = Number.isFinite(idx) && idx >= 0 ? rdPeaks[Math.floor(idx)] : null;
    if (!peak) return;
    setRdRangeBinText(String(peak.col));
    setRdDopplerBinText(String(peak.row));
  }, [rdPeakLock, rdPeakSelectText, rdPeaks]);

  React.useEffect(() => {
    if (!raPeakLock) return;
    const idx = Number(raPeakSelectText);
    const peak = Number.isFinite(idx) && idx >= 0 ? raPeaks[Math.floor(idx)] : null;
    if (!peak) return;
    setRaRangeBinText(String(peak.col));
    setRaAngleBinText(String(peak.row));
  }, [raPeakLock, raPeakSelectText, raPeaks]);

  const rdProbe = React.useMemo(() => {
    const rangeBin = parseBinText(rdRangeBinText, 0);
    const dopplerBin = parseBinText(rdDopplerBinText, 0);
    return computeProbe(rdPeaks, dopplerBin, rangeBin, rdShape);
  }, [rdDopplerBinText, rdPeaks, rdRangeBinText, rdShape]);

  const raProbe = React.useMemo(() => {
    const rangeBin = parseBinText(raRangeBinText, 0);
    const angleBin = parseBinText(raAngleBinText, 0);
    return computeProbe(raPeaks, angleBin, rangeBin, raShape);
  }, [raAngleBinText, raPeaks, raRangeBinText, raShape]);

  const runDiff = React.useMemo(
    () => computeRunDiffOverlay(graphRunSummary, compareGraphRunSummary),
    [compareGraphRunSummary, graphRunSummary]
  );

  const renderProbeSummary = (probe) => {
    const exact = probe.exact;
    const nearest = probe.nearest;
    const nearestPart = nearest
      ? `nearest_peak=#${nearest.index} d=${Number(probe.nearestDist)} rel_db=${Number(nearest.relDb).toFixed(2)}`
      : "nearest_peak=none";
    const exactPart = exact
      ? `exact_peak=#${exact.index} rel_db=${Number(exact.relDb).toFixed(2)}`
      : "exact_peak=none";
    return [
      `${exactPart} | ${nearestPart}`,
      `cursor_norm=(${Number(probe.rowNorm).toFixed(3)}, ${Number(probe.colNorm).toFixed(3)})`,
    ];
  };

  return h("div", { className: "result-box", key: "aibox" }, [
    h("div", { key: "kpi", style: { marginBottom: "8px" } }, [
      `paths=${Number(graphRunSummary?.path_summary?.path_count_total || 0)} | `,
      `adc_shape=${Array.isArray(graphRunSummary?.adc_summary?.shape) ? graphRunSummary.adc_summary.shape.join("x") : "-"} | `,
      `rd=${Array.isArray(graphRunSummary?.radar_map_summary?.rd_shape) ? graphRunSummary.radar_map_summary.rd_shape.join("x") : "-"} | `,
      `ra=${Array.isArray(graphRunSummary?.radar_map_summary?.ra_shape) ? graphRunSummary.radar_map_summary.ra_shape.join("x") : "-"}`,
    ]),
    runtimeContract
      ? h("div", { key: "contract_runtime", style: { marginBottom: "8px", color: "#8fb3c9" } }, [
          `contract_delta(unique/attempt): ${formatSigned(runtimeContract?.delta?.unique_warning_count)}/${formatSigned(runtimeContract?.delta?.attempt_count_total)} | `,
          `contract_total(unique/attempt): ${Number(runtimeContract?.snapshot?.unique_warning_count || 0)}/${Number(runtimeContract?.snapshot?.attempt_count_total || 0)}`,
        ])
      : null,
    h("div", { key: "diff_overlay", style: { marginBottom: "8px", padding: "8px", border: "1px solid #284a5d", borderRadius: "6px", background: "rgba(9, 22, 30, 0.62)" } }, [
      h("div", { key: "diff_title", style: { marginBottom: "5px", color: "#8fb3c9" } }, "run-to-run diff overlay:"),
      runDiff
        ? h("div", { key: "diff_body", style: { display: "flex", flexDirection: "column", gap: "3px" } }, [
            h("div", { key: "diff_hdr" }, `current=${runDiff.currentGraphRunId} | compare=${runDiff.compareGraphRunId}`),
            h("div", { key: "diff_shape_adc" }, `shape.adc: ${runDiff.shapeText.adc} | eq=${runDiff.shapeEq.adc}`),
            h("div", { key: "diff_shape_rd" }, `shape.rd: ${runDiff.shapeText.rd} | eq=${runDiff.shapeEq.rd}`),
            h("div", { key: "diff_shape_ra" }, `shape.ra: ${runDiff.shapeText.ra} | eq=${runDiff.shapeEq.ra}`),
            h("div", { key: "diff_paths" }, `path_count_delta: ${runDiff.toSigned(runDiff.pathCountDelta)}`),
            h(
              "div",
              { key: "diff_rd" },
              runDiff.rdPeakDelta
                ? `rd_peak_delta(range/doppler/rel_db): ${runDiff.toSigned(runDiff.rdPeakDelta.rangeBinDelta)}/${runDiff.toSigned(runDiff.rdPeakDelta.dopplerBinDelta)}/${runDiff.rdPeakDelta.relDbDelta.toFixed(2)}`
                : "rd_peak_delta: unavailable"
            ),
            h(
              "div",
              { key: "diff_ra" },
              runDiff.raPeakDelta
                ? `ra_peak_delta(range/angle/rel_db): ${runDiff.toSigned(runDiff.raPeakDelta.rangeBinDelta)}/${runDiff.toSigned(runDiff.raPeakDelta.angleBinDelta)}/${runDiff.raPeakDelta.relDbDelta.toFixed(2)}`
                : "ra_peak_delta: unavailable"
            ),
          ])
        : h("div", { key: "diff_empty", style: { color: "#86a1b4" } }, String(compareRunStatusText || "compare run not loaded")),
    ]),
    h("div", { key: "probe", style: { marginBottom: "8px", padding: "8px", border: "1px solid #284a5d", borderRadius: "6px", background: "rgba(9, 22, 30, 0.62)" } }, [
      h("div", { key: "probe_title", style: { marginBottom: "6px", color: "#8fb3c9" } }, "cursor probe + peak lock:"),
      h("div", { key: "probe_grid", style: { display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: "8px" } }, [
        h("div", { key: "probe_rd", style: { border: "1px solid #264758", borderRadius: "6px", padding: "6px" } }, [
          h("div", { key: "probe_rd_title", style: { marginBottom: "4px", color: "#9fc1d4" } }, `RD probe (shape=${safeShapeLabel(rdShape)})`),
          h("div", { key: "probe_rd_inputs", style: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: "6px", marginBottom: "6px" } }, [
            h("input", {
              key: "rd_range_bin",
              className: "input",
              value: rdRangeBinText,
              onChange: (e) => setRdRangeBinText(String(e.target.value || "0")),
              placeholder: "range_bin",
            }),
            h("input", {
              key: "rd_doppler_bin",
              className: "input",
              value: rdDopplerBinText,
              onChange: (e) => setRdDopplerBinText(String(e.target.value || "0")),
              placeholder: "doppler_bin",
            }),
          ]),
          h("div", { key: "probe_rd_peakctl", style: { display: "grid", gridTemplateColumns: "1fr auto", gap: "6px", marginBottom: "6px" } }, [
            h("select", {
              key: "rd_peak_select",
              className: "select",
              value: rdPeakSelectText,
              onChange: (e) => setRdPeakSelectText(String(e.target.value || "-1")),
            }, [
              h("option", { key: "rd_peak_none", value: "-1" }, "RD peak: none"),
              ...rdPeaks.map((peak) =>
                h(
                  "option",
                  { key: `rd_peak_${peak.index}`, value: String(peak.index) },
                  `#${peak.index} d=${peak.row} r=${peak.col} rel=${Number(peak.relDb).toFixed(2)}`
                )
              ),
            ]),
            h("button", {
              key: "rd_snap",
              className: "btn",
              onClick: () => {
                const idx = Number(rdPeakSelectText);
                const peak = Number.isFinite(idx) && idx >= 0 ? rdPeaks[Math.floor(idx)] : null;
                if (!peak) return;
                setRdRangeBinText(String(peak.col));
                setRdDopplerBinText(String(peak.row));
              },
            }, "Snap"),
          ]),
          h("label", { key: "rd_lock_lbl", style: { display: "inline-flex", alignItems: "center", gap: "6px", color: "#8fb3c9" } }, [
            h("input", {
              key: "rd_lock_chk",
              type: "checkbox",
              checked: Boolean(rdPeakLock),
              onChange: (e) => setRdPeakLock(Boolean(e.target.checked)),
            }),
            "Peak lock",
          ]),
          ...renderProbeSummary(rdProbe).map((line, idx) =>
            h("div", { key: `rd_probe_line_${idx}`, style: { marginTop: idx === 0 ? "6px" : "2px", color: "#b9d5e7" } }, line)
          ),
        ]),
        h("div", { key: "probe_ra", style: { border: "1px solid #264758", borderRadius: "6px", padding: "6px" } }, [
          h("div", { key: "probe_ra_title", style: { marginBottom: "4px", color: "#9fc1d4" } }, `RA probe (shape=${safeShapeLabel(raShape)})`),
          h("div", { key: "probe_ra_inputs", style: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: "6px", marginBottom: "6px" } }, [
            h("input", {
              key: "ra_range_bin",
              className: "input",
              value: raRangeBinText,
              onChange: (e) => setRaRangeBinText(String(e.target.value || "0")),
              placeholder: "range_bin",
            }),
            h("input", {
              key: "ra_angle_bin",
              className: "input",
              value: raAngleBinText,
              onChange: (e) => setRaAngleBinText(String(e.target.value || "0")),
              placeholder: "angle_bin",
            }),
          ]),
          h("div", { key: "probe_ra_peakctl", style: { display: "grid", gridTemplateColumns: "1fr auto", gap: "6px", marginBottom: "6px" } }, [
            h("select", {
              key: "ra_peak_select",
              className: "select",
              value: raPeakSelectText,
              onChange: (e) => setRaPeakSelectText(String(e.target.value || "-1")),
            }, [
              h("option", { key: "ra_peak_none", value: "-1" }, "RA peak: none"),
              ...raPeaks.map((peak) =>
                h(
                  "option",
                  { key: `ra_peak_${peak.index}`, value: String(peak.index) },
                  `#${peak.index} a=${peak.row} r=${peak.col} rel=${Number(peak.relDb).toFixed(2)}`
                )
              ),
            ]),
            h("button", {
              key: "ra_snap",
              className: "btn",
              onClick: () => {
                const idx = Number(raPeakSelectText);
                const peak = Number.isFinite(idx) && idx >= 0 ? raPeaks[Math.floor(idx)] : null;
                if (!peak) return;
                setRaRangeBinText(String(peak.col));
                setRaAngleBinText(String(peak.row));
              },
            }, "Snap"),
          ]),
          h("label", { key: "ra_lock_lbl", style: { display: "inline-flex", alignItems: "center", gap: "6px", color: "#8fb3c9" } }, [
            h("input", {
              key: "ra_lock_chk",
              type: "checkbox",
              checked: Boolean(raPeakLock),
              onChange: (e) => setRaPeakLock(Boolean(e.target.checked)),
            }),
            "Peak lock",
          ]),
          ...renderProbeSummary(raProbe).map((line, idx) =>
            h("div", { key: `ra_probe_line_${idx}`, style: { marginTop: idx === 0 ? "6px" : "2px", color: "#b9d5e7" } }, line)
          ),
        ]),
      ]),
    ]),
    h("div", { key: "links", style: { marginBottom: "8px" } }, [
      h("div", { key: "lt" }, "artifacts:"),
      ...[
        ["path_list_json", graphRunSummary?.outputs?.path_list_json],
        ["adc_cube_npz", graphRunSummary?.outputs?.adc_cube_npz],
        ["radar_map_npz", graphRunSummary?.outputs?.radar_map_npz],
        ["graph_run_summary_json", graphRunSummary?.outputs?.graph_run_summary_json],
      ].map(([name, rawPath]) => {
        const href = normalizeRepoPath(String(rawPath || ""));
        if (!href) {
          return h("div", { key: `m_${name}` }, `- ${name}: -`);
        }
        return h("div", { key: `l_${name}` }, [
          `- ${name}: `,
          h(
            "a",
            {
              href,
              target: "_blank",
              rel: "noopener noreferrer",
              style: { color: "#7ed9ff", textDecoration: "underline" },
            },
            "open"
          ),
        ]);
      }),
    ]),
    h("div", { key: "trace", style: { marginBottom: "8px" } }, [
      h("div", { key: "tt" }, "node trace:"),
      ...((Array.isArray(graphRunSummary?.execution?.node_results)
        ? graphRunSummary.execution.node_results
        : []
      ).slice(0, 24).map((row, idx) => {
        const artifactMap = row?.artifacts && typeof row.artifacts === "object" ? row.artifacts : {};
        const artifactCount = Object.keys(artifactMap).length;
        const isCacheHit = Boolean(row?.cache_hit) || String(row?.status || "").toLowerCase() === "cached";
        const artifactBadge = artifactCount <= 0 ? "n/a" : (isCacheHit ? "cache-hit" : "recomputed");
        const badgeStyle = artifactBadge === "cache-hit"
          ? { border: "1px solid #2f6f57", color: "#7ee3b8", background: "rgba(53, 200, 133, 0.1)" }
          : artifactBadge === "recomputed"
            ? { border: "1px solid #8a6a2d", color: "#f4c265", background: "rgba(240, 179, 58, 0.1)" }
            : { border: "1px solid #36586d", color: "#8eb6ca", background: "rgba(58, 103, 129, 0.1)" };
        const sourceRun = String(row?.cache_source_graph_run_id || "").trim();
        return h("div", { key: `tr_${idx}` }, [
          `- #${Number(idx)} ${String(row?.node_type || "-")} (${String(row?.node_id || "-")}) | status=${String(row?.status || "-")} | contract=${String(row?.output_contract || "-")} | artifact=`,
          h(
            "span",
            {
              style: {
                display: "inline-flex",
                alignItems: "center",
                borderRadius: "999px",
                padding: "1px 7px",
                fontSize: "10px",
                marginLeft: "5px",
                ...badgeStyle,
              },
            },
            artifactBadge
          ),
          sourceRun && isCacheHit ? ` | source=${sourceRun}` : "",
        ]);
      })),
    ]),
    h("div", { key: "visTitle", style: { marginBottom: "4px" } }, "visuals:"),
    h(
      "div",
      {
        key: "visGrid",
        style: {
          display: "grid",
          gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
          gap: "8px",
        },
      },
      [
        ["rd_map_png", graphRunSummary?.visuals?.rd_map_png],
        ["ra_map_png", graphRunSummary?.visuals?.ra_map_png],
        ["adc_tx0_rx0_png", graphRunSummary?.visuals?.adc_tx0_rx0_png],
        ["path_scatter_chirp0_png", graphRunSummary?.visuals?.path_scatter_chirp0_png],
      ]
        .map(([name, rawPath]) => {
          const src = normalizeRepoPath(String(rawPath || ""));
          if (!src) return null;
          return h(
            "div",
            { key: `v_${name}`, style: { border: "1px solid #284a5d", borderRadius: "6px", padding: "4px" } },
            [
              h("div", { key: `vt_${name}`, style: { fontSize: "10px", marginBottom: "4px", color: "#8fb3c9" } }, name),
              h("img", {
                key: `img_${name}`,
                src,
                alt: String(name),
                style: { width: "100%", height: "92px", objectFit: "cover", borderRadius: "4px" },
              }),
            ]
          );
        })
        .filter(Boolean)
    ),
  ]);
}

export function TopBar({
  statusTone,
  statusText,
  nodeCount,
  edgeCount,
  runtimeBackendType,
  runtimeMode,
  runtimeLicenseTier,
  runtimeLicenseSet,
  layoutMode,
  setLayoutMode,
  densityMode,
  setDensityMode,
  pipelineStages,
  focusLeftOpen,
  focusRightOpen,
  onToggleFocusLeft,
  onToggleFocusRight,
}) {
  const backendLabel = String(runtimeBackendType || "unknown");
  const modeLabel = String(runtimeMode || "-");
  const tierLabel = String(runtimeLicenseTier || "trial");
  const safeLayoutMode = String(layoutMode || "triad");
  const safeDensityMode = String(densityMode || "comfortable");
  const safePipeline = Array.isArray(pipelineStages) && pipelineStages.length > 0
    ? pipelineStages
    : [
      { id: "design", label: "Design", done: false, active: true },
      { id: "run", label: "Run", done: false, active: false },
      { id: "inspect", label: "Inspect", done: false, active: false },
      { id: "gate", label: "Gate", done: false, active: false },
      { id: "export", label: "Export", done: false, active: false },
    ];

  return h("header", { className: "topbar", key: "hd" }, [
    h("div", { className: "top-main", key: "tm" }, [
      h("div", { className: "brand", key: "b1" }, [
        h("span", { className: "brand-dot", key: "dot" }),
        h("div", { key: "txt" }, [
          h("div", { className: "brand-title", key: "t1" }, "Radar Graph Lab"),
          h("div", { className: "brand-sub", key: "t2" }, "Design -> Run -> Inspect -> Gate -> Export"),
        ]),
      ]),

      h(
        "div",
        { className: "top-pipeline", key: "pipeline" },
        safePipeline.flatMap((stage, idx) => {
          const id = String(stage?.id || `stage_${idx}`);
          const label = String(stage?.label || id);
          const done = Boolean(stage?.done);
          const active = Boolean(stage?.active);
          const step = h(
            "span",
            {
              className: `pipeline-step${done ? " done" : ""}${active ? " active" : ""}`,
              key: `pipe_step_${id}`,
            },
            [
              h("span", { className: "pipeline-index", key: `pipe_idx_${id}` }, `${idx + 1}`),
              h("span", { className: "pipeline-label", key: `pipe_lbl_${id}` }, label),
            ]
          );
          if (idx >= safePipeline.length - 1) {
            return [step];
          }
          return [
            step,
            h("span", { className: "pipeline-arrow", key: `pipe_arrow_${id}` }, "›"),
          ];
        })
      ),

      h("div", { className: "top-toolbar", key: "b2" }, [
        h("div", { className: "toolbar-group", key: "layout_group" }, [
          h("span", { className: "toolbar-label", key: "layout_label" }, "view"),
          ["triad", "build", "review", "focus"].map((mode) =>
            h("button", {
              type: "button",
              key: `layout_${mode}`,
              className: `toolbar-btn${safeLayoutMode === mode ? " active" : ""}`,
              onClick: () => (typeof setLayoutMode === "function" ? setLayoutMode(mode) : null),
            }, mode)
          ),
        ]),
        h("div", { className: "toolbar-group", key: "density_group" }, [
          h("span", { className: "toolbar-label", key: "density_label" }, "density"),
          ["comfortable", "compact"].map((mode) =>
            h("button", {
              type: "button",
              key: `density_${mode}`,
              className: `toolbar-btn${safeDensityMode === mode ? " active" : ""}`,
              onClick: () => (typeof setDensityMode === "function" ? setDensityMode(mode) : null),
            }, mode)
          ),
        ]),
        safeLayoutMode === "focus"
          ? h("div", { className: "toolbar-group", key: "focus_drawer_group" }, [
              h("span", { className: "toolbar-label", key: "focus_drawer_label" }, "drawers"),
              h("button", {
                type: "button",
                key: "focus_drawer_left",
                className: `toolbar-btn${focusLeftOpen ? " active" : ""}`,
                onClick: () => (typeof onToggleFocusLeft === "function" ? onToggleFocusLeft() : null),
              }, focusLeftOpen ? "inputs on" : "inputs"),
              h("button", {
                type: "button",
                key: "focus_drawer_right",
                className: `toolbar-btn${focusRightOpen ? " active" : ""}`,
                onClick: () => (typeof onToggleFocusRight === "function" ? onToggleFocusRight() : null),
              }, focusRightOpen ? "inspect on" : "inspect"),
            ])
          : null,
        h("div", { className: "top-actions", key: "actions" }, [
          h("span", { className: `stat ${statusTone}`, key: "s1" }, statusText),
          h("span", { className: "stat", key: "s2" }, `nodes ${nodeCount} / edges ${edgeCount}`),
          h("span", { className: "stat", key: "s3" }, `backend ${backendLabel}`),
          h("span", { className: "stat", key: "s4" }, `runtime ${modeLabel}`),
          h(
            "span",
            { className: `stat ${runtimeLicenseSet ? "status-ok" : "status-warn"}`, key: "s5" },
            `license ${tierLabel} ${runtimeLicenseSet ? "set" : "unset"}`
          ),
        ]),
      ]),
    ]),
  ]);
}

export function GraphInputsPanel({ model }) {
  const safeModel = normalizeGraphInputsPanelModel(model);
  const {
    values,
    setters,
    templateActions,
    graphActions,
    runActions,
    gateActions,
    contractActions,
  } = safeModel;
  const {
    apiBase,
    graphId,
    sceneJsonPath,
    baselineId,
    profile,
    runtimeBackendType,
    runtimeProviderSpec,
    runtimeRequiredModulesText,
    runtimeFailurePolicy,
    runtimeSimulationMode,
    runtimeMultiplexingMode,
    runtimeBpmPhaseCodeText,
    runtimeMultiplexingPlanJson,
    runtimeDevice,
    runtimeLicenseTier,
    runtimeLicenseFile,
    runtimeTxFfdFilesText,
    runtimeRxFfdFilesText,
    runtimeMitsubaEgoOriginText,
    runtimeMitsubaChirpIntervalText,
    runtimeMitsubaMinRangeText,
    runtimeMitsubaSpheresJson,
    runtimePoSbrRepoRoot,
    runtimePoSbrGeometryPath,
    runtimePoSbrChirpIntervalText,
    runtimePoSbrBouncesText,
    runtimePoSbrRaysPerLambdaText,
    runtimePoSbrAlphaDegText,
    runtimePoSbrPhiDegText,
    runtimePoSbrThetaDegText,
    runtimePoSbrRadialVelocityText,
    runtimePoSbrMinRangeText,
    runtimePoSbrMaterialTag,
    runtimePoSbrPathIdPrefix,
    runtimePoSbrComponentsJson,
    runtimeDiagnosticBadges,
    runtimeDiagnosticText,
    runtimeStatusLine,
    runMode,
    autoPollAsyncRun,
    pollIntervalMsText,
    pollStateText,
    pollingActive,
    templates,
    lastGraphRunId,
    contractDebugText,
    contractOverlayEnabled,
    contractTimelineCount,
  } = values;
  const {
    setApiBase,
    setGraphId,
    setSceneJsonPath,
    setBaselineId,
    setProfile,
    setRuntimeBackendType,
    setRuntimeProviderSpec,
    setRuntimeRequiredModulesText,
    setRuntimeFailurePolicy,
    setRuntimeSimulationMode,
    setRuntimeMultiplexingMode,
    setRuntimeBpmPhaseCodeText,
    setRuntimeMultiplexingPlanJson,
    setRuntimeDevice,
    setRuntimeLicenseTier,
    setRuntimeLicenseFile,
    setRuntimeTxFfdFilesText,
    setRuntimeRxFfdFilesText,
    setRuntimeMitsubaEgoOriginText,
    setRuntimeMitsubaChirpIntervalText,
    setRuntimeMitsubaMinRangeText,
    setRuntimeMitsubaSpheresJson,
    setRuntimePoSbrRepoRoot,
    setRuntimePoSbrGeometryPath,
    setRuntimePoSbrChirpIntervalText,
    setRuntimePoSbrBouncesText,
    setRuntimePoSbrRaysPerLambdaText,
    setRuntimePoSbrAlphaDegText,
    setRuntimePoSbrPhiDegText,
    setRuntimePoSbrThetaDegText,
    setRuntimePoSbrRadialVelocityText,
    setRuntimePoSbrMinRangeText,
    setRuntimePoSbrMaterialTag,
    setRuntimePoSbrPathIdPrefix,
    setRuntimePoSbrComponentsJson,
    setRunMode,
    setAutoPollAsyncRun,
    setPollIntervalMsText,
    setContractOverlayEnabled,
  } = setters;
  const {
    fetchTemplates,
    exportGraph,
    loadTemplateByIndex,
  } = templateActions;
  const {
    addNodeByType,
    runGraphValidation,
  } = graphActions;
  const {
    runGraphViaApi,
    retryLastGraphRun,
    cancelLastGraphRun,
    pollLastGraphRunOnce,
  } = runActions;
  const {
    pinBaselineFromGraphRun,
    runPolicyGateForGraphRun,
    exportGateReport,
  } = gateActions;
  const {
    refreshContractWarnings,
    resetContractWarnings,
    clearContractTimeline,
  } = contractActions;

  return h("section", { className: "panel panel-left", key: "left" }, [
    h("div", { className: "panel-hd", key: "lhd" }, "Graph Inputs"),
    h("div", { className: "panel-bd", key: "lbd" }, [
      h("div", { className: "field", key: "api" }, [
        h("label", { className: "label", key: "lbl" }, "API Base"),
        h("input", {
          className: "input",
          value: apiBase,
          onChange: (e) => setApiBase(e.target.value),
          placeholder: "http://127.0.0.1:8099",
        }),
      ]),
      h("div", { className: "btn-row", key: "btns0" }, [
        h("button", { className: "btn", onClick: fetchTemplates, key: "r1" }, "Refresh Templates"),
        h("button", { className: "btn", onClick: exportGraph, key: "r2" }, "Export Graph"),
      ]),
      h("div", { className: "field", key: "graphid" }, [
        h("label", { className: "label", key: "lbl1" }, "Graph ID"),
        h("input", {
          className: "input",
          value: graphId,
          onChange: (e) => setGraphId(e.target.value),
          placeholder: "graph_lab",
        }),
      ]),
      h("div", { className: "field", key: "scenepath" }, [
        h("label", { className: "label", key: "lbl1b" }, "Scene JSON Path"),
        h("input", {
          className: "input",
          value: sceneJsonPath,
          onChange: (e) => setSceneJsonPath(e.target.value),
          placeholder: "data/demo/.../scene.json",
        }),
      ]),
      h("div", { className: "field", key: "baselineid" }, [
        h("label", { className: "label", key: "lbl1c" }, "Baseline ID"),
        h("input", {
          className: "input",
          value: baselineId,
          onChange: (e) => setBaselineId(e.target.value),
          placeholder: "graph_lab_baseline",
        }),
      ]),
      h("div", { className: "field", key: "profile" }, [
        h("label", { className: "label", key: "lbl2" }, "Profile"),
        h("select", {
          className: "select",
          value: profile,
          onChange: (e) => setProfile(e.target.value),
        }, [
          h("option", { value: "fast_debug", key: "p1" }, "fast_debug"),
          h("option", { value: "balanced_dev", key: "p2" }, "balanced_dev"),
          h("option", { value: "fidelity_eval", key: "p3" }, "fidelity_eval"),
        ]),
      ]),
      h(RuntimeConfigSection, {
        key: "runtime_config_section",
        runtimeBackendType,
        setRuntimeBackendType,
        runtimeProviderSpec,
        setRuntimeProviderSpec,
        runtimeRequiredModulesText,
        setRuntimeRequiredModulesText,
        runtimeFailurePolicy,
        setRuntimeFailurePolicy,
        runtimeSimulationMode,
        setRuntimeSimulationMode,
        runtimeMultiplexingMode,
        setRuntimeMultiplexingMode,
        runtimeBpmPhaseCodeText,
        setRuntimeBpmPhaseCodeText,
        runtimeMultiplexingPlanJson,
        setRuntimeMultiplexingPlanJson,
        runtimeDevice,
        setRuntimeDevice,
        runtimeLicenseTier,
        setRuntimeLicenseTier,
        runtimeLicenseFile,
        setRuntimeLicenseFile,
        runtimeTxFfdFilesText,
        setRuntimeTxFfdFilesText,
        runtimeRxFfdFilesText,
        setRuntimeRxFfdFilesText,
        runtimeMitsubaEgoOriginText,
        setRuntimeMitsubaEgoOriginText,
        runtimeMitsubaChirpIntervalText,
        setRuntimeMitsubaChirpIntervalText,
        runtimeMitsubaMinRangeText,
        setRuntimeMitsubaMinRangeText,
        runtimeMitsubaSpheresJson,
        setRuntimeMitsubaSpheresJson,
        runtimePoSbrRepoRoot,
        setRuntimePoSbrRepoRoot,
        runtimePoSbrGeometryPath,
        setRuntimePoSbrGeometryPath,
        runtimePoSbrChirpIntervalText,
        setRuntimePoSbrChirpIntervalText,
        runtimePoSbrBouncesText,
        setRuntimePoSbrBouncesText,
        runtimePoSbrRaysPerLambdaText,
        setRuntimePoSbrRaysPerLambdaText,
        runtimePoSbrAlphaDegText,
        setRuntimePoSbrAlphaDegText,
        runtimePoSbrPhiDegText,
        setRuntimePoSbrPhiDegText,
        runtimePoSbrThetaDegText,
        setRuntimePoSbrThetaDegText,
        runtimePoSbrRadialVelocityText,
        setRuntimePoSbrRadialVelocityText,
        runtimePoSbrMinRangeText,
        setRuntimePoSbrMinRangeText,
        runtimePoSbrMaterialTag,
        setRuntimePoSbrMaterialTag,
        runtimePoSbrPathIdPrefix,
        setRuntimePoSbrPathIdPrefix,
        runtimePoSbrComponentsJson,
        setRuntimePoSbrComponentsJson,
        runtimeDiagnosticBadges,
        runtimeDiagnosticText,
        runtimeStatusLine,
      }),
      h("div", { className: "field", key: "runmode" }, [
        h("label", { className: "label", key: "lbl_runmode" }, "Run Mode"),
        h("select", {
          className: "select",
          value: runMode,
          onChange: (e) => setRunMode(String(e.target.value || "sync")),
        }, [
          h("option", { value: "sync", key: "rm_sync" }, "sync"),
          h("option", { value: "async", key: "rm_async" }, "async"),
        ]),
      ]),
      h("div", { className: "field", key: "pollcfg" }, [
        h("label", { className: "label", key: "lbl_pollcfg" }, "Async Poll Config"),
        h("div", { className: "btn-row", key: "pollcfg_row" }, [
          h("label", { key: "pollchk", style: { display: "inline-flex", alignItems: "center", gap: "6px", fontSize: "11px" } }, [
            h("input", {
              type: "checkbox",
              checked: Boolean(autoPollAsyncRun),
              onChange: (e) => setAutoPollAsyncRun(Boolean(e.target.checked)),
            }),
            "Auto Poll",
          ]),
          h("input", {
            className: "input",
            value: pollIntervalMsText,
            onChange: (e) => setPollIntervalMsText(e.target.value),
            placeholder: "400",
            style: { maxWidth: "110px" },
          }),
        ]),
      ]),
      h("div", { className: "hint", key: "pollstate" }, `poll_state: ${String(pollStateText || "-")} | polling_active: ${Boolean(pollingActive)}`),
      h("div", { className: "field", key: "tpl" }, [
        h("label", { className: "label", key: "lbl3" }, "Template"),
        h("div", { className: "btn-row", key: "btnrowtpl" }, [
          h("select", {
            className: "select",
            id: "templateSelect",
            defaultValue: "0",
            onChange: (e) => loadTemplateByIndex(Number(e.target.value)),
          }, (templates.length > 0 ? templates : [{ template_id: "none", title: "(none)" }]).map((t, i) =>
            h("option", { value: String(i), key: `tpl_${i}` }, `${t.template_id || i} | ${t.title || "-"}`)
          )),
          h("button", { className: "btn", onClick: () => loadTemplateByIndex(0), key: "tplbtn" }, "Load #1"),
        ]),
      ]),
      h("div", { className: "field", key: "nodepalette" }, [
        h("label", { className: "label", key: "lbl4" }, "Node Palette"),
        h("div", { className: "chip-list", key: "chips" }, NODE_TYPES.map((x) =>
          h("button", {
            key: `node_${x}`,
            className: "chip btn",
            onClick: () => addNodeByType(x),
            title: `Add ${x}`,
          }, x)
        )),
      ]),
      h("button", { className: "btn", onClick: runGraphValidation, key: "validate" }, "Validate Graph Contract"),
      h("button", { className: "btn", onClick: runGraphViaApi, key: "rungraph" }, "Run Graph (API)"),
      h("div", { className: "btn-row", key: "hardeningbtns" }, [
        h("button", { className: "btn", onClick: retryLastGraphRun, key: "retryrun" }, "Retry Last Run"),
        h("button", { className: "btn", onClick: cancelLastGraphRun, key: "cancelrun" }, "Cancel Last Run"),
        h("button", { className: "btn", onClick: pollLastGraphRunOnce, key: "pollrun" }, "Poll Last Run"),
      ]),
      h("div", { className: "hint", key: "lastrunhint" }, `last_graph_run_id: ${String(lastGraphRunId || "-")}`),
      h("div", { className: "hint", key: "decision_pane_hint" }, "Gate/session/export controls moved to Node Inspector -> Decision Pane."),
      h("div", { className: "field", key: "contractdbg" }, [
        h("label", { className: "label", key: "lblcd" }, "Contract Guard"),
        h("div", { className: "btn-row", key: "contractbtns" }, [
          h("button", { className: "btn", onClick: refreshContractWarnings, key: "cdr1" }, "Refresh Guard"),
          h("button", { className: "btn", onClick: resetContractWarnings, key: "cdr2" }, "Reset Guard"),
        ]),
        h("div", { className: "btn-row", key: "contractoverlay" }, [
          h("label", { key: "overlaychk", style: { display: "inline-flex", alignItems: "center", gap: "6px", fontSize: "11px", color: "#8fb3c9" } }, [
            h("input", {
              type: "checkbox",
              checked: Boolean(contractOverlayEnabled),
              onChange: (e) => setContractOverlayEnabled(Boolean(e.target.checked)),
            }),
            "Show Overlay",
          ]),
          h("button", { className: "btn", onClick: clearContractTimeline, key: "clearTimeline" }, "Clear Timeline"),
        ]),
        h("pre", { className: "result-box", key: "cdbox" }, String(contractDebugText || "-")),
        h("div", { className: "hint", key: "contracthint2" }, `contract_timeline_events: ${Number(contractTimelineCount || 0)}`),
      ]),
      h("div", { className: "hint", key: "hint" }, "Tip: connect nodes on canvas, then validate to check schema/profile/DAG constraints."),
    ]),
  ]);
}

export function ContractWarningOverlay({
  visible,
  timeline,
  onClose,
  onClear,
  onExport,
  onOpenRun,
  onOpenGateEvidence,
}) {
  if (!visible) return null;
  const rows = Array.isArray(timeline) ? timeline : [];
  const runOpenHandler = typeof onOpenRun === "function" ? onOpenRun : () => {};
  const gateOpenHandler = typeof onOpenGateEvidence === "function" ? onOpenGateEvidence : () => {};
  const initialPrefs = React.useMemo(() => loadContractOverlayPrefs(), []);
  const initialFilterPresets = React.useMemo(() => loadFilterPresets(), []);
  const initialActiveFilterPreset = React.useMemo(() => {
    const preferred = String(
      initialPrefs.activeFilterPreset || CONTRACT_OVERLAY_DEFAULT_PREFS.activeFilterPreset
    ).trim();
    if (preferred && initialFilterPresets[preferred]) return preferred;
    if (initialFilterPresets.default) return "default";
    const names = Object.keys(initialFilterPresets);
    return names.length > 0 ? String(names[0]) : "default";
  }, [initialFilterPresets, initialPrefs.activeFilterPreset]);
  const initialShortcutProfiles = React.useMemo(() => loadShortcutProfiles(), []);
  const initialActiveShortcutProfile = React.useMemo(() => {
    const preferred = String(
      initialPrefs.activeShortcutProfile || CONTRACT_OVERLAY_DEFAULT_PREFS.activeShortcutProfile
    ).trim();
    if (preferred && initialShortcutProfiles[preferred]) return preferred;
    if (initialShortcutProfiles.default) return "default";
    const names = Object.keys(initialShortcutProfiles);
    return names.length > 0 ? String(names[0]) : "default";
  }, [initialPrefs.activeShortcutProfile, initialShortcutProfiles]);
  const initialShortcutBindings = React.useMemo(() => {
    const profileBindings = initialShortcutProfiles[initialActiveShortcutProfile] || DEFAULT_SHORTCUT_BINDINGS;
    return normalizeShortcutBindings(initialPrefs.shortcutBindings, profileBindings);
  }, [initialActiveShortcutProfile, initialPrefs.shortcutBindings, initialShortcutProfiles]);
  const initialQuickTelemetryDrilldownProfiles = React.useMemo(() => loadQuickTelemetryDrilldownProfiles(), []);
  const initialActiveQuickTelemetryDrilldownProfile = React.useMemo(() => {
    const preferred = String(
      initialPrefs.activeQuickTelemetryDrilldownProfile
      || CONTRACT_OVERLAY_DEFAULT_PREFS.activeQuickTelemetryDrilldownProfile
    ).trim();
    if (preferred && initialQuickTelemetryDrilldownProfiles[preferred]) return preferred;
    if (initialQuickTelemetryDrilldownProfiles.default) return "default";
    const names = Object.keys(initialQuickTelemetryDrilldownProfiles);
    return names.length > 0 ? String(names[0]) : "default";
  }, [
    initialPrefs.activeQuickTelemetryDrilldownProfile,
    initialQuickTelemetryDrilldownProfiles,
  ]);
  const initialFilterImportHistory = React.useMemo(() => loadFilterImportHistoryState(), []);
  const initialFilterImportAuditPinnedPresetId = React.useMemo(() => {
    const pid = String(
      initialPrefs.filterImportAuditPinnedPreset || CONTRACT_OVERLAY_DEFAULT_PREFS.filterImportAuditPinnedPreset
    ).trim();
    if (!pid) return "";
    if (!FILTER_IMPORT_AUDIT_QUERY_PRESETS.some((row) => String(row?.id || "") === pid)) return "";
    return pid;
  }, [initialPrefs.filterImportAuditPinnedPreset]);
  const initialFilterImportAuditQueryPreset = React.useMemo(
    () => resolveFilterImportAuditQueryPreset(initialFilterImportAuditPinnedPresetId || "all"),
    [initialFilterImportAuditPinnedPresetId]
  );
  const [sourceFilter, setSourceFilter] = React.useState(
    String(initialPrefs.sourceFilter || CONTRACT_OVERLAY_DEFAULT_PREFS.sourceFilter)
  );
  const [severityFilter, setSeverityFilter] = React.useState(
    String(initialPrefs.severityFilter || CONTRACT_OVERLAY_DEFAULT_PREFS.severityFilter)
  );
  const [policyFilter, setPolicyFilter] = React.useState(
    String(initialPrefs.policyFilter || CONTRACT_OVERLAY_DEFAULT_PREFS.policyFilter)
  );
  const [pinnedRunId, setPinnedRunId] = React.useState(
    String(initialPrefs.pinnedRunId || CONTRACT_OVERLAY_DEFAULT_PREFS.pinnedRunId)
  );
  const [nonZeroOnly, setNonZeroOnly] = React.useState(
    Boolean(
      initialPrefs.nonZeroOnly !== undefined
        ? initialPrefs.nonZeroOnly
        : CONTRACT_OVERLAY_DEFAULT_PREFS.nonZeroOnly
    )
  );
  const [compactMode, setCompactMode] = React.useState(
    Boolean(
      initialPrefs.compactMode !== undefined
        ? initialPrefs.compactMode
        : CONTRACT_OVERLAY_DEFAULT_PREFS.compactMode
    )
  );
  const [gateHistoryLimit, setGateHistoryLimit] = React.useState(
    String(initialPrefs.gateHistoryLimit || CONTRACT_OVERLAY_DEFAULT_PREFS.gateHistoryLimit)
  );
  const [gateHistoryPages, setGateHistoryPages] = React.useState(
    String(initialPrefs.gateHistoryPages || CONTRACT_OVERLAY_DEFAULT_PREFS.gateHistoryPages)
  );
  const [rowWindowSizeText, setRowWindowSizeText] = React.useState(
    String(initialPrefs.rowWindowSize || CONTRACT_OVERLAY_DEFAULT_PREFS.rowWindowSize)
  );
  const [rowVolumeGuardBypass, setRowVolumeGuardBypass] = React.useState(
    Boolean(
      initialPrefs.rowVolumeGuardBypass !== undefined
        ? initialPrefs.rowVolumeGuardBypass
        : CONTRACT_OVERLAY_DEFAULT_PREFS.rowVolumeGuardBypass
    )
  );
  const [showShortcutHelp, setShowShortcutHelp] = React.useState(
    Boolean(
      initialPrefs.showShortcutHelp !== undefined
        ? initialPrefs.showShortcutHelp
        : CONTRACT_OVERLAY_DEFAULT_PREFS.showShortcutHelp
    )
  );
  const [filterPresets, setFilterPresets] = React.useState(() => initialFilterPresets);
  const [activeFilterPreset, setActiveFilterPreset] = React.useState(
    String(initialActiveFilterPreset || "default")
  );
  const [filterPresetDraft, setFilterPresetDraft] = React.useState(
    String(initialPrefs.filterPresetDraft || CONTRACT_OVERLAY_DEFAULT_PREFS.filterPresetDraft)
  );
  const [filterImportMode, setFilterImportMode] = React.useState(
    normalizeFilterImportMode(
      initialPrefs.filterImportMode || CONTRACT_OVERLAY_DEFAULT_PREFS.filterImportMode
    )
  );
  const [shortcutProfiles, setShortcutProfiles] = React.useState(() => initialShortcutProfiles);
  const [activeShortcutProfile, setActiveShortcutProfile] = React.useState(
    String(initialActiveShortcutProfile || "default")
  );
  const [shortcutProfileDraft, setShortcutProfileDraft] = React.useState(
    String(initialPrefs.shortcutProfileDraft || CONTRACT_OVERLAY_DEFAULT_PREFS.shortcutProfileDraft)
  );
  const [quickTelemetryDrilldownProfiles, setQuickTelemetryDrilldownProfiles] = React.useState(
    () => initialQuickTelemetryDrilldownProfiles
  );
  const [activeQuickTelemetryDrilldownProfile, setActiveQuickTelemetryDrilldownProfile] = React.useState(
    String(initialActiveQuickTelemetryDrilldownProfile || "default")
  );
  const [quickTelemetryDrilldownProfileDraft, setQuickTelemetryDrilldownProfileDraft] = React.useState(
    String(
      initialPrefs.quickTelemetryDrilldownProfileDraft
      || CONTRACT_OVERLAY_DEFAULT_PREFS.quickTelemetryDrilldownProfileDraft
    )
  );
  const [shortcutBindings, setShortcutBindings] = React.useState(() => initialShortcutBindings);
  const [detailFieldStates, setDetailFieldStates] = React.useState(() =>
    normalizeDetailFieldStates(
      initialPrefs.detailFieldStates,
      DEFAULT_DETAIL_FIELD_STATES
    )
  );
  const [filterTransferText, setFilterTransferText] = React.useState("");
  const [filterTransferStatus, setFilterTransferStatus] = React.useState("");
  const [filterImportSelection, setFilterImportSelection] = React.useState({});
  const [filterReplaceConfirmChecked, setFilterReplaceConfirmChecked] = React.useState(false);
  const [filterImportUndoStack, setFilterImportUndoStack] = React.useState(
    () => initialFilterImportHistory.undoStack
  );
  const [filterImportRedoStack, setFilterImportRedoStack] = React.useState(
    () => initialFilterImportHistory.redoStack
  );
  const [filterImportAuditTrail, setFilterImportAuditTrail] = React.useState(
    () => initialFilterImportHistory.auditTrail
  );
  const [activeFilterImportAuditId, setActiveFilterImportAuditId] = React.useState(
    () => String(initialFilterImportHistory.auditTrail[0]?.id || "")
  );
  const [filterImportAuditSearchText, setFilterImportAuditSearchText] = React.useState(
    () => String(initialFilterImportAuditQueryPreset.search || "")
  );
  const [filterImportAuditKindFilter, setFilterImportAuditKindFilter] = React.useState(
    () => String(initialFilterImportAuditQueryPreset.kind || "all")
  );
  const [filterImportAuditModeFilter, setFilterImportAuditModeFilter] = React.useState(
    () => String(initialFilterImportAuditQueryPreset.mode || "all")
  );
  const [filterImportAuditPinnedPresetId, setFilterImportAuditPinnedPresetId] = React.useState(
    () => String(initialFilterImportAuditPinnedPresetId || "")
  );
  const [filterImportAuditRestoreQueryChecked, setFilterImportAuditRestoreQueryChecked] = React.useState(
    Boolean(
      initialPrefs.filterImportAuditRestoreQuery !== undefined
        ? initialPrefs.filterImportAuditRestoreQuery
        : CONTRACT_OVERLAY_DEFAULT_PREFS.filterImportAuditRestoreQuery
    )
  );
  const [filterImportAuditRestorePagingChecked, setFilterImportAuditRestorePagingChecked] = React.useState(
    Boolean(
      initialPrefs.filterImportAuditRestorePaging !== undefined
        ? initialPrefs.filterImportAuditRestorePaging
        : CONTRACT_OVERLAY_DEFAULT_PREFS.filterImportAuditRestorePaging
    )
  );
  const [filterImportAuditRestorePinnedPresetChecked, setFilterImportAuditRestorePinnedPresetChecked] = React.useState(
    Boolean(
      initialPrefs.filterImportAuditRestorePinnedPreset !== undefined
        ? initialPrefs.filterImportAuditRestorePinnedPreset
        : CONTRACT_OVERLAY_DEFAULT_PREFS.filterImportAuditRestorePinnedPreset
    )
  );
  const [filterImportAuditRestoreActiveEntryChecked, setFilterImportAuditRestoreActiveEntryChecked] = React.useState(
    Boolean(
      initialPrefs.filterImportAuditRestoreActiveEntry !== undefined
        ? initialPrefs.filterImportAuditRestoreActiveEntry
        : CONTRACT_OVERLAY_DEFAULT_PREFS.filterImportAuditRestoreActiveEntry
    )
  );
  const [filterImportAuditQuickApplySyncRestoreChecked, setFilterImportAuditQuickApplySyncRestoreChecked] = React.useState(
    Boolean(
      initialPrefs.filterImportAuditQuickApplySyncRestore !== undefined
        ? initialPrefs.filterImportAuditQuickApplySyncRestore
        : CONTRACT_OVERLAY_DEFAULT_PREFS.filterImportAuditQuickApplySyncRestore
    )
  );
  const [filterImportAuditPinChipFilter, setFilterImportAuditPinChipFilter] = React.useState(
    normalizeFilterImportAuditPinChipFilter(
      initialPrefs.filterImportAuditPinChipFilter || CONTRACT_OVERLAY_DEFAULT_PREFS.filterImportAuditPinChipFilter
    )
  );
  const [filterImportAuditResetArmedChecked, setFilterImportAuditResetArmedChecked] = React.useState(false);
  const [filterImportAuditResetArmedAtMs, setFilterImportAuditResetArmedAtMs] = React.useState(0);
  const [filterImportAuditResetTickMs, setFilterImportAuditResetTickMs] = React.useState(0);
  const [filterImportAuditQuickApplyTelemetry, setFilterImportAuditQuickApplyTelemetry] = React.useState([]);
  const [filterImportAuditQuickTelemetryFailureOnlyChecked, setFilterImportAuditQuickTelemetryFailureOnlyChecked] = React.useState(
    Boolean(
      initialPrefs.filterImportAuditQuickTelemetryFailureOnly !== undefined
        ? initialPrefs.filterImportAuditQuickTelemetryFailureOnly
        : CONTRACT_OVERLAY_DEFAULT_PREFS.filterImportAuditQuickTelemetryFailureOnly
    )
  );
  const [filterImportAuditQuickTelemetryReasonQuery, setFilterImportAuditQuickTelemetryReasonQuery] = React.useState(
    String(
      initialPrefs.filterImportAuditQuickTelemetryReasonQuery
      || CONTRACT_OVERLAY_DEFAULT_PREFS.filterImportAuditQuickTelemetryReasonQuery
      || ""
    ).slice(0, FILTER_IMPORT_AUDIT_QUICK_REASON_QUERY_MAX)
  );
  const [filterImportHistoryKeepText, setFilterImportHistoryKeepText] = React.useState("8");
  const [filterImportAuditRowCapText, setFilterImportAuditRowCapText] = React.useState(
    String(initialPrefs.filterImportAuditRowCap || CONTRACT_OVERLAY_DEFAULT_PREFS.filterImportAuditRowCap)
  );
  const [filterImportAuditRowOffset, setFilterImportAuditRowOffset] = React.useState(0);
  const [shortcutTransferText, setShortcutTransferText] = React.useState("");
  const [shortcutTransferStatus, setShortcutTransferStatus] = React.useState("");
  const [quickTelemetryDrilldownTransferText, setQuickTelemetryDrilldownTransferText] = React.useState("");
  const [quickTelemetryDrilldownTransferStatus, setQuickTelemetryDrilldownTransferStatus] = React.useState("");
  const [quickTelemetryDrilldownImportFilterBundleText, setQuickTelemetryDrilldownImportFilterBundleText] = React.useState("");
  const [quickTelemetryDrilldownImportFilterBundleStatus, setQuickTelemetryDrilldownImportFilterBundleStatus] = React.useState("");
  const [quickTelemetryDrilldownImportFilterBundleMode, setQuickTelemetryDrilldownImportFilterBundleMode] = React.useState(
    normalizeQuickTelemetryDrilldownImportFilterBundleMode(
      initialPrefs.quickTelemetryDrilldownImportFilterBundleMode
      || CONTRACT_OVERLAY_DEFAULT_PREFS.quickTelemetryDrilldownImportFilterBundleMode
    )
  );
  const [quickTelemetryDrilldownStrictAdoptionSignals, setQuickTelemetryDrilldownStrictAdoptionSignals] = React.useState(
    () => normalizeQuickTelemetryDrilldownStrictAdoptionSignals(
      initialPrefs.quickTelemetryDrilldownStrictAdoptionSignals,
      null
    )
  );
  const [quickTelemetryDrilldownStrictAdoptionGateStatus, setQuickTelemetryDrilldownStrictAdoptionGateStatus] = React.useState("");
  const [quickTelemetryDrilldownStrictCutoverStatus, setQuickTelemetryDrilldownStrictCutoverStatus] = React.useState("");
  const [quickTelemetryDrilldownStrictCutoverLedger, setQuickTelemetryDrilldownStrictCutoverLedger] = React.useState([]);
  const [quickTelemetryDrilldownStrictCutoverLedgerStatus, setQuickTelemetryDrilldownStrictCutoverLedgerStatus] = React.useState("");
  const [quickTelemetryDrilldownStrictRollbackDrillStatus, setQuickTelemetryDrilldownStrictRollbackDrillStatus] = React.useState("");
  const [quickTelemetryStrictRollbackPackageTrustPolicy, setQuickTelemetryStrictRollbackPackageTrustPolicy] = React.useState(
    normalizeQuickTelemetryStrictRollbackPackageTrustPolicy(
      initialPrefs.quickTelemetryStrictRollbackPackageTrustPolicy
      || CONTRACT_OVERLAY_DEFAULT_PREFS.quickTelemetryStrictRollbackPackageTrustPolicy
    )
  );
  const [quickTelemetryDrilldownStrictRollbackPackageStatus, setQuickTelemetryDrilldownStrictRollbackPackageStatus] = React.useState("");
  const [quickTelemetryDrilldownStrictRollbackPackageReplayText, setQuickTelemetryDrilldownStrictRollbackPackageReplayText] = React.useState("");
  const [quickTelemetryDrilldownStrictRollbackPackageDeltaConfirmChecked, setQuickTelemetryDrilldownStrictRollbackPackageDeltaConfirmChecked] = React.useState(false);
  const [quickTelemetryDrilldownStrictRollbackPackageOverrideReasonText, setQuickTelemetryDrilldownStrictRollbackPackageOverrideReasonText] = React.useState("");
  const [quickTelemetryDrilldownStrictRollbackPackageOverrideLog, setQuickTelemetryDrilldownStrictRollbackPackageOverrideLog] = React.useState([]);
  const [quickTelemetryDrilldownStrictRollbackPackageOverrideLogStatus, setQuickTelemetryDrilldownStrictRollbackPackageOverrideLogStatus] = React.useState("");
  const [quickTelemetryDrilldownStrictRollbackTrustAuditBundleStatus, setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleStatus] = React.useState("");
  const [quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus, setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus] = React.useState("");
  const [quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffImportText, setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffImportText] = React.useState("");
  const [quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydratedSnapshot, setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydratedSnapshot] = React.useState(null);
  const [quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmChecked, setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmChecked] = React.useState(false);
  const [quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmArmedAtMs, setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmArmedAtMs] = React.useState(0);
  const [quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmTickMs, setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmTickMs] = React.useState(0);
  const [quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityTrail, setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityTrail] = React.useState([]);
  const [quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityImportText, setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityImportText] = React.useState("");
  const [quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmChecked, setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmChecked] = React.useState(false);
  const [quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmArmedAtMs, setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmArmedAtMs] = React.useState(0);
  const [quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTickMs, setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTickMs] = React.useState(0);
  const [quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportText, setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportText] = React.useState("");
  const [quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmChecked, setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmChecked] = React.useState(false);
  const [quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmArmedAtMs, setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmArmedAtMs] = React.useState(0);
  const [quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTickMs, setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTickMs] = React.useState(0);
  const [quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportText, setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportText] = React.useState("");
  const [quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmChecked, setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmChecked] = React.useState(false);
  const [quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmArmedAtMs, setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmArmedAtMs] = React.useState(0);
  const [quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmTickMs, setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmTickMs] = React.useState(0);
  const [quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrail, setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrail] = React.useState([]);
  const [quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailControlsStatus, setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailControlsStatus] = React.useState("");
  const [quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrail, setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrail] = React.useState([]);
  const [quickTelemetryDrilldownStrictRollbackTrustAuditBundleImportText, setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleImportText] = React.useState("");
  const [quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmChecked, setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmChecked] = React.useState(false);
  const [quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmArmedAtMs, setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmArmedAtMs] = React.useState(0);
  const [quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmTickMs, setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmTickMs] = React.useState(0);
  const [quickTelemetryDrilldownImportSelection, setQuickTelemetryDrilldownImportSelection] = React.useState({});
  const [quickTelemetryDrilldownImportConflictOnlyChecked, setQuickTelemetryDrilldownImportConflictOnlyChecked] = React.useState(
    Boolean(
      initialPrefs.quickTelemetryDrilldownImportConflictOnly !== undefined
        ? initialPrefs.quickTelemetryDrilldownImportConflictOnly
        : CONTRACT_OVERLAY_DEFAULT_PREFS.quickTelemetryDrilldownImportConflictOnly
    )
  );
  const [quickTelemetryDrilldownImportNameQuery, setQuickTelemetryDrilldownImportNameQuery] = React.useState(
    String(
      initialPrefs.quickTelemetryDrilldownImportNameQuery
      || CONTRACT_OVERLAY_DEFAULT_PREFS.quickTelemetryDrilldownImportNameQuery
      || ""
    ).slice(0, QUICK_TELEMETRY_DRILLDOWN_IMPORT_NAME_QUERY_MAX)
  );
  const [quickTelemetryDrilldownImportConflictFilter, setQuickTelemetryDrilldownImportConflictFilter] = React.useState(
    normalizeQuickTelemetryDrilldownImportConflictFilter(
      initialPrefs.quickTelemetryDrilldownImportConflictFilter
      || CONTRACT_OVERLAY_DEFAULT_PREFS.quickTelemetryDrilldownImportConflictFilter
    )
  );
  const [quickTelemetryDrilldownImportRowCapText, setQuickTelemetryDrilldownImportRowCapText] = React.useState(
    String(
      initialPrefs.quickTelemetryDrilldownImportRowCap
      || CONTRACT_OVERLAY_DEFAULT_PREFS.quickTelemetryDrilldownImportRowCap
    )
  );
  const [quickTelemetryDrilldownImportRowOffset, setQuickTelemetryDrilldownImportRowOffset] = React.useState(0);
  const [quickTelemetryDrilldownImportOverwriteConfirmChecked, setQuickTelemetryDrilldownImportOverwriteConfirmChecked] = React.useState(false);
  const [quickTelemetryDrilldownImportUndoSnapshot, setQuickTelemetryDrilldownImportUndoSnapshot] = React.useState(null);
  const [detailCopyStatus, setDetailCopyStatus] = React.useState("");
  const filterImportFileInputRef = React.useRef(null);
  const shortcutImportFileInputRef = React.useRef(null);
  const quickTelemetryDrilldownImportFileInputRef = React.useRef(null);
  const [rowWindowOffset, setRowWindowOffset] = React.useState(0);
  const [expandedRowKeys, setExpandedRowKeys] = React.useState(() => new Set());
  const applyOverlayPreset = React.useCallback((presetName) => {
    const name = String(presetName || "").trim();
    if (name === "reset_all") {
      setSourceFilter(CONTRACT_OVERLAY_DEFAULT_PREFS.sourceFilter);
      setSeverityFilter(CONTRACT_OVERLAY_DEFAULT_PREFS.severityFilter);
      setPolicyFilter(CONTRACT_OVERLAY_DEFAULT_PREFS.policyFilter);
      setPinnedRunId(CONTRACT_OVERLAY_DEFAULT_PREFS.pinnedRunId);
      setNonZeroOnly(Boolean(CONTRACT_OVERLAY_DEFAULT_PREFS.nonZeroOnly));
      setCompactMode(Boolean(CONTRACT_OVERLAY_DEFAULT_PREFS.compactMode));
      setGateHistoryLimit(String(CONTRACT_OVERLAY_DEFAULT_PREFS.gateHistoryLimit));
      setGateHistoryPages(String(CONTRACT_OVERLAY_DEFAULT_PREFS.gateHistoryPages));
      setRowWindowSizeText(String(CONTRACT_OVERLAY_DEFAULT_PREFS.rowWindowSize));
      setRowVolumeGuardBypass(Boolean(CONTRACT_OVERLAY_DEFAULT_PREFS.rowVolumeGuardBypass));
      setFilterImportAuditRowCapText(String(CONTRACT_OVERLAY_DEFAULT_PREFS.filterImportAuditRowCap));
      setFilterImportAuditRowOffset(0);
      setFilterImportAuditSearchText("");
      setFilterImportAuditKindFilter("all");
      setFilterImportAuditModeFilter("all");
      setFilterImportAuditPinnedPresetId(String(CONTRACT_OVERLAY_DEFAULT_PREFS.filterImportAuditPinnedPreset || ""));
      setFilterImportAuditRestoreQueryChecked(Boolean(CONTRACT_OVERLAY_DEFAULT_PREFS.filterImportAuditRestoreQuery));
      setFilterImportAuditRestorePagingChecked(Boolean(CONTRACT_OVERLAY_DEFAULT_PREFS.filterImportAuditRestorePaging));
      setFilterImportAuditRestorePinnedPresetChecked(Boolean(CONTRACT_OVERLAY_DEFAULT_PREFS.filterImportAuditRestorePinnedPreset));
      setFilterImportAuditRestoreActiveEntryChecked(Boolean(CONTRACT_OVERLAY_DEFAULT_PREFS.filterImportAuditRestoreActiveEntry));
      setFilterImportAuditQuickApplySyncRestoreChecked(
        Boolean(CONTRACT_OVERLAY_DEFAULT_PREFS.filterImportAuditQuickApplySyncRestore)
      );
      setFilterImportAuditQuickTelemetryFailureOnlyChecked(
        Boolean(CONTRACT_OVERLAY_DEFAULT_PREFS.filterImportAuditQuickTelemetryFailureOnly)
      );
      setFilterImportAuditQuickTelemetryReasonQuery(
        String(CONTRACT_OVERLAY_DEFAULT_PREFS.filterImportAuditQuickTelemetryReasonQuery || "")
      );
      setQuickTelemetryDrilldownImportConflictOnlyChecked(
        Boolean(CONTRACT_OVERLAY_DEFAULT_PREFS.quickTelemetryDrilldownImportConflictOnly)
      );
      setQuickTelemetryDrilldownImportNameQuery(
        String(CONTRACT_OVERLAY_DEFAULT_PREFS.quickTelemetryDrilldownImportNameQuery || "")
      );
      setQuickTelemetryDrilldownImportConflictFilter(
        normalizeQuickTelemetryDrilldownImportConflictFilter(
          CONTRACT_OVERLAY_DEFAULT_PREFS.quickTelemetryDrilldownImportConflictFilter
        )
      );
      setQuickTelemetryDrilldownImportRowCapText(
        String(CONTRACT_OVERLAY_DEFAULT_PREFS.quickTelemetryDrilldownImportRowCap || "16")
      );
      setQuickTelemetryDrilldownImportFilterBundleMode(
        normalizeQuickTelemetryDrilldownImportFilterBundleMode(
          CONTRACT_OVERLAY_DEFAULT_PREFS.quickTelemetryDrilldownImportFilterBundleMode
        )
      );
      setQuickTelemetryDrilldownStrictAdoptionSignals(
        normalizeQuickTelemetryDrilldownStrictAdoptionSignals(
          CONTRACT_OVERLAY_DEFAULT_PREFS.quickTelemetryDrilldownStrictAdoptionSignals,
          null
        )
      );
      setQuickTelemetryDrilldownStrictAdoptionGateStatus("");
      setQuickTelemetryDrilldownStrictCutoverStatus("");
      setQuickTelemetryDrilldownStrictCutoverLedger([]);
      setQuickTelemetryDrilldownStrictCutoverLedgerStatus("");
      setQuickTelemetryDrilldownStrictRollbackDrillStatus("");
      setQuickTelemetryStrictRollbackPackageTrustPolicy(
        normalizeQuickTelemetryStrictRollbackPackageTrustPolicy(
          CONTRACT_OVERLAY_DEFAULT_PREFS.quickTelemetryStrictRollbackPackageTrustPolicy
        )
      );
      setQuickTelemetryDrilldownStrictRollbackPackageStatus("");
      setQuickTelemetryDrilldownStrictRollbackPackageReplayText("");
      setQuickTelemetryDrilldownStrictRollbackPackageDeltaConfirmChecked(false);
      setQuickTelemetryDrilldownStrictRollbackPackageOverrideReasonText("");
      setQuickTelemetryDrilldownStrictRollbackPackageOverrideLog([]);
      setQuickTelemetryDrilldownStrictRollbackPackageOverrideLogStatus("");
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleStatus("");
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus("");
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydratedSnapshot(null);
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmChecked(false);
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffImportText("");
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleImportText("");
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmChecked(false);
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmArmedAtMs(0);
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmTickMs(0);
      setQuickTelemetryDrilldownImportRowOffset(0);
      setActiveQuickTelemetryDrilldownProfile(
        String(CONTRACT_OVERLAY_DEFAULT_PREFS.activeQuickTelemetryDrilldownProfile || "default")
      );
      setQuickTelemetryDrilldownProfileDraft(
        String(CONTRACT_OVERLAY_DEFAULT_PREFS.quickTelemetryDrilldownProfileDraft || "custom_drilldown")
      );
      setFilterImportAuditPinChipFilter(
        normalizeFilterImportAuditPinChipFilter(CONTRACT_OVERLAY_DEFAULT_PREFS.filterImportAuditPinChipFilter)
      );
      setFilterImportAuditResetArmedChecked(false);
      setFilterImportAuditResetArmedAtMs(0);
      setShowShortcutHelp(false);
      setDetailFieldStates(normalizeDetailFieldStates(DEFAULT_DETAIL_FIELD_STATES, DEFAULT_DETAIL_FIELD_STATES));
      setRowWindowOffset(0);
      return;
    }
    if (name === "triage") {
      setSeverityFilter("high");
      setPolicyFilter("hold");
      setNonZeroOnly(true);
      setCompactMode(true);
      setGateHistoryLimit("128");
      setGateHistoryPages("2");
      setRowWindowSizeText("80");
      setRowVolumeGuardBypass(false);
      setShowShortcutHelp(false);
      setDetailFieldStates(normalizeDetailFieldStates({
        timestamp_iso: true,
        event_meta: true,
        delta: true,
        snapshot: false,
        baseline: false,
        note_json: false,
      }, DEFAULT_DETAIL_FIELD_STATES));
      setRowWindowOffset(0);
      return;
    }
    if (name === "deep_gate") {
      setSeverityFilter("all");
      setPolicyFilter("all");
      setNonZeroOnly(false);
      setCompactMode(false);
      setGateHistoryLimit("512");
      setGateHistoryPages("4");
      setRowWindowSizeText("200");
      setRowVolumeGuardBypass(false);
      setShowShortcutHelp(false);
      setDetailFieldStates(normalizeDetailFieldStates({
        timestamp_iso: true,
        event_meta: true,
        delta: true,
        snapshot: true,
        baseline: true,
        note_json: true,
      }, DEFAULT_DETAIL_FIELD_STATES));
      setRowWindowOffset(0);
    }
  }, []);
  const gateLookupOptions = React.useMemo(() => {
    const limitRaw = Number(gateHistoryLimit || 0);
    const pagesRaw = Number(gateHistoryPages || 0);
    const historyLimit = Number.isFinite(limitRaw) && limitRaw > 0
      ? Math.max(32, Math.min(4096, Math.floor(limitRaw)))
      : 256;
    const pageBudget = Number.isFinite(pagesRaw) && pagesRaw > 0
      ? Math.max(1, Math.min(8, Math.floor(pagesRaw)))
      : 2;
    return { historyLimit, pageBudget };
  }, [gateHistoryLimit, gateHistoryPages]);
  const sourceOptions = React.useMemo(() => {
    const set = new Set();
    rows.forEach((row) => set.add(String(row?.event_source || "-")));
    return ["all", ...Array.from(set.values()).sort((a, b) => a.localeCompare(b))];
  }, [rows]);
  const runOptions = React.useMemo(() => {
    const set = new Set();
    rows.forEach((row) => {
      const runId = String(row?.graph_run_id || "").trim();
      if (runId) set.add(runId);
    });
    return ["all", ...Array.from(set.values()).sort((a, b) => a.localeCompare(b))];
  }, [rows]);
  const rowWindowSize = React.useMemo(
    () => clampInteger(rowWindowSizeText, 20, 500, 120),
    [rowWindowSizeText]
  );

  React.useEffect(() => {
    if (!sourceOptions.includes(sourceFilter)) {
      setSourceFilter("all");
    }
  }, [sourceFilter, sourceOptions]);

  React.useEffect(() => {
    const allowed = SEVERITY_FILTER_OPTIONS.map((x) => String(x.id || ""));
    if (!allowed.includes(severityFilter)) {
      setSeverityFilter("all");
    }
  }, [severityFilter]);

  React.useEffect(() => {
    const allowed = POLICY_FILTER_OPTIONS.map((x) => String(x.id || ""));
    if (!allowed.includes(policyFilter)) {
      setPolicyFilter("all");
    }
  }, [policyFilter]);

  React.useEffect(() => {
    const allowed = FILTER_IMPORT_MODE_OPTIONS.map((x) => String(x.id || ""));
    if (!allowed.includes(filterImportMode)) {
      setFilterImportMode(CONTRACT_OVERLAY_DEFAULT_PREFS.filterImportMode);
    }
  }, [filterImportMode]);

  React.useEffect(() => {
    if (FILTER_IMPORT_AUDIT_KIND_OPTIONS.includes(filterImportAuditKindFilter)) return;
    setFilterImportAuditKindFilter("all");
  }, [filterImportAuditKindFilter]);

  React.useEffect(() => {
    if (FILTER_IMPORT_AUDIT_MODE_OPTIONS.includes(filterImportAuditModeFilter)) return;
    setFilterImportAuditModeFilter("all");
  }, [filterImportAuditModeFilter]);

  React.useEffect(() => {
    if (!filterImportAuditPinnedPresetId) return;
    if (FILTER_IMPORT_AUDIT_QUERY_PRESETS.some((row) => String(row?.id || "") === filterImportAuditPinnedPresetId)) return;
    setFilterImportAuditPinnedPresetId("");
  }, [filterImportAuditPinnedPresetId]);

  React.useEffect(() => {
    if (!filterImportAuditResetArmedChecked) {
      setFilterImportAuditResetTickMs(0);
      return;
    }
    setFilterImportAuditResetTickMs(Date.now());
    const timer = setInterval(() => {
      setFilterImportAuditResetTickMs(Date.now());
    }, 1_000);
    return () => clearInterval(timer);
  }, [filterImportAuditResetArmedChecked]);

  React.useEffect(() => {
    if (!filterImportAuditResetArmedChecked) return;
    const timeout = setTimeout(() => {
      setFilterImportAuditResetArmedChecked(false);
      setFilterImportAuditResetArmedAtMs(0);
      setFilterImportAuditResetTickMs(0);
      setFilterTransferStatus("reset arm expired: re-arm to execute reset");
    }, FILTER_IMPORT_AUDIT_RESET_ARM_TIMEOUT_MS);
    return () => clearTimeout(timeout);
  }, [filterImportAuditResetArmedChecked]);

  React.useEffect(() => {
    const normalized = normalizeFilterImportAuditPinChipFilter(filterImportAuditPinChipFilter);
    if (normalized === filterImportAuditPinChipFilter) return;
    setFilterImportAuditPinChipFilter(normalized);
  }, [filterImportAuditPinChipFilter]);

  React.useEffect(() => {
    const normalized = String(filterImportAuditQuickTelemetryReasonQuery || "")
      .slice(0, FILTER_IMPORT_AUDIT_QUICK_REASON_QUERY_MAX);
    if (normalized === filterImportAuditQuickTelemetryReasonQuery) return;
    setFilterImportAuditQuickTelemetryReasonQuery(normalized);
  }, [filterImportAuditQuickTelemetryReasonQuery]);

  React.useEffect(() => {
    const normalized = String(quickTelemetryDrilldownImportNameQuery || "")
      .slice(0, QUICK_TELEMETRY_DRILLDOWN_IMPORT_NAME_QUERY_MAX);
    if (normalized === quickTelemetryDrilldownImportNameQuery) return;
    setQuickTelemetryDrilldownImportNameQuery(normalized);
  }, [quickTelemetryDrilldownImportNameQuery]);

  React.useEffect(() => {
    const normalized = normalizeQuickTelemetryDrilldownImportConflictFilter(
      quickTelemetryDrilldownImportConflictFilter
    );
    if (normalized === quickTelemetryDrilldownImportConflictFilter) return;
    setQuickTelemetryDrilldownImportConflictFilter(normalized);
  }, [quickTelemetryDrilldownImportConflictFilter]);

  React.useEffect(() => {
    const normalized = normalizeQuickTelemetryDrilldownImportFilterBundleMode(
      quickTelemetryDrilldownImportFilterBundleMode
    );
    if (normalized === quickTelemetryDrilldownImportFilterBundleMode) return;
    setQuickTelemetryDrilldownImportFilterBundleMode(normalized);
  }, [quickTelemetryDrilldownImportFilterBundleMode]);

  React.useEffect(() => {
    const normalized = normalizeQuickTelemetryStrictRollbackPackageTrustPolicy(
      quickTelemetryStrictRollbackPackageTrustPolicy
    );
    if (normalized === quickTelemetryStrictRollbackPackageTrustPolicy) return;
    setQuickTelemetryStrictRollbackPackageTrustPolicy(normalized);
  }, [quickTelemetryStrictRollbackPackageTrustPolicy]);

  React.useEffect(() => {
    const normalized = normalizeQuickTelemetryDrilldownStrictAdoptionSignals(
      quickTelemetryDrilldownStrictAdoptionSignals,
      null
    );
    if (JSON.stringify(normalized) === JSON.stringify(quickTelemetryDrilldownStrictAdoptionSignals || {})) return;
    setQuickTelemetryDrilldownStrictAdoptionSignals(normalized);
  }, [quickTelemetryDrilldownStrictAdoptionSignals]);

  React.useEffect(() => {
    const normalizedRaw = clampInteger(quickTelemetryDrilldownImportRowCapText, 4, 200, 16);
    const normalized = QUICK_TELEMETRY_DRILLDOWN_IMPORT_ROW_CAP_OPTIONS.includes(String(normalizedRaw))
      ? normalizedRaw
      : Number(CONTRACT_OVERLAY_DEFAULT_PREFS.quickTelemetryDrilldownImportRowCap || 16);
    if (String(normalized) === String(quickTelemetryDrilldownImportRowCapText)) return;
    setQuickTelemetryDrilldownImportRowCapText(String(normalized));
  }, [quickTelemetryDrilldownImportRowCapText]);

  React.useEffect(() => {
    const normalizedRaw = clampInteger(filterImportAuditRowCapText, 6, 200, 24);
    const normalized = FILTER_IMPORT_AUDIT_ROW_CAP_OPTIONS.includes(String(normalizedRaw))
      ? normalizedRaw
      : Number(CONTRACT_OVERLAY_DEFAULT_PREFS.filterImportAuditRowCap || 24);
    if (String(normalized) === String(filterImportAuditRowCapText)) return;
    setFilterImportAuditRowCapText(String(normalized));
  }, [filterImportAuditRowCapText]);

  React.useEffect(() => {
    if (filterImportMode === "replace_custom") return;
    if (!filterReplaceConfirmChecked) return;
    setFilterReplaceConfirmChecked(false);
  }, [filterImportMode, filterReplaceConfirmChecked]);

  React.useEffect(() => {
    if (!filterReplaceConfirmChecked) return;
    setFilterReplaceConfirmChecked(false);
  }, [filterReplaceConfirmChecked, filterTransferText]);

  React.useEffect(() => {
    if (!quickTelemetryDrilldownImportOverwriteConfirmChecked) return;
    setQuickTelemetryDrilldownImportOverwriteConfirmChecked(false);
  }, [quickTelemetryDrilldownImportOverwriteConfirmChecked, quickTelemetryDrilldownTransferText]);

  React.useEffect(() => {
    if (!runOptions.includes(pinnedRunId)) {
      setPinnedRunId("all");
    }
  }, [pinnedRunId, runOptions]);

  React.useEffect(() => {
    const names = Object.keys(filterPresets);
    if (names.length === 0) {
      setFilterPresets(loadFilterPresets());
      return;
    }
    if (filterPresets[activeFilterPreset]) return;
    const fallbackName = filterPresets.default ? "default" : String(names[0] || "default");
    setActiveFilterPreset(fallbackName);
  }, [activeFilterPreset, filterPresets]);

  React.useEffect(() => {
    saveFilterPresets(filterPresets);
  }, [filterPresets]);

  React.useEffect(() => {
    const names = Object.keys(shortcutProfiles);
    if (names.length === 0) {
      setShortcutProfiles(loadShortcutProfiles());
      return;
    }
    if (shortcutProfiles[activeShortcutProfile]) return;
    const fallbackName = shortcutProfiles.default ? "default" : String(names[0] || "default");
    const fallbackBindings = normalizeShortcutBindings(
      shortcutProfiles[fallbackName],
      DEFAULT_SHORTCUT_BINDINGS
    );
    setActiveShortcutProfile(fallbackName);
    setShortcutBindings(fallbackBindings);
  }, [activeShortcutProfile, shortcutProfiles]);

  React.useEffect(() => {
    saveShortcutProfiles(shortcutProfiles);
  }, [shortcutProfiles]);

  React.useEffect(() => {
    const names = Object.keys(quickTelemetryDrilldownProfiles);
    if (names.length === 0) {
      setQuickTelemetryDrilldownProfiles(loadQuickTelemetryDrilldownProfiles());
      return;
    }
    if (quickTelemetryDrilldownProfiles[activeQuickTelemetryDrilldownProfile]) return;
    const fallbackName = quickTelemetryDrilldownProfiles.default ? "default" : String(names[0] || "default");
    setActiveQuickTelemetryDrilldownProfile(fallbackName);
  }, [activeQuickTelemetryDrilldownProfile, quickTelemetryDrilldownProfiles]);

  React.useEffect(() => {
    saveQuickTelemetryDrilldownProfiles(quickTelemetryDrilldownProfiles);
  }, [quickTelemetryDrilldownProfiles]);

  React.useEffect(() => {
    saveFilterImportHistoryState({
      undoStack: filterImportUndoStack,
      redoStack: filterImportRedoStack,
      auditTrail: filterImportAuditTrail,
    });
  }, [filterImportAuditTrail, filterImportRedoStack, filterImportUndoStack]);

  React.useEffect(() => {
    saveContractOverlayPrefs({
      sourceFilter,
      severityFilter,
      policyFilter,
      pinnedRunId,
      nonZeroOnly,
      compactMode,
      gateHistoryLimit,
      gateHistoryPages,
      rowWindowSize,
      rowVolumeGuardBypass,
      showShortcutHelp,
      activeFilterPreset,
      filterPresetDraft,
      filterImportMode,
      filterImportAuditRowCap: filterImportAuditRowCapText,
      filterImportAuditPinnedPreset: filterImportAuditPinnedPresetId,
      filterImportAuditRestoreQuery: filterImportAuditRestoreQueryChecked,
      filterImportAuditRestorePaging: filterImportAuditRestorePagingChecked,
      filterImportAuditRestorePinnedPreset: filterImportAuditRestorePinnedPresetChecked,
      filterImportAuditRestoreActiveEntry: filterImportAuditRestoreActiveEntryChecked,
      filterImportAuditQuickApplySyncRestore: filterImportAuditQuickApplySyncRestoreChecked,
      filterImportAuditQuickTelemetryFailureOnly: filterImportAuditQuickTelemetryFailureOnlyChecked,
      filterImportAuditQuickTelemetryReasonQuery: filterImportAuditQuickTelemetryReasonQuery,
      quickTelemetryDrilldownImportConflictOnly: quickTelemetryDrilldownImportConflictOnlyChecked,
      quickTelemetryDrilldownImportNameQuery: quickTelemetryDrilldownImportNameQuery,
      quickTelemetryDrilldownImportConflictFilter: quickTelemetryDrilldownImportConflictFilter,
      quickTelemetryDrilldownImportRowCap: quickTelemetryDrilldownImportRowCapText,
      quickTelemetryDrilldownImportFilterBundleMode: quickTelemetryDrilldownImportFilterBundleMode,
      quickTelemetryStrictRollbackPackageTrustPolicy: quickTelemetryStrictRollbackPackageTrustPolicy,
      quickTelemetryDrilldownStrictAdoptionSignals: quickTelemetryDrilldownStrictAdoptionSignals,
      activeQuickTelemetryDrilldownProfile,
      quickTelemetryDrilldownProfileDraft,
      filterImportAuditPinChipFilter,
      activeShortcutProfile,
      shortcutProfileDraft,
      shortcutBindings,
      detailFieldStates,
    });
  }, [
    activeFilterPreset,
    filterImportAuditRowCapText,
    filterImportAuditPinnedPresetId,
    filterImportAuditRestoreActiveEntryChecked,
    filterImportAuditQuickApplySyncRestoreChecked,
    filterImportAuditQuickTelemetryFailureOnlyChecked,
    filterImportAuditQuickTelemetryReasonQuery,
    quickTelemetryDrilldownImportConflictOnlyChecked,
    quickTelemetryDrilldownImportNameQuery,
    quickTelemetryDrilldownImportConflictFilter,
    quickTelemetryDrilldownImportRowCapText,
    quickTelemetryDrilldownImportFilterBundleMode,
    quickTelemetryStrictRollbackPackageTrustPolicy,
    quickTelemetryDrilldownStrictAdoptionSignals,
    activeQuickTelemetryDrilldownProfile,
    quickTelemetryDrilldownProfileDraft,
    filterImportAuditPinChipFilter,
    filterImportAuditRestorePagingChecked,
    filterImportAuditRestorePinnedPresetChecked,
    filterImportAuditRestoreQueryChecked,
    filterImportMode,
    filterPresetDraft,
    activeShortcutProfile,
    compactMode,
    detailFieldStates,
    gateHistoryLimit,
    gateHistoryPages,
    nonZeroOnly,
    policyFilter,
    pinnedRunId,
    rowWindowSize,
    rowVolumeGuardBypass,
    severityFilter,
    showShortcutHelp,
    shortcutBindings,
    shortcutProfileDraft,
    sourceFilter,
  ]);

  const scopedRows = React.useMemo(() => rows.filter((row) => {
    const source = String(row?.event_source || "-");
    if (sourceFilter !== "all" && source !== sourceFilter) return false;
    const runId = String(row?.graph_run_id || "");
    if (pinnedRunId !== "all" && runId !== pinnedRunId) return false;
    if (!nonZeroOnly) return true;
    const du = Number(row?.delta?.unique_warning_count || 0);
    const da = Number(row?.delta?.attempt_count_total || 0);
    return du !== 0 || da !== 0;
  }), [nonZeroOnly, pinnedRunId, rows, sourceFilter]);
  const severityCounts = React.useMemo(() => {
    const out = { high: 0, med: 0, low: 0 };
    scopedRows.forEach((row) => {
      const s = classifyContractSeverity(row);
      if (s === "high" || s === "med" || s === "low") {
        out[s] += 1;
      }
    });
    return out;
  }, [scopedRows]);
  const severityScopedRows = React.useMemo(() => {
    if (severityFilter === "all") return scopedRows;
    return scopedRows.filter((row) => classifyContractSeverity(row) === severityFilter);
  }, [scopedRows, severityFilter]);
  const policyCounts = React.useMemo(() => {
    const out = { hold: 0, adopt: 0, none: 0 };
    severityScopedRows.forEach((row) => {
      const p = classifyPolicyState(row);
      if (p === "hold" || p === "adopt" || p === "none") {
        out[p] += 1;
      }
    });
    return out;
  }, [severityScopedRows]);
  const filteredRows = React.useMemo(() => {
    if (policyFilter === "all") return severityScopedRows;
    return severityScopedRows.filter((row) => classifyPolicyState(row) === policyFilter);
  }, [policyFilter, severityScopedRows]);
  const rowVolumeGuardActive = React.useMemo(
    () => Number(filteredRows.length || 0) >= CONTRACT_ROW_VOLUME_GUARD_TRIGGER,
    [filteredRows.length]
  );
  React.useEffect(() => {
    if (!rowVolumeGuardActive || rowVolumeGuardBypass) return;
    const clamped = clampInteger(
      rowWindowSizeText,
      20,
      CONTRACT_ROW_VOLUME_GUARD_MAX_WINDOW,
      CONTRACT_OVERLAY_DEFAULT_PREFS.rowWindowSize
    );
    if (String(clamped) === String(rowWindowSizeText)) return;
    setRowWindowSizeText(String(clamped));
  }, [rowVolumeGuardActive, rowVolumeGuardBypass, rowWindowSizeText]);
  const rowWindowOptionValues = React.useMemo(() => {
    if (rowVolumeGuardActive && !rowVolumeGuardBypass) {
      return ROW_WINDOW_SIZE_OPTIONS.filter((opt) => Number(opt) <= CONTRACT_ROW_VOLUME_GUARD_MAX_WINDOW);
    }
    return ROW_WINDOW_SIZE_OPTIONS;
  }, [rowVolumeGuardActive, rowVolumeGuardBypass]);
  const maxRowWindowOffset = React.useMemo(
    () => Math.max(0, Number(filteredRows.length || 0) - rowWindowSize),
    [filteredRows.length, rowWindowSize]
  );
  React.useEffect(() => {
    setRowWindowOffset(0);
  }, [nonZeroOnly, pinnedRunId, policyFilter, rowWindowSize, severityFilter, sourceFilter]);
  React.useEffect(() => {
    if (rowWindowOffset > maxRowWindowOffset) {
      setRowWindowOffset(maxRowWindowOffset);
    }
  }, [maxRowWindowOffset, rowWindowOffset]);
  const rowWindowEnd = Math.min(filteredRows.length, rowWindowOffset + rowWindowSize);
  const visibleRows = React.useMemo(
    () => filteredRows.slice(rowWindowOffset, rowWindowEnd),
    [filteredRows, rowWindowEnd, rowWindowOffset]
  );
  const visibleRowKeySet = React.useMemo(() => {
    const out = new Set();
    visibleRows.forEach((row) => out.add(buildContractRowKey(row)));
    return out;
  }, [visibleRows]);
  React.useEffect(() => {
    setExpandedRowKeys((prev) => {
      if (!(prev instanceof Set) || prev.size === 0) return prev;
      const next = new Set();
      prev.forEach((key) => {
        if (visibleRowKeySet.has(key)) next.add(key);
      });
      if (next.size === prev.size) return prev;
      return next;
    });
  }, [visibleRowKeySet]);
  const toggleRowExpanded = React.useCallback((rowKey) => {
    const key = String(rowKey || "");
    if (!key) return;
    setExpandedRowKeys((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }, []);
  const expandVisibleDetails = React.useCallback(() => {
    setExpandedRowKeys((prev) => {
      const next = new Set(prev);
      visibleRows.forEach((row) => next.add(buildContractRowKey(row)));
      return next;
    });
  }, [visibleRows]);
  const collapseAllDetails = React.useCallback(() => {
    setExpandedRowKeys(new Set());
  }, []);
  const shortcutProfileOptions = React.useMemo(() => {
    const names = Object.keys(shortcutProfiles).map((name) => String(name || "").trim()).filter(Boolean);
    names.sort((a, b) => a.localeCompare(b));
    if (!names.includes("default")) return names;
    return ["default", ...names.filter((name) => name !== "default")];
  }, [shortcutProfiles]);
  const normalizedShortcutProfileDraft = React.useMemo(
    () => normalizeShortcutProfileName(shortcutProfileDraft),
    [shortcutProfileDraft]
  );
  const activeShortcutIsBuiltin = React.useMemo(
    () => Object.prototype.hasOwnProperty.call(DEFAULT_SHORTCUT_PROFILES, activeShortcutProfile),
    [activeShortcutProfile]
  );
  const applyActiveShortcutProfile = React.useCallback(() => {
    const profileName = String(activeShortcutProfile || "").trim();
    const fromProfile = shortcutProfiles[profileName] || DEFAULT_SHORTCUT_BINDINGS;
    setShortcutBindings(normalizeShortcutBindings(fromProfile, DEFAULT_SHORTCUT_BINDINGS));
  }, [activeShortcutProfile, shortcutProfiles]);
  const resetShortcutBindingsToDefaults = React.useCallback(() => {
    setShortcutBindings(normalizeShortcutBindings(DEFAULT_SHORTCUT_BINDINGS, DEFAULT_SHORTCUT_BINDINGS));
  }, []);
  const saveCurrentShortcutProfile = React.useCallback(() => {
    const nextName = normalizeShortcutProfileName(shortcutProfileDraft);
    if (!nextName) return;
    const normalizedBindings = normalizeShortcutBindings(shortcutBindings, DEFAULT_SHORTCUT_BINDINGS);
    setShortcutProfiles((prev) => ({
      ...prev,
      [nextName]: normalizedBindings,
    }));
    setActiveShortcutProfile(nextName);
    setShortcutProfileDraft(nextName);
  }, [shortcutBindings, shortcutProfileDraft]);
  const deleteActiveShortcutProfile = React.useCallback(() => {
    const profileName = String(activeShortcutProfile || "").trim();
    if (!profileName) return;
    if (Object.prototype.hasOwnProperty.call(DEFAULT_SHORTCUT_PROFILES, profileName)) return;
    setShortcutProfiles((prev) => {
      if (!Object.prototype.hasOwnProperty.call(prev, profileName)) return prev;
      const next = { ...prev };
      delete next[profileName];
      return next;
    });
  }, [activeShortcutProfile]);
  const updateShortcutBinding = React.useCallback((actionId, rawToken) => {
    const id = String(actionId || "");
    if (!id) return;
    const token = normalizeShortcutToken(rawToken);
    if (!token) return;
    setShortcutBindings((prev) =>
      normalizeShortcutBindings(
        {
          ...prev,
          [id]: token,
        },
        prev
      )
    );
  }, []);
  const triggerShortcutImportFilePick = React.useCallback(() => {
    const input = shortcutImportFileInputRef.current;
    if (!input || typeof input.click !== "function") return;
    input.click();
  }, []);
  const handleShortcutImportFileChange = React.useCallback((evt) => {
    const file = evt?.target?.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const text = String(reader.result || "");
      setShortcutTransferText(text);
      setShortcutTransferStatus(`loaded file: ${String(file.name || "-")}`);
    };
    reader.onerror = () => {
      setShortcutTransferStatus(`failed to read file: ${String(file.name || "-")}`);
    };
    reader.readAsText(file);
    if (evt?.target) evt.target.value = "";
  }, []);
  const exportShortcutProfilesToJson = React.useCallback(() => {
    const jsonText = serializeShortcutProfileExportBundle(shortcutProfiles);
    setShortcutTransferText(jsonText);
    try {
      if (typeof window === "undefined" || typeof document === "undefined" || !window.URL) {
        setShortcutTransferStatus("exported to text buffer");
        return;
      }
      const blob = new Blob([jsonText], { type: "application/json;charset=utf-8" });
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      const ts = new Date().toISOString().replace(/[:.]/g, "-");
      anchor.href = url;
      anchor.download = `graph_lab_shortcut_profiles_${ts}.json`;
      document.body.appendChild(anchor);
      anchor.click();
      document.body.removeChild(anchor);
      window.URL.revokeObjectURL(url);
      setShortcutTransferStatus(`exported ${Object.keys(shortcutProfiles).length} profile(s)`);
    } catch (_) {
      setShortcutTransferStatus("exported to text buffer (file download unavailable)");
    }
  }, [shortcutProfiles]);
  const copyShortcutProfilesJson = React.useCallback(async () => {
    const jsonText = serializeShortcutProfileExportBundle(shortcutProfiles);
    setShortcutTransferText(jsonText);
    try {
      if (typeof navigator !== "undefined" && navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(jsonText);
        setShortcutTransferStatus(`copied ${Object.keys(shortcutProfiles).length} profile(s) to clipboard`);
        return;
      }
      setShortcutTransferStatus("clipboard unavailable; copy from text buffer");
    } catch (_) {
      setShortcutTransferStatus("clipboard write failed; copy from text buffer");
    }
  }, [shortcutProfiles]);
  const importShortcutProfilesFromText = React.useCallback(() => {
    try {
      const imported = parseShortcutProfileImportText(shortcutTransferText);
      const names = Object.keys(imported);
      setShortcutProfiles((prev) => ({
        ...prev,
        ...imported,
      }));
      setShortcutTransferStatus(`imported ${names.length} profile(s)`);
      if (!activeShortcutProfile && names.length > 0) {
        setActiveShortcutProfile(String(names[0]));
      }
      if (names.length > 0) {
        setShortcutProfileDraft(String(names[0]));
      }
    } catch (err) {
      setShortcutTransferStatus(`import failed: ${String(err?.message || "invalid payload")}`);
    }
  }, [activeShortcutProfile, shortcutTransferText]);
  const parsedQuickTelemetryDrilldownProfileImportPayload = React.useMemo(() => {
    const text = String(quickTelemetryDrilldownTransferText || "").trim();
    if (!text) {
      return {
        imported: null,
        error: "",
        empty: true,
      };
    }
    try {
      return {
        imported: parseQuickTelemetryDrilldownProfileImportText(text),
        error: "",
        empty: false,
      };
    } catch (err) {
      return {
        imported: null,
        error: String(err?.message || "parse error"),
        empty: false,
      };
    }
  }, [quickTelemetryDrilldownTransferText]);
  const quickTelemetryDrilldownImportRows = React.useMemo(() => {
    const imported = parsedQuickTelemetryDrilldownProfileImportPayload.imported;
    if (!imported || typeof imported !== "object") return [];
    return Object.keys(imported)
      .sort((a, b) => String(a).localeCompare(String(b)))
      .map((name) => {
        const hasExisting = Object.prototype.hasOwnProperty.call(quickTelemetryDrilldownProfiles, name);
        const fallback = DEFAULT_FILTER_IMPORT_AUDIT_QUICK_TELEMETRY_DRILLDOWN_PROFILES[name]
          || DEFAULT_FILTER_IMPORT_AUDIT_QUICK_TELEMETRY_DRILLDOWN_PROFILES.default;
        const importedProfile = normalizeQuickTelemetryDrilldownProfile(imported[name], fallback);
        if (!hasExisting) {
          return { name, conflict: "new", changed: true };
        }
        const existingFallback = DEFAULT_FILTER_IMPORT_AUDIT_QUICK_TELEMETRY_DRILLDOWN_PROFILES[name]
          || DEFAULT_FILTER_IMPORT_AUDIT_QUICK_TELEMETRY_DRILLDOWN_PROFILES.default;
        const existingProfile = normalizeQuickTelemetryDrilldownProfile(
          quickTelemetryDrilldownProfiles[name],
          existingFallback
        );
        const changed = JSON.stringify(existingProfile) !== JSON.stringify(importedProfile);
        if (Object.prototype.hasOwnProperty.call(DEFAULT_FILTER_IMPORT_AUDIT_QUICK_TELEMETRY_DRILLDOWN_PROFILES, name)) {
          return { name, conflict: "overwrite_builtin", changed };
        }
        return { name, conflict: "overwrite_custom", changed };
      });
  }, [parsedQuickTelemetryDrilldownProfileImportPayload.imported, quickTelemetryDrilldownProfiles]);
  const quickTelemetryDrilldownImportNamesSignature = React.useMemo(
    () => quickTelemetryDrilldownImportRows.map((row) => row.name).join("|"),
    [quickTelemetryDrilldownImportRows]
  );
  React.useEffect(() => {
    if (!quickTelemetryDrilldownImportNamesSignature) {
      setQuickTelemetryDrilldownImportSelection({});
      return;
    }
    setQuickTelemetryDrilldownImportSelection((prev) => {
      const base = prev && typeof prev === "object" && !Array.isArray(prev) ? prev : {};
      const next = {};
      quickTelemetryDrilldownImportRows.forEach((row) => {
        const name = String(row.name || "");
        if (!name) return;
        if (Object.prototype.hasOwnProperty.call(base, name)) {
          next[name] = Boolean(base[name]);
          return;
        }
        next[name] = true;
      });
      return next;
    });
  }, [quickTelemetryDrilldownImportNamesSignature, quickTelemetryDrilldownImportRows]);
  const quickTelemetryDrilldownImportNameQueryNormalized = React.useMemo(
    () => String(quickTelemetryDrilldownImportNameQuery || "").trim().toLowerCase(),
    [quickTelemetryDrilldownImportNameQuery]
  );
  const quickTelemetryDrilldownImportRowsScope = React.useMemo(() => {
    if (!quickTelemetryDrilldownImportConflictOnlyChecked) return quickTelemetryDrilldownImportRows;
    return quickTelemetryDrilldownImportRows.filter((row) => row.conflict !== "new");
  }, [quickTelemetryDrilldownImportConflictOnlyChecked, quickTelemetryDrilldownImportRows]);
  const quickTelemetryDrilldownImportRowsByQuery = React.useMemo(() => {
    if (!quickTelemetryDrilldownImportNameQueryNormalized) return quickTelemetryDrilldownImportRowsScope;
    return quickTelemetryDrilldownImportRowsScope.filter((row) =>
      String(row?.name || "").toLowerCase().includes(quickTelemetryDrilldownImportNameQueryNormalized)
    );
  }, [quickTelemetryDrilldownImportNameQueryNormalized, quickTelemetryDrilldownImportRowsScope]);
  const quickTelemetryDrilldownImportConflictFilterCounts = React.useMemo(() => {
    const baseRows = quickTelemetryDrilldownImportRowsByQuery;
    const counts = {};
    QUICK_TELEMETRY_DRILLDOWN_IMPORT_CONFLICT_FILTER_OPTIONS.forEach((opt) => {
      const oid = String(opt?.id || "");
      if (!oid) return;
      counts[oid] = baseRows.filter((row) => matchQuickTelemetryDrilldownImportConflictFilter(row, oid)).length;
    });
    if (!Object.prototype.hasOwnProperty.call(counts, "all")) {
      counts.all = baseRows.length;
    }
    return counts;
  }, [quickTelemetryDrilldownImportRowsByQuery]);
  const quickTelemetryDrilldownImportFilterPresetCounts = React.useMemo(() => {
    const counts = {};
    QUICK_TELEMETRY_DRILLDOWN_IMPORT_FILTER_PRESETS.forEach((preset) => {
      const pid = String(preset?.id || "");
      if (!pid) return;
      const rowsScope = Boolean(preset?.conflict_only)
        ? quickTelemetryDrilldownImportRows.filter((row) => String(row?.conflict || "") !== "new")
        : quickTelemetryDrilldownImportRows;
      const q = String(preset?.name_query || "").trim().toLowerCase();
      const rowsByQuery = q
        ? rowsScope.filter((row) => String(row?.name || "").toLowerCase().includes(q))
        : rowsScope;
      const conflictFilter = normalizeQuickTelemetryDrilldownImportConflictFilter(preset?.conflict_filter || "all");
      counts[pid] = rowsByQuery.filter((row) =>
        matchQuickTelemetryDrilldownImportConflictFilter(row, conflictFilter)
      ).length;
    });
    return counts;
  }, [quickTelemetryDrilldownImportRows]);
  const activeQuickTelemetryDrilldownImportFilterPresetId = React.useMemo(() => {
    const hit = QUICK_TELEMETRY_DRILLDOWN_IMPORT_FILTER_PRESETS.find((preset) =>
      Boolean(preset?.conflict_only) === Boolean(quickTelemetryDrilldownImportConflictOnlyChecked)
      && normalizeQuickTelemetryDrilldownImportConflictFilter(preset?.conflict_filter || "all")
        === normalizeQuickTelemetryDrilldownImportConflictFilter(quickTelemetryDrilldownImportConflictFilter)
      && String(preset?.name_query || "").trim().toLowerCase() === quickTelemetryDrilldownImportNameQueryNormalized
    );
    return hit ? String(hit.id || "all") : "custom";
  }, [
    quickTelemetryDrilldownImportConflictFilter,
    quickTelemetryDrilldownImportConflictOnlyChecked,
    quickTelemetryDrilldownImportNameQueryNormalized,
  ]);
  const quickTelemetryDrilldownImportFilterBundleHint = React.useMemo(
    () => `filter bundle active:${activeQuickTelemetryDrilldownImportFilterPresetId} conflict-only:${quickTelemetryDrilldownImportConflictOnlyChecked ? "on" : "off"} conflict:${quickTelemetryDrilldownImportConflictFilter} query:${quickTelemetryDrilldownImportNameQueryNormalized || "-"} mode:${quickTelemetryDrilldownImportFilterBundleMode}`,
    [
      activeQuickTelemetryDrilldownImportFilterPresetId,
      quickTelemetryDrilldownImportConflictFilter,
      quickTelemetryDrilldownImportConflictOnlyChecked,
      quickTelemetryDrilldownImportNameQueryNormalized,
      quickTelemetryDrilldownImportFilterBundleMode,
    ]
  );
  const parsedQuickTelemetryDrilldownImportFilterBundlePayload = React.useMemo(() => {
    const text = String(quickTelemetryDrilldownImportFilterBundleText || "").trim();
    if (!text) {
      return {
        bundle: null,
        error: "",
        empty: true,
      };
    }
    try {
      return {
        bundle: parseQuickTelemetryDrilldownImportFilterBundleText(text, {
          mode: quickTelemetryDrilldownImportFilterBundleMode,
        }),
        error: "",
        empty: false,
      };
    } catch (err) {
      return {
        bundle: null,
        error: String(err?.message || "parse error"),
        empty: false,
      };
    }
  }, [
    quickTelemetryDrilldownImportFilterBundleText,
    quickTelemetryDrilldownImportFilterBundleMode,
  ]);
  const quickTelemetryDrilldownImportFilterBundleSchemaHint = React.useMemo(
    () =>
      `filter bundle expects kind=${QUICK_TELEMETRY_DRILLDOWN_IMPORT_FILTER_BUNDLE_KIND}, schema=${QUICK_TELEMETRY_DRILLDOWN_IMPORT_FILTER_BUNDLE_SCHEMA_VERSION}, mode=${quickTelemetryDrilldownImportFilterBundleMode}`,
    [quickTelemetryDrilldownImportFilterBundleMode]
  );
  const quickTelemetryDrilldownImportFilterBundleInvalidGuidance = React.useMemo(() => {
    if (parsedQuickTelemetryDrilldownImportFilterBundlePayload.empty) return "";
    const err = String(parsedQuickTelemetryDrilldownImportFilterBundlePayload.error || "");
    if (!err) return "";
    if (err.includes("unexpected kind")) {
      return `guidance: set kind=${QUICK_TELEMETRY_DRILLDOWN_IMPORT_FILTER_BUNDLE_KIND}`;
    }
    if (err.includes("unsupported schema_version")) {
      return `guidance: set schema_version=${QUICK_TELEMETRY_DRILLDOWN_IMPORT_FILTER_BUNDLE_SCHEMA_VERSION}`;
    }
    if (err.includes("strict mode requires filter_bundle wrapper")) {
      return "guidance: strict mode requires wrapped payload ({\"filter_bundle\": {...}}); use Wrap Legacy -> Strict helper";
    }
    if (err.includes("strict mode requires kind=")) {
      return `guidance: strict mode requires kind=${QUICK_TELEMETRY_DRILLDOWN_IMPORT_FILTER_BUNDLE_KIND}`;
    }
    if (err.includes("strict mode requires schema_version=")) {
      return `guidance: strict mode requires schema_version=${QUICK_TELEMETRY_DRILLDOWN_IMPORT_FILTER_BUNDLE_SCHEMA_VERSION}`;
    }
    if (err.includes("invalid JSON")) {
      return "guidance: paste valid JSON object";
    }
    if (err.includes("import root must be object")) {
      return "guidance: JSON root must be object or {\"filter_bundle\": {...}}";
    }
    if (err.includes("empty import payload")) {
      return "guidance: paste exported filter bundle JSON";
    }
    return "guidance: use Export Filter Bundle from this panel";
  }, [
    parsedQuickTelemetryDrilldownImportFilterBundlePayload.empty,
    parsedQuickTelemetryDrilldownImportFilterBundlePayload.error,
  ]);
  const quickTelemetryDrilldownImportFilterBundleStrictWrapCandidate = React.useMemo(() => {
    if (quickTelemetryDrilldownImportFilterBundleMode !== "strict") {
      return { available: false, reason: "mode_not_strict", wrapped_text: "" };
    }
    return buildQuickTelemetryDrilldownImportFilterBundleStrictWrapCandidate(
      quickTelemetryDrilldownImportFilterBundleText
    );
  }, [
    quickTelemetryDrilldownImportFilterBundleMode,
    quickTelemetryDrilldownImportFilterBundleText,
  ]);
  const quickTelemetryDrilldownImportFilterBundleStrictWrapHint = React.useMemo(() => {
    if (quickTelemetryDrilldownImportFilterBundleMode !== "strict") {
      return "rollout helper: compat mode keeps legacy bare-object payload support";
    }
    if (quickTelemetryDrilldownImportFilterBundleStrictWrapCandidate.available) {
      return "rollout helper: legacy bare-object payload detected, ready to auto-wrap for strict mode";
    }
    const reason = String(quickTelemetryDrilldownImportFilterBundleStrictWrapCandidate.reason || "");
    if (reason === "already_wrapped") {
      return "rollout helper: payload already wrapped for strict mode";
    }
    if (reason === "invalid_json") {
      return "rollout helper: payload must be valid JSON before auto-wrap";
    }
    if (reason === "import_root_not_object") {
      return "rollout helper: payload root must be object for auto-wrap";
    }
    if (reason === "empty") {
      return "rollout helper: paste legacy payload to generate strict wrap preview";
    }
    return "rollout helper: strict migration helper ready";
  }, [
    quickTelemetryDrilldownImportFilterBundleMode,
    quickTelemetryDrilldownImportFilterBundleStrictWrapCandidate.available,
    quickTelemetryDrilldownImportFilterBundleStrictWrapCandidate.reason,
  ]);
  const quickTelemetryDrilldownImportFilterBundleStrictWrapPreview = React.useMemo(() => {
    if (!quickTelemetryDrilldownImportFilterBundleStrictWrapCandidate.available) {
      return "";
    }
    return String(quickTelemetryDrilldownImportFilterBundleStrictWrapCandidate.wrapped_text || "");
  }, [
    quickTelemetryDrilldownImportFilterBundleStrictWrapCandidate.available,
    quickTelemetryDrilldownImportFilterBundleStrictWrapCandidate.wrapped_text,
  ]);
  const bumpQuickTelemetryDrilldownStrictAdoptionSignals = React.useCallback((delta) => {
    const src = delta && typeof delta === "object" && !Array.isArray(delta) ? delta : {};
    setQuickTelemetryDrilldownStrictAdoptionSignals((prev) => {
      const base = normalizeQuickTelemetryDrilldownStrictAdoptionSignals(prev, null);
      const addAttempt = Number.isFinite(Number(src.attempt_count)) ? Math.floor(Number(src.attempt_count)) : 0;
      const addSuccess = Number.isFinite(Number(src.success_count)) ? Math.floor(Number(src.success_count)) : 0;
      const addLegacyWrapUse = Number.isFinite(Number(src.legacy_wrap_use_count))
        ? Math.floor(Number(src.legacy_wrap_use_count))
        : 0;
      const addLegacyParseBlock = Number.isFinite(Number(src.legacy_parse_block_count))
        ? Math.floor(Number(src.legacy_parse_block_count))
        : 0;
      const touched = addAttempt !== 0 || addSuccess !== 0 || addLegacyWrapUse !== 0 || addLegacyParseBlock !== 0;
      return normalizeQuickTelemetryDrilldownStrictAdoptionSignals({
        attempt_count: Math.max(0, Number(base.attempt_count || 0) + addAttempt),
        success_count: Math.max(0, Number(base.success_count || 0) + addSuccess),
        legacy_wrap_use_count: Math.max(0, Number(base.legacy_wrap_use_count || 0) + addLegacyWrapUse),
        legacy_parse_block_count: Math.max(0, Number(base.legacy_parse_block_count || 0) + addLegacyParseBlock),
        last_event_ts_ms: touched ? Date.now() : Number(base.last_event_ts_ms || 0),
      }, base);
    });
  }, []);
  const resetQuickTelemetryDrilldownStrictAdoptionSignals = React.useCallback(() => {
    setQuickTelemetryDrilldownStrictAdoptionSignals(
      normalizeQuickTelemetryDrilldownStrictAdoptionSignals(
        CONTRACT_OVERLAY_DEFAULT_PREFS.quickTelemetryDrilldownStrictAdoptionSignals,
        null
      )
    );
    setQuickTelemetryDrilldownStrictAdoptionGateStatus("strict adoption gate signals reset");
    setQuickTelemetryDrilldownStrictCutoverStatus("");
    setQuickTelemetryDrilldownStrictCutoverLedgerStatus("");
    setQuickTelemetryDrilldownStrictRollbackDrillStatus("");
    setQuickTelemetryDrilldownStrictRollbackPackageStatus("");
    setQuickTelemetryDrilldownStrictRollbackPackageReplayText("");
    setQuickTelemetryDrilldownStrictRollbackPackageDeltaConfirmChecked(false);
    setQuickTelemetryDrilldownStrictRollbackPackageOverrideReasonText("");
    setQuickTelemetryDrilldownStrictRollbackPackageOverrideLogStatus("");
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleStatus("");
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus("");
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydratedSnapshot(null);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmChecked(false);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffImportText("");
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleImportText("");
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmChecked(false);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmArmedAtMs(0);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmTickMs(0);
  }, []);
  const quickTelemetryDrilldownStrictAdoptionChecklist = React.useMemo(() => {
    return buildQuickTelemetryDrilldownStrictAdoptionChecklist(
      quickTelemetryDrilldownStrictAdoptionSignals,
      quickTelemetryDrilldownImportFilterBundleMode
    );
  }, [
    quickTelemetryDrilldownImportFilterBundleMode,
    quickTelemetryDrilldownStrictAdoptionSignals,
  ]);
  const quickTelemetryDrilldownStrictAdoptionChecklistHint = React.useMemo(() => {
    const row = quickTelemetryDrilldownStrictAdoptionChecklist;
    const status = row.ready ? "READY" : "HOLD";
    return `strict default-switch checklist: ${status} (${row.pass_count}/${row.item_count})`;
  }, [quickTelemetryDrilldownStrictAdoptionChecklist]);
  const quickTelemetryDrilldownStrictAdoptionChecklistPreview = React.useMemo(() => {
    const row = quickTelemetryDrilldownStrictAdoptionChecklist;
    const sig = row.signals || {};
    const itemTokens = row.items.map((x) => `${x.ok ? "ok" : "hold"}:${x.id}`).join(", ");
    return [
      `attempts=${Number(sig.attempt_count || 0)}`,
      `success=${Number(sig.success_count || 0)}`,
      `legacy_wrap_use=${Number(sig.legacy_wrap_use_count || 0)}`,
      `legacy_parse_block=${Number(sig.legacy_parse_block_count || 0)}`,
      `last_event=${String(row.last_event_iso || "-")}`,
      itemTokens,
    ].join(" | ");
  }, [quickTelemetryDrilldownStrictAdoptionChecklist]);
  const quickTelemetryDrilldownStrictCutoverHint = React.useMemo(() => {
    const row = quickTelemetryDrilldownStrictAdoptionChecklist;
    const modeStrict = quickTelemetryDrilldownImportFilterBundleMode === "strict";
    if (row.ready && modeStrict) {
      return "cutover helper: strict default is active and checklist is READY";
    }
    if (row.ready) {
      return "cutover helper: checklist READY, apply strict default when team is ready";
    }
    if (modeStrict) {
      return "cutover helper: strict mode active but checklist is HOLD";
    }
    return "cutover helper: compat mode active, strict default cutover not applied";
  }, [
    quickTelemetryDrilldownImportFilterBundleMode,
    quickTelemetryDrilldownStrictAdoptionChecklist,
  ]);
  const quickTelemetryDrilldownCompatFallbackReminder = React.useMemo(() => {
    if (quickTelemetryDrilldownImportFilterBundleMode === "strict") {
      return "compat fallback reminder: if strict import fails on legacy payload, click 'Switch to Compat Fallback'.";
    }
    return "compat fallback reminder: compat mode is active (legacy payload support on).";
  }, [quickTelemetryDrilldownImportFilterBundleMode]);
  const quickTelemetryDrilldownStrictCutoverLedgerRows = React.useMemo(
    () => buildQuickTelemetryDrilldownStrictCutoverLedgerBundle(quickTelemetryDrilldownStrictCutoverLedger).entries,
    [quickTelemetryDrilldownStrictCutoverLedger]
  );
  const quickTelemetryDrilldownStrictCutoverTimelineHint = React.useMemo(() => {
    if (quickTelemetryDrilldownStrictCutoverLedgerRows.length === 0) {
      return `cutover timeline: 0/${QUICK_TELEMETRY_STRICT_CUTOVER_LEDGER_LIMIT} events`;
    }
    const latest = quickTelemetryDrilldownStrictCutoverLedgerRows[0] || {};
    return [
      `cutover timeline: ${quickTelemetryDrilldownStrictCutoverLedgerRows.length}/${QUICK_TELEMETRY_STRICT_CUTOVER_LEDGER_LIMIT} events`,
      `latest ${String(latest.event_id || "-")}`,
      `mode ${String(latest.import_mode || "-")}`,
      `checklist ${String(latest.checklist_status || "HOLD")}`,
    ].join(", ");
  }, [quickTelemetryDrilldownStrictCutoverLedgerRows]);
  const quickTelemetryDrilldownStrictCutoverTimelinePreview = React.useMemo(() => {
    if (quickTelemetryDrilldownStrictCutoverLedgerRows.length === 0) {
      return "timeline preview: no strict cutover events yet";
    }
    return quickTelemetryDrilldownStrictCutoverLedgerRows
      .map((row, idx) => [
        `#${idx + 1}`,
        String(row.timestamp_iso || "-"),
        String(row.event_id || "-"),
        `mode=${String(row.import_mode || "-")}`,
        `checklist=${String(row.checklist_status || "HOLD")}(${Number(row.pass_count || 0)}/${Number(row.item_count || 0)})`,
        `attempts=${Number(row.attempt_count || 0)}`,
        `success=${Number(row.success_count || 0)}`,
        `legacy_wrap=${Number(row.legacy_wrap_use_count || 0)}`,
        `legacy_parse_block=${Number(row.legacy_parse_block_count || 0)}`,
      ].join(" | "))
      .join("\n");
  }, [quickTelemetryDrilldownStrictCutoverLedgerRows]);
  const quickTelemetryDrilldownImportFilterBundlePreview = React.useMemo(() => {
    if (parsedQuickTelemetryDrilldownImportFilterBundlePayload.empty) {
      return "filter bundle preview: waiting for JSON payload";
    }
    if (parsedQuickTelemetryDrilldownImportFilterBundlePayload.error) {
      return `filter bundle preview: invalid payload (${parsedQuickTelemetryDrilldownImportFilterBundlePayload.error})`;
    }
    const bundle = parsedQuickTelemetryDrilldownImportFilterBundlePayload.bundle || {};
    return [
      `filter bundle preview: preset ${String(bundle.preset_id || "custom")}`,
      `conflict-only ${Boolean(bundle.conflict_only) ? "on" : "off"}`,
      `conflict ${String(bundle.conflict_filter || "all")}`,
      `query ${String(bundle.name_query || "").trim() || "-"}`,
      `row-cap ${Number(bundle.row_cap || 0)}`,
      `kind ${String(bundle.kind || QUICK_TELEMETRY_DRILLDOWN_IMPORT_FILTER_BUNDLE_KIND)}`,
      `schema ${Number(bundle.schema_version || QUICK_TELEMETRY_DRILLDOWN_IMPORT_FILTER_BUNDLE_SCHEMA_VERSION)}`,
      `wrapper ${Boolean(bundle.has_wrapper) ? "on" : "off"}`,
      `mode ${String(bundle.import_mode || quickTelemetryDrilldownImportFilterBundleMode)}`,
    ].join(", ");
  }, [
    quickTelemetryDrilldownImportFilterBundleMode,
    parsedQuickTelemetryDrilldownImportFilterBundlePayload.bundle,
    parsedQuickTelemetryDrilldownImportFilterBundlePayload.empty,
    parsedQuickTelemetryDrilldownImportFilterBundlePayload.error,
  ]);
  const quickTelemetryDrilldownImportRowsVisible = React.useMemo(
    () =>
      quickTelemetryDrilldownImportRowsByQuery.filter((row) =>
        matchQuickTelemetryDrilldownImportConflictFilter(row, quickTelemetryDrilldownImportConflictFilter)
      ),
    [quickTelemetryDrilldownImportConflictFilter, quickTelemetryDrilldownImportRowsByQuery]
  );
  const quickTelemetryDrilldownImportRowCap = React.useMemo(
    () => clampInteger(quickTelemetryDrilldownImportRowCapText, 4, 200, 16),
    [quickTelemetryDrilldownImportRowCapText]
  );
  React.useEffect(() => {
    setQuickTelemetryDrilldownImportRowOffset(0);
  }, [
    quickTelemetryDrilldownImportConflictFilter,
    quickTelemetryDrilldownImportConflictOnlyChecked,
    quickTelemetryDrilldownImportNameQueryNormalized,
    quickTelemetryDrilldownImportNamesSignature,
    quickTelemetryDrilldownImportRowCap,
  ]);
  const quickTelemetryDrilldownImportMaxOffset = React.useMemo(
    () => Math.max(0, Number(quickTelemetryDrilldownImportRowsVisible.length || 0) - quickTelemetryDrilldownImportRowCap),
    [quickTelemetryDrilldownImportRowCap, quickTelemetryDrilldownImportRowsVisible.length]
  );
  React.useEffect(() => {
    if (quickTelemetryDrilldownImportRowOffset > quickTelemetryDrilldownImportMaxOffset) {
      setQuickTelemetryDrilldownImportRowOffset(quickTelemetryDrilldownImportMaxOffset);
    }
  }, [quickTelemetryDrilldownImportMaxOffset, quickTelemetryDrilldownImportRowOffset]);
  const quickTelemetryDrilldownImportRowEnd = Math.min(
    quickTelemetryDrilldownImportRowsVisible.length,
    quickTelemetryDrilldownImportRowOffset + quickTelemetryDrilldownImportRowCap
  );
  const quickTelemetryDrilldownImportRowsPage = React.useMemo(
    () => quickTelemetryDrilldownImportRowsVisible.slice(
      quickTelemetryDrilldownImportRowOffset,
      quickTelemetryDrilldownImportRowEnd
    ),
    [
      quickTelemetryDrilldownImportRowEnd,
      quickTelemetryDrilldownImportRowOffset,
      quickTelemetryDrilldownImportRowsVisible,
    ]
  );
  const quickTelemetryDrilldownImportSelectionRows = React.useMemo(
    () => quickTelemetryDrilldownImportRowsVisible,
    [quickTelemetryDrilldownImportRowsVisible]
  );
  const selectedQuickTelemetryDrilldownImportNames = React.useMemo(
    () =>
      quickTelemetryDrilldownImportSelectionRows
        .map((row) => String(row.name || ""))
        .filter((name) => name.length > 0 && Boolean(quickTelemetryDrilldownImportSelection[name])),
    [quickTelemetryDrilldownImportSelectionRows, quickTelemetryDrilldownImportSelection]
  );
  const selectedQuickTelemetryDrilldownImportRows = React.useMemo(() => {
    const selectedSet = new Set(selectedQuickTelemetryDrilldownImportNames);
    return quickTelemetryDrilldownImportRows.filter((row) => selectedSet.has(String(row.name || "")));
  }, [quickTelemetryDrilldownImportRows, selectedQuickTelemetryDrilldownImportNames]);
  const quickTelemetryDrilldownImportSelectedAllCount = React.useMemo(
    () => quickTelemetryDrilldownImportRows.filter((row) => Boolean(quickTelemetryDrilldownImportSelection[row.name])).length,
    [quickTelemetryDrilldownImportRows, quickTelemetryDrilldownImportSelection]
  );
  const quickTelemetryDrilldownImportSelectedPageCount = React.useMemo(
    () => quickTelemetryDrilldownImportRowsPage.filter((row) => Boolean(quickTelemetryDrilldownImportSelection[row.name])).length,
    [quickTelemetryDrilldownImportRowsPage, quickTelemetryDrilldownImportSelection]
  );
  const quickTelemetryDrilldownImportHiddenSelectionCount = Math.max(
    0,
    quickTelemetryDrilldownImportSelectedAllCount - selectedQuickTelemetryDrilldownImportNames.length
  );
  const quickTelemetryDrilldownImportSelectedOffPageCount = Math.max(
    0,
    selectedQuickTelemetryDrilldownImportNames.length - quickTelemetryDrilldownImportSelectedPageCount
  );
  const quickTelemetryDrilldownImportFilterBundleIsDefault = React.useMemo(
    () =>
      !quickTelemetryDrilldownImportNameQueryNormalized
      && normalizeQuickTelemetryDrilldownImportConflictFilter(quickTelemetryDrilldownImportConflictFilter)
        === normalizeQuickTelemetryDrilldownImportConflictFilter(
          CONTRACT_OVERLAY_DEFAULT_PREFS.quickTelemetryDrilldownImportConflictFilter
        )
      && Boolean(quickTelemetryDrilldownImportConflictOnlyChecked)
        === Boolean(CONTRACT_OVERLAY_DEFAULT_PREFS.quickTelemetryDrilldownImportConflictOnly)
      && quickTelemetryDrilldownImportRowOffset <= 0,
    [
      quickTelemetryDrilldownImportConflictFilter,
      quickTelemetryDrilldownImportConflictOnlyChecked,
      quickTelemetryDrilldownImportNameQueryNormalized,
      quickTelemetryDrilldownImportRowOffset,
    ]
  );
  const quickTelemetryDrilldownImportSafetyBundleIsDefault = React.useMemo(
    () =>
      quickTelemetryDrilldownImportFilterBundleIsDefault
      && quickTelemetryDrilldownImportSelectedAllCount === 0
      && !quickTelemetryDrilldownImportOverwriteConfirmChecked,
    [
      quickTelemetryDrilldownImportFilterBundleIsDefault,
      quickTelemetryDrilldownImportOverwriteConfirmChecked,
      quickTelemetryDrilldownImportSelectedAllCount,
    ]
  );
  const quickTelemetryDrilldownImportSelectionSafetyHint = React.useMemo(() => {
    if (parsedQuickTelemetryDrilldownProfileImportPayload.empty) {
      return "selection safety: waiting for JSON payload";
    }
    if (parsedQuickTelemetryDrilldownProfileImportPayload.error) {
      return `selection safety: invalid payload (${parsedQuickTelemetryDrilldownProfileImportPayload.error})`;
    }
    const pageStart = quickTelemetryDrilldownImportRowsVisible.length === 0
      ? 0
      : quickTelemetryDrilldownImportRowOffset + 1;
    const pageToken = `${pageStart}-${quickTelemetryDrilldownImportRowEnd}/${quickTelemetryDrilldownImportRowsVisible.length}`;
    const tokens = [
      `selection scope ${selectedQuickTelemetryDrilldownImportNames.length}/${quickTelemetryDrilldownImportSelectionRows.length}`,
      `page ${quickTelemetryDrilldownImportSelectedPageCount}/${quickTelemetryDrilldownImportRowsPage.length} (${pageToken})`,
      `filter ${quickTelemetryDrilldownImportConflictFilter}`,
      `query ${quickTelemetryDrilldownImportNameQueryNormalized || "-"}`,
    ];
    if (quickTelemetryDrilldownImportSelectedOffPageCount > 0) {
      tokens.push(`off-page ${quickTelemetryDrilldownImportSelectedOffPageCount}`);
    }
    if (quickTelemetryDrilldownImportHiddenSelectionCount > 0) {
      tokens.push(`hidden-by-view ${quickTelemetryDrilldownImportHiddenSelectionCount}`);
    }
    return tokens.join(", ");
  }, [
    parsedQuickTelemetryDrilldownProfileImportPayload.empty,
    parsedQuickTelemetryDrilldownProfileImportPayload.error,
    quickTelemetryDrilldownImportHiddenSelectionCount,
    quickTelemetryDrilldownImportConflictFilter,
    quickTelemetryDrilldownImportNameQueryNormalized,
    quickTelemetryDrilldownImportRowEnd,
    quickTelemetryDrilldownImportRowOffset,
    quickTelemetryDrilldownImportRowsPage.length,
    quickTelemetryDrilldownImportRowsVisible.length,
    quickTelemetryDrilldownImportSelectedOffPageCount,
    quickTelemetryDrilldownImportSelectedPageCount,
    quickTelemetryDrilldownImportSelectionRows.length,
    selectedQuickTelemetryDrilldownImportNames.length,
  ]);
  const quickTelemetryDrilldownImportHasChangedOverwrite = React.useMemo(
    () => selectedQuickTelemetryDrilldownImportRows.some((row) => row.conflict !== "new" && Boolean(row.changed)),
    [selectedQuickTelemetryDrilldownImportRows]
  );
  const quickTelemetryDrilldownImportPreview = React.useMemo(() => {
    if (parsedQuickTelemetryDrilldownProfileImportPayload.empty) {
      return "drilldown profile preview: waiting for JSON payload";
    }
    if (parsedQuickTelemetryDrilldownProfileImportPayload.error) {
      return `drilldown profile preview: invalid payload (${parsedQuickTelemetryDrilldownProfileImportPayload.error})`;
    }
    let newCount = 0;
    let overwriteCount = 0;
    let changedOverwrite = 0;
    let changedBuiltinOverwrite = 0;
    let unchangedCount = 0;
    selectedQuickTelemetryDrilldownImportRows.forEach((row) => {
      if (row.conflict === "new") {
        newCount += 1;
        return;
      }
      overwriteCount += 1;
      if (row.changed) {
        changedOverwrite += 1;
        if (row.conflict === "overwrite_builtin") changedBuiltinOverwrite += 1;
      } else {
        unchangedCount += 1;
      }
    });
    const viewToken = quickTelemetryDrilldownImportConflictOnlyChecked ? "conflict_only" : "all";
    if (selectedQuickTelemetryDrilldownImportNames.length === 0) {
      return [
        `drilldown profile preview: total ${quickTelemetryDrilldownImportRows.length}`,
        `visible ${quickTelemetryDrilldownImportRowsVisible.length}`,
        `page ${quickTelemetryDrilldownImportRowsVisible.length === 0 ? 0 : quickTelemetryDrilldownImportRowOffset + 1}-${quickTelemetryDrilldownImportRowEnd}/${quickTelemetryDrilldownImportRowsVisible.length}`,
        "selected 0",
        `filter ${quickTelemetryDrilldownImportConflictFilter}`,
        `query ${quickTelemetryDrilldownImportNameQueryNormalized || "-"}`,
        `view ${viewToken} (select profiles to import)`,
      ].join(", ");
    }
    const builtinTag = changedBuiltinOverwrite > 0 ? `, built-in overwrite ${changedBuiltinOverwrite}` : "";
    return [
      `drilldown profile preview: total ${quickTelemetryDrilldownImportRows.length}`,
      `visible ${quickTelemetryDrilldownImportRowsVisible.length}`,
      `selected ${selectedQuickTelemetryDrilldownImportNames.length}`,
      `page ${quickTelemetryDrilldownImportRowsVisible.length === 0 ? 0 : quickTelemetryDrilldownImportRowOffset + 1}-${quickTelemetryDrilldownImportRowEnd}/${quickTelemetryDrilldownImportRowsVisible.length}`,
      `new ${newCount}`,
      `overwrite ${overwriteCount}`,
      `changed ${changedOverwrite}${builtinTag}`,
      `unchanged ${unchangedCount}`,
      `filter ${quickTelemetryDrilldownImportConflictFilter}`,
      `query ${quickTelemetryDrilldownImportNameQueryNormalized || "-"}`,
      `view ${viewToken}`,
    ].join(", ");
  }, [
    parsedQuickTelemetryDrilldownProfileImportPayload.empty,
    parsedQuickTelemetryDrilldownProfileImportPayload.error,
    quickTelemetryDrilldownImportConflictFilter,
    quickTelemetryDrilldownImportConflictOnlyChecked,
    quickTelemetryDrilldownImportNameQueryNormalized,
    quickTelemetryDrilldownImportRowEnd,
    quickTelemetryDrilldownImportRowOffset,
    quickTelemetryDrilldownImportRows,
    quickTelemetryDrilldownImportRowsVisible.length,
    selectedQuickTelemetryDrilldownImportNames.length,
    selectedQuickTelemetryDrilldownImportRows,
  ]);
  const quickTelemetryDrilldownImportPreviewRows = React.useMemo(
    () => quickTelemetryDrilldownImportRowsPage,
    [quickTelemetryDrilldownImportRowsPage]
  );
  const quickTelemetryDrilldownImportRollbackHint = React.useMemo(() => {
    const snap = quickTelemetryDrilldownImportUndoSnapshot;
    if (!snap || typeof snap !== "object") return "rollback: no import snapshot";
    return `rollback: undo available (${String(snap.imported_at_iso || "-")})`;
  }, [quickTelemetryDrilldownImportUndoSnapshot]);
  React.useEffect(() => {
    if (!quickTelemetryDrilldownImportOverwriteConfirmChecked) return;
    if (quickTelemetryDrilldownImportHasChangedOverwrite) return;
    setQuickTelemetryDrilldownImportOverwriteConfirmChecked(false);
  }, [
    quickTelemetryDrilldownImportHasChangedOverwrite,
    quickTelemetryDrilldownImportOverwriteConfirmChecked,
  ]);
  const applyQuickTelemetryDrilldownImportFilterPreset = React.useCallback((presetId) => {
    const preset = resolveQuickTelemetryDrilldownImportFilterPreset(presetId);
    setQuickTelemetryDrilldownImportConflictOnlyChecked(Boolean(preset?.conflict_only));
    setQuickTelemetryDrilldownImportConflictFilter(
      normalizeQuickTelemetryDrilldownImportConflictFilter(preset?.conflict_filter || "all")
    );
    setQuickTelemetryDrilldownImportNameQuery(
      String(preset?.name_query || "").slice(0, QUICK_TELEMETRY_DRILLDOWN_IMPORT_NAME_QUERY_MAX)
    );
    setQuickTelemetryDrilldownImportRowOffset(0);
    setQuickTelemetryDrilldownTransferStatus(`import filter preset applied: ${String(preset?.id || "all")}`);
  }, []);
  const resetQuickTelemetryDrilldownImportFilterBundle = React.useCallback(() => {
    setQuickTelemetryDrilldownImportConflictOnlyChecked(
      Boolean(CONTRACT_OVERLAY_DEFAULT_PREFS.quickTelemetryDrilldownImportConflictOnly)
    );
    setQuickTelemetryDrilldownImportConflictFilter(
      normalizeQuickTelemetryDrilldownImportConflictFilter(
        CONTRACT_OVERLAY_DEFAULT_PREFS.quickTelemetryDrilldownImportConflictFilter
      )
    );
    setQuickTelemetryDrilldownImportNameQuery(
      String(CONTRACT_OVERLAY_DEFAULT_PREFS.quickTelemetryDrilldownImportNameQuery || "")
    );
    setQuickTelemetryDrilldownImportRowOffset(0);
    setQuickTelemetryDrilldownTransferStatus("import filter bundle reset");
  }, []);
  const resetQuickTelemetryDrilldownImportSafetyBundle = React.useCallback(() => {
    setQuickTelemetryDrilldownImportConflictOnlyChecked(
      Boolean(CONTRACT_OVERLAY_DEFAULT_PREFS.quickTelemetryDrilldownImportConflictOnly)
    );
    setQuickTelemetryDrilldownImportConflictFilter(
      normalizeQuickTelemetryDrilldownImportConflictFilter(
        CONTRACT_OVERLAY_DEFAULT_PREFS.quickTelemetryDrilldownImportConflictFilter
      )
    );
    setQuickTelemetryDrilldownImportNameQuery(
      String(CONTRACT_OVERLAY_DEFAULT_PREFS.quickTelemetryDrilldownImportNameQuery || "")
    );
    const nextSelection = {};
    quickTelemetryDrilldownImportRows.forEach((row) => {
      const name = String(row?.name || "");
      if (!name) return;
      nextSelection[name] = false;
    });
    setQuickTelemetryDrilldownImportSelection(nextSelection);
    setQuickTelemetryDrilldownImportOverwriteConfirmChecked(false);
    setQuickTelemetryDrilldownImportRowOffset(0);
    setQuickTelemetryDrilldownTransferStatus("import safety bundle reset (filters + selection + overwrite confirm)");
  }, [quickTelemetryDrilldownImportRows]);
  const appendQuickTelemetryDrilldownStrictCutoverLedgerEvent = React.useCallback((eventId, nextMode) => {
    const eventKind = String(eventId || "").trim().toLowerCase() === "compat_fallback"
      ? "compat_fallback"
      : "apply_strict_default";
    const mode = normalizeQuickTelemetryDrilldownImportFilterBundleMode(nextMode || "compat");
    const checklist = buildQuickTelemetryDrilldownStrictAdoptionChecklist(
      quickTelemetryDrilldownStrictAdoptionSignals,
      mode
    );
    const sig = checklist.signals || {};
    const timestampMs = Date.now();
    const entry = normalizeQuickTelemetryDrilldownStrictCutoverLedgerEntry({
      id: `qt_cutover_${timestampMs}_${eventKind}`,
      event_id: eventKind,
      import_mode: mode,
      checklist_status: checklist.ready ? "READY" : "HOLD",
      pass_count: checklist.pass_count,
      item_count: checklist.item_count,
      attempt_count: Number(sig.attempt_count || 0),
      success_count: Number(sig.success_count || 0),
      legacy_wrap_use_count: Number(sig.legacy_wrap_use_count || 0),
      legacy_parse_block_count: Number(sig.legacy_parse_block_count || 0),
      timestamp_ms: timestampMs,
      timestamp_iso: formatTimestampIso(timestampMs),
    });
    if (!entry) return;
    setQuickTelemetryDrilldownStrictCutoverLedger((prev) => [
      entry,
      ...buildQuickTelemetryDrilldownStrictCutoverLedgerBundle(prev).entries,
    ].slice(0, QUICK_TELEMETRY_STRICT_CUTOVER_LEDGER_LIMIT));
    setQuickTelemetryDrilldownStrictCutoverLedgerStatus(
      `cutover timeline event logged: ${eventKind} (${entry.checklist_status} ${entry.pass_count}/${entry.item_count})`
    );
  }, [quickTelemetryDrilldownStrictAdoptionSignals]);
  const applyQuickTelemetryStrictDefaultCutoverPreset = React.useCallback(() => {
    setQuickTelemetryDrilldownImportFilterBundleMode("strict");
    setQuickTelemetryDrilldownImportFilterBundleStatus(
      "strict default cutover preset applied (mode=strict)"
    );
    setQuickTelemetryDrilldownStrictAdoptionGateStatus(
      "strict adoption gate signal: strict-default cutover helper applied"
    );
    setQuickTelemetryDrilldownStrictCutoverStatus(
      `strict default cutover applied (${quickTelemetryDrilldownStrictAdoptionChecklist.ready ? "READY" : "HOLD"} ${quickTelemetryDrilldownStrictAdoptionChecklist.pass_count}/${quickTelemetryDrilldownStrictAdoptionChecklist.item_count})`
    );
    setQuickTelemetryDrilldownStrictRollbackDrillStatus("");
    setQuickTelemetryDrilldownStrictRollbackPackageStatus("");
    setQuickTelemetryDrilldownStrictRollbackPackageDeltaConfirmChecked(false);
    setQuickTelemetryDrilldownStrictRollbackPackageOverrideLogStatus("");
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleStatus("");
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus("");
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydratedSnapshot(null);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmChecked(false);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityTrail([]);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmChecked(false);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmArmedAtMs(0);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTickMs(0);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmChecked(false);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmArmedAtMs(0);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTickMs(0);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrail([]);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrail([]);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmChecked(false);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmArmedAtMs(0);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmTickMs(0);
    appendQuickTelemetryDrilldownStrictCutoverLedgerEvent("apply_strict_default", "strict");
  }, [
    appendQuickTelemetryDrilldownStrictCutoverLedgerEvent,
    quickTelemetryDrilldownStrictAdoptionChecklist.item_count,
    quickTelemetryDrilldownStrictAdoptionChecklist.pass_count,
    quickTelemetryDrilldownStrictAdoptionChecklist.ready,
  ]);
  const switchQuickTelemetryToCompatFallback = React.useCallback(() => {
    setQuickTelemetryDrilldownImportFilterBundleMode("compat");
    setQuickTelemetryDrilldownImportFilterBundleStatus(
      "compat fallback preset applied (legacy payload support restored)"
    );
    setQuickTelemetryDrilldownStrictAdoptionGateStatus(
      "strict adoption gate signal: switched to compat fallback"
    );
    setQuickTelemetryDrilldownStrictCutoverStatus(
      "compat fallback applied; strict-default cutover is paused"
    );
    setQuickTelemetryDrilldownStrictRollbackDrillStatus("");
    setQuickTelemetryDrilldownStrictRollbackPackageStatus("");
    setQuickTelemetryDrilldownStrictRollbackPackageDeltaConfirmChecked(false);
    setQuickTelemetryDrilldownStrictRollbackPackageOverrideLogStatus("");
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleStatus("");
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus("");
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydratedSnapshot(null);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmChecked(false);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityTrail([]);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmChecked(false);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmArmedAtMs(0);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTickMs(0);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmChecked(false);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmArmedAtMs(0);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTickMs(0);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrail([]);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrail([]);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmChecked(false);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmArmedAtMs(0);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmTickMs(0);
    appendQuickTelemetryDrilldownStrictCutoverLedgerEvent("compat_fallback", "compat");
  }, [appendQuickTelemetryDrilldownStrictCutoverLedgerEvent]);
  const applyQuickTelemetryStrictRollbackDrillPreset = React.useCallback((presetId) => {
    const preset = resolveQuickTelemetryStrictRollbackDrillPreset(presetId);
    setQuickTelemetryDrilldownImportFilterBundleMode("compat");
    setFilterImportAuditQuickTelemetryFailureOnlyChecked(Boolean(preset?.failure_only));
    setFilterImportAuditQuickTelemetryReasonQuery(
      String(preset?.reason_query || "").slice(0, FILTER_IMPORT_AUDIT_QUICK_REASON_QUERY_MAX)
    );
    setQuickTelemetryDrilldownImportFilterBundleStatus(
      `rollback drill preset applied (${String(preset?.id || "parse_error")} -> mode=compat)`
    );
    setQuickTelemetryDrilldownStrictAdoptionGateStatus(
      "strict adoption gate signal: rollback drill preset switched to compat fallback"
    );
    setQuickTelemetryDrilldownStrictCutoverStatus(
      "compat fallback applied via rollback drill helper"
    );
    setQuickTelemetryDrilldownStrictRollbackDrillStatus(
      `rollback drill preset: ${String(preset?.id || "parse_error")} (reason=${String(preset?.reason_query || "-")})`
    );
    setQuickTelemetryDrilldownStrictRollbackPackageStatus("");
    setQuickTelemetryDrilldownStrictRollbackPackageDeltaConfirmChecked(false);
    setQuickTelemetryDrilldownStrictRollbackPackageOverrideLogStatus("");
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleStatus("");
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus("");
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydratedSnapshot(null);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmChecked(false);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityTrail([]);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmChecked(false);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmArmedAtMs(0);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTickMs(0);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmChecked(false);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmArmedAtMs(0);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTickMs(0);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrail([]);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrail([]);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmChecked(false);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmArmedAtMs(0);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmTickMs(0);
    appendQuickTelemetryDrilldownStrictCutoverLedgerEvent("compat_fallback", "compat");
  }, [appendQuickTelemetryDrilldownStrictCutoverLedgerEvent]);
  const resetQuickTelemetryStrictRollbackDrillPreset = React.useCallback(() => {
    setFilterImportAuditQuickTelemetryFailureOnlyChecked(
      Boolean(CONTRACT_OVERLAY_DEFAULT_PREFS.filterImportAuditQuickTelemetryFailureOnly)
    );
    setFilterImportAuditQuickTelemetryReasonQuery(
      String(CONTRACT_OVERLAY_DEFAULT_PREFS.filterImportAuditQuickTelemetryReasonQuery || "")
    );
    setQuickTelemetryDrilldownStrictRollbackDrillStatus("rollback drill filter reset");
    setQuickTelemetryDrilldownStrictRollbackPackageStatus("");
    setQuickTelemetryDrilldownStrictRollbackPackageDeltaConfirmChecked(false);
    setQuickTelemetryDrilldownStrictRollbackPackageOverrideLogStatus("");
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleStatus("");
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus("");
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydratedSnapshot(null);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmChecked(false);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityTrail([]);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmChecked(false);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmArmedAtMs(0);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTickMs(0);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmChecked(false);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmArmedAtMs(0);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTickMs(0);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrail([]);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrail([]);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmChecked(false);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmArmedAtMs(0);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmTickMs(0);
  }, []);
  const exportQuickTelemetryStrictRollbackDrillPackageToJson = React.useCallback(() => {
    const jsonText = serializeQuickTelemetryStrictRollbackDrillPackage(
      quickTelemetryStrictRollbackDrillPackagePayload
    );
    try {
      if (typeof window === "undefined" || typeof document === "undefined" || !window.URL) {
        setQuickTelemetryDrilldownStrictRollbackPackageStatus("rollback drill package export prepared in-memory");
        return;
      }
      const blob = new Blob([jsonText], { type: "application/json;charset=utf-8" });
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      const ts = new Date().toISOString().replace(/[:.]/g, "-");
      anchor.href = url;
      anchor.download = `graph_lab_quick_telemetry_strict_rollback_drill_package_${ts}.json`;
      document.body.appendChild(anchor);
      anchor.click();
      document.body.removeChild(anchor);
      window.URL.revokeObjectURL(url);
      setQuickTelemetryDrilldownStrictRollbackPackageStatus(
        `rollback drill package export complete (${quickTelemetryStrictRollbackDrillPackagePayload.cutover_timeline_entries.length} timeline events)`
      );
    } catch (_) {
      setQuickTelemetryDrilldownStrictRollbackPackageStatus("rollback drill package export failed");
    }
  }, [quickTelemetryStrictRollbackDrillPackagePayload]);
  const copyQuickTelemetryStrictRollbackDrillPackageJson = React.useCallback(async () => {
    const jsonText = serializeQuickTelemetryStrictRollbackDrillPackage(
      quickTelemetryStrictRollbackDrillPackagePayload
    );
    try {
      if (typeof navigator !== "undefined" && navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(jsonText);
        setQuickTelemetryDrilldownStrictRollbackPackageStatus(
          `rollback drill package copied (${quickTelemetryStrictRollbackDrillPackagePayload.cutover_timeline_entries.length} timeline events)`
        );
        return;
      }
      throw new Error("clipboard unavailable");
    } catch (_) {
      setQuickTelemetryDrilldownStrictRollbackPackageStatus("rollback drill package copy failed");
    }
  }, [quickTelemetryStrictRollbackDrillPackagePayload]);
  const copyQuickTelemetryStrictRollbackChecklistReportText = React.useCallback(async () => {
    const reportText = String(quickTelemetryDrilldownStrictRollbackChecklistReportPreview || "").trim();
    if (!reportText) {
      setQuickTelemetryDrilldownStrictRollbackPackageStatus("rollback checklist report copy skipped (empty)");
      return;
    }
    try {
      if (typeof navigator !== "undefined" && navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(reportText);
        setQuickTelemetryDrilldownStrictRollbackPackageStatus("rollback checklist report copied");
        return;
      }
      throw new Error("clipboard unavailable");
    } catch (_) {
      setQuickTelemetryDrilldownStrictRollbackPackageStatus("rollback checklist report copy failed");
    }
  }, [quickTelemetryDrilldownStrictRollbackChecklistReportPreview]);
  const copyQuickTelemetryStrictRollbackPackageOverrideLogJson = React.useCallback(async () => {
    const jsonText = serializeQuickTelemetryStrictRollbackOverrideLogBundle(
      quickTelemetryStrictRollbackPackageOverrideLogRows
    );
    try {
      if (typeof navigator !== "undefined" && navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(jsonText);
        setQuickTelemetryDrilldownStrictRollbackPackageOverrideLogStatus(
          `override log copied (${quickTelemetryStrictRollbackPackageOverrideLogRows.length} events)`
        );
        return;
      }
      throw new Error("clipboard unavailable");
    } catch (_) {
      setQuickTelemetryDrilldownStrictRollbackPackageOverrideLogStatus("override log copy failed");
    }
  }, [quickTelemetryStrictRollbackPackageOverrideLogRows]);
  const exportQuickTelemetryStrictRollbackPackageOverrideLogToJson = React.useCallback(() => {
    const jsonText = serializeQuickTelemetryStrictRollbackOverrideLogBundle(
      quickTelemetryStrictRollbackPackageOverrideLogRows
    );
    try {
      if (typeof window === "undefined" || typeof document === "undefined" || !window.URL) {
        setQuickTelemetryDrilldownStrictRollbackPackageOverrideLogStatus("override log export prepared in-memory");
        return;
      }
      const blob = new Blob([jsonText], { type: "application/json;charset=utf-8" });
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      const ts = new Date().toISOString().replace(/[:.]/g, "-");
      anchor.href = url;
      anchor.download = `graph_lab_quick_telemetry_strict_rollback_override_log_${ts}.json`;
      document.body.appendChild(anchor);
      anchor.click();
      document.body.removeChild(anchor);
      window.URL.revokeObjectURL(url);
      setQuickTelemetryDrilldownStrictRollbackPackageOverrideLogStatus(
        `override log export complete (${quickTelemetryStrictRollbackPackageOverrideLogRows.length} events)`
      );
    } catch (_) {
      setQuickTelemetryDrilldownStrictRollbackPackageOverrideLogStatus("override log export failed");
    }
  }, [quickTelemetryStrictRollbackPackageOverrideLogRows]);
  const resetQuickTelemetryStrictRollbackPackageOverrideLog = React.useCallback(() => {
    setQuickTelemetryDrilldownStrictRollbackPackageOverrideLog([]);
    setQuickTelemetryDrilldownStrictRollbackPackageOverrideReasonText("");
    setQuickTelemetryDrilldownStrictRollbackPackageOverrideLogStatus("override log reset");
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleStatus("");
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus("");
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydratedSnapshot(null);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmChecked(false);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityTrail([]);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmChecked(false);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmArmedAtMs(0);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTickMs(0);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmChecked(false);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmArmedAtMs(0);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTickMs(0);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrail([]);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrail([]);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmChecked(false);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmArmedAtMs(0);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmTickMs(0);
  }, []);
  const copyQuickTelemetryStrictRollbackTrustAuditBundleJson = React.useCallback(async () => {
    const jsonText = serializeQuickTelemetryStrictRollbackTrustAuditBundle(
      quickTelemetryStrictRollbackTrustAuditBundle
    );
    const eventCount = Number(quickTelemetryStrictRollbackTrustAuditBundle?.override_log?.entry_count || 0);
    try {
      if (typeof navigator !== "undefined" && navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(jsonText);
        setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleStatus(
          `trust audit bundle copied (${eventCount} override events)`
        );
        return;
      }
      throw new Error("clipboard unavailable");
    } catch (_) {
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleStatus("trust audit bundle copy failed");
    }
  }, [quickTelemetryStrictRollbackTrustAuditBundle]);
  const exportQuickTelemetryStrictRollbackTrustAuditBundleToJson = React.useCallback(() => {
    const jsonText = serializeQuickTelemetryStrictRollbackTrustAuditBundle(
      quickTelemetryStrictRollbackTrustAuditBundle
    );
    const eventCount = Number(quickTelemetryStrictRollbackTrustAuditBundle?.override_log?.entry_count || 0);
    try {
      if (typeof window === "undefined" || typeof document === "undefined" || !window.URL) {
        setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleStatus(
          "trust audit bundle export prepared in-memory"
        );
        return;
      }
      const blob = new Blob([jsonText], { type: "application/json;charset=utf-8" });
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      const ts = new Date().toISOString().replace(/[:.]/g, "-");
      anchor.href = url;
      anchor.download = `graph_lab_quick_telemetry_strict_rollback_trust_audit_bundle_${ts}.json`;
      document.body.appendChild(anchor);
      anchor.click();
      document.body.removeChild(anchor);
      window.URL.revokeObjectURL(url);
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleStatus(
        `trust audit bundle export complete (${eventCount} override events)`
      );
    } catch (_) {
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleStatus("trust audit bundle export failed");
    }
  }, [quickTelemetryStrictRollbackTrustAuditBundle]);
  const applyQuickTelemetryStrictRollbackTrustAuditBundleFromText = React.useCallback(() => {
    if (parsedQuickTelemetryStrictRollbackTrustAuditBundlePayload.empty) {
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleStatus(
        "trust audit bundle apply skipped: empty payload"
      );
      return;
    }
    if (parsedQuickTelemetryStrictRollbackTrustAuditBundlePayload.error) {
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleStatus(
        `trust audit bundle apply failed: ${parsedQuickTelemetryStrictRollbackTrustAuditBundlePayload.error}`
      );
      return;
    }
    const bundle = parsedQuickTelemetryStrictRollbackTrustAuditBundlePayload.bundle || null;
    if (!bundle || typeof bundle !== "object") {
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleStatus(
        "trust audit bundle apply failed: invalid payload"
      );
      return;
    }
    if (
      quickTelemetryStrictRollbackTrustAuditBundleApplySafety.needs_confirm
      && !quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmChecked
    ) {
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleStatus(
        "trust audit bundle apply blocked: replacement safety confirm required"
      );
      return;
    }
    const policyMode = normalizeQuickTelemetryStrictRollbackPackageTrustPolicy(bundle.trust_policy_mode);
    const overrideEntries = buildQuickTelemetryStrictRollbackOverrideLogBundle(
      bundle.override_log?.entries
    ).entries;
    const snapshot = normalizeQuickTelemetryStrictRollbackTrustAuditProvenanceSnapshot(
      bundle.provenance_snapshot
    );
    setQuickTelemetryStrictRollbackPackageTrustPolicy(policyMode);
    setQuickTelemetryDrilldownStrictRollbackPackageOverrideLog(overrideEntries);
    setQuickTelemetryDrilldownStrictRollbackPackageOverrideReasonText("");
    setQuickTelemetryDrilldownStrictRollbackPackageOverrideLogStatus(
      `override log hydrated from trust audit bundle (${overrideEntries.length} events)`
    );
    setQuickTelemetryDrilldownStrictRollbackPackageStatus("");
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleStatus(
      `trust audit bundle applied (policy=${policyMode}, overrides=${overrideEntries.length}, parse=${snapshot.parse_state})`
    );
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmChecked(false);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmArmedAtMs(0);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmTickMs(0);
  }, [
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmChecked,
    quickTelemetryStrictRollbackTrustAuditBundleApplySafety.needs_confirm,
    parsedQuickTelemetryStrictRollbackTrustAuditBundlePayload.bundle,
    parsedQuickTelemetryStrictRollbackTrustAuditBundlePayload.empty,
    parsedQuickTelemetryStrictRollbackTrustAuditBundlePayload.error,
  ]);
  const applyQuickTelemetryStrictRollbackPackageReplay = React.useCallback((opts = null) => {
    const options = opts && typeof opts === "object" && !Array.isArray(opts) ? opts : {};
    const allowProvenanceOverride = Boolean(options.allow_provenance_override);
    if (parsedQuickTelemetryStrictRollbackDrillPackagePayload.empty) {
      setQuickTelemetryDrilldownStrictRollbackPackageStatus("rollback package replay skipped: empty payload");
      return;
    }
    if (parsedQuickTelemetryStrictRollbackDrillPackagePayload.error) {
      setQuickTelemetryDrilldownStrictRollbackPackageStatus(
        `rollback package replay failed: ${parsedQuickTelemetryStrictRollbackDrillPackagePayload.error}`
      );
      return;
    }
    const parsedPkg = parsedQuickTelemetryStrictRollbackDrillPackagePayload.pkg || null;
    if (!parsedPkg || typeof parsedPkg !== "object") {
      setQuickTelemetryDrilldownStrictRollbackPackageStatus("rollback package replay failed: invalid package");
      return;
    }
    const policyMode = normalizeQuickTelemetryStrictRollbackPackageTrustPolicy(
      quickTelemetryStrictRollbackPackageTrustPolicy
    );
    const provenanceIssue = quickTelemetryStrictRollbackPackageProvenanceGuard.has_guard_issue;
    const strictRejectPolicy = policyMode === "strict_reject";
    if (strictRejectPolicy && provenanceIssue && !allowProvenanceOverride) {
      setQuickTelemetryDrilldownStrictRollbackPackageStatus(
        "rollback package replay blocked: provenance strict-reject policy (use override replay)"
      );
      return;
    }
    const guardBlocked = (
      quickTelemetryStrictRollbackPackageChecklistDeltaGuard.has_delta
      || (provenanceIssue && !strictRejectPolicy)
    );
    if (guardBlocked && !quickTelemetryDrilldownStrictRollbackPackageDeltaConfirmChecked) {
      setQuickTelemetryDrilldownStrictRollbackPackageStatus(
        "rollback package replay blocked: checklist delta/provenance guard detected (confirm replay required)"
      );
      return;
    }
    if (allowProvenanceOverride && (!strictRejectPolicy || !provenanceIssue)) {
      setQuickTelemetryDrilldownStrictRollbackPackageStatus(
        "rollback package override replay skipped: strict provenance reject is not active"
      );
      return;
    }
    const snapshot = parsedPkg.preset_snapshot && typeof parsedPkg.preset_snapshot === "object"
      ? parsedPkg.preset_snapshot
      : {};
    const rowCapRaw = clampInteger(snapshot.row_cap, 4, 200, 16);
    const rowCap = QUICK_TELEMETRY_DRILLDOWN_IMPORT_ROW_CAP_OPTIONS.includes(String(rowCapRaw))
      ? rowCapRaw
      : Number(CONTRACT_OVERLAY_DEFAULT_PREFS.quickTelemetryDrilldownImportRowCap || 16);
    const timelineRows = buildQuickTelemetryDrilldownStrictCutoverLedgerBundle(
      Array.isArray(parsedPkg.cutover_timeline_entries) ? parsedPkg.cutover_timeline_entries : []
    ).entries;
    const report = parsedPkg.checklist_report && typeof parsedPkg.checklist_report === "object"
      ? parsedPkg.checklist_report
      : {};
    setQuickTelemetryDrilldownImportFilterBundleMode(
      normalizeQuickTelemetryDrilldownImportFilterBundleMode(snapshot.import_mode || "compat")
    );
    setFilterImportAuditQuickTelemetryFailureOnlyChecked(Boolean(snapshot.failure_only));
    setFilterImportAuditQuickTelemetryReasonQuery(
      String(snapshot.reason_query || "").slice(0, FILTER_IMPORT_AUDIT_QUICK_REASON_QUERY_MAX)
    );
    setQuickTelemetryDrilldownImportConflictOnlyChecked(Boolean(snapshot.conflict_only));
    setQuickTelemetryDrilldownImportConflictFilter(
      normalizeQuickTelemetryDrilldownImportConflictFilter(snapshot.conflict_filter || "all")
    );
    setQuickTelemetryDrilldownImportNameQuery(
      String(snapshot.name_query || "").slice(0, QUICK_TELEMETRY_DRILLDOWN_IMPORT_NAME_QUERY_MAX)
    );
    setQuickTelemetryDrilldownImportRowCapText(String(rowCap));
    setQuickTelemetryDrilldownImportRowOffset(0);
    setQuickTelemetryDrilldownStrictCutoverLedger(timelineRows);
    setQuickTelemetryDrilldownStrictCutoverLedgerStatus(
      `cutover timeline replayed from rollback package (${timelineRows.length} events)`
    );
    setQuickTelemetryDrilldownStrictAdoptionGateStatus(
      "strict adoption gate signal: rollback package replay applied"
    );
    setQuickTelemetryDrilldownStrictCutoverStatus(
      [
        `rollback package replay applied (mode=${String(snapshot.import_mode || "compat")})`,
        `checklist=${String(report.status || "HOLD")} ${Number(report.pass_count || 0)}/${Number(report.item_count || 0)}`,
      ].join(", ")
    );
    setQuickTelemetryDrilldownStrictRollbackDrillStatus(
      `rollback package replay preset:${String(snapshot.preset_id || "custom")} reason:${String(snapshot.reason_query || "-") || "-"}`
    );
    if (allowProvenanceOverride && strictRejectPolicy && provenanceIssue) {
      const overrideReason = String(quickTelemetryDrilldownStrictRollbackPackageOverrideReasonText || "").trim();
      const timestampIso = new Date().toISOString();
      setQuickTelemetryDrilldownStrictRollbackPackageOverrideLog((prev) => [
        normalizeQuickTelemetryStrictRollbackOverrideLogEntry({
          id: `qt_override_${Date.now()}`,
          timestamp_iso: timestampIso,
          event_kind: "override_replay",
          policy_mode: policyMode,
          source_stamp: quickTelemetryStrictRollbackPackageProvenanceGuard.source_stamp,
          payload_checksum: quickTelemetryStrictRollbackPackageProvenanceGuard.payload_checksum,
          computed_checksum: quickTelemetryStrictRollbackPackageProvenanceGuard.computed_checksum,
          provenance_issue: provenanceIssue,
          checklist_delta: quickTelemetryStrictRollbackPackageChecklistDeltaGuard.has_delta,
          delta_confirmed: quickTelemetryDrilldownStrictRollbackPackageDeltaConfirmChecked,
          override_reason: overrideReason || "operator_override",
          preset_id: String(snapshot.preset_id || "custom"),
        }),
        ...buildQuickTelemetryStrictRollbackOverrideLogBundle(prev).entries,
      ].slice(0, QUICK_TELEMETRY_STRICT_ROLLBACK_OVERRIDE_LOG_LIMIT));
      setQuickTelemetryDrilldownStrictRollbackPackageOverrideLogStatus(
        `override log appended (${policyMode}, preset:${String(snapshot.preset_id || "custom")})`
      );
      setQuickTelemetryDrilldownStrictRollbackPackageOverrideReasonText("");
    }
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleStatus("");
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus("");
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydratedSnapshot(null);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmChecked(false);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmChecked(false);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmArmedAtMs(0);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmTickMs(0);
    setQuickTelemetryDrilldownStrictRollbackPackageStatus(
      [
        allowProvenanceOverride ? "rollback package override replayed" : "rollback package replayed",
        `delta=${quickTelemetryStrictRollbackPackageChecklistDeltaGuard.has_delta ? "confirmed" : "none"}`,
        `provenance=${provenanceIssue ? (allowProvenanceOverride ? "override" : "guarded") : "ok"}`,
        `policy=${policyMode}`,
      ].join(" ")
    );
    setQuickTelemetryDrilldownStrictRollbackPackageDeltaConfirmChecked(false);
  }, [
    parsedQuickTelemetryStrictRollbackDrillPackagePayload.empty,
    parsedQuickTelemetryStrictRollbackDrillPackagePayload.error,
    parsedQuickTelemetryStrictRollbackDrillPackagePayload.pkg,
    quickTelemetryDrilldownStrictRollbackPackageOverrideReasonText,
    quickTelemetryStrictRollbackPackageTrustPolicy,
    quickTelemetryDrilldownStrictRollbackPackageDeltaConfirmChecked,
    quickTelemetryStrictRollbackPackageChecklistDeltaGuard.has_delta,
    quickTelemetryStrictRollbackPackageProvenanceGuard.computed_checksum,
    quickTelemetryStrictRollbackPackageProvenanceGuard.has_guard_issue,
    quickTelemetryStrictRollbackPackageProvenanceGuard.payload_checksum,
    quickTelemetryStrictRollbackPackageProvenanceGuard.source_stamp,
  ]);
  const replayQuickTelemetryStrictRollbackPackageFromText = React.useCallback(() => {
    applyQuickTelemetryStrictRollbackPackageReplay({ allow_provenance_override: false });
  }, [applyQuickTelemetryStrictRollbackPackageReplay]);
  const overrideReplayQuickTelemetryStrictRollbackPackageFromText = React.useCallback(() => {
    applyQuickTelemetryStrictRollbackPackageReplay({ allow_provenance_override: true });
  }, [applyQuickTelemetryStrictRollbackPackageReplay]);
  const resetQuickTelemetryDrilldownStrictCutoverLedger = React.useCallback(() => {
    setQuickTelemetryDrilldownStrictCutoverLedger([]);
    setQuickTelemetryDrilldownStrictCutoverLedgerStatus("cutover timeline reset");
    setQuickTelemetryDrilldownStrictRollbackPackageStatus("");
    setQuickTelemetryDrilldownStrictRollbackPackageDeltaConfirmChecked(false);
    setQuickTelemetryDrilldownStrictRollbackPackageOverrideReasonText("");
    setQuickTelemetryDrilldownStrictRollbackPackageOverrideLogStatus("");
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleStatus("");
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus("");
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydratedSnapshot(null);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmChecked(false);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmChecked(false);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmArmedAtMs(0);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmTickMs(0);
  }, []);
  const exportQuickTelemetryDrilldownStrictCutoverLedgerToJson = React.useCallback(() => {
    const jsonText = serializeQuickTelemetryDrilldownStrictCutoverLedgerBundle(
      quickTelemetryDrilldownStrictCutoverLedgerRows
    );
    try {
      if (typeof window === "undefined" || typeof document === "undefined" || !window.URL) {
        setQuickTelemetryDrilldownStrictCutoverLedgerStatus("cutover timeline export ready in memory");
        return;
      }
      const blob = new Blob([jsonText], { type: "application/json;charset=utf-8" });
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      const ts = new Date().toISOString().replace(/[:.]/g, "-");
      anchor.href = url;
      anchor.download = `graph_lab_quick_telemetry_strict_cutover_timeline_${ts}.json`;
      document.body.appendChild(anchor);
      anchor.click();
      document.body.removeChild(anchor);
      window.URL.revokeObjectURL(url);
      setQuickTelemetryDrilldownStrictCutoverLedgerStatus(
        `cutover timeline export complete (${quickTelemetryDrilldownStrictCutoverLedgerRows.length} events)`
      );
    } catch (_) {
      setQuickTelemetryDrilldownStrictCutoverLedgerStatus("cutover timeline export failed");
    }
  }, [quickTelemetryDrilldownStrictCutoverLedgerRows]);
  const copyQuickTelemetryDrilldownStrictCutoverLedgerJson = React.useCallback(async () => {
    const jsonText = serializeQuickTelemetryDrilldownStrictCutoverLedgerBundle(
      quickTelemetryDrilldownStrictCutoverLedgerRows
    );
    try {
      if (typeof navigator !== "undefined" && navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(jsonText);
        setQuickTelemetryDrilldownStrictCutoverLedgerStatus(
          `cutover timeline copied (${quickTelemetryDrilldownStrictCutoverLedgerRows.length} events)`
        );
        return;
      }
      throw new Error("clipboard unavailable");
    } catch (_) {
      setQuickTelemetryDrilldownStrictCutoverLedgerStatus("cutover timeline copy failed");
    }
  }, [quickTelemetryDrilldownStrictCutoverLedgerRows]);
  const exportQuickTelemetryDrilldownImportFilterBundleToJson = React.useCallback(() => {
    const jsonText = serializeQuickTelemetryDrilldownImportFilterBundle({
      preset_id: activeQuickTelemetryDrilldownImportFilterPresetId,
      conflict_only: quickTelemetryDrilldownImportConflictOnlyChecked,
      conflict_filter: quickTelemetryDrilldownImportConflictFilter,
      name_query: quickTelemetryDrilldownImportNameQuery,
      row_cap: quickTelemetryDrilldownImportRowCap,
    });
    setQuickTelemetryDrilldownImportFilterBundleText(jsonText);
    try {
      if (typeof window === "undefined" || typeof document === "undefined" || !window.URL) {
        setQuickTelemetryDrilldownImportFilterBundleStatus("filter bundle exported to text buffer");
        return;
      }
      const blob = new Blob([jsonText], { type: "application/json;charset=utf-8" });
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      const ts = new Date().toISOString().replace(/[:.]/g, "-");
      anchor.href = url;
      anchor.download = `graph_lab_quick_telemetry_import_filter_bundle_${ts}.json`;
      document.body.appendChild(anchor);
      anchor.click();
      document.body.removeChild(anchor);
      window.URL.revokeObjectURL(url);
      setQuickTelemetryDrilldownImportFilterBundleStatus("filter bundle exported");
    } catch (_) {
      setQuickTelemetryDrilldownImportFilterBundleStatus("filter bundle export failed; fallback to text buffer");
    }
  }, [
    activeQuickTelemetryDrilldownImportFilterPresetId,
    quickTelemetryDrilldownImportConflictFilter,
    quickTelemetryDrilldownImportConflictOnlyChecked,
    quickTelemetryDrilldownImportNameQuery,
    quickTelemetryDrilldownImportRowCap,
  ]);
  const copyQuickTelemetryDrilldownImportFilterBundleJson = React.useCallback(async () => {
    const jsonText = serializeQuickTelemetryDrilldownImportFilterBundle({
      preset_id: activeQuickTelemetryDrilldownImportFilterPresetId,
      conflict_only: quickTelemetryDrilldownImportConflictOnlyChecked,
      conflict_filter: quickTelemetryDrilldownImportConflictFilter,
      name_query: quickTelemetryDrilldownImportNameQuery,
      row_cap: quickTelemetryDrilldownImportRowCap,
    });
    setQuickTelemetryDrilldownImportFilterBundleText(jsonText);
    try {
      if (typeof navigator !== "undefined" && navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(jsonText);
        setQuickTelemetryDrilldownImportFilterBundleStatus("filter bundle copied to clipboard");
        return;
      }
      setQuickTelemetryDrilldownImportFilterBundleStatus("clipboard unavailable; copy filter bundle from text");
    } catch (_) {
      setQuickTelemetryDrilldownImportFilterBundleStatus("filter bundle copy failed");
    }
  }, [
    activeQuickTelemetryDrilldownImportFilterPresetId,
    quickTelemetryDrilldownImportConflictFilter,
    quickTelemetryDrilldownImportConflictOnlyChecked,
    quickTelemetryDrilldownImportNameQuery,
    quickTelemetryDrilldownImportRowCap,
  ]);
  const wrapQuickTelemetryDrilldownImportFilterBundleLegacyPayload = React.useCallback(() => {
    if (quickTelemetryDrilldownImportFilterBundleMode !== "strict") {
      setQuickTelemetryDrilldownImportFilterBundleStatus(
        "legacy wrap skipped: switch import mode to strict"
      );
      return;
    }
    if (!quickTelemetryDrilldownImportFilterBundleStrictWrapCandidate.available) {
      setQuickTelemetryDrilldownImportFilterBundleStatus(
        `legacy wrap skipped: ${String(quickTelemetryDrilldownImportFilterBundleStrictWrapCandidate.reason || "no candidate")}`
      );
      return;
    }
    setQuickTelemetryDrilldownImportFilterBundleText(
      String(quickTelemetryDrilldownImportFilterBundleStrictWrapCandidate.wrapped_text || "")
    );
    bumpQuickTelemetryDrilldownStrictAdoptionSignals({ legacy_wrap_use_count: 1 });
    setQuickTelemetryDrilldownStrictAdoptionGateStatus(
      "strict adoption gate signal: legacy wrap helper used (+1)"
    );
    setQuickTelemetryDrilldownImportFilterBundleStatus(
      "legacy payload wrapped to strict bundle preview (kind/schema/filter_bundle)"
    );
  }, [
    bumpQuickTelemetryDrilldownStrictAdoptionSignals,
    quickTelemetryDrilldownImportFilterBundleMode,
    quickTelemetryDrilldownImportFilterBundleStrictWrapCandidate.available,
    quickTelemetryDrilldownImportFilterBundleStrictWrapCandidate.reason,
    quickTelemetryDrilldownImportFilterBundleStrictWrapCandidate.wrapped_text,
  ]);
  const importQuickTelemetryDrilldownImportFilterBundleFromText = React.useCallback(() => {
    const strictMode = quickTelemetryDrilldownImportFilterBundleMode === "strict";
    if (parsedQuickTelemetryDrilldownImportFilterBundlePayload.empty) {
      setQuickTelemetryDrilldownImportFilterBundleStatus("filter bundle import skipped: empty payload");
      return;
    }
    if (parsedQuickTelemetryDrilldownImportFilterBundlePayload.error) {
      if (strictMode) {
        const errText = String(parsedQuickTelemetryDrilldownImportFilterBundlePayload.error || "");
        bumpQuickTelemetryDrilldownStrictAdoptionSignals({
          attempt_count: 1,
          legacy_parse_block_count: errText.includes("strict mode requires filter_bundle wrapper") ? 1 : 0,
        });
        setQuickTelemetryDrilldownStrictAdoptionGateStatus(
          "strict adoption gate signal: strict import failure recorded"
        );
      }
      setQuickTelemetryDrilldownImportFilterBundleStatus(
        [
          `filter bundle import failed: ${parsedQuickTelemetryDrilldownImportFilterBundlePayload.error}`,
          quickTelemetryDrilldownImportFilterBundleInvalidGuidance,
        ].filter(Boolean).join(" | ")
      );
      return;
    }
    const bundle = parsedQuickTelemetryDrilldownImportFilterBundlePayload.bundle || {};
    setQuickTelemetryDrilldownImportConflictOnlyChecked(Boolean(bundle.conflict_only));
    setQuickTelemetryDrilldownImportConflictFilter(
      normalizeQuickTelemetryDrilldownImportConflictFilter(bundle.conflict_filter || "all")
    );
    setQuickTelemetryDrilldownImportNameQuery(
      String(bundle.name_query || "").slice(0, QUICK_TELEMETRY_DRILLDOWN_IMPORT_NAME_QUERY_MAX)
    );
    setQuickTelemetryDrilldownImportRowCapText(String(bundle.row_cap || CONTRACT_OVERLAY_DEFAULT_PREFS.quickTelemetryDrilldownImportRowCap));
    setQuickTelemetryDrilldownImportRowOffset(0);
    if (strictMode) {
      bumpQuickTelemetryDrilldownStrictAdoptionSignals({
        attempt_count: 1,
        success_count: 1,
      });
      setQuickTelemetryDrilldownStrictAdoptionGateStatus(
        "strict adoption gate signal: strict import success recorded"
      );
    }
    setQuickTelemetryDrilldownImportFilterBundleStatus(
      `filter bundle imported (preset:${String(bundle.preset_id || "custom")}, schema:${Number(bundle.schema_version || QUICK_TELEMETRY_DRILLDOWN_IMPORT_FILTER_BUNDLE_SCHEMA_VERSION)}, wrapper:${Boolean(bundle.has_wrapper) ? "on" : "off"}, mode:${String(bundle.import_mode || quickTelemetryDrilldownImportFilterBundleMode)})`
    );
  }, [
    bumpQuickTelemetryDrilldownStrictAdoptionSignals,
    quickTelemetryDrilldownImportFilterBundleMode,
    quickTelemetryDrilldownImportFilterBundleInvalidGuidance,
    parsedQuickTelemetryDrilldownImportFilterBundlePayload.bundle,
    parsedQuickTelemetryDrilldownImportFilterBundlePayload.empty,
    parsedQuickTelemetryDrilldownImportFilterBundlePayload.error,
  ]);
  const toggleQuickTelemetryDrilldownImportSelection = React.useCallback((profileName) => {
    const name = String(profileName || "").trim();
    if (!name) return;
    setQuickTelemetryDrilldownImportSelection((prev) => ({
      ...(prev && typeof prev === "object" && !Array.isArray(prev) ? prev : {}),
      [name]: !Boolean(prev?.[name]),
    }));
  }, []);
  const selectAllQuickTelemetryDrilldownImportRowsVisible = React.useCallback(() => {
    setQuickTelemetryDrilldownImportSelection((prev) => {
      const base = prev && typeof prev === "object" && !Array.isArray(prev) ? prev : {};
      const next = { ...base };
      quickTelemetryDrilldownImportSelectionRows.forEach((row) => {
        const name = String(row.name || "");
        if (!name) return;
        next[name] = true;
      });
      return next;
    });
  }, [quickTelemetryDrilldownImportSelectionRows]);
  const clearQuickTelemetryDrilldownImportSelection = React.useCallback(() => {
    setQuickTelemetryDrilldownImportSelection((prev) => {
      const base = prev && typeof prev === "object" && !Array.isArray(prev) ? prev : {};
      const next = { ...base };
      quickTelemetryDrilldownImportSelectionRows.forEach((row) => {
        const name = String(row.name || "");
        if (!name) return;
        next[name] = false;
      });
      return next;
    });
  }, [quickTelemetryDrilldownImportSelectionRows]);
  const selectPageQuickTelemetryDrilldownImportSelection = React.useCallback(() => {
    setQuickTelemetryDrilldownImportSelection((prev) => {
      const base = prev && typeof prev === "object" && !Array.isArray(prev) ? prev : {};
      const next = { ...base };
      quickTelemetryDrilldownImportRowsPage.forEach((row) => {
        const name = String(row.name || "");
        if (!name) return;
        next[name] = true;
      });
      return next;
    });
  }, [quickTelemetryDrilldownImportRowsPage]);
  const clearPageQuickTelemetryDrilldownImportSelection = React.useCallback(() => {
    setQuickTelemetryDrilldownImportSelection((prev) => {
      const base = prev && typeof prev === "object" && !Array.isArray(prev) ? prev : {};
      const next = { ...base };
      quickTelemetryDrilldownImportRowsPage.forEach((row) => {
        const name = String(row.name || "");
        if (!name) return;
        next[name] = false;
      });
      return next;
    });
  }, [quickTelemetryDrilldownImportRowsPage]);
  const quickTelemetryDrilldownProfileOptions = React.useMemo(() => {
    const names = Object.keys(quickTelemetryDrilldownProfiles).map((name) => String(name || "").trim()).filter(Boolean);
    names.sort((a, b) => a.localeCompare(b));
    if (!names.includes("default")) return names;
    return ["default", ...names.filter((name) => name !== "default")];
  }, [quickTelemetryDrilldownProfiles]);
  const normalizedQuickTelemetryDrilldownProfileDraft = React.useMemo(
    () => normalizeQuickTelemetryDrilldownProfileName(quickTelemetryDrilldownProfileDraft),
    [quickTelemetryDrilldownProfileDraft]
  );
  const activeQuickTelemetryDrilldownProfileIsBuiltin = React.useMemo(
    () => Object.prototype.hasOwnProperty.call(
      DEFAULT_FILTER_IMPORT_AUDIT_QUICK_TELEMETRY_DRILLDOWN_PROFILES,
      activeQuickTelemetryDrilldownProfile
    ),
    [activeQuickTelemetryDrilldownProfile]
  );
  const applyActiveQuickTelemetryDrilldownProfile = React.useCallback(() => {
    const profileName = String(activeQuickTelemetryDrilldownProfile || "").trim();
    const fromProfile = quickTelemetryDrilldownProfiles[profileName]
      || DEFAULT_FILTER_IMPORT_AUDIT_QUICK_TELEMETRY_DRILLDOWN_PROFILES.default;
    const normalized = normalizeQuickTelemetryDrilldownProfile(
      fromProfile,
      DEFAULT_FILTER_IMPORT_AUDIT_QUICK_TELEMETRY_DRILLDOWN_PROFILES.default
    );
    setFilterImportAuditQuickTelemetryFailureOnlyChecked(Boolean(normalized.failure_only));
    setFilterImportAuditQuickTelemetryReasonQuery(
      String(normalized.reason_query || "").slice(0, FILTER_IMPORT_AUDIT_QUICK_REASON_QUERY_MAX)
    );
    setFilterTransferStatus(`quick telemetry profile loaded: ${profileName || "default"}`);
  }, [activeQuickTelemetryDrilldownProfile, quickTelemetryDrilldownProfiles]);
  const saveCurrentQuickTelemetryDrilldownProfile = React.useCallback(() => {
    const nextName = normalizeQuickTelemetryDrilldownProfileName(quickTelemetryDrilldownProfileDraft);
    if (!nextName) return;
    const normalized = normalizeQuickTelemetryDrilldownProfile({
      failure_only: filterImportAuditQuickTelemetryFailureOnlyChecked,
      reason_query: filterImportAuditQuickTelemetryReasonQuery,
    }, DEFAULT_FILTER_IMPORT_AUDIT_QUICK_TELEMETRY_DRILLDOWN_PROFILES.default);
    setQuickTelemetryDrilldownProfiles((prev) => ({
      ...prev,
      [nextName]: normalized,
    }));
    setActiveQuickTelemetryDrilldownProfile(nextName);
    setQuickTelemetryDrilldownProfileDraft(nextName);
    setQuickTelemetryDrilldownImportUndoSnapshot(null);
    setQuickTelemetryDrilldownTransferStatus(`saved profile: ${nextName}`);
  }, [
    filterImportAuditQuickTelemetryFailureOnlyChecked,
    filterImportAuditQuickTelemetryReasonQuery,
    quickTelemetryDrilldownProfileDraft,
  ]);
  const deleteActiveQuickTelemetryDrilldownProfile = React.useCallback(() => {
    const profileName = String(activeQuickTelemetryDrilldownProfile || "").trim();
    if (!profileName) return;
    if (Object.prototype.hasOwnProperty.call(
      DEFAULT_FILTER_IMPORT_AUDIT_QUICK_TELEMETRY_DRILLDOWN_PROFILES,
      profileName
    )) return;
    setQuickTelemetryDrilldownProfiles((prev) => {
      if (!Object.prototype.hasOwnProperty.call(prev, profileName)) return prev;
      const next = { ...prev };
      delete next[profileName];
      return next;
    });
    setQuickTelemetryDrilldownImportUndoSnapshot(null);
    setQuickTelemetryDrilldownTransferStatus(`deleted profile: ${profileName}`);
  }, [activeQuickTelemetryDrilldownProfile]);
  const triggerQuickTelemetryDrilldownImportFilePick = React.useCallback(() => {
    const input = quickTelemetryDrilldownImportFileInputRef.current;
    if (!input || typeof input.click !== "function") return;
    input.click();
  }, []);
  const handleQuickTelemetryDrilldownImportFileChange = React.useCallback((evt) => {
    const file = evt?.target?.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const text = String(reader.result || "");
      setQuickTelemetryDrilldownTransferText(text);
      setQuickTelemetryDrilldownTransferStatus(`loaded file: ${String(file.name || "-")}`);
    };
    reader.onerror = () => {
      setQuickTelemetryDrilldownTransferStatus(`failed to read file: ${String(file.name || "-")}`);
    };
    reader.readAsText(file);
    if (evt?.target) evt.target.value = "";
  }, []);
  const exportQuickTelemetryDrilldownProfilesToJson = React.useCallback(() => {
    const jsonText = serializeQuickTelemetryDrilldownProfileExportBundle(quickTelemetryDrilldownProfiles);
    setQuickTelemetryDrilldownTransferText(jsonText);
    try {
      if (typeof window === "undefined" || typeof document === "undefined" || !window.URL) {
        setQuickTelemetryDrilldownTransferStatus("exported to text buffer");
        return;
      }
      const blob = new Blob([jsonText], { type: "application/json;charset=utf-8" });
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      const ts = new Date().toISOString().replace(/[:.]/g, "-");
      anchor.href = url;
      anchor.download = `graph_lab_quick_telemetry_drilldown_profiles_${ts}.json`;
      document.body.appendChild(anchor);
      anchor.click();
      document.body.removeChild(anchor);
      window.URL.revokeObjectURL(url);
      setQuickTelemetryDrilldownTransferStatus(`exported ${Object.keys(quickTelemetryDrilldownProfiles).length} profile(s)`);
    } catch (_) {
      setQuickTelemetryDrilldownTransferStatus("exported to text buffer (file download unavailable)");
    }
  }, [quickTelemetryDrilldownProfiles]);
  const copyQuickTelemetryDrilldownProfilesJson = React.useCallback(async () => {
    const jsonText = serializeQuickTelemetryDrilldownProfileExportBundle(quickTelemetryDrilldownProfiles);
    setQuickTelemetryDrilldownTransferText(jsonText);
    try {
      if (typeof navigator !== "undefined" && navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(jsonText);
        setQuickTelemetryDrilldownTransferStatus(`copied ${Object.keys(quickTelemetryDrilldownProfiles).length} profile(s) to clipboard`);
        return;
      }
      setQuickTelemetryDrilldownTransferStatus("clipboard unavailable; copy from text buffer");
    } catch (_) {
      setQuickTelemetryDrilldownTransferStatus("clipboard write failed; copy from text buffer");
    }
  }, [quickTelemetryDrilldownProfiles]);
  const importQuickTelemetryDrilldownProfilesFromText = React.useCallback(() => {
    if (parsedQuickTelemetryDrilldownProfileImportPayload.empty) {
      setQuickTelemetryDrilldownTransferStatus("import skipped: empty payload");
      return;
    }
    if (parsedQuickTelemetryDrilldownProfileImportPayload.error) {
      setQuickTelemetryDrilldownTransferStatus(
        `import failed: ${parsedQuickTelemetryDrilldownProfileImportPayload.error}`
      );
      return;
    }
    const imported = parsedQuickTelemetryDrilldownProfileImportPayload.imported;
    const names = imported && typeof imported === "object"
      ? selectedQuickTelemetryDrilldownImportNames.filter((name) => Object.prototype.hasOwnProperty.call(imported, name))
      : [];
    if (names.length === 0) {
      setQuickTelemetryDrilldownTransferStatus("import skipped: select profiles");
      return;
    }
    const selectedImported = {};
    names.forEach((name) => {
      selectedImported[name] = imported[name];
    });
    if (Object.keys(selectedImported).length === 0) {
      setQuickTelemetryDrilldownTransferStatus("import skipped: no profiles");
      return;
    }
    if (quickTelemetryDrilldownImportHasChangedOverwrite && !quickTelemetryDrilldownImportOverwriteConfirmChecked) {
      setQuickTelemetryDrilldownTransferStatus("import blocked: confirm overwrite changed profiles");
      return;
    }
    const beforeProfiles = cloneNormalizedQuickTelemetryDrilldownProfiles(quickTelemetryDrilldownProfiles);
    const beforeActive = String(activeQuickTelemetryDrilldownProfile || "default");
    const beforeDraft = String(
      quickTelemetryDrilldownProfileDraft || CONTRACT_OVERLAY_DEFAULT_PREFS.quickTelemetryDrilldownProfileDraft
    );
    setQuickTelemetryDrilldownProfiles((prev) => ({
      ...prev,
      ...selectedImported,
    }));
    setQuickTelemetryDrilldownImportUndoSnapshot({
      imported_at_iso: new Date().toISOString(),
      profiles: beforeProfiles,
      active_profile: beforeActive,
      draft_profile: beforeDraft,
    });
    setQuickTelemetryDrilldownImportOverwriteConfirmChecked(false);
    if (names.length > 0) {
      setQuickTelemetryDrilldownProfileDraft(String(names[0]));
    }
    let newCount = 0;
    let changedOverwrite = 0;
    let changedBuiltin = 0;
    selectedQuickTelemetryDrilldownImportRows.forEach((row) => {
      if (row.conflict === "new") {
        newCount += 1;
        return;
      }
      if (!row.changed) return;
      changedOverwrite += 1;
      if (row.conflict === "overwrite_builtin") changedBuiltin += 1;
    });
    const builtinTag = changedBuiltin > 0 ? `, built-in overwrite ${changedBuiltin}` : "";
    setQuickTelemetryDrilldownTransferStatus(
      `imported ${names.length} profile(s); new ${newCount}, overwrite ${changedOverwrite}${builtinTag} (undo available)`
    );
  }, [
    activeQuickTelemetryDrilldownProfile,
    parsedQuickTelemetryDrilldownProfileImportPayload.empty,
    parsedQuickTelemetryDrilldownProfileImportPayload.error,
    parsedQuickTelemetryDrilldownProfileImportPayload.imported,
    quickTelemetryDrilldownImportHasChangedOverwrite,
    quickTelemetryDrilldownImportOverwriteConfirmChecked,
    quickTelemetryDrilldownProfileDraft,
    quickTelemetryDrilldownProfiles,
    selectedQuickTelemetryDrilldownImportNames,
    selectedQuickTelemetryDrilldownImportRows,
  ]);
  const undoLastQuickTelemetryDrilldownProfileImport = React.useCallback(() => {
    const snap = quickTelemetryDrilldownImportUndoSnapshot;
    if (!snap || typeof snap !== "object") {
      setQuickTelemetryDrilldownTransferStatus("undo skipped: no import snapshot");
      return;
    }
    const restoredProfiles = cloneNormalizedQuickTelemetryDrilldownProfiles(snap.profiles);
    if (Object.keys(restoredProfiles).length === 0) {
      setQuickTelemetryDrilldownTransferStatus("undo failed: invalid snapshot");
      return;
    }
    setQuickTelemetryDrilldownProfiles(restoredProfiles);
    setActiveQuickTelemetryDrilldownProfile(String(snap.active_profile || "default"));
    setQuickTelemetryDrilldownProfileDraft(
      String(snap.draft_profile || CONTRACT_OVERLAY_DEFAULT_PREFS.quickTelemetryDrilldownProfileDraft)
    );
    setQuickTelemetryDrilldownImportUndoSnapshot(null);
    setQuickTelemetryDrilldownImportOverwriteConfirmChecked(false);
    setQuickTelemetryDrilldownTransferStatus(
      `undo restored drilldown profiles (${String(snap.imported_at_iso || "-")})`
    );
  }, [quickTelemetryDrilldownImportUndoSnapshot]);
  const shortcutActionByKey = React.useMemo(() => {
    const map = new Map();
    SHORTCUT_ACTION_DEFS.forEach((def) => {
      const actionId = String(def.id || "");
      const token = normalizeShortcutToken(shortcutBindings[actionId]);
      if (!actionId || !token) return;
      if (!map.has(token)) {
        map.set(token, actionId);
      }
    });
    return map;
  }, [shortcutBindings]);
  const shortcutConflictText = React.useMemo(() => {
    const reverse = new Map();
    SHORTCUT_ACTION_DEFS.forEach((def) => {
      const actionId = String(def.id || "");
      const token = normalizeShortcutToken(shortcutBindings[actionId]);
      if (!actionId || !token) return;
      const bag = reverse.get(token) || [];
      bag.push(String(def.label || actionId));
      reverse.set(token, bag);
    });
    const conflicts = [];
    reverse.forEach((labels, token) => {
      if (labels.length <= 1) return;
      conflicts.push(`${token}: ${labels.join("/")}`);
    });
    return conflicts.join(" | ");
  }, [shortcutBindings]);
  const conflictActionSet = React.useMemo(() => {
    const reverse = new Map();
    SHORTCUT_ACTION_DEFS.forEach((def) => {
      const actionId = String(def.id || "");
      const token = normalizeShortcutToken(shortcutBindings[actionId]);
      if (!actionId || !token) return;
      const bag = reverse.get(token) || [];
      bag.push(actionId);
      reverse.set(token, bag);
    });
    const out = new Set();
    reverse.forEach((actionIds) => {
      if (actionIds.length <= 1) return;
      actionIds.forEach((actionId) => out.add(actionId));
    });
    return out;
  }, [shortcutBindings]);
  const shortcutHintText = React.useMemo(
    () =>
      SHORTCUT_ACTION_DEFS
        .map((def) => {
          const actionId = String(def.id || "");
          const token = normalizeShortcutToken(shortcutBindings[actionId]) || "-";
          return `${token}(${String(def.label || actionId)})`;
        })
        .join(", "),
    [shortcutBindings]
  );
  const detailFieldSelectedCount = React.useMemo(
    () => DETAIL_FIELD_DEFS.filter((def) => Boolean(detailFieldStates[String(def.id || "")])).length,
    [detailFieldStates]
  );
  const applyDetailFieldPreset = React.useCallback((presetName) => {
    const name = String(presetName || "").trim();
    if (name === "all") {
      setDetailFieldStates(normalizeDetailFieldStates({
        timestamp_iso: true,
        event_meta: true,
        delta: true,
        snapshot: true,
        baseline: true,
        note_json: true,
      }, DEFAULT_DETAIL_FIELD_STATES));
      return;
    }
    if (name === "core") {
      setDetailFieldStates(normalizeDetailFieldStates({
        timestamp_iso: true,
        event_meta: true,
        delta: true,
        snapshot: false,
        baseline: false,
        note_json: false,
      }, DEFAULT_DETAIL_FIELD_STATES));
    }
  }, []);
  const toggleDetailField = React.useCallback((fieldId) => {
    const id = String(fieldId || "");
    if (!id) return;
    setDetailFieldStates((prev) => {
      const next = normalizeDetailFieldStates(
        {
          ...prev,
          [id]: !Boolean(prev[id]),
        },
        prev
      );
      return next;
    });
  }, []);
  const formatRowDetailText = React.useCallback((row) => {
    const snapshot = row?.snapshot && typeof row.snapshot === "object" ? row.snapshot : {};
    const baseline = row?.baseline && typeof row.baseline === "object" ? row.baseline : {};
    const delta = row?.delta && typeof row.delta === "object" ? row.delta : {};
    const note = row?.note && typeof row.note === "object" ? row.note : {};
    const lines = [];
    if (detailFieldStates.timestamp_iso) {
      lines.push(`timestamp_iso: ${formatTimestampIso(row?.timestamp_ms)}`);
    }
    if (detailFieldStates.event_meta) {
      lines.push(`event_source: ${String(row?.event_source || "-")}`);
      lines.push(`graph_run_id: ${String(row?.graph_run_id || "-")}`);
    }
    if (detailFieldStates.delta) {
      lines.push(`delta(unique/attempt): ${formatSigned(delta.unique_warning_count)}/${formatSigned(delta.attempt_count_total)}`);
    }
    if (detailFieldStates.snapshot) {
      lines.push(`snapshot(unique/attempt): ${Number(snapshot.unique_warning_count || 0)}/${Number(snapshot.attempt_count_total || 0)}`);
    }
    if (detailFieldStates.baseline) {
      lines.push(`baseline(unique/attempt): ${Number(baseline.unique_warning_count || 0)}/${Number(baseline.attempt_count_total || 0)}`);
    }
    if (detailFieldStates.note_json) {
      let noteJson = "{}";
      try {
        noteJson = JSON.stringify(note, null, 2);
      } catch (_) {
        noteJson = String(note);
      }
      lines.push("note_json:");
      lines.push(noteJson);
    }
    if (lines.length === 0) {
      lines.push("(no detail fields selected)");
    }
    return lines.join("\n");
  }, [detailFieldStates]);
  const copyTextToClipboard = React.useCallback(async (text, label) => {
    const body = String(text || "");
    if (!body.trim()) {
      setDetailCopyStatus("copy skipped: empty detail payload");
      return;
    }
    try {
      if (typeof navigator !== "undefined" && navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(body);
        setDetailCopyStatus(`copied: ${String(label || "details")}`);
        return;
      }
      setDetailCopyStatus("clipboard unavailable");
    } catch (_) {
      setDetailCopyStatus("clipboard write failed");
    }
  }, []);
  const copyVisibleDetailRows = React.useCallback(async () => {
    if (!Array.isArray(visibleRows) || visibleRows.length === 0) {
      setDetailCopyStatus("copy skipped: no visible rows");
      return;
    }
    const payload = visibleRows
      .map((row, localIdx) => {
        const idx = rowWindowOffset + localIdx;
        const runId = String(row?.graph_run_id || "-");
        const source = String(row?.event_source || "-");
        return [
          `row#${idx + 1} | run=${runId} | source=${source}`,
          formatRowDetailText(row),
        ].join("\n");
      })
      .join("\n\n---\n\n");
    await copyTextToClipboard(payload, `visible_rows:${visibleRows.length}`);
  }, [copyTextToClipboard, formatRowDetailText, rowWindowOffset, visibleRows]);
  const copySingleRowDetails = React.useCallback(async (row, idx) => {
    const source = String(row?.event_source || "-");
    const runId = String(row?.graph_run_id || "-");
    const header = `row#${Number(idx) + 1} | run=${runId} | source=${source}`;
    const payload = [header, formatRowDetailText(row)].join("\n");
    await copyTextToClipboard(payload, `row:${Number(idx) + 1}`);
  }, [copyTextToClipboard, formatRowDetailText]);
  const applyFilterPresetConfig = React.useCallback((rawConfig) => {
    const cfg = normalizeFilterPresetConfig(rawConfig, DEFAULT_FILTER_PRESETS.default);
    setSourceFilter(cfg.sourceFilter);
    setSeverityFilter(cfg.severityFilter);
    setPolicyFilter(cfg.policyFilter);
    setPinnedRunId(cfg.pinnedRunId);
    setNonZeroOnly(Boolean(cfg.nonZeroOnly));
    setGateHistoryLimit(String(cfg.gateHistoryLimit));
    setGateHistoryPages(String(cfg.gateHistoryPages));
    setRowWindowSizeText(String(cfg.rowWindowSizeText));
    setRowWindowOffset(0);
  }, []);
  const filterPresetOptions = React.useMemo(() => {
    const names = Object.keys(filterPresets).map((name) => String(name || "").trim()).filter(Boolean);
    names.sort((a, b) => a.localeCompare(b));
    if (!names.includes("default")) return names;
    return ["default", ...names.filter((name) => name !== "default")];
  }, [filterPresets]);
  const normalizedFilterPresetDraft = React.useMemo(
    () => normalizeFilterPresetName(filterPresetDraft),
    [filterPresetDraft]
  );
  const activeFilterPresetIsBuiltin = React.useMemo(
    () => Object.prototype.hasOwnProperty.call(DEFAULT_FILTER_PRESETS, activeFilterPreset),
    [activeFilterPreset]
  );
  const parsedFilterImportPayload = React.useMemo(() => {
    const text = String(filterTransferText || "").trim();
    if (!text) {
      return {
        imported: null,
        error: "",
        empty: true,
      };
    }
    try {
      return {
        imported: parseFilterPresetImportText(text),
        error: "",
        empty: false,
      };
    } catch (err) {
      return {
        imported: null,
        error: String(err?.message || "parse error"),
        empty: false,
      };
    }
  }, [filterTransferText]);
  const parsedFilterImportAuditDeepLinkPayload = React.useMemo(() => {
    const text = String(filterTransferText || "").trim();
    if (!text) {
      return {
        bundle: null,
        error: "",
        empty: true,
      };
    }
    try {
      return {
        bundle: parseFilterImportAuditDeepLinkBundleText(text),
        error: "",
        empty: false,
      };
    } catch (err) {
      return {
        bundle: null,
        error: String(err?.message || "parse error"),
        empty: false,
      };
    }
  }, [filterTransferText]);
  const filterImportAuditDeepLinkPreview = React.useMemo(() => {
    if (parsedFilterImportAuditDeepLinkPayload.empty) {
      return "audit bundle: waiting for JSON payload";
    }
    if (parsedFilterImportAuditDeepLinkPayload.error) {
      return `audit bundle: invalid payload (${parsedFilterImportAuditDeepLinkPayload.error})`;
    }
    const bundle = parsedFilterImportAuditDeepLinkPayload.bundle;
    const schemaVersion = Number(bundle?.schema_version || 0);
    const pinned = String(bundle?.pinned_preset_id || "-");
    const entry = String(bundle?.active_entry_id || "-");
    return `audit bundle: valid (schema:${schemaVersion}, pinned:${pinned}, entry:${entry})`;
  }, [parsedFilterImportAuditDeepLinkPayload.bundle, parsedFilterImportAuditDeepLinkPayload.empty, parsedFilterImportAuditDeepLinkPayload.error]);
  const filterImportRows = React.useMemo(() => {
    const imported = parsedFilterImportPayload.imported;
    if (!imported || typeof imported !== "object") return [];
    return Object.keys(imported)
      .sort((a, b) => String(a).localeCompare(String(b)))
      .map((name) => {
        const hasExisting = Object.prototype.hasOwnProperty.call(filterPresets, name);
        if (!hasExisting) {
          return { name, conflict: "new" };
        }
        if (Object.prototype.hasOwnProperty.call(DEFAULT_FILTER_PRESETS, name)) {
          return { name, conflict: "overwrite_builtin" };
        }
        return { name, conflict: "overwrite_custom" };
      });
  }, [filterPresets, parsedFilterImportPayload.imported]);
  const filterImportNamesSignature = React.useMemo(
    () => filterImportRows.map((row) => row.name).join("|"),
    [filterImportRows]
  );
  React.useEffect(() => {
    if (!filterImportNamesSignature) {
      setFilterImportSelection({});
      return;
    }
    setFilterImportSelection((prev) => {
      const base = prev && typeof prev === "object" && !Array.isArray(prev) ? prev : {};
      const next = {};
      filterImportRows.forEach((row) => {
        const name = String(row.name || "");
        if (!name) return;
        if (Object.prototype.hasOwnProperty.call(base, name)) {
          next[name] = Boolean(base[name]);
          return;
        }
        next[name] = true;
      });
      return next;
    });
  }, [filterImportNamesSignature, filterImportRows]);
  const selectedFilterImportNames = React.useMemo(
    () =>
      filterImportRows
        .map((row) => String(row.name || ""))
        .filter((name) => name.length > 0 && Boolean(filterImportSelection[name])),
    [filterImportRows, filterImportSelection]
  );
  const filterImportPreview = React.useMemo(() => {
    if (parsedFilterImportPayload.empty) {
      return "preview: waiting for JSON payload";
    }
    if (parsedFilterImportPayload.error) {
      return `preview: invalid payload (${parsedFilterImportPayload.error})`;
    }
    const selectedSet = new Set(selectedFilterImportNames);
    let selectedNew = 0;
    let selectedOverwrite = 0;
    let selectedBuiltinOverwrite = 0;
    filterImportRows.forEach((row) => {
      const name = String(row?.name || "");
      if (!selectedSet.has(name)) return;
      if (row.conflict === "new") {
        selectedNew += 1;
        return;
      }
      selectedOverwrite += 1;
      if (row.conflict === "overwrite_builtin") {
        selectedBuiltinOverwrite += 1;
      }
    });
    const modeToken = filterImportMode === "replace_custom" ? "replace_custom" : "merge";
    if (selectedFilterImportNames.length === 0) {
      return `preview: total ${filterImportRows.length}, selected 0, mode ${modeToken} (select presets to import)`;
    }
    const builtinTag = selectedBuiltinOverwrite > 0 ? `, built-in overwrite ${selectedBuiltinOverwrite}` : "";
    return [
      `preview: total ${filterImportRows.length}`,
      `selected ${selectedFilterImportNames.length}`,
      `new ${selectedNew}`,
      `overwrite ${selectedOverwrite}${builtinTag}`,
      `mode ${modeToken}`,
    ].join(", ");
  }, [
    filterImportMode,
    filterImportRows,
    parsedFilterImportPayload.empty,
    parsedFilterImportPayload.error,
    selectedFilterImportNames,
  ]);
  const filterImportPreviewIsValid = React.useMemo(
    () => !parsedFilterImportPayload.empty && !parsedFilterImportPayload.error,
    [parsedFilterImportPayload.empty, parsedFilterImportPayload.error]
  );
  const replaceImportNeedsConfirmation = React.useMemo(
    () => filterImportMode === "replace_custom" && selectedFilterImportNames.length > 0,
    [filterImportMode, selectedFilterImportNames]
  );
  const filterImportAuditRowsFiltered = React.useMemo(() => {
    const rows = Array.isArray(filterImportAuditTrail) ? filterImportAuditTrail : [];
    const kindFilter = String(filterImportAuditKindFilter || "all");
    const modeFilter = String(filterImportAuditModeFilter || "all");
    const queryTokens = String(filterImportAuditSearchText || "")
      .toLowerCase()
      .trim()
      .split(/\s+/)
      .filter(Boolean);
    return rows.filter((entry) => {
      const kind = String(entry?.kind || "import");
      const mode = String(entry?.mode || "merge");
      if (kindFilter !== "all" && kind !== kindFilter) return false;
      if (modeFilter !== "all" && mode !== modeFilter) return false;
      if (queryTokens.length === 0) return true;
      const haystack = [
        String(entry?.id || ""),
        String(entry?.timestamp_iso || ""),
        kind,
        mode,
        String(entry?.note || ""),
        ...sanitizeAuditNameList(entry?.selected_names),
        ...sanitizeAuditNameList(entry?.added_names),
        ...sanitizeAuditNameList(entry?.removed_names),
      ]
        .join(" ")
        .toLowerCase();
      return queryTokens.every((token) => haystack.includes(token));
    });
  }, [
    filterImportAuditKindFilter,
    filterImportAuditModeFilter,
    filterImportAuditSearchText,
    filterImportAuditTrail,
  ]);
  const filterImportAuditQueryActive = React.useMemo(
    () =>
      String(filterImportAuditSearchText || "").trim().length > 0
      || String(filterImportAuditKindFilter || "all") !== "all"
      || String(filterImportAuditModeFilter || "all") !== "all",
    [filterImportAuditKindFilter, filterImportAuditModeFilter, filterImportAuditSearchText]
  );
  const activeFilterImportAuditQueryPresetId = React.useMemo(() => {
    const search = String(filterImportAuditSearchText || "").trim().toLowerCase();
    const kind = String(filterImportAuditKindFilter || "all");
    const mode = String(filterImportAuditModeFilter || "all");
    const match = FILTER_IMPORT_AUDIT_QUERY_PRESETS.find((preset) => (
      String(preset.search || "").trim().toLowerCase() === search
      && String(preset.kind || "all") === kind
      && String(preset.mode || "all") === mode
    ));
    return match ? String(match.id || "") : "custom";
  }, [filterImportAuditKindFilter, filterImportAuditModeFilter, filterImportAuditSearchText]);
  const filterImportAuditPresetPinnable = React.useMemo(
    () => activeFilterImportAuditQueryPresetId !== "custom",
    [activeFilterImportAuditQueryPresetId]
  );
  const filterImportAuditPinnedPresetActive = React.useMemo(
    () => (
      Boolean(filterImportAuditPinnedPresetId)
      && String(filterImportAuditPinnedPresetId) === String(activeFilterImportAuditQueryPresetId)
    ),
    [activeFilterImportAuditQueryPresetId, filterImportAuditPinnedPresetId]
  );
  const activeFilterImportAuditRestorePresetId = React.useMemo(() => {
    const match = FILTER_IMPORT_AUDIT_RESTORE_PRESETS.find((preset) => (
      Boolean(preset?.query) === Boolean(filterImportAuditRestoreQueryChecked)
      && Boolean(preset?.paging) === Boolean(filterImportAuditRestorePagingChecked)
      && Boolean(preset?.pinned) === Boolean(filterImportAuditRestorePinnedPresetChecked)
      && Boolean(preset?.entry) === Boolean(filterImportAuditRestoreActiveEntryChecked)
    ));
    return match ? String(match.id || "") : "custom";
  }, [
    filterImportAuditRestoreActiveEntryChecked,
    filterImportAuditRestorePagingChecked,
    filterImportAuditRestorePinnedPresetChecked,
    filterImportAuditRestoreQueryChecked,
  ]);
  const activeFilterImportAuditQuickApplyOptionId = React.useMemo(() => {
    const match = FILTER_IMPORT_AUDIT_QUICK_APPLY_OPTIONS.find((option) => (
      Boolean(option?.query) === Boolean(filterImportAuditRestoreQueryChecked)
      && Boolean(option?.paging) === Boolean(filterImportAuditRestorePagingChecked)
      && Boolean(option?.pinned) === Boolean(filterImportAuditRestorePinnedPresetChecked)
      && Boolean(option?.entry) === Boolean(filterImportAuditRestoreActiveEntryChecked)
    ));
    return match ? String(match.id || "") : "custom";
  }, [
    filterImportAuditRestoreActiveEntryChecked,
    filterImportAuditRestorePagingChecked,
    filterImportAuditRestorePinnedPresetChecked,
    filterImportAuditRestoreQueryChecked,
  ]);
  const filterImportAuditRestoreScopeHint = React.useMemo(() => [
    `restore:q${filterImportAuditRestoreQueryChecked ? 1 : 0}`,
    `p${filterImportAuditRestorePagingChecked ? 1 : 0}`,
    `pin${filterImportAuditRestorePinnedPresetChecked ? 1 : 0}`,
    `e${filterImportAuditRestoreActiveEntryChecked ? 1 : 0}`,
    `preset:${activeFilterImportAuditRestorePresetId}`,
    `quick:${activeFilterImportAuditQuickApplyOptionId}`,
    `sync:${filterImportAuditQuickApplySyncRestoreChecked ? "on" : "off"}`,
  ].join(" "), [
    activeFilterImportAuditQuickApplyOptionId,
    activeFilterImportAuditRestorePresetId,
    filterImportAuditRestoreActiveEntryChecked,
    filterImportAuditRestorePagingChecked,
    filterImportAuditRestorePinnedPresetChecked,
    filterImportAuditQuickApplySyncRestoreChecked,
    filterImportAuditRestoreQueryChecked,
  ]);
  const filterImportAuditPinChipVisibility = React.useMemo(() => {
    const mode = normalizeFilterImportAuditPinChipFilter(filterImportAuditPinChipFilter);
    const showCustom = activeFilterImportAuditQueryPresetId === "custom";
    if (mode === "state") {
      return { pinned: true, active: true, custom: false, shortcut: false };
    }
    if (mode === "context") {
      return { pinned: false, active: false, custom: showCustom, shortcut: true };
    }
    if (mode === "shortcut") {
      return { pinned: false, active: false, custom: false, shortcut: true };
    }
    return { pinned: true, active: true, custom: showCustom, shortcut: true };
  }, [activeFilterImportAuditQueryPresetId, filterImportAuditPinChipFilter]);
  const filterImportAuditPinOperatorHint = React.useMemo(() => [
    `pin-op:pinned:${filterImportAuditPinnedPresetId || "-"}`,
    `active:${activeFilterImportAuditQueryPresetId}`,
    `state:${filterImportAuditPinnedPresetActive ? "active" : "idle"}`,
    `chips:${filterImportAuditPinChipFilter}`,
  ].join(" "), [
    activeFilterImportAuditQueryPresetId,
    filterImportAuditPinChipFilter,
    filterImportAuditPinnedPresetActive,
    filterImportAuditPinnedPresetId,
  ]);
  const filterImportAuditQuickApplyTelemetrySummary = React.useMemo(() => {
    const rows = Array.isArray(filterImportAuditQuickApplyTelemetry) ? filterImportAuditQuickApplyTelemetry : [];
    const total = rows.length;
    const success = rows.filter((row) => Boolean(row?.apply_ok)).length;
    const failed = total - success;
    const latest = total > 0 ? rows[0] : null;
    const latestOption = String(latest?.option_id || "-");
    const recentRows = rows.slice(0, FILTER_IMPORT_AUDIT_QUICK_TREND_WINDOW);
    const recentTotal = recentRows.length;
    const recentSuccess = recentRows.filter((row) => Boolean(row?.apply_ok)).length;
    return `quick-telemetry total:${total} ok:${success} fail:${failed} latest:${latestOption} recent:${recentSuccess}/${recentTotal}`;
  }, [filterImportAuditQuickApplyTelemetry]);
  const filterImportAuditQuickTelemetryTrend = React.useMemo(() => {
    const rows = Array.isArray(filterImportAuditQuickApplyTelemetry) ? filterImportAuditQuickApplyTelemetry : [];
    const recentRows = rows.slice(0, FILTER_IMPORT_AUDIT_QUICK_TREND_WINDOW);
    const recentCount = recentRows.length;
    const recentOk = recentRows.filter((row) => Boolean(row?.apply_ok)).length;
    const recentFail = recentCount - recentOk;
    let failStreak = 0;
    for (let idx = 0; idx < recentRows.length; idx += 1) {
      if (Boolean(recentRows[idx]?.apply_ok)) break;
      failStreak += 1;
    }
    const syncApplied = recentRows.filter((row) => Boolean(row?.sync_applied)).length;
    const latest = recentCount > 0 ? recentRows[0] : null;
    const recentOkPct = recentCount > 0 ? Math.round((recentOk / recentCount) * 100) : 0;
    const syncAppliedPct = recentCount > 0 ? Math.round((syncApplied / recentCount) * 100) : 0;
    const latestReasonRaw = String(latest?.apply_reason || "-").trim();
    const latestReason = latestReasonRaw.length > 36
      ? `${latestReasonRaw.slice(0, 36)}...`
      : (latestReasonRaw || "-");
    const latestOption = String(latest?.option_id || "-").trim() || "-";
    return {
      recentCount,
      recentOk,
      recentFail,
      recentOkPct,
      failStreak,
      syncApplied,
      syncAppliedPct,
      latestReason,
      latestOption,
    };
  }, [filterImportAuditQuickApplyTelemetry]);
  const filterImportAuditQuickTelemetryReasonQueryNormalized = React.useMemo(
    () => String(filterImportAuditQuickTelemetryReasonQuery || "").trim().toLowerCase().slice(0, FILTER_IMPORT_AUDIT_QUICK_REASON_QUERY_MAX),
    [filterImportAuditQuickTelemetryReasonQuery]
  );
  const activeFilterImportAuditQuickTelemetryDrilldownPresetId = React.useMemo(() => {
    const match = FILTER_IMPORT_AUDIT_QUICK_DRILLDOWN_PRESETS.find((preset) => (
      Boolean(preset?.failure_only) === Boolean(filterImportAuditQuickTelemetryFailureOnlyChecked)
      && String(preset?.reason_query || "").trim().toLowerCase() === filterImportAuditQuickTelemetryReasonQueryNormalized
    ));
    return match ? String(match.id || "") : "custom";
  }, [
    filterImportAuditQuickTelemetryFailureOnlyChecked,
    filterImportAuditQuickTelemetryReasonQueryNormalized,
  ]);
  const filterImportAuditQuickTelemetryRowsDrilldown = React.useMemo(() => {
    const rows = Array.isArray(filterImportAuditQuickApplyTelemetry) ? filterImportAuditQuickApplyTelemetry : [];
    return rows.filter((row) => {
      if (filterImportAuditQuickTelemetryFailureOnlyChecked && Boolean(row?.apply_ok)) {
        return false;
      }
      if (!filterImportAuditQuickTelemetryReasonQueryNormalized) {
        return true;
      }
      const haystack = [
        String(row?.apply_reason || ""),
        String(row?.option_id || ""),
        String(row?.restore_tag || ""),
      ].join(" ").toLowerCase();
      return haystack.includes(filterImportAuditQuickTelemetryReasonQueryNormalized);
    });
  }, [
    filterImportAuditQuickApplyTelemetry,
    filterImportAuditQuickTelemetryFailureOnlyChecked,
    filterImportAuditQuickTelemetryReasonQueryNormalized,
  ]);
  const filterImportAuditQuickTelemetryReasonChips = React.useMemo(() => {
    const rows = Array.isArray(filterImportAuditQuickTelemetryRowsDrilldown)
      ? filterImportAuditQuickTelemetryRowsDrilldown
      : [];
    const counter = new Map();
    rows.forEach((row) => {
      const key = String(row?.apply_reason || "unknown").trim() || "unknown";
      counter.set(key, Number(counter.get(key) || 0) + 1);
    });
    return Array.from(counter.entries())
      .sort((a, b) => {
        const dc = Number(b[1] || 0) - Number(a[1] || 0);
        if (dc !== 0) return dc;
        return String(a[0] || "").localeCompare(String(b[0] || ""));
      })
      .slice(0, FILTER_IMPORT_AUDIT_QUICK_REASON_CHIP_LIMIT)
      .map(([reason, count]) => ({
        reason: String(reason || "unknown"),
        count: Number(count || 0),
      }));
  }, [filterImportAuditQuickTelemetryRowsDrilldown]);
  const filterImportAuditQuickTelemetryDrilldownSummary = React.useMemo(() => {
    const total = Array.isArray(filterImportAuditQuickApplyTelemetry) ? filterImportAuditQuickApplyTelemetry.length : 0;
    const visibleRows = Array.isArray(filterImportAuditQuickTelemetryRowsDrilldown)
      ? filterImportAuditQuickTelemetryRowsDrilldown
      : [];
    const visible = visibleRows.length;
    const failed = visibleRows.filter((row) => !Boolean(row?.apply_ok)).length;
    const latest = visible > 0 ? visibleRows[0] : null;
    const latestReason = String(latest?.apply_reason || "-").slice(0, 28) || "-";
    return `drilldown ${visible}/${total} fail:${failed} preset:${activeFilterImportAuditQuickTelemetryDrilldownPresetId} filter:${filterImportAuditQuickTelemetryReasonQueryNormalized || "-"} latest:${latestReason}`;
  }, [
    activeFilterImportAuditQuickTelemetryDrilldownPresetId,
    filterImportAuditQuickApplyTelemetry,
    filterImportAuditQuickTelemetryReasonQueryNormalized,
    filterImportAuditQuickTelemetryRowsDrilldown,
  ]);
  const activeQuickTelemetryStrictRollbackDrillPresetId = React.useMemo(() => {
    const match = QUICK_TELEMETRY_STRICT_ROLLBACK_DRILL_PRESETS.find((preset) => (
      Boolean(preset?.failure_only) === Boolean(filterImportAuditQuickTelemetryFailureOnlyChecked)
      && String(preset?.reason_query || "").trim().toLowerCase() === filterImportAuditQuickTelemetryReasonQueryNormalized
    ));
    return match ? String(match.id || "") : "custom";
  }, [
    filterImportAuditQuickTelemetryFailureOnlyChecked,
    filterImportAuditQuickTelemetryReasonQueryNormalized,
  ]);
  const quickTelemetryDrilldownStrictRollbackChecklist = React.useMemo(() => {
    const visibleRows = Array.isArray(filterImportAuditQuickTelemetryRowsDrilldown)
      ? filterImportAuditQuickTelemetryRowsDrilldown
      : [];
    const failedVisible = visibleRows.filter((row) => !Boolean(row?.apply_ok)).length;
    const items = [
      {
        id: "mode_compat",
        label: "compat fallback mode active",
        ok: quickTelemetryDrilldownImportFilterBundleMode === "compat",
      },
      {
        id: "failure_only",
        label: "failure-only drilldown enabled",
        ok: Boolean(filterImportAuditQuickTelemetryFailureOnlyChecked),
      },
      {
        id: "reason_query",
        label: "failure tag query selected",
        ok: String(filterImportAuditQuickTelemetryReasonQueryNormalized || "").length > 0,
      },
      {
        id: "failure_rows",
        label: "matching failure rows > 0",
        ok: failedVisible > 0,
      },
    ];
    const passCount = items.filter((row) => Boolean(row.ok)).length;
    const ready = passCount === items.length;
    return {
      ready,
      pass_count: passCount,
      item_count: items.length,
      items,
      failed_visible_count: failedVisible,
      visible_count: visibleRows.length,
      active_preset_id: activeQuickTelemetryStrictRollbackDrillPresetId,
    };
  }, [
    activeQuickTelemetryStrictRollbackDrillPresetId,
    filterImportAuditQuickTelemetryFailureOnlyChecked,
    filterImportAuditQuickTelemetryReasonQueryNormalized,
    filterImportAuditQuickTelemetryRowsDrilldown,
    quickTelemetryDrilldownImportFilterBundleMode,
  ]);
  const quickTelemetryDrilldownStrictRollbackChecklistHint = React.useMemo(() => {
    const row = quickTelemetryDrilldownStrictRollbackChecklist;
    const status = row.ready ? "READY" : "HOLD";
    return [
      `rollback drill checklist: ${status} (${row.pass_count}/${row.item_count})`,
      `preset ${String(row.active_preset_id || "custom")}`,
      `fail ${Number(row.failed_visible_count || 0)}/${Number(row.visible_count || 0)}`,
    ].join(", ");
  }, [quickTelemetryDrilldownStrictRollbackChecklist]);
  const quickTelemetryDrilldownStrictRollbackChecklistPreview = React.useMemo(() => {
    const row = quickTelemetryDrilldownStrictRollbackChecklist;
    const itemTokens = row.items.map((x) => `${x.ok ? "ok" : "hold"}:${x.id}`).join(", ");
    return [
      `mode ${quickTelemetryDrilldownImportFilterBundleMode}`,
      `failure_only ${Boolean(filterImportAuditQuickTelemetryFailureOnlyChecked) ? "on" : "off"}`,
      `reason ${filterImportAuditQuickTelemetryReasonQueryNormalized || "-"}`,
      `visible_fail ${Number(row.failed_visible_count || 0)}`,
      itemTokens,
    ].join(" | ");
  }, [
    filterImportAuditQuickTelemetryFailureOnlyChecked,
    filterImportAuditQuickTelemetryReasonQueryNormalized,
    quickTelemetryDrilldownImportFilterBundleMode,
    quickTelemetryDrilldownStrictRollbackChecklist,
  ]);
  const quickTelemetryDrilldownStrictRollbackChecklistReport = React.useMemo(() => {
    const row = quickTelemetryDrilldownStrictRollbackChecklist;
    return {
      status: row.ready ? "READY" : "HOLD",
      pass_count: Number(row.pass_count || 0),
      item_count: Number(row.item_count || 0),
      failed_visible_count: Number(row.failed_visible_count || 0),
      visible_count: Number(row.visible_count || 0),
      generated_at_iso: new Date().toISOString(),
      items: Array.isArray(row.items)
        ? row.items.map((x) => ({
          id: String(x?.id || ""),
          label: String(x?.label || ""),
          ok: Boolean(x?.ok),
        }))
        : [],
    };
  }, [quickTelemetryDrilldownStrictRollbackChecklist]);
  const quickTelemetryDrilldownStrictRollbackChecklistReportPreview = React.useMemo(() => {
    const row = quickTelemetryDrilldownStrictRollbackChecklistReport;
    const itemTokens = Array.isArray(row.items)
      ? row.items.map((x) => `${x.ok ? "ok" : "hold"}:${x.id}`).join(", ")
      : "-";
    return [
      `checklist_report status=${String(row.status || "HOLD")} pass=${Number(row.pass_count || 0)}/${Number(row.item_count || 0)}`,
      `visible_fail=${Number(row.failed_visible_count || 0)}/${Number(row.visible_count || 0)}`,
      `generated_at=${String(row.generated_at_iso || "-")}`,
      itemTokens || "-",
    ].join("\n");
  }, [quickTelemetryDrilldownStrictRollbackChecklistReport]);
  const quickTelemetryStrictRollbackDrillPackagePayload = React.useMemo(() => ({
    preset_snapshot: {
      preset_id: activeQuickTelemetryStrictRollbackDrillPresetId,
      import_mode: quickTelemetryDrilldownImportFilterBundleMode,
      failure_only: filterImportAuditQuickTelemetryFailureOnlyChecked,
      reason_query: filterImportAuditQuickTelemetryReasonQueryNormalized,
      conflict_only: quickTelemetryDrilldownImportConflictOnlyChecked,
      conflict_filter: quickTelemetryDrilldownImportConflictFilter,
      name_query: quickTelemetryDrilldownImportNameQuery,
      row_cap: quickTelemetryDrilldownImportRowCap,
    },
    checklist_report: quickTelemetryDrilldownStrictRollbackChecklistReport,
    cutover_timeline_entries: quickTelemetryDrilldownStrictCutoverLedgerRows,
  }), [
    activeQuickTelemetryStrictRollbackDrillPresetId,
    filterImportAuditQuickTelemetryFailureOnlyChecked,
    filterImportAuditQuickTelemetryReasonQueryNormalized,
    quickTelemetryDrilldownImportConflictFilter,
    quickTelemetryDrilldownImportConflictOnlyChecked,
    quickTelemetryDrilldownImportFilterBundleMode,
    quickTelemetryDrilldownImportNameQuery,
    quickTelemetryDrilldownImportRowCap,
    quickTelemetryDrilldownStrictCutoverLedgerRows,
    quickTelemetryDrilldownStrictRollbackChecklistReport,
  ]);
  const quickTelemetryStrictRollbackDrillPackageBundle = React.useMemo(
    () => buildQuickTelemetryStrictRollbackDrillPackage(quickTelemetryStrictRollbackDrillPackagePayload),
    [quickTelemetryStrictRollbackDrillPackagePayload]
  );
  const parsedQuickTelemetryStrictRollbackDrillPackagePayload = React.useMemo(() => {
    const text = String(quickTelemetryDrilldownStrictRollbackPackageReplayText || "").trim();
    if (!text) {
      return {
        pkg: null,
        error: "",
        empty: true,
      };
    }
    try {
      return {
        pkg: parseQuickTelemetryStrictRollbackDrillPackageText(text),
        error: "",
        empty: false,
      };
    } catch (err) {
      return {
        pkg: null,
        error: String(err?.message || "parse error"),
        empty: false,
      };
    }
  }, [quickTelemetryDrilldownStrictRollbackPackageReplayText]);
  const quickTelemetryStrictRollbackPackageProvenanceGuard = React.useMemo(() => {
    if (parsedQuickTelemetryStrictRollbackDrillPackagePayload.empty) {
      return {
        has_guard_issue: false,
        missing_source_stamp: false,
        missing_payload_checksum: false,
        source_match: true,
        checksum_match: true,
        source_stamp: QUICK_TELEMETRY_STRICT_ROLLBACK_DRILL_PACKAGE_SOURCE_STAMP,
        payload_checksum: "",
        computed_checksum: "",
        checksum_hint: "",
      };
    }
    if (parsedQuickTelemetryStrictRollbackDrillPackagePayload.error) {
      return {
        has_guard_issue: true,
        missing_source_stamp: false,
        missing_payload_checksum: false,
        source_match: false,
        checksum_match: false,
        source_stamp: QUICK_TELEMETRY_STRICT_ROLLBACK_DRILL_PACKAGE_SOURCE_STAMP,
        payload_checksum: "",
        computed_checksum: "",
        checksum_hint: "",
      };
    }
    const guard = parsedQuickTelemetryStrictRollbackDrillPackagePayload.pkg?.provenance_guard;
    if (!guard || typeof guard !== "object") {
      return {
        has_guard_issue: true,
        missing_source_stamp: true,
        missing_payload_checksum: true,
        source_match: false,
        checksum_match: false,
        source_stamp: QUICK_TELEMETRY_STRICT_ROLLBACK_DRILL_PACKAGE_SOURCE_STAMP,
        payload_checksum: "",
        computed_checksum: "",
        checksum_hint: "",
      };
    }
    return {
      has_guard_issue: Boolean(guard.has_guard_issue),
      missing_source_stamp: Boolean(guard.missing_source_stamp),
      missing_payload_checksum: Boolean(guard.missing_payload_checksum),
      source_match: Boolean(guard.source_match),
      checksum_match: Boolean(guard.checksum_match),
      source_stamp: String(guard.source_stamp || QUICK_TELEMETRY_STRICT_ROLLBACK_DRILL_PACKAGE_SOURCE_STAMP),
      payload_checksum: String(guard.payload_checksum || ""),
      computed_checksum: String(guard.computed_checksum || ""),
      checksum_hint: String(guard.checksum_hint || ""),
    };
  }, [
    parsedQuickTelemetryStrictRollbackDrillPackagePayload.empty,
    parsedQuickTelemetryStrictRollbackDrillPackagePayload.error,
    parsedQuickTelemetryStrictRollbackDrillPackagePayload.pkg,
  ]);
  const quickTelemetryStrictRollbackPackageProvenanceHint = React.useMemo(() => {
    if (parsedQuickTelemetryStrictRollbackDrillPackagePayload.empty) {
      return "provenance guard: waiting for rollback package payload";
    }
    if (parsedQuickTelemetryStrictRollbackDrillPackagePayload.error) {
      return "provenance guard: blocked by parse error";
    }
    const guard = quickTelemetryStrictRollbackPackageProvenanceGuard;
    if (!guard.has_guard_issue) {
      return [
        "provenance guard: ok",
        `source=${guard.source_stamp}`,
        `checksum=${guard.computed_checksum || guard.payload_checksum || "-"}`,
      ].join(", ");
    }
    return [
      "provenance guard: issue detected",
      `missing_source:${guard.missing_source_stamp ? "yes" : "no"}`,
      `missing_checksum:${guard.missing_payload_checksum ? "yes" : "no"}`,
      `source_match:${guard.source_match ? "yes" : "no"}`,
      `checksum_match:${guard.checksum_match ? "yes" : "no"}`,
      guard.checksum_hint || "checksum hint unavailable",
    ].join(", ");
  }, [
    parsedQuickTelemetryStrictRollbackDrillPackagePayload.empty,
    parsedQuickTelemetryStrictRollbackDrillPackagePayload.error,
    quickTelemetryStrictRollbackPackageProvenanceGuard,
  ]);
  const quickTelemetryStrictRollbackTrustAuditProvenanceSnapshot = React.useMemo(() => {
    if (parsedQuickTelemetryStrictRollbackDrillPackagePayload.empty) {
      return normalizeQuickTelemetryStrictRollbackTrustAuditProvenanceSnapshot({
        parse_state: "empty",
        has_guard_issue: false,
        missing_source_stamp: false,
        missing_payload_checksum: false,
        source_match: true,
        checksum_match: true,
        source_stamp: QUICK_TELEMETRY_STRICT_ROLLBACK_DRILL_PACKAGE_SOURCE_STAMP,
        payload_checksum: "",
        computed_checksum: "",
        checksum_hint: "",
        package_kind: QUICK_TELEMETRY_STRICT_ROLLBACK_DRILL_PACKAGE_KIND,
        package_schema_version: QUICK_TELEMETRY_STRICT_ROLLBACK_DRILL_PACKAGE_SCHEMA_VERSION,
        package_preset_id: "custom",
        package_import_mode: "compat",
        package_timeline_entry_count: 0,
        package_exported_at_iso: "-",
      });
    }
    if (parsedQuickTelemetryStrictRollbackDrillPackagePayload.error) {
      return normalizeQuickTelemetryStrictRollbackTrustAuditProvenanceSnapshot({
        parse_state: "error",
        parse_error: parsedQuickTelemetryStrictRollbackDrillPackagePayload.error,
        has_guard_issue: true,
        missing_source_stamp: quickTelemetryStrictRollbackPackageProvenanceGuard.missing_source_stamp,
        missing_payload_checksum: quickTelemetryStrictRollbackPackageProvenanceGuard.missing_payload_checksum,
        source_match: quickTelemetryStrictRollbackPackageProvenanceGuard.source_match,
        checksum_match: quickTelemetryStrictRollbackPackageProvenanceGuard.checksum_match,
        source_stamp: quickTelemetryStrictRollbackPackageProvenanceGuard.source_stamp,
        payload_checksum: quickTelemetryStrictRollbackPackageProvenanceGuard.payload_checksum,
        computed_checksum: quickTelemetryStrictRollbackPackageProvenanceGuard.computed_checksum,
        checksum_hint: quickTelemetryStrictRollbackPackageProvenanceGuard.checksum_hint,
        package_kind: QUICK_TELEMETRY_STRICT_ROLLBACK_DRILL_PACKAGE_KIND,
        package_schema_version: QUICK_TELEMETRY_STRICT_ROLLBACK_DRILL_PACKAGE_SCHEMA_VERSION,
        package_preset_id: "custom",
        package_import_mode: "compat",
        package_timeline_entry_count: 0,
        package_exported_at_iso: "-",
      });
    }
    const pkg = parsedQuickTelemetryStrictRollbackDrillPackagePayload.pkg || {};
    const snapshot = pkg.preset_snapshot && typeof pkg.preset_snapshot === "object"
      ? pkg.preset_snapshot
      : {};
    const timelineRows = Array.isArray(pkg.cutover_timeline_entries) ? pkg.cutover_timeline_entries : [];
    return normalizeQuickTelemetryStrictRollbackTrustAuditProvenanceSnapshot({
      parse_state: "ready",
      parse_error: "",
      has_guard_issue: quickTelemetryStrictRollbackPackageProvenanceGuard.has_guard_issue,
      missing_source_stamp: quickTelemetryStrictRollbackPackageProvenanceGuard.missing_source_stamp,
      missing_payload_checksum: quickTelemetryStrictRollbackPackageProvenanceGuard.missing_payload_checksum,
      source_match: quickTelemetryStrictRollbackPackageProvenanceGuard.source_match,
      checksum_match: quickTelemetryStrictRollbackPackageProvenanceGuard.checksum_match,
      source_stamp: quickTelemetryStrictRollbackPackageProvenanceGuard.source_stamp,
      payload_checksum: quickTelemetryStrictRollbackPackageProvenanceGuard.payload_checksum,
      computed_checksum: quickTelemetryStrictRollbackPackageProvenanceGuard.computed_checksum,
      checksum_hint: quickTelemetryStrictRollbackPackageProvenanceGuard.checksum_hint,
      package_kind: String(pkg.kind || QUICK_TELEMETRY_STRICT_ROLLBACK_DRILL_PACKAGE_KIND),
      package_schema_version: Number(pkg.schema_version || QUICK_TELEMETRY_STRICT_ROLLBACK_DRILL_PACKAGE_SCHEMA_VERSION),
      package_preset_id: String(snapshot.preset_id || "custom"),
      package_import_mode: String(snapshot.import_mode || "compat"),
      package_timeline_entry_count: timelineRows.length,
      package_exported_at_iso: String(pkg.exported_at_iso || "-"),
    });
  }, [
    parsedQuickTelemetryStrictRollbackDrillPackagePayload.empty,
    parsedQuickTelemetryStrictRollbackDrillPackagePayload.error,
    parsedQuickTelemetryStrictRollbackDrillPackagePayload.pkg,
    quickTelemetryStrictRollbackPackageProvenanceGuard,
  ]);
  const quickTelemetryStrictRollbackPackageTrustPolicyHint = React.useMemo(() => {
    const mode = normalizeQuickTelemetryStrictRollbackPackageTrustPolicy(
      quickTelemetryStrictRollbackPackageTrustPolicy
    );
    if (mode === "strict_reject") {
      return "trust policy: strict_reject (provenance issue requires explicit override replay)";
    }
    return "trust policy: compat_confirm (provenance issue follows confirm replay guard)";
  }, [quickTelemetryStrictRollbackPackageTrustPolicy]);
  const quickTelemetryStrictRollbackPackageOverrideLogRows = React.useMemo(
    () => buildQuickTelemetryStrictRollbackOverrideLogBundle(
      quickTelemetryDrilldownStrictRollbackPackageOverrideLog
    ).entries,
    [quickTelemetryDrilldownStrictRollbackPackageOverrideLog]
  );
  const quickTelemetryStrictRollbackPackageOverrideLogPreview = React.useMemo(() => {
    if (quickTelemetryStrictRollbackPackageOverrideLogRows.length === 0) {
      return "override log: no override replay events";
    }
    return quickTelemetryStrictRollbackPackageOverrideLogRows
      .map((row, idx) => [
        `#${idx + 1}`,
        String(row.timestamp_iso || "-"),
        String(row.event_kind || "override_replay"),
        `policy=${String(row.policy_mode || "-")}`,
        `preset=${String(row.preset_id || "-")}`,
        `provenance_issue=${Boolean(row.provenance_issue) ? "yes" : "no"}`,
        `delta=${Boolean(row.checklist_delta) ? "yes" : "no"}`,
        `reason=${String(row.override_reason || "-") || "-"}`,
      ].join(" | "))
      .join("\n");
  }, [quickTelemetryStrictRollbackPackageOverrideLogRows]);
  const quickTelemetryStrictRollbackPackageOverrideLogHint = React.useMemo(() => {
    const count = quickTelemetryStrictRollbackPackageOverrideLogRows.length;
    if (count <= 0) {
      return `override log: 0/${QUICK_TELEMETRY_STRICT_ROLLBACK_OVERRIDE_LOG_LIMIT} events`;
    }
    const latest = quickTelemetryStrictRollbackPackageOverrideLogRows[0] || {};
    return [
      `override log: ${count}/${QUICK_TELEMETRY_STRICT_ROLLBACK_OVERRIDE_LOG_LIMIT} events`,
      `latest policy ${String(latest.policy_mode || "-")}`,
      `preset ${String(latest.preset_id || "-")}`,
    ].join(", ");
  }, [quickTelemetryStrictRollbackPackageOverrideLogRows]);
  const quickTelemetryStrictRollbackTrustAuditBundle = React.useMemo(() => {
    return buildQuickTelemetryStrictRollbackTrustAuditBundle({
      trust_policy_mode: quickTelemetryStrictRollbackPackageTrustPolicy,
      override_log_entries: quickTelemetryStrictRollbackPackageOverrideLogRows,
      provenance_snapshot: quickTelemetryStrictRollbackTrustAuditProvenanceSnapshot,
    });
  }, [
    quickTelemetryStrictRollbackPackageTrustPolicy,
    quickTelemetryStrictRollbackPackageOverrideLogRows,
    quickTelemetryStrictRollbackTrustAuditProvenanceSnapshot,
  ]);
  const quickTelemetryStrictRollbackTrustAuditBundleHint = React.useMemo(() => {
    const bundle = quickTelemetryStrictRollbackTrustAuditBundle;
    const snapshot = bundle.provenance_snapshot || {};
    const eventCount = Number(bundle.override_log?.entry_count || 0);
    return [
      `trust audit bundle: policy ${String(bundle.trust_policy_mode || "strict_reject")}`,
      `override_events ${eventCount}`,
      `parse ${String(snapshot.parse_state || "empty")}`,
      `provenance_issue ${Boolean(snapshot.has_guard_issue) ? "yes" : "no"}`,
    ].join(", ");
  }, [quickTelemetryStrictRollbackTrustAuditBundle]);
  const quickTelemetryStrictRollbackTrustAuditBundlePreview = React.useMemo(() => {
    const bundle = quickTelemetryStrictRollbackTrustAuditBundle;
    const snapshot = bundle.provenance_snapshot || {};
    const overrideLog = bundle.override_log || {};
    const lines = [
      `trust_audit_bundle kind=${String(bundle.kind || QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_BUNDLE_KIND)} schema=${Number(bundle.schema_version || QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_BUNDLE_SCHEMA_VERSION)}`,
      `exported_at=${String(bundle.exported_at_iso || "-")}`,
      `policy=${String(bundle.trust_policy_mode || "strict_reject")} override_events=${Number(overrideLog.entry_count || 0)}`,
      `parse_state=${String(snapshot.parse_state || "empty")} provenance_issue=${Boolean(snapshot.has_guard_issue) ? "yes" : "no"}`,
      `source=${String(snapshot.source_stamp || QUICK_TELEMETRY_STRICT_ROLLBACK_DRILL_PACKAGE_SOURCE_STAMP)}`,
      `checksum imported=${String(snapshot.payload_checksum || "-")} computed=${String(snapshot.computed_checksum || "-")}`,
      `package kind=${String(snapshot.package_kind || QUICK_TELEMETRY_STRICT_ROLLBACK_DRILL_PACKAGE_KIND)} schema=${Number(snapshot.package_schema_version || QUICK_TELEMETRY_STRICT_ROLLBACK_DRILL_PACKAGE_SCHEMA_VERSION)} preset=${String(snapshot.package_preset_id || "custom")} mode=${String(snapshot.package_import_mode || "compat")}`,
      `package timeline_entries=${Number(snapshot.package_timeline_entry_count || 0)} exported_at=${String(snapshot.package_exported_at_iso || "-")}`,
    ];
    if (String(snapshot.parse_error || "").trim()) {
      lines.push(`parse_error=${String(snapshot.parse_error || "")}`);
    }
    return lines.join("\n");
  }, [quickTelemetryStrictRollbackTrustAuditBundle]);
  const parsedQuickTelemetryStrictRollbackTrustAuditBundlePayload = React.useMemo(() => {
    const text = String(quickTelemetryDrilldownStrictRollbackTrustAuditBundleImportText || "").trim();
    if (!text) {
      return {
        bundle: null,
        error: "",
        empty: true,
      };
    }
    try {
      return {
        bundle: parseQuickTelemetryStrictRollbackTrustAuditBundleText(text),
        error: "",
        empty: false,
      };
    } catch (err) {
      return {
        bundle: null,
        error: String(err?.message || "parse error"),
        empty: false,
      };
    }
  }, [quickTelemetryDrilldownStrictRollbackTrustAuditBundleImportText]);
  const quickTelemetryStrictRollbackTrustAuditBundleImportSchemaHint = React.useMemo(
    () =>
      `trust audit bundle expects kind=${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_BUNDLE_KIND}, schema=${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_BUNDLE_SCHEMA_VERSION}`,
    []
  );
  const quickTelemetryStrictRollbackTrustAuditBundleImportGuidance = React.useMemo(() => {
    if (parsedQuickTelemetryStrictRollbackTrustAuditBundlePayload.empty) return "";
    const err = String(parsedQuickTelemetryStrictRollbackTrustAuditBundlePayload.error || "");
    if (!err) return "";
    if (err.includes("unexpected kind")) {
      return `guidance: set kind=${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_BUNDLE_KIND}`;
    }
    if (err.includes("requires kind=")) {
      return `guidance: trust audit bundle requires kind=${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_BUNDLE_KIND}`;
    }
    if (err.includes("unsupported schema_version")) {
      return `guidance: set schema_version=${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_BUNDLE_SCHEMA_VERSION}`;
    }
    if (err.includes("requires schema_version=")) {
      return `guidance: trust audit bundle requires schema_version=${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_BUNDLE_SCHEMA_VERSION}`;
    }
    if (err.includes("missing override_log")) {
      return "guidance: include override_log wrapper with entries array";
    }
    if (err.includes("override_log.entries must be array")) {
      return "guidance: override_log.entries must be an array";
    }
    if (err.includes("missing provenance_snapshot")) {
      return "guidance: include provenance_snapshot object";
    }
    return "";
  }, [parsedQuickTelemetryStrictRollbackTrustAuditBundlePayload.empty, parsedQuickTelemetryStrictRollbackTrustAuditBundlePayload.error]);
  const quickTelemetryStrictRollbackTrustAuditBundleImportPreview = React.useMemo(() => {
    if (parsedQuickTelemetryStrictRollbackTrustAuditBundlePayload.empty) {
      return "trust audit import preview: waiting for JSON payload";
    }
    if (parsedQuickTelemetryStrictRollbackTrustAuditBundlePayload.error) {
      return `trust audit import preview: invalid payload (${parsedQuickTelemetryStrictRollbackTrustAuditBundlePayload.error})`;
    }
    const bundle = parsedQuickTelemetryStrictRollbackTrustAuditBundlePayload.bundle || {};
    const snapshot = bundle.provenance_snapshot || {};
    const overrideLog = bundle.override_log || {};
    const latest = Array.isArray(overrideLog.entries) && overrideLog.entries.length > 0
      ? overrideLog.entries[0]
      : {};
    return [
      `trust audit import preview: policy ${String(bundle.trust_policy_mode || "strict_reject")}`,
      `override_events ${Number(overrideLog.entry_count || 0)}`,
      `parse ${String(snapshot.parse_state || "empty")}`,
      `provenance_issue ${Boolean(snapshot.has_guard_issue) ? "yes" : "no"}`,
      `source ${String(snapshot.source_stamp || QUICK_TELEMETRY_STRICT_ROLLBACK_DRILL_PACKAGE_SOURCE_STAMP)}`,
      `package ${String(snapshot.package_kind || QUICK_TELEMETRY_STRICT_ROLLBACK_DRILL_PACKAGE_KIND)}@${Number(snapshot.package_schema_version || QUICK_TELEMETRY_STRICT_ROLLBACK_DRILL_PACKAGE_SCHEMA_VERSION)}`,
      `latest_override_preset ${String(latest.preset_id || "-")}`,
    ].join(", ");
  }, [
    parsedQuickTelemetryStrictRollbackTrustAuditBundlePayload.bundle,
    parsedQuickTelemetryStrictRollbackTrustAuditBundlePayload.empty,
    parsedQuickTelemetryStrictRollbackTrustAuditBundlePayload.error,
  ]);
  const quickTelemetryStrictRollbackTrustAuditBundleApplySafety = React.useMemo(() => {
    if (parsedQuickTelemetryStrictRollbackTrustAuditBundlePayload.empty) {
      return {
        needs_confirm: false,
        policy_changed: false,
        overrides_replaced: false,
        incoming_policy: normalizeQuickTelemetryStrictRollbackPackageTrustPolicy(
          quickTelemetryStrictRollbackPackageTrustPolicy
        ),
        existing_policy: normalizeQuickTelemetryStrictRollbackPackageTrustPolicy(
          quickTelemetryStrictRollbackPackageTrustPolicy
        ),
        incoming_override_count: 0,
        existing_override_count: quickTelemetryStrictRollbackPackageOverrideLogRows.length,
        parse_state: "empty",
      };
    }
    if (parsedQuickTelemetryStrictRollbackTrustAuditBundlePayload.error) {
      return {
        needs_confirm: false,
        policy_changed: false,
        overrides_replaced: false,
        incoming_policy: normalizeQuickTelemetryStrictRollbackPackageTrustPolicy(
          quickTelemetryStrictRollbackPackageTrustPolicy
        ),
        existing_policy: normalizeQuickTelemetryStrictRollbackPackageTrustPolicy(
          quickTelemetryStrictRollbackPackageTrustPolicy
        ),
        incoming_override_count: 0,
        existing_override_count: quickTelemetryStrictRollbackPackageOverrideLogRows.length,
        parse_state: "error",
      };
    }
    const bundle = parsedQuickTelemetryStrictRollbackTrustAuditBundlePayload.bundle || {};
    const incomingPolicy = normalizeQuickTelemetryStrictRollbackPackageTrustPolicy(bundle.trust_policy_mode);
    const existingPolicy = normalizeQuickTelemetryStrictRollbackPackageTrustPolicy(
      quickTelemetryStrictRollbackPackageTrustPolicy
    );
    const incomingEntries = buildQuickTelemetryStrictRollbackOverrideLogBundle(
      bundle.override_log?.entries
    ).entries;
    const existingEntries = quickTelemetryStrictRollbackPackageOverrideLogRows;
    const incomingSignature = JSON.stringify(incomingEntries);
    const existingSignature = JSON.stringify(existingEntries);
    const policyChanged = incomingPolicy !== existingPolicy;
    const overridesReplaced = existingEntries.length > 0 && incomingSignature !== existingSignature;
    return {
      needs_confirm: policyChanged || overridesReplaced,
      policy_changed: policyChanged,
      overrides_replaced: overridesReplaced,
      incoming_policy: incomingPolicy,
      existing_policy: existingPolicy,
      incoming_override_count: incomingEntries.length,
      existing_override_count: existingEntries.length,
      parse_state: "ready",
    };
  }, [
    parsedQuickTelemetryStrictRollbackTrustAuditBundlePayload.bundle,
    parsedQuickTelemetryStrictRollbackTrustAuditBundlePayload.empty,
    parsedQuickTelemetryStrictRollbackTrustAuditBundlePayload.error,
    quickTelemetryStrictRollbackPackageOverrideLogRows,
    quickTelemetryStrictRollbackPackageTrustPolicy,
  ]);
  const quickTelemetryStrictRollbackTrustAuditBundleApplySafetyHint = React.useMemo(() => {
    const safety = quickTelemetryStrictRollbackTrustAuditBundleApplySafety;
    if (safety.parse_state === "empty") {
      return "apply safety: waiting for trust-audit handoff payload";
    }
    if (safety.parse_state === "error") {
      return "apply safety: blocked by parse error";
    }
    if (!safety.needs_confirm) {
      return "apply safety: no replacement risk detected (apply enabled)";
    }
    const policyToken = safety.policy_changed
      ? `policy ${safety.existing_policy} -> ${safety.incoming_policy}`
      : "policy unchanged";
    const overrideToken = safety.overrides_replaced
      ? `override log ${safety.existing_override_count} -> ${safety.incoming_override_count}`
      : `override log unchanged (${safety.incoming_override_count})`;
    return `apply safety: confirm required (${policyToken}, ${overrideToken})`;
  }, [quickTelemetryStrictRollbackTrustAuditBundleApplySafety]);
  const quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunSummary = React.useMemo(() => {
    if (parsedQuickTelemetryStrictRollbackTrustAuditBundlePayload.empty) {
      return {
        parse_state: "empty",
        policy_changed: false,
        existing_policy: normalizeQuickTelemetryStrictRollbackPackageTrustPolicy(
          quickTelemetryStrictRollbackPackageTrustPolicy
        ),
        incoming_policy: normalizeQuickTelemetryStrictRollbackPackageTrustPolicy(
          quickTelemetryStrictRollbackPackageTrustPolicy
        ),
        existing_override_count: quickTelemetryStrictRollbackPackageOverrideLogRows.length,
        incoming_override_count: 0,
        added_override_count: 0,
        removed_override_count: 0,
        changed_override_count: 0,
        unchanged_override_count: 0,
        existing_latest_override_id: "-",
        existing_latest_override_ts: "-",
        existing_latest_override_preset: "-",
        incoming_latest_override_id: "-",
        incoming_latest_override_ts: "-",
        incoming_latest_override_preset: "-",
      };
    }
    if (parsedQuickTelemetryStrictRollbackTrustAuditBundlePayload.error) {
      return {
        parse_state: "error",
        policy_changed: false,
        existing_policy: normalizeQuickTelemetryStrictRollbackPackageTrustPolicy(
          quickTelemetryStrictRollbackPackageTrustPolicy
        ),
        incoming_policy: normalizeQuickTelemetryStrictRollbackPackageTrustPolicy(
          quickTelemetryStrictRollbackPackageTrustPolicy
        ),
        existing_override_count: quickTelemetryStrictRollbackPackageOverrideLogRows.length,
        incoming_override_count: 0,
        added_override_count: 0,
        removed_override_count: 0,
        changed_override_count: 0,
        unchanged_override_count: 0,
        existing_latest_override_id: "-",
        existing_latest_override_ts: "-",
        existing_latest_override_preset: "-",
        incoming_latest_override_id: "-",
        incoming_latest_override_ts: "-",
        incoming_latest_override_preset: "-",
      };
    }
    const bundle = parsedQuickTelemetryStrictRollbackTrustAuditBundlePayload.bundle || {};
    const incomingPolicy = normalizeQuickTelemetryStrictRollbackPackageTrustPolicy(bundle.trust_policy_mode);
    const existingPolicy = normalizeQuickTelemetryStrictRollbackPackageTrustPolicy(
      quickTelemetryStrictRollbackPackageTrustPolicy
    );
    const incomingEntries = buildQuickTelemetryStrictRollbackOverrideLogBundle(
      bundle.override_log?.entries
    ).entries;
    const existingEntries = quickTelemetryStrictRollbackPackageOverrideLogRows;
    const existingById = new Map();
    existingEntries.forEach((row) => {
      const id = String(row?.id || "").trim();
      if (!id) return;
      existingById.set(id, row);
    });
    const incomingById = new Map();
    incomingEntries.forEach((row) => {
      const id = String(row?.id || "").trim();
      if (!id) return;
      incomingById.set(id, row);
    });
    let addedCount = 0;
    let changedCount = 0;
    let unchangedCount = 0;
    const entrySignature = (row) => [
      String(row?.event_kind || ""),
      String(row?.policy_mode || ""),
      String(row?.source_stamp || ""),
      String(row?.payload_checksum || ""),
      String(row?.computed_checksum || ""),
      String(Boolean(row?.provenance_issue)),
      String(Boolean(row?.checklist_delta)),
      String(Boolean(row?.delta_confirmed)),
      String(row?.override_reason || ""),
      String(row?.preset_id || ""),
      String(row?.timestamp_iso || ""),
    ].join("|");
    incomingById.forEach((incomingRow, id) => {
      const existingRow = existingById.get(id);
      if (!existingRow) {
        addedCount += 1;
        return;
      }
      if (entrySignature(incomingRow) === entrySignature(existingRow)) {
        unchangedCount += 1;
        return;
      }
      changedCount += 1;
    });
    let removedCount = 0;
    existingById.forEach((_, id) => {
      if (!incomingById.has(id)) removedCount += 1;
    });
    const existingLatest = existingEntries[0] || {};
    const incomingLatest = incomingEntries[0] || {};
    return {
      parse_state: "ready",
      policy_changed: incomingPolicy !== existingPolicy,
      existing_policy: existingPolicy,
      incoming_policy: incomingPolicy,
      existing_override_count: existingEntries.length,
      incoming_override_count: incomingEntries.length,
      added_override_count: addedCount,
      removed_override_count: removedCount,
      changed_override_count: changedCount,
      unchanged_override_count: unchangedCount,
      existing_latest_override_id: String(existingLatest.id || "-"),
      existing_latest_override_ts: String(existingLatest.timestamp_iso || "-"),
      existing_latest_override_preset: String(existingLatest.preset_id || "-"),
      incoming_latest_override_id: String(incomingLatest.id || "-"),
      incoming_latest_override_ts: String(incomingLatest.timestamp_iso || "-"),
      incoming_latest_override_preset: String(incomingLatest.preset_id || "-"),
    };
  }, [
    parsedQuickTelemetryStrictRollbackTrustAuditBundlePayload.bundle,
    parsedQuickTelemetryStrictRollbackTrustAuditBundlePayload.empty,
    parsedQuickTelemetryStrictRollbackTrustAuditBundlePayload.error,
    quickTelemetryStrictRollbackPackageOverrideLogRows,
    quickTelemetryStrictRollbackPackageTrustPolicy,
  ]);
  const quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHint = React.useMemo(() => {
    const summary = quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunSummary;
    if (summary.parse_state === "empty") {
      return "apply dry-run: waiting for trust-audit handoff payload";
    }
    if (summary.parse_state === "error") {
      return "apply dry-run: blocked by parse error";
    }
    return [
      `apply dry-run: policy ${summary.existing_policy}->${summary.incoming_policy} ${summary.policy_changed ? "changed" : "same"}`,
      `override live ${summary.existing_override_count} incoming ${summary.incoming_override_count}`,
      `diff +${summary.added_override_count}/-${summary.removed_override_count}/~${summary.changed_override_count}`,
    ].join(", ");
  }, [quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunSummary]);
  const quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunPreview = React.useMemo(() => {
    const summary = quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunSummary;
    if (summary.parse_state === "empty") {
      return "apply dry-run preview: waiting for trust-audit handoff payload";
    }
    if (summary.parse_state === "error") {
      return "apply dry-run preview: blocked by parse error";
    }
    return [
      `policy live=${summary.existing_policy} incoming=${summary.incoming_policy} changed=${summary.policy_changed ? "yes" : "no"}`,
      `override_count live=${summary.existing_override_count} incoming=${summary.incoming_override_count}`,
      `override_diff added=${summary.added_override_count} removed=${summary.removed_override_count} changed=${summary.changed_override_count} unchanged=${summary.unchanged_override_count}`,
      `live_latest id=${summary.existing_latest_override_id} ts=${summary.existing_latest_override_ts} preset=${summary.existing_latest_override_preset}`,
      `incoming_latest id=${summary.incoming_latest_override_id} ts=${summary.incoming_latest_override_ts} preset=${summary.incoming_latest_override_preset}`,
    ].join("\n");
  }, [quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunSummary]);
  const quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackagePayload = React.useMemo(() => {
    const parsedBundle = parsedQuickTelemetryStrictRollbackTrustAuditBundlePayload.bundle || {};
    const parsedSnapshot = parsedBundle.provenance_snapshot || {};
    const parsedOverrideLog = parsedBundle.override_log || {};
    return buildQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackage({
      dry_run_summary: quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunSummary,
      apply_safety: quickTelemetryStrictRollbackTrustAuditBundleApplySafety,
      import_preview: quickTelemetryStrictRollbackTrustAuditBundleImportPreview,
      trust_audit_bundle_kind: String(parsedBundle.kind || QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_BUNDLE_KIND),
      trust_audit_bundle_schema_version: Number(
        parsedBundle.schema_version || QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_BUNDLE_SCHEMA_VERSION
      ),
      trust_audit_bundle_policy_mode: normalizeQuickTelemetryStrictRollbackPackageTrustPolicy(
        parsedBundle.trust_policy_mode || quickTelemetryStrictRollbackPackageTrustPolicy
      ),
      trust_audit_bundle_override_event_count: Number(parsedOverrideLog.entry_count || 0),
      trust_audit_bundle_parse_state: String(parsedSnapshot.parse_state || "empty"),
    });
  }, [
    parsedQuickTelemetryStrictRollbackTrustAuditBundlePayload.bundle,
    quickTelemetryStrictRollbackPackageTrustPolicy,
    quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunSummary,
    quickTelemetryStrictRollbackTrustAuditBundleApplySafety,
    quickTelemetryStrictRollbackTrustAuditBundleImportPreview,
  ]);
  const quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackageHint = React.useMemo(() => {
    const pkg = quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackagePayload;
    const summary = pkg.dry_run_summary || {};
    const safety = pkg.apply_safety || {};
    return [
      `dry-run handoff package: parse ${String(summary.parse_state || "empty")}`,
      `policy ${String(summary.existing_policy || "strict_reject")}->${String(summary.incoming_policy || "strict_reject")}`,
      `diff +${Number(summary.added_override_count || 0)}/-${Number(summary.removed_override_count || 0)}/~${Number(summary.changed_override_count || 0)}`,
      `confirm ${Boolean(safety.needs_confirm) ? "required" : "not_required"}`,
    ].join(", ");
  }, [quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackagePayload]);
  const quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackagePreview = React.useMemo(() => {
    const pkg = quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackagePayload;
    const summary = pkg.dry_run_summary || {};
    const safety = pkg.apply_safety || {};
    const snapshot = pkg.trust_audit_bundle_snapshot || {};
    return [
      `handoff kind=${String(pkg.kind || QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_KIND)} schema=${Number(pkg.schema_version || QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_SCHEMA_VERSION)}`,
      `exported_at=${String(pkg.exported_at_iso || "-")}`,
      `summary parse=${String(summary.parse_state || "empty")} policy=${String(summary.existing_policy || "strict_reject")}->${String(summary.incoming_policy || "strict_reject")} changed=${Boolean(summary.policy_changed) ? "yes" : "no"}`,
      `summary override live=${Number(summary.existing_override_count || 0)} incoming=${Number(summary.incoming_override_count || 0)} diff +${Number(summary.added_override_count || 0)}/-${Number(summary.removed_override_count || 0)}/~${Number(summary.changed_override_count || 0)}/=${Number(summary.unchanged_override_count || 0)}`,
      `safety needs_confirm=${Boolean(safety.needs_confirm) ? "yes" : "no"} policy_changed=${Boolean(safety.policy_changed) ? "yes" : "no"} overrides_replaced=${Boolean(safety.overrides_replaced) ? "yes" : "no"}`,
      `bundle kind=${String(snapshot.kind || QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_BUNDLE_KIND)} schema=${Number(snapshot.schema_version || QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_BUNDLE_SCHEMA_VERSION)} policy=${String(snapshot.trust_policy_mode || "strict_reject")} override_events=${Number(snapshot.override_event_count || 0)} parse=${String(snapshot.parse_state || "empty")}`,
      `import_preview=${String(pkg.import_preview || "-")}`,
    ].join("\n");
  }, [quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackagePayload]);
  const parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackagePayload = React.useMemo(() => {
    const text = String(quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffImportText || "").trim();
    if (!text) {
      return {
        pkg: null,
        error: "",
        empty: true,
      };
    }
    try {
      return {
        pkg: parseQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackageText(text),
        error: "",
        empty: false,
      };
    } catch (err) {
      return {
        pkg: null,
        error: String(err?.message || "parse error"),
        empty: false,
      };
    }
  }, [quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffImportText]);
  const quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffImportSchemaHint = React.useMemo(
    () =>
      `dry-run handoff package expects kind=${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_KIND}, schema=${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_SCHEMA_VERSION}`,
    []
  );
  const quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffImportGuidance = React.useMemo(() => {
    if (parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackagePayload.empty) return "";
    const err = String(parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackagePayload.error || "");
    if (!err) return "";
    if (err.includes("unexpected kind")) {
      return `guidance: set kind=${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_KIND}`;
    }
    if (err.includes("requires kind=")) {
      return `guidance: dry-run handoff package requires kind=${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_KIND}`;
    }
    if (err.includes("unsupported schema_version")) {
      return `guidance: set schema_version=${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_SCHEMA_VERSION}`;
    }
    if (err.includes("requires schema_version=")) {
      return `guidance: dry-run handoff package requires schema_version=${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_SCHEMA_VERSION}`;
    }
    if (err.includes("missing dry_run_summary")) {
      return "guidance: include dry_run_summary object";
    }
    if (err.includes("missing apply_safety")) {
      return "guidance: include apply_safety object";
    }
    if (err.includes("missing trust_audit_bundle_snapshot")) {
      return "guidance: include trust_audit_bundle_snapshot object";
    }
    return "";
  }, [
    parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackagePayload.empty,
    parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackagePayload.error,
  ]);
  const quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffImportPreview = React.useMemo(() => {
    if (parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackagePayload.empty) {
      return "dry-run handoff import preview: waiting for JSON payload";
    }
    if (parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackagePayload.error) {
      return `dry-run handoff import preview: invalid payload (${parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackagePayload.error})`;
    }
    const pkg = parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackagePayload.pkg || {};
    const summary = pkg.dry_run_summary || {};
    const safety = pkg.apply_safety || {};
    const snapshot = pkg.trust_audit_bundle_snapshot || {};
    return [
      `dry-run handoff import preview: parse ${String(summary.parse_state || "empty")}`,
      `policy ${String(summary.existing_policy || "strict_reject")}->${String(summary.incoming_policy || "strict_reject")}`,
      `diff +${Number(summary.added_override_count || 0)}/-${Number(summary.removed_override_count || 0)}/~${Number(summary.changed_override_count || 0)}`,
      `confirm ${Boolean(safety.needs_confirm) ? "required" : "not_required"}`,
      `bundle ${String(snapshot.kind || QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_BUNDLE_KIND)}@${Number(snapshot.schema_version || QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_BUNDLE_SCHEMA_VERSION)}`,
    ].join(", ");
  }, [
    parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackagePayload.empty,
    parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackagePayload.error,
    parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackagePayload.pkg,
  ]);
  const quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateSafety = React.useMemo(() => {
    const existingHydrated = (
      quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydratedSnapshot
      && typeof quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydratedSnapshot === "object"
    )
      ? quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydratedSnapshot
      : null;
    const existingPkg = existingHydrated?.pkg && typeof existingHydrated.pkg === "object"
      ? existingHydrated.pkg
      : null;
    if (parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackagePayload.empty) {
      return {
        needs_confirm: false,
        snapshot_replaced: false,
        parse_state: "empty",
        has_existing: Boolean(existingPkg),
        existing_exported_at_iso: String(existingPkg?.exported_at_iso || "-"),
        incoming_exported_at_iso: "-",
      };
    }
    if (parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackagePayload.error) {
      return {
        needs_confirm: false,
        snapshot_replaced: false,
        parse_state: "error",
        has_existing: Boolean(existingPkg),
        existing_exported_at_iso: String(existingPkg?.exported_at_iso || "-"),
        incoming_exported_at_iso: "-",
      };
    }
    const incomingPkg = parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackagePayload.pkg || {};
    const incomingSignature = JSON.stringify(incomingPkg);
    const existingSignature = existingPkg ? JSON.stringify(existingPkg) : "";
    const snapshotReplaced = Boolean(existingPkg) && existingSignature !== incomingSignature;
    return {
      needs_confirm: snapshotReplaced,
      snapshot_replaced: snapshotReplaced,
      parse_state: "ready",
      has_existing: Boolean(existingPkg),
      existing_exported_at_iso: String(existingPkg?.exported_at_iso || "-"),
      incoming_exported_at_iso: String(incomingPkg.exported_at_iso || "-"),
    };
  }, [
    parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackagePayload.empty,
    parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackagePayload.error,
    parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackagePayload.pkg,
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydratedSnapshot,
  ]);
  const quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateSafetyHint = React.useMemo(() => {
    const safety = quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateSafety;
    if (safety.parse_state === "empty") {
      return "dry-run handoff hydrate safety: waiting for handoff payload";
    }
    if (safety.parse_state === "error") {
      return "dry-run handoff hydrate safety: blocked by parse error";
    }
    if (!safety.needs_confirm) {
      return "dry-run handoff hydrate safety: no replacement risk detected (hydrate enabled)";
    }
    return [
      "dry-run handoff hydrate safety: confirm required",
      `replace hydrated snapshot exported_at ${safety.existing_exported_at_iso} -> ${safety.incoming_exported_at_iso}`,
    ].join(" (") + ")";
  }, [quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateSafety]);
  const quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmCountdownHint = React.useMemo(() => {
    const safety = quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateSafety;
    if (safety.parse_state === "empty") {
      return "dry-run handoff apply confirm timer: waiting for handoff payload";
    }
    if (safety.parse_state === "error") {
      return "dry-run handoff apply confirm timer: blocked by parse error";
    }
    if (!safety.needs_confirm) {
      return "dry-run handoff apply confirm timer: no replacement-risk confirmation required";
    }
    const timeoutSec = Math.floor(
      QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_TIMEOUT_MS / 1000
    );
    if (!quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmChecked) {
      return `dry-run handoff apply confirm timer: check confirm to arm (${timeoutSec}s auto-disarm)`;
    }
    const armedAt = Number(quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmArmedAtMs || 0);
    const tickMs = Number(quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmTickMs || 0);
    const nowMs = tickMs > 0 ? tickMs : Date.now();
    const elapsedMs = armedAt > 0 ? Math.max(0, nowMs - armedAt) : 0;
    const remainingSec = Math.max(
      0,
      Math.ceil((QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_TIMEOUT_MS - elapsedMs) / 1000)
    );
    if (remainingSec <= 5) {
      return `dry-run handoff apply confirm timer: armed (${remainingSec}s left, auto-disarm soon)`;
    }
    return `dry-run handoff apply confirm timer: armed (${remainingSec}s left)`;
  }, [
    quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateSafety,
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmArmedAtMs,
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmChecked,
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmTickMs,
  ]);
  const appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityEvent = React.useCallback((eventId, detail) => {
    const eventKind = String(eventId || "").trim().toLowerCase() || "unknown";
    const eventDetail = String(detail || "").trim();
    const timestampMs = Date.now();
    const row = {
      id: `qt_trust_audit_dry_run_handoff_apply_confirm_activity_${timestampMs}_${eventKind}`,
      timestamp_ms: timestampMs,
      event_id: eventKind,
      detail: eventDetail,
    };
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityTrail((prev) => {
      const rows = Array.isArray(prev) ? prev : [];
      return [row, ...rows].slice(0, QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_LIMIT);
    });
  }, []);
  const quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityRows = React.useMemo(() => (
    buildQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityBundle(
      quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityTrail
    ).entries
  ), [quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityTrail]);
  const quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityTrailHint = React.useMemo(() => {
    const rows = quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityRows;
    if (!rows.length) {
      return "dry-run handoff apply confirm activity: no events yet";
    }
    const latest = rows[0] || {};
    return [
      `dry-run handoff apply confirm activity: ${rows.length}/${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_LIMIT} events`,
      `latest ${String(latest.event_id || "-")} @ ${formatTimeOfDay(Number(latest.timestamp_ms || 0))}`,
    ].join(" (") + ")";
  }, [quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityRows]);
  const quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityTrailPreview = React.useMemo(() => {
    const rows = quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityRows;
    if (!rows.length) {
      return "dry-run handoff apply confirm activity trail appears here";
    }
    return rows.map((row, idx) => (
      `${idx + 1}. ${formatTimeOfDay(Number(row?.timestamp_ms || 0))} | ${String(row?.event_id || "-")} | ${String(row?.detail || "-")}`
    )).join("\n");
  }, [quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityRows]);
  const parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityBundlePayload = React.useMemo(() => {
    const text = String(
      quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityImportText || ""
    ).trim();
    if (!text) {
      return {
        bundle: null,
        error: "",
        empty: true,
      };
    }
    try {
      return {
        bundle: parseQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityText(text),
        error: "",
        empty: false,
      };
    } catch (err) {
      return {
        bundle: null,
        error: String(err?.message || "parse error"),
        empty: false,
      };
    }
  }, [quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityImportText]);
  const quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityImportSchemaHint = React.useMemo(
    () => (
      `confirm activity bundle expects kind=${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_KIND}, `
      + `schema=${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_SCHEMA_VERSION}`
    ),
    []
  );
  const quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityImportGuidance = React.useMemo(() => {
    if (parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityBundlePayload.empty) return "";
    const err = String(parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityBundlePayload.error || "");
    if (!err) return "";
    if (err.includes("unexpected kind")) {
      return `guidance: set kind=${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_KIND}`;
    }
    if (err.includes("requires kind=")) {
      return `guidance: confirm activity bundle requires kind=${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_KIND}`;
    }
    if (err.includes("unsupported schema_version")) {
      return `guidance: set schema_version=${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_SCHEMA_VERSION}`;
    }
    if (err.includes("requires schema_version=")) {
      return `guidance: confirm activity bundle requires schema_version=${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_SCHEMA_VERSION}`;
    }
    if (err.includes("missing entries array")) {
      return "guidance: include entries array";
    }
    return "";
  }, [
    parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityBundlePayload.empty,
    parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityBundlePayload.error,
  ]);
  const quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityImportPreview = React.useMemo(() => {
    if (parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityBundlePayload.empty) {
      return "confirm activity import preview: waiting for JSON payload";
    }
    if (parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityBundlePayload.error) {
      return `confirm activity import preview: invalid payload (${parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityBundlePayload.error})`;
    }
    const bundle = parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityBundlePayload.bundle || {};
    const rows = Array.isArray(bundle.entries) ? bundle.entries : [];
    const latest = rows[0] || {};
    return [
      `confirm activity import preview: ${String(bundle.kind || QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_KIND)}@${Number(bundle.schema_version || QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_SCHEMA_VERSION)}`,
      `events ${rows.length}`,
      `latest ${String(latest.event_id || "-")} @ ${formatTimeOfDay(Number(latest.timestamp_ms || 0))}`,
      `exported_at ${String(bundle.exported_at_iso || "-")}`,
    ].join(", ");
  }, [
    parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityBundlePayload.bundle,
    parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityBundlePayload.empty,
    parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityBundlePayload.error,
  ]);
  const quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplaySafety = React.useMemo(() => {
    const existingRows = quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityRows;
    if (parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityBundlePayload.empty) {
      return {
        needs_confirm: false,
        trail_replaced: false,
        parse_state: "empty",
        existing_entry_count: existingRows.length,
        incoming_entry_count: 0,
      };
    }
    if (parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityBundlePayload.error) {
      return {
        needs_confirm: false,
        trail_replaced: false,
        parse_state: "error",
        existing_entry_count: existingRows.length,
        incoming_entry_count: 0,
      };
    }
    const bundle = parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityBundlePayload.bundle || {};
    const incomingRows = Array.isArray(bundle.entries) ? bundle.entries : [];
    const existingSignature = JSON.stringify(existingRows);
    const incomingSignature = JSON.stringify(incomingRows);
    const trailReplaced = existingRows.length > 0 && existingSignature !== incomingSignature;
    return {
      needs_confirm: trailReplaced,
      trail_replaced: trailReplaced,
      parse_state: "ready",
      existing_entry_count: existingRows.length,
      incoming_entry_count: incomingRows.length,
    };
  }, [
    parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityBundlePayload.bundle,
    parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityBundlePayload.empty,
    parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityBundlePayload.error,
    quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityRows,
  ]);
  const quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplaySafetyHint = React.useMemo(() => {
    const safety = quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplaySafety;
    if (safety.parse_state === "empty") {
      return "confirm activity replay safety: waiting for replay payload";
    }
    if (safety.parse_state === "error") {
      return "confirm activity replay safety: blocked by parse error";
    }
    if (!safety.needs_confirm) {
      return "confirm activity replay safety: no replacement risk detected (replay enabled)";
    }
    return `confirm activity replay safety: confirm required (replace trail ${safety.existing_entry_count}->${safety.incoming_entry_count} events)`;
  }, [quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplaySafety]);
  const quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmCountdownHint = React.useMemo(() => {
    const safety = quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplaySafety;
    if (safety.parse_state === "empty") {
      return "confirm activity replay timer: waiting for replay payload";
    }
    if (safety.parse_state === "error") {
      return "confirm activity replay timer: blocked by parse error";
    }
    if (!safety.needs_confirm) {
      return "confirm activity replay timer: no replacement-risk confirmation required";
    }
    const timeoutSec = Math.floor(
      QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TIMEOUT_MS / 1000
    );
    if (!quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmChecked) {
      return `confirm activity replay timer: check confirm to arm (${timeoutSec}s auto-disarm)`;
    }
    const armedAt = Number(
      quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmArmedAtMs || 0
    );
    const tickMs = Number(
      quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTickMs || 0
    );
    const nowMs = tickMs > 0 ? tickMs : Date.now();
    const elapsedMs = armedAt > 0 ? Math.max(0, nowMs - armedAt) : 0;
    const remainingSec = Math.max(
      0,
      Math.ceil((QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TIMEOUT_MS - elapsedMs) / 1000)
    );
    if (remainingSec <= 5) {
      return `confirm activity replay timer: armed (${remainingSec}s left, auto-disarm soon)`;
    }
    return `confirm activity replay timer: armed (${remainingSec}s left)`;
  }, [
    quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplaySafety,
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmArmedAtMs,
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmChecked,
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTickMs,
  ]);
  const appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmEvent = React.useCallback((eventId, detail) => {
    const eventKind = String(eventId || "").trim().toLowerCase() || "unknown";
    const eventDetail = String(detail || "").trim();
    const timestampMs = Date.now();
    const row = {
      id: `qt_trust_audit_dry_run_handoff_confirm_activity_replay_confirm_${timestampMs}_${eventKind}`,
      timestamp_ms: timestampMs,
      event_id: eventKind,
      detail: eventDetail,
    };
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrail((prev) => {
      const rows = Array.isArray(prev) ? prev : [];
      return [row, ...rows].slice(0, QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_LIMIT);
    });
  }, []);
  const quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmRows = React.useMemo(() => {
    const rows = Array.isArray(quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrail)
      ? quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrail
      : [];
    return rows
      .map((row, idx) => normalizeQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityEntry(row, idx))
      .filter(Boolean)
      .slice(0, QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_LIMIT);
  }, [quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrail]);
  const quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailHint = React.useMemo(() => {
    const rows = quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmRows;
    if (!rows.length) {
      return "confirm activity replay trail: no events yet";
    }
    const latest = rows[0] || {};
    return [
      `confirm activity replay trail: ${rows.length}/${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_LIMIT} events`,
      `latest ${String(latest.event_id || "-")} @ ${formatTimeOfDay(Number(latest.timestamp_ms || 0))}`,
    ].join(" (") + ")";
  }, [quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmRows]);
  const quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailPreview = React.useMemo(() => {
    const rows = quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmRows;
    if (!rows.length) {
      return "confirm activity replay trail appears here";
    }
    return rows.map((row, idx) => (
      `${idx + 1}. ${formatTimeOfDay(Number(row?.timestamp_ms || 0))} | ${String(row?.event_id || "-")} | ${String(row?.detail || "-")}`
    )).join("\n");
  }, [quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmRows]);
  const parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportPayload = React.useMemo(() => {
    const text = String(
      quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportText || ""
    ).trim();
    if (!text) {
      return {
        bundle: null,
        error: "",
        empty: true,
      };
    }
    try {
      return {
        bundle: parseQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailText(text),
        error: "",
        empty: false,
      };
    } catch (err) {
      return {
        bundle: null,
        error: String(err?.message || "parse error"),
        empty: false,
      };
    }
  }, [quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportText]);
  const quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportSchemaHint = React.useMemo(
    () => (
      `confirm activity replay trail bundle expects kind=${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_KIND}, `
      + `schema=${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_SCHEMA_VERSION}`
    ),
    []
  );
  const quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportGuidance = React.useMemo(() => {
    if (parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportPayload.empty) return "";
    const err = String(parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportPayload.error || "");
    if (!err) return "";
    if (err.includes("unexpected kind")) {
      return `guidance: set kind=${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_KIND}`;
    }
    if (err.includes("requires kind=")) {
      return `guidance: confirm activity replay trail bundle requires kind=${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_KIND}`;
    }
    if (err.includes("unsupported schema_version")) {
      return `guidance: set schema_version=${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_SCHEMA_VERSION}`;
    }
    if (err.includes("requires schema_version=")) {
      return `guidance: confirm activity replay trail bundle requires schema_version=${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_SCHEMA_VERSION}`;
    }
    if (err.includes("missing entries array")) {
      return "guidance: include entries array";
    }
    return "";
  }, [
    parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportPayload.empty,
    parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportPayload.error,
  ]);
  const quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportPreview = React.useMemo(() => {
    if (parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportPayload.empty) {
      return "confirm activity replay trail import preview: waiting for JSON payload";
    }
    if (parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportPayload.error) {
      return `confirm activity replay trail import preview: invalid payload (${parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportPayload.error})`;
    }
    const bundle = parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportPayload.bundle || {};
    const rows = Array.isArray(bundle.entries) ? bundle.entries : [];
    const latest = rows[0] || {};
    return [
      `confirm activity replay trail import preview: ${String(bundle.kind || QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_KIND)}@${Number(bundle.schema_version || QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_SCHEMA_VERSION)}`,
      `events ${rows.length}`,
      `latest ${String(latest.event_id || "-")} @ ${formatTimeOfDay(Number(latest.timestamp_ms || 0))}`,
      `exported_at ${String(bundle.exported_at_iso || "-")}`,
    ].join(", ");
  }, [
    parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportPayload.bundle,
    parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportPayload.empty,
    parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportPayload.error,
  ]);
  const quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportSafety = React.useMemo(() => {
    const existingRows = quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmRows;
    if (parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportPayload.empty) {
      return {
        needs_confirm: false,
        trail_replaced: false,
        parse_state: "empty",
        existing_entry_count: existingRows.length,
        incoming_entry_count: 0,
      };
    }
    if (parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportPayload.error) {
      return {
        needs_confirm: false,
        trail_replaced: false,
        parse_state: "error",
        existing_entry_count: existingRows.length,
        incoming_entry_count: 0,
      };
    }
    const bundle = parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportPayload.bundle || {};
    const incomingRows = Array.isArray(bundle.entries) ? bundle.entries : [];
    const existingSignature = JSON.stringify(existingRows);
    const incomingSignature = JSON.stringify(incomingRows);
    const trailReplaced = existingRows.length > 0 && existingSignature !== incomingSignature;
    return {
      needs_confirm: trailReplaced,
      trail_replaced: trailReplaced,
      parse_state: "ready",
      existing_entry_count: existingRows.length,
      incoming_entry_count: incomingRows.length,
    };
  }, [
    parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportPayload.bundle,
    parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportPayload.empty,
    parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportPayload.error,
    quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmRows,
  ]);
  const quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportSafetyHint = React.useMemo(() => {
    const safety = quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportSafety;
    if (safety.parse_state === "empty") {
      return "confirm activity replay trail import safety: waiting for replay timeline payload";
    }
    if (safety.parse_state === "error") {
      return "confirm activity replay trail import safety: blocked by parse error";
    }
    if (!safety.needs_confirm) {
      return "confirm activity replay trail import safety: no replacement risk detected (import apply enabled)";
    }
    return `confirm activity replay trail import safety: confirm required (replace trail ${safety.existing_entry_count}->${safety.incoming_entry_count} events)`;
  }, [quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportSafety]);
  const quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmCountdownHint = React.useMemo(() => {
    const safety = quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportSafety;
    if (safety.parse_state === "empty") {
      return "confirm activity replay trail import timer: waiting for replay timeline payload";
    }
    if (safety.parse_state === "error") {
      return "confirm activity replay trail import timer: blocked by parse error";
    }
    if (!safety.needs_confirm) {
      return "confirm activity replay trail import timer: no replacement-risk confirmation required";
    }
    const timeoutSec = Math.floor(
      QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_IMPORT_CONFIRM_TIMEOUT_MS / 1000
    );
    if (!quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmChecked) {
      return `confirm activity replay trail import timer: check confirm to arm (${timeoutSec}s auto-disarm)`;
    }
    const armedAt = Number(
      quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmArmedAtMs || 0
    );
    const tickMs = Number(
      quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTickMs || 0
    );
    const nowMs = tickMs > 0 ? tickMs : Date.now();
    const elapsedMs = armedAt > 0 ? Math.max(0, nowMs - armedAt) : 0;
    const remainingSec = Math.max(
      0,
      Math.ceil((QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_IMPORT_CONFIRM_TIMEOUT_MS - elapsedMs) / 1000)
    );
    if (remainingSec <= 5) {
      return `confirm activity replay trail import timer: armed (${remainingSec}s left, auto-disarm soon)`;
    }
    return `confirm activity replay trail import timer: armed (${remainingSec}s left)`;
  }, [
    quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportSafety,
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmArmedAtMs,
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmChecked,
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTickMs,
  ]);
  const appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmEvent = React.useCallback((eventId, detail) => {
    const eventKind = String(eventId || "").trim().toLowerCase() || "unknown";
    const eventDetail = String(detail || "").trim();
    const timestampMs = Date.now();
    const row = {
      id: `qt_trust_audit_dry_run_handoff_confirm_activity_replay_confirm_trail_import_confirm_${timestampMs}_${eventKind}`,
      timestamp_ms: timestampMs,
      event_id: eventKind,
      detail: eventDetail,
    };
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrail((prev) => {
      const rows = Array.isArray(prev) ? prev : [];
      return [row, ...rows].slice(0, QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_IMPORT_CONFIRM_TRAIL_LIMIT);
    });
  }, []);
  const quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmRows = React.useMemo(() => {
    const rows = Array.isArray(quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrail)
      ? quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrail
      : [];
    return rows
      .map((row, idx) => normalizeQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityEntry(row, idx))
      .filter(Boolean)
      .slice(0, QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_IMPORT_CONFIRM_TRAIL_LIMIT);
  }, [quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrail]);
  const quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailHint = React.useMemo(() => {
    const rows = quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmRows;
    if (!rows.length) {
      return "confirm activity replay trail import confirm trail: no events yet";
    }
    const latest = rows[0] || {};
    return [
      `confirm activity replay trail import confirm trail: ${rows.length}/${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_IMPORT_CONFIRM_TRAIL_LIMIT} events`,
      `latest ${String(latest.event_id || "-")} @ ${formatTimeOfDay(Number(latest.timestamp_ms || 0))}`,
    ].join(" (") + ")";
  }, [quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmRows]);
  const quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailControlsHint = React.useMemo(() => {
    const status = String(
      quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailControlsStatus || ""
    ).trim();
    if (status) return status;
    const rowCount = quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmRows.length;
    return `import confirm trail controls: ${rowCount} event snapshot row(s) ready for copy/export/reset`;
  }, [
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailControlsStatus,
    quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmRows.length,
  ]);
  const quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailControlsContinuityHint = React.useMemo(() => {
    const status = String(
      quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailControlsStatus || ""
    ).trim();
    if (!status) {
      return "import confirm trail controls continuity: waiting for copy/export/reset lifecycle action";
    }
    if (status.includes("continuity echo aligned")) {
      return `import confirm trail controls continuity: echo aligned (${status})`;
    }
    return `import confirm trail controls continuity: echo pending (${status})`;
  }, [quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailControlsStatus]);
  const quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailApplyTrailLifecycleHint = React.useMemo(() => {
    const status = String(
      quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailControlsStatus || ""
    ).trim();
    if (!status) {
      return "import confirm trail apply-trail continuity: waiting for apply/copy/export/reset lifecycle stamp";
    }
    if (status.includes("continuity echo lifecycle stamp:")) {
      return `import confirm trail apply-trail continuity: lifecycle stamp aligned (${status})`;
    }
    return `import confirm trail apply-trail continuity: lifecycle stamp pending (${status})`;
  }, [quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailControlsStatus]);
  const quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailPreview = React.useMemo(() => {
    const rows = quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmRows;
    const controlsEcho = `controls continuity echo: ${quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailControlsHint}`;
    if (!rows.length) {
      return [
        "confirm activity replay trail import confirm trail appears here",
        controlsEcho,
      ].join("\n");
    }
    const detailLines = rows.map((row, idx) => (
      `${idx + 1}. ${formatTimeOfDay(Number(row?.timestamp_ms || 0))} | ${String(row?.event_id || "-")} | ${String(row?.detail || "-")}`
    ));
    return [...detailLines, `-- ${controlsEcho}`].join("\n");
  }, [
    quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmRows,
    quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailControlsHint,
  ]);
  const parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportPayload = React.useMemo(() => {
    const text = String(
      quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportText || ""
    ).trim();
    if (!text) {
      return {
        bundle: null,
        error: "",
        empty: true,
      };
    }
    try {
      return {
        bundle: parseQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailText(text),
        error: "",
        empty: false,
      };
    } catch (err) {
      return {
        bundle: null,
        error: String(err?.message || "parse error"),
        empty: false,
      };
    }
  }, [quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportText]);
  const quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportSchemaHint = React.useMemo(
    () => (
      `confirm activity replay trail import confirm trail bundle expects kind=${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_IMPORT_CONFIRM_TRAIL_KIND}, `
      + `schema=${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_IMPORT_CONFIRM_TRAIL_SCHEMA_VERSION}`
    ),
    []
  );
  const quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportGuidance = React.useMemo(() => {
    if (parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportPayload.empty) return "";
    const err = String(parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportPayload.error || "");
    if (!err) return "";
    if (err.includes("unexpected kind")) {
      return `guidance: set kind=${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_IMPORT_CONFIRM_TRAIL_KIND}`;
    }
    if (err.includes("requires kind=")) {
      return `guidance: confirm activity replay trail import confirm trail bundle requires kind=${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_IMPORT_CONFIRM_TRAIL_KIND}`;
    }
    if (err.includes("unsupported schema_version")) {
      return `guidance: set schema_version=${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_IMPORT_CONFIRM_TRAIL_SCHEMA_VERSION}`;
    }
    if (err.includes("requires schema_version=")) {
      return `guidance: confirm activity replay trail import confirm trail bundle requires schema_version=${QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_IMPORT_CONFIRM_TRAIL_SCHEMA_VERSION}`;
    }
    if (err.includes("missing entries array")) {
      return "guidance: include entries array";
    }
    return "";
  }, [
    parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportPayload.empty,
    parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportPayload.error,
  ]);
  const quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportControlsSnapshotGuidance = React.useMemo(() => {
    const controlsHint = quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailControlsHint;
    if (parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportPayload.empty) {
      return `guidance: parser waiting; controls snapshot continuity active (${controlsHint})`;
    }
    if (parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportPayload.error) {
      return `guidance: resolve parser errors; controls snapshot continuity preserved (${controlsHint})`;
    }
    return `guidance: controls snapshot continuity active (${controlsHint})`;
  }, [
    quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailControlsHint,
    parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportPayload.empty,
    parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportPayload.error,
  ]);
  const quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportPreview = React.useMemo(() => {
    const controlsHint = quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailControlsHint;
    if (parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportPayload.empty) {
      return `confirm activity replay trail import confirm trail import preview: waiting for JSON payload, controls_snapshot ${controlsHint}`;
    }
    if (parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportPayload.error) {
      return `confirm activity replay trail import confirm trail import preview: invalid payload (${parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportPayload.error}), controls_snapshot ${controlsHint}`;
    }
    const bundle = parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportPayload.bundle || {};
    const rows = Array.isArray(bundle.entries) ? bundle.entries : [];
    const latest = rows[0] || {};
    return [
      `confirm activity replay trail import confirm trail import preview: ${String(bundle.kind || QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_IMPORT_CONFIRM_TRAIL_KIND)}@${Number(bundle.schema_version || QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_IMPORT_CONFIRM_TRAIL_SCHEMA_VERSION)}`,
      `events ${rows.length}`,
      `latest ${String(latest.event_id || "-")} @ ${formatTimeOfDay(Number(latest.timestamp_ms || 0))}`,
      `exported_at ${String(bundle.exported_at_iso || "-")}`,
      `controls_snapshot ${controlsHint}`,
    ].join(", ");
  }, [
    quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailControlsHint,
    parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportPayload.bundle,
    parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportPayload.empty,
    parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportPayload.error,
  ]);
  const quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportSafety = React.useMemo(() => {
    const existingRows = quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmRows;
    if (parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportPayload.empty) {
      return {
        needs_confirm: false,
        trail_replaced: false,
        parse_state: "empty",
        existing_entry_count: existingRows.length,
        incoming_entry_count: 0,
      };
    }
    if (parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportPayload.error) {
      return {
        needs_confirm: false,
        trail_replaced: false,
        parse_state: "error",
        existing_entry_count: existingRows.length,
        incoming_entry_count: 0,
      };
    }
    const bundle = parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportPayload.bundle || {};
    const incomingRows = Array.isArray(bundle.entries) ? bundle.entries : [];
    const existingSignature = JSON.stringify(existingRows);
    const incomingSignature = JSON.stringify(incomingRows);
    const trailReplaced = existingRows.length > 0 && existingSignature !== incomingSignature;
    return {
      needs_confirm: trailReplaced,
      trail_replaced: trailReplaced,
      parse_state: "ready",
      existing_entry_count: existingRows.length,
      incoming_entry_count: incomingRows.length,
    };
  }, [
    parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportPayload.bundle,
    parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportPayload.empty,
    parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportPayload.error,
    quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmRows,
  ]);
  const quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportSafetyHint = React.useMemo(() => {
    const safety = quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportSafety;
    if (safety.parse_state === "empty") {
      return "confirm activity replay trail import confirm trail import safety: waiting for import-confirm payload";
    }
    if (safety.parse_state === "error") {
      return "confirm activity replay trail import confirm trail import safety: blocked by parse error";
    }
    if (!safety.needs_confirm) {
      return "confirm activity replay trail import confirm trail import safety: no replacement risk detected (import apply enabled)";
    }
    return `confirm activity replay trail import confirm trail import safety: confirm required (replace trail ${safety.existing_entry_count}->${safety.incoming_entry_count} events)`;
  }, [quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportSafety]);
  const quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportOperatorHint = React.useMemo(() => {
    const safety = quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportSafety;
    if (safety.parse_state === "empty") {
      return "operator hint: paste import-confirm trail payload to evaluate replacement risk";
    }
    if (safety.parse_state === "error") {
      return "operator hint: fix parser errors before arming replace-confirm";
    }
    if (!safety.needs_confirm) {
      return "operator hint: no destructive overwrite detected; apply can proceed without replace-confirm";
    }
    if (!quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmChecked) {
      return "operator hint: enable replace-confirm checkbox before applying import-confirm trail overwrite";
    }
    return "operator hint: replace-confirm armed; apply now to overwrite existing import-confirm trail";
  }, [
    quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportSafety,
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmChecked,
  ]);
  const quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmCountdownHint = React.useMemo(() => {
    const safety = quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportSafety;
    if (safety.parse_state === "empty") {
      return "confirm activity replay trail import confirm trail import timer: waiting for import-confirm payload";
    }
    if (safety.parse_state === "error") {
      return "confirm activity replay trail import confirm trail import timer: blocked by parse error";
    }
    if (!safety.needs_confirm) {
      return "confirm activity replay trail import confirm trail import timer: no replacement-risk confirmation required";
    }
    const timeoutSec = Math.floor(
      QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_IMPORT_CONFIRM_TRAIL_IMPORT_CONFIRM_TIMEOUT_MS / 1000
    );
    if (!quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmChecked) {
      return `confirm activity replay trail import confirm trail import timer: check confirm to arm (${timeoutSec}s auto-disarm)`;
    }
    const armedAt = Number(
      quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmArmedAtMs || 0
    );
    const tickMs = Number(
      quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmTickMs || 0
    );
    const nowMs = tickMs > 0 ? tickMs : Date.now();
    const elapsedMs = armedAt > 0 ? Math.max(0, nowMs - armedAt) : 0;
    const remainingSec = Math.max(
      0,
      Math.ceil((QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_IMPORT_CONFIRM_TRAIL_IMPORT_CONFIRM_TIMEOUT_MS - elapsedMs) / 1000)
    );
    if (remainingSec <= 5) {
      return `confirm activity replay trail import confirm trail import timer: armed (${remainingSec}s left, auto-disarm soon)`;
    }
    return `confirm activity replay trail import confirm trail import timer: armed (${remainingSec}s left)`;
  }, [
    quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportSafety,
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmArmedAtMs,
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmChecked,
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmTickMs,
  ]);
  const quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportApplyContinuityHint = React.useMemo(() => {
    const controlsHint = quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailControlsHint;
    const safety = quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportSafety;
    if (safety.parse_state === "empty") {
      return `apply continuity: waiting for payload; controls snapshot unchanged (${controlsHint})`;
    }
    if (safety.parse_state === "error") {
      return `apply continuity: parser blocked; controls snapshot unchanged (${controlsHint})`;
    }
    if (safety.needs_confirm && !quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmChecked) {
      return `apply continuity: replacement confirm required before alignment (${controlsHint})`;
    }
    return `apply continuity: apply will align controls snapshot after hydrate (${controlsHint})`;
  }, [
    quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailControlsHint,
    quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportSafety,
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmChecked,
  ]);
  React.useEffect(() => {
    if (!quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmChecked) return;
    if (quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportSafety.needs_confirm) return;
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmChecked(false);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmArmedAtMs(0);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmTickMs(0);
    appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmEvent(
      "import_confirm_trail_import_disarm_risk_cleared",
      `replacement-risk requirement cleared for import confirm trail apply (${quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportOperatorHint})`
    );
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailControlsStatus(
      "import confirm trail controls: replacement confirm disarmed (risk cleared)"
    );
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
      "dry-run handoff apply confirm activity replay trail import confirm trail import confirm disarmed"
    );
  }, [
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmArmedAtMs,
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmChecked,
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmTickMs,
    quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportSafety.needs_confirm,
    quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportOperatorHint,
    appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmEvent,
  ]);
  React.useEffect(() => {
    if (
      !quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmChecked
      || !quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportSafety.needs_confirm
    ) {
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmArmedAtMs(0);
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmTickMs(0);
      return;
    }
    const nowMs = Date.now();
    if (Number(quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmArmedAtMs || 0) <= 0) {
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmArmedAtMs(nowMs);
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmTickMs(nowMs);
    }
    const timer = setInterval(() => {
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmTickMs(Date.now());
    }, 1_000);
    return () => clearInterval(timer);
  }, [
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmArmedAtMs,
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmChecked,
    quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportSafety.needs_confirm,
  ]);
  React.useEffect(() => {
    if (!quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmChecked) return;
    if (!quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportSafety.needs_confirm) return;
    const armedAt = Number(
      quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmArmedAtMs || 0
    );
    if (armedAt <= 0) return;
    const timeoutMs = QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_IMPORT_CONFIRM_TRAIL_IMPORT_CONFIRM_TIMEOUT_MS;
    const elapsedMs = Math.max(0, Date.now() - armedAt);
    const remainingMs = Math.max(0, timeoutMs - elapsedMs);
    const timeout = setTimeout(() => {
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmChecked(false);
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmArmedAtMs(0);
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmTickMs(0);
      appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmEvent(
        "import_confirm_trail_import_auto_disarm_timeout",
        `import confirm trail replacement-confirm timer elapsed (20s); ${quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportOperatorHint}`
      );
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailControlsStatus(
        "import confirm trail controls: replacement confirm auto-disarmed (timer elapsed)"
      );
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
        "dry-run handoff apply confirm activity replay trail import confirm trail import confirm auto-disarmed: re-check confirm to apply import confirm trail"
      );
    }, remainingMs);
    return () => clearTimeout(timeout);
  }, [
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmArmedAtMs,
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmChecked,
    quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportSafety.needs_confirm,
    quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportOperatorHint,
    appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmEvent,
  ]);
  React.useEffect(() => {
    if (!quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmChecked) return;
    if (quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportSafety.needs_confirm) return;
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmChecked(false);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmArmedAtMs(0);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTickMs(0);
    appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmEvent(
      "trail_import_disarm_risk_cleared",
      "replacement-risk requirement cleared for replay trail import"
    );
  }, [
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmArmedAtMs,
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmChecked,
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTickMs,
    quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportSafety.needs_confirm,
    appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmEvent,
  ]);
  React.useEffect(() => {
    if (
      !quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmChecked
      || !quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportSafety.needs_confirm
    ) {
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmArmedAtMs(0);
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTickMs(0);
      return;
    }
    const nowMs = Date.now();
    if (Number(quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmArmedAtMs || 0) <= 0) {
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmArmedAtMs(nowMs);
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTickMs(nowMs);
    }
    const timer = setInterval(() => {
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTickMs(Date.now());
    }, 1_000);
    return () => clearInterval(timer);
  }, [
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmArmedAtMs,
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmChecked,
    quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportSafety.needs_confirm,
  ]);
  React.useEffect(() => {
    if (!quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmChecked) return;
    if (!quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportSafety.needs_confirm) return;
    const armedAt = Number(
      quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmArmedAtMs || 0
    );
    if (armedAt <= 0) return;
    const timeoutMs = QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_IMPORT_CONFIRM_TIMEOUT_MS;
    const elapsedMs = Math.max(0, Date.now() - armedAt);
    const remainingMs = Math.max(0, timeoutMs - elapsedMs);
    const timeout = setTimeout(() => {
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmChecked(false);
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmArmedAtMs(0);
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTickMs(0);
      appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmEvent(
        "trail_import_auto_disarm_timeout",
        "replay trail import replacement-confirm timer elapsed (20s)"
      );
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
        "dry-run handoff apply confirm activity replay trail import confirm auto-disarmed: re-check confirm to import replay timeline"
      );
    }, remainingMs);
    return () => clearTimeout(timeout);
  }, [
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmArmedAtMs,
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmChecked,
    quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportSafety.needs_confirm,
    appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmEvent,
  ]);
  React.useEffect(() => {
    if (!quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmChecked) return;
    if (quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplaySafety.needs_confirm) return;
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmChecked(false);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmArmedAtMs(0);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTickMs(0);
    appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmEvent(
      "replay_disarm_risk_cleared",
      "replacement-risk requirement cleared for replay"
    );
  }, [
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmArmedAtMs,
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmChecked,
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTickMs,
    quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplaySafety.needs_confirm,
    appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmEvent,
  ]);
  React.useEffect(() => {
    if (
      !quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmChecked
      || !quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplaySafety.needs_confirm
    ) {
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmArmedAtMs(0);
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTickMs(0);
      return;
    }
    const nowMs = Date.now();
    if (Number(quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmArmedAtMs || 0) <= 0) {
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmArmedAtMs(nowMs);
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTickMs(nowMs);
    }
    const timer = setInterval(() => {
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTickMs(Date.now());
    }, 1_000);
    return () => clearInterval(timer);
  }, [
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmArmedAtMs,
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmChecked,
    quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplaySafety.needs_confirm,
  ]);
  React.useEffect(() => {
    if (!quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmChecked) return;
    if (!quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplaySafety.needs_confirm) return;
    const armedAt = Number(quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmArmedAtMs || 0);
    if (armedAt <= 0) return;
    const timeoutMs = QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TIMEOUT_MS;
    const elapsedMs = Math.max(0, Date.now() - armedAt);
    const remainingMs = Math.max(0, timeoutMs - elapsedMs);
    const timeout = setTimeout(() => {
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmChecked(false);
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmArmedAtMs(0);
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTickMs(0);
      appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmEvent(
        "replay_auto_disarm_timeout",
        "replay replacement-confirm timer elapsed (20s)"
      );
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
        "dry-run handoff apply confirm activity replay confirm auto-disarmed: re-check confirm to replay"
      );
    }, remainingMs);
    return () => clearTimeout(timeout);
  }, [
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmArmedAtMs,
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmChecked,
    quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplaySafety.needs_confirm,
    appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmEvent,
  ]);
  const quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydratedHint = React.useMemo(() => {
    const hydrated = quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydratedSnapshot;
    if (!hydrated || typeof hydrated !== "object") {
      return "dry-run handoff hydrate: no imported snapshot applied";
    }
    const pkg = hydrated.pkg && typeof hydrated.pkg === "object" ? hydrated.pkg : {};
    const summary = pkg.dry_run_summary || {};
    return [
      `dry-run handoff hydrate: active`,
      `parse ${String(summary.parse_state || "empty")}`,
      `policy ${String(summary.existing_policy || "strict_reject")}->${String(summary.incoming_policy || "strict_reject")}`,
      `diff +${Number(summary.added_override_count || 0)}/-${Number(summary.removed_override_count || 0)}/~${Number(summary.changed_override_count || 0)}`,
      `hydrated_at ${String(hydrated.hydrated_at_iso || "-")}`,
    ].join(", ");
  }, [quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydratedSnapshot]);
  const quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydratedPreview = React.useMemo(() => {
    const hydrated = quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydratedSnapshot;
    if (!hydrated || typeof hydrated !== "object") {
      return "dry-run handoff hydrate preview: no imported snapshot applied";
    }
    const pkg = hydrated.pkg && typeof hydrated.pkg === "object" ? hydrated.pkg : {};
    const summary = pkg.dry_run_summary || {};
    const safety = pkg.apply_safety || {};
    const snapshot = pkg.trust_audit_bundle_snapshot || {};
    return [
      `hydrated_at=${String(hydrated.hydrated_at_iso || "-")}`,
      `handoff kind=${String(pkg.kind || QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_KIND)} schema=${Number(pkg.schema_version || QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_SCHEMA_VERSION)} exported_at=${String(pkg.exported_at_iso || "-")}`,
      `summary parse=${String(summary.parse_state || "empty")} policy=${String(summary.existing_policy || "strict_reject")}->${String(summary.incoming_policy || "strict_reject")} changed=${Boolean(summary.policy_changed) ? "yes" : "no"}`,
      `summary override live=${Number(summary.existing_override_count || 0)} incoming=${Number(summary.incoming_override_count || 0)} diff +${Number(summary.added_override_count || 0)}/-${Number(summary.removed_override_count || 0)}/~${Number(summary.changed_override_count || 0)}/=${Number(summary.unchanged_override_count || 0)}`,
      `safety needs_confirm=${Boolean(safety.needs_confirm) ? "yes" : "no"} policy_changed=${Boolean(safety.policy_changed) ? "yes" : "no"} overrides_replaced=${Boolean(safety.overrides_replaced) ? "yes" : "no"} parse=${String(safety.parse_state || "blocked")}`,
      `bundle kind=${String(snapshot.kind || QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_BUNDLE_KIND)} schema=${Number(snapshot.schema_version || QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_BUNDLE_SCHEMA_VERSION)} policy=${String(snapshot.trust_policy_mode || "strict_reject")} override_events=${Number(snapshot.override_event_count || 0)} parse=${String(snapshot.parse_state || "empty")}`,
      `import_preview=${String(pkg.import_preview || "-")}`,
    ].join("\n");
  }, [quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydratedSnapshot]);
  const applyQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffFromText = React.useCallback(() => {
    if (parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackagePayload.empty) {
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
        "dry-run handoff apply skipped: empty payload"
      );
      return;
    }
    if (parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackagePayload.error) {
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
        `dry-run handoff apply failed: ${parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackagePayload.error}`
      );
      return;
    }
    const pkg = parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackagePayload.pkg || null;
    if (!pkg || typeof pkg !== "object") {
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
        "dry-run handoff apply failed: invalid payload"
      );
      return;
    }
    if (
      quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateSafety.needs_confirm
      && !quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmChecked
    ) {
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
        "dry-run handoff apply blocked: replacement safety confirm required"
      );
      return;
    }
    const summary = pkg.dry_run_summary || {};
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydratedSnapshot({
      hydrated_at_iso: new Date().toISOString(),
      pkg,
    });
    if (quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmChecked) {
      appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityEvent(
        "disarm_after_hydrate",
        "hydrate apply succeeded; confirm disarmed"
      );
    }
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmChecked(false);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmArmedAtMs(0);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmTickMs(0);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
      `dry-run handoff snapshot hydrated (parse=${String(summary.parse_state || "empty")}, diff +${Number(summary.added_override_count || 0)}/-${Number(summary.removed_override_count || 0)}/~${Number(summary.changed_override_count || 0)})`
    );
  }, [
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmChecked,
    quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateSafety.needs_confirm,
    parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackagePayload.empty,
    parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackagePayload.error,
    parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackagePayload.pkg,
    appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityEvent,
  ]);
  const resetQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydratedSnapshot = React.useCallback(() => {
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydratedSnapshot(null);
    if (quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmChecked) {
      appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityEvent(
        "disarm_after_reset",
        "hydrate snapshot reset; confirm disarmed"
      );
    }
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmChecked(false);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmArmedAtMs(0);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmTickMs(0);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
      "dry-run handoff snapshot reset"
    );
  }, [
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmChecked,
    appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityEvent,
  ]);
  React.useEffect(() => {
    if (!quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmChecked) return;
    if (quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateSafety.needs_confirm) return;
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmChecked(false);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmArmedAtMs(0);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmTickMs(0);
    appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityEvent(
      "disarm_risk_cleared",
      "replacement-risk requirement cleared"
    );
  }, [
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmChecked,
    quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateSafety.needs_confirm,
    appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityEvent,
  ]);
  React.useEffect(() => {
    if (
      !quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmChecked
      || !quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateSafety.needs_confirm
    ) {
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmArmedAtMs(0);
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmTickMs(0);
      return;
    }
    const nowMs = Date.now();
    if (Number(quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmArmedAtMs || 0) <= 0) {
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmArmedAtMs(nowMs);
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmTickMs(nowMs);
    }
    const timer = setInterval(() => {
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmTickMs(Date.now());
    }, 1_000);
    return () => clearInterval(timer);
  }, [
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmArmedAtMs,
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmChecked,
    quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateSafety.needs_confirm,
  ]);
  React.useEffect(() => {
    if (!quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmChecked) return;
    if (!quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateSafety.needs_confirm) return;
    const armedAt = Number(quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmArmedAtMs || 0);
    if (armedAt <= 0) return;
    const timeoutMs = QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_TIMEOUT_MS;
    const elapsedMs = Math.max(0, Date.now() - armedAt);
    const remainingMs = Math.max(0, timeoutMs - elapsedMs);
    const timeout = setTimeout(() => {
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmChecked(false);
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmArmedAtMs(0);
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmTickMs(0);
      appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityEvent(
        "auto_disarm_timeout",
        "safety timer elapsed (20s)"
      );
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
        "dry-run handoff apply confirm auto-disarmed: re-check confirm to hydrate"
      );
    }, remainingMs);
    return () => clearTimeout(timeout);
  }, [
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmArmedAtMs,
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmChecked,
    quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateSafety.needs_confirm,
    appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityEvent,
  ]);
  const copyQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackageJson = React.useCallback(async () => {
    const jsonText = serializeQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackage(
      quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackagePayload
    );
    const summary = quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackagePayload?.dry_run_summary || {};
    try {
      if (typeof navigator !== "undefined" && navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(jsonText);
        setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
          `dry-run handoff package copied (parse=${String(summary.parse_state || "empty")}, diff +${Number(summary.added_override_count || 0)}/-${Number(summary.removed_override_count || 0)}/~${Number(summary.changed_override_count || 0)})`
        );
        return;
      }
      throw new Error("clipboard unavailable");
    } catch (_) {
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
        "dry-run handoff package copy failed"
      );
    }
  }, [quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackagePayload]);
  const exportQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackageToJson = React.useCallback(() => {
    const jsonText = serializeQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackage(
      quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackagePayload
    );
    const summary = quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackagePayload?.dry_run_summary || {};
    try {
      if (typeof window === "undefined" || typeof document === "undefined" || !window.URL) {
        setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
          "dry-run handoff package export prepared in-memory"
        );
        return;
      }
      const blob = new Blob([jsonText], { type: "application/json;charset=utf-8" });
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      const ts = new Date().toISOString().replace(/[:.]/g, "-");
      anchor.href = url;
      anchor.download = `graph_lab_quick_telemetry_strict_rollback_trust_audit_apply_dry_run_handoff_package_${ts}.json`;
      document.body.appendChild(anchor);
      anchor.click();
      document.body.removeChild(anchor);
      window.URL.revokeObjectURL(url);
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
        `dry-run handoff package export complete (parse=${String(summary.parse_state || "empty")}, diff +${Number(summary.added_override_count || 0)}/-${Number(summary.removed_override_count || 0)}/~${Number(summary.changed_override_count || 0)})`
      );
    } catch (_) {
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
        "dry-run handoff package export failed"
      );
    }
  }, [quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackagePayload]);
  const copyQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityTrailJson = React.useCallback(async () => {
    const jsonText = serializeQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityBundle(
      quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityRows
    );
    try {
      if (typeof navigator !== "undefined" && navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(jsonText);
        setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
          `dry-run handoff apply confirm activity copied (${quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityRows.length} events)`
        );
        return;
      }
      throw new Error("clipboard unavailable");
    } catch (_) {
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
        "dry-run handoff apply confirm activity copy failed"
      );
    }
  }, [quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityRows]);
  const exportQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityTrailToJson = React.useCallback(() => {
    const jsonText = serializeQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityBundle(
      quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityRows
    );
    try {
      if (typeof window === "undefined" || typeof document === "undefined" || !window.URL) {
        setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
          "dry-run handoff apply confirm activity export prepared in-memory"
        );
        return;
      }
      const blob = new Blob([jsonText], { type: "application/json;charset=utf-8" });
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      const ts = new Date().toISOString().replace(/[:.]/g, "-");
      anchor.href = url;
      anchor.download = `graph_lab_quick_telemetry_strict_rollback_trust_audit_dry_run_handoff_confirm_activity_${ts}.json`;
      document.body.appendChild(anchor);
      anchor.click();
      document.body.removeChild(anchor);
      window.URL.revokeObjectURL(url);
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
        `dry-run handoff apply confirm activity export complete (${quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityRows.length} events)`
      );
    } catch (_) {
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
        "dry-run handoff apply confirm activity export failed"
      );
    }
  }, [quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityRows]);
  const resetQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityTrail = React.useCallback(() => {
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityTrail([]);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmChecked(false);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmArmedAtMs(0);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTickMs(0);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmChecked(false);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmArmedAtMs(0);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTickMs(0);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrail([]);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrail([]);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
      "dry-run handoff apply confirm activity reset"
    );
  }, []);
  const copyQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailJson = React.useCallback(async () => {
    const jsonText = serializeQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailBundle(
      quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmRows
    );
    try {
      if (typeof navigator !== "undefined" && navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(jsonText);
        setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
          `dry-run handoff apply confirm activity replay trail copied (${quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmRows.length} events)`
        );
        return;
      }
      throw new Error("clipboard unavailable");
    } catch (_) {
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
        "dry-run handoff apply confirm activity replay trail copy failed"
      );
    }
  }, [quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmRows]);
  const exportQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailToJson = React.useCallback(() => {
    const jsonText = serializeQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailBundle(
      quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmRows
    );
    try {
      if (typeof window === "undefined" || typeof document === "undefined" || !window.URL) {
        setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
          "dry-run handoff apply confirm activity replay trail export prepared in-memory"
        );
        return;
      }
      const blob = new Blob([jsonText], { type: "application/json;charset=utf-8" });
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      const ts = new Date().toISOString().replace(/[:.]/g, "-");
      anchor.href = url;
      anchor.download = `graph_lab_quick_telemetry_strict_rollback_trust_audit_dry_run_handoff_confirm_activity_replay_trail_${ts}.json`;
      document.body.appendChild(anchor);
      anchor.click();
      document.body.removeChild(anchor);
      window.URL.revokeObjectURL(url);
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
        `dry-run handoff apply confirm activity replay trail export complete (${quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmRows.length} events)`
      );
    } catch (_) {
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
        "dry-run handoff apply confirm activity replay trail export failed"
      );
    }
  }, [quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmRows]);
  const resetQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrail = React.useCallback(() => {
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmChecked(false);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmArmedAtMs(0);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTickMs(0);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrail([]);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrail([]);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
      "dry-run handoff apply confirm activity replay trail reset"
    );
  }, []);
  const copyQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailJson = React.useCallback(async () => {
    const jsonText = serializeQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailBundle(
      quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmRows
    );
    const stamp = `continuity echo lifecycle stamp: copy (${quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmRows.length} rows @ ${new Date().toISOString()})`;
    try {
      if (typeof navigator !== "undefined" && navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(jsonText);
        setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailControlsStatus(
          `import confirm trail controls: event snapshot copied (${quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmRows.length} rows), continuity echo aligned, ${stamp}`
        );
        appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmEvent(
          "import_confirm_trail_controls_copy",
          `copy complete (${quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmRows.length} rows, ${stamp})`
        );
        setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
          `dry-run handoff apply confirm activity replay trail import confirm trail copied (${quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmRows.length} events)`
        );
        return;
      }
      throw new Error("clipboard unavailable");
    } catch (_) {
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailControlsStatus(
        `import confirm trail controls: event snapshot copy failed, continuity echo aligned, ${stamp}`
      );
      appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmEvent(
        "import_confirm_trail_controls_copy_failed",
        `copy failed (${stamp})`
      );
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
        "dry-run handoff apply confirm activity replay trail import confirm trail copy failed"
      );
    }
  }, [
    quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmRows,
    appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmEvent,
  ]);
  const exportQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailToJson = React.useCallback(() => {
    const jsonText = serializeQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailBundle(
      quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmRows
    );
    const stamp = `continuity echo lifecycle stamp: export (${quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmRows.length} rows @ ${new Date().toISOString()})`;
    try {
      if (typeof window === "undefined" || typeof document === "undefined" || !window.URL) {
        setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailControlsStatus(
          `import confirm trail controls: event snapshot export prepared in-memory, continuity echo aligned, ${stamp}`
        );
        appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmEvent(
          "import_confirm_trail_controls_export_memory",
          `export prepared in-memory (${stamp})`
        );
        setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
          "dry-run handoff apply confirm activity replay trail import confirm trail export prepared in-memory"
        );
        return;
      }
      const blob = new Blob([jsonText], { type: "application/json;charset=utf-8" });
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      const ts = new Date().toISOString().replace(/[:.]/g, "-");
      anchor.href = url;
      anchor.download = `graph_lab_quick_telemetry_strict_rollback_trust_audit_dry_run_handoff_confirm_activity_replay_trail_import_confirm_trail_${ts}.json`;
      document.body.appendChild(anchor);
      anchor.click();
      document.body.removeChild(anchor);
      window.URL.revokeObjectURL(url);
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailControlsStatus(
        `import confirm trail controls: event snapshot export complete (${quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmRows.length} rows), continuity echo aligned, ${stamp}`
      );
      appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmEvent(
        "import_confirm_trail_controls_export",
        `export complete (${quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmRows.length} rows, ${stamp})`
      );
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
        `dry-run handoff apply confirm activity replay trail import confirm trail export complete (${quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmRows.length} events)`
      );
    } catch (_) {
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailControlsStatus(
        `import confirm trail controls: event snapshot export failed, continuity echo aligned, ${stamp}`
      );
      appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmEvent(
        "import_confirm_trail_controls_export_failed",
        `export failed (${stamp})`
      );
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
        "dry-run handoff apply confirm activity replay trail import confirm trail export failed"
      );
    }
  }, [
    quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmRows,
    appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmEvent,
  ]);
  const resetQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrail = React.useCallback(() => {
    const stamp = `continuity echo lifecycle stamp: reset (0 rows @ ${new Date().toISOString()})`;
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrail([]);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailControlsStatus(
      `import confirm trail controls: event snapshot reset, continuity echo aligned, ${stamp}`
    );
    appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmEvent(
      "import_confirm_trail_controls_reset",
      `reset complete (${stamp})`
    );
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
      "dry-run handoff apply confirm activity replay trail import confirm trail reset"
    );
  }, [appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmEvent]);
  const applyQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailFromText = React.useCallback(() => {
    const stampBase = `continuity echo lifecycle stamp: apply (${new Date().toISOString()})`;
    if (parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportPayload.empty) {
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailControlsStatus(
        `import confirm trail controls: apply skipped (empty payload), ${stampBase}`
      );
      appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmEvent(
        "import_confirm_trail_apply_skipped_empty",
        `apply skipped (${stampBase})`
      );
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
        "dry-run handoff apply confirm activity replay trail import confirm trail import skipped: empty payload"
      );
      return;
    }
    if (parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportPayload.error) {
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailControlsStatus(
        `import confirm trail controls: apply blocked (parse error), ${stampBase}`
      );
      appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmEvent(
        "import_confirm_trail_apply_blocked_parse",
        `apply blocked by parse error (${stampBase})`
      );
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
        `dry-run handoff apply confirm activity replay trail import confirm trail import failed: ${parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportPayload.error}`
      );
      return;
    }
    const bundle = parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportPayload.bundle || null;
    if (!bundle || typeof bundle !== "object") {
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailControlsStatus(
        `import confirm trail controls: apply blocked (invalid payload), ${stampBase}`
      );
      appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmEvent(
        "import_confirm_trail_apply_blocked_invalid",
        `apply blocked by invalid payload (${stampBase})`
      );
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
        "dry-run handoff apply confirm activity replay trail import confirm trail import failed: invalid payload"
      );
      return;
    }
    if (
      quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportSafety.needs_confirm
      && !quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmChecked
    ) {
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailControlsStatus(
        `import confirm trail controls: apply blocked (replacement confirm required), ${stampBase}`
      );
      appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmEvent(
        "import_confirm_trail_apply_blocked_confirm",
        `apply blocked by replacement confirm (${stampBase})`
      );
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
        "dry-run handoff apply confirm activity replay trail import confirm trail import blocked: replacement confirm required"
      );
      return;
    }
    const rows = Array.isArray(bundle.entries) ? bundle.entries : [];
    const applyStamp = `continuity echo lifecycle stamp: apply (${rows.length} rows @ ${new Date().toISOString()})`;
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrail(rows);
    if (quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmChecked) {
      appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmEvent(
        "import_confirm_trail_import_disarm_after_apply",
        "import confirm trail import applied; replacement confirm disarmed"
      );
    }
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmChecked(false);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmArmedAtMs(0);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmTickMs(0);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailControlsStatus(
      `import confirm trail controls: event snapshot aligned after apply (${rows.length} rows), ${applyStamp}`
    );
    appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmEvent(
      "import_confirm_trail_apply_aligned",
      `apply aligned (${rows.length} rows, ${applyStamp})`
    );
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
      `dry-run handoff apply confirm activity replay trail import confirm trail hydrated (${rows.length} events)`
    );
  }, [
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmChecked,
    parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportPayload.bundle,
    parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportPayload.empty,
    parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportPayload.error,
    quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportSafety.needs_confirm,
    appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmEvent,
  ]);
  const applyQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailFromText = React.useCallback(() => {
    if (parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportPayload.empty) {
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
        "dry-run handoff apply confirm activity replay trail import skipped: empty payload"
      );
      return;
    }
    if (parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportPayload.error) {
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
        `dry-run handoff apply confirm activity replay trail import failed: ${parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportPayload.error}`
      );
      return;
    }
    const bundle = parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportPayload.bundle || null;
    if (!bundle || typeof bundle !== "object") {
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
        "dry-run handoff apply confirm activity replay trail import failed: invalid payload"
      );
      return;
    }
    if (
      quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportSafety.needs_confirm
      && !quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmChecked
    ) {
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
        "dry-run handoff apply confirm activity replay trail import blocked: replacement confirm required"
      );
      return;
    }
    const rows = Array.isArray(bundle.entries) ? bundle.entries : [];
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrail(rows);
    if (quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmChecked) {
      appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmEvent(
        "trail_import_disarm_after_apply",
        "replay trail import applied; replacement confirm disarmed"
      );
    }
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmChecked(false);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmArmedAtMs(0);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTickMs(0);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
      `dry-run handoff apply confirm activity replay trail hydrated (${rows.length} events)`
    );
  }, [
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmChecked,
    parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportPayload.bundle,
    parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportPayload.empty,
    parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportPayload.error,
    quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportSafety.needs_confirm,
    appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmEvent,
  ]);
  const replayQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityTrailFromText = React.useCallback(() => {
    if (parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityBundlePayload.empty) {
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
        "dry-run handoff apply confirm activity replay skipped: empty payload"
      );
      return;
    }
    if (parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityBundlePayload.error) {
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
        `dry-run handoff apply confirm activity replay failed: ${parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityBundlePayload.error}`
      );
      return;
    }
    const bundle = parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityBundlePayload.bundle || null;
    if (!bundle || typeof bundle !== "object") {
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
        "dry-run handoff apply confirm activity replay failed: invalid payload"
      );
      return;
    }
    if (
      quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplaySafety.needs_confirm
      && !quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmChecked
    ) {
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
        "dry-run handoff apply confirm activity replay blocked: replacement confirm required"
      );
      return;
    }
    const rows = Array.isArray(bundle.entries) ? bundle.entries : [];
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityTrail(rows);
    if (quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmChecked) {
      appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmEvent(
        "replay_disarm_after_replay",
        "confirm activity replay applied; replacement confirm disarmed"
      );
    }
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmChecked(false);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmArmedAtMs(0);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTickMs(0);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
      `dry-run handoff apply confirm activity replayed (${rows.length} events)`
    );
  }, [
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmChecked,
    parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityBundlePayload.bundle,
    parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityBundlePayload.empty,
    parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityBundlePayload.error,
    quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplaySafety.needs_confirm,
    appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmEvent,
  ]);
  const quickTelemetryStrictRollbackTrustAuditBundleApplyConfirmCountdownHint = React.useMemo(() => {
    const safety = quickTelemetryStrictRollbackTrustAuditBundleApplySafety;
    if (safety.parse_state === "empty") {
      return "apply confirm timer: waiting for trust-audit payload";
    }
    if (safety.parse_state === "error") {
      return "apply confirm timer: blocked by parse error";
    }
    if (!safety.needs_confirm) {
      return "apply confirm timer: no replacement-risk confirmation required";
    }
    const timeoutSec = Math.floor(
      QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_CONFIRM_TIMEOUT_MS / 1000
    );
    if (!quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmChecked) {
      return `apply confirm timer: check confirm to arm (${timeoutSec}s auto-disarm)`;
    }
    const armedAt = Number(quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmArmedAtMs || 0);
    const tickMs = Number(quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmTickMs || 0);
    const nowMs = tickMs > 0 ? tickMs : Date.now();
    const elapsedMs = armedAt > 0 ? Math.max(0, nowMs - armedAt) : 0;
    const remainingSec = Math.max(
      0,
      Math.ceil((QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_CONFIRM_TIMEOUT_MS - elapsedMs) / 1000)
    );
    if (remainingSec <= 5) {
      return `apply confirm timer: armed (${remainingSec}s left, auto-disarm soon)`;
    }
    return `apply confirm timer: armed (${remainingSec}s left)`;
  }, [
    quickTelemetryStrictRollbackTrustAuditBundleApplySafety,
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmArmedAtMs,
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmChecked,
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmTickMs,
  ]);
  React.useEffect(() => {
    if (!quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmChecked) return;
    if (quickTelemetryStrictRollbackTrustAuditBundleApplySafety.needs_confirm) return;
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmChecked(false);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmArmedAtMs(0);
    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmTickMs(0);
  }, [
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmArmedAtMs,
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmChecked,
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmTickMs,
    quickTelemetryStrictRollbackTrustAuditBundleApplySafety.needs_confirm,
  ]);
  React.useEffect(() => {
    if (
      !quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmChecked
      || !quickTelemetryStrictRollbackTrustAuditBundleApplySafety.needs_confirm
    ) {
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmArmedAtMs(0);
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmTickMs(0);
      return;
    }
    const nowMs = Date.now();
    if (Number(quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmArmedAtMs || 0) <= 0) {
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmArmedAtMs(nowMs);
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmTickMs(nowMs);
    }
    const timer = setInterval(() => {
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmTickMs(Date.now());
    }, 1_000);
    return () => clearInterval(timer);
  }, [
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmArmedAtMs,
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmChecked,
    quickTelemetryStrictRollbackTrustAuditBundleApplySafety.needs_confirm,
  ]);
  React.useEffect(() => {
    if (!quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmChecked) return;
    if (!quickTelemetryStrictRollbackTrustAuditBundleApplySafety.needs_confirm) return;
    const armedAt = Number(quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmArmedAtMs || 0);
    if (armedAt <= 0) return;
    const timeoutMs = QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_CONFIRM_TIMEOUT_MS;
    const elapsedMs = Math.max(0, Date.now() - armedAt);
    const remainingMs = Math.max(0, timeoutMs - elapsedMs);
    const timeout = setTimeout(() => {
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmChecked(false);
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmArmedAtMs(0);
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmTickMs(0);
      setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleStatus(
        "trust audit apply confirm auto-disarmed: re-check confirm to apply"
      );
    }, remainingMs);
    return () => clearTimeout(timeout);
  }, [
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmArmedAtMs,
    quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmChecked,
    quickTelemetryStrictRollbackTrustAuditBundleApplySafety.needs_confirm,
  ]);
  const quickTelemetryStrictRollbackPackageChecklistDeltaGuard = React.useMemo(() => {
    if (parsedQuickTelemetryStrictRollbackDrillPackagePayload.empty) {
      return {
        has_delta: false,
        status_changed: false,
        pass_count_delta: 0,
        item_count_delta: 0,
        failed_visible_count_delta: 0,
        ok_flip_count: 0,
        missing_live_item_count: 0,
        extra_imported_item_count: 0,
      };
    }
    if (parsedQuickTelemetryStrictRollbackDrillPackagePayload.error) {
      return {
        has_delta: true,
        status_changed: true,
        pass_count_delta: 0,
        item_count_delta: 0,
        failed_visible_count_delta: 0,
        ok_flip_count: 0,
        missing_live_item_count: 0,
        extra_imported_item_count: 0,
      };
    }
    const importedChecklist = parsedQuickTelemetryStrictRollbackDrillPackagePayload.pkg?.checklist_report || {};
    const liveChecklist = quickTelemetryDrilldownStrictRollbackChecklistReport || {};
    const importedItems = Array.isArray(importedChecklist.items) ? importedChecklist.items : [];
    const liveItems = Array.isArray(liveChecklist.items) ? liveChecklist.items : [];
    const importedMap = new Map();
    importedItems.forEach((row) => {
      const id = String(row?.id || "").trim();
      if (!id) return;
      importedMap.set(id, Boolean(row?.ok));
    });
    const liveMap = new Map();
    liveItems.forEach((row) => {
      const id = String(row?.id || "").trim();
      if (!id) return;
      liveMap.set(id, Boolean(row?.ok));
    });
    let okFlipCount = 0;
    liveMap.forEach((ok, id) => {
      if (!importedMap.has(id)) return;
      if (Boolean(importedMap.get(id)) !== Boolean(ok)) {
        okFlipCount += 1;
      }
    });
    let missingLiveItemCount = 0;
    liveMap.forEach((_, id) => {
      if (!importedMap.has(id)) missingLiveItemCount += 1;
    });
    let extraImportedItemCount = 0;
    importedMap.forEach((_, id) => {
      if (!liveMap.has(id)) extraImportedItemCount += 1;
    });
    const statusChanged = String(importedChecklist.status || "HOLD") !== String(liveChecklist.status || "HOLD");
    const passCountDelta = Number(importedChecklist.pass_count || 0) - Number(liveChecklist.pass_count || 0);
    const itemCountDelta = Number(importedChecklist.item_count || 0) - Number(liveChecklist.item_count || 0);
    const failedVisibleDelta =
      Number(importedChecklist.failed_visible_count || 0) - Number(liveChecklist.failed_visible_count || 0);
    const hasDelta = statusChanged
      || passCountDelta !== 0
      || itemCountDelta !== 0
      || failedVisibleDelta !== 0
      || okFlipCount > 0
      || missingLiveItemCount > 0
      || extraImportedItemCount > 0;
    return {
      has_delta: hasDelta,
      status_changed: statusChanged,
      pass_count_delta: passCountDelta,
      item_count_delta: itemCountDelta,
      failed_visible_count_delta: failedVisibleDelta,
      ok_flip_count: okFlipCount,
      missing_live_item_count: missingLiveItemCount,
      extra_imported_item_count: extraImportedItemCount,
    };
  }, [
    parsedQuickTelemetryStrictRollbackDrillPackagePayload.empty,
    parsedQuickTelemetryStrictRollbackDrillPackagePayload.error,
    parsedQuickTelemetryStrictRollbackDrillPackagePayload.pkg,
    quickTelemetryDrilldownStrictRollbackChecklistReport,
  ]);
  const quickTelemetryStrictRollbackPackageReplayPreview = React.useMemo(() => {
    if (parsedQuickTelemetryStrictRollbackDrillPackagePayload.empty) {
      return "rollback package replay preview: waiting for JSON payload";
    }
    if (parsedQuickTelemetryStrictRollbackDrillPackagePayload.error) {
      return `rollback package replay preview: invalid payload (${parsedQuickTelemetryStrictRollbackDrillPackagePayload.error})`;
    }
    const pkg = parsedQuickTelemetryStrictRollbackDrillPackagePayload.pkg || {};
    const snapshot = pkg.preset_snapshot || {};
    const checklist = pkg.checklist_report || {};
    const timelineRows = Array.isArray(pkg.cutover_timeline_entries) ? pkg.cutover_timeline_entries : [];
    const provenance = pkg.provenance_guard && typeof pkg.provenance_guard === "object"
      ? pkg.provenance_guard
      : {};
    return [
      `rollback package replay preview: preset ${String(snapshot.preset_id || "custom")}`,
      `mode ${String(snapshot.import_mode || "compat")}`,
      `reason ${String(snapshot.reason_query || "-") || "-"}`,
      `checklist ${String(checklist.status || "HOLD")} ${Number(checklist.pass_count || 0)}/${Number(checklist.item_count || 0)}`,
      `fail ${Number(checklist.failed_visible_count || 0)}/${Number(checklist.visible_count || 0)}`,
      `timeline_entries ${timelineRows.length}`,
      `source ${String(provenance.source_stamp || "-")}`,
    ].join(", ");
  }, [
    parsedQuickTelemetryStrictRollbackDrillPackagePayload.empty,
    parsedQuickTelemetryStrictRollbackDrillPackagePayload.error,
    parsedQuickTelemetryStrictRollbackDrillPackagePayload.pkg,
  ]);
  const quickTelemetryStrictRollbackPackageChecklistDeltaHint = React.useMemo(() => {
    if (parsedQuickTelemetryStrictRollbackDrillPackagePayload.empty) {
      return "checklist delta guard: waiting for rollback package payload";
    }
    if (parsedQuickTelemetryStrictRollbackDrillPackagePayload.error) {
      return `checklist delta guard: blocked (${parsedQuickTelemetryStrictRollbackDrillPackagePayload.error})`;
    }
    if (!quickTelemetryStrictRollbackPackageChecklistDeltaGuard.has_delta) {
      return "checklist delta guard: no delta detected (replay allowed)";
    }
    return [
      "checklist delta guard: delta detected",
      `status_change:${quickTelemetryStrictRollbackPackageChecklistDeltaGuard.status_changed ? "yes" : "no"}`,
      `pass_delta:${formatSigned(quickTelemetryStrictRollbackPackageChecklistDeltaGuard.pass_count_delta)}`,
      `item_delta:${formatSigned(quickTelemetryStrictRollbackPackageChecklistDeltaGuard.item_count_delta)}`,
      `fail_delta:${formatSigned(quickTelemetryStrictRollbackPackageChecklistDeltaGuard.failed_visible_count_delta)}`,
      `ok_flip:${Number(quickTelemetryStrictRollbackPackageChecklistDeltaGuard.ok_flip_count || 0)}`,
      `missing_live:${Number(quickTelemetryStrictRollbackPackageChecklistDeltaGuard.missing_live_item_count || 0)}`,
      `extra_imported:${Number(quickTelemetryStrictRollbackPackageChecklistDeltaGuard.extra_imported_item_count || 0)}`,
    ].join(", ");
  }, [
    parsedQuickTelemetryStrictRollbackDrillPackagePayload.empty,
    parsedQuickTelemetryStrictRollbackDrillPackagePayload.error,
    quickTelemetryStrictRollbackPackageChecklistDeltaGuard,
  ]);
  React.useEffect(() => {
    if (!quickTelemetryDrilldownStrictRollbackPackageDeltaConfirmChecked) return;
    const provenanceConfirmActive = quickTelemetryStrictRollbackPackageProvenanceGuard.has_guard_issue
      && normalizeQuickTelemetryStrictRollbackPackageTrustPolicy(
        quickTelemetryStrictRollbackPackageTrustPolicy
      ) !== "strict_reject";
    if (quickTelemetryStrictRollbackPackageChecklistDeltaGuard.has_delta || provenanceConfirmActive) return;
    setQuickTelemetryDrilldownStrictRollbackPackageDeltaConfirmChecked(false);
  }, [
    quickTelemetryDrilldownStrictRollbackPackageDeltaConfirmChecked,
    quickTelemetryStrictRollbackPackageChecklistDeltaGuard.has_delta,
    quickTelemetryStrictRollbackPackageTrustPolicy,
    quickTelemetryStrictRollbackPackageProvenanceGuard.has_guard_issue,
  ]);
  const quickTelemetryDrilldownStrictRollbackPackagePreview = React.useMemo(() => {
    const report = quickTelemetryStrictRollbackDrillPackageBundle.checklist_report || {};
    const snapshot = quickTelemetryStrictRollbackDrillPackageBundle.preset_snapshot || {};
    const timelineRows = Array.isArray(quickTelemetryStrictRollbackDrillPackageBundle.cutover_timeline_entries)
      ? quickTelemetryStrictRollbackDrillPackageBundle.cutover_timeline_entries
      : [];
    const provenance = quickTelemetryStrictRollbackDrillPackageBundle.provenance || {};
    return [
      `rollback package preview: preset ${String(snapshot.preset_id || "custom")}`,
      `mode ${String(snapshot.import_mode || "compat")}`,
      `reason ${String(snapshot.reason_query || "-") || "-"}`,
      `checklist ${String(report.status || "HOLD")} ${Number(report.pass_count || 0)}/${Number(report.item_count || 0)}`,
      `timeline_entries ${timelineRows.length}`,
      `source ${String(provenance.source_stamp || QUICK_TELEMETRY_STRICT_ROLLBACK_DRILL_PACKAGE_SOURCE_STAMP)}`,
    ].join(", ");
  }, [quickTelemetryStrictRollbackDrillPackageBundle]);
  const filterImportAuditResetGuidedHint = React.useMemo(() => {
    if (!filterImportAuditResetArmedChecked) {
      return `safe reset guide: arm reset -> choose action (auto-disarm ${Math.floor(FILTER_IMPORT_AUDIT_RESET_ARM_TIMEOUT_MS / 1000)}s)`;
    }
    const armedAt = Number(filterImportAuditResetArmedAtMs || 0);
    const tickMs = Number(filterImportAuditResetTickMs || 0);
    const nowMs = tickMs > 0 ? tickMs : Date.now();
    const elapsedMs = armedAt > 0 ? Math.max(0, nowMs - armedAt) : 0;
    const remainingSec = Math.max(0, Math.ceil((FILTER_IMPORT_AUDIT_RESET_ARM_TIMEOUT_MS - elapsedMs) / 1000));
    if (remainingSec <= 5) {
      return `safe reset guide: armed (${remainingSec}s left) -> execute one reset action now`;
    }
    return `safe reset guide: armed (${remainingSec}s left) -> next reset executes then disarms`;
  }, [filterImportAuditResetArmedAtMs, filterImportAuditResetArmedChecked, filterImportAuditResetTickMs]);
  const filterImportAuditRowCap = React.useMemo(
    () => clampInteger(filterImportAuditRowCapText, 6, 200, 24),
    [filterImportAuditRowCapText]
  );
  React.useEffect(() => {
    setFilterImportAuditRowOffset(0);
  }, [filterImportAuditKindFilter, filterImportAuditModeFilter, filterImportAuditRowCap, filterImportAuditSearchText]);
  const filterImportAuditMaxOffset = React.useMemo(
    () => Math.max(0, Number(filterImportAuditRowsFiltered.length || 0) - filterImportAuditRowCap),
    [filterImportAuditRowCap, filterImportAuditRowsFiltered.length]
  );
  React.useEffect(() => {
    if (filterImportAuditRowOffset > filterImportAuditMaxOffset) {
      setFilterImportAuditRowOffset(filterImportAuditMaxOffset);
    }
  }, [filterImportAuditMaxOffset, filterImportAuditRowOffset]);
  const filterImportAuditRowEnd = Math.min(
    filterImportAuditRowsFiltered.length,
    filterImportAuditRowOffset + filterImportAuditRowCap
  );
  const filterImportAuditRowsVisible = React.useMemo(
    () => filterImportAuditRowsFiltered.slice(filterImportAuditRowOffset, filterImportAuditRowEnd),
    [filterImportAuditRowEnd, filterImportAuditRowOffset, filterImportAuditRowsFiltered]
  );
  const activeFilterImportAuditEntry = React.useMemo(() => {
    const rows = Array.isArray(filterImportAuditRowsVisible) ? filterImportAuditRowsVisible : [];
    if (rows.length === 0) return null;
    if (!activeFilterImportAuditId) return rows[0];
    return rows.find((row) => String(row?.id || "") === activeFilterImportAuditId) || rows[0];
  }, [activeFilterImportAuditId, filterImportAuditRowsVisible]);
  React.useEffect(() => {
    const rows = Array.isArray(filterImportAuditRowsVisible) ? filterImportAuditRowsVisible : [];
    if (rows.length === 0) {
      if (activeFilterImportAuditId) {
        setActiveFilterImportAuditId("");
      }
      return;
    }
    if (!activeFilterImportAuditId) {
      setActiveFilterImportAuditId(String(rows[0]?.id || ""));
      return;
    }
    if (rows.some((row) => String(row?.id || "") === activeFilterImportAuditId)) return;
    setActiveFilterImportAuditId(String(rows[0]?.id || ""));
  }, [activeFilterImportAuditId, filterImportAuditRowsVisible]);
  const filterImportAuditDetailText = React.useMemo(
    () => buildFilterImportAuditDetailText(activeFilterImportAuditEntry),
    [activeFilterImportAuditEntry]
  );
  const toggleFilterImportPresetSelection = React.useCallback((presetName) => {
    const name = String(presetName || "").trim();
    if (!name) return;
    setFilterImportSelection((prev) => ({
      ...(prev && typeof prev === "object" && !Array.isArray(prev) ? prev : {}),
      [name]: !Boolean(prev?.[name]),
    }));
  }, []);
  const selectAllFilterImportPresets = React.useCallback(() => {
    const next = {};
    filterImportRows.forEach((row) => {
      const name = String(row.name || "");
      if (!name) return;
      next[name] = true;
    });
    setFilterImportSelection(next);
  }, [filterImportRows]);
  const clearFilterImportPresets = React.useCallback(() => {
    const next = {};
    filterImportRows.forEach((row) => {
      const name = String(row.name || "");
      if (!name) return;
      next[name] = false;
    });
    setFilterImportSelection(next);
  }, [filterImportRows]);
  const applyActiveFilterPreset = React.useCallback(() => {
    const profileName = String(activeFilterPreset || "").trim();
    const cfg = filterPresets[profileName] || DEFAULT_FILTER_PRESETS.default;
    applyFilterPresetConfig(cfg);
  }, [activeFilterPreset, applyFilterPresetConfig, filterPresets]);
  const saveCurrentFilterPreset = React.useCallback(() => {
    const nextName = normalizeFilterPresetName(filterPresetDraft);
    if (!nextName) return;
    const cfg = normalizeFilterPresetConfig(
      {
        sourceFilter,
        severityFilter,
        policyFilter,
        pinnedRunId,
        nonZeroOnly,
        gateHistoryLimit,
        gateHistoryPages,
        rowWindowSizeText,
      },
      DEFAULT_FILTER_PRESETS.default
    );
    setFilterPresets((prev) => ({
      ...prev,
      [nextName]: cfg,
    }));
    setActiveFilterPreset(nextName);
    setFilterPresetDraft(nextName);
  }, [
    filterPresetDraft,
    gateHistoryLimit,
    gateHistoryPages,
    nonZeroOnly,
    pinnedRunId,
    policyFilter,
    rowWindowSizeText,
    severityFilter,
    sourceFilter,
  ]);
  const deleteActiveFilterPreset = React.useCallback(() => {
    const profileName = String(activeFilterPreset || "").trim();
    if (!profileName) return;
    if (Object.prototype.hasOwnProperty.call(DEFAULT_FILTER_PRESETS, profileName)) return;
    setFilterPresets((prev) => {
      if (!Object.prototype.hasOwnProperty.call(prev, profileName)) return prev;
      const next = { ...prev };
      delete next[profileName];
      return next;
    });
  }, [activeFilterPreset]);
  const triggerFilterImportFilePick = React.useCallback(() => {
    const input = filterImportFileInputRef.current;
    if (!input || typeof input.click !== "function") return;
    input.click();
  }, []);
  const handleFilterImportFileChange = React.useCallback((evt) => {
    const file = evt?.target?.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const text = String(reader.result || "");
      setFilterTransferText(text);
      setFilterTransferStatus(`loaded file: ${String(file.name || "-")}`);
    };
    reader.onerror = () => {
      setFilterTransferStatus(`failed to read file: ${String(file.name || "-")}`);
    };
    reader.readAsText(file);
    if (evt?.target) evt.target.value = "";
  }, []);
  const exportFilterPresetsToJson = React.useCallback(() => {
    const jsonText = serializeFilterPresetExportBundle(filterPresets);
    setFilterTransferText(jsonText);
    try {
      if (typeof window === "undefined" || typeof document === "undefined" || !window.URL) {
        setFilterTransferStatus("exported to text buffer");
        return;
      }
      const blob = new Blob([jsonText], { type: "application/json;charset=utf-8" });
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      const ts = new Date().toISOString().replace(/[:.]/g, "-");
      anchor.href = url;
      anchor.download = `graph_lab_filter_presets_${ts}.json`;
      document.body.appendChild(anchor);
      anchor.click();
      document.body.removeChild(anchor);
      window.URL.revokeObjectURL(url);
      setFilterTransferStatus(`exported ${Object.keys(filterPresets).length} preset(s)`);
    } catch (_) {
      setFilterTransferStatus("exported to text buffer (file download unavailable)");
    }
  }, [filterPresets]);
  const copyFilterPresetsJson = React.useCallback(async () => {
    const jsonText = serializeFilterPresetExportBundle(filterPresets);
    setFilterTransferText(jsonText);
    try {
      if (typeof navigator !== "undefined" && navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(jsonText);
        setFilterTransferStatus(`copied ${Object.keys(filterPresets).length} preset(s) to clipboard`);
        return;
      }
      setFilterTransferStatus("clipboard unavailable; copy from text buffer");
    } catch (_) {
      setFilterTransferStatus("clipboard write failed; copy from text buffer");
    }
  }, [filterPresets]);
  const copyFilterImportAuditDetail = React.useCallback(async () => {
    const detailText = String(filterImportAuditDetailText || "");
    if (!detailText.trim()) {
      setFilterTransferStatus("audit copy skipped: empty detail");
      return;
    }
    try {
      if (typeof navigator !== "undefined" && navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(detailText);
        setFilterTransferStatus("audit detail copied to clipboard");
        return;
      }
      setFilterTransferStatus("audit copy failed: clipboard unavailable");
    } catch (_) {
      setFilterTransferStatus("audit copy failed: clipboard write error");
    }
  }, [filterImportAuditDetailText]);
  const exportFilterImportAuditJson = React.useCallback(() => {
    const jsonText = serializeFilterImportAuditExportBundle(filterImportAuditTrail);
    try {
      if (typeof window === "undefined" || typeof document === "undefined" || !window.URL) {
        setFilterTransferStatus("audit export prepared in-memory only");
        return;
      }
      const blob = new Blob([jsonText], { type: "application/json;charset=utf-8" });
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      const ts = new Date().toISOString().replace(/[:.]/g, "-");
      anchor.href = url;
      anchor.download = `graph_lab_filter_import_audit_${ts}.json`;
      document.body.appendChild(anchor);
      anchor.click();
      document.body.removeChild(anchor);
      window.URL.revokeObjectURL(url);
      setFilterTransferStatus(`audit export complete (${filterImportAuditTrail.length} entries)`);
    } catch (_) {
      setFilterTransferStatus("audit export failed");
    }
  }, [filterImportAuditTrail]);
  const exportFilterImportAuditQuickApplyTelemetryJson = React.useCallback(() => {
    const jsonText = serializeFilterImportAuditQuickApplyTelemetryBundle(filterImportAuditQuickApplyTelemetry);
    setFilterTransferText(jsonText);
    try {
      if (typeof window === "undefined" || typeof document === "undefined" || !window.URL) {
        setFilterTransferStatus("quick telemetry export prepared in-memory only");
        return;
      }
      const blob = new Blob([jsonText], { type: "application/json;charset=utf-8" });
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      const ts = new Date().toISOString().replace(/[:.]/g, "-");
      anchor.href = url;
      anchor.download = `graph_lab_filter_import_quick_apply_telemetry_${ts}.json`;
      document.body.appendChild(anchor);
      anchor.click();
      document.body.removeChild(anchor);
      window.URL.revokeObjectURL(url);
      setFilterTransferStatus(`quick telemetry export complete (${filterImportAuditQuickApplyTelemetry.length} entries)`);
    } catch (_) {
      setFilterTransferStatus("quick telemetry export failed");
    }
  }, [filterImportAuditQuickApplyTelemetry]);
  const copyFilterImportAuditQuickApplyTelemetryJson = React.useCallback(async () => {
    const jsonText = serializeFilterImportAuditQuickApplyTelemetryBundle(filterImportAuditQuickApplyTelemetry);
    setFilterTransferText(jsonText);
    try {
      if (typeof navigator !== "undefined" && navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(jsonText);
        setFilterTransferStatus(`quick telemetry copied (${filterImportAuditQuickApplyTelemetry.length} entries)`);
        return;
      }
      setFilterTransferStatus("quick telemetry copy failed: clipboard unavailable");
    } catch (_) {
      setFilterTransferStatus("quick telemetry copy failed: clipboard write error");
    }
  }, [filterImportAuditQuickApplyTelemetry]);
  const clearFilterImportAuditQuickApplyTelemetry = React.useCallback(() => {
    setFilterImportAuditQuickApplyTelemetry([]);
    setFilterTransferStatus("quick telemetry cleared");
  }, []);
  const applyFilterImportAuditQuickTelemetryDrilldownPreset = React.useCallback((presetId) => {
    const preset = resolveFilterImportAuditQuickDrilldownPreset(presetId);
    setFilterImportAuditQuickTelemetryFailureOnlyChecked(Boolean(preset.failure_only));
    setFilterImportAuditQuickTelemetryReasonQuery(
      String(preset.reason_query || "").slice(0, FILTER_IMPORT_AUDIT_QUICK_REASON_QUERY_MAX)
    );
    setFilterTransferStatus(`quick telemetry drilldown preset: ${String(preset.id || "all")}`);
  }, []);
  const clearFilterImportAuditQuickTelemetryDrilldown = React.useCallback(() => {
    setFilterImportAuditQuickTelemetryFailureOnlyChecked(false);
    setFilterImportAuditQuickTelemetryReasonQuery("");
    setFilterTransferStatus("quick telemetry drilldown reset");
  }, []);
  const applyFilterImportAuditQuickTelemetryReasonChip = React.useCallback((reason) => {
    const nextReason = String(reason || "").trim().slice(0, FILTER_IMPORT_AUDIT_QUICK_REASON_QUERY_MAX);
    if (!nextReason) return;
    setFilterImportAuditQuickTelemetryFailureOnlyChecked(true);
    setFilterImportAuditQuickTelemetryReasonQuery(nextReason);
    setFilterTransferStatus(`quick telemetry reason focus: ${nextReason}`);
  }, []);
  const exportFilterImportAuditQuickTelemetryDrilldownJson = React.useCallback(() => {
    const jsonText = serializeFilterImportAuditQuickTelemetryDrilldownBundle(
      filterImportAuditQuickTelemetryRowsDrilldown,
      {
        preset_id: activeFilterImportAuditQuickTelemetryDrilldownPresetId,
        failure_only: filterImportAuditQuickTelemetryFailureOnlyChecked,
        reason_query: filterImportAuditQuickTelemetryReasonQueryNormalized,
      }
    );
    setFilterTransferText(jsonText);
    try {
      if (typeof window === "undefined" || typeof document === "undefined" || !window.URL) {
        setFilterTransferStatus("quick telemetry drilldown export prepared in-memory only");
        return;
      }
      const blob = new Blob([jsonText], { type: "application/json;charset=utf-8" });
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      const ts = new Date().toISOString().replace(/[:.]/g, "-");
      anchor.href = url;
      anchor.download = `graph_lab_filter_import_quick_apply_telemetry_drilldown_${ts}.json`;
      document.body.appendChild(anchor);
      anchor.click();
      document.body.removeChild(anchor);
      window.URL.revokeObjectURL(url);
      setFilterTransferStatus(`quick telemetry drilldown export complete (${filterImportAuditQuickTelemetryRowsDrilldown.length} entries)`);
    } catch (_) {
      setFilterTransferStatus("quick telemetry drilldown export failed");
    }
  }, [
    activeFilterImportAuditQuickTelemetryDrilldownPresetId,
    filterImportAuditQuickTelemetryFailureOnlyChecked,
    filterImportAuditQuickTelemetryReasonQueryNormalized,
    filterImportAuditQuickTelemetryRowsDrilldown,
  ]);
  const copyFilterImportAuditQuickTelemetryDrilldownJson = React.useCallback(async () => {
    const jsonText = serializeFilterImportAuditQuickTelemetryDrilldownBundle(
      filterImportAuditQuickTelemetryRowsDrilldown,
      {
        preset_id: activeFilterImportAuditQuickTelemetryDrilldownPresetId,
        failure_only: filterImportAuditQuickTelemetryFailureOnlyChecked,
        reason_query: filterImportAuditQuickTelemetryReasonQueryNormalized,
      }
    );
    setFilterTransferText(jsonText);
    try {
      if (typeof navigator !== "undefined" && navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(jsonText);
        setFilterTransferStatus(`quick telemetry drilldown copied (${filterImportAuditQuickTelemetryRowsDrilldown.length} entries)`);
        return;
      }
      setFilterTransferStatus("quick telemetry drilldown copy failed: clipboard unavailable");
    } catch (_) {
      setFilterTransferStatus("quick telemetry drilldown copy failed: clipboard write error");
    }
  }, [
    activeFilterImportAuditQuickTelemetryDrilldownPresetId,
    filterImportAuditQuickTelemetryFailureOnlyChecked,
    filterImportAuditQuickTelemetryReasonQueryNormalized,
    filterImportAuditQuickTelemetryRowsDrilldown,
  ]);
  const copyFilterImportAuditDeepLinkBundle = React.useCallback(async () => {
    const bundleText = serializeFilterImportAuditDeepLinkBundle({
      activeEntry: activeFilterImportAuditEntry,
      visibleEntries: filterImportAuditRowsVisible,
      trailCount: filterImportAuditTrail.length,
      filteredCount: filterImportAuditRowsFiltered.length,
      visibleCount: filterImportAuditRowsVisible.length,
      activePresetId: activeFilterImportAuditQueryPresetId,
      pinnedPresetId: filterImportAuditPinnedPresetId,
      query: {
        search: filterImportAuditSearchText,
        kind: filterImportAuditKindFilter,
        mode: filterImportAuditModeFilter,
      },
      paging: {
        offset: filterImportAuditRowOffset,
        cap: filterImportAuditRowCap,
        end: filterImportAuditRowEnd,
      },
    });
    setFilterTransferText(bundleText);
    try {
      if (typeof navigator !== "undefined" && navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(bundleText);
        setFilterTransferStatus("audit deep-link bundle copied to clipboard");
        return;
      }
      setFilterTransferStatus("audit deep-link bundle prepared in text buffer");
    } catch (_) {
      setFilterTransferStatus("audit deep-link bundle copy failed");
    }
  }, [
    activeFilterImportAuditEntry,
    activeFilterImportAuditQueryPresetId,
    filterImportAuditKindFilter,
    filterImportAuditModeFilter,
    filterImportAuditPinnedPresetId,
    filterImportAuditRowCap,
    filterImportAuditRowEnd,
    filterImportAuditRowOffset,
    filterImportAuditRowsFiltered.length,
    filterImportAuditRowsVisible,
    filterImportAuditSearchText,
    filterImportAuditTrail.length,
  ]);
  const applyFilterImportAuditDeepLinkBundleWithScopes = React.useCallback((scopeConfig, restoreTag) => {
    const normalizedRestoreTag = String(restoreTag || "custom").trim() || "custom";
    if (parsedFilterImportAuditDeepLinkPayload.empty) {
      setFilterTransferStatus("audit bundle apply failed: empty import payload");
      return {
        ok: false,
        reason: "empty_payload",
        restore_tag: normalizedRestoreTag,
        schema_version: 0,
        applied_scopes: [],
      };
    }
    if (parsedFilterImportAuditDeepLinkPayload.error) {
      setFilterTransferStatus(`audit bundle apply failed: ${parsedFilterImportAuditDeepLinkPayload.error}`);
      return {
        ok: false,
        reason: "parse_error",
        restore_tag: normalizedRestoreTag,
        schema_version: 0,
        applied_scopes: [],
      };
    }
    const bundle = parsedFilterImportAuditDeepLinkPayload.bundle;
    if (!bundle || typeof bundle !== "object") {
      setFilterTransferStatus("audit bundle apply failed: invalid payload");
      return {
        ok: false,
        reason: "invalid_payload",
        restore_tag: normalizedRestoreTag,
        schema_version: 0,
        applied_scopes: [],
      };
    }
    const query = bundle.query && typeof bundle.query === "object" ? bundle.query : {};
    const paging = bundle.paging && typeof bundle.paging === "object" ? bundle.paging : {};
    const appliedScopes = [];
    const scope = scopeConfig && typeof scopeConfig === "object" ? scopeConfig : {};
    const shouldQuery = Boolean(scope.query);
    const shouldPaging = Boolean(scope.paging);
    const shouldPinned = Boolean(scope.pinned);
    const shouldEntry = Boolean(scope.entry);
    if (shouldQuery) {
      setFilterImportAuditSearchText(String(query.search || ""));
      setFilterImportAuditKindFilter(String(query.kind || "all"));
      setFilterImportAuditModeFilter(String(query.mode || "all"));
      appliedScopes.push("query");
    }
    if (shouldPaging) {
      setFilterImportAuditRowCapText(String(paging.cap || CONTRACT_OVERLAY_DEFAULT_PREFS.filterImportAuditRowCap));
      setFilterImportAuditRowOffset(clampInteger(paging.offset, 0, 1_000_000, 0));
      appliedScopes.push("paging");
    }
    if (shouldPinned) {
      setFilterImportAuditPinnedPresetId(String(bundle.pinned_preset_id || ""));
      appliedScopes.push("pinned");
    }
    if (shouldEntry) {
      const activeEntryId = String(bundle.active_entry_id || "").trim();
      if (activeEntryId) {
        setActiveFilterImportAuditId(activeEntryId);
      }
      appliedScopes.push("entry");
    }
    if (appliedScopes.length === 0) {
      setFilterTransferStatus("audit bundle apply skipped: no restore scope enabled");
      return {
        ok: false,
        reason: "no_scope_enabled",
        restore_tag: normalizedRestoreTag,
        schema_version: Number(bundle.schema_version || 0),
        applied_scopes: [],
      };
    }
    setFilterTransferStatus(
      `audit deep-link bundle applied (schema:${Number(bundle.schema_version || 0)}, scope:${appliedScopes.join("/")}, restore:${normalizedRestoreTag})`
    );
    return {
      ok: true,
      reason: "applied",
      restore_tag: normalizedRestoreTag,
      schema_version: Number(bundle.schema_version || 0),
      applied_scopes: [...appliedScopes],
    };
  }, [parsedFilterImportAuditDeepLinkPayload]);
  const applyFilterImportAuditDeepLinkBundleFromText = React.useCallback(() => {
    applyFilterImportAuditDeepLinkBundleWithScopes({
      query: filterImportAuditRestoreQueryChecked,
      paging: filterImportAuditRestorePagingChecked,
      pinned: filterImportAuditRestorePinnedPresetChecked,
      entry: filterImportAuditRestoreActiveEntryChecked,
    }, activeFilterImportAuditRestorePresetId);
  }, [
    activeFilterImportAuditRestorePresetId,
    applyFilterImportAuditDeepLinkBundleWithScopes,
    filterImportAuditRestoreActiveEntryChecked,
    filterImportAuditRestorePagingChecked,
    filterImportAuditRestorePinnedPresetChecked,
    filterImportAuditRestoreQueryChecked,
  ]);
  const applyFilterImportAuditDeepLinkQuickScope = React.useCallback((optionId) => {
    const option = resolveFilterImportAuditQuickApplyOption(optionId);
    const scopeConfig = {
      query: Boolean(option.query),
      paging: Boolean(option.paging),
      pinned: Boolean(option.pinned),
      entry: Boolean(option.entry),
    };
    const result = applyFilterImportAuditDeepLinkBundleWithScopes(
      scopeConfig,
      `quick:${String(option.id || "all")}`
    );
    const telemetryEntry = normalizeFilterImportAuditQuickApplyTelemetryEntry({
      id: `fiq_${Date.now()}_${Math.random().toString(16).slice(2, 8)}`,
      timestamp_iso: new Date().toISOString(),
      option_id: String(option.id || ""),
      restore_tag: String(result?.restore_tag || ""),
      apply_ok: Boolean(result?.ok),
      apply_reason: String(result?.reason || "unknown"),
      schema_version: Number(result?.schema_version || 0),
      scope: scopeConfig,
      sync_enabled: Boolean(filterImportAuditQuickApplySyncRestoreChecked),
      sync_applied: Boolean(filterImportAuditQuickApplySyncRestoreChecked && result?.ok),
      active_restore_preset_id: activeFilterImportAuditRestorePresetId,
      active_query_preset_id: activeFilterImportAuditQueryPresetId,
      pinned_preset_id: filterImportAuditPinnedPresetId,
    }, 0);
    if (telemetryEntry) {
      setFilterImportAuditQuickApplyTelemetry((prev) => [
        telemetryEntry,
        ...(Array.isArray(prev) ? prev : []),
      ].slice(0, FILTER_IMPORT_AUDIT_QUICK_TELEMETRY_LIMIT));
    }
    if (!result?.ok) return;
    if (!filterImportAuditQuickApplySyncRestoreChecked) return;
    setFilterImportAuditRestoreQueryChecked(Boolean(option.query));
    setFilterImportAuditRestorePagingChecked(Boolean(option.paging));
    setFilterImportAuditRestorePinnedPresetChecked(Boolean(option.pinned));
    setFilterImportAuditRestoreActiveEntryChecked(Boolean(option.entry));
    setFilterImportAuditResetArmedChecked(false);
    setFilterImportAuditResetArmedAtMs(0);
  }, [
    activeFilterImportAuditQueryPresetId,
    activeFilterImportAuditRestorePresetId,
    applyFilterImportAuditDeepLinkBundleWithScopes,
    filterImportAuditPinnedPresetId,
    filterImportAuditQuickApplySyncRestoreChecked,
  ]);
  const resetFilterImportAuditRestoreScope = React.useCallback(() => {
    if (!filterImportAuditResetArmedChecked) {
      setFilterTransferStatus("reset blocked: arm reset first (safe window required)");
      return;
    }
    setFilterImportAuditRestoreQueryChecked(Boolean(CONTRACT_OVERLAY_DEFAULT_PREFS.filterImportAuditRestoreQuery));
    setFilterImportAuditRestorePagingChecked(Boolean(CONTRACT_OVERLAY_DEFAULT_PREFS.filterImportAuditRestorePaging));
    setFilterImportAuditRestorePinnedPresetChecked(Boolean(CONTRACT_OVERLAY_DEFAULT_PREFS.filterImportAuditRestorePinnedPreset));
    setFilterImportAuditRestoreActiveEntryChecked(Boolean(CONTRACT_OVERLAY_DEFAULT_PREFS.filterImportAuditRestoreActiveEntry));
    setFilterImportAuditResetArmedChecked(false);
    setFilterImportAuditResetArmedAtMs(0);
    setFilterImportAuditResetTickMs(0);
    setFilterTransferStatus("audit restore scope reset (safe reset consumed)");
  }, [filterImportAuditResetArmedChecked]);
  const resetFilterImportAuditPinContext = React.useCallback(() => {
    if (!filterImportAuditResetArmedChecked) {
      setFilterTransferStatus("reset blocked: arm reset first (safe window required)");
      return;
    }
    setFilterImportAuditPinnedPresetId(String(CONTRACT_OVERLAY_DEFAULT_PREFS.filterImportAuditPinnedPreset || ""));
    setFilterImportAuditPinChipFilter(
      normalizeFilterImportAuditPinChipFilter(CONTRACT_OVERLAY_DEFAULT_PREFS.filterImportAuditPinChipFilter)
    );
    setFilterImportAuditResetArmedChecked(false);
    setFilterImportAuditResetArmedAtMs(0);
    setFilterImportAuditResetTickMs(0);
    setFilterTransferStatus("audit pin context reset (safe reset consumed)");
  }, [filterImportAuditResetArmedChecked]);
  const resetFilterImportAuditOperatorContext = React.useCallback(() => {
    if (!filterImportAuditResetArmedChecked) {
      setFilterTransferStatus("reset blocked: arm reset first (safe window required)");
      return;
    }
    setFilterImportAuditRestoreQueryChecked(Boolean(CONTRACT_OVERLAY_DEFAULT_PREFS.filterImportAuditRestoreQuery));
    setFilterImportAuditRestorePagingChecked(Boolean(CONTRACT_OVERLAY_DEFAULT_PREFS.filterImportAuditRestorePaging));
    setFilterImportAuditRestorePinnedPresetChecked(Boolean(CONTRACT_OVERLAY_DEFAULT_PREFS.filterImportAuditRestorePinnedPreset));
    setFilterImportAuditRestoreActiveEntryChecked(Boolean(CONTRACT_OVERLAY_DEFAULT_PREFS.filterImportAuditRestoreActiveEntry));
    setFilterImportAuditPinnedPresetId(String(CONTRACT_OVERLAY_DEFAULT_PREFS.filterImportAuditPinnedPreset || ""));
    setFilterImportAuditPinChipFilter(
      normalizeFilterImportAuditPinChipFilter(CONTRACT_OVERLAY_DEFAULT_PREFS.filterImportAuditPinChipFilter)
    );
    setFilterImportAuditQuickApplySyncRestoreChecked(
      Boolean(CONTRACT_OVERLAY_DEFAULT_PREFS.filterImportAuditQuickApplySyncRestore)
    );
    setFilterImportAuditResetArmedChecked(false);
    setFilterImportAuditResetArmedAtMs(0);
    setFilterImportAuditResetTickMs(0);
    setFilterTransferStatus("audit operator context reset (safe reset consumed)");
  }, [filterImportAuditResetArmedChecked]);
  const applyFilterImportAuditRestorePreset = React.useCallback((presetId) => {
    const preset = resolveFilterImportAuditRestorePreset(presetId);
    setFilterImportAuditRestoreQueryChecked(Boolean(preset.query));
    setFilterImportAuditRestorePagingChecked(Boolean(preset.paging));
    setFilterImportAuditRestorePinnedPresetChecked(Boolean(preset.pinned));
    setFilterImportAuditRestoreActiveEntryChecked(Boolean(preset.entry));
    setFilterTransferStatus(`audit restore preset: ${String(preset.id || "all")}`);
  }, []);
  const applyFilterImportAuditQueryPreset = React.useCallback((presetId) => {
    const pid = String(presetId || "").trim();
    const preset = resolveFilterImportAuditQueryPreset(pid);
    setFilterImportAuditSearchText(String(preset?.search || ""));
    setFilterImportAuditKindFilter(String(preset?.kind || "all"));
    setFilterImportAuditModeFilter(String(preset?.mode || "all"));
    setFilterImportAuditRowOffset(0);
    setFilterTransferStatus(`audit query preset: ${String(preset?.id || "all")}`);
  }, []);
  const toggleFilterImportAuditPinnedPreset = React.useCallback(() => {
    if (filterImportAuditPinnedPresetActive) {
      setFilterImportAuditPinnedPresetId("");
      setFilterTransferStatus("audit query preset unpinned");
      return;
    }
    if (!filterImportAuditPresetPinnable) {
      setFilterTransferStatus("audit preset pin skipped: custom query");
      return;
    }
    const next = String(activeFilterImportAuditQueryPresetId || "all");
    setFilterImportAuditPinnedPresetId(next);
    setFilterTransferStatus(`audit query preset pinned: ${next}`);
  }, [
    activeFilterImportAuditQueryPresetId,
    filterImportAuditPinnedPresetActive,
    filterImportAuditPresetPinnable,
  ]);
  const resetFilterImportAuditQuery = React.useCallback(() => {
    const preset = resolveFilterImportAuditQueryPreset(filterImportAuditPinnedPresetId || "all");
    setFilterImportAuditSearchText(String(preset?.search || ""));
    setFilterImportAuditKindFilter(String(preset?.kind || "all"));
    setFilterImportAuditModeFilter(String(preset?.mode || "all"));
    setFilterImportAuditRowOffset(0);
    if (filterImportAuditPinnedPresetId) {
      setFilterTransferStatus(`audit query reset -> pinned:${filterImportAuditPinnedPresetId}`);
      return;
    }
    setFilterTransferStatus("audit query reset");
  }, [filterImportAuditPinnedPresetId]);
  const clearFilterImportHistory = React.useCallback(() => {
    setFilterImportUndoStack([]);
    setFilterImportRedoStack([]);
    setFilterImportAuditTrail([]);
    setActiveFilterImportAuditId("");
    setFilterImportAuditRowOffset(0);
    setFilterTransferStatus("import history cleared");
  }, []);
  const pruneFilterImportHistory = React.useCallback(() => {
    const keep = clampInteger(filterImportHistoryKeepText, 1, FILTER_IMPORT_HISTORY_LIMIT, 8);
    setFilterImportHistoryKeepText(String(keep));
    setFilterImportUndoStack((prev) => {
      const rows = Array.isArray(prev) ? prev : [];
      return rows.slice(-keep);
    });
    setFilterImportRedoStack((prev) => {
      const rows = Array.isArray(prev) ? prev : [];
      return rows.slice(-keep);
    });
    setFilterImportAuditTrail((prev) => {
      const rows = Array.isArray(prev) ? prev : [];
      return rows.slice(0, keep);
    });
    setFilterTransferStatus(`import history pruned to ${keep}`);
  }, [filterImportHistoryKeepText]);
  const restoreFilterPresetSnapshot = React.useCallback((snapshot) => {
    const row = snapshot && typeof snapshot === "object" ? snapshot : null;
    if (!row || !row.presets || typeof row.presets !== "object") return false;
    const restored = cloneNormalizedFilterPresets(row.presets);
    setFilterPresets(restored);
    setActiveFilterPreset(String(row.activeFilterPreset || "default"));
    setFilterPresetDraft(
      String(row.filterPresetDraft || CONTRACT_OVERLAY_DEFAULT_PREFS.filterPresetDraft)
    );
    return true;
  }, []);
  const undoLastFilterImport = React.useCallback(() => {
    const stack = Array.isArray(filterImportUndoStack) ? filterImportUndoStack : [];
    if (stack.length === 0) {
      setFilterTransferStatus("undo skipped: no snapshot");
      return;
    }
    const snapshot = stack[stack.length - 1];
    const currentSnapshot = buildFilterPresetStateSnapshot(
      filterPresets,
      activeFilterPreset,
      filterPresetDraft
    );
    const ok = restoreFilterPresetSnapshot(snapshot);
    if (!ok) {
      setFilterTransferStatus("undo failed: invalid snapshot");
      return;
    }
    setFilterImportUndoStack((prev) => prev.slice(0, -1));
    setFilterImportRedoStack((prev) => [...prev, currentSnapshot].slice(-FILTER_IMPORT_HISTORY_LIMIT));
    const auditEntry = {
      id: `fia_${Date.now()}_${Math.random().toString(16).slice(2, 8)}`,
      kind: "undo",
      timestamp_iso: new Date().toISOString(),
      mode: "undo",
      selected_count: 0,
      added_count: 0,
      changed_count: 0,
      removed_count: 0,
      note: `restored ${String(snapshot.captured_at_iso || "-")}`,
      selected_names: [],
      added_names: [],
      removed_names: [],
    };
    setFilterImportAuditTrail((prev) => [
      auditEntry,
      ...prev,
    ].slice(0, FILTER_IMPORT_HISTORY_LIMIT));
    setActiveFilterImportAuditId(String(auditEntry.id));
    setFilterReplaceConfirmChecked(false);
    setFilterTransferStatus(`undo restored snapshot (${String(snapshot.captured_at_iso || "-")})`);
  }, [
    activeFilterPreset,
    filterImportUndoStack,
    filterPresetDraft,
    filterPresets,
    restoreFilterPresetSnapshot,
  ]);
  const redoLastFilterImport = React.useCallback(() => {
    const stack = Array.isArray(filterImportRedoStack) ? filterImportRedoStack : [];
    if (stack.length === 0) {
      setFilterTransferStatus("redo skipped: no snapshot");
      return;
    }
    const snapshot = stack[stack.length - 1];
    const currentSnapshot = buildFilterPresetStateSnapshot(
      filterPresets,
      activeFilterPreset,
      filterPresetDraft
    );
    const ok = restoreFilterPresetSnapshot(snapshot);
    if (!ok) {
      setFilterTransferStatus("redo failed: invalid snapshot");
      return;
    }
    setFilterImportRedoStack((prev) => prev.slice(0, -1));
    setFilterImportUndoStack((prev) => [...prev, currentSnapshot].slice(-FILTER_IMPORT_HISTORY_LIMIT));
    const auditEntry = {
      id: `fia_${Date.now()}_${Math.random().toString(16).slice(2, 8)}`,
      kind: "redo",
      timestamp_iso: new Date().toISOString(),
      mode: "redo",
      selected_count: 0,
      added_count: 0,
      changed_count: 0,
      removed_count: 0,
      note: `restored ${String(snapshot.captured_at_iso || "-")}`,
      selected_names: [],
      added_names: [],
      removed_names: [],
    };
    setFilterImportAuditTrail((prev) => [
      auditEntry,
      ...prev,
    ].slice(0, FILTER_IMPORT_HISTORY_LIMIT));
    setActiveFilterImportAuditId(String(auditEntry.id));
    setFilterReplaceConfirmChecked(false);
    setFilterTransferStatus(`redo restored snapshot (${String(snapshot.captured_at_iso || "-")})`);
  }, [
    activeFilterPreset,
    filterImportRedoStack,
    filterPresetDraft,
    filterPresets,
    restoreFilterPresetSnapshot,
  ]);
  const importFilterPresetsFromText = React.useCallback(() => {
    if (parsedFilterImportPayload.empty) {
      setFilterTransferStatus("import failed: empty import payload");
      return;
    }
    if (parsedFilterImportPayload.error) {
      setFilterTransferStatus(`import failed: ${parsedFilterImportPayload.error}`);
      return;
    }
    const importedAll = parsedFilterImportPayload.imported;
    if (!importedAll || typeof importedAll !== "object") {
      setFilterTransferStatus("import failed: invalid payload");
      return;
    }
    const names = selectedFilterImportNames.filter((name) =>
      Object.prototype.hasOwnProperty.call(importedAll, name)
    );
    if (names.length === 0) {
      setFilterTransferStatus("import skipped: no presets selected");
      return;
    }
    if (filterImportMode === "replace_custom" && !filterReplaceConfirmChecked) {
      setFilterTransferStatus("confirm required: enable replace confirmation for replace custom");
      return;
    }
    const imported = {};
    names.forEach((name) => {
      const fallback = DEFAULT_FILTER_PRESETS[name] || DEFAULT_FILTER_PRESETS.default;
      imported[name] = normalizeFilterPresetConfig(importedAll[name], fallback);
    });
    const beforeSnapshot = buildFilterPresetStateSnapshot(
      filterPresets,
      activeFilterPreset,
      filterPresetDraft
    );
    const beforePresets = beforeSnapshot.presets;
    let afterPresets = {};
    if (filterImportMode !== "replace_custom") {
      afterPresets = {
        ...beforePresets,
        ...imported,
      };
    } else {
      const keptBuiltins = {};
      Object.keys(beforePresets).forEach((name) => {
        if (!Object.prototype.hasOwnProperty.call(DEFAULT_FILTER_PRESETS, name)) return;
        const fallback = DEFAULT_FILTER_PRESETS[name] || DEFAULT_FILTER_PRESETS.default;
        keptBuiltins[name] = normalizeFilterPresetConfig(beforePresets[name], fallback);
      });
      afterPresets = {
        ...keptBuiltins,
        ...imported,
      };
    }
    const beforeNames = Object.keys(beforePresets);
    const afterNames = Object.keys(afterPresets);
    const beforeSet = new Set(beforeNames);
    const afterSet = new Set(afterNames);
    const addedNames = afterNames.filter((name) => !beforeSet.has(name));
    const removedNames = beforeNames.filter((name) => !afterSet.has(name));
    const changedNames = afterNames.filter((name) => {
      if (!beforeSet.has(name)) return false;
      const a = JSON.stringify(beforePresets[name] || {});
      const b = JSON.stringify(afterPresets[name] || {});
      return a !== b;
    });
    const selectedSet = new Set(names);
    let selectedNewCount = 0;
    let selectedOverwriteBuiltinCount = 0;
    let selectedOverwriteCustomCount = 0;
    filterImportRows.forEach((row) => {
      const name = String(row?.name || "");
      if (!selectedSet.has(name)) return;
      if (row.conflict === "new") selectedNewCount += 1;
      if (row.conflict === "overwrite_builtin") selectedOverwriteBuiltinCount += 1;
      if (row.conflict === "overwrite_custom") selectedOverwriteCustomCount += 1;
    });
    const timestampIso = new Date().toISOString();
    const auditEntry = {
      id: `fia_${Date.now()}_${Math.random().toString(16).slice(2, 8)}`,
      kind: "import",
      timestamp_iso: timestampIso,
      mode: filterImportMode,
      selected_count: names.length,
      added_count: addedNames.length,
      changed_count: changedNames.length,
      removed_count: removedNames.length,
      new_count: selectedNewCount,
      overwrite_builtin_count: selectedOverwriteBuiltinCount,
      overwrite_custom_count: selectedOverwriteCustomCount,
      selected_names: [...names],
      added_names: [...addedNames],
      removed_names: [...removedNames],
      note: filterImportMode === "replace_custom" ? "replace custom apply" : "merge apply",
    };
    setFilterImportUndoStack((prev) => [...prev, beforeSnapshot].slice(-FILTER_IMPORT_HISTORY_LIMIT));
    setFilterImportRedoStack([]);
    setFilterImportAuditTrail((prev) => [auditEntry, ...prev].slice(0, FILTER_IMPORT_HISTORY_LIMIT));
    setActiveFilterImportAuditId(String(auditEntry.id));
    setFilterPresets(afterPresets);
    if (filterImportMode === "replace_custom") {
      setFilterTransferStatus(
        `imported ${names.length} preset(s); +${addedNames.length}/~${changedNames.length}/-${removedNames.length} (replace custom)`
      );
    } else {
      setFilterTransferStatus(
        `imported ${names.length} preset(s); +${addedNames.length}/~${changedNames.length}/-${removedNames.length}`
      );
    }
    const firstImported = String(names[0] || "");
    if (firstImported) {
      setFilterPresetDraft(firstImported);
      setActiveFilterPreset(firstImported);
    }
    setFilterReplaceConfirmChecked(false);
  }, [
    activeFilterPreset,
    filterImportMode,
    filterImportRows,
    filterPresetDraft,
    filterPresets,
    filterReplaceConfirmChecked,
    parsedFilterImportPayload.empty,
    parsedFilterImportPayload.error,
    parsedFilterImportPayload.imported,
    selectedFilterImportNames,
  ]);
  const resetOverlayFilters = React.useCallback(() => {
    setSourceFilter(CONTRACT_OVERLAY_DEFAULT_PREFS.sourceFilter);
    setSeverityFilter(CONTRACT_OVERLAY_DEFAULT_PREFS.severityFilter);
    setPolicyFilter(CONTRACT_OVERLAY_DEFAULT_PREFS.policyFilter);
    setPinnedRunId(CONTRACT_OVERLAY_DEFAULT_PREFS.pinnedRunId);
    setNonZeroOnly(Boolean(CONTRACT_OVERLAY_DEFAULT_PREFS.nonZeroOnly));
    setGateHistoryLimit(String(CONTRACT_OVERLAY_DEFAULT_PREFS.gateHistoryLimit));
    setGateHistoryPages(String(CONTRACT_OVERLAY_DEFAULT_PREFS.gateHistoryPages));
    setRowWindowSizeText(String(CONTRACT_OVERLAY_DEFAULT_PREFS.rowWindowSize));
    setRowVolumeGuardBypass(Boolean(CONTRACT_OVERLAY_DEFAULT_PREFS.rowVolumeGuardBypass));
    setRowWindowOffset(0);
  }, []);
  const activeFilterTokens = React.useMemo(() => {
    const tokens = [];
    if (sourceFilter !== CONTRACT_OVERLAY_DEFAULT_PREFS.sourceFilter) {
      tokens.push(`source:${sourceFilter}`);
    }
    if (severityFilter !== CONTRACT_OVERLAY_DEFAULT_PREFS.severityFilter) {
      tokens.push(`severity:${severityFilter}`);
    }
    if (policyFilter !== CONTRACT_OVERLAY_DEFAULT_PREFS.policyFilter) {
      tokens.push(`policy:${policyFilter}`);
    }
    if (pinnedRunId !== CONTRACT_OVERLAY_DEFAULT_PREFS.pinnedRunId) {
      tokens.push(`run:${pinnedRunId}`);
    }
    if (Boolean(nonZeroOnly) !== Boolean(CONTRACT_OVERLAY_DEFAULT_PREFS.nonZeroOnly)) {
      tokens.push("delta!=0");
    }
    if (String(gateHistoryLimit) !== String(CONTRACT_OVERLAY_DEFAULT_PREFS.gateHistoryLimit)) {
      tokens.push(`gate_window:${gateHistoryLimit}`);
    }
    if (String(gateHistoryPages) !== String(CONTRACT_OVERLAY_DEFAULT_PREFS.gateHistoryPages)) {
      tokens.push(`gate_pages:${gateHistoryPages}`);
    }
    if (String(rowWindowSizeText) !== String(CONTRACT_OVERLAY_DEFAULT_PREFS.rowWindowSize)) {
      tokens.push(`rows_window:${rowWindowSizeText}`);
    }
    if (Boolean(rowVolumeGuardBypass) !== Boolean(CONTRACT_OVERLAY_DEFAULT_PREFS.rowVolumeGuardBypass)) {
      tokens.push("rows_guard:off");
    }
    return tokens;
  }, [
    gateHistoryLimit,
    gateHistoryPages,
    nonZeroOnly,
    pinnedRunId,
    policyFilter,
    rowVolumeGuardBypass,
    rowWindowSizeText,
    severityFilter,
    sourceFilter,
  ]);
  const triggerShortcutAction = React.useCallback((actionId) => {
    const id = String(actionId || "");
    if (id === "toggle_help") {
      setShowShortcutHelp((x) => !x);
      return true;
    }
    if (id === "toggle_compact") {
      setCompactMode((x) => !x);
      return true;
    }
    if (id === "toggle_nonzero") {
      setNonZeroOnly((x) => !x);
      return true;
    }
    if (id === "row_top") {
      setRowWindowOffset(0);
      return true;
    }
    if (id === "row_next") {
      setRowWindowOffset((prev) => Math.min(maxRowWindowOffset, Number(prev || 0) + rowWindowSize));
      return true;
    }
    if (id === "row_prev") {
      setRowWindowOffset((prev) => Math.max(0, Number(prev || 0) - rowWindowSize));
      return true;
    }
    if (id === "preset_triage") {
      applyOverlayPreset("triage");
      return true;
    }
    if (id === "preset_deep") {
      applyOverlayPreset("deep_gate");
      return true;
    }
    if (id === "preset_reset") {
      applyOverlayPreset("reset_all");
      return true;
    }
    if (id === "audit_pin_toggle") {
      toggleFilterImportAuditPinnedPreset();
      return true;
    }
    if (id === "expand_visible") {
      expandVisibleDetails();
      return true;
    }
    if (id === "collapse_details") {
      collapseAllDetails();
      return true;
    }
    return false;
  }, [
    applyOverlayPreset,
    collapseAllDetails,
    expandVisibleDetails,
    maxRowWindowOffset,
    rowWindowSize,
    toggleFilterImportAuditPinnedPreset,
  ]);
  React.useEffect(() => {
    const onKeyDown = (evt) => {
      if (!evt || evt.defaultPrevented) return;
      if (evt.metaKey || evt.ctrlKey || evt.altKey) return;
      if (isEditableElementTarget(evt.target)) return;
      const key = normalizeShortcutToken(evt.key);
      if (!key) return;
      const actionId = shortcutActionByKey.get(key);
      if (!actionId) return;
      evt.preventDefault();
      triggerShortcutAction(actionId);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [
    shortcutActionByKey,
    triggerShortcutAction,
  ]);
  const policyByRun = React.useMemo(() => {
    const map = new Map();
    rows.forEach((row) => {
      const runId = String(row?.graph_run_id || "").trim();
      if (!runId) return;
      const note = row?.note && typeof row.note === "object" ? row.note : {};
      if (typeof note.gate_failed !== "boolean") return;
      const previous = map.get(runId) || null;
      const candidate = {
        gate_failed: Boolean(note.gate_failed),
        failure_count: Number(note.failure_count || 0),
        failure_rules: Array.isArray(note.failure_rules) ? note.failure_rules.slice(0, 3) : [],
        policy_eval_id: String(note.policy_eval_id || "-"),
        recommendation: String(note.recommendation || "-"),
        baseline_id: String(note.baseline_id || "-"),
      };
      if (!previous) {
        map.set(runId, candidate);
        return;
      }
      const prevScore = Number(previous.failure_count || 0);
      const nextScore = Number(candidate.failure_count || 0);
      if (nextScore >= prevScore) {
        map.set(runId, candidate);
      }
    });
    return map;
  }, [rows]);
  return h("aside", { className: "contract-overlay", key: "contract_overlay" }, [
    h("div", { className: "contract-overlay-hd", key: "co_hd" }, [
      h("div", { key: "co_t" }, `Contract Timeline (${rows.length})`),
      h("div", { className: "contract-overlay-actions", key: "co_actions" }, [
        h("button", {
          className: "btn",
          onClick: () => setCompactMode((x) => !x),
          key: "co_compact",
        }, compactMode ? "Compact: on" : "Compact: off"),
        h("button", {
          className: "btn",
          onClick: () => applyOverlayPreset("triage"),
          key: "co_preset_triage",
        }, "Preset: Triage"),
        h("button", {
          className: "btn",
          onClick: () => applyOverlayPreset("deep_gate"),
          key: "co_preset_deep",
        }, "Preset: Deep"),
        h("button", {
          className: "btn",
          onClick: () => applyOverlayPreset("reset_all"),
          key: "co_preset_reset",
        }, "Reset Preset"),
        h("button", {
          className: "btn",
          onClick: () => setShowShortcutHelp((x) => !x),
          key: "co_shortcuts_toggle",
        }, showShortcutHelp ? "Shortcuts: on" : "Shortcuts: off"),
        h("button", {
          className: "btn",
          onClick: expandVisibleDetails,
          key: "co_expand_visible",
          disabled: visibleRows.length === 0,
        }, "Expand Visible"),
        h("button", {
          className: "btn",
          onClick: collapseAllDetails,
          key: "co_collapse_details",
          disabled: expandedRowKeys.size === 0,
        }, "Collapse Details"),
        h("button", {
          className: "btn",
          onClick: copyVisibleDetailRows,
          key: "co_copy_visible_details",
          disabled: visibleRows.length === 0,
        }, "Copy Visible"),
        h("button", { className: "btn", onClick: onExport, key: "co_export" }, "Export JSON"),
        h("button", { className: "btn", onClick: onClear, key: "co_clear" }, "Clear"),
        h("button", { className: "btn", onClick: onClose, key: "co_hide" }, "Hide"),
      ]),
    ]),
    h("div", { className: "contract-overlay-filter", key: "co_filter" }, [
      h("label", { key: "co_filter_label" }, "source:"),
      h("select", {
        className: "select",
        key: "co_filter_select",
        value: sourceFilter,
        onChange: (e) => setSourceFilter(String(e.target.value || "all")),
      }, sourceOptions.map((opt) => h("option", { value: opt, key: `co_src_${opt}` }, opt))),
      h("label", { key: "co_severity_label" }, "severity:"),
      h("select", {
        className: "select",
        key: "co_severity_select",
        value: severityFilter,
        onChange: (e) => setSeverityFilter(String(e.target.value || "all")),
      }, SEVERITY_FILTER_OPTIONS.map((opt) =>
        h("option", { value: String(opt.id || "all"), key: `co_sev_opt_${String(opt.id || "all")}` }, String(opt.label || opt.id || "all"))
      )),
      h("div", { key: "co_severity_quick", style: { display: "inline-flex", alignItems: "center", gap: "4px" } }, [
        ...["all", "high", "med", "low"].map((sev) =>
          h("button", {
            className: "btn",
            key: `co_sev_btn_${sev}`,
            onClick: () => setSeverityFilter(sev),
            style: {
              padding: "4px 7px",
              fontSize: "10px",
              lineHeight: 1,
              minHeight: 0,
              borderColor: severityFilter === sev ? "#4d7a93" : undefined,
              background: severityFilter === sev ? "rgba(46, 86, 106, 0.42)" : undefined,
            },
          }, `${sev}:${sev === "all" ? Number(scopedRows.length || 0) : Number(severityCounts[sev] || 0)}`)
        ),
      ]),
      h("label", { key: "co_policy_label" }, "policy:"),
      h("select", {
        className: "select",
        key: "co_policy_select",
        value: policyFilter,
        onChange: (e) => setPolicyFilter(String(e.target.value || "all")),
      }, POLICY_FILTER_OPTIONS.map((opt) =>
        h("option", { value: String(opt.id || "all"), key: `co_pol_opt_${String(opt.id || "all")}` }, String(opt.label || opt.id || "all"))
      )),
      h("div", { key: "co_policy_quick", style: { display: "inline-flex", alignItems: "center", gap: "4px" } }, [
        ...["all", "hold", "adopt", "none"].map((policy) =>
          h("button", {
            className: "btn",
            key: `co_pol_btn_${policy}`,
            onClick: () => setPolicyFilter(policy),
            style: {
              padding: "4px 7px",
              fontSize: "10px",
              lineHeight: 1,
              minHeight: 0,
              borderColor: policyFilter === policy ? "#4d7a93" : undefined,
              background: policyFilter === policy ? "rgba(46, 86, 106, 0.42)" : undefined,
            },
          }, `${policy}:${policy === "all" ? Number(severityScopedRows.length || 0) : Number(policyCounts[policy] || 0)}`)
        ),
      ]),
      h("label", { key: "co_run_label" }, "run:"),
      h("select", {
        className: "select",
        key: "co_run_select",
        value: pinnedRunId,
        onChange: (e) => setPinnedRunId(String(e.target.value || "all")),
      }, runOptions.map((opt) => h("option", { value: opt, key: `co_run_${opt}` }, opt))),
      h("label", {
        key: "co_filter_nonzero",
        style: { display: "inline-flex", alignItems: "center", gap: "6px", marginLeft: "6px" },
      }, [
        h("input", {
          type: "checkbox",
          checked: Boolean(nonZeroOnly),
          onChange: (e) => setNonZeroOnly(Boolean(e.target.checked)),
        }),
        "non-zero delta",
      ]),
      h("label", { key: "co_gate_window_label", style: { marginLeft: "8px" } }, "gate window:"),
      h("select", {
        className: "select",
        key: "co_gate_window_select",
        value: gateHistoryLimit,
        onChange: (e) => setGateHistoryLimit(String(e.target.value || "256")),
      }, ["64", "128", "256", "512", "1024"].map((opt) =>
        h("option", { value: opt, key: `co_gate_window_${opt}` }, opt)
      )),
      h("label", { key: "co_gate_pages_label" }, "max pages:"),
      h("div", { className: "btn-row", key: "co_gate_pages_row", style: { gap: "4px" } }, [
        h("select", {
          className: "select",
          key: "co_gate_pages_select",
          value: gateHistoryPages,
          onChange: (e) => setGateHistoryPages(String(e.target.value || "2")),
        }, ["1", "2", "3", "4", "5", "6", "7", "8"].map((opt) =>
          h("option", { value: opt, key: `co_gate_pages_${opt}` }, opt)
        )),
        h("button", {
          className: "btn",
          key: "co_gate_pages_more",
          onClick: () =>
            setGateHistoryPages((prev) => {
              const n = Number(prev || 0);
              const next = Number.isFinite(n) ? (Math.floor(n) + 1) : 2;
              return String(Math.max(1, Math.min(8, next)));
            }),
        }, "+page"),
      ]),
      h("label", { key: "co_row_window_label", style: { marginLeft: "8px" } }, "rows/window:"),
      h("select", {
        className: "select",
        key: "co_row_window_select",
        value: rowWindowSizeText,
        onChange: (e) => setRowWindowSizeText(String(e.target.value || "120")),
      }, rowWindowOptionValues.map((opt) =>
        h("option", { value: opt, key: `co_row_window_${opt}` }, opt)
      )),
      rowVolumeGuardActive
        ? h("label", {
          key: "co_row_volume_guard_bypass",
          className: "hint",
          style: { display: "inline-flex", alignItems: "center", gap: "4px", color: "#8eb6ca" },
        }, [
          h("input", {
            type: "checkbox",
            checked: Boolean(rowVolumeGuardBypass),
            onChange: (e) => setRowVolumeGuardBypass(Boolean(e.target.checked)),
          }),
          "allow large window",
        ])
        : null,
      h("div", { className: "btn-row", key: "co_row_window_nav", style: { gap: "4px" } }, [
        h("button", {
          className: "btn",
          key: "co_row_window_top",
          disabled: rowWindowOffset <= 0,
          onClick: () => setRowWindowOffset(0),
        }, "Top"),
        h("button", {
          className: "btn",
          key: "co_row_window_prev",
          disabled: rowWindowOffset <= 0,
          onClick: () => setRowWindowOffset((prev) => Math.max(0, Number(prev || 0) - rowWindowSize)),
        }, "Prev"),
        h("button", {
          className: "btn",
          key: "co_row_window_next",
          disabled: rowWindowOffset >= maxRowWindowOffset,
          onClick: () => setRowWindowOffset((prev) => Math.min(maxRowWindowOffset, Number(prev || 0) + rowWindowSize)),
        }, "Next"),
      ]),
      h("span", { key: "co_filter_count", style: { marginLeft: "auto", color: "#8eb6ca" } }, [
        `showing ${filteredRows.length}/${severityScopedRows.length}/${scopedRows.length}/${rows.length} (policy/severity/scoped/all) | `,
        `window ${filteredRows.length === 0 ? 0 : rowWindowOffset + 1}-${rowWindowEnd}/${filteredRows.length}`,
      ]),
      rowVolumeGuardActive && !rowVolumeGuardBypass
        ? h("span", {
          key: "co_row_volume_guard_hint",
          className: "hint",
          style: { color: "#f0b33a" },
        }, `guard on: rows/window capped at ${CONTRACT_ROW_VOLUME_GUARD_MAX_WINDOW} (rows>=${CONTRACT_ROW_VOLUME_GUARD_TRIGGER})`)
        : null,
    ]),
    h("div", {
      className: "contract-overlay-filter",
      key: "co_filter_preset_cfg",
      style: { flexWrap: "wrap", rowGap: "6px" },
    }, [
      h("label", { key: "co_filter_preset_label" }, "filter preset:"),
      h("select", {
        className: "select",
        key: "co_filter_preset_select",
        value: activeFilterPreset,
        onChange: (e) => setActiveFilterPreset(String(e.target.value || "default")),
      }, filterPresetOptions.map((name) =>
        h("option", { value: name, key: `co_filter_preset_opt_${name}` }, name)
      )),
      h("button", {
        className: "btn",
        key: "co_filter_preset_apply",
        onClick: applyActiveFilterPreset,
      }, "Load Filter Preset"),
      h("label", { key: "co_filter_preset_save_label", style: { marginLeft: "8px" } }, "save as:"),
      h("input", {
        className: "input",
        key: "co_filter_preset_draft",
        value: filterPresetDraft,
        onChange: (e) => setFilterPresetDraft(String(e.target.value || "")),
        placeholder: "custom_filter",
        style: { minWidth: "140px", maxWidth: "180px", padding: "5px 7px", fontSize: "11px" },
      }),
      h("button", {
        className: "btn",
        key: "co_filter_preset_save",
        onClick: saveCurrentFilterPreset,
        disabled: !normalizedFilterPresetDraft,
      }, "Save Filter Preset"),
      h("button", {
        className: "btn",
        key: "co_filter_preset_delete",
        onClick: deleteActiveFilterPreset,
        disabled: activeFilterPresetIsBuiltin,
      }, "Delete Filter Preset"),
      h("span", {
        key: "co_filter_preset_builtin_tag",
        className: "hint",
        style: { marginLeft: "auto", color: activeFilterPresetIsBuiltin ? "#8eb6ca" : "#f0b33a" },
      }, activeFilterPresetIsBuiltin ? "preset: built-in" : "preset: custom"),
    ]),
    h("div", {
      className: "contract-overlay-filter",
      key: "co_filter_transfer_cfg",
      style: { flexWrap: "wrap", rowGap: "6px" },
    }, [
      h("label", { key: "co_filter_transfer_label" }, "filter preset transfer:"),
      h("button", {
        className: "btn",
        key: "co_filter_export_presets",
        onClick: exportFilterPresetsToJson,
      }, "Export Filter Presets"),
      h("button", {
        className: "btn",
        key: "co_filter_copy_presets",
        onClick: copyFilterPresetsJson,
      }, "Copy Filter Presets"),
      h("button", {
        className: "btn",
        key: "co_filter_load_json",
        onClick: triggerFilterImportFilePick,
      }, "Load Filter JSON"),
      h("label", { key: "co_filter_import_mode_label" }, "import mode:"),
      h("select", {
        className: "select",
        key: "co_filter_import_mode_select",
        value: filterImportMode,
        onChange: (e) => setFilterImportMode(normalizeFilterImportMode(e.target.value)),
      }, FILTER_IMPORT_MODE_OPTIONS.map((option) =>
        h("option", { value: option.id, key: `co_filter_import_mode_opt_${option.id}` }, option.label)
      )),
      filterImportMode === "replace_custom"
        ? h("label", {
          key: "co_filter_replace_confirm",
          className: "hint",
          style: { display: "inline-flex", alignItems: "center", gap: "4px", color: "#f0b33a" },
        }, [
          h("input", {
            type: "checkbox",
            checked: Boolean(filterReplaceConfirmChecked),
            onChange: (e) => setFilterReplaceConfirmChecked(Boolean(e.target.checked)),
          }),
          "confirm replace custom presets",
        ])
        : null,
      h("button", {
        className: "btn",
        key: "co_filter_import_select_all",
        onClick: selectAllFilterImportPresets,
        disabled: filterImportRows.length === 0,
      }, "Select All"),
      h("button", {
        className: "btn",
        key: "co_filter_import_select_none",
        onClick: clearFilterImportPresets,
        disabled: filterImportRows.length === 0,
      }, "Select None"),
      h("button", {
        className: "btn",
        key: "co_filter_import_presets",
        onClick: importFilterPresetsFromText,
        disabled:
          String(filterTransferText || "").trim().length === 0
          || !filterImportPreviewIsValid
          || selectedFilterImportNames.length === 0
          || (replaceImportNeedsConfirmation && !filterReplaceConfirmChecked),
      }, "Import Filter Presets"),
      h("button", {
        className: "btn",
        key: "co_filter_import_undo",
        onClick: undoLastFilterImport,
        disabled: filterImportUndoStack.length === 0,
      }, "Undo Import"),
      h("button", {
        className: "btn",
        key: "co_filter_import_redo",
        onClick: redoLastFilterImport,
        disabled: filterImportRedoStack.length === 0,
      }, "Redo Import"),
      h("input", {
        type: "file",
        key: "co_filter_import_file",
        ref: filterImportFileInputRef,
        accept: ".json,application/json",
        onChange: handleFilterImportFileChange,
        style: { display: "none" },
      }),
      h("textarea", {
        className: "textarea",
        key: "co_filter_transfer_text",
        value: filterTransferText,
        onChange: (e) => setFilterTransferText(String(e.target.value || "")),
        placeholder: "{\"presets\": {\"my_filter\": {\"severityFilter\": \"high\", \"policyFilter\": \"hold\"}}}",
        style: {
          flexBasis: "100%",
          minHeight: "74px",
          padding: "6px 7px",
          fontSize: "10px",
          lineHeight: "1.35",
        },
      }),
      h("span", {
        key: "co_filter_import_preview",
        className: "hint",
        style: {
          color: String(filterImportPreview || "").startsWith("preview: invalid payload")
            ? "#f39b9b"
            : "#8eb6ca",
        },
      }, filterImportPreview),
      h("span", {
        key: "co_filter_import_audit_bundle_preview",
        className: "hint",
        style: {
          color: String(filterImportAuditDeepLinkPreview || "").includes("invalid payload")
            ? "#f39b9b"
            : "#8eb6ca",
        },
      }, filterImportAuditDeepLinkPreview),
      h("span", {
        key: "co_filter_import_audit_bundle_schema_hint",
        className: "hint",
        style: { color: "#8eb6ca" },
      }, `audit bundle expects kind=${FILTER_IMPORT_AUDIT_DEEPLINK_KIND}, schema=${FILTER_IMPORT_AUDIT_DEEPLINK_SCHEMA_VERSION}`),
      h("span", {
        key: "co_filter_import_history_depth",
        className: "hint",
        style: { color: "#8eb6ca" },
      }, `undo/redo depth: ${filterImportUndoStack.length}/${filterImportRedoStack.length}`),
      filterImportRows.length > 0
        ? h("div", {
          key: "co_filter_import_rows",
          style: {
            flexBasis: "100%",
            display: "flex",
            flexWrap: "wrap",
            gap: "6px",
          },
        }, filterImportRows.map((row) =>
          h("label", {
            key: `co_filter_import_row_${row.name}`,
            className: "hint",
            style: {
              display: "inline-flex",
              alignItems: "center",
              gap: "4px",
              border: "1px solid #31576b",
              borderRadius: "999px",
              padding: "2px 7px",
              background: "rgba(24, 50, 65, 0.42)",
              color: "#b8d5e7",
            },
          }, [
            h("input", {
              type: "checkbox",
              checked: Boolean(filterImportSelection[row.name]),
              onChange: () => toggleFilterImportPresetSelection(row.name),
            }),
            `${row.name}:${row.conflict}`,
          ])
        ))
        : null,
      filterImportAuditTrail.length > 0
        ? h("div", {
          key: "co_filter_import_audit",
          style: {
            flexBasis: "100%",
            borderTop: "1px dashed #27485a",
            paddingTop: "6px",
            display: "grid",
            rowGap: "6px",
          },
        }, [
          h("div", { className: "btn-row", key: "co_filter_import_audit_controls", style: { gap: "6px" } }, [
            h("label", { key: "co_filter_import_audit_label" }, "audit trail:"),
            h("input", {
              className: "input",
              key: "co_filter_import_audit_search",
              value: filterImportAuditSearchText,
              onChange: (e) => setFilterImportAuditSearchText(String(e.target.value || "")),
              placeholder: "search id/name/note",
              style: { minWidth: "160px", maxWidth: "240px", padding: "5px 7px", fontSize: "11px" },
            }),
            h("select", {
              className: "select",
              key: "co_filter_import_audit_kind",
              value: filterImportAuditKindFilter,
              onChange: (e) => setFilterImportAuditKindFilter(String(e.target.value || "all")),
              style: { minWidth: "110px", padding: "5px 7px", fontSize: "11px" },
            }, FILTER_IMPORT_AUDIT_KIND_OPTIONS.map((kind) =>
              h("option", { value: kind, key: `co_filter_import_audit_kind_opt_${kind}` }, `kind:${kind}`)
            )),
            h("select", {
              className: "select",
              key: "co_filter_import_audit_mode",
              value: filterImportAuditModeFilter,
              onChange: (e) => setFilterImportAuditModeFilter(String(e.target.value || "all")),
              style: { minWidth: "150px", padding: "5px 7px", fontSize: "11px" },
            }, FILTER_IMPORT_AUDIT_MODE_OPTIONS.map((mode) =>
              h("option", { value: mode, key: `co_filter_import_audit_mode_opt_${mode}` }, `mode:${mode}`)
            )),
            h("div", {
              key: "co_filter_import_audit_presets",
              className: "btn-row",
              style: { gap: "4px" },
            }, FILTER_IMPORT_AUDIT_QUERY_PRESETS.map((preset) => {
              const pid = String(preset?.id || "");
              const selected = pid === activeFilterImportAuditQueryPresetId;
              return h("button", {
                className: "btn",
                key: `co_filter_import_audit_preset_${pid}`,
                onClick: () => applyFilterImportAuditQueryPreset(pid),
                style: selected
                  ? { borderColor: "#4d7a93", background: "rgba(46, 86, 106, 0.42)" }
                  : undefined,
              }, String(preset?.label || pid));
            })),
            h("button", {
              className: "btn",
              key: "co_filter_import_audit_preset_pin",
              onClick: toggleFilterImportAuditPinnedPreset,
              disabled: !filterImportAuditPresetPinnable && !filterImportAuditPinnedPresetActive,
            }, filterImportAuditPinnedPresetActive ? "Unpin Preset" : "Pin Preset"),
            h("span", {
              key: "co_filter_import_audit_preset_pin_hint",
              className: "hint",
              style: { color: "#8eb6ca" },
            }, `pinned:${filterImportAuditPinnedPresetId || "-"}`),
            h("span", {
              key: "co_filter_import_audit_preset_active_hint",
              className: "hint",
              style: { color: "#8eb6ca" },
            }, `active:${activeFilterImportAuditQueryPresetId}`),
            h("span", {
              key: "co_filter_import_audit_shortcut_hint",
              className: "hint",
              style: { color: "#8eb6ca" },
            }, `pin shortcut:${normalizeShortcutToken(shortcutBindings.audit_pin_toggle) || "-"}`),
            h("label", { key: "co_filter_import_prune_label", className: "hint", style: { color: "#8eb6ca" } }, "keep:"),
            h("input", {
              className: "input",
              key: "co_filter_import_prune_keep",
              type: "number",
              min: 1,
              max: FILTER_IMPORT_HISTORY_LIMIT,
              step: 1,
              value: filterImportHistoryKeepText,
              onChange: (e) => setFilterImportHistoryKeepText(String(e.target.value || "")),
              style: { width: "72px", padding: "5px 7px", fontSize: "11px" },
            }),
            h("button", {
              className: "btn",
              key: "co_filter_import_prune",
              onClick: pruneFilterImportHistory,
              disabled: filterImportAuditTrail.length === 0,
            }, "Prune"),
            h("button", {
              className: "btn",
              key: "co_filter_import_clear",
              onClick: clearFilterImportHistory,
              disabled: filterImportAuditTrail.length === 0,
            }, "Clear"),
            h("button", {
              className: "btn",
              key: "co_filter_import_audit_reset",
              onClick: resetFilterImportAuditQuery,
              disabled: !filterImportAuditQueryActive,
            }, "Reset Query"),
            h("button", {
              className: "btn",
              key: "co_filter_import_audit_copy",
              onClick: copyFilterImportAuditDetail,
              disabled: !activeFilterImportAuditEntry,
            }, "Copy Audit Detail"),
            h("button", {
              className: "btn",
              key: "co_filter_import_audit_copy_deeplink",
              onClick: copyFilterImportAuditDeepLinkBundle,
              disabled: !activeFilterImportAuditEntry,
            }, "Copy Deep-Link Bundle"),
            h("button", {
              className: "btn",
              key: "co_filter_import_audit_apply_deeplink",
              onClick: applyFilterImportAuditDeepLinkBundleFromText,
              disabled: parsedFilterImportAuditDeepLinkPayload.empty || Boolean(parsedFilterImportAuditDeepLinkPayload.error),
            }, "Apply Deep-Link Bundle"),
            h("button", {
              className: "btn",
              key: "co_filter_import_audit_export",
              onClick: exportFilterImportAuditJson,
              disabled: filterImportAuditTrail.length === 0,
            }, "Export Audit JSON"),
            h("span", {
              key: "co_filter_import_audit_count",
              className: "hint",
              style: { marginLeft: "auto", color: "#8eb6ca" },
            }, `filtered ${filterImportAuditRowsFiltered.length}/${filterImportAuditTrail.length}`),
          ]),
          h("div", { className: "btn-row", key: "co_filter_import_audit_apply_quick_scopes", style: { gap: "6px", flexWrap: "wrap" } }, [
            h("span", { key: "co_filter_import_audit_apply_quick_label", className: "hint", style: { color: "#8eb6ca" } }, "quick apply:"),
            ...FILTER_IMPORT_AUDIT_QUICK_APPLY_OPTIONS.map((opt) => {
              const oid = String(opt?.id || "");
              const selected = oid === activeFilterImportAuditQuickApplyOptionId;
              return h("button", {
                className: "btn",
                key: `co_filter_import_audit_apply_quick_${oid}`,
                onClick: () => applyFilterImportAuditDeepLinkQuickScope(oid),
                disabled: parsedFilterImportAuditDeepLinkPayload.empty || Boolean(parsedFilterImportAuditDeepLinkPayload.error),
                style: selected
                  ? { borderColor: "#4d7a93", background: "rgba(46, 86, 106, 0.42)" }
                  : undefined,
              }, String(opt?.label || oid));
            }),
            h("label", {
              key: "co_filter_import_audit_apply_quick_sync",
              className: "hint",
              style: { display: "inline-flex", alignItems: "center", gap: "4px", color: "#8eb6ca" },
            }, [
              h("input", {
                type: "checkbox",
                checked: Boolean(filterImportAuditQuickApplySyncRestoreChecked),
                onChange: (e) => setFilterImportAuditQuickApplySyncRestoreChecked(Boolean(e.target.checked)),
              }),
              "sync->restore",
            ]),
            h("span", {
              key: "co_filter_import_audit_apply_quick_active",
              className: "hint",
              style: { color: "#8eb6ca" },
            }, `active:${activeFilterImportAuditQuickApplyOptionId}`),
            h("span", {
              key: "co_filter_import_audit_apply_quick_hint",
              className: "hint",
              style: { marginLeft: "auto", color: "#8eb6ca" },
            }, "quick apply overrides restore scope for this action"),
          ]),
          h("div", { className: "btn-row", key: "co_filter_import_audit_quick_telemetry_controls", style: { gap: "6px", flexWrap: "wrap" } }, [
            h("button", {
              className: "btn",
              key: "co_filter_import_audit_quick_telemetry_copy",
              onClick: copyFilterImportAuditQuickApplyTelemetryJson,
              disabled: filterImportAuditQuickApplyTelemetry.length === 0,
            }, "Copy Quick Telemetry"),
            h("button", {
              className: "btn",
              key: "co_filter_import_audit_quick_telemetry_export",
              onClick: exportFilterImportAuditQuickApplyTelemetryJson,
              disabled: filterImportAuditQuickApplyTelemetry.length === 0,
            }, "Export Quick Telemetry"),
            h("button", {
              className: "btn",
              key: "co_filter_import_audit_quick_telemetry_clear",
              onClick: clearFilterImportAuditQuickApplyTelemetry,
              disabled: filterImportAuditQuickApplyTelemetry.length === 0,
            }, "Clear Quick Telemetry"),
            h("span", {
              key: "co_filter_import_audit_quick_telemetry_summary",
              className: "hint",
              style: { marginLeft: "auto", color: "#8eb6ca" },
            }, filterImportAuditQuickApplyTelemetrySummary),
          ]),
          h("div", { className: "btn-row", key: "co_filter_import_audit_quick_telemetry_drilldown_controls", style: { gap: "6px", flexWrap: "wrap" } }, [
            h("label", {
              key: "co_filter_import_audit_quick_telemetry_drilldown_failure_only",
              className: "hint",
              style: { display: "inline-flex", alignItems: "center", gap: "4px", color: "#8eb6ca" },
            }, [
              h("input", {
                type: "checkbox",
                checked: Boolean(filterImportAuditQuickTelemetryFailureOnlyChecked),
                onChange: (e) => setFilterImportAuditQuickTelemetryFailureOnlyChecked(Boolean(e.target.checked)),
              }),
              "failures-only",
            ]),
            h("label", {
              key: "co_filter_import_audit_quick_telemetry_drilldown_reason_label",
              className: "hint",
              style: { display: "inline-flex", alignItems: "center", gap: "4px", color: "#8eb6ca" },
            }, [
              "reason:",
              h("input", {
                key: "co_filter_import_audit_quick_telemetry_drilldown_reason_query",
                value: filterImportAuditQuickTelemetryReasonQuery,
                onChange: (e) => setFilterImportAuditQuickTelemetryReasonQuery(
                  String(e.target.value || "").slice(0, FILTER_IMPORT_AUDIT_QUICK_REASON_QUERY_MAX)
                ),
                placeholder: "applied/parse_error/no_scope...",
                style: { width: "210px" },
              }),
            ]),
            h("button", {
              className: "btn",
              key: "co_filter_import_audit_quick_telemetry_drilldown_clear",
              onClick: clearFilterImportAuditQuickTelemetryDrilldown,
              disabled: !filterImportAuditQuickTelemetryFailureOnlyChecked && !filterImportAuditQuickTelemetryReasonQuery,
            }, "Reset Drilldown"),
            h("span", {
              key: "co_filter_import_audit_quick_telemetry_drilldown_summary",
              className: "hint",
              style: { marginLeft: "auto", color: "#8eb6ca" },
            }, filterImportAuditQuickTelemetryDrilldownSummary),
          ]),
          h("div", { className: "btn-row", key: "co_filter_import_audit_quick_telemetry_drilldown_presets", style: { gap: "6px", flexWrap: "wrap" } }, [
            h("span", {
              key: "co_filter_import_audit_quick_telemetry_drilldown_preset_label",
              className: "hint",
              style: { color: "#8eb6ca" },
            }, "drilldown preset:"),
            ...FILTER_IMPORT_AUDIT_QUICK_DRILLDOWN_PRESETS.map((preset) => {
              const pid = String(preset?.id || "");
              const selected = pid === activeFilterImportAuditQuickTelemetryDrilldownPresetId;
              return h("button", {
                className: "btn",
                key: `co_filter_import_audit_quick_telemetry_drilldown_preset_${pid}`,
                onClick: () => applyFilterImportAuditQuickTelemetryDrilldownPreset(pid),
                style: selected
                  ? { borderColor: "#4d7a93", background: "rgba(46, 86, 106, 0.42)" }
                  : undefined,
              }, String(preset?.label || pid));
            }),
            h("button", {
              className: "btn",
              key: "co_filter_import_audit_quick_telemetry_drilldown_copy",
              onClick: copyFilterImportAuditQuickTelemetryDrilldownJson,
              disabled: filterImportAuditQuickTelemetryRowsDrilldown.length === 0,
            }, "Copy Drilldown JSON"),
            h("button", {
              className: "btn",
              key: "co_filter_import_audit_quick_telemetry_drilldown_export",
              onClick: exportFilterImportAuditQuickTelemetryDrilldownJson,
              disabled: filterImportAuditQuickTelemetryRowsDrilldown.length === 0,
            }, "Export Drilldown JSON"),
            h("span", {
              key: "co_filter_import_audit_quick_telemetry_drilldown_preset_active",
              className: "hint",
              style: { marginLeft: "auto", color: "#8eb6ca" },
            }, `active:${activeFilterImportAuditQuickTelemetryDrilldownPresetId}`),
          ]),
          h("div", { className: "btn-row", key: "co_filter_import_audit_quick_telemetry_profile_cfg", style: { gap: "6px", flexWrap: "wrap" } }, [
            h("label", {
              key: "co_filter_import_audit_quick_telemetry_profile_label",
              className: "hint",
              style: { color: "#8eb6ca" },
            }, "drilldown profile:"),
            h("select", {
              className: "select",
              key: "co_filter_import_audit_quick_telemetry_profile_select",
              value: activeQuickTelemetryDrilldownProfile,
              onChange: (e) => setActiveQuickTelemetryDrilldownProfile(String(e.target.value || "default")),
            }, quickTelemetryDrilldownProfileOptions.map((name) =>
              h("option", { value: name, key: `co_filter_import_audit_quick_telemetry_profile_opt_${name}` }, name)
            )),
            h("button", {
              className: "btn",
              key: "co_filter_import_audit_quick_telemetry_profile_apply",
              onClick: applyActiveQuickTelemetryDrilldownProfile,
            }, "Load Profile"),
            h("label", {
              key: "co_filter_import_audit_quick_telemetry_profile_save_label",
              className: "hint",
              style: { marginLeft: "6px", color: "#8eb6ca" },
            }, "save as:"),
            h("input", {
              className: "input",
              key: "co_filter_import_audit_quick_telemetry_profile_draft",
              value: quickTelemetryDrilldownProfileDraft,
              onChange: (e) => setQuickTelemetryDrilldownProfileDraft(String(e.target.value || "")),
              placeholder: "custom_drilldown",
              style: { minWidth: "140px", maxWidth: "180px", padding: "5px 7px", fontSize: "11px" },
            }),
            h("button", {
              className: "btn",
              key: "co_filter_import_audit_quick_telemetry_profile_save",
              onClick: saveCurrentQuickTelemetryDrilldownProfile,
              disabled: !normalizedQuickTelemetryDrilldownProfileDraft,
            }, "Save Profile"),
            h("button", {
              className: "btn",
              key: "co_filter_import_audit_quick_telemetry_profile_delete",
              onClick: deleteActiveQuickTelemetryDrilldownProfile,
              disabled: activeQuickTelemetryDrilldownProfileIsBuiltin,
            }, "Delete Profile"),
            h("span", {
              key: "co_filter_import_audit_quick_telemetry_profile_builtin_tag",
              className: "hint",
              style: { marginLeft: "auto", color: activeQuickTelemetryDrilldownProfileIsBuiltin ? "#8eb6ca" : "#f0b33a" },
            }, activeQuickTelemetryDrilldownProfileIsBuiltin ? "profile: built-in" : "profile: custom"),
          ]),
          h("div", { className: "btn-row", key: "co_filter_import_audit_quick_telemetry_profile_transfer_cfg", style: { gap: "6px", flexWrap: "wrap" } }, [
            h("label", {
              key: "co_filter_import_audit_quick_telemetry_profile_transfer_label",
              className: "hint",
              style: { color: "#8eb6ca" },
            }, "drilldown profile transfer:"),
            h("button", {
              className: "btn",
              key: "co_filter_import_audit_quick_telemetry_profile_export",
              onClick: exportQuickTelemetryDrilldownProfilesToJson,
            }, "Export Profiles"),
            h("button", {
              className: "btn",
              key: "co_filter_import_audit_quick_telemetry_profile_copy",
              onClick: copyQuickTelemetryDrilldownProfilesJson,
            }, "Copy Profiles"),
            h("button", {
              className: "btn",
              key: "co_filter_import_audit_quick_telemetry_profile_load_json",
              onClick: triggerQuickTelemetryDrilldownImportFilePick,
            }, "Load JSON"),
            h("button", {
              className: "btn",
              key: "co_filter_import_audit_quick_telemetry_profile_import",
              onClick: importQuickTelemetryDrilldownProfilesFromText,
              disabled: (
                String(quickTelemetryDrilldownTransferText || "").trim().length === 0
                || selectedQuickTelemetryDrilldownImportNames.length === 0
                || (quickTelemetryDrilldownImportHasChangedOverwrite && !quickTelemetryDrilldownImportOverwriteConfirmChecked)
              ),
            }, "Import Profiles"),
            h("button", {
              className: "btn",
              key: "co_filter_import_audit_quick_telemetry_profile_import_undo",
              onClick: undoLastQuickTelemetryDrilldownProfileImport,
              disabled: !quickTelemetryDrilldownImportUndoSnapshot,
            }, "Undo Import"),
            h("label", {
              key: "co_filter_import_audit_quick_telemetry_profile_import_confirm_label",
              className: "hint",
              style: { display: "inline-flex", alignItems: "center", gap: "4px", color: "#8eb6ca" },
            }, [
              h("input", {
                type: "checkbox",
                checked: Boolean(quickTelemetryDrilldownImportOverwriteConfirmChecked),
                onChange: (e) => setQuickTelemetryDrilldownImportOverwriteConfirmChecked(Boolean(e.target.checked)),
              }),
              "confirm overwrite changed profiles",
            ]),
            h("label", {
              key: "co_filter_import_audit_quick_telemetry_profile_import_conflict_only",
              className: "hint",
              style: { display: "inline-flex", alignItems: "center", gap: "4px", color: "#8eb6ca" },
            }, [
              h("input", {
                type: "checkbox",
                checked: Boolean(quickTelemetryDrilldownImportConflictOnlyChecked),
                onChange: (e) => setQuickTelemetryDrilldownImportConflictOnlyChecked(Boolean(e.target.checked)),
              }),
              "conflict-only view",
            ]),
            h("div", {
              key: "co_filter_import_audit_quick_telemetry_profile_import_filter_presets",
              style: {
                flexBasis: "100%",
                display: "flex",
                flexWrap: "wrap",
                gap: "6px",
                alignItems: "center",
              },
            }, [
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_preset_label",
                className: "hint",
                style: { color: "#8eb6ca" },
              }, "filter presets:"),
              ...QUICK_TELEMETRY_DRILLDOWN_IMPORT_FILTER_PRESETS.map((preset) => {
                const pid = String(preset?.id || "");
                const selected = pid === activeQuickTelemetryDrilldownImportFilterPresetId;
                const count = Number(quickTelemetryDrilldownImportFilterPresetCounts[pid] || 0);
                return h("button", {
                  className: "btn",
                  key: `co_filter_import_audit_quick_telemetry_profile_import_filter_preset_chip_${pid}`,
                  onClick: () => applyQuickTelemetryDrilldownImportFilterPreset(pid),
                  style: selected
                    ? { borderColor: "#4d7a93", background: "rgba(46, 86, 106, 0.42)" }
                    : undefined,
                }, `${String(preset?.label || pid)}:${count}`);
              }),
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_preset_active",
                className: "hint",
                style: { marginLeft: "auto", color: "#8eb6ca" },
              }, `active:${activeQuickTelemetryDrilldownImportFilterPresetId}`),
            ]),
            h("label", {
              key: "co_filter_import_audit_quick_telemetry_profile_import_name_query_label",
              className: "hint",
              style: { color: "#8eb6ca" },
            }, "name filter:"),
            h("input", {
              className: "input",
              key: "co_filter_import_audit_quick_telemetry_profile_import_name_query",
              value: quickTelemetryDrilldownImportNameQuery,
              onChange: (e) => setQuickTelemetryDrilldownImportNameQuery(String(e.target.value || "")),
              placeholder: "contains profile name",
              style: { minWidth: "140px", maxWidth: "200px", padding: "5px 7px", fontSize: "11px" },
            }),
            h("button", {
              className: "btn",
              key: "co_filter_import_audit_quick_telemetry_profile_import_filter_reset",
              onClick: resetQuickTelemetryDrilldownImportFilterBundle,
              disabled: quickTelemetryDrilldownImportFilterBundleIsDefault,
            }, "Reset Filter Bundle"),
            h("button", {
              className: "btn",
              key: "co_filter_import_audit_quick_telemetry_profile_import_safety_bundle_reset",
              onClick: resetQuickTelemetryDrilldownImportSafetyBundle,
              disabled: quickTelemetryDrilldownImportSafetyBundleIsDefault,
            }, "Reset Safety Bundle"),
            h("label", {
              key: "co_filter_import_audit_quick_telemetry_profile_import_row_cap_label",
              className: "hint",
              style: { color: "#8eb6ca" },
            }, "rows/page:"),
            h("select", {
              className: "select",
              key: "co_filter_import_audit_quick_telemetry_profile_import_row_cap",
              value: String(quickTelemetryDrilldownImportRowCap),
              onChange: (e) => setQuickTelemetryDrilldownImportRowCapText(
                String(e.target.value || CONTRACT_OVERLAY_DEFAULT_PREFS.quickTelemetryDrilldownImportRowCap)
              ),
              style: { minWidth: "80px", padding: "5px 7px", fontSize: "11px" },
            }, QUICK_TELEMETRY_DRILLDOWN_IMPORT_ROW_CAP_OPTIONS.map((opt) =>
              h("option", { value: opt, key: `co_filter_import_audit_quick_telemetry_profile_import_row_cap_opt_${opt}` }, opt)
            )),
            h("button", {
              className: "btn",
              key: "co_filter_import_audit_quick_telemetry_profile_import_page_top",
              onClick: () => setQuickTelemetryDrilldownImportRowOffset(0),
              disabled: quickTelemetryDrilldownImportRowOffset <= 0,
            }, "Top"),
            h("button", {
              className: "btn",
              key: "co_filter_import_audit_quick_telemetry_profile_import_page_prev",
              onClick: () => setQuickTelemetryDrilldownImportRowOffset((prev) => Math.max(0, Number(prev || 0) - quickTelemetryDrilldownImportRowCap)),
              disabled: quickTelemetryDrilldownImportRowOffset <= 0,
            }, "Prev"),
            h("button", {
              className: "btn",
              key: "co_filter_import_audit_quick_telemetry_profile_import_page_next",
              onClick: () => setQuickTelemetryDrilldownImportRowOffset((prev) => Math.min(
                quickTelemetryDrilldownImportMaxOffset,
                Number(prev || 0) + quickTelemetryDrilldownImportRowCap
              )),
              disabled: quickTelemetryDrilldownImportRowOffset >= quickTelemetryDrilldownImportMaxOffset,
            }, "Next"),
            h("button", {
              className: "btn",
              key: "co_filter_import_audit_quick_telemetry_profile_import_select_all",
              onClick: selectAllQuickTelemetryDrilldownImportRowsVisible,
              disabled: quickTelemetryDrilldownImportSelectionRows.length === 0,
            }, "Select Scope"),
            h("button", {
              className: "btn",
              key: "co_filter_import_audit_quick_telemetry_profile_import_select_none",
              onClick: clearQuickTelemetryDrilldownImportSelection,
              disabled: quickTelemetryDrilldownImportSelectionRows.length === 0,
            }, "Clear Scope"),
            h("button", {
              className: "btn",
              key: "co_filter_import_audit_quick_telemetry_profile_import_select_page",
              onClick: selectPageQuickTelemetryDrilldownImportSelection,
              disabled: quickTelemetryDrilldownImportPreviewRows.length === 0,
            }, "Select Page"),
            h("button", {
              className: "btn",
              key: "co_filter_import_audit_quick_telemetry_profile_import_clear_page",
              onClick: clearPageQuickTelemetryDrilldownImportSelection,
              disabled: quickTelemetryDrilldownImportPreviewRows.length === 0,
            }, "Clear Page"),
            h("input", {
              type: "file",
              key: "co_filter_import_audit_quick_telemetry_profile_import_file",
              ref: quickTelemetryDrilldownImportFileInputRef,
              accept: ".json,application/json",
              onChange: handleQuickTelemetryDrilldownImportFileChange,
              style: { display: "none" },
            }),
            h("span", {
              key: "co_filter_import_audit_quick_telemetry_profile_import_preview",
              className: "hint",
              style: { flexBasis: "100%", color: "#8eb6ca" },
            }, quickTelemetryDrilldownImportPreview),
            h("span", {
              key: "co_filter_import_audit_quick_telemetry_profile_import_page_hint",
              className: "hint",
              style: { flexBasis: "100%", color: "#8eb6ca" },
            }, `window ${quickTelemetryDrilldownImportRowsVisible.length === 0 ? 0 : quickTelemetryDrilldownImportRowOffset + 1}-${quickTelemetryDrilldownImportRowEnd}/${quickTelemetryDrilldownImportRowsVisible.length}`),
            h("div", {
              key: "co_filter_import_audit_quick_telemetry_profile_import_conflict_filter_chips",
              style: {
                flexBasis: "100%",
                display: "flex",
                flexWrap: "wrap",
                gap: "6px",
                alignItems: "center",
              },
            }, [
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_conflict_filter_label",
                className: "hint",
                style: { color: "#8eb6ca" },
              }, "conflict filter:"),
              ...QUICK_TELEMETRY_DRILLDOWN_IMPORT_CONFLICT_FILTER_OPTIONS.map((opt) => {
                const oid = String(opt?.id || "");
                const selected = oid === quickTelemetryDrilldownImportConflictFilter;
                const count = Number(quickTelemetryDrilldownImportConflictFilterCounts[oid] || 0);
                return h("button", {
                  className: "btn",
                  key: `co_filter_import_audit_quick_telemetry_profile_import_conflict_filter_chip_${oid}`,
                  onClick: () => setQuickTelemetryDrilldownImportConflictFilter(oid),
                  style: selected
                    ? { borderColor: "#4d7a93", background: "rgba(46, 86, 106, 0.42)" }
                    : undefined,
                }, `${String(opt?.label || oid)}:${count}`);
              }),
            ]),
            h("span", {
              key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_hint",
              className: "hint",
              style: { flexBasis: "100%", color: "#8eb6ca" },
            }, quickTelemetryDrilldownImportFilterBundleHint),
            h("div", {
              key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_transfer",
              style: {
                flexBasis: "100%",
                display: "flex",
                flexWrap: "wrap",
                gap: "6px",
              },
            }, [
              h("label", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_transfer_label",
                className: "hint",
                style: { color: "#8eb6ca" },
              }, "filter bundle transfer:"),
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_mode_label",
                className: "hint",
                style: { color: "#8eb6ca" },
              }, "import mode:"),
              ...QUICK_TELEMETRY_DRILLDOWN_IMPORT_FILTER_BUNDLE_MODE_OPTIONS.map((opt) => {
                const oid = String(opt?.id || "");
                const selected = oid === quickTelemetryDrilldownImportFilterBundleMode;
                return h("button", {
                  className: "btn",
                  key: `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_mode_chip_${oid}`,
                  onClick: () => setQuickTelemetryDrilldownImportFilterBundleMode(oid),
                  style: selected
                    ? { borderColor: "#4d7a93", background: "rgba(46, 86, 106, 0.42)" }
                    : undefined,
                }, String(opt?.label || oid));
              }),
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_mode_hint",
                className: "hint",
                style: { flexBasis: "100%", color: "#8eb6ca" },
              }, `import mode active:${quickTelemetryDrilldownImportFilterBundleMode}`),
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollout_hint",
                className: "hint",
                style: {
                  flexBasis: "100%",
                  color: quickTelemetryDrilldownImportFilterBundleStrictWrapCandidate.available ? "#e4cf98" : "#8eb6ca",
                },
              }, quickTelemetryDrilldownImportFilterBundleStrictWrapHint),
              h("button", {
                className: "btn",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_wrap_legacy",
                onClick: wrapQuickTelemetryDrilldownImportFilterBundleLegacyPayload,
                disabled: !quickTelemetryDrilldownImportFilterBundleStrictWrapCandidate.available,
              }, "Wrap Legacy -> Strict"),
              h("textarea", {
                className: "textarea",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_wrap_legacy_preview",
                value: quickTelemetryDrilldownImportFilterBundleStrictWrapPreview,
                readOnly: true,
                placeholder: "strict-wrap preview appears here when strict mode detects legacy payload",
                style: {
                  flexBasis: "100%",
                  minHeight: "44px",
                  padding: "6px 7px",
                  fontSize: "10px",
                  lineHeight: "1.3",
                  opacity: quickTelemetryDrilldownImportFilterBundleStrictWrapCandidate.available ? 1 : 0.75,
                },
              }),
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_adoption_gate_hint",
                className: "hint",
                style: {
                  flexBasis: "100%",
                  color: quickTelemetryDrilldownStrictAdoptionChecklist.ready ? "#9ad6b5" : "#e4cf98",
                },
              }, quickTelemetryDrilldownStrictAdoptionChecklistHint),
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_adoption_gate_preview",
                className: "hint",
                style: { flexBasis: "100%", color: "#8eb6ca" },
              }, quickTelemetryDrilldownStrictAdoptionChecklistPreview),
              h("button", {
                className: "btn",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_adoption_gate_reset",
                onClick: resetQuickTelemetryDrilldownStrictAdoptionSignals,
              }, "Reset Adoption Gate"),
              quickTelemetryDrilldownStrictAdoptionGateStatus
                ? h("span", {
                  key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_adoption_gate_status",
                  className: "hint",
                  style: { flexBasis: "100%", color: "#8eb6ca" },
                }, quickTelemetryDrilldownStrictAdoptionGateStatus)
                : null,
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_cutover_hint",
                className: "hint",
                style: {
                  flexBasis: "100%",
                  color: quickTelemetryDrilldownStrictAdoptionChecklist.ready ? "#9ad6b5" : "#e4cf98",
                },
              }, quickTelemetryDrilldownStrictCutoverHint),
              h("button", {
                className: "btn",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_cutover_apply",
                onClick: applyQuickTelemetryStrictDefaultCutoverPreset,
              }, "Apply Strict Default"),
              h("button", {
                className: "btn",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_cutover_compat",
                onClick: switchQuickTelemetryToCompatFallback,
              }, "Switch to Compat Fallback"),
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_cutover_reminder",
                className: "hint",
                style: { flexBasis: "100%", color: "#8eb6ca" },
              }, quickTelemetryDrilldownCompatFallbackReminder),
              quickTelemetryDrilldownStrictCutoverStatus
                ? h("span", {
                  key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_cutover_status",
                  className: "hint",
                  style: { flexBasis: "100%", color: "#8eb6ca" },
                }, quickTelemetryDrilldownStrictCutoverStatus)
                : null,
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_cutover_timeline_hint",
                className: "hint",
                style: { flexBasis: "100%", color: "#8eb6ca" },
              }, quickTelemetryDrilldownStrictCutoverTimelineHint),
              h("button", {
                className: "btn",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_cutover_timeline_export",
                onClick: exportQuickTelemetryDrilldownStrictCutoverLedgerToJson,
              }, "Export Cutover Timeline"),
              h("button", {
                className: "btn",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_cutover_timeline_copy",
                onClick: copyQuickTelemetryDrilldownStrictCutoverLedgerJson,
              }, "Copy Cutover Timeline"),
              h("button", {
                className: "btn",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_cutover_timeline_reset",
                onClick: resetQuickTelemetryDrilldownStrictCutoverLedger,
              }, "Reset Cutover Timeline"),
              h("textarea", {
                className: "textarea",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_cutover_timeline_preview",
                value: quickTelemetryDrilldownStrictCutoverTimelinePreview,
                readOnly: true,
                placeholder: "cutover timeline events appear here",
                style: {
                  flexBasis: "100%",
                  minHeight: "58px",
                  padding: "6px 7px",
                  fontSize: "10px",
                  lineHeight: "1.3",
                  opacity: 0.9,
                },
              }),
              quickTelemetryDrilldownStrictCutoverLedgerStatus
                ? h("span", {
                  key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_cutover_timeline_status",
                  className: "hint",
                  style: { flexBasis: "100%", color: "#8eb6ca" },
                }, quickTelemetryDrilldownStrictCutoverLedgerStatus)
                : null,
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_checklist_hint",
                className: "hint",
                style: {
                  flexBasis: "100%",
                  color: quickTelemetryDrilldownStrictRollbackChecklist.ready ? "#9ad6b5" : "#e4cf98",
                },
              }, quickTelemetryDrilldownStrictRollbackChecklistHint),
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_checklist_preview",
                className: "hint",
                style: { flexBasis: "100%", color: "#8eb6ca" },
              }, quickTelemetryDrilldownStrictRollbackChecklistPreview),
              ...QUICK_TELEMETRY_STRICT_ROLLBACK_DRILL_PRESETS.map((preset) => {
                const pid = String(preset?.id || "");
                const selected = pid === activeQuickTelemetryStrictRollbackDrillPresetId;
                return h("button", {
                  className: "btn",
                  key: `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_preset_chip_${pid}`,
                  onClick: () => applyQuickTelemetryStrictRollbackDrillPreset(pid),
                  style: selected
                    ? { borderColor: "#4d7a93", background: "rgba(46, 86, 106, 0.42)" }
                    : undefined,
                }, String(preset?.label || pid));
              }),
              h("button", {
                className: "btn",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_reset",
                onClick: resetQuickTelemetryStrictRollbackDrillPreset,
              }, "Reset Rollback Drill"),
              quickTelemetryDrilldownStrictRollbackDrillStatus
                ? h("span", {
                  key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_status",
                  className: "hint",
                  style: { flexBasis: "100%", color: "#8eb6ca" },
                }, quickTelemetryDrilldownStrictRollbackDrillStatus)
                : null,
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_hint",
                className: "hint",
                style: { flexBasis: "100%", color: "#8eb6ca" },
              }, quickTelemetryDrilldownStrictRollbackPackagePreview),
              h("button", {
                className: "btn",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_export",
                onClick: exportQuickTelemetryStrictRollbackDrillPackageToJson,
              }, "Export Rollback Package"),
              h("button", {
                className: "btn",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_copy",
                onClick: copyQuickTelemetryStrictRollbackDrillPackageJson,
              }, "Copy Rollback Package"),
              h("button", {
                className: "btn",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_report_copy",
                onClick: copyQuickTelemetryStrictRollbackChecklistReportText,
              }, "Copy Checklist Report"),
              h("textarea", {
                className: "textarea",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_report_preview",
                value: quickTelemetryDrilldownStrictRollbackChecklistReportPreview,
                readOnly: true,
                placeholder: "rollback checklist report preview appears here",
                style: {
                  flexBasis: "100%",
                  minHeight: "50px",
                  padding: "6px 7px",
                  fontSize: "10px",
                  lineHeight: "1.3",
                  opacity: 0.9,
                },
              }),
              quickTelemetryDrilldownStrictRollbackPackageStatus
                ? h("span", {
                  key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_status",
                  className: "hint",
                  style: { flexBasis: "100%", color: "#8eb6ca" },
                }, quickTelemetryDrilldownStrictRollbackPackageStatus)
                : null,
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_policy_label",
                className: "hint",
                style: { color: "#8eb6ca" },
              }, "trust policy:"),
              ...QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_POLICY_OPTIONS.map((opt) => {
                const oid = String(opt?.id || "");
                const selected = oid === quickTelemetryStrictRollbackPackageTrustPolicy;
                return h("button", {
                  className: "btn",
                  key: `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_policy_chip_${oid}`,
                  onClick: () => setQuickTelemetryStrictRollbackPackageTrustPolicy(oid),
                  style: selected
                    ? { borderColor: "#4d7a93", background: "rgba(46, 86, 106, 0.42)" }
                    : undefined,
                }, String(opt?.label || oid));
              }),
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_policy_hint",
                className: "hint",
                style: { flexBasis: "100%", color: "#8eb6ca" },
              }, quickTelemetryStrictRollbackPackageTrustPolicyHint),
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_replay_preview",
                className: "hint",
                style: {
                  flexBasis: "100%",
                  color: parsedQuickTelemetryStrictRollbackDrillPackagePayload.error ? "#f39b9b" : "#8eb6ca",
                },
              }, quickTelemetryStrictRollbackPackageReplayPreview),
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_provenance_hint",
                className: "hint",
                style: {
                  flexBasis: "100%",
                  color: quickTelemetryStrictRollbackPackageProvenanceGuard.has_guard_issue ? "#e4cf98" : "#8eb6ca",
                },
              }, quickTelemetryStrictRollbackPackageProvenanceHint),
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_delta_hint",
                className: "hint",
                style: {
                  flexBasis: "100%",
                  color: (
                    parsedQuickTelemetryStrictRollbackDrillPackagePayload.error
                    || quickTelemetryStrictRollbackPackageChecklistDeltaGuard.has_delta
                  ) ? "#e4cf98" : "#8eb6ca",
                },
              }, quickTelemetryStrictRollbackPackageChecklistDeltaHint),
              h("label", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_delta_confirm",
                className: "hint",
                style: { flexBasis: "100%", display: "inline-flex", alignItems: "center", gap: "6px", color: "#8eb6ca" },
              }, [
                h("input", {
                  type: "checkbox",
                  key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_delta_confirm_checkbox",
                  checked: quickTelemetryDrilldownStrictRollbackPackageDeltaConfirmChecked,
                  onChange: (e) => setQuickTelemetryDrilldownStrictRollbackPackageDeltaConfirmChecked(Boolean(e.target.checked)),
                  disabled: (
                    (
                      !quickTelemetryStrictRollbackPackageChecklistDeltaGuard.has_delta
                      && !quickTelemetryStrictRollbackPackageProvenanceGuard.has_guard_issue
                    )
                    || (
                      quickTelemetryStrictRollbackPackageTrustPolicy === "strict_reject"
                      && quickTelemetryStrictRollbackPackageProvenanceGuard.has_guard_issue
                    )
                  ),
                }),
                "confirm replay when checklist delta/provenance guard exists",
              ]),
              h("button", {
                className: "btn",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_replay",
                onClick: replayQuickTelemetryStrictRollbackPackageFromText,
                disabled: parsedQuickTelemetryStrictRollbackDrillPackagePayload.empty,
              }, "Replay Rollback Package"),
              h("button", {
                className: "btn",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_override_replay",
                onClick: overrideReplayQuickTelemetryStrictRollbackPackageFromText,
                disabled: (
                  parsedQuickTelemetryStrictRollbackDrillPackagePayload.empty
                  || quickTelemetryStrictRollbackPackageTrustPolicy !== "strict_reject"
                  || !quickTelemetryStrictRollbackPackageProvenanceGuard.has_guard_issue
                ),
              }, "Override Reject + Replay"),
              h("input", {
                className: "input",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_override_reason",
                value: quickTelemetryDrilldownStrictRollbackPackageOverrideReasonText,
                onChange: (e) => setQuickTelemetryDrilldownStrictRollbackPackageOverrideReasonText(
                  String(e.target.value || "").slice(0, 160)
                ),
                placeholder: "override reason (optional; logged when override replay runs)",
                style: { minWidth: "280px", flex: "1 1 280px" },
              }),
              h("textarea", {
                className: "textarea",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_replay_text",
                value: quickTelemetryDrilldownStrictRollbackPackageReplayText,
                onChange: (e) => {
                  setQuickTelemetryDrilldownStrictRollbackPackageReplayText(String(e.target.value || ""));
                  setQuickTelemetryDrilldownStrictRollbackPackageDeltaConfirmChecked(false);
                  setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleStatus("");
                  setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus("");
                  setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydratedSnapshot(null);
                  setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmChecked(false);
                },
                placeholder: "{\"schema_version\":1,\"kind\":\"graph_lab_contract_overlay_quick_telemetry_strict_rollback_drill_package\",\"preset_snapshot\":{},\"checklist_report\":{},\"cutover_timeline_entries\":[]}",
                style: {
                  flexBasis: "100%",
                  minHeight: "58px",
                  padding: "6px 7px",
                  fontSize: "10px",
                  lineHeight: "1.3",
                },
              }),
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_override_log_hint",
                className: "hint",
                style: { flexBasis: "100%", color: "#8eb6ca" },
              }, quickTelemetryStrictRollbackPackageOverrideLogHint),
              h("button", {
                className: "btn",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_override_log_copy",
                onClick: copyQuickTelemetryStrictRollbackPackageOverrideLogJson,
                disabled: quickTelemetryStrictRollbackPackageOverrideLogRows.length === 0,
              }, "Copy Override Log"),
              h("button", {
                className: "btn",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_override_log_export",
                onClick: exportQuickTelemetryStrictRollbackPackageOverrideLogToJson,
                disabled: quickTelemetryStrictRollbackPackageOverrideLogRows.length === 0,
              }, "Export Override Log"),
              h("button", {
                className: "btn",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_override_log_reset",
                onClick: resetQuickTelemetryStrictRollbackPackageOverrideLog,
                disabled: (
                  quickTelemetryStrictRollbackPackageOverrideLogRows.length === 0
                  && !String(quickTelemetryDrilldownStrictRollbackPackageOverrideReasonText || "").trim()
                ),
              }, "Reset Override Log"),
              h("textarea", {
                className: "textarea",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_override_log_preview",
                value: quickTelemetryStrictRollbackPackageOverrideLogPreview,
                readOnly: true,
                placeholder: "override replay log preview appears here",
                style: {
                  flexBasis: "100%",
                  minHeight: "58px",
                  padding: "6px 7px",
                  fontSize: "10px",
                  lineHeight: "1.3",
                  opacity: 0.9,
                },
              }),
              quickTelemetryDrilldownStrictRollbackPackageOverrideLogStatus
                ? h("span", {
                  key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_override_log_status",
                  className: "hint",
                  style: { flexBasis: "100%", color: "#8eb6ca" },
                }, quickTelemetryDrilldownStrictRollbackPackageOverrideLogStatus)
                : null,
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_hint",
                className: "hint",
                style: { flexBasis: "100%", color: "#8eb6ca" },
              }, quickTelemetryStrictRollbackTrustAuditBundleHint),
              h("button", {
                className: "btn",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_copy",
                onClick: copyQuickTelemetryStrictRollbackTrustAuditBundleJson,
              }, "Copy Trust Audit Bundle"),
              h("button", {
                className: "btn",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_export",
                onClick: exportQuickTelemetryStrictRollbackTrustAuditBundleToJson,
              }, "Export Trust Audit Bundle"),
              h("textarea", {
                className: "textarea",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_preview",
                value: quickTelemetryStrictRollbackTrustAuditBundlePreview,
                readOnly: true,
                placeholder: "trust audit bundle preview appears here",
                style: {
                  flexBasis: "100%",
                  minHeight: "58px",
                  padding: "6px 7px",
                  fontSize: "10px",
                  lineHeight: "1.3",
                  opacity: 0.9,
                },
              }),
              quickTelemetryDrilldownStrictRollbackTrustAuditBundleStatus
                ? h("span", {
                  key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_status",
                  className: "hint",
                  style: { flexBasis: "100%", color: "#8eb6ca" },
                }, quickTelemetryDrilldownStrictRollbackTrustAuditBundleStatus)
                : null,
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_import_schema_hint",
                className: "hint",
                style: { flexBasis: "100%", color: "#8eb6ca" },
              }, quickTelemetryStrictRollbackTrustAuditBundleImportSchemaHint),
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_import_preview",
                className: "hint",
                style: {
                  flexBasis: "100%",
                  color: parsedQuickTelemetryStrictRollbackTrustAuditBundlePayload.error ? "#f39b9b" : "#8eb6ca",
                },
              }, quickTelemetryStrictRollbackTrustAuditBundleImportPreview),
              quickTelemetryStrictRollbackTrustAuditBundleImportGuidance
                ? h("span", {
                  key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_import_guidance",
                  className: "hint",
                  style: { flexBasis: "100%", color: "#e4cf98" },
                }, quickTelemetryStrictRollbackTrustAuditBundleImportGuidance)
                : null,
              h("textarea", {
                className: "textarea",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_import_text",
                value: quickTelemetryDrilldownStrictRollbackTrustAuditBundleImportText,
                onChange: (e) => {
                  setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleImportText(String(e.target.value || ""));
                  setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleStatus("");
                  setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus("");
                  setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydratedSnapshot(null);
                  setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmChecked(false);
                  setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmChecked(false);
                  setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmArmedAtMs(0);
                  setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmTickMs(0);
                },
                placeholder: "{\"schema_version\":1,\"kind\":\"graph_lab_contract_overlay_quick_telemetry_strict_rollback_trust_audit_bundle\",\"trust_policy_mode\":\"strict_reject\",\"override_log\":{\"entries\":[]},\"provenance_snapshot\":{}}",
                style: {
                  flexBasis: "100%",
                  minHeight: "58px",
                  padding: "6px 7px",
                  fontSize: "10px",
                  lineHeight: "1.3",
                },
              }),
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_safety_hint",
                className: "hint",
                style: {
                  flexBasis: "100%",
                  color: quickTelemetryStrictRollbackTrustAuditBundleApplySafety.needs_confirm ? "#e4cf98" : "#8eb6ca",
                },
              }, quickTelemetryStrictRollbackTrustAuditBundleApplySafetyHint),
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_hint",
                className: "hint",
                style: {
                  flexBasis: "100%",
                  color: quickTelemetryStrictRollbackTrustAuditBundleApplySafety.needs_confirm ? "#e4cf98" : "#8eb6ca",
                },
              }, quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHint),
              h("textarea", {
                className: "textarea",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_preview",
                value: quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunPreview,
                readOnly: true,
                placeholder: "apply dry-run diff preview appears here",
                style: {
                  flexBasis: "100%",
                  minHeight: "58px",
                  padding: "6px 7px",
                  fontSize: "10px",
                  lineHeight: "1.3",
                  opacity: 0.9,
                },
              }),
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_hint",
                className: "hint",
                style: {
                  flexBasis: "100%",
                  color: quickTelemetryStrictRollbackTrustAuditBundleApplySafety.needs_confirm ? "#e4cf98" : "#8eb6ca",
                },
              }, quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackageHint),
              h("button", {
                className: "btn",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_copy",
                onClick: copyQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackageJson,
              }, "Copy Dry-Run Handoff"),
              h("button", {
                className: "btn",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_export",
                onClick: exportQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackageToJson,
              }, "Export Dry-Run Handoff"),
              h("textarea", {
                className: "textarea",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_preview",
                value: quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackagePreview,
                readOnly: true,
                placeholder: "apply dry-run handoff package preview appears here",
                style: {
                  flexBasis: "100%",
                  minHeight: "58px",
                  padding: "6px 7px",
                  fontSize: "10px",
                  lineHeight: "1.3",
                  opacity: 0.9,
                },
              }),
              quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus
                ? h("span", {
                  key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_status",
                  className: "hint",
                  style: { flexBasis: "100%", color: "#8eb6ca" },
                }, quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus)
                : null,
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_schema_hint",
                className: "hint",
                style: { flexBasis: "100%", color: "#8eb6ca" },
              }, quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffImportSchemaHint),
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_preview",
                className: "hint",
                style: {
                  flexBasis: "100%",
                  color: parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackagePayload.error ? "#f39b9b" : "#8eb6ca",
                },
              }, quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffImportPreview),
              quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffImportGuidance
                ? h("span", {
                  key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_guidance",
                  className: "hint",
                  style: { flexBasis: "100%", color: "#e4cf98" },
                }, quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffImportGuidance)
                : null,
              h("textarea", {
                className: "textarea",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_text",
                value: quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffImportText,
                onChange: (e) => {
                  const hadConfirm = quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmChecked;
                  setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffImportText(String(e.target.value || ""));
                  setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus("");
                  setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydratedSnapshot(null);
                  setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmChecked(false);
                  setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmArmedAtMs(0);
                  setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmTickMs(0);
                  if (hadConfirm) {
                    appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityEvent(
                      "disarm_payload_edit",
                      "import payload changed; confirm disarmed"
                    );
                  }
                },
                placeholder: "{\"schema_version\":1,\"kind\":\"graph_lab_contract_overlay_quick_telemetry_strict_rollback_trust_audit_bundle_apply_dry_run_handoff_package\",\"dry_run_summary\":{},\"apply_safety\":{},\"trust_audit_bundle_snapshot\":{}}",
                style: {
                  flexBasis: "100%",
                  minHeight: "58px",
                  padding: "6px 7px",
                  fontSize: "10px",
                  lineHeight: "1.3",
                },
              }),
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_safety_hint",
                className: "hint",
                style: {
                  flexBasis: "100%",
                  color: quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateSafety.needs_confirm
                    ? "#e4cf98"
                    : "#8eb6ca",
                },
              }, quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateSafetyHint),
              h("label", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm",
                className: "hint",
                style: { flexBasis: "100%", display: "inline-flex", alignItems: "center", gap: "6px", color: "#8eb6ca" },
              }, [
                h("input", {
                  type: "checkbox",
                  key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_checkbox",
                  checked: quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmChecked,
                  onChange: (e) => {
                    const next = Boolean(e.target.checked);
                    const nowMs = Date.now();
                    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmChecked(next);
                    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmArmedAtMs(next ? nowMs : 0);
                    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmTickMs(next ? nowMs : 0);
                    appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityEvent(
                      next ? "arm_manual" : "disarm_manual",
                      next ? "operator enabled overwrite confirm" : "operator disabled overwrite confirm"
                    );
                    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
                      next
                        ? "dry-run handoff apply confirm armed: hydrate overwrite is enabled (within 20s or it auto-disarms)"
                        : "dry-run handoff apply confirm disarmed"
                    );
                  },
                  disabled: (
                    parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackagePayload.empty
                    || Boolean(parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackagePayload.error)
                    || !quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateSafety.needs_confirm
                  ),
                }),
                "confirm replace existing hydrated dry-run handoff snapshot",
              ]),
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_countdown_hint",
                className: "hint",
                style: {
                  flexBasis: "100%",
                  color: quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmChecked ? "#e6cf95" : "#8eb6ca",
                },
              }, quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmCountdownHint),
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_hint",
                className: "hint",
                style: { flexBasis: "100%", color: "#8eb6ca" },
              }, quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityTrailHint),
              h("textarea", {
                className: "textarea",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_preview",
                value: quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityTrailPreview,
                readOnly: true,
                placeholder: "dry-run handoff apply confirm activity trail appears here",
                style: {
                  flexBasis: "100%",
                  minHeight: "52px",
                  padding: "6px 7px",
                  fontSize: "10px",
                  lineHeight: "1.3",
                  opacity: 0.9,
                },
              }),
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_schema_hint",
                className: "hint",
                style: { flexBasis: "100%", color: "#8eb6ca" },
              }, quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityImportSchemaHint),
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_preview",
                className: "hint",
                style: {
                  flexBasis: "100%",
                  color: parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityBundlePayload.error
                    ? "#f39b9b"
                    : "#8eb6ca",
                },
              }, quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityImportPreview),
              quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityImportGuidance
                ? h("span", {
                  key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_guidance",
                  className: "hint",
                  style: { flexBasis: "100%", color: "#e4cf98" },
                }, quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityImportGuidance)
                : null,
              h("textarea", {
                className: "textarea",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_text",
                value: quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityImportText,
                onChange: (e) => {
                  const hadReplayConfirm = quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmChecked;
                  setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityImportText(String(e.target.value || ""));
                  setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmChecked(false);
                  setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmArmedAtMs(0);
                  setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTickMs(0);
                  if (hadReplayConfirm) {
                    appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmEvent(
                      "replay_disarm_payload_edit",
                      "replay payload changed; replacement confirm disarmed"
                    );
                  }
                  setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus("");
                },
                placeholder: "{\"schema_version\":1,\"kind\":\"graph_lab_contract_overlay_quick_telemetry_strict_rollback_trust_audit_bundle_apply_dry_run_handoff_hydrate_confirm_activity\",\"entries\":[]}",
                style: {
                  flexBasis: "100%",
                  minHeight: "52px",
                  padding: "6px 7px",
                  fontSize: "10px",
                  lineHeight: "1.3",
                },
              }),
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_safety_hint",
                className: "hint",
                style: {
                  flexBasis: "100%",
                  color: quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplaySafety.needs_confirm
                    ? "#e4cf98"
                    : "#8eb6ca",
                },
              }, quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplaySafetyHint),
              h("label", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm",
                className: "hint",
                style: { flexBasis: "100%", display: "inline-flex", alignItems: "center", gap: "6px", color: "#8eb6ca" },
              }, [
                h("input", {
                  type: "checkbox",
                  key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_checkbox",
                  checked: quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmChecked,
                  onChange: (e) => {
                    const next = Boolean(e.target.checked);
                    const nowMs = Date.now();
                    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmChecked(next);
                    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmArmedAtMs(next ? nowMs : 0);
                    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTickMs(next ? nowMs : 0);
                    appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmEvent(
                      next ? "replay_arm_manual" : "replay_disarm_manual",
                      next
                        ? "operator enabled replay replacement confirm"
                        : "operator disabled replay replacement confirm"
                    );
                    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
                      next
                        ? "dry-run handoff apply confirm activity replay confirm armed (within 20s or it auto-disarms)"
                        : "dry-run handoff apply confirm activity replay confirm disarmed"
                    );
                  },
                  disabled: (
                    parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityBundlePayload.empty
                    || Boolean(parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityBundlePayload.error)
                    || !quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplaySafety.needs_confirm
                  ),
                }),
                "confirm replace existing confirm activity trail",
              ]),
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_countdown_hint",
                className: "hint",
                style: {
                  flexBasis: "100%",
                  color: quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmChecked
                    ? "#e6cf95"
                    : "#8eb6ca",
                },
              }, quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmCountdownHint),
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_hint",
                className: "hint",
                style: { flexBasis: "100%", color: "#8eb6ca" },
              }, quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailHint),
              h("textarea", {
                className: "textarea",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_preview",
                value: quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailPreview,
                readOnly: true,
                placeholder: "confirm activity replay trail appears here",
                style: {
                  flexBasis: "100%",
                  minHeight: "52px",
                  padding: "6px 7px",
                  fontSize: "10px",
                  lineHeight: "1.3",
                  opacity: 0.9,
                },
              }),
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_schema_hint",
                className: "hint",
                style: { flexBasis: "100%", color: "#8eb6ca" },
              }, quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportSchemaHint),
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_preview",
                className: "hint",
                style: {
                  flexBasis: "100%",
                  color: parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportPayload.error
                    ? "#f39b9b"
                    : "#8eb6ca",
                },
              }, quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportPreview),
              quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportGuidance
                ? h("span", {
                  key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_guidance",
                  className: "hint",
                  style: { flexBasis: "100%", color: "#e4cf98" },
                }, quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportGuidance)
                : null,
              h("textarea", {
                className: "textarea",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_text",
                value: quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportText,
                onChange: (e) => {
                  const hadTrailImportConfirm = quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmChecked;
                  setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportText(String(e.target.value || ""));
                  setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmChecked(false);
                  setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmArmedAtMs(0);
                  setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTickMs(0);
                  if (hadTrailImportConfirm) {
                    appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmEvent(
                      "trail_import_disarm_payload_edit",
                      "replay trail import payload changed; replacement confirm disarmed"
                    );
                  }
                  setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus("");
                },
                placeholder: "{\"schema_version\":1,\"kind\":\"graph_lab_contract_overlay_quick_telemetry_strict_rollback_trust_audit_bundle_apply_dry_run_handoff_hydrate_confirm_activity_replay_confirm_trail\",\"entries\":[]}",
                style: {
                  flexBasis: "100%",
                  minHeight: "52px",
                  padding: "6px 7px",
                  fontSize: "10px",
                  lineHeight: "1.3",
                },
              }),
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_safety_hint",
                className: "hint",
                style: {
                  flexBasis: "100%",
                  color: quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportSafety.needs_confirm
                    ? "#e4cf98"
                    : "#8eb6ca",
                },
              }, quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportSafetyHint),
              h("label", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_confirm",
                className: "hint",
                style: { flexBasis: "100%", display: "inline-flex", alignItems: "center", gap: "6px", color: "#8eb6ca" },
              }, [
                h("input", {
                  type: "checkbox",
                  key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_confirm_checkbox",
                  checked: quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmChecked,
                  onChange: (e) => {
                    const next = Boolean(e.target.checked);
                    const nowMs = Date.now();
                    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmChecked(next);
                    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmArmedAtMs(next ? nowMs : 0);
                    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTickMs(next ? nowMs : 0);
                    appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmEvent(
                      next ? "trail_import_arm_manual" : "trail_import_disarm_manual",
                      next
                        ? "operator enabled replay trail import replacement confirm"
                        : "operator disabled replay trail import replacement confirm"
                    );
                    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
                      next
                        ? "dry-run handoff apply confirm activity replay trail import confirm armed (within 20s or it auto-disarms)"
                        : "dry-run handoff apply confirm activity replay trail import confirm disarmed"
                    );
                  },
                  disabled: (
                    parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportPayload.empty
                    || Boolean(parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportPayload.error)
                    || !quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportSafety.needs_confirm
                  ),
                }),
                "confirm replace existing replay timeline trail",
              ]),
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_confirm_countdown_hint",
                className: "hint",
                style: {
                  flexBasis: "100%",
                  color: quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmChecked
                    ? "#e6cf95"
                    : "#8eb6ca",
                },
              }, quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmCountdownHint),
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_confirm_trail_import_schema_hint",
                className: "hint",
                style: { flexBasis: "100%", color: "#8eb6ca" },
              }, quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportSchemaHint),
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_confirm_trail_import_preview",
                className: "hint",
                style: {
                  flexBasis: "100%",
                  color: parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportPayload.error
                    ? "#f39b9b"
                    : "#8eb6ca",
                },
              }, quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportPreview),
              quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportGuidance
                ? h("span", {
                  key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_confirm_trail_import_guidance",
                  className: "hint",
                  style: { flexBasis: "100%", color: "#e4cf98" },
                }, quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportGuidance)
                : null,
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_confirm_trail_import_controls_snapshot_guidance",
                className: "hint",
                style: { flexBasis: "100%", color: "#8eb6ca" },
              }, quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportControlsSnapshotGuidance),
              h("textarea", {
                className: "textarea",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_confirm_trail_import_text",
                value: quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportText,
                onChange: (e) => {
                  const hadImportConfirm = quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmChecked;
                  setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportText(String(e.target.value || ""));
                  setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmChecked(false);
                  setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmArmedAtMs(0);
                  setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmTickMs(0);
                  if (hadImportConfirm) {
                    appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmEvent(
                      "import_confirm_trail_import_disarm_payload_edit",
                      `import confirm trail payload changed; replacement confirm disarmed (${quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportOperatorHint})`
                    );
                    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailControlsStatus(
                      "import confirm trail controls: replacement confirm disarmed (payload edit)"
                    );
                  }
                  setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
                    hadImportConfirm
                      ? "dry-run handoff apply confirm activity replay trail import confirm trail import payload changed; replacement confirm disarmed"
                      : ""
                  );
                },
                placeholder: "{\"schema_version\":1,\"kind\":\"graph_lab_contract_overlay_quick_telemetry_strict_rollback_trust_audit_bundle_apply_dry_run_handoff_hydrate_confirm_activity_replay_confirm_trail_import_confirm_trail\",\"entries\":[]}",
                style: {
                  flexBasis: "100%",
                  minHeight: "52px",
                  padding: "6px 7px",
                  fontSize: "10px",
                  lineHeight: "1.3",
                },
              }),
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_confirm_trail_import_safety_hint",
                className: "hint",
                style: {
                  flexBasis: "100%",
                  color: quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportSafety.needs_confirm
                    ? "#e4cf98"
                    : "#8eb6ca",
                },
              }, quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportSafetyHint),
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_confirm_trail_import_operator_hint",
                className: "hint",
                style: { flexBasis: "100%", color: "#8eb6ca" },
              }, quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportOperatorHint),
              h("label", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_confirm_trail_import_confirm",
                className: "hint",
                style: { flexBasis: "100%", display: "inline-flex", alignItems: "center", gap: "6px", color: "#8eb6ca" },
              }, [
                h("input", {
                  type: "checkbox",
                  key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_confirm_trail_import_confirm_checkbox",
                  checked: quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmChecked,
                  onChange: (e) => {
                    const next = Boolean(e.target.checked);
                    const nowMs = Date.now();
                    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmChecked(next);
                    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmArmedAtMs(next ? nowMs : 0);
                    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmTickMs(next ? nowMs : 0);
                    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailControlsStatus(
                      next
                        ? "import confirm trail controls: replacement confirm armed"
                        : "import confirm trail controls: replacement confirm disarmed (manual)"
                    );
                    appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmEvent(
                      next ? "import_confirm_trail_import_arm_manual" : "import_confirm_trail_import_disarm_manual",
                      next
                        ? `operator enabled import confirm trail replacement confirm (${quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportOperatorHint})`
                        : `operator disabled import confirm trail replacement confirm (${quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportOperatorHint})`
                    );
                    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus(
                      next
                        ? "dry-run handoff apply confirm activity replay trail import confirm trail import confirm armed"
                        : "dry-run handoff apply confirm activity replay trail import confirm trail import confirm disarmed"
                    );
                  },
                  disabled: (
                    parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportPayload.empty
                    || Boolean(parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportPayload.error)
                    || !quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportSafety.needs_confirm
                  ),
                }),
                "confirm replace existing import confirm trail",
              ]),
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_confirm_trail_import_confirm_countdown_hint",
                className: "hint",
                style: {
                  flexBasis: "100%",
                  color: quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmChecked
                    ? "#e6cf95"
                    : "#8eb6ca",
                },
              }, quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmCountdownHint),
              h("button", {
                className: "btn",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_confirm_trail_import_apply",
                onClick: applyQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailFromText,
                disabled: (
                  parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportPayload.empty
                  || Boolean(parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportPayload.error)
                  || (
                    quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportSafety.needs_confirm
                    && !quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmChecked
                  )
                ),
              }, "Apply Import Confirm Trail"),
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_confirm_trail_import_apply_continuity_hint",
                className: "hint",
                style: { flexBasis: "100%", color: "#8eb6ca" },
              }, quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportApplyContinuityHint),
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_confirm_trail_hint",
                className: "hint",
                style: { flexBasis: "100%", color: "#8eb6ca" },
              }, quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailHint),
              h("textarea", {
                className: "textarea",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_confirm_trail_preview",
                value: quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailPreview,
                readOnly: true,
                placeholder: "confirm activity replay trail import confirm trail appears here",
                style: {
                  flexBasis: "100%",
                  minHeight: "52px",
                  padding: "6px 7px",
                  fontSize: "10px",
                  lineHeight: "1.3",
                  opacity: 0.9,
                },
              }),
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_confirm_trail_controls_hint",
                className: "hint",
                style: { flexBasis: "100%", color: "#8eb6ca" },
              }, quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailControlsHint),
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_confirm_trail_controls_continuity_hint",
                className: "hint",
                style: { flexBasis: "100%", color: "#8eb6ca" },
              }, quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailControlsContinuityHint),
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_confirm_trail_apply_trail_lifecycle_hint",
                className: "hint",
                style: { flexBasis: "100%", color: "#8eb6ca" },
              }, quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailApplyTrailLifecycleHint),
              h("button", {
                className: "btn",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_confirm_trail_copy",
                onClick: copyQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailJson,
                disabled: quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmRows.length === 0,
              }, "Copy Import Confirm Trail"),
              h("button", {
                className: "btn",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_confirm_trail_export",
                onClick: exportQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailToJson,
                disabled: quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmRows.length === 0,
              }, "Export Import Confirm Trail"),
              h("button", {
                className: "btn",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_confirm_trail_reset",
                onClick: resetQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrail,
                disabled: quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmRows.length === 0,
              }, "Reset Import Confirm Trail"),
              h("button", {
                className: "btn",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_apply",
                onClick: applyQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailFromText,
                disabled: (
                  parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportPayload.empty
                  || Boolean(parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportPayload.error)
                ),
              }, "Apply Replay Trail Import"),
              h("button", {
                className: "btn",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_copy",
                onClick: copyQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailJson,
                disabled: quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmRows.length === 0,
              }, "Copy Replay Trail"),
              h("button", {
                className: "btn",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_export",
                onClick: exportQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailToJson,
                disabled: quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmRows.length === 0,
              }, "Export Replay Trail"),
              h("button", {
                className: "btn",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_reset",
                onClick: resetQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrail,
                disabled: quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmRows.length === 0,
              }, "Reset Replay Trail"),
              h("button", {
                className: "btn",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_replay",
                onClick: replayQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityTrailFromText,
                disabled: (
                  parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityBundlePayload.empty
                  || Boolean(parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityBundlePayload.error)
                ),
              }, "Replay Confirm Activity"),
              h("button", {
                className: "btn",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_copy",
                onClick: copyQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityTrailJson,
                disabled: quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityRows.length === 0,
              }, "Copy Confirm Activity"),
              h("button", {
                className: "btn",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_export",
                onClick: exportQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityTrailToJson,
                disabled: quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityRows.length === 0,
              }, "Export Confirm Activity"),
              h("button", {
                className: "btn",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_reset",
                onClick: resetQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityTrail,
                disabled: quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityRows.length === 0,
              }, "Reset Confirm Activity"),
              h("button", {
                className: "btn",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply",
                onClick: applyQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffFromText,
                disabled: (
                  parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackagePayload.empty
                  || Boolean(parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackagePayload.error)
                ),
              }, "Apply Dry-Run Handoff Snapshot"),
              h("button", {
                className: "btn",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_reset",
                onClick: resetQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydratedSnapshot,
                disabled: !quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydratedSnapshot,
              }, "Reset Hydrated Snapshot"),
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_hint",
                className: "hint",
                style: { flexBasis: "100%", color: "#8eb6ca" },
              }, quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydratedHint),
              h("textarea", {
                className: "textarea",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_preview",
                value: quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydratedPreview,
                readOnly: true,
                placeholder: "hydrated dry-run handoff snapshot preview appears here",
                style: {
                  flexBasis: "100%",
                  minHeight: "58px",
                  padding: "6px 7px",
                  fontSize: "10px",
                  lineHeight: "1.3",
                  opacity: 0.9,
                },
              }),
              h("label", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_confirm",
                className: "hint",
                style: { flexBasis: "100%", display: "inline-flex", alignItems: "center", gap: "6px", color: "#8eb6ca" },
              }, [
                h("input", {
                  type: "checkbox",
                  key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_confirm_checkbox",
                  checked: quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmChecked,
                  onChange: (e) => {
                    const next = Boolean(e.target.checked);
                    const nowMs = Date.now();
                    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmChecked(next);
                    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmArmedAtMs(next ? nowMs : 0);
                    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmTickMs(next ? nowMs : 0);
                    setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleStatus(
                      next
                        ? "trust audit apply confirm armed: apply within 20s or it auto-disarms"
                        : "trust audit apply confirm disarmed"
                    );
                  },
                  disabled: (
                    parsedQuickTelemetryStrictRollbackTrustAuditBundlePayload.empty
                    || Boolean(parsedQuickTelemetryStrictRollbackTrustAuditBundlePayload.error)
                    || !quickTelemetryStrictRollbackTrustAuditBundleApplySafety.needs_confirm
                  ),
                }),
                "confirm replace trust policy/override log from trust-audit handoff",
              ]),
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_confirm_countdown_hint",
                className: "hint",
                style: {
                  flexBasis: "100%",
                  color: quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmChecked ? "#e6cf95" : "#8eb6ca",
                },
              }, quickTelemetryStrictRollbackTrustAuditBundleApplyConfirmCountdownHint),
              h("button", {
                className: "btn",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_import_apply",
                onClick: applyQuickTelemetryStrictRollbackTrustAuditBundleFromText,
                disabled: (
                  parsedQuickTelemetryStrictRollbackTrustAuditBundlePayload.empty
                  || Boolean(parsedQuickTelemetryStrictRollbackTrustAuditBundlePayload.error)
                ),
              }, "Apply Trust Audit Bundle"),
              h("button", {
                className: "btn",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_export",
                onClick: exportQuickTelemetryDrilldownImportFilterBundleToJson,
              }, "Export Filter Bundle"),
              h("button", {
                className: "btn",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_copy",
                onClick: copyQuickTelemetryDrilldownImportFilterBundleJson,
              }, "Copy Filter Bundle"),
              h("button", {
                className: "btn",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_import",
                onClick: importQuickTelemetryDrilldownImportFilterBundleFromText,
                disabled: String(quickTelemetryDrilldownImportFilterBundleText || "").trim().length === 0,
              }, "Import Filter Bundle"),
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_schema_hint",
                className: "hint",
                style: { flexBasis: "100%", color: "#8eb6ca" },
              }, quickTelemetryDrilldownImportFilterBundleSchemaHint),
              h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_preview",
                className: "hint",
                style: { flexBasis: "100%", color: String(quickTelemetryDrilldownImportFilterBundlePreview || "").includes("invalid payload") ? "#f39b9b" : "#8eb6ca" },
              }, quickTelemetryDrilldownImportFilterBundlePreview),
              quickTelemetryDrilldownImportFilterBundleInvalidGuidance
                ? h("span", {
                  key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_operator_hint",
                  className: "hint",
                  style: { flexBasis: "100%", color: "#e4cf98" },
                }, quickTelemetryDrilldownImportFilterBundleInvalidGuidance)
                : null,
              h("textarea", {
                className: "textarea",
                key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_text",
                value: quickTelemetryDrilldownImportFilterBundleText,
                onChange: (e) => setQuickTelemetryDrilldownImportFilterBundleText(String(e.target.value || "")),
                placeholder: "{\"kind\":\"graph_lab_contract_overlay_quick_telemetry_drilldown_import_filter_bundle\",\"schema_version\":1,\"filter_bundle\":{\"conflict_only\":true,\"conflict_filter\":\"overwrite_changed\",\"name_query\":\"ops\",\"row_cap\":24}}",
                style: {
                  flexBasis: "100%",
                  minHeight: "50px",
                  padding: "6px 7px",
                  fontSize: "10px",
                  lineHeight: "1.35",
                },
              }),
              quickTelemetryDrilldownImportFilterBundleStatus
                ? h("span", {
                  key: "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_status",
                  className: "hint",
                  style: { marginLeft: "auto", color: "#8eb6ca" },
                }, quickTelemetryDrilldownImportFilterBundleStatus)
                : null,
            ]),
            h("span", {
              key: "co_filter_import_audit_quick_telemetry_profile_import_selection_safety",
              className: "hint",
              style: {
                flexBasis: "100%",
                color: (
                  quickTelemetryDrilldownImportHiddenSelectionCount > 0
                  || quickTelemetryDrilldownImportSelectedOffPageCount > 0
                ) ? "#e4cf98" : "#8eb6ca",
              },
            }, quickTelemetryDrilldownImportSelectionSafetyHint),
            h("span", {
              key: "co_filter_import_audit_quick_telemetry_profile_import_rollback_hint",
              className: "hint",
              style: { flexBasis: "100%", color: "#8eb6ca" },
            }, quickTelemetryDrilldownImportRollbackHint),
            quickTelemetryDrilldownImportPreviewRows.length > 0
              ? h("div", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_rows",
                style: {
                  flexBasis: "100%",
                  display: "flex",
                  flexWrap: "wrap",
                  gap: "6px",
                },
              }, quickTelemetryDrilldownImportPreviewRows.map((row, idx) =>
                h("label", {
                  key: `co_filter_import_audit_quick_telemetry_profile_import_preview_row_${idx}`,
                  className: "hint",
                  style: {
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "4px",
                    border: "1px solid #31576b",
                    borderRadius: "999px",
                    padding: "2px 7px",
                    color: row.conflict === "new"
                      ? "#8eb6ca"
                      : (row.changed ? "#e4cf98" : "#8eb6ca"),
                    background: row.conflict === "new"
                      ? "rgba(20, 37, 47, 0.42)"
                      : (row.changed ? "rgba(79, 63, 19, 0.33)" : "rgba(20, 37, 47, 0.42)"),
                  },
                }, [
                  h("input", {
                    type: "checkbox",
                    checked: Boolean(quickTelemetryDrilldownImportSelection[row.name]),
                    onChange: () => toggleQuickTelemetryDrilldownImportSelection(row.name),
                  }),
                  `${String(row.name || "-")} (${String(row.conflict || "-")}${row.changed ? ", changed" : ", same"})`,
                ])
              ))
              : h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_import_rows_empty",
                className: "hint",
                style: { flexBasis: "100%", color: "#8eb6ca" },
              }, "import rows: no matches in current view"),
            h("textarea", {
              className: "textarea",
              key: "co_filter_import_audit_quick_telemetry_profile_transfer_text",
              value: quickTelemetryDrilldownTransferText,
              onChange: (e) => setQuickTelemetryDrilldownTransferText(String(e.target.value || "")),
              placeholder: "{\"profiles\": {\"ops_fail_focus\": {\"failure_only\": true, \"reason_query\": \"parse_error\"}}}",
              style: {
                flexBasis: "100%",
                minHeight: "62px",
                padding: "6px 7px",
                fontSize: "10px",
                lineHeight: "1.35",
              },
            }),
            quickTelemetryDrilldownTransferStatus
              ? h("span", {
                key: "co_filter_import_audit_quick_telemetry_profile_transfer_status",
                className: "hint",
                style: { marginLeft: "auto", color: "#8eb6ca" },
              }, quickTelemetryDrilldownTransferStatus)
              : null,
          ]),
          h("div", { className: "btn-row", key: "co_filter_import_audit_quick_telemetry_reason_chips", style: { gap: "6px", flexWrap: "wrap" } }, [
            h("span", {
              key: "co_filter_import_audit_quick_telemetry_reason_chip_label",
              className: "hint",
              style: { color: "#8eb6ca" },
            }, "reason focus:"),
            ...filterImportAuditQuickTelemetryReasonChips.map((row, idx) => h("button", {
              className: "btn",
              key: `co_filter_import_audit_quick_telemetry_reason_chip_${idx}`,
              onClick: () => applyFilterImportAuditQuickTelemetryReasonChip(row.reason),
            }, `${String(row.reason || "-").slice(0, 28)}:${Number(row.count || 0)}`)),
            filterImportAuditQuickTelemetryReasonChips.length === 0 ? h("span", {
              key: "co_filter_import_audit_quick_telemetry_reason_chip_empty",
              className: "hint",
              style: { color: "#8eb6ca" },
            }, "no reason matches") : null,
          ]),
          h("div", { className: "btn-row", key: "co_filter_import_audit_quick_telemetry_trend_chips", style: { gap: "6px", flexWrap: "wrap" } }, [
            h("span", {
              key: "co_filter_import_audit_quick_telemetry_chip_recent_rate",
              className: "hint",
              style: {
                border: "1px solid #31576b",
                borderRadius: "999px",
                padding: "2px 7px",
                color: filterImportAuditQuickTelemetryTrend.recentOkPct >= 70 ? "#b2e7bf" : (filterImportAuditQuickTelemetryTrend.recentOkPct >= 40 ? "#e4cf98" : "#efb0a6"),
                background: filterImportAuditQuickTelemetryTrend.recentOkPct >= 70 ? "rgba(21, 72, 38, 0.38)" : "rgba(20, 37, 47, 0.42)",
              },
            }, `recent-ok:${filterImportAuditQuickTelemetryTrend.recentOk}/${filterImportAuditQuickTelemetryTrend.recentCount} (${filterImportAuditQuickTelemetryTrend.recentOkPct}%)`),
            h("span", {
              key: "co_filter_import_audit_quick_telemetry_chip_fail_streak",
              className: "hint",
              style: {
                border: "1px solid #31576b",
                borderRadius: "999px",
                padding: "2px 7px",
                color: filterImportAuditQuickTelemetryTrend.failStreak > 0 ? "#efb0a6" : "#8eb6ca",
                background: filterImportAuditQuickTelemetryTrend.failStreak > 0 ? "rgba(94, 44, 36, 0.38)" : "rgba(20, 37, 47, 0.42)",
              },
            }, `fail-streak:${filterImportAuditQuickTelemetryTrend.failStreak}`),
            h("span", {
              key: "co_filter_import_audit_quick_telemetry_chip_sync_rate",
              className: "hint",
              style: {
                border: "1px solid #31576b",
                borderRadius: "999px",
                padding: "2px 7px",
                color: "#8eb6ca",
                background: "rgba(20, 37, 47, 0.42)",
              },
            }, `sync-applied:${filterImportAuditQuickTelemetryTrend.syncApplied}/${filterImportAuditQuickTelemetryTrend.recentCount} (${filterImportAuditQuickTelemetryTrend.syncAppliedPct}%)`),
            h("span", {
              key: "co_filter_import_audit_quick_telemetry_chip_latest_reason",
              className: "hint",
              style: {
                border: "1px solid #31576b",
                borderRadius: "999px",
                padding: "2px 7px",
                color: "#8eb6ca",
                background: "rgba(20, 37, 47, 0.42)",
              },
            }, `latest:${filterImportAuditQuickTelemetryTrend.latestOption}/${filterImportAuditQuickTelemetryTrend.latestReason}`),
          ]),
          h("div", { className: "btn-row", key: "co_filter_import_audit_safe_reset_controls", style: { gap: "6px", flexWrap: "wrap" } }, [
            h("label", {
              key: "co_filter_import_audit_reset_arm",
              className: "hint",
              style: { display: "inline-flex", alignItems: "center", gap: "4px", color: "#8eb6ca" },
            }, [
              h("input", {
                type: "checkbox",
                checked: Boolean(filterImportAuditResetArmedChecked),
                onChange: (e) => {
                  const next = Boolean(e.target.checked);
                  setFilterImportAuditResetArmedChecked(next);
                  setFilterImportAuditResetArmedAtMs(next ? Date.now() : 0);
                  setFilterImportAuditResetTickMs(next ? Date.now() : 0);
                  setFilterTransferStatus(
                    next
                      ? "reset armed: choose reset action within 20s (safe window active)"
                      : "reset disarmed: safe reset idle"
                  );
                },
              }),
              "arm reset",
            ]),
            h("button", {
              className: "btn",
              key: "co_filter_import_audit_reset_restore_scope",
              onClick: resetFilterImportAuditRestoreScope,
              disabled: !filterImportAuditResetArmedChecked,
            }, "Reset Restore Scope"),
            h("button", {
              className: "btn",
              key: "co_filter_import_audit_reset_pin_context",
              onClick: resetFilterImportAuditPinContext,
              disabled: !filterImportAuditResetArmedChecked,
            }, "Reset Pin Context"),
            h("button", {
              className: "btn",
              key: "co_filter_import_audit_reset_operator_context",
              onClick: resetFilterImportAuditOperatorContext,
              disabled: !filterImportAuditResetArmedChecked,
            }, "Reset Operator Context"),
            h("span", {
              key: "co_filter_import_audit_reset_hint",
              className: "hint",
              style: { marginLeft: "auto", color: filterImportAuditResetArmedChecked ? "#e6cf95" : "#8eb6ca" },
            }, filterImportAuditResetArmedChecked ? "safe reset armed" : "safe reset: arm required"),
            h("span", {
              key: "co_filter_import_audit_reset_guided_hint",
              className: "hint",
              style: { flexBasis: "100%", color: "#8eb6ca" },
            }, filterImportAuditResetGuidedHint),
          ]),
          h("div", { className: "btn-row", key: "co_filter_import_audit_restore_scopes", style: { gap: "8px", flexWrap: "wrap" } }, [
            h("span", { key: "co_filter_import_audit_restore_label", className: "hint", style: { color: "#8eb6ca" } }, "restore scope:"),
            h("label", {
              key: "co_filter_import_audit_restore_query",
              className: "hint",
              style: { display: "inline-flex", alignItems: "center", gap: "4px", color: "#8eb6ca" },
            }, [
              h("input", {
                type: "checkbox",
                checked: Boolean(filterImportAuditRestoreQueryChecked),
                onChange: (e) => setFilterImportAuditRestoreQueryChecked(Boolean(e.target.checked)),
              }),
              "query",
            ]),
            h("label", {
              key: "co_filter_import_audit_restore_paging",
              className: "hint",
              style: { display: "inline-flex", alignItems: "center", gap: "4px", color: "#8eb6ca" },
            }, [
              h("input", {
                type: "checkbox",
                checked: Boolean(filterImportAuditRestorePagingChecked),
                onChange: (e) => setFilterImportAuditRestorePagingChecked(Boolean(e.target.checked)),
              }),
              "paging",
            ]),
            h("label", {
              key: "co_filter_import_audit_restore_pinned",
              className: "hint",
              style: { display: "inline-flex", alignItems: "center", gap: "4px", color: "#8eb6ca" },
            }, [
              h("input", {
                type: "checkbox",
                checked: Boolean(filterImportAuditRestorePinnedPresetChecked),
                onChange: (e) => setFilterImportAuditRestorePinnedPresetChecked(Boolean(e.target.checked)),
              }),
              "pinned",
            ]),
            h("label", {
              key: "co_filter_import_audit_restore_entry",
              className: "hint",
              style: { display: "inline-flex", alignItems: "center", gap: "4px", color: "#8eb6ca" },
            }, [
              h("input", {
                type: "checkbox",
                checked: Boolean(filterImportAuditRestoreActiveEntryChecked),
                onChange: (e) => setFilterImportAuditRestoreActiveEntryChecked(Boolean(e.target.checked)),
              }),
              "entry",
            ]),
            h("span", {
              key: "co_filter_import_audit_restore_scope_hint",
              className: "hint",
              style: { marginLeft: "auto", color: "#8eb6ca" },
            }, filterImportAuditRestoreScopeHint),
          ]),
          h("div", { className: "btn-row", key: "co_filter_import_audit_restore_presets", style: { gap: "6px", flexWrap: "wrap" } }, [
            h("span", { key: "co_filter_import_audit_restore_preset_label", className: "hint", style: { color: "#8eb6ca" } }, "restore preset:"),
            ...FILTER_IMPORT_AUDIT_RESTORE_PRESETS.map((preset) => {
              const pid = String(preset?.id || "");
              const selected = pid === activeFilterImportAuditRestorePresetId;
              return h("button", {
                className: "btn",
                key: `co_filter_import_audit_restore_preset_${pid}`,
                onClick: () => applyFilterImportAuditRestorePreset(pid),
                style: selected
                  ? { borderColor: "#4d7a93", background: "rgba(46, 86, 106, 0.42)" }
                  : undefined,
              }, String(preset?.label || pid));
            }),
            h("span", {
              key: "co_filter_import_audit_restore_preset_active",
              className: "hint",
              style: { color: "#8eb6ca" },
            }, `active:${activeFilterImportAuditRestorePresetId}`),
          ]),
          h("div", { className: "btn-row", key: "co_filter_import_audit_pin_chip_filters", style: { gap: "6px", flexWrap: "wrap" } }, [
            h("span", { key: "co_filter_import_audit_pin_chip_filter_label", className: "hint", style: { color: "#8eb6ca" } }, "chip filter:"),
            ...FILTER_IMPORT_AUDIT_PIN_CHIP_FILTER_OPTIONS.map((opt) => {
              const oid = String(opt?.id || "");
              const selected = oid === filterImportAuditPinChipFilter;
              return h("button", {
                className: "btn",
                key: `co_filter_import_audit_pin_chip_filter_${oid}`,
                onClick: () => setFilterImportAuditPinChipFilter(oid),
                style: selected
                  ? { borderColor: "#4d7a93", background: "rgba(46, 86, 106, 0.42)" }
                  : undefined,
              }, String(opt?.label || oid));
            }),
            h("span", {
              key: "co_filter_import_audit_pin_chip_filter_active",
              className: "hint",
              style: { color: "#8eb6ca" },
            }, `active:${filterImportAuditPinChipFilter}`),
            h("span", {
              key: "co_filter_import_audit_pin_operator_hint",
              className: "hint",
              style: { marginLeft: "auto", color: "#8eb6ca" },
            }, filterImportAuditPinOperatorHint),
          ]),
          h("div", { className: "btn-row", key: "co_filter_import_audit_pin_state_chips", style: { gap: "6px", flexWrap: "wrap" } }, [
            filterImportAuditPinChipVisibility.pinned ? h("span", {
              key: "co_filter_import_audit_pin_chip_pinned",
              className: "hint",
              style: {
                border: "1px solid #31576b",
                borderRadius: "999px",
                padding: "2px 7px",
                color: "#b8d5e7",
                background: "rgba(24, 50, 65, 0.42)",
              },
            }, `pin:${filterImportAuditPinnedPresetId || "-"}`) : null,
            filterImportAuditPinChipVisibility.active ? h("span", {
              key: "co_filter_import_audit_pin_chip_active",
              className: "hint",
              style: {
                border: "1px solid #31576b",
                borderRadius: "999px",
                padding: "2px 7px",
                color: filterImportAuditPinnedPresetActive ? "#b2e7bf" : "#8eb6ca",
                background: filterImportAuditPinnedPresetActive ? "rgba(21, 72, 38, 0.38)" : "rgba(20, 37, 47, 0.42)",
              },
            }, filterImportAuditPinnedPresetActive ? "pin-state:active" : "pin-state:idle") : null,
            filterImportAuditPinChipVisibility.custom && activeFilterImportAuditQueryPresetId === "custom"
              ? h("span", {
                key: "co_filter_import_audit_pin_chip_custom",
                className: "hint",
                style: {
                  border: "1px solid #5c4f2a",
                  borderRadius: "999px",
                  padding: "2px 7px",
                  color: "#e4cf98",
                  background: "rgba(79, 63, 19, 0.33)",
                },
              }, "active:custom")
              : null,
            filterImportAuditPinChipVisibility.shortcut ? h("span", {
              key: "co_filter_import_audit_pin_chip_shortcut",
              className: "hint",
              style: {
                border: "1px solid #31576b",
                borderRadius: "999px",
                padding: "2px 7px",
                color: "#8eb6ca",
                background: "rgba(20, 37, 47, 0.42)",
              },
            }, `shortcut:${normalizeShortcutToken(shortcutBindings.audit_pin_toggle) || "-"}`) : null,
          ]),
          h("div", { className: "btn-row", key: "co_filter_import_audit_window", style: { gap: "4px" } }, [
            h("label", { key: "co_filter_import_audit_row_cap_label", className: "hint", style: { color: "#8eb6ca" } }, "rows/page:"),
            h("select", {
              className: "select",
              key: "co_filter_import_audit_row_cap",
              value: String(filterImportAuditRowCap),
              onChange: (e) => setFilterImportAuditRowCapText(String(e.target.value || CONTRACT_OVERLAY_DEFAULT_PREFS.filterImportAuditRowCap)),
              style: { minWidth: "88px", padding: "5px 7px", fontSize: "11px" },
            }, FILTER_IMPORT_AUDIT_ROW_CAP_OPTIONS.map((opt) =>
              h("option", { value: opt, key: `co_filter_import_audit_row_cap_opt_${opt}` }, opt)
            )),
            h("button", {
              className: "btn",
              key: "co_filter_import_audit_top",
              disabled: filterImportAuditRowOffset <= 0,
              onClick: () => setFilterImportAuditRowOffset(0),
            }, "Top"),
            h("button", {
              className: "btn",
              key: "co_filter_import_audit_prev",
              disabled: filterImportAuditRowOffset <= 0,
              onClick: () => setFilterImportAuditRowOffset((prev) => Math.max(0, Number(prev || 0) - filterImportAuditRowCap)),
            }, "Prev"),
            h("button", {
              className: "btn",
              key: "co_filter_import_audit_next",
              disabled: filterImportAuditRowOffset >= filterImportAuditMaxOffset,
              onClick: () => setFilterImportAuditRowOffset((prev) => Math.min(filterImportAuditMaxOffset, Number(prev || 0) + filterImportAuditRowCap)),
            }, "Next"),
            h("span", {
              key: "co_filter_import_audit_window_hint",
              className: "hint",
              style: { marginLeft: "auto", color: "#8eb6ca" },
            }, `window ${filterImportAuditRowsFiltered.length === 0 ? 0 : filterImportAuditRowOffset + 1}-${filterImportAuditRowEnd}/${filterImportAuditRowsFiltered.length}`),
          ]),
          filterImportAuditRowsVisible.length > 0
            ? h("div", { key: "co_filter_import_audit_rows", style: { display: "grid", rowGap: "3px" } },
              filterImportAuditRowsVisible.map((entry, localIdx) => {
                const idx = filterImportAuditRowOffset + localIdx;
                const entryId = String(entry?.id || `idx_${idx}`);
                const selected = entryId === String(activeFilterImportAuditId || "");
                const namesPreview = compactNameList(entry?.selected_names, 3).join(", ");
                return h("button", {
                  className: "btn",
                  key: `co_filter_import_audit_row_${idx}`,
                  onClick: () => setActiveFilterImportAuditId(entryId),
                  style: {
                    textAlign: "left",
                    justifyContent: "flex-start",
                    fontSize: "10px",
                    minHeight: 0,
                    borderColor: selected ? "#4d7a93" : undefined,
                    background: selected ? "rgba(46, 86, 106, 0.42)" : undefined,
                  },
                }, [
                  `${String(entry?.timestamp_iso || "-")} | ${String(entry?.kind || "import")} | mode:${String(entry?.mode || "-")} | `,
                  `sel:${Number(entry?.selected_count || 0)} +${Number(entry?.added_count || 0)} `,
                  `~${Number(entry?.changed_count || 0)} -${Number(entry?.removed_count || 0)} `,
                  namesPreview ? `| names:${namesPreview} ` : "",
                  entry?.note ? `| ${String(entry.note)}` : "",
                ].join(""));
              })
            )
            : h("div", {
              key: "co_filter_import_audit_empty",
              className: "hint",
              style: { color: "#8eb6ca", padding: "2px 0 4px 2px" },
            }, "no audit rows matched current filters"),
          h("textarea", {
            className: "textarea",
            key: "co_filter_import_audit_detail",
            value: filterImportAuditDetailText,
            readOnly: true,
            style: {
              flexBasis: "100%",
              minHeight: "120px",
              padding: "6px 7px",
              fontSize: "10px",
              lineHeight: "1.35",
            },
          }),
        ])
        : null,
      filterTransferStatus
        ? h("span", {
          key: "co_filter_transfer_status",
          className: "hint",
          style: { marginLeft: "auto", color: "#8eb6ca" },
        }, filterTransferStatus)
        : null,
    ]),
    h("div", {
      className: "contract-overlay-filter",
      key: "co_filter_summary",
      style: { flexWrap: "wrap", rowGap: "6px", borderTop: "1px dashed #27485a" },
    }, [
      h("label", { key: "co_filter_summary_label" }, "active filters:"),
      activeFilterTokens.length === 0
        ? h("span", { key: "co_filter_summary_none", className: "hint", style: { color: "#8eb6ca" } }, "(none)")
        : activeFilterTokens.map((token, idx) =>
          h("span", {
            key: `co_filter_token_${idx}`,
            className: "hint",
            style: {
              display: "inline-flex",
              alignItems: "center",
              border: "1px solid #31576b",
              borderRadius: "999px",
              padding: "2px 7px",
              background: "rgba(24, 50, 65, 0.42)",
              color: "#b8d5e7",
            },
          }, token)
        ),
      h("button", {
        className: "btn",
        key: "co_reset_filters",
        onClick: resetOverlayFilters,
        disabled: activeFilterTokens.length === 0,
      }, "Reset Filters"),
    ]),
    h("div", {
      className: "contract-overlay-filter",
      key: "co_shortcut_profile_cfg",
      style: { flexWrap: "wrap", rowGap: "6px" },
    }, [
      h("label", { key: "co_shortcut_profile_label" }, "shortcut profile:"),
      h("select", {
        className: "select",
        key: "co_shortcut_profile_select",
        value: activeShortcutProfile,
        onChange: (e) => setActiveShortcutProfile(String(e.target.value || "default")),
      }, shortcutProfileOptions.map((name) =>
        h("option", { value: name, key: `co_shortcut_profile_opt_${name}` }, name)
      )),
      h("button", {
        className: "btn",
        key: "co_shortcut_profile_apply",
        onClick: applyActiveShortcutProfile,
      }, "Load Profile"),
      h("button", {
        className: "btn",
        key: "co_shortcut_reset_defaults",
        onClick: resetShortcutBindingsToDefaults,
      }, "Reset Keys"),
      h("label", { key: "co_shortcut_save_label", style: { marginLeft: "8px" } }, "save as:"),
      h("input", {
        className: "input",
        key: "co_shortcut_profile_draft",
        value: shortcutProfileDraft,
        onChange: (e) => setShortcutProfileDraft(String(e.target.value || "")),
        placeholder: "custom_profile",
        style: { minWidth: "140px", maxWidth: "180px", padding: "5px 7px", fontSize: "11px" },
      }),
      h("button", {
        className: "btn",
        key: "co_shortcut_profile_save",
        onClick: saveCurrentShortcutProfile,
        disabled: !normalizedShortcutProfileDraft,
      }, "Save Profile"),
      h("button", {
        className: "btn",
        key: "co_shortcut_profile_delete",
        onClick: deleteActiveShortcutProfile,
        disabled: activeShortcutIsBuiltin,
      }, "Delete Profile"),
      h("span", {
        key: "co_shortcut_profile_builtin_tag",
        className: "hint",
        style: { marginLeft: "auto", color: activeShortcutIsBuiltin ? "#8eb6ca" : "#f0b33a" },
      }, activeShortcutIsBuiltin ? "profile: built-in" : "profile: custom"),
    ]),
    h("div", {
      className: "contract-overlay-filter",
      key: "co_shortcut_transfer_cfg",
      style: { flexWrap: "wrap", rowGap: "6px" },
    }, [
      h("label", { key: "co_shortcut_transfer_label" }, "profile transfer:"),
      h("button", {
        className: "btn",
        key: "co_shortcut_export_profiles",
        onClick: exportShortcutProfilesToJson,
      }, "Export Profiles"),
      h("button", {
        className: "btn",
        key: "co_shortcut_copy_profiles",
        onClick: copyShortcutProfilesJson,
      }, "Copy Profiles"),
      h("button", {
        className: "btn",
        key: "co_shortcut_load_json",
        onClick: triggerShortcutImportFilePick,
      }, "Load JSON"),
      h("button", {
        className: "btn",
        key: "co_shortcut_import_profiles",
        onClick: importShortcutProfilesFromText,
        disabled: String(shortcutTransferText || "").trim().length === 0,
      }, "Import Profiles"),
      h("input", {
        type: "file",
        key: "co_shortcut_import_file",
        ref: shortcutImportFileInputRef,
        accept: ".json,application/json",
        onChange: handleShortcutImportFileChange,
        style: { display: "none" },
      }),
      h("textarea", {
        className: "textarea",
        key: "co_shortcut_transfer_text",
        value: shortcutTransferText,
        onChange: (e) => setShortcutTransferText(String(e.target.value || "")),
        placeholder: "{\"profiles\": {\"my_team\": {\"toggle_help\": \"h\"}}}",
        style: {
          flexBasis: "100%",
          minHeight: "74px",
          padding: "6px 7px",
          fontSize: "10px",
          lineHeight: "1.35",
        },
      }),
      shortcutTransferStatus
        ? h("span", {
          key: "co_shortcut_transfer_status",
          className: "hint",
          style: { marginLeft: "auto", color: "#8eb6ca" },
        }, shortcutTransferStatus)
        : null,
    ]),
    h("div", {
      className: "contract-overlay-filter",
      key: "co_shortcut_remap_grid",
      style: { flexWrap: "wrap", rowGap: "6px", alignItems: "stretch" },
    }, SHORTCUT_ACTION_DEFS.map((def) => {
      const actionId = String(def.id || "");
      const value = normalizeShortcutToken(shortcutBindings[actionId]);
      const hasConflict = conflictActionSet.has(actionId);
      return h("div", {
        key: `co_shortcut_row_${actionId}`,
        style: {
          display: "inline-flex",
          alignItems: "center",
          gap: "6px",
          border: hasConflict ? "1px solid #c28c2f" : "1px solid #27485a",
          borderRadius: "6px",
          background: hasConflict ? "rgba(92, 65, 20, 0.32)" : "rgba(9, 18, 24, 0.72)",
          padding: "4px 6px",
        },
      }, [
        h("label", {
          key: `co_shortcut_row_lbl_${actionId}`,
          className: "hint",
          style: { color: "#9bc3d8", whiteSpace: "nowrap" },
        }, `${String(def.label || actionId)}:`),
        h("input", {
          className: "input",
          key: `co_shortcut_row_in_${actionId}`,
          value,
          onChange: (e) => updateShortcutBinding(actionId, e.target.value),
          maxLength: 1,
          style: {
            width: "34px",
            textAlign: "center",
            padding: "4px 5px",
            fontSize: "11px",
          },
        }),
        hasConflict
          ? h("span", {
            key: `co_shortcut_row_conflict_${actionId}`,
            className: "hint",
            style: { color: "#ffd08b" },
          }, "dup")
          : null,
      ]);
    })),
    shortcutConflictText
      ? h("div", {
        className: "hint",
        key: "co_shortcuts_conflict_hint",
        style: { margin: "4px 2px 2px 2px", color: "#ffd08b" },
      }, `Shortcut conflict: ${shortcutConflictText} (first mapping wins).`)
      : null,
    h("div", {
      className: "contract-overlay-filter",
      key: "co_detail_fields_cfg",
      style: { flexWrap: "wrap", rowGap: "6px" },
    }, [
      h("label", { key: "co_detail_fields_label" }, "detail fields:"),
      ...DETAIL_FIELD_DEFS.map((def) => {
        const fieldId = String(def.id || "");
        if (!fieldId) return null;
        const checked = Boolean(detailFieldStates[fieldId]);
        return h("label", {
          key: `co_detail_field_toggle_${fieldId}`,
          style: {
            display: "inline-flex",
            alignItems: "center",
            gap: "4px",
            border: checked ? "1px solid #3a6277" : "1px solid #27485a",
            borderRadius: "6px",
            padding: "3px 6px",
            background: checked ? "rgba(34, 68, 86, 0.35)" : "rgba(9, 18, 24, 0.72)",
          },
        }, [
          h("input", {
            type: "checkbox",
            checked,
            onChange: () => toggleDetailField(fieldId),
          }),
          String(def.label || fieldId),
        ]);
      }).filter(Boolean),
      h("button", {
        className: "btn",
        key: "co_detail_fields_core",
        onClick: () => applyDetailFieldPreset("core"),
      }, "Core Fields"),
      h("button", {
        className: "btn",
        key: "co_detail_fields_all",
        onClick: () => applyDetailFieldPreset("all"),
      }, "All Fields"),
      h("span", {
        key: "co_detail_fields_count",
        className: "hint",
        style: { marginLeft: "auto", color: "#8eb6ca" },
      }, `selected ${detailFieldSelectedCount}/${DETAIL_FIELD_DEFS.length}`),
    ]),
    detailCopyStatus
      ? h("div", {
        className: "hint",
        key: "co_detail_copy_status",
        style: { margin: "2px 2px 4px 2px", color: "#8eb6ca" },
      }, `detail_copy: ${detailCopyStatus}`)
      : null,
    showShortcutHelp
      ? h(
        "div",
        {
          className: "hint",
          key: "co_shortcuts_hint",
          style: { margin: "6px 2px 8px 2px", color: "#8eb6ca" },
        },
        `Shortcuts: ${shortcutHintText}.`
      )
      : null,
    h("div", { className: "contract-overlay-bd", key: "co_bd" }, filteredRows.length === 0
      ? h("pre", { className: "result-box", key: "co_empty" }, "no contract events yet")
      : visibleRows.map((row, localIdx) =>
        (() => {
          const idx = rowWindowOffset + localIdx;
          const rowExpandedKey = buildContractRowKey(row);
          const rowDetailsExpanded = expandedRowKeys.has(rowExpandedKey);
          const rowDetailText = rowDetailsExpanded ? formatRowDetailText(row) : "";
          const runId = String(row?.graph_run_id || "").trim();
          const severity = classifyContractSeverity(row);
          const badgeText = severityLabel(severity);
          const policyTag = getPolicyCorrelationTag(row, policyByRun);
          const failureRuleTags = getFailureRuleTags(row, policyByRun);
          const hasPolicyCorrelation = Boolean(policyTag);
          const className = compactMode
            ? `contract-overlay-row compact contract-sev-${severity}`
            : `contract-overlay-row contract-sev-${severity}`;
          if (compactMode) {
            return h("div", { className, key: `co_row_${idx}` }, [
              h("div", { className: "contract-overlay-row-compact", key: `co_row_compact_${idx}` }, [
                h("span", { className: `contract-sev-badge ${severity}`, key: `co_row_badge_${idx}` }, badgeText),
                policyTag
                  ? h("span", { className: `contract-policy-tag ${String(policyTag).includes("HOLD") ? "hold" : "adopt"}`, key: `co_row_policy_compact_${idx}` }, policyTag)
                  : null,
                ...failureRuleTags.map((rule, ridx) =>
                  h("span", { className: "contract-failure-rule-badge", key: `co_row_rule_compact_${idx}_${ridx}` }, rule)
                ),
                `${formatTimeOfDay(row?.timestamp_ms)} | ${String(row?.event_source || "-")} | run=${String(row?.graph_run_id || "-")} | `,
                `d=${formatSigned(row?.delta?.unique_warning_count)}/${formatSigned(row?.delta?.attempt_count_total)}`,
                runId
                  ? h("button", {
                      className: "btn contract-open-run-btn",
                      key: `co_row_open_compact_${idx}`,
                      onClick: () => {
                        setPinnedRunId(runId);
                        runOpenHandler(runId);
                      },
                    }, "Open Run")
                  : null,
                runId && hasPolicyCorrelation
                  ? h("button", {
                      className: "btn contract-open-gate-btn",
                      key: `co_row_gate_compact_${idx}`,
                      onClick: () => gateOpenHandler(row, gateLookupOptions),
                    }, "Open Gate")
                  : null,
                h("button", {
                  className: "btn contract-row-detail-btn",
                  key: `co_row_copy_compact_${idx}`,
                  onClick: () => copySingleRowDetails(row, idx),
                }, "Copy"),
                h("button", {
                  className: "btn contract-row-detail-btn",
                  key: `co_row_detail_compact_${idx}`,
                  onClick: () => toggleRowExpanded(rowExpandedKey),
                }, rowDetailsExpanded ? "Hide" : "Details"),
              ]),
              rowDetailsExpanded
                ? h("pre", {
                  className: "contract-overlay-row-detail",
                  key: `co_row_detail_block_compact_${idx}`,
                }, rowDetailText)
                : null,
            ]);
          }
          return h("div", { className, key: `co_row_${idx}` }, [
            h("div", { className: "contract-overlay-row-hd", key: `co_row_hd_${idx}` }, [
              h("span", { className: `contract-sev-badge ${severity}`, key: `co_row_badge_${idx}` }, badgeText),
              policyTag
                ? h("span", { className: `contract-policy-tag ${String(policyTag).includes("HOLD") ? "hold" : "adopt"}`, key: `co_row_policy_${idx}` }, policyTag)
                : null,
              ...failureRuleTags.map((rule, ridx) =>
                h("span", { className: "contract-failure-rule-badge", key: `co_row_rule_${idx}_${ridx}` }, rule)
              ),
              `${formatTimeOfDay(row?.timestamp_ms)} | ${String(row?.event_source || "-")} | run=${String(row?.graph_run_id || "-")}`,
            ]),
            h("div", { className: "contract-overlay-row-kpi", key: `co_row_kpi_${idx}` }, [
              `delta(unique/attempt): ${formatSigned(row?.delta?.unique_warning_count)}/${formatSigned(row?.delta?.attempt_count_total)} | `,
              `total(unique/attempt): ${Number(row?.snapshot?.unique_warning_count || 0)}/${Number(row?.snapshot?.attempt_count_total || 0)}`,
            ]),
            runId
              ? h("div", { className: "contract-overlay-row-actions", key: `co_row_actions_${idx}` }, [
                  h("button", {
                    key: `co_row_open_${idx}`,
                    className: "btn contract-open-run-btn",
                    onClick: () => {
                      setPinnedRunId(runId);
                      runOpenHandler(runId);
                    },
                  }, "Open Run"),
                  hasPolicyCorrelation
                    ? h("button", {
                        key: `co_row_gate_${idx}`,
                        className: "btn contract-open-gate-btn",
                        onClick: () => gateOpenHandler(row, gateLookupOptions),
                      }, "Open Gate")
                    : null,
                  h("button", {
                    key: `co_row_copy_${idx}`,
                    className: "btn contract-row-detail-btn",
                    onClick: () => copySingleRowDetails(row, idx),
                  }, "Copy"),
                  h("button", {
                    key: `co_row_detail_${idx}`,
                    className: "btn contract-row-detail-btn",
                    onClick: () => toggleRowExpanded(rowExpandedKey),
                  }, rowDetailsExpanded ? "Hide" : "Details"),
                ])
              : h("div", { className: "contract-overlay-row-actions", key: `co_row_actions_${idx}` }, [
                  h("button", {
                    key: `co_row_copy_only_${idx}`,
                    className: "btn contract-row-detail-btn",
                    onClick: () => copySingleRowDetails(row, idx),
                  }, "Copy"),
                  h("button", {
                    key: `co_row_detail_only_${idx}`,
                    className: "btn contract-row-detail-btn",
                    onClick: () => toggleRowExpanded(rowExpandedKey),
                  }, rowDetailsExpanded ? "Hide" : "Details"),
                ]),
            rowDetailsExpanded
              ? h("pre", {
                className: "contract-overlay-row-detail",
                key: `co_row_detail_block_${idx}`,
              }, rowDetailText)
              : null,
          ]);
        })()
      )),
  ]);
}

export function GraphCanvasPanel({
  nodes,
  edges,
  onNodesChange,
  onEdgesChange,
  onConnect,
  setSelectedNodeId,
}) {
  return h("section", { className: "panel panel-center", key: "center" }, [
    h("div", { className: "panel-hd", key: "chd" }, "Graph Canvas"),
    h("div", { className: "panel-bd", style: { padding: "8px" }, key: "cbd" }, [
      h("div", { className: "flow-wrap", style: { height: "100%" }, key: "flow" }, [
        h(ReactFlow, {
          nodes,
          edges,
          onNodesChange,
          onEdgesChange,
          onConnect,
          fitView: true,
          onNodeClick: (_, node) => setSelectedNodeId(String(node.id)),
        }, [
          h(Background, { key: "bg", color: "#2b4f62", gap: 22, size: 1 }),
          h(MiniMap, { key: "mm", pannable: true, zoomable: true, style: { background: "#0f1d27" } }),
          h(Controls, { key: "ctl", showInteractive: false }),
        ]),
      ]),
    ]),
  ]);
}

export function NodeInspectorPanel({
  selectedNode,
  selectedNodeParamsText,
  setSelectedNodeParamsText,
  applySelectedNodeParams,
  runGraphValidation,
  validationText,
  graphRunText,
  gateResultText,
  graphRunSummary,
  compareGraphRunId,
  setCompareGraphRunId,
  compareRunStatusText,
  compareGraphRunSummary,
  loadCompareGraphRunById,
  clearCompareGraphRun,
  pinCurrentGraphRunAsCompare,
  baselineId,
  pinBaselineFromGraphRun,
  runPolicyGateForGraphRun,
  runDecisionRegressionSession,
  runLowVsCurrentTrackCompare,
  trackCompareBaselinePresetId,
  setTrackCompareBaselinePresetId,
  trackCompareTargetPresetId,
  setTrackCompareTargetPresetId,
  trackComparePresetOptions,
  trackCompareQuickPairOptions,
  applyTrackCompareQuickPair,
  trackCompareSelectedPairSummaryText,
  trackCompareSelectedPairForecastText,
  runPresetPairTrackCompare,
  exportGateReport,
  exportDecisionRegressionSession,
  exportDecisionBriefMd,
  currentTrackLabel,
  compareTrackLabel,
  trackCompareGuideText,
  decisionSummaryText,
  decisionOpsStatusText,
  trackCompareRunnerStatusText,
  lastRegressionSession,
  lastRegressionExport,
  contractDebugText,
}) {
  return h("section", { className: "panel panel-right", key: "right" }, [
    h("div", { className: "panel-hd", key: "rhd" }, "Node Inspector"),
    h("div", { className: "panel-bd", key: "rbd" }, [
      h("div", { className: "field", key: "selnode" }, [
        h("label", { className: "label", key: "lbls" }, "Selected Node"),
        h("input", {
          className: "input",
          readOnly: true,
          value: selectedNode ? `${selectedNode.data.nodeType} | ${selectedNode.id}` : "(none)",
        }),
      ]),
      h("div", { className: "field", key: "params" }, [
        h("label", { className: "label", key: "lblp" }, "Node Params (JSON)"),
        h("textarea", {
          className: "textarea",
          value: selectedNodeParamsText,
          onChange: (e) => setSelectedNodeParamsText(e.target.value),
          placeholder: "{}",
        }),
      ]),
      h("div", { className: "btn-row-3", key: "btns2" }, [
        h("button", { className: "btn", onClick: applySelectedNodeParams, key: "b1" }, "Apply Params"),
        h("button", {
          className: "btn",
          onClick: () => setSelectedNodeParamsText("{}"),
          key: "b2",
        }, "Reset JSON"),
        h("button", { className: "btn", onClick: runGraphValidation, key: "b3" }, "Re-Validate"),
      ]),
      h("div", { className: "field", key: "result" }, [
        h("label", { className: "label", key: "lblr" }, "Validation Result"),
        h("pre", { className: "result-box", key: "box" }, validationText),
      ]),
      h("div", { className: "field", key: "runresult" }, [
        h("label", { className: "label", key: "lblrr" }, "Graph Run Result"),
        h("pre", { className: "result-box", key: "runbox" }, graphRunText),
      ]),
      h("div", { className: "field", key: "gateresult" }, [
        h("label", { className: "label", key: "lblgr" }, "Policy Gate Result"),
        h("pre", { className: "result-box", key: "gatebox" }, gateResultText),
      ]),
      h(ContractDiagnosticsPanel, {
        key: "contract_diagnostics_panel",
        contractDebugText,
      }),
      h(DecisionPane, {
        key: "decision_pane_v1",
        baselineId,
        compareGraphRunId,
        setCompareGraphRunId,
        loadCompareGraphRunById,
        clearCompareGraphRun,
        pinCurrentGraphRunAsCompare,
        pinBaselineFromGraphRun,
        runPolicyGateForGraphRun,
        runDecisionRegressionSession,
        runLowVsCurrentTrackCompare,
        trackCompareBaselinePresetId,
        setTrackCompareBaselinePresetId,
        trackCompareTargetPresetId,
        setTrackCompareTargetPresetId,
        trackComparePresetOptions,
        trackCompareQuickPairOptions,
        applyTrackCompareQuickPair,
        trackCompareSelectedPairSummaryText,
        trackCompareSelectedPairForecastText,
        runPresetPairTrackCompare,
        exportGateReport,
        exportDecisionRegressionSession,
        exportDecisionBriefMd,
        currentTrackLabel,
        compareTrackLabel,
        trackCompareGuideText,
        decisionSummaryText,
        decisionOpsStatusText,
        trackCompareRunnerStatusText,
        compareRunStatusText,
        lastRegressionSession,
        lastRegressionExport,
      }),
      h("div", { className: "field", key: "artifactinspect" }, [
        h("label", { className: "label", key: "lblai" }, "Artifact Inspector"),
        h(ArtifactInspectorPanel, {
          key: "artifact_inspector_v2",
          graphRunSummary,
          compareGraphRunSummary,
          compareRunStatusText,
        }),
      ]),
    ]),
  ]);
}
