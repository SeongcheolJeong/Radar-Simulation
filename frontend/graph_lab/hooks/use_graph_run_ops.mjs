import { React } from "../deps.mjs";
import {
  getContractWarningSnapshot,
  normalizeGraphRunOpsOptions,
} from "../contracts.mjs";
import { toGraphPayload } from "../graph_helpers.mjs";
import { buildGraphRunRecordText, clampPollIntervalMs } from "../run_monitor.mjs";
import { buildSceneOverrides } from "../runtime_overrides.mjs";
import {
  cancelGraphRun,
  getGraphRunMaybe,
  getGraphRunSummaryMaybe,
  retryGraphRun,
  runGraph,
} from "../api_client.mjs";

function applyRuntimeBackendToGraph(graph, backendType, runtimeProviderSpec) {
  const root = graph && typeof graph === "object" ? graph : {};
  const nodes = Array.isArray(root.nodes) ? root.nodes : [];
  const normalizedBackend = String(backendType || "").trim().toLowerCase();
  if (!normalizedBackend) return root;
  const normalizedProvider = String(runtimeProviderSpec || "").trim();
  return {
    ...root,
    nodes: nodes.map((node) => {
      if (!node || typeof node !== "object") return node;
      if (String(node.type || "").trim() !== "Propagation") return node;
      const params = node.params && typeof node.params === "object" ? { ...node.params } : {};
      params.backend = normalizedBackend;
      if (normalizedProvider) {
        params.runtime_provider = normalizedProvider;
      }
      return { ...node, params };
    }),
  };
}

export function useGraphRunOps(opts) {
  const safeOpts = normalizeGraphRunOpsOptions(opts);
  const {
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
    onContractDiagnosticsEvent,
  } = safeOpts;

  const normalizePollIntervalMs = React.useCallback(
    () => clampPollIntervalMs(pollIntervalMsText),
    [pollIntervalMsText]
  );

  const collectContractDiagnostics = React.useCallback((beforeSnapshot) => {
    const beforeUnique = Number(beforeSnapshot?.unique_warning_count || 0);
    const beforeAttempts = Number(beforeSnapshot?.attempt_count_total || 0);
    const s = getContractWarningSnapshot();
    const nowUnique = Number(s.unique_warning_count || 0);
    const nowAttempts = Number(s.attempt_count_total || 0);
    const uniqueDelta = nowUnique - beforeUnique;
    const attemptsDelta = nowAttempts - beforeAttempts;
    return {
      baseline: {
        unique_warning_count: beforeUnique,
        attempt_count_total: beforeAttempts,
      },
      snapshot: s,
      delta: {
        unique_warning_count: uniqueDelta,
        attempt_count_total: attemptsDelta,
      },
      lines: [
        `contract_warning_unique: ${nowUnique}`,
        `contract_warning_attempts: ${nowAttempts}`,
        `contract_warning_delta_unique: ${uniqueDelta >= 0 ? "+" : ""}${uniqueDelta}`,
        `contract_warning_delta_attempts: ${attemptsDelta >= 0 ? "+" : ""}${attemptsDelta}`,
      ],
    };
  }, []);

  const emitContractDiagnosticsEvent = React.useCallback((source, graphRunId, contract, note) => {
    const diag = contract && typeof contract === "object" && contract.snapshot
      ? contract
      : collectContractDiagnostics(contract);
    const payload = {
      event_source: String(source || "graph_run"),
      graph_run_id: String(graphRunId || ""),
      timestamp_ms: Date.now(),
      snapshot: diag.snapshot,
      delta: diag.delta,
      baseline: diag.baseline,
      note: note && typeof note === "object" ? { ...note } : {},
    };
    onContractDiagnosticsEvent(payload);
    return payload;
  }, [collectContractDiagnostics, onContractDiagnosticsEvent]);

  const renderGraphRunRecord = React.useCallback((row, graphRunId, extraLines, beforeSnapshot) => {
    const contract = collectContractDiagnostics(beforeSnapshot);
    setGraphRunText(buildGraphRunRecordText(row, graphRunId, [
      ...(Array.isArray(extraLines) ? extraLines.map((x) => String(x)) : []),
      ...contract.lines,
    ]));
    return contract;
  }, [collectContractDiagnostics, setGraphRunText]);

  const loadGraphRunSummaryById = React.useCallback(async (
    graphRunId,
    fallbackRow,
    beforeContractSnapshot,
    eventSource
  ) => {
    const sumRes = await getGraphRunSummaryMaybe(apiBase, graphRunId);
    if (!sumRes.ok) {
      const recRes = await getGraphRunMaybe(apiBase, graphRunId);
      if (recRes.ok) {
        const rec = recRes.payload || {};
        const contract = renderGraphRunRecord(rec, graphRunId, [
          `summary_fetch_error: graph summary request failed (${Number(sumRes.status)})`,
        ], beforeContractSnapshot);
        emitContractDiagnosticsEvent("graph_run_summary_missing", graphRunId, contract, {
          http_status: Number(sumRes.status),
        });
        setGraphRunSummary(null);
        setGateResultText("-");
        setLastPolicyEval(null);
        setStatus(`graph run failed: ${graphRunId}`, "status-err");
        return { ok: false, record: rec };
      }
      throw new Error(`graph summary request failed (${Number(sumRes.status)})`);
    }
    const summary = sumRes.payload || {};
    const quick = summary.quicklook || {};
    const cacheInfo = summary?.execution?.cache || {};
    const contract = collectContractDiagnostics(beforeContractSnapshot);
    const lines = [
      `graph_run_id: ${graphRunId}`,
      `status: ${summary.status || (fallbackRow && fallbackRow.status) || "-"}`,
      `graph_id: ${summary?.graph?.graph_id || "-"}`,
      `profile: ${summary.profile || profile}`,
      `nodes/edges: ${Number(summary?.graph?.node_count || 0)}/${Number(summary?.graph?.edge_count || 0)}`,
      `cache_hit: ${Boolean(cacheInfo?.hit)}`,
      `cache_scope: ${String(cacheInfo?.hit_scope || "-")}`,
      `cache_source_graph_run_id: ${String(cacheInfo?.source_graph_run_id || "-")}`,
      `path_count_total: ${Number(quick.path_count_total || 0)}`,
      `adc_shape: ${Array.isArray(quick.adc_shape) ? quick.adc_shape.join("x") : "-"}`,
      `rd_shape: ${Array.isArray(quick.rd_shape) ? quick.rd_shape.join("x") : "-"}`,
      `ra_shape: ${Array.isArray(quick.ra_shape) ? quick.ra_shape.join("x") : "-"}`,
      "",
      "artifacts:",
      `- path_list_json: ${String(summary?.outputs?.path_list_json || "-")}`,
      `- adc_cube_npz: ${String(summary?.outputs?.adc_cube_npz || "-")}`,
      `- radar_map_npz: ${String(summary?.outputs?.radar_map_npz || "-")}`,
      `- lgit_customized_output_npz: ${String(summary?.outputs?.lgit_customized_output_npz || "-")}`,
      `- graph_run_summary_json: ${String(summary?.outputs?.graph_run_summary_json || "-")}`,
      "",
      "contract_diagnostics:",
      ...contract.lines,
    ];
    setGraphRunText(lines.join("\n"));
    const runtimeDiag = {
      version: "graph_run_contract_diagnostics_v1",
      source: String(eventSource || "graph_run_summary"),
      graph_run_id: graphRunId,
      timestamp_ms: Date.now(),
      baseline: contract.baseline,
      snapshot: {
        contract_debug_version: String(contract.snapshot?.contract_debug_version || "-"),
        unique_warning_count: Number(contract.snapshot?.unique_warning_count || 0),
        attempt_count_total: Number(contract.snapshot?.attempt_count_total || 0),
      },
      delta: contract.delta,
    };
    setGraphRunSummary({
      ...summary,
      runtime_contract_diagnostics: runtimeDiag,
    });
    emitContractDiagnosticsEvent(
      runtimeDiag.source,
      graphRunId,
      contract,
      { cache_hit: Boolean(cacheInfo?.hit) }
    );
    setGateResultText("-");
    setLastPolicyEval(null);
    setStatus(`graph run completed: ${graphRunId}`, "status-ok");
    return { ok: true, summary };
  }, [
    apiBase,
    collectContractDiagnostics,
    emitContractDiagnosticsEvent,
    profile,
    renderGraphRunRecord,
    setGateResultText,
    setGraphRunSummary,
    setGraphRunText,
    setLastPolicyEval,
    setStatus,
  ]);

  const pollGraphRunUntilTerminal = React.useCallback(async (graphRunId, beforeContractSnapshot) => {
    const intervalMs = normalizePollIntervalMs();
    const maxPolls = 300;
    setPollingActive(true);
    setPollStateText(`polling graph run every ${intervalMs} ms`);
    try {
      for (let i = 0; i < maxPolls; i += 1) {
        const recRes = await getGraphRunMaybe(apiBase, graphRunId);
        if (!recRes.ok) throw new Error(`graph run poll failed (${Number(recRes.status)})`);
        const row = recRes.payload || {};
        const status = String(row?.status || "").trim().toLowerCase();
        setPollStateText(`poll #${i + 1} status=${status || "-"}`);
        if (status === "completed") {
          await loadGraphRunSummaryById(
            graphRunId,
            row,
            beforeContractSnapshot,
            "graph_run_poll_completed"
          );
          return { ok: true, status: "completed" };
        }
        if (status === "failed" || status === "canceled") {
          const contract = renderGraphRunRecord(
            row,
            graphRunId,
            [`poll_final_status: ${status}`],
            beforeContractSnapshot
          );
          emitContractDiagnosticsEvent(
            status === "canceled" ? "graph_run_poll_canceled" : "graph_run_poll_failed",
            graphRunId,
            contract,
            { poll_final_status: status }
          );
          setGraphRunSummary(null);
          setGateResultText("-");
          setLastPolicyEval(null);
          setStatus(
            status === "canceled" ? `graph run canceled: ${graphRunId}` : `graph run failed: ${graphRunId}`,
            status === "canceled" ? "status-warn" : "status-err"
          );
          return { ok: false, status };
        }
        await new Promise((resolve) => window.setTimeout(resolve, intervalMs));
      }
      throw new Error(`graph run poll timeout (${maxPolls} checks)`);
    } finally {
      setPollingActive(false);
    }
  }, [
    apiBase,
    emitContractDiagnosticsEvent,
    loadGraphRunSummaryById,
    normalizePollIntervalMs,
    renderGraphRunRecord,
    setGateResultText,
    setGraphRunSummary,
    setLastPolicyEval,
    setPollingActive,
    setPollStateText,
    setStatus,
  ]);

  const runGraphViaApi = React.useCallback(async () => {
    const graphRaw = toGraphPayload({ graphId, profile, nodes, edges });
    const graph = applyRuntimeBackendToGraph(graphRaw, runtimeBackendType, runtimeProviderSpec);
    const sceneOverrides = buildSceneOverrides({
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
    });
    const runAsync = String(runMode || "sync") === "async";
    const beforeContractSnapshot = getContractWarningSnapshot();
    let submittedGraphRunId = "";
    setStatus(
      runAsync ? "submitting graph run (async)..." : "submitting graph run...",
      "status-warn"
    );
    try {
      const requestPayload = {
        graph,
        scene_json_path: sceneJsonPath,
        profile,
        run_hybrid_estimation: false,
        tag: "graph_lab",
      };
      if (sceneOverrides) {
        requestPayload.scene_overrides = sceneOverrides;
      }
      const payload = await runGraph(
        apiBase,
        requestPayload,
        runAsync
      );
      const row = payload.graph_run || {};
      const graphRunId = String(row.graph_run_id || "").trim();
      submittedGraphRunId = graphRunId;
      if (!graphRunId) {
        throw new Error("graph run id missing in response");
      }
      setLastGraphRunId(graphRunId);
      setPollStateText(runAsync ? "async run submitted" : "-");
      const rowStatus = String(row.status || "").trim().toLowerCase();
      if (runAsync) {
        const contract = renderGraphRunRecord(row, graphRunId, [
          "run_mode: async",
          `polling: ${autoPollAsyncRun ? "auto" : "manual"}`,
        ], beforeContractSnapshot);
        emitContractDiagnosticsEvent("graph_run_async_submitted", graphRunId, contract, {
          auto_poll: Boolean(autoPollAsyncRun),
        });
        setGraphRunSummary(null);
        setGateResultText("-");
        setLastPolicyEval(null);
        if (autoPollAsyncRun) {
          await pollGraphRunUntilTerminal(graphRunId, beforeContractSnapshot);
        } else {
          setStatus(`graph run queued: ${graphRunId}`, "status-warn");
        }
        return;
      }
      if (rowStatus && rowStatus !== "completed") {
        const contract = renderGraphRunRecord(row, graphRunId, [], beforeContractSnapshot);
        emitContractDiagnosticsEvent("graph_run_non_completed", graphRunId, contract, {
          status: rowStatus,
        });
        setGraphRunSummary(null);
        setGateResultText("-");
        setLastPolicyEval(null);
        const tone = rowStatus === "canceled" ? "status-warn" : "status-err";
        setStatus(`graph run ${rowStatus}: ${graphRunId}`, tone);
        return;
      }
      await loadGraphRunSummaryById(
        graphRunId,
        row,
        beforeContractSnapshot,
        "graph_run_sync_completed"
      );
    } catch (err) {
      const contract = collectContractDiagnostics(beforeContractSnapshot);
      setGraphRunText([
        "graph run failed",
        `- ${String(err.message || err)}`,
        ...contract.lines.map((line) => `- ${line}`),
      ].join("\n"));
      emitContractDiagnosticsEvent(
        "graph_run_submit_error",
        submittedGraphRunId,
        contract,
        { error: String(err.message || err) }
      );
      setGraphRunSummary(null);
      setGateResultText("-");
      setLastPolicyEval(null);
      setStatus(`graph run failed: ${String(err.message || err)}`, "status-err");
    }
  }, [
    apiBase,
    autoPollAsyncRun,
    collectContractDiagnostics,
    edges,
    emitContractDiagnosticsEvent,
    graphId,
    loadGraphRunSummaryById,
    nodes,
    pollGraphRunUntilTerminal,
    profile,
    renderGraphRunRecord,
    runMode,
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
    sceneJsonPath,
    setGateResultText,
    setGraphRunSummary,
    setGraphRunText,
    setLastGraphRunId,
    setLastPolicyEval,
    setPollStateText,
    setStatus,
  ]);

  const cancelLastGraphRun = React.useCallback(async () => {
    const graphRunId = String(lastGraphRunId || "").trim();
    if (!graphRunId) {
      setStatus("no graph run id to cancel", "status-warn");
      return;
    }
    setStatus(`canceling graph run: ${graphRunId}`, "status-warn");
    try {
      const beforeContractSnapshot = getContractWarningSnapshot();
      const payload = await cancelGraphRun(apiBase, graphRunId, "graph_lab_manual_cancel");
      const row = payload.graph_run || {};
      const contract = renderGraphRunRecord(
        row,
        graphRunId,
        ["cancel_requested: true"],
        beforeContractSnapshot
      );
      emitContractDiagnosticsEvent("graph_run_cancel_requested", graphRunId, contract, {
        cancel_requested: true,
      });
      setGraphRunSummary(null);
      setGateResultText("-");
      setLastPolicyEval(null);
      setPollStateText("cancel requested");
      setStatus(`cancel requested: ${graphRunId}`, "status-warn");
    } catch (err) {
      setStatus(`cancel failed: ${String(err.message || err)}`, "status-err");
    }
  }, [
    apiBase,
    emitContractDiagnosticsEvent,
    lastGraphRunId,
    renderGraphRunRecord,
    setGateResultText,
    setGraphRunSummary,
    setLastPolicyEval,
    setPollStateText,
    setStatus,
  ]);

  const retryLastGraphRun = React.useCallback(async () => {
    const graphRunId = String(lastGraphRunId || "").trim();
    if (!graphRunId) {
      setStatus("no graph run id to retry", "status-warn");
      return;
    }
    const runAsync = String(runMode || "sync") === "async";
    const beforeContractSnapshot = getContractWarningSnapshot();
    setStatus(`retrying graph run: ${graphRunId}${runAsync ? " (async)" : ""}`, "status-warn");
    try {
      const payload = await retryGraphRun(
        apiBase,
        graphRunId,
        runAsync,
        {
          cache: { enable: false, mode: "off" },
          tag: "graph_lab_retry",
        }
      );
      const row = payload.graph_run || {};
      const newGraphRunId = String(row.graph_run_id || "").trim();
      if (!newGraphRunId) throw new Error("retry response missing graph_run_id");
      setLastGraphRunId(newGraphRunId);
      setPollStateText(runAsync ? "async retry submitted" : "-");

      const rowStatus = String(row.status || "").trim().toLowerCase();
      if (runAsync) {
        const contract = renderGraphRunRecord(row, newGraphRunId, [
          "run_mode: async",
          `polling: ${autoPollAsyncRun ? "auto" : "manual"}`,
        ], beforeContractSnapshot);
        emitContractDiagnosticsEvent("graph_run_retry_async_submitted", newGraphRunId, contract, {
          auto_poll: Boolean(autoPollAsyncRun),
        });
        setGraphRunSummary(null);
        setGateResultText("-");
        setLastPolicyEval(null);
        if (autoPollAsyncRun) {
          await pollGraphRunUntilTerminal(newGraphRunId, beforeContractSnapshot);
        } else {
          setStatus(`retry queued: ${newGraphRunId}`, "status-warn");
        }
        return;
      }
      if (rowStatus !== "completed") {
        const contract = renderGraphRunRecord(
          row,
          newGraphRunId,
          [],
          beforeContractSnapshot
        );
        emitContractDiagnosticsEvent("graph_run_retry_non_completed", newGraphRunId, contract, {
          status: String(row.status || "-"),
        });
        setGraphRunSummary(null);
        setGateResultText("-");
        setLastPolicyEval(null);
        setStatus(`retry ended with status: ${String(row.status || "-")}`, "status-warn");
        return;
      }
      await loadGraphRunSummaryById(
        newGraphRunId,
        row,
        beforeContractSnapshot,
        "graph_run_retry_completed"
      );
    } catch (err) {
      setStatus(`retry failed: ${String(err.message || err)}`, "status-err");
    }
  }, [
    apiBase,
    autoPollAsyncRun,
    emitContractDiagnosticsEvent,
    lastGraphRunId,
    loadGraphRunSummaryById,
    pollGraphRunUntilTerminal,
    renderGraphRunRecord,
    runMode,
    setGateResultText,
    setGraphRunSummary,
    setLastGraphRunId,
    setLastPolicyEval,
    setPollStateText,
    setStatus,
  ]);

  const pollLastGraphRunOnce = React.useCallback(async (pollingActive) => {
    const graphRunId = String(lastGraphRunId || "").trim();
    if (!graphRunId) {
      setStatus("no graph run id to poll", "status-warn");
      return;
    }
    if (pollingActive) {
      setStatus("poll already in progress", "status-warn");
      return;
    }
    setStatus(`polling graph run: ${graphRunId}`, "status-warn");
    try {
      await pollGraphRunUntilTerminal(graphRunId, getContractWarningSnapshot());
    } catch (err) {
      setStatus(`poll failed: ${String(err.message || err)}`, "status-err");
    }
  }, [lastGraphRunId, pollGraphRunUntilTerminal, setStatus]);

  const openGraphRunById = React.useCallback(async (graphRunIdInput) => {
    const graphRunId = String(graphRunIdInput || "").trim();
    if (!graphRunId) {
      setStatus("graph run id is required", "status-warn");
      return;
    }
    const beforeContractSnapshot = getContractWarningSnapshot();
    setLastGraphRunId(graphRunId);
    setPollStateText("-");
    setStatus(`opening graph run: ${graphRunId}`, "status-warn");
    try {
      const recRes = await getGraphRunMaybe(apiBase, graphRunId);
      if (!recRes.ok) {
        throw new Error(`graph run lookup failed (${Number(recRes.status)})`);
      }
      const row = recRes.payload || {};
      const status = String(row?.status || "").trim().toLowerCase();
      if (status === "completed") {
        await loadGraphRunSummaryById(
          graphRunId,
          row,
          beforeContractSnapshot,
          "graph_run_overlay_open"
        );
        return;
      }
      const contract = renderGraphRunRecord(
        row,
        graphRunId,
        ["opened_from_overlay: true"],
        beforeContractSnapshot
      );
      emitContractDiagnosticsEvent("graph_run_overlay_open_non_completed", graphRunId, contract, {
        status,
      });
      setGraphRunSummary(null);
      setGateResultText("-");
      setLastPolicyEval(null);
      const tone = status === "failed" ? "status-err" : "status-warn";
      setStatus(`graph run ${status || "-"}: ${graphRunId}`, tone);
    } catch (err) {
      setStatus(`open graph run failed: ${String(err.message || err)}`, "status-err");
    }
  }, [
    apiBase,
    emitContractDiagnosticsEvent,
    loadGraphRunSummaryById,
    renderGraphRunRecord,
    setGateResultText,
    setGraphRunSummary,
    setLastGraphRunId,
    setLastPolicyEval,
    setPollStateText,
    setStatus,
  ]);

  return {
    runGraphViaApi,
    cancelLastGraphRun,
    retryLastGraphRun,
    pollLastGraphRunOnce,
    openGraphRunById,
  };
}
