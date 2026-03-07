import {
  React,
  addEdge,
  useNodesState,
  useEdgesState,
} from "./deps.mjs";
import {
  getContractWarningSnapshot,
  normalizeGraphInputsPanelModel,
  resetContractWarnings as resetContractWarningStore,
} from "./contracts.mjs";
import { toFlowNode, toGraphPayload } from "./graph_helpers.mjs";
import {
  getGraphRunSummaryMaybe,
  getGraphTemplates,
  getPolicyEval,
  exportRegressionSession,
  listGraphRuns,
  listPolicyEvals,
  runRegressionSession,
  validateGraphContract,
} from "./api_client.mjs";
import {
  ContractWarningOverlay,
  GraphCanvasPanel,
  GraphInputsPanel,
  NodeInspectorPanel,
  TopBar,
} from "./panels.mjs";
import { useGateOps } from "./hooks/use_gate_ops.mjs";
import { useGraphRunOps } from "./hooks/use_graph_run_ops.mjs";

const h = React.createElement;
const LAYOUT_MODE_SET = new Set(["triad", "build", "review", "focus"]);
const DENSITY_MODE_SET = new Set(["comfortable", "compact"]);

function normalizeLayoutMode(value) {
  const mode = String(value || "").trim().toLowerCase();
  return LAYOUT_MODE_SET.has(mode) ? mode : "triad";
}

function normalizeDensityMode(value) {
  const mode = String(value || "").trim().toLowerCase();
  return DENSITY_MODE_SET.has(mode) ? mode : "comfortable";
}

export function App() {
  const params = new URLSearchParams(window.location.search);
  const [layoutMode, setLayoutMode] = React.useState(
    normalizeLayoutMode(params.get("view") || "triad")
  );
  const [densityMode, setDensityMode] = React.useState(
    normalizeDensityMode(params.get("density") || "comfortable")
  );
  const [focusLeftOpen, setFocusLeftOpen] = React.useState(false);
  const [focusRightOpen, setFocusRightOpen] = React.useState(false);
  const [apiBase, setApiBase] = React.useState(
    String(params.get("api") || "http://127.0.0.1:8099")
  );
  const [graphId, setGraphId] = React.useState("graph_lab");
  const [profile, setProfile] = React.useState("fast_debug");
  const [sceneJsonPath, setSceneJsonPath] = React.useState(
    String(params.get("scene") || "data/demo/frontend_quickstart_v1/scene_frontend_quickstart.json")
  );
  const [baselineId, setBaselineId] = React.useState(
    String(params.get("baseline_id") || "graph_lab_baseline")
  );
  const [runtimeBackendType, setRuntimeBackendType] = React.useState(
    String(params.get("backend") || "analytic_targets")
  );
  const [runtimeProviderSpec, setRuntimeProviderSpec] = React.useState(
    String(params.get("runtime_provider") || "")
  );
  const [runtimeRequiredModulesText, setRuntimeRequiredModulesText] = React.useState(
    String(params.get("runtime_required_modules") || "")
  );
  const [runtimeFailurePolicy, setRuntimeFailurePolicy] = React.useState(
    String(params.get("runtime_failure_policy") || "error")
  );
  const [runtimeSimulationMode, setRuntimeSimulationMode] = React.useState(
    String(params.get("simulation_mode") || "auto")
  );
  const [runtimeMultiplexingMode, setRuntimeMultiplexingMode] = React.useState(
    String(params.get("runtime_multiplexing_mode") || "tdm")
  );
  const [runtimeBpmPhaseCodeText, setRuntimeBpmPhaseCodeText] = React.useState(
    String(params.get("runtime_bpm_phase_code") || "")
  );
  const [runtimeMultiplexingPlanJson, setRuntimeMultiplexingPlanJson] = React.useState(
    String(params.get("runtime_multiplexing_plan_json") || "")
  );
  const [runtimeDevice, setRuntimeDevice] = React.useState(
    String(params.get("runtime_device") || "cpu")
  );
  const [runtimeLicenseTier, setRuntimeLicenseTier] = React.useState(
    String(params.get("runtime_license_tier") || "trial")
  );
  const [runtimeLicenseFile, setRuntimeLicenseFile] = React.useState(
    String(params.get("runtime_license_file") || "")
  );
  const [runtimeTxFfdFilesText, setRuntimeTxFfdFilesText] = React.useState(
    String(params.get("runtime_tx_ffd_files") || "")
  );
  const [runtimeRxFfdFilesText, setRuntimeRxFfdFilesText] = React.useState(
    String(params.get("runtime_rx_ffd_files") || "")
  );
  const [compareGraphRunId, setCompareGraphRunId] = React.useState(
    String(params.get("compare_run_id") || "")
  );
  const [compareGraphRunSummary, setCompareGraphRunSummary] = React.useState(null);
  const [compareRunStatusText, setCompareRunStatusText] = React.useState("-");
  const [compareRunPinnedManual, setCompareRunPinnedManual] = React.useState(
    String(params.get("compare_run_id") || "").trim() !== ""
  );
  const [compareAutoSkipForRunId, setCompareAutoSkipForRunId] = React.useState("");
  const [lastRegressionSession, setLastRegressionSession] = React.useState(null);
  const [lastRegressionExport, setLastRegressionExport] = React.useState(null);
  const [decisionOpsStatusText, setDecisionOpsStatusText] = React.useState("-");
  const [templates, setTemplates] = React.useState([]);
  const [statusText, setStatusText] = React.useState("idle");
  const [statusTone, setStatusTone] = React.useState("status-neutral");
  const [validationText, setValidationText] = React.useState("-");
  const [graphRunText, setGraphRunText] = React.useState("-");
  const [graphRunSummary, setGraphRunSummary] = React.useState(null);
  const [lastGraphRunId, setLastGraphRunId] = React.useState("");
  const [runMode, setRunMode] = React.useState(String(params.get("run_mode") || "sync"));
  const [autoPollAsyncRun, setAutoPollAsyncRun] = React.useState(
    String(params.get("auto_poll") || "1") !== "0"
  );
  const [pollIntervalMsText, setPollIntervalMsText] = React.useState(
    String(params.get("poll_ms") || "400")
  );
  const [pollStateText, setPollStateText] = React.useState("-");
  const [pollingActive, setPollingActive] = React.useState(false);
  const [gateResultText, setGateResultText] = React.useState("-");
  const [lastPolicyEval, setLastPolicyEval] = React.useState(null);
  const [contractDebugText, setContractDebugText] = React.useState("-");
  const [contractOverlayEnabled, setContractOverlayEnabled] = React.useState(
    String(params.get("contract_overlay") || "0") === "1"
  );
  const [contractTimeline, setContractTimeline] = React.useState([]);
  const [selectedNodeId, setSelectedNodeId] = React.useState("");
  const [selectedNodeParamsText, setSelectedNodeParamsText] = React.useState("{}");
  const policyEvalListCacheRef = React.useRef(new Map());

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  const selectedNode = React.useMemo(
    () => nodes.find((n) => String(n.id) === String(selectedNodeId)) || null,
    [nodes, selectedNodeId]
  );

  React.useEffect(() => {
    if (!selectedNode) {
      setSelectedNodeParamsText("{}");
      return;
    }
    const paramsObj = selectedNode.data && selectedNode.data.params ? selectedNode.data.params : {};
    setSelectedNodeParamsText(JSON.stringify(paramsObj, null, 2));
  }, [selectedNode]);

  React.useEffect(() => {
    const query = new URLSearchParams(window.location.search);
    query.set("view", layoutMode);
    query.set("density", densityMode);
    const next = `${window.location.pathname}?${query.toString()}`;
    window.history.replaceState(null, "", next);
  }, [densityMode, layoutMode]);

  React.useEffect(() => {
    if (layoutMode === "focus") return;
    setFocusLeftOpen(false);
    setFocusRightOpen(false);
  }, [layoutMode]);

  const setStatus = React.useCallback((text, tone) => {
    setStatusText(String(text || "idle"));
    setStatusTone(String(tone || "status-neutral"));
  }, []);

  const formatContractWarningSnapshot = React.useCallback((snapshot) => {
    const s = snapshot && typeof snapshot === "object" ? snapshot : {};
    const byScope = Array.isArray(s.by_scope) ? s.by_scope : [];
    const topScopes = byScope
      .slice(0, 4)
      .map((x) => `${String(x.scope || "-")}(${Number(x.unique || 0)}/${Number(x.attempts || 0)})`)
      .join(", ");
    const last = s.last_warning && typeof s.last_warning === "object" ? s.last_warning : null;
    return [
      `contract_debug_version: ${String(s.contract_debug_version || "-")}`,
      `unique_warning_count: ${Number(s.unique_warning_count || 0)}`,
      `warning_attempt_count: ${Number(s.attempt_count_total || 0)}`,
      `top_scopes(unique/attempt): ${topScopes || "-"}`,
      `last_warning: ${last ? `${String(last.scope || "-")} | ${String(last.message || "-")}` : "-"}`,
    ].join("\n");
  }, []);

  const refreshContractWarnings = React.useCallback(() => {
    const snapshot = getContractWarningSnapshot();
    setContractDebugText(formatContractWarningSnapshot(snapshot));
  }, [formatContractWarningSnapshot]);

  const resetContractWarnings = React.useCallback(() => {
    resetContractWarningStore();
    refreshContractWarnings();
    setStatus("contract warnings reset", "status-ok");
  }, [refreshContractWarnings, setStatus]);

  const appendContractDiagnosticsEvent = React.useCallback((eventPayload) => {
    const e = eventPayload && typeof eventPayload === "object" ? eventPayload : {};
    const row = {
      event_source: String(e.event_source || "graph_lab"),
      graph_run_id: String(e.graph_run_id || ""),
      timestamp_ms: Number(e.timestamp_ms || Date.now()),
      snapshot: e.snapshot && typeof e.snapshot === "object" ? e.snapshot : {},
      delta: e.delta && typeof e.delta === "object" ? e.delta : {},
      baseline: e.baseline && typeof e.baseline === "object" ? e.baseline : {},
      note: e.note && typeof e.note === "object" ? e.note : {},
    };
    setContractTimeline((prev) => [row, ...prev].slice(0, 80));
  }, []);

  const clearContractTimeline = React.useCallback(() => {
    setContractTimeline([]);
    setStatus("contract timeline cleared", "status-ok");
  }, [setStatus]);

  const exportContractTimeline = React.useCallback(() => {
    const nowIso = new Date().toISOString();
    const payload = {
      version: "contract_timeline_export_v1",
      exported_at_utc: nowIso,
      event_count: Number(contractTimeline.length || 0),
      events: contractTimeline,
    };
    const text = JSON.stringify(payload, null, 2);
    const blob = new Blob([text], { type: "application/json;charset=utf-8" });
    const href = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = href;
    a.download = `contract_timeline_${nowIso.slice(0, 19).replace(/[:T]/g, "_")}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.setTimeout(() => URL.revokeObjectURL(href), 1000);
    setStatus("contract timeline exported", "status-ok");
  }, [contractTimeline, setStatus]);

  React.useEffect(() => {
    policyEvalListCacheRef.current.clear();
  }, [apiBase]);

  const fetchPolicyEvalListCached = React.useCallback(async (options) => {
    const opts = options && typeof options === "object" ? options : {};
    const candidateRunId = String(opts.candidateRunId || "").trim();
    const baselineId = String(opts.baselineId || "").trim();
    const limit = Number(opts.limit || 0);
    const offset = Number(opts.offset || 0);
    const normalized = {
      candidateRunId,
      baselineId,
      limit: Number.isFinite(limit) && limit > 0 ? Math.floor(limit) : 0,
      offset: Number.isFinite(offset) && offset > 0 ? Math.floor(offset) : 0,
    };
    const key = JSON.stringify(normalized);
    const nowMs = Date.now();
    const ttlMs = 20_000;
    const cache = policyEvalListCacheRef.current;
    const cached = cache.get(key);
    if (
      cached &&
      typeof cached === "object" &&
      Number.isFinite(Number(cached.timestamp_ms || 0)) &&
      (nowMs - Number(cached.timestamp_ms || 0)) <= ttlMs
    ) {
      return { payload: cached.payload || {}, cacheHit: true };
    }
    const payload = await listPolicyEvals(apiBase, normalized);
    cache.set(key, { timestamp_ms: nowMs, payload });
    if (cache.size > 24) {
      const entries = Array.from(cache.entries());
      entries.sort((a, b) => Number(a?.[1]?.timestamp_ms || 0) - Number(b?.[1]?.timestamp_ms || 0));
      while (entries.length > 16) {
        const removed = entries.shift();
        if (!removed) break;
        cache.delete(String(removed[0]));
      }
    }
    return { payload, cacheHit: false };
  }, [apiBase]);

  const loadCompareGraphRunById = React.useCallback(async (graphRunIdInput, options) => {
    const opts = options && typeof options === "object" ? options : {};
    const mode = String(opts.mode || "manual");
    const graphRunId = String(graphRunIdInput || "").trim();
    const shouldSetStatus = Boolean(opts.setStatus !== false);
    const pinManual = mode === "manual" || Boolean(opts.pinManual);

    if (!graphRunId) {
      if (mode === "manual" && shouldSetStatus) {
        setStatus("compare graph run id is required", "status-warn");
      }
      setCompareGraphRunId("");
      setCompareGraphRunSummary(null);
      setCompareRunStatusText("compare: not set");
      setCompareRunPinnedManual(false);
      return false;
    }

    if (mode === "manual" && shouldSetStatus) {
      setStatus(`loading compare graph run: ${graphRunId}`, "status-warn");
    }

    try {
      const sumRes = await getGraphRunSummaryMaybe(apiBase, graphRunId);
      if (!sumRes.ok) {
        throw new Error(`graph summary request failed (${Number(sumRes.status)})`);
      }
      const summary = sumRes.payload || {};
      const completedAt = String(summary.completed_at || summary.created_at || "-");
      const status = String(summary.status || "-");
      setCompareGraphRunId(graphRunId);
      setCompareGraphRunSummary(summary);
      setCompareRunPinnedManual(pinManual);
      setCompareAutoSkipForRunId("");
      setCompareRunStatusText(
        `compare_mode=${mode} | run=${graphRunId} | status=${status} | completed_at=${completedAt}`
      );
      if (mode === "manual" && shouldSetStatus) {
        setStatus(`compare graph run loaded: ${graphRunId}`, "status-ok");
      }
      return true;
    } catch (err) {
      setCompareGraphRunSummary(null);
      if (pinManual) {
        setCompareRunPinnedManual(true);
      }
      setCompareRunStatusText(
        `compare_mode=${mode} | run=${graphRunId} | load_failed=${String(err.message || err)}`
      );
      if (mode === "manual" && shouldSetStatus) {
        setStatus(`compare graph run load failed: ${String(err.message || err)}`, "status-err");
      }
      return false;
    }
  }, [apiBase, setStatus]);

  const clearCompareGraphRun = React.useCallback(() => {
    setCompareGraphRunId("");
    setCompareGraphRunSummary(null);
    setCompareRunPinnedManual(false);
    setCompareAutoSkipForRunId(String(graphRunSummary?.graph_run_id || "").trim());
    setCompareRunStatusText("compare: cleared");
    setStatus("compare graph run cleared", "status-ok");
  }, [graphRunSummary?.graph_run_id, setStatus]);

  const setCompareGraphRunIdDraft = React.useCallback((nextText) => {
    const text = String(nextText || "");
    setCompareGraphRunId(text);
    setCompareRunPinnedManual(text.trim() !== "");
  }, []);

  const openGateEvidenceFromTimeline = React.useCallback(async (row, lookupOptions) => {
    const eventRow = row && typeof row === "object" ? row : {};
    const note = eventRow.note && typeof eventRow.note === "object" ? eventRow.note : {};
    const lookup = lookupOptions && typeof lookupOptions === "object" ? lookupOptions : {};
    const normalizeHint = (v) => {
      const text = String(v || "").trim();
      if (text === "" || text === "-") return "";
      const low = text.toLowerCase();
      if (low === "none" || low === "null") return "";
      return text;
    };
    const asPositiveInt = (v, fallback, minValue, maxValue) => {
      const n = Number(v);
      if (!Number.isFinite(n) || n <= 0) return Number(fallback);
      const iv = Math.floor(n);
      return Math.max(Number(minValue), Math.min(Number(maxValue), iv));
    };
    const normalizePath = (v) => String(v || "").replace(/\\/g, "/").trim();
    const pathMatches = (a, b) => {
      const left = normalizePath(a);
      const right = normalizePath(b);
      if (!left || !right) return false;
      return left === right || left.endsWith(right) || right.endsWith(left);
    };

    const policyEvalIdHint = normalizeHint(note.policy_eval_id);
    const runIdHint = normalizeHint(eventRow.graph_run_id);
    const baselineIdHint = normalizeHint(note.baseline_id);
    const summaryHint = normalizeHint(note.candidate_summary_json);
    const historyLimit = asPositiveInt(lookup.historyLimit, 256, 32, 4096);
    const pageBudget = asPositiveInt(lookup.pageBudget, 2, 1, 8);

    setStatus("loading gate evidence...", "status-warn");

    let resolvedEval = null;
    let evidenceSource = "timeline_note";
    let scanCount = 0;
    let cacheHitAny = false;
    let pageCountUsed = 0;
    const lookupErrors = [];

    if (policyEvalIdHint) {
      try {
        const payload = await getPolicyEval(apiBase, policyEvalIdHint);
        if (payload && typeof payload === "object") {
          resolvedEval = payload;
          evidenceSource = "policy_eval_id";
        }
      } catch (err) {
        lookupErrors.push(`get_policy_eval(${policyEvalIdHint}) failed: ${String(err.message || err)}`);
      }
    }

    if (!resolvedEval) {
      const resolveFromRows = (rows, scopeTag, cacheHit, pageIndex) => {
        const list = Array.isArray(rows) ? rows : [];
        const matchRun = (item) =>
          runIdHint !== "" &&
          normalizeHint(item?.candidate?.run_id) === runIdHint;
        const matchSummary = (item) =>
          summaryHint !== "" &&
          pathMatches(item?.candidate?.run_summary_json, summaryHint);

        const byEvalId = policyEvalIdHint !== ""
          ? list.find((item) => normalizeHint(item?.policy_eval_id) === policyEvalIdHint) || null
          : null;
        const byRunAndSummary = list.find((item) => matchRun(item) && matchSummary(item)) || null;
        const byRunOnly = list.find((item) => matchRun(item)) || null;
        const bySummaryOnly = list.find((item) => matchSummary(item)) || null;
        const byBaselineOnly = baselineIdHint !== ""
          ? list.find((item) => normalizeHint(item?.baseline?.baseline_id) === baselineIdHint) || null
          : null;
        const resolved = byEvalId || byRunAndSummary || byRunOnly || bySummaryOnly || byBaselineOnly;
        if (!resolved) return false;

        let matchedBy = "fallback";
        if (byEvalId) matchedBy = "policy_eval_id";
        else if (byRunAndSummary) matchedBy = "run_id+summary_json";
        else if (byRunOnly) matchedBy = "run_id";
        else if (bySummaryOnly) matchedBy = "summary_json";
        else if (byBaselineOnly) matchedBy = "baseline_id";
        resolvedEval = resolved;
        evidenceSource = `policy_eval_list:${scopeTag}:${matchedBy}:page${Number(pageIndex)}${cacheHit ? ":cache_hit" : ""}`;
        return true;
      };

      const queryPlans = [];
      if (runIdHint) {
        queryPlans.push({
          scopeTag: baselineIdHint ? "run_id+baseline_id" : "run_id",
          candidateRunId: runIdHint,
          baselineId: baselineIdHint || "",
        });
      }
      if (baselineIdHint) {
        queryPlans.push({
          scopeTag: "baseline_id",
          baselineId: baselineIdHint,
        });
      }
      queryPlans.push({
        scopeTag: "global",
      });

      const seenPlans = new Set();
      for (const plan of queryPlans) {
        const basePlan = {
          candidateRunId: String(plan.candidateRunId || "").trim(),
          baselineId: String(plan.baselineId || "").trim(),
          limit: historyLimit,
          offset: 0,
        };
        const planKey = JSON.stringify({
          candidateRunId: basePlan.candidateRunId,
          baselineId: basePlan.baselineId,
        });
        if (seenPlans.has(planKey)) continue;
        seenPlans.add(planKey);

        for (let pageIdx = 0; pageIdx < pageBudget; pageIdx += 1) {
          const normalizedPlan = {
            ...basePlan,
            offset: pageIdx * historyLimit,
          };
          try {
            const result = await fetchPolicyEvalListCached(normalizedPlan);
            const payload = result && typeof result === "object" ? result.payload : {};
            const cacheHit = Boolean(result && result.cacheHit);
            cacheHitAny = cacheHitAny || cacheHit;
            const rows = Array.isArray(payload?.policy_evals) ? payload.policy_evals : [];
            const returnedCount = Number(payload?.page?.returned_count);
            const totalCount = Number(payload?.page?.total_count);
            const effectiveReturnedCount =
              Number.isFinite(returnedCount) && returnedCount >= 0
                ? returnedCount
                : rows.length;
            scanCount += effectiveReturnedCount;
            pageCountUsed = Math.max(pageCountUsed, pageIdx + 1);
            if (resolveFromRows(rows, String(plan.scopeTag || "global"), cacheHit, pageIdx + 1)) {
              break;
            }
            const reachedEnd =
              effectiveReturnedCount <= 0 ||
              !Number.isFinite(totalCount) ||
              (normalizedPlan.offset + effectiveReturnedCount) >= totalCount;
            if (reachedEnd) {
              break;
            }
          } catch (err) {
            lookupErrors.push(
              `list_policy_evals(${String(plan.scopeTag || "global")}@page${pageIdx + 1}) failed: ${String(err.message || err)}`
            );
            break;
          }
        }
        if (resolvedEval) {
          break;
        }
      }
    }

    if (resolvedEval && typeof resolvedEval === "object") {
      const candidate = resolvedEval.candidate && typeof resolvedEval.candidate === "object"
        ? resolvedEval.candidate
        : {};
      const baseline = resolvedEval.baseline && typeof resolvedEval.baseline === "object"
        ? resolvedEval.baseline
        : {};
      const parity = resolvedEval.parity && typeof resolvedEval.parity === "object"
        ? resolvedEval.parity
        : {};
      const policy = resolvedEval.policy && typeof resolvedEval.policy === "object"
        ? resolvedEval.policy
        : {};
      const gateFailures = Array.isArray(resolvedEval.gate_failures) ? resolvedEval.gate_failures : [];
      const parityFailures = Array.isArray(parity.failures) ? parity.failures : [];
      const runId = normalizeHint(candidate.run_id) || runIdHint;
      const gateFailed = Boolean(resolvedEval.gate_failed);
      const policyKeys = Object.keys(policy).sort((a, b) => a.localeCompare(b));
      const lines = [
        `policy_eval_id: ${normalizeHint(resolvedEval.policy_eval_id) || policyEvalIdHint || "-"}`,
        `evidence_source: persisted/${evidenceSource}`,
        `gate_failed: ${gateFailed}`,
        `recommendation: ${String(resolvedEval.recommendation || "-")}`,
        `baseline_id: ${normalizeHint(baseline.baseline_id) || baselineIdHint || "-"}`,
        `candidate_run_id: ${runId || "-"}`,
        `candidate_summary_json: ${normalizeHint(candidate.run_summary_json) || summaryHint || "-"}`,
        `parity_pass: ${Boolean(parity.pass)}`,
        `parity_failure_count: ${Number(parityFailures.length || 0)}`,
        `gate_failure_count: ${Number(gateFailures.length || 0)}`,
        `policy_eval_history_limit: ${Number(historyLimit)}`,
        `policy_eval_page_budget: ${Number(pageBudget)}`,
        `policy_eval_page_count_used: ${Number(pageCountUsed || 0)}`,
        `policy_eval_scan_count: ${Number(scanCount || 0)}`,
        `policy_eval_cache_hit_any: ${Boolean(cacheHitAny)}`,
        "",
        "gate_failures:",
      ];
      if (gateFailures.length === 0) {
        lines.push("- none");
      } else {
        gateFailures.slice(0, 12).forEach((failure, idx) => {
          const metric = failure && failure.metric ? ` (${String(failure.metric)})` : "";
          lines.push(
            `- [${Number(idx) + 1}] ${String((failure && failure.rule) || "unknown_rule")}${metric}: ${String(
              (failure && failure.value) ?? "-"
            )} > ${String((failure && failure.limit) ?? "-")}`
          );
        });
      }
      lines.push("", "policy:");
      if (policyKeys.length === 0) {
        lines.push("- none");
      } else {
        policyKeys.forEach((key) => {
          lines.push(`- ${String(key)}: ${String(policy[key])}`);
        });
      }
      lines.push(
        "",
        `source_event: ${String(eventRow.event_source || "-")}`,
        `timestamp_ms: ${Number(eventRow.timestamp_ms || 0)}`,
        `contract_delta: ${Number(eventRow?.delta?.unique_warning_count || 0)}/${Number(eventRow?.delta?.attempt_count_total || 0)}`,
      );
      if (lookupErrors.length > 0) {
        lines.push("", "lookup_warnings:", ...lookupErrors.map((msg) => `- ${msg}`));
      }
      setGateResultText(lines.join("\n"));
      if (runId) setLastGraphRunId(runId);
      setStatus(
        gateFailed ? `gate evidence opened (HOLD): ${runId || "-"}` : `gate evidence opened (ADOPT): ${runId || "-"}`,
        gateFailed ? "status-warn" : "status-ok"
      );
      return;
    }

    const gateFailed = Boolean(note.gate_failed);
    const rules = Array.isArray(note.failure_rules) ? note.failure_rules : [];
    const lines = [
      `policy_eval_id: ${policyEvalIdHint || "-"}`,
      "evidence_source: timeline_note_only",
      `gate_failed: ${gateFailed}`,
      `recommendation: ${String(note.recommendation || "-")}`,
      `baseline_id: ${baselineIdHint || "-"}`,
      `graph_run_id: ${runIdHint || "-"}`,
      `candidate_summary_json: ${summaryHint || "-"}`,
      `failure_count: ${Number(note.failure_count || 0)}`,
      `policy_eval_history_limit: ${Number(historyLimit)}`,
      `policy_eval_page_budget: ${Number(pageBudget)}`,
      `policy_eval_page_count_used: ${Number(pageCountUsed || 0)}`,
      `policy_eval_scan_count: ${Number(scanCount || 0)}`,
      `policy_eval_cache_hit_any: ${Boolean(cacheHitAny)}`,
      "",
      "gate_failures:",
      ...(rules.length > 0 ? rules.map((rule, idx) => `- [${Number(idx) + 1}] ${rule}`) : ["- none"]),
      "",
      `source_event: ${String(eventRow.event_source || "-")}`,
      `timestamp_ms: ${Number(eventRow.timestamp_ms || 0)}`,
      `contract_delta: ${Number(eventRow?.delta?.unique_warning_count || 0)}/${Number(eventRow?.delta?.attempt_count_total || 0)}`,
    ];
    if (lookupErrors.length > 0) {
      lines.push("", "lookup_warnings:", ...lookupErrors.map((msg) => `- ${msg}`));
    }
    setGateResultText(lines.join("\n"));
    if (runIdHint) setLastGraphRunId(runIdHint);
    setStatus(`gate evidence unresolved: ${runIdHint || "-"}`, "status-warn");
  }, [apiBase, fetchPolicyEvalListCached, setGateResultText, setLastGraphRunId, setStatus]);

  React.useEffect(() => {
    refreshContractWarnings();
  }, [refreshContractWarnings]);

  React.useEffect(() => {
    refreshContractWarnings();
  }, [graphRunText, gateResultText, validationText, refreshContractWarnings]);

  React.useEffect(() => {
    const currentGraphRunId = String(graphRunSummary?.graph_run_id || "").trim();
    if (!currentGraphRunId) return;
    if (String(compareAutoSkipForRunId || "").trim() === currentGraphRunId) return;

    const compareLockedByUser = Boolean(compareRunPinnedManual);
    if (compareLockedByUser && String(compareGraphRunId).trim() === currentGraphRunId) {
      setCompareRunStatusText("compare: same as current run (disabled)");
      setCompareGraphRunSummary(null);
      return;
    }
    if (compareLockedByUser) return;

    let canceled = false;
    const loadAutoCompare = async () => {
      const cacheSourceId = String(
        graphRunSummary?.execution?.cache?.source_graph_run_id || ""
      ).trim();
      if (cacheSourceId && cacheSourceId !== currentGraphRunId) {
        if (
          cacheSourceId === String(compareGraphRunId || "").trim()
          && compareGraphRunSummary
        ) {
          return;
        }
        if (canceled) return;
        await loadCompareGraphRunById(cacheSourceId, { mode: "auto_cache_source", setStatus: false });
        return;
      }

      const payload = await listGraphRuns(apiBase);
      const rows = Array.isArray(payload.graph_runs) ? payload.graph_runs : [];
      const candidate = rows.find((row) => {
        const rid = String(row?.graph_run_id || "").trim();
        const status = String(row?.status || "").trim().toLowerCase();
        return rid !== "" && rid !== currentGraphRunId && status === "completed";
      });
      const candidateId = String(candidate?.graph_run_id || "").trim();
      if (!candidateId) {
        setCompareGraphRunSummary(null);
        setCompareRunStatusText("compare_mode=auto_previous | no completed baseline run");
        return;
      }
      if (
        candidateId === String(compareGraphRunId || "").trim()
        && compareGraphRunSummary
      ) {
        return;
      }
      if (canceled) return;
      await loadCompareGraphRunById(candidateId, { mode: "auto_previous", setStatus: false });
    };

    loadAutoCompare().catch((err) => {
      if (canceled) return;
      setCompareGraphRunSummary(null);
      setCompareRunStatusText(`compare_mode=auto | load_failed=${String(err.message || err)}`);
    });
    return () => {
      canceled = true;
    };
  }, [
    apiBase,
    compareGraphRunId,
    compareGraphRunSummary,
    compareAutoSkipForRunId,
    compareRunPinnedManual,
    graphRunSummary,
    loadCompareGraphRunById,
  ]);

  const applyGraph = React.useCallback((graph) => {
    const g = graph && typeof graph === "object" ? graph : {};
    setGraphId(String(g.graph_id || "graph_lab"));
    setProfile(String(g.profile || "fast_debug"));
    const nextNodes = Array.isArray(g.nodes) ? g.nodes.map(toFlowNode) : [];
    const nextEdges = Array.isArray(g.edges)
      ? g.edges.map((e, idx) => ({
          id: String(e.id || `e${idx + 1}`),
          source: String(e.source || ""),
          target: String(e.target || ""),
          data: { contract: String(e.contract || "generic") },
        }))
      : [];
    setNodes(nextNodes);
    setEdges(nextEdges);
    setSelectedNodeId(nextNodes.length > 0 ? String(nextNodes[0].id) : "");
  }, [setEdges, setNodes]);

  const fetchTemplates = React.useCallback(async () => {
    setStatus("loading templates...", "status-warn");
    try {
      const payload = await getGraphTemplates(apiBase);
      const rows = Array.isArray(payload.templates) ? payload.templates : [];
      setTemplates(rows);
      if (rows.length > 0 && rows[0].graph) {
        applyGraph(rows[0].graph);
      }
      setStatus(`templates loaded: ${rows.length}`, "status-ok");
    } catch (err) {
      setStatus(`template load failed: ${String(err.message || err)}`, "status-err");
    }
  }, [apiBase, applyGraph, setStatus]);

  React.useEffect(() => {
    fetchTemplates();
  }, [fetchTemplates]);

  const onConnect = React.useCallback(
    (params) => setEdges((eds) => addEdge({ ...params, data: { contract: "generic" } }, eds)),
    [setEdges]
  );

  const addNodeByType = React.useCallback((nodeType) => {
    const idx = nodes.length;
    const id = `${String(nodeType || "Node")}_${idx + 1}`;
    const col = idx % 4;
    const row = Math.floor(idx / 4);
    setNodes((prev) =>
      prev.concat({
        id,
        type: "default",
        position: { x: 80 + col * 230, y: 80 + row * 130 },
        data: { label: `${nodeType}\n${id}`, nodeType, params: {} },
      })
    );
    setSelectedNodeId(id);
  }, [nodes.length, setNodes]);

  const applySelectedNodeParams = React.useCallback(() => {
    if (!selectedNode) {
      setStatus("select a node first", "status-warn");
      return;
    }
    try {
      const obj = JSON.parse(selectedNodeParamsText || "{}");
      setNodes((prev) =>
        prev.map((n) => {
          if (String(n.id) !== String(selectedNode.id)) return n;
          return {
            ...n,
            data: {
              ...(n.data || {}),
              params: obj,
            },
          };
        })
      );
      setStatus(`params updated: ${selectedNode.id}`, "status-ok");
    } catch (err) {
      setStatus(`invalid params json: ${String(err.message || err)}`, "status-err");
    }
  }, [selectedNode, selectedNodeParamsText, setNodes, setStatus]);

  const runGraphValidation = React.useCallback(async () => {
    const graph = toGraphPayload({ graphId, profile, nodes, edges });
    setStatus("validating graph...", "status-warn");
    try {
      const payload = await validateGraphContract(apiBase, graph);
      const gv = payload.graph_validation || {};
      const ok = Boolean(gv.valid);
      const lines = [
        `valid: ${ok}`,
        `nodes: ${Number(gv?.stats?.node_count || 0)}, edges: ${Number(gv?.stats?.edge_count || 0)}`,
        `sources/sinks: ${Number(gv?.stats?.source_count || 0)}/${Number(gv?.stats?.sink_count || 0)}`,
        "",
        "errors:",
        ...(Array.isArray(gv.errors) && gv.errors.length > 0 ? gv.errors.map((x) => `- ${x}`) : ["- none"]),
        "",
        "warnings:",
        ...(Array.isArray(gv.warnings) && gv.warnings.length > 0 ? gv.warnings.map((x) => `- ${x}`) : ["- none"]),
        "",
        `topological_order: ${(gv?.normalized?.topological_order || []).join(" -> ") || "-"}`,
      ];
      setValidationText(lines.join("\n"));
      setStatus(ok ? "graph valid" : "graph invalid", ok ? "status-ok" : "status-err");
    } catch (err) {
      setValidationText(`validate failed\n- ${String(err.message || err)}`);
      setStatus(`validate failed: ${String(err.message || err)}`, "status-err");
    }
  }, [apiBase, edges, graphId, nodes, profile, setStatus]);

  const runtimeSummary = React.useMemo(() => {
    const meta = graphRunSummary?.radar_map_summary?.metadata || {};
    const runtimeResolution = meta?.runtime_resolution && typeof meta.runtime_resolution === "object"
      ? meta.runtime_resolution
      : {};
    const antennaSummary = meta?.antenna_summary && typeof meta.antenna_summary === "object"
      ? meta.antenna_summary
      : {};
    const providerInfo = runtimeResolution?.provider_runtime_info && typeof runtimeResolution.provider_runtime_info === "object"
      ? runtimeResolution.provider_runtime_info
      : {};
    const backendTypeObserved = String(meta?.backend_type || "").trim();
    const runtimeModeObserved = String(runtimeResolution?.mode || "").trim();
    const simulationBackendObserved = String(
      providerInfo?.simulation_backend || providerInfo?.generator || ""
    ).trim();
    const multiplexingObserved = String(providerInfo?.multiplexing_mode || "").trim();
    const licenseObserved = String(
      providerInfo?.license_file || providerInfo?.license_file_hint || ""
    ).trim();
    const antennaModeObserved = String(antennaSummary?.antenna_mode || "").trim();
    const ffdRequested = String(runtimeTxFfdFilesText || "").trim() !== ""
      || String(runtimeRxFfdFilesText || "").trim() !== "";
    const runtimeStatusLine = [
      `backend=${backendTypeObserved || runtimeBackendType || "-"}`,
      `mode=${runtimeModeObserved || "-"}`,
      `sim=${simulationBackendObserved || "-"}`,
      `mux=${multiplexingObserved || runtimeMultiplexingMode || "-"}`,
      `ant=${antennaModeObserved || (ffdRequested ? "ffd_requested" : "isotropic")}`,
      `license=${licenseObserved ? "set" : (runtimeLicenseFile ? "requested" : "none")}`,
    ].join(" | ");
    return {
      backendTypeObserved,
      runtimeModeObserved,
      simulationBackendObserved,
      multiplexingObserved,
      antennaModeObserved,
      licenseObserved,
      runtimeStatusLine,
    };
  }, [
    graphRunSummary,
    runtimeBackendType,
    runtimeLicenseFile,
    runtimeMultiplexingMode,
    runtimeRxFfdFilesText,
    runtimeTxFfdFilesText,
  ]);

  const {
    runGraphViaApi,
    cancelLastGraphRun,
    retryLastGraphRun,
    pollLastGraphRunOnce,
    openGraphRunById,
  } = useGraphRunOps({
    apiBase,
    profile,
    graphId,
    sceneJsonPath,
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
    nodes,
    edges,
    runMode,
    autoPollAsyncRun,
    pollIntervalMsText,
    lastGraphRunId,
    setStatus,
    setGraphRunText,
    setGraphRunSummary,
    setLastGraphRunId,
    setPollStateText,
    setPollingActive,
    setGateResultText,
    setLastPolicyEval,
    onContractDiagnosticsEvent: appendContractDiagnosticsEvent,
  });

  const {
    pinBaselineFromGraphRun,
    runPolicyGateForGraphRun,
    exportGateReport,
  } = useGateOps({
    apiBase,
    graphRunSummary,
    baselineId,
    graphId,
    lastPolicyEval,
    contractTimeline,
    setStatus,
    setGateResultText,
    setLastPolicyEval,
    onContractDiagnosticsEvent: appendContractDiagnosticsEvent,
  });

  const runDecisionRegressionSession = React.useCallback(async () => {
    const currentRunIdRaw = String(
      graphRunSummary?.graph_run_id || graphRunSummary?.run_id || ""
    ).trim();
    const currentRunId = currentRunIdRaw.startsWith("run_") ? currentRunIdRaw : "";
    const currentSummary = String(graphRunSummary?.outputs?.graph_run_summary_json || "").trim();
    const compareRunIdRaw = String(compareGraphRunId || "").trim();
    const compareRunId = compareRunIdRaw.startsWith("run_") ? compareRunIdRaw : "";
    const compareSummary = String(
      compareGraphRunSummary?.outputs?.graph_run_summary_json || ""
    ).trim();
    const baseline = String(baselineId || "").trim();

    if (!baseline) {
      setStatus("baseline id is required for regression session", "status-warn");
      return;
    }
    if (!currentRunIdRaw && !currentSummary) {
      setStatus("run graph first before regression session", "status-warn");
      return;
    }

    const candidatesRaw = [];
    if (compareRunId || compareSummary) {
      candidatesRaw.push({
        label: "compare",
        run_id: compareRunId || undefined,
        summary_json: compareSummary || undefined,
      });
    }
    if (currentRunId || currentSummary) {
      candidatesRaw.push({
        label: "current",
        run_id: currentRunId || undefined,
        summary_json: currentSummary || undefined,
      });
    }
    const seen = new Set();
    const candidates = candidatesRaw.filter((row) => {
      const key = `${String(row.run_id || "")}::${String(row.summary_json || "")}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
    if (candidates.length === 0) {
      setStatus("no candidates available for regression session", "status-warn");
      return;
    }

    const sessionId = `dssn_${Date.now()}`;
    setStatus(`running regression session: ${sessionId}`, "status-warn");
    try {
      const payload = await runRegressionSession(apiBase, {
        session_id: sessionId,
        baseline_id: baseline,
        candidates,
        stop_on_first_fail: false,
        overwrite: true,
        note: "decision pane quick session",
        tag: "graph_lab_decision_pane",
      });
      const row = payload.regression_session || {};
      setLastRegressionSession(row);
      setDecisionOpsStatusText(
        `regression_session_id=${String(row.session_id || sessionId)} | evaluated=${Number(row.evaluated_candidate_count || 0)} | held=${Number(row.held_count || 0)} | recommendation=${String(row.recommendation || "-")}`
      );
      setStatus(`regression session completed: ${String(row.session_id || sessionId)}`, "status-ok");
    } catch (err) {
      setDecisionOpsStatusText(`regression_session_failed: ${String(err.message || err)}`);
      setStatus(`regression session failed: ${String(err.message || err)}`, "status-err");
    }
  }, [
    apiBase,
    baselineId,
    compareGraphRunId,
    compareGraphRunSummary,
    graphRunSummary,
    setStatus,
  ]);

  const exportDecisionRegressionSession = React.useCallback(async () => {
    const sessionId = String(lastRegressionSession?.session_id || "").trim();
    if (!sessionId) {
      setStatus("run regression session first", "status-warn");
      return;
    }
    setStatus(`exporting regression session: ${sessionId}`, "status-warn");
    try {
      const payload = await exportRegressionSession(apiBase, {
        session_id: sessionId,
        overwrite: true,
        include_policy_payload: false,
        note: "decision pane export",
        tag: "graph_lab_decision_pane",
      });
      const row = payload.regression_export || {};
      setLastRegressionExport(row);
      setDecisionOpsStatusText(
        `regression_export_id=${String(row.export_id || "-")} | rows=${Number(row.row_count || 0)} | recommendation=${String(row.session_recommendation || "-")}`
      );
      setStatus(`regression export completed: ${String(row.export_id || "-")}`, "status-ok");
    } catch (err) {
      setDecisionOpsStatusText(`regression_export_failed: ${String(err.message || err)}`);
      setStatus(`regression export failed: ${String(err.message || err)}`, "status-err");
    }
  }, [apiBase, lastRegressionSession, setStatus]);

  const decisionSummaryText = React.useMemo(() => {
    const nowIso = new Date().toISOString();
    const currentRunId = String(
      graphRunSummary?.graph_run_id || graphRunSummary?.run_id || ""
    ).trim() || "-";
    const compareRunId = String(compareGraphRunSummary?.graph_run_id || compareGraphRunId || "").trim() || "-";
    const recommendation = String(lastPolicyEval?.recommendation || "unknown");
    const gateKnown = typeof lastPolicyEval?.gate_failed === "boolean";
    const gateFailed = gateKnown ? Boolean(lastPolicyEval?.gate_failed) : null;
    const decision = gateKnown ? (gateFailed ? "HOLD" : "ADOPT") : "UNKNOWN";
    const failureRows = Array.isArray(lastPolicyEval?.gate_failures) ? lastPolicyEval.gate_failures : [];
    const currentPathCount = Number(graphRunSummary?.path_summary?.path_count_total || 0);
    const comparePathCount = Number(compareGraphRunSummary?.path_summary?.path_count_total || 0);
    const pathDelta = currentPathCount - comparePathCount;

    const currentRdPeak = Array.isArray(graphRunSummary?.quicklook?.rd_top_peaks)
      ? graphRunSummary.quicklook.rd_top_peaks[0] || null
      : null;
    const compareRdPeak = Array.isArray(compareGraphRunSummary?.quicklook?.rd_top_peaks)
      ? compareGraphRunSummary.quicklook.rd_top_peaks[0] || null
      : null;
    const currentRaPeak = Array.isArray(graphRunSummary?.quicklook?.ra_top_peaks)
      ? graphRunSummary.quicklook.ra_top_peaks[0] || null
      : null;
    const compareRaPeak = Array.isArray(compareGraphRunSummary?.quicklook?.ra_top_peaks)
      ? compareGraphRunSummary.quicklook.ra_top_peaks[0] || null
      : null;
    const signed = (value) => {
      const n = Number(value || 0);
      return `${n >= 0 ? "+" : ""}${n}`;
    };

    const lines = [
      `generated_at_utc: ${nowIso}`,
      `decision: ${decision}`,
      `recommendation: ${recommendation}`,
      `baseline_id: ${String(baselineId || "-")}`,
      `current_run_id: ${currentRunId}`,
      `compare_run_id: ${compareRunId}`,
      `gate_failure_count: ${Number(failureRows.length || 0)}`,
      `path_count_delta(current-compare): ${signed(pathDelta)}`,
    ];

    if (currentRdPeak && compareRdPeak) {
      lines.push(
        `rd_peak_delta(range/doppler): ${signed(Number(currentRdPeak.range_bin || 0) - Number(compareRdPeak.range_bin || 0))}/${signed(Number(currentRdPeak.doppler_bin || 0) - Number(compareRdPeak.doppler_bin || 0))}`
      );
    }
    if (currentRaPeak && compareRaPeak) {
      lines.push(
        `ra_peak_delta(range/angle): ${signed(Number(currentRaPeak.range_bin || 0) - Number(compareRaPeak.range_bin || 0))}/${signed(Number(currentRaPeak.angle_bin || 0) - Number(compareRaPeak.angle_bin || 0))}`
      );
    }
    if (failureRows.length > 0) {
      lines.push("top_failure_evidence:");
      failureRows.slice(0, 3).forEach((row, idx) => {
        const metric = row?.metric ? `(${String(row.metric)})` : "";
        lines.push(
          `- [${Number(idx) + 1}] ${String(row?.rule || "unknown_rule")}${metric} value=${String(row?.value ?? "-")} limit=${String(row?.limit ?? "-")}`
        );
      });
    }
    return lines.join("\n");
  }, [
    baselineId,
    compareGraphRunId,
    compareGraphRunSummary,
    graphRunSummary,
    lastPolicyEval,
  ]);

  const exportDecisionBriefMd = React.useCallback(() => {
    const nowIso = new Date().toISOString();
    const fileStamp = nowIso.slice(0, 19).replace(/[:T]/g, "_");
    const currentOutputs = graphRunSummary?.outputs && typeof graphRunSummary.outputs === "object"
      ? graphRunSummary.outputs
      : {};
    const compareOutputs = compareGraphRunSummary?.outputs && typeof compareGraphRunSummary.outputs === "object"
      ? compareGraphRunSummary.outputs
      : {};
    const failures = Array.isArray(lastPolicyEval?.gate_failures) ? lastPolicyEval.gate_failures : [];
    const lines = [
      "# Radar Decision Brief",
      "",
      `- generated_at_utc: ${nowIso}`,
      `- graph_id: ${String(graphId || "-")}`,
      "",
      "## Decision Snapshot",
      "```text",
      decisionSummaryText,
      "```",
      "",
      "## Current Artifacts",
      `- graph_run_summary_json: ${String(currentOutputs.graph_run_summary_json || "-")}`,
      `- radar_map_npz: ${String(currentOutputs.radar_map_npz || "-")}`,
      `- adc_cube_npz: ${String(currentOutputs.adc_cube_npz || "-")}`,
      `- path_list_json: ${String(currentOutputs.path_list_json || "-")}`,
      "",
      "## Compare Artifacts",
      `- graph_run_summary_json: ${String(compareOutputs.graph_run_summary_json || "-")}`,
      `- radar_map_npz: ${String(compareOutputs.radar_map_npz || "-")}`,
      `- adc_cube_npz: ${String(compareOutputs.adc_cube_npz || "-")}`,
      `- path_list_json: ${String(compareOutputs.path_list_json || "-")}`,
      "",
      "## Gate Evidence",
    ];
    if (failures.length === 0) {
      lines.push("- none");
    } else {
      failures.slice(0, 8).forEach((row, idx) => {
        const metric = row?.metric ? ` (${String(row.metric)})` : "";
        lines.push(
          `- [${Number(idx) + 1}] ${String(row?.rule || "unknown_rule")}${metric}: value=${String(row?.value ?? "-")} limit=${String(row?.limit ?? "-")}`
        );
      });
    }
    lines.push(
      "",
      "## Regression Session",
      `- session_id: ${String(lastRegressionSession?.session_id || "-")}`,
      `- session_recommendation: ${String(lastRegressionSession?.recommendation || "-")}`,
      `- export_id: ${String(lastRegressionExport?.export_id || "-")}`,
      `- export_package_json: ${String(lastRegressionExport?.artifacts?.package_json || "-")}`
    );

    const text = lines.join("\n");
    const blob = new Blob([text], { type: "text/markdown;charset=utf-8" });
    const href = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = href;
    a.download = `decision_brief_${String(graphId || "graph")}_${fileStamp}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.setTimeout(() => URL.revokeObjectURL(href), 1000);
    setDecisionOpsStatusText(`decision_brief_exported_at=${nowIso}`);
    setStatus("decision brief exported", "status-ok");
  }, [
    compareGraphRunSummary,
    decisionSummaryText,
    graphId,
    graphRunSummary,
    lastPolicyEval,
    lastRegressionExport,
    lastRegressionSession,
    setStatus,
  ]);

  const loadTemplateByIndex = React.useCallback((idx) => {
    const i = Math.max(0, Math.floor(Number(idx)));
    const row = templates[i];
    if (!row || !row.graph) {
      setStatus("template not found", "status-warn");
      return;
    }
    applyGraph(row.graph);
    setValidationText("-");
    setStatus(`template applied: ${row.template_id || i}`, "status-ok");
  }, [applyGraph, setStatus, templates]);

  const exportGraph = React.useCallback(() => {
    const payload = toGraphPayload({ graphId, profile, nodes, edges });
    const text = JSON.stringify(payload, null, 2);
    const blob = new Blob([text], { type: "application/json;charset=utf-8" });
    const href = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = href;
    a.download = `${payload.graph_id || "graph"}_schema_v1.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.setTimeout(() => URL.revokeObjectURL(href), 1000);
    setStatus("graph exported", "status-ok");
  }, [edges, graphId, nodes, profile, setStatus]);

  const pipelineStages = React.useMemo(() => {
    const hasDesign = Number(nodes.length || 0) > 0;
    const hasRun = Boolean(graphRunSummary && (graphRunSummary.graph_run_id || graphRunSummary.run_id));
    const hasInspect = Boolean(
      hasRun && (
        compareGraphRunSummary
        || (graphRunSummary && typeof graphRunSummary === "object")
      )
    );
    const hasGate = typeof lastPolicyEval?.gate_failed === "boolean";
    const hasExport = Boolean(lastRegressionExport || lastRegressionSession);
    const activeId = hasExport
      ? "export"
      : hasGate
        ? "gate"
        : hasInspect
          ? "inspect"
          : hasRun
            ? "run"
            : "design";
    return [
      { id: "design", label: "Design", done: hasDesign, active: activeId === "design" },
      { id: "run", label: "Run", done: hasRun, active: activeId === "run" },
      { id: "inspect", label: "Inspect", done: hasInspect, active: activeId === "inspect" },
      { id: "gate", label: "Gate", done: hasGate, active: activeId === "gate" },
      { id: "export", label: "Export", done: hasExport, active: activeId === "export" },
    ];
  }, [
    compareGraphRunSummary,
    graphRunSummary,
    lastPolicyEval,
    lastRegressionExport,
    lastRegressionSession,
    nodes.length,
  ]);

  const toggleFocusLeftDrawer = React.useCallback(() => {
    setFocusLeftOpen((prev) => !prev);
  }, []);

  const toggleFocusRightDrawer = React.useCallback(() => {
    setFocusRightOpen((prev) => !prev);
  }, []);

  const closeFocusDrawers = React.useCallback(() => {
    setFocusLeftOpen(false);
    setFocusRightOpen(false);
  }, []);

  const focusAnyOpen = layoutMode === "focus" && (focusLeftOpen || focusRightOpen);
  React.useEffect(() => {
    if (layoutMode !== "focus" || !focusAnyOpen) return undefined;
    const onKeyDown = (event) => {
      if (String(event?.key || "") !== "Escape") return;
      const target = event?.target;
      const tag = String(target?.tagName || "").toLowerCase();
      if (target?.isContentEditable || tag === "input" || tag === "textarea" || tag === "select") {
        return;
      }
      closeFocusDrawers();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [closeFocusDrawers, focusAnyOpen, layoutMode]);

  const contentClassName = `content view-${layoutMode}${focusLeftOpen ? " focus-left-open" : ""}${focusRightOpen ? " focus-right-open" : ""}${focusAnyOpen ? " focus-any-open" : ""}`;

  const inputPanelModel = React.useMemo(() => normalizeGraphInputsPanelModel({
    values: {
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
      runtimeStatusLine: runtimeSummary.runtimeStatusLine,
      runMode,
      autoPollAsyncRun,
      pollIntervalMsText,
      pollStateText,
      pollingActive,
      templates,
      lastGraphRunId,
      contractDebugText,
      contractOverlayEnabled,
      contractTimelineCount: contractTimeline.length,
    },
    setters: {
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
      setRunMode,
      setAutoPollAsyncRun,
      setPollIntervalMsText,
      setContractOverlayEnabled,
    },
    templateActions: {
      fetchTemplates,
      exportGraph,
      loadTemplateByIndex,
    },
    graphActions: {
      addNodeByType,
      runGraphValidation,
    },
    runActions: {
      runGraphViaApi,
      retryLastGraphRun,
      cancelLastGraphRun,
      pollLastGraphRunOnce: () => pollLastGraphRunOnce(pollingActive),
    },
    gateActions: {
      pinBaselineFromGraphRun,
      runPolicyGateForGraphRun,
      exportGateReport,
    },
    contractActions: {
      refreshContractWarnings,
      resetContractWarnings,
      clearContractTimeline,
    },
  }), [
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
    runtimeSummary.runtimeStatusLine,
    runMode,
    autoPollAsyncRun,
    pollIntervalMsText,
    pollStateText,
    pollingActive,
    templates,
    lastGraphRunId,
    contractDebugText,
    contractOverlayEnabled,
    contractTimeline.length,
    fetchTemplates,
    exportGraph,
    loadTemplateByIndex,
    addNodeByType,
    runGraphValidation,
    runGraphViaApi,
    retryLastGraphRun,
    cancelLastGraphRun,
    pollLastGraphRunOnce,
    pinBaselineFromGraphRun,
    runPolicyGateForGraphRun,
    exportGateReport,
    refreshContractWarnings,
    resetContractWarnings,
    clearContractTimeline,
    setContractOverlayEnabled,
  ]);

  return h("div", { className: `page density-${densityMode}` }, [
    h(TopBar, {
      key: "topbar",
      statusTone,
      statusText,
      nodeCount: nodes.length,
      edgeCount: edges.length,
      runtimeBackendType: runtimeSummary.backendTypeObserved || runtimeBackendType,
      runtimeMode: runtimeSummary.runtimeModeObserved || runtimeSimulationMode,
      runtimeLicenseTier,
      runtimeLicenseSet: Boolean(runtimeSummary.licenseObserved || runtimeLicenseFile),
      layoutMode,
      setLayoutMode,
      densityMode,
      setDensityMode,
      pipelineStages,
      focusLeftOpen,
      focusRightOpen,
      onToggleFocusLeft: toggleFocusLeftDrawer,
      onToggleFocusRight: toggleFocusRightDrawer,
    }),
    h("main", { className: contentClassName, key: "ct" }, [
      h("button", {
        type: "button",
        className: "focus-backdrop",
        key: "focus_backdrop",
        onClick: closeFocusDrawers,
        "aria-label": "Close focus drawers",
      }),
      h(GraphInputsPanel, {
        key: "left",
        model: inputPanelModel,
      }),
      h(GraphCanvasPanel, {
        key: "center",
        nodes,
        edges,
        onNodesChange,
        onEdgesChange,
        onConnect,
        setSelectedNodeId,
      }),
      h(NodeInspectorPanel, {
        key: "right",
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
        setCompareGraphRunId: setCompareGraphRunIdDraft,
        compareRunStatusText,
        compareGraphRunSummary,
        loadCompareGraphRunById,
        clearCompareGraphRun,
        baselineId,
        pinBaselineFromGraphRun,
        runPolicyGateForGraphRun,
        runDecisionRegressionSession,
        exportGateReport,
        exportDecisionRegressionSession,
        exportDecisionBriefMd,
        decisionSummaryText,
        decisionOpsStatusText,
        lastRegressionSession,
        lastRegressionExport,
        contractDebugText,
      }),
    ]),
    h(ContractWarningOverlay, {
      key: "contract_overlay",
      visible: contractOverlayEnabled,
      timeline: contractTimeline,
      onClose: () => setContractOverlayEnabled(false),
      onClear: clearContractTimeline,
      onExport: exportContractTimeline,
      onOpenRun: openGraphRunById,
      onOpenGateEvidence: openGateEvidenceFromTimeline,
    }),
  ]);
}

export default App;
