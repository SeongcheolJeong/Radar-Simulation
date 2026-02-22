const CONTRACT_WARNED = new Set();
const CONTRACT_WARNING_ATTEMPTS = new Map();
const CONTRACT_WARNING_UNIQUE_BY_SCOPE = new Map();
const CONTRACT_WARNING_ATTEMPTS_BY_SCOPE = new Map();
let LAST_WARNING = null;
const NOOP = () => {};

function warnOnce(scope, message) {
  const key = `${scope}:${message}`;
  CONTRACT_WARNING_ATTEMPTS.set(key, Number(CONTRACT_WARNING_ATTEMPTS.get(key) || 0) + 1);
  CONTRACT_WARNING_ATTEMPTS_BY_SCOPE.set(
    scope,
    Number(CONTRACT_WARNING_ATTEMPTS_BY_SCOPE.get(scope) || 0) + 1
  );
  if (CONTRACT_WARNED.has(key)) return;
  CONTRACT_WARNED.add(key);
  CONTRACT_WARNING_UNIQUE_BY_SCOPE.set(
    scope,
    Number(CONTRACT_WARNING_UNIQUE_BY_SCOPE.get(scope) || 0) + 1
  );
  LAST_WARNING = {
    key,
    scope,
    message: String(message),
    timestamp_ms: Date.now(),
  };
  if (typeof console !== "undefined" && typeof console.warn === "function") {
    console.warn(`[contract:${scope}] ${message}`);
  }
}

function asObject(value) {
  if (value && typeof value === "object" && !Array.isArray(value)) return value;
  return {};
}

function asNullableObject(scope, value, label) {
  if (value === null || value === undefined) return null;
  if (value && typeof value === "object" && !Array.isArray(value)) return value;
  warnOnce(scope, `expected object for "${label}"`);
  return null;
}

function readObjectSection(scope, root, key) {
  const value = root[key];
  if (value && typeof value === "object" && !Array.isArray(value)) return value;
  if (value !== undefined) {
    warnOnce(scope, `expected object section "${key}"`);
  }
  return {};
}

function readString(scope, root, key, fallback) {
  const value = root[key];
  if (typeof value === "string") return value;
  if (value === undefined || value === null) return String(fallback);
  warnOnce(scope, `expected string for "${key}"`);
  return String(fallback);
}

function readBoolean(scope, root, key, fallback) {
  const value = root[key];
  if (typeof value === "boolean") return value;
  if (value === undefined || value === null) return Boolean(fallback);
  warnOnce(scope, `expected boolean for "${key}"`);
  return Boolean(fallback);
}

function readNumber(scope, root, key, fallback) {
  const value = root[key];
  if (typeof value === "number" && Number.isFinite(value)) return Number(value);
  if (value === undefined || value === null || value === "") return Number(fallback);
  const parsed = Number(value);
  if (Number.isFinite(parsed)) return parsed;
  warnOnce(scope, `expected number for "${key}"`);
  return Number(fallback);
}

function readArray(scope, root, key, fallback) {
  const value = root[key];
  if (Array.isArray(value)) return value;
  if (value === undefined || value === null) return fallback.slice();
  warnOnce(scope, `expected array for "${key}"`);
  return fallback.slice();
}

function readFunction(scope, root, key) {
  const value = root[key];
  if (typeof value === "function") return value;
  if (value !== undefined) {
    warnOnce(scope, `expected function for "${key}"`);
  } else {
    warnOnce(scope, `missing function "${key}"`);
  }
  return NOOP;
}

function readOptionalFunction(scope, root, key) {
  const value = root[key];
  if (typeof value === "function") return value;
  if (value === undefined || value === null) return NOOP;
  warnOnce(scope, `expected function for "${key}"`);
  return NOOP;
}

export const GRAPH_INPUTS_PANEL_MODEL_CONTRACT = "graph_inputs_panel_model_v1";
export const GRAPH_RUN_OPS_OPTIONS_CONTRACT = "graph_run_ops_options_v1";
export const GATE_OPS_OPTIONS_CONTRACT = "gate_ops_options_v1";

export function getContractWarningSnapshot() {
  const uniqueWarningCount = Number(CONTRACT_WARNED.size || 0);
  const attemptCountTotal = Array.from(CONTRACT_WARNING_ATTEMPTS.values()).reduce(
    (acc, v) => acc + Number(v || 0),
    0
  );
  const byScope = Array.from(CONTRACT_WARNING_ATTEMPTS_BY_SCOPE.entries())
    .map(([scope, attempts]) => ({
      scope,
      attempts: Number(attempts || 0),
      unique: Number(CONTRACT_WARNING_UNIQUE_BY_SCOPE.get(scope) || 0),
    }))
    .sort((a, b) => {
      const d1 = Number(b.attempts || 0) - Number(a.attempts || 0);
      if (d1 !== 0) return d1;
      return String(a.scope).localeCompare(String(b.scope));
    });
  return {
    contract_debug_version: "contract_warning_debug_v1",
    unique_warning_count: uniqueWarningCount,
    attempt_count_total: Number(attemptCountTotal || 0),
    by_scope: byScope,
    last_warning: LAST_WARNING ? { ...LAST_WARNING } : null,
  };
}

export function resetContractWarnings() {
  CONTRACT_WARNED.clear();
  CONTRACT_WARNING_ATTEMPTS.clear();
  CONTRACT_WARNING_UNIQUE_BY_SCOPE.clear();
  CONTRACT_WARNING_ATTEMPTS_BY_SCOPE.clear();
  LAST_WARNING = null;
}

/**
 * @typedef {Object} GraphInputsPanelValues
 * @property {string} apiBase
 * @property {string} graphId
 * @property {string} sceneJsonPath
 * @property {string} baselineId
 * @property {string} profile
 * @property {string} runMode
 * @property {boolean} autoPollAsyncRun
 * @property {string} pollIntervalMsText
 * @property {string} pollStateText
 * @property {boolean} pollingActive
 * @property {Array<any>} templates
 * @property {string} lastGraphRunId
 * @property {string} contractDebugText
 * @property {boolean} contractOverlayEnabled
 * @property {number} contractTimelineCount
 */

/**
 * @typedef {Object} GraphInputsPanelModel
 * @property {string} __contract_version
 * @property {GraphInputsPanelValues} values
 * @property {Object<string, Function>} setters
 * @property {Object<string, Function>} templateActions
 * @property {Object<string, Function>} graphActions
 * @property {Object<string, Function>} runActions
 * @property {Object<string, Function>} gateActions
 * @property {Object<string, Function>} contractActions
 */

/**
 * Normalize GraphInputsPanel binding object.
 * Returns a safe model shape even when parts are missing.
 *
 * @param {any} rawModel
 * @returns {GraphInputsPanelModel}
 */
export function normalizeGraphInputsPanelModel(rawModel) {
  const scope = "graph-inputs-panel-model";
  const root = asObject(rawModel);
  const values = readObjectSection(scope, root, "values");
  const setters = readObjectSection(scope, root, "setters");
  const templateActions = readObjectSection(scope, root, "templateActions");
  const graphActions = readObjectSection(scope, root, "graphActions");
  const runActions = readObjectSection(scope, root, "runActions");
  const gateActions = readObjectSection(scope, root, "gateActions");
  const contractActions = readObjectSection(scope, root, "contractActions");

  return {
    __contract_version: GRAPH_INPUTS_PANEL_MODEL_CONTRACT,
    values: {
      apiBase: readString(scope, values, "apiBase", "http://127.0.0.1:8099"),
      graphId: readString(scope, values, "graphId", "graph_lab"),
      sceneJsonPath: readString(scope, values, "sceneJsonPath", ""),
      baselineId: readString(scope, values, "baselineId", "graph_lab_baseline"),
      profile: readString(scope, values, "profile", "fast_debug"),
      runMode: readString(scope, values, "runMode", "sync"),
      autoPollAsyncRun: readBoolean(scope, values, "autoPollAsyncRun", true),
      pollIntervalMsText: readString(scope, values, "pollIntervalMsText", "400"),
      pollStateText: readString(scope, values, "pollStateText", "-"),
      pollingActive: readBoolean(scope, values, "pollingActive", false),
      templates: readArray(scope, values, "templates", []),
      lastGraphRunId: readString(scope, values, "lastGraphRunId", ""),
      contractDebugText: readString(scope, values, "contractDebugText", "-"),
      contractOverlayEnabled: readBoolean(scope, values, "contractOverlayEnabled", false),
      contractTimelineCount: readNumber(scope, values, "contractTimelineCount", 0),
    },
    setters: {
      setApiBase: readFunction(scope, setters, "setApiBase"),
      setGraphId: readFunction(scope, setters, "setGraphId"),
      setSceneJsonPath: readFunction(scope, setters, "setSceneJsonPath"),
      setBaselineId: readFunction(scope, setters, "setBaselineId"),
      setProfile: readFunction(scope, setters, "setProfile"),
      setRunMode: readFunction(scope, setters, "setRunMode"),
      setAutoPollAsyncRun: readFunction(scope, setters, "setAutoPollAsyncRun"),
      setPollIntervalMsText: readFunction(scope, setters, "setPollIntervalMsText"),
      setContractOverlayEnabled: readFunction(scope, setters, "setContractOverlayEnabled"),
    },
    templateActions: {
      fetchTemplates: readFunction(scope, templateActions, "fetchTemplates"),
      exportGraph: readFunction(scope, templateActions, "exportGraph"),
      loadTemplateByIndex: readFunction(scope, templateActions, "loadTemplateByIndex"),
    },
    graphActions: {
      addNodeByType: readFunction(scope, graphActions, "addNodeByType"),
      runGraphValidation: readFunction(scope, graphActions, "runGraphValidation"),
    },
    runActions: {
      runGraphViaApi: readFunction(scope, runActions, "runGraphViaApi"),
      retryLastGraphRun: readFunction(scope, runActions, "retryLastGraphRun"),
      cancelLastGraphRun: readFunction(scope, runActions, "cancelLastGraphRun"),
      pollLastGraphRunOnce: readFunction(scope, runActions, "pollLastGraphRunOnce"),
    },
    gateActions: {
      pinBaselineFromGraphRun: readFunction(scope, gateActions, "pinBaselineFromGraphRun"),
      runPolicyGateForGraphRun: readFunction(scope, gateActions, "runPolicyGateForGraphRun"),
      exportGateReport: readFunction(scope, gateActions, "exportGateReport"),
    },
    contractActions: {
      refreshContractWarnings: readFunction(scope, contractActions, "refreshContractWarnings"),
      resetContractWarnings: readFunction(scope, contractActions, "resetContractWarnings"),
      clearContractTimeline: readFunction(scope, contractActions, "clearContractTimeline"),
    },
  };
}

/**
 * Normalize useGraphRunOps options.
 *
 * @param {any} raw
 * @returns {Object}
 */
export function normalizeGraphRunOpsOptions(raw) {
  const scope = "graph-run-ops-options";
  const root = asObject(raw);
  return {
    __contract_version: GRAPH_RUN_OPS_OPTIONS_CONTRACT,
    apiBase: readString(scope, root, "apiBase", "http://127.0.0.1:8099"),
    profile: readString(scope, root, "profile", "fast_debug"),
    graphId: readString(scope, root, "graphId", "graph_lab"),
    sceneJsonPath: readString(scope, root, "sceneJsonPath", ""),
    nodes: readArray(scope, root, "nodes", []),
    edges: readArray(scope, root, "edges", []),
    runMode: readString(scope, root, "runMode", "sync"),
    autoPollAsyncRun: readBoolean(scope, root, "autoPollAsyncRun", true),
    pollIntervalMsText: readString(scope, root, "pollIntervalMsText", "400"),
    lastGraphRunId: readString(scope, root, "lastGraphRunId", ""),
    setStatus: readFunction(scope, root, "setStatus"),
    setGraphRunText: readFunction(scope, root, "setGraphRunText"),
    setGraphRunSummary: readFunction(scope, root, "setGraphRunSummary"),
    setLastGraphRunId: readFunction(scope, root, "setLastGraphRunId"),
    setPollStateText: readFunction(scope, root, "setPollStateText"),
    setPollingActive: readFunction(scope, root, "setPollingActive"),
    setGateResultText: readFunction(scope, root, "setGateResultText"),
    setLastPolicyEval: readFunction(scope, root, "setLastPolicyEval"),
    onContractDiagnosticsEvent: readOptionalFunction(scope, root, "onContractDiagnosticsEvent"),
  };
}

/**
 * Normalize useGateOps options.
 *
 * @param {any} raw
 * @returns {Object}
 */
export function normalizeGateOpsOptions(raw) {
  const scope = "gate-ops-options";
  const root = asObject(raw);
  return {
    __contract_version: GATE_OPS_OPTIONS_CONTRACT,
    apiBase: readString(scope, root, "apiBase", "http://127.0.0.1:8099"),
    graphRunSummary: asNullableObject(scope, root.graphRunSummary, "graphRunSummary"),
    baselineId: readString(scope, root, "baselineId", "graph_lab_baseline"),
    graphId: readString(scope, root, "graphId", "graph_lab"),
    lastPolicyEval: asNullableObject(scope, root.lastPolicyEval, "lastPolicyEval"),
    contractTimeline: readArray(scope, root, "contractTimeline", []),
    setStatus: readFunction(scope, root, "setStatus"),
    setGateResultText: readFunction(scope, root, "setGateResultText"),
    setLastPolicyEval: readFunction(scope, root, "setLastPolicyEval"),
    onContractDiagnosticsEvent: readOptionalFunction(scope, root, "onContractDiagnosticsEvent"),
  };
}
