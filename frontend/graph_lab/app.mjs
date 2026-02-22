import {
  React,
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  addEdge,
  useNodesState,
  useEdgesState,
} from "./deps.mjs";
import { NODE_TYPES } from "./constants.mjs";
import { normalizeRepoPath, toFlowNode, toGraphPayload } from "./graph_helpers.mjs";
import { buildGraphRunRecordText, clampPollIntervalMs } from "./run_monitor.mjs";

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
    const base = apiBase.replace(/\\/$/, "");
    const sumRes = await fetch(`${base}/api/graph/runs/${encodeURIComponent(graphRunId)}/summary`);
    if (!sumRes.ok) {
      const recRes = await fetch(`${base}/api/graph/runs/${encodeURIComponent(graphRunId)}`);
      if (recRes.ok) {
        const rec = await recRes.json();
        renderGraphRunRecord(rec, graphRunId, [
          `summary_fetch_error: graph summary request failed (${sumRes.status})`,
        ]);
        setGraphRunSummary(null);
        setGateResultText("-");
        setLastPolicyEval(null);
        setStatus(`graph run failed: ${graphRunId}`, "status-err");
        return { ok: false, record: rec };
      }
      throw new Error(`graph summary request failed (${sumRes.status})`);
    }
    const summary = await sumRes.json();
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
    const base = apiBase.replace(/\\/$/, "");
    const intervalMs = normalizePollIntervalMs();
    const maxPolls = 300;
    setPollingActive(true);
    setPollStateText(`polling graph run every ${intervalMs} ms`);
    try {
      for (let i = 0; i < maxPolls; i += 1) {
        const recRes = await fetch(`${base}/api/graph/runs/${encodeURIComponent(graphRunId)}`);
        if (!recRes.ok) throw new Error(`graph run poll failed (${recRes.status})`);
        const row = await recRes.json();
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
      const res = await fetch(`${apiBase.replace(/\\/$/, "")}/api/graph/templates`);
      if (!res.ok) throw new Error(`template request failed (${res.status})`);
      const payload = await res.json();
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
      const res = await fetch(`${apiBase.replace(/\\/$/, "")}/api/graph/validate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(graph),
      });
      if (!res.ok) throw new Error(`validate request failed (${res.status})`);
      const payload = await res.json();
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
      const res = await fetch(`${apiBase.replace(/\\/$/, "")}/api/graph/runs?async=${runAsync ? 1 : 0}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          graph,
          scene_json_path: sceneJsonPath,
          profile,
          run_hybrid_estimation: false,
          tag: "graph_lab",
        }),
      });
      if (!res.ok) throw new Error(`graph run request failed (${res.status})`);
      const payload = await res.json();
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
      const res = await fetch(
        `${apiBase.replace(/\\/$/, "")}/api/graph/runs/${encodeURIComponent(graphRunId)}/cancel`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ reason: "graph_lab_manual_cancel" }),
        }
      );
      if (!res.ok) throw new Error(`cancel request failed (${res.status})`);
      const payload = await res.json();
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
      const res = await fetch(
        `${apiBase.replace(/\\/$/, "")}/api/graph/runs/${encodeURIComponent(graphRunId)}/retry?async=${runAsync ? 1 : 0}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            cache: { enable: false, mode: "off" },
            tag: "graph_lab_retry",
          }),
        }
      );
      if (!res.ok) throw new Error(`retry request failed (${res.status})`);
      const payload = await res.json();
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
      const res = await fetch(`${apiBase.replace(/\\/$/, "")}/api/baselines`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          baseline_id: bId,
          summary_json: summaryPath,
          overwrite: true,
          note: "pinned from graph_lab",
          tags: ["graph_lab", "graph_run"],
        }),
      });
      if (!res.ok) throw new Error(`baseline pin failed (${res.status})`);
      const payload = await res.json();
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
      const res = await fetch(`${apiBase.replace(/\\/$/, "")}/api/compare/policy`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          baseline_id: bId,
          candidate_summary_json: summaryPath,
        }),
      });
      if (!res.ok) throw new Error(`policy gate failed (${res.status})`);
      const payload = await res.json();
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

  return h("div", { className: "page" }, [
    h("header", { className: "topbar", key: "hd" }, [
      h("div", { className: "brand", key: "b1" }, [
        h("span", { className: "brand-dot", key: "dot" }),
        h("div", { key: "txt" }, [
          h("div", { className: "brand-title", key: "t1" }, "Radar Graph Lab"),
          h("div", { className: "brand-sub", key: "t2" }, "ReactFlow Simulink-Style Workspace"),
        ]),
      ]),
      h("div", { className: "top-actions", key: "b2" }, [
        h("span", { className: `stat ${statusTone}`, key: "s1" }, statusText),
        h("span", { className: "stat", key: "s2" }, `nodes ${nodes.length} / edges ${edges.length}`),
      ]),
    ]),

    h("main", { className: "content", key: "ct" }, [
      h("section", { className: "panel", key: "left" }, [
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
          h("div", { className: "hint", key: "hint" }, "Tip: connect nodes on canvas, then validate to check schema/profile/DAG constraints."),
        ]),
      ]),

      h("section", { className: "panel", key: "center" }, [
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
      ]),

      h("section", { className: "panel", key: "right" }, [
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
          h("div", { className: "field", key: "artifactinspect" }, [
            h("label", { className: "label", key: "lblai" }, "Artifact Inspector"),
            graphRunSummary
              ? h("div", { className: "result-box", key: "aibox" }, [
                  h("div", { key: "kpi", style: { marginBottom: "8px" } }, [
                    `paths=${Number(graphRunSummary?.path_summary?.path_count_total || 0)} | `,
                    `adc_shape=${Array.isArray(graphRunSummary?.adc_summary?.shape) ? graphRunSummary.adc_summary.shape.join("x") : "-"} | `,
                    `rd=${Array.isArray(graphRunSummary?.radar_map_summary?.rd_shape) ? graphRunSummary.radar_map_summary.rd_shape.join("x") : "-"} | `,
                    `ra=${Array.isArray(graphRunSummary?.radar_map_summary?.ra_shape) ? graphRunSummary.radar_map_summary.ra_shape.join("x") : "-"}`,
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
                ])
              : h("pre", { className: "result-box", key: "aibox_empty" }, "run graph first to inspect artifacts"),
          ]),
        ]),
      ]),
    ]),
  ]);
}

export default App;
