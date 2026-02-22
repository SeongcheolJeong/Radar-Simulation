import { React } from "../deps.mjs";
import { normalizeGraphRunOpsOptions } from "../contracts.mjs";
import { toGraphPayload } from "../graph_helpers.mjs";
import { buildGraphRunRecordText, clampPollIntervalMs } from "../run_monitor.mjs";
import {
  cancelGraphRun,
  getGraphRunMaybe,
  getGraphRunSummaryMaybe,
  retryGraphRun,
  runGraph,
} from "../api_client.mjs";

export function useGraphRunOps(opts) {
  const safeOpts = normalizeGraphRunOpsOptions(opts);
  const {
    apiBase,
    profile,
    graphId,
    sceneJsonPath,
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
  } = safeOpts;

  const normalizePollIntervalMs = React.useCallback(
    () => clampPollIntervalMs(pollIntervalMsText),
    [pollIntervalMsText]
  );

  const renderGraphRunRecord = React.useCallback((row, graphRunId, extraLines) => {
    setGraphRunText(buildGraphRunRecordText(row, graphRunId, extraLines));
  }, [setGraphRunText]);

  const loadGraphRunSummaryById = React.useCallback(async (graphRunId, fallbackRow) => {
    const sumRes = await getGraphRunSummaryMaybe(apiBase, graphRunId);
    if (!sumRes.ok) {
      const recRes = await getGraphRunMaybe(apiBase, graphRunId);
      if (recRes.ok) {
        const rec = recRes.payload || {};
        renderGraphRunRecord(rec, graphRunId, [
          `summary_fetch_error: graph summary request failed (${Number(sumRes.status)})`,
        ]);
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
      `- graph_run_summary_json: ${String(summary?.outputs?.graph_run_summary_json || "-")}`,
    ];
    setGraphRunText(lines.join("\n"));
    setGraphRunSummary(summary);
    setGateResultText("-");
    setLastPolicyEval(null);
    setStatus(`graph run completed: ${graphRunId}`, "status-ok");
    return { ok: true, summary };
  }, [
    apiBase,
    profile,
    renderGraphRunRecord,
    setGateResultText,
    setGraphRunSummary,
    setGraphRunText,
    setLastPolicyEval,
    setStatus,
  ]);

  const pollGraphRunUntilTerminal = React.useCallback(async (graphRunId) => {
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
          await loadGraphRunSummaryById(graphRunId, row);
          return { ok: true, status: "completed" };
        }
        if (status === "failed" || status === "canceled") {
          renderGraphRunRecord(row, graphRunId, [`poll_final_status: ${status}`]);
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
    const graph = toGraphPayload({ graphId, profile, nodes, edges });
    const runAsync = String(runMode || "sync") === "async";
    setStatus(
      runAsync ? "submitting graph run (async)..." : "submitting graph run...",
      "status-warn"
    );
    try {
      const payload = await runGraph(
        apiBase,
        {
          graph,
          scene_json_path: sceneJsonPath,
          profile,
          run_hybrid_estimation: false,
          tag: "graph_lab",
        },
        runAsync
      );
      const row = payload.graph_run || {};
      const graphRunId = String(row.graph_run_id || "").trim();
      if (!graphRunId) {
        throw new Error("graph run id missing in response");
      }
      setLastGraphRunId(graphRunId);
      setPollStateText(runAsync ? "async run submitted" : "-");
      const rowStatus = String(row.status || "").trim().toLowerCase();
      if (runAsync) {
        renderGraphRunRecord(row, graphRunId, [
          "run_mode: async",
          `polling: ${autoPollAsyncRun ? "auto" : "manual"}`,
        ]);
        setGraphRunSummary(null);
        setGateResultText("-");
        setLastPolicyEval(null);
        if (autoPollAsyncRun) {
          await pollGraphRunUntilTerminal(graphRunId);
        } else {
          setStatus(`graph run queued: ${graphRunId}`, "status-warn");
        }
        return;
      }
      if (rowStatus && rowStatus !== "completed") {
        renderGraphRunRecord(row, graphRunId);
        setGraphRunSummary(null);
        setGateResultText("-");
        setLastPolicyEval(null);
        const tone = rowStatus === "canceled" ? "status-warn" : "status-err";
        setStatus(`graph run ${rowStatus}: ${graphRunId}`, tone);
        return;
      }
      await loadGraphRunSummaryById(graphRunId, row);
    } catch (err) {
      setGraphRunText(`graph run failed\n- ${String(err.message || err)}`);
      setGraphRunSummary(null);
      setGateResultText("-");
      setLastPolicyEval(null);
      setStatus(`graph run failed: ${String(err.message || err)}`, "status-err");
    }
  }, [
    apiBase,
    autoPollAsyncRun,
    edges,
    graphId,
    loadGraphRunSummaryById,
    nodes,
    pollGraphRunUntilTerminal,
    profile,
    renderGraphRunRecord,
    runMode,
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
      const payload = await cancelGraphRun(apiBase, graphRunId, "graph_lab_manual_cancel");
      const row = payload.graph_run || {};
      renderGraphRunRecord(row, graphRunId, ["cancel_requested: true"]);
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
        renderGraphRunRecord(row, newGraphRunId, [
          "run_mode: async",
          `polling: ${autoPollAsyncRun ? "auto" : "manual"}`,
        ]);
        setGraphRunSummary(null);
        setGateResultText("-");
        setLastPolicyEval(null);
        if (autoPollAsyncRun) {
          await pollGraphRunUntilTerminal(newGraphRunId);
        } else {
          setStatus(`retry queued: ${newGraphRunId}`, "status-warn");
        }
        return;
      }
      if (rowStatus !== "completed") {
        renderGraphRunRecord(row, newGraphRunId);
        setGraphRunSummary(null);
        setGateResultText("-");
        setLastPolicyEval(null);
        setStatus(`retry ended with status: ${String(row.status || "-")}`, "status-warn");
        return;
      }
      await loadGraphRunSummaryById(newGraphRunId, row);
    } catch (err) {
      setStatus(`retry failed: ${String(err.message || err)}`, "status-err");
    }
  }, [
    apiBase,
    autoPollAsyncRun,
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
      await pollGraphRunUntilTerminal(graphRunId);
    } catch (err) {
      setStatus(`poll failed: ${String(err.message || err)}`, "status-err");
    }
  }, [lastGraphRunId, pollGraphRunUntilTerminal, setStatus]);

  return {
    runGraphViaApi,
    cancelLastGraphRun,
    retryLastGraphRun,
    pollLastGraphRunOnce,
  };
}
