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
 * @property {string} runtimeBackendType
 * @property {string} runtimeProviderSpec
 * @property {string} runtimeRequiredModulesText
 * @property {string} runtimeFailurePolicy
 * @property {string} runtimeSimulationMode
 * @property {string} runtimeMultiplexingMode
 * @property {string} runtimeBpmPhaseCodeText
 * @property {string} runtimeMultiplexingPlanJson
 * @property {string} runtimeDevice
 * @property {string} runtimeLicenseTier
 * @property {string} runtimeLicenseFile
 * @property {string} runtimeTxFfdFilesText
 * @property {string} runtimeRxFfdFilesText
 * @property {string} runtimeMitsubaEgoOriginText
 * @property {string} runtimeMitsubaChirpIntervalText
 * @property {string} runtimeMitsubaMinRangeText
 * @property {string} runtimeMitsubaSpheresJson
 * @property {string} runtimePoSbrRepoRoot
 * @property {string} runtimePoSbrGeometryPath
 * @property {string} runtimePoSbrChirpIntervalText
 * @property {string} runtimePoSbrBouncesText
 * @property {string} runtimePoSbrRaysPerLambdaText
 * @property {string} runtimePoSbrAlphaDegText
 * @property {string} runtimePoSbrPhiDegText
 * @property {string} runtimePoSbrThetaDegText
 * @property {string} runtimePoSbrRadialVelocityText
 * @property {string} runtimePoSbrMinRangeText
 * @property {string} runtimePoSbrMaterialTag
 * @property {string} runtimePoSbrPathIdPrefix
 * @property {string} runtimePoSbrComponentsJson
 * @property {Array<any>} runtimeDiagnosticBadges
 * @property {string} runtimeDiagnosticText
 * @property {string} runtimeStatusLine
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
      runtimeBackendType: readString(scope, values, "runtimeBackendType", "analytic_targets"),
      runtimeProviderSpec: readString(scope, values, "runtimeProviderSpec", ""),
      runtimeRequiredModulesText: readString(scope, values, "runtimeRequiredModulesText", ""),
      runtimeFailurePolicy: readString(scope, values, "runtimeFailurePolicy", "error"),
      runtimeSimulationMode: readString(scope, values, "runtimeSimulationMode", "auto"),
      runtimeMultiplexingMode: readString(scope, values, "runtimeMultiplexingMode", "tdm"),
      runtimeBpmPhaseCodeText: readString(scope, values, "runtimeBpmPhaseCodeText", ""),
      runtimeMultiplexingPlanJson: readString(scope, values, "runtimeMultiplexingPlanJson", ""),
      runtimeDevice: readString(scope, values, "runtimeDevice", "cpu"),
      runtimeLicenseTier: readString(scope, values, "runtimeLicenseTier", "trial"),
      runtimeLicenseFile: readString(scope, values, "runtimeLicenseFile", ""),
      runtimeTxFfdFilesText: readString(scope, values, "runtimeTxFfdFilesText", ""),
      runtimeRxFfdFilesText: readString(scope, values, "runtimeRxFfdFilesText", ""),
      runtimeMitsubaEgoOriginText: readString(scope, values, "runtimeMitsubaEgoOriginText", ""),
      runtimeMitsubaChirpIntervalText: readString(scope, values, "runtimeMitsubaChirpIntervalText", ""),
      runtimeMitsubaMinRangeText: readString(scope, values, "runtimeMitsubaMinRangeText", ""),
      runtimeMitsubaSpheresJson: readString(scope, values, "runtimeMitsubaSpheresJson", ""),
      runtimePoSbrRepoRoot: readString(scope, values, "runtimePoSbrRepoRoot", ""),
      runtimePoSbrGeometryPath: readString(scope, values, "runtimePoSbrGeometryPath", ""),
      runtimePoSbrChirpIntervalText: readString(scope, values, "runtimePoSbrChirpIntervalText", ""),
      runtimePoSbrBouncesText: readString(scope, values, "runtimePoSbrBouncesText", ""),
      runtimePoSbrRaysPerLambdaText: readString(scope, values, "runtimePoSbrRaysPerLambdaText", ""),
      runtimePoSbrAlphaDegText: readString(scope, values, "runtimePoSbrAlphaDegText", ""),
      runtimePoSbrPhiDegText: readString(scope, values, "runtimePoSbrPhiDegText", ""),
      runtimePoSbrThetaDegText: readString(scope, values, "runtimePoSbrThetaDegText", ""),
      runtimePoSbrRadialVelocityText: readString(scope, values, "runtimePoSbrRadialVelocityText", ""),
      runtimePoSbrMinRangeText: readString(scope, values, "runtimePoSbrMinRangeText", ""),
      runtimePoSbrMaterialTag: readString(scope, values, "runtimePoSbrMaterialTag", ""),
      runtimePoSbrPathIdPrefix: readString(scope, values, "runtimePoSbrPathIdPrefix", ""),
      runtimePoSbrComponentsJson: readString(scope, values, "runtimePoSbrComponentsJson", ""),
      runtimeDiagnosticBadges: readArray(scope, values, "runtimeDiagnosticBadges", []),
      runtimeDiagnosticText: readString(scope, values, "runtimeDiagnosticText", "-"),
      runtimeStatusLine: readString(scope, values, "runtimeStatusLine", "-"),
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
      setRuntimeBackendType: readFunction(scope, setters, "setRuntimeBackendType"),
      setRuntimeProviderSpec: readFunction(scope, setters, "setRuntimeProviderSpec"),
      setRuntimeRequiredModulesText: readFunction(scope, setters, "setRuntimeRequiredModulesText"),
      setRuntimeFailurePolicy: readFunction(scope, setters, "setRuntimeFailurePolicy"),
      setRuntimeSimulationMode: readFunction(scope, setters, "setRuntimeSimulationMode"),
      setRuntimeMultiplexingMode: readFunction(scope, setters, "setRuntimeMultiplexingMode"),
      setRuntimeBpmPhaseCodeText: readFunction(scope, setters, "setRuntimeBpmPhaseCodeText"),
      setRuntimeMultiplexingPlanJson: readFunction(scope, setters, "setRuntimeMultiplexingPlanJson"),
      setRuntimeDevice: readFunction(scope, setters, "setRuntimeDevice"),
      setRuntimeLicenseTier: readFunction(scope, setters, "setRuntimeLicenseTier"),
      setRuntimeLicenseFile: readFunction(scope, setters, "setRuntimeLicenseFile"),
      setRuntimeTxFfdFilesText: readFunction(scope, setters, "setRuntimeTxFfdFilesText"),
      setRuntimeRxFfdFilesText: readFunction(scope, setters, "setRuntimeRxFfdFilesText"),
      setRuntimeMitsubaEgoOriginText: readFunction(scope, setters, "setRuntimeMitsubaEgoOriginText"),
      setRuntimeMitsubaChirpIntervalText: readFunction(scope, setters, "setRuntimeMitsubaChirpIntervalText"),
      setRuntimeMitsubaMinRangeText: readFunction(scope, setters, "setRuntimeMitsubaMinRangeText"),
      setRuntimeMitsubaSpheresJson: readFunction(scope, setters, "setRuntimeMitsubaSpheresJson"),
      setRuntimePoSbrRepoRoot: readFunction(scope, setters, "setRuntimePoSbrRepoRoot"),
      setRuntimePoSbrGeometryPath: readFunction(scope, setters, "setRuntimePoSbrGeometryPath"),
      setRuntimePoSbrChirpIntervalText: readFunction(scope, setters, "setRuntimePoSbrChirpIntervalText"),
      setRuntimePoSbrBouncesText: readFunction(scope, setters, "setRuntimePoSbrBouncesText"),
      setRuntimePoSbrRaysPerLambdaText: readFunction(scope, setters, "setRuntimePoSbrRaysPerLambdaText"),
      setRuntimePoSbrAlphaDegText: readFunction(scope, setters, "setRuntimePoSbrAlphaDegText"),
      setRuntimePoSbrPhiDegText: readFunction(scope, setters, "setRuntimePoSbrPhiDegText"),
      setRuntimePoSbrThetaDegText: readFunction(scope, setters, "setRuntimePoSbrThetaDegText"),
      setRuntimePoSbrRadialVelocityText: readFunction(scope, setters, "setRuntimePoSbrRadialVelocityText"),
      setRuntimePoSbrMinRangeText: readFunction(scope, setters, "setRuntimePoSbrMinRangeText"),
      setRuntimePoSbrMaterialTag: readFunction(scope, setters, "setRuntimePoSbrMaterialTag"),
      setRuntimePoSbrPathIdPrefix: readFunction(scope, setters, "setRuntimePoSbrPathIdPrefix"),
      setRuntimePoSbrComponentsJson: readFunction(scope, setters, "setRuntimePoSbrComponentsJson"),
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
    runtimeBackendType: readString(scope, root, "runtimeBackendType", "analytic_targets"),
    runtimeProviderSpec: readString(scope, root, "runtimeProviderSpec", ""),
    runtimeRequiredModulesText: readString(scope, root, "runtimeRequiredModulesText", ""),
    runtimeFailurePolicy: readString(scope, root, "runtimeFailurePolicy", "error"),
    runtimeSimulationMode: readString(scope, root, "runtimeSimulationMode", "auto"),
    runtimeMultiplexingMode: readString(scope, root, "runtimeMultiplexingMode", "tdm"),
    runtimeBpmPhaseCodeText: readString(scope, root, "runtimeBpmPhaseCodeText", ""),
    runtimeMultiplexingPlanJson: readString(scope, root, "runtimeMultiplexingPlanJson", ""),
    runtimeDevice: readString(scope, root, "runtimeDevice", "cpu"),
    runtimeLicenseTier: readString(scope, root, "runtimeLicenseTier", "trial"),
    runtimeLicenseFile: readString(scope, root, "runtimeLicenseFile", ""),
    runtimeTxFfdFilesText: readString(scope, root, "runtimeTxFfdFilesText", ""),
    runtimeRxFfdFilesText: readString(scope, root, "runtimeRxFfdFilesText", ""),
    runtimeMitsubaEgoOriginText: readString(scope, root, "runtimeMitsubaEgoOriginText", ""),
    runtimeMitsubaChirpIntervalText: readString(scope, root, "runtimeMitsubaChirpIntervalText", ""),
    runtimeMitsubaMinRangeText: readString(scope, root, "runtimeMitsubaMinRangeText", ""),
    runtimeMitsubaSpheresJson: readString(scope, root, "runtimeMitsubaSpheresJson", ""),
    runtimePoSbrRepoRoot: readString(scope, root, "runtimePoSbrRepoRoot", ""),
    runtimePoSbrGeometryPath: readString(scope, root, "runtimePoSbrGeometryPath", ""),
    runtimePoSbrChirpIntervalText: readString(scope, root, "runtimePoSbrChirpIntervalText", ""),
    runtimePoSbrBouncesText: readString(scope, root, "runtimePoSbrBouncesText", ""),
    runtimePoSbrRaysPerLambdaText: readString(scope, root, "runtimePoSbrRaysPerLambdaText", ""),
    runtimePoSbrAlphaDegText: readString(scope, root, "runtimePoSbrAlphaDegText", ""),
    runtimePoSbrPhiDegText: readString(scope, root, "runtimePoSbrPhiDegText", ""),
    runtimePoSbrThetaDegText: readString(scope, root, "runtimePoSbrThetaDegText", ""),
    runtimePoSbrRadialVelocityText: readString(scope, root, "runtimePoSbrRadialVelocityText", ""),
    runtimePoSbrMinRangeText: readString(scope, root, "runtimePoSbrMinRangeText", ""),
    runtimePoSbrMaterialTag: readString(scope, root, "runtimePoSbrMaterialTag", ""),
    runtimePoSbrPathIdPrefix: readString(scope, root, "runtimePoSbrPathIdPrefix", ""),
    runtimePoSbrComponentsJson: readString(scope, root, "runtimePoSbrComponentsJson", ""),
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
