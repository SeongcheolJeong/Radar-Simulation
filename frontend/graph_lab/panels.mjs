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

function isEditableElementTarget(target) {
  const t = target && typeof target === "object" ? target : null;
  if (!t) return false;
  if (Boolean(t.isContentEditable)) return true;
  const tag = String(t.tagName || "").toLowerCase();
  return tag === "input" || tag === "textarea" || tag === "select";
}

function renderArtifactInspector(graphRunSummary) {
  if (!graphRunSummary) {
    return h("pre", { className: "result-box", key: "aibox_empty" }, "run graph first to inspect artifacts");
  }
  const runtimeContract = graphRunSummary?.runtime_contract_diagnostics || null;
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
      ).slice(0, 16).map((row, idx) =>
        h(
          "div",
          { key: `tr_${idx}` },
          `- #${Number(idx)} ${String(row?.node_type || "-")} (${String(
            row?.node_id || "-"
          )}) | status=${String(row?.status || "-")} | contract=${String(
            row?.output_contract || "-"
          )}`
        )
      )),
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

export function TopBar({ statusTone, statusText, nodeCount, edgeCount }) {
  return h("header", { className: "topbar", key: "hd" }, [
    h("div", { className: "brand", key: "b1" }, [
      h("span", { className: "brand-dot", key: "dot" }),
      h("div", { key: "txt" }, [
        h("div", { className: "brand-title", key: "t1" }, "Radar Graph Lab"),
        h("div", { className: "brand-sub", key: "t2" }, "ReactFlow Simulink-Style Workspace"),
      ]),
    ]),
    h("div", { className: "top-actions", key: "b2" }, [
      h("span", { className: `stat ${statusTone}`, key: "s1" }, statusText),
      h("span", { className: "stat", key: "s2" }, `nodes ${nodeCount} / edges ${edgeCount}`),
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

  return h("section", { className: "panel", key: "left" }, [
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
      h("div", { className: "btn-row", key: "gatebtns" }, [
        h("button", { className: "btn", onClick: pinBaselineFromGraphRun, key: "pinb" }, "Pin Baseline"),
        h("button", { className: "btn", onClick: runPolicyGateForGraphRun, key: "runpg" }, "Policy Gate"),
      ]),
      h("button", { className: "btn", onClick: exportGateReport, key: "xgate" }, "Export Gate Report (.md)"),
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
  const quickTelemetryDrilldownImportHasChangedOverwrite = React.useMemo(
    () => quickTelemetryDrilldownImportRows.some((row) => row.conflict !== "new" && Boolean(row.changed)),
    [quickTelemetryDrilldownImportRows]
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
    quickTelemetryDrilldownImportRows.forEach((row) => {
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
    const builtinTag = changedBuiltinOverwrite > 0 ? `, built-in overwrite ${changedBuiltinOverwrite}` : "";
    return [
      `drilldown profile preview: total ${quickTelemetryDrilldownImportRows.length}`,
      `new ${newCount}`,
      `overwrite ${overwriteCount}`,
      `changed ${changedOverwrite}${builtinTag}`,
      `unchanged ${unchangedCount}`,
    ].join(", ");
  }, [
    parsedQuickTelemetryDrilldownProfileImportPayload.empty,
    parsedQuickTelemetryDrilldownProfileImportPayload.error,
    quickTelemetryDrilldownImportRows,
  ]);
  const quickTelemetryDrilldownImportPreviewRows = React.useMemo(
    () => quickTelemetryDrilldownImportRows.slice(0, 8),
    [quickTelemetryDrilldownImportRows]
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
      ? Object.keys(imported).sort((a, b) => String(a).localeCompare(String(b)))
      : [];
    if (names.length === 0) {
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
      ...imported,
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
    quickTelemetryDrilldownImportRows.forEach((row) => {
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
    quickTelemetryDrilldownImportRows,
    quickTelemetryDrilldownProfileDraft,
    quickTelemetryDrilldownProfiles,
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
              style: { marginLeft: "auto", color: "#8eb6ca" },
            }, quickTelemetryDrilldownImportPreview),
            h("span", {
              key: "co_filter_import_audit_quick_telemetry_profile_import_rollback_hint",
              className: "hint",
              style: { flexBasis: "100%", color: "#8eb6ca" },
            }, quickTelemetryDrilldownImportRollbackHint),
            ...quickTelemetryDrilldownImportPreviewRows.map((row, idx) => h("span", {
              key: `co_filter_import_audit_quick_telemetry_profile_import_preview_row_${idx}`,
              className: "hint",
              style: {
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
            }, `${String(row.name || "-")} (${String(row.conflict || "-")}${row.changed ? ", changed" : ", same"})`)),
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
  return h("section", { className: "panel", key: "center" }, [
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
  contractDebugText,
}) {
  return h("section", { className: "panel", key: "right" }, [
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
      h("div", { className: "field", key: "contractdiagauto" }, [
        h("label", { className: "label", key: "lblcda" }, "Contract Diagnostics (Auto)"),
        h("pre", { className: "result-box", key: "contractboxauto" }, String(contractDebugText || "-")),
      ]),
      h("div", { className: "field", key: "artifactinspect" }, [
        h("label", { className: "label", key: "lblai" }, "Artifact Inspector"),
        renderArtifactInspector(graphRunSummary),
      ]),
    ]),
  ]);
}
