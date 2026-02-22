import {
  React,
  addEdge,
  useNodesState,
  useEdgesState,
} from "./deps.mjs";
import { toFlowNode, toGraphPayload } from "./graph_helpers.mjs";
import { buildGraphRunRecordText, clampPollIntervalMs } from "./run_monitor.mjs";
import {
  cancelGraphRun,
  createBaseline,
  evaluatePolicyGate,
  getGraphRunMaybe,
  getGraphRunSummaryMaybe,
  getGraphTemplates,
  retryGraphRun,
  runGraph,
  validateGraphContract,
} from "./api_client.mjs";
import {
  GraphCanvasPanel,
  GraphInputsPanel,
  NodeInspectorPanel,
  TopBar,
} from "./panels.mjs";

const h = React.createElement;

export function App() {
  const params = new URLSearchParams(window.location.search);
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
  const [selectedNodeId, setSelectedNodeId] = React.useState("");
  const [selectedNodeParamsText, setSelectedNodeParamsText] = React.useState("{}");

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

  const setStatus = React.useCallback((text, tone) => {
    setStatusText(String(text || "idle"));
    setStatusTone(String(tone || "status-neutral"));
  }, []);

  const normalizePollIntervalMs = React.useCallback(
    () => clampPollIntervalMs(pollIntervalMsText),
    [pollIntervalMsText]
  );

  const renderGraphRunRecord = React.useCallback((row, graphRunId, extraLines) => {
    setGraphRunText(buildGraphRunRecordText(row, graphRunId, extraLines));
  }, []);

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
  }, [apiBase, profile, renderGraphRunRecord, setStatus]);

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
  }, [apiBase, loadGraphRunSummaryById, normalizePollIntervalMs, renderGraphRunRecord, setStatus]);

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
          `run_mode: async`,
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
  }, [apiBase, lastGraphRunId, renderGraphRunRecord, setStatus]);

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
          `run_mode: async`,
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
    setStatus,
  ]);

  const pollLastGraphRunOnce = React.useCallback(async () => {
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
  }, [lastGraphRunId, pollGraphRunUntilTerminal, pollingActive, setStatus]);

  const pinBaselineFromGraphRun = React.useCallback(async () => {
    const summaryPath = String(graphRunSummary?.outputs?.graph_run_summary_json || "").trim();
    const bId = String(baselineId || "").trim();
    if (!summaryPath) {
      setStatus("run graph first to pin baseline", "status-warn");
      return;
    }
    if (!bId) {
      setStatus("baseline id is required", "status-warn");
      return;
    }
    setStatus("pinning baseline...", "status-warn");
    try {
      const payload = await createBaseline(apiBase, {
        baseline_id: bId,
        summary_json: summaryPath,
        overwrite: true,
        note: "pinned from graph_lab",
        tags: ["graph_lab", "graph_run"],
      });
      const row = payload.baseline || {};
      setStatus(`baseline pinned: ${String(row.baseline_id || bId)}`, "status-ok");
    } catch (err) {
      setStatus(`baseline pin failed: ${String(err.message || err)}`, "status-err");
    }
  }, [apiBase, baselineId, graphRunSummary, setStatus]);

  const runPolicyGateForGraphRun = React.useCallback(async () => {
    const summaryPath = String(graphRunSummary?.outputs?.graph_run_summary_json || "").trim();
    const bId = String(baselineId || "").trim();
    if (!summaryPath) {
      setStatus("run graph first to evaluate gate", "status-warn");
      return;
    }
    if (!bId) {
      setStatus("baseline id is required", "status-warn");
      return;
    }
    setStatus("running policy gate...", "status-warn");
    try {
      const payload = await evaluatePolicyGate(apiBase, {
        baseline_id: bId,
        candidate_summary_json: summaryPath,
      });
      const row = payload.policy_eval || {};
      const failures = Array.isArray(row.gate_failures) ? row.gate_failures : [];
      const lines = [
        `policy_eval_id: ${String(row.policy_eval_id || "-")}`,
        `gate_failed: ${Boolean(row.gate_failed)}`,
        `recommendation: ${String(row.recommendation || "-")}`,
        `failure_count: ${failures.length}`,
      ];
      if (failures.length > 0) {
        lines.push("gate_failures:");
        failures.slice(0, 8).forEach((f, idx) => {
          const metric = f && f.metric ? ` (${String(f.metric)})` : "";
          lines.push(
            `- [${Number(idx) + 1}] ${String((f && f.rule) || "unknown_rule")}${metric}: ${String(
              (f && f.value) ?? "-"
            )} > ${String((f && f.limit) ?? "-")}`
          );
        });
      }
      setGateResultText(lines.join("\n"));
      setLastPolicyEval(row);
      setStatus(
        Boolean(row.gate_failed) ? "policy gate: HOLD" : "policy gate: ADOPT",
        Boolean(row.gate_failed) ? "status-warn" : "status-ok"
      );
    } catch (err) {
      setGateResultText(`gate failed\n- ${String(err.message || err)}`);
      setLastPolicyEval(null);
      setStatus(`policy gate failed: ${String(err.message || err)}`, "status-err");
    }
  }, [apiBase, baselineId, graphRunSummary, setStatus]);

  const exportGateReport = React.useCallback(() => {
    const summaryPath = String(graphRunSummary?.outputs?.graph_run_summary_json || "").trim() || "-";
    const p = lastPolicyEval || {};
    const failures = Array.isArray(p.gate_failures) ? p.gate_failures : [];
    const nowIso = new Date().toISOString();
    const reportLines = [
      "# Graph Run Gate Report",
      "",
      `- generated_at_utc: ${nowIso}`,
      `- graph_id: ${String(graphRunSummary?.graph?.graph_id || graphId || "-")}`,
      `- graph_run_summary_json: ${summaryPath}`,
      `- baseline_id: ${String(baselineId || "-")}`,
      `- policy_eval_id: ${String(p.policy_eval_id || "-")}`,
      `- gate_failed: ${Boolean(p.gate_failed)}`,
      `- recommendation: ${String(p.recommendation || "-")}`,
      "",
      "## Failures",
    ];
    if (failures.length === 0) {
      reportLines.push("- none");
    } else {
      failures.forEach((f, idx) => {
        const metric = f && f.metric ? ` (${String(f.metric)})` : "";
        reportLines.push(
          `- [${Number(idx) + 1}] ${String((f && f.rule) || "unknown_rule")}${metric}: value=${String(
            (f && f.value) ?? "-"
          )} limit=${String((f && f.limit) ?? "-")}`
        );
      });
    }
    const text = reportLines.join("\n");
    const blob = new Blob([text], { type: "text/markdown;charset=utf-8" });
    const href = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = href;
    a.download = `graph_gate_report_${String(graphId || "graph")}_${nowIso.slice(0, 19).replace(/[:T]/g, "_")}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.setTimeout(() => URL.revokeObjectURL(href), 1000);
    setStatus("gate report exported", "status-ok");
  }, [baselineId, graphId, graphRunSummary, lastPolicyEval, setStatus]);

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

  const inputState = {
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
  };

  const inputActions = {
    setApiBase,
    setGraphId,
    setSceneJsonPath,
    setBaselineId,
    setProfile,
    setRunMode,
    setAutoPollAsyncRun,
    setPollIntervalMsText,
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
  };

  return h("div", { className: "page" }, [
    h(TopBar, {
      key: "topbar",
      statusTone,
      statusText,
      nodeCount: nodes.length,
      edgeCount: edges.length,
    }),
    h("main", { className: "content", key: "ct" }, [
      h(GraphInputsPanel, {
        key: "left",
        state: inputState,
        actions: inputActions,
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
      }),
    ]),
  ]);
}

export default App;
