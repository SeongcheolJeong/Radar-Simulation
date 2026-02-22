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
  getGraphTemplates,
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
  const [contractDebugText, setContractDebugText] = React.useState("-");
  const [contractOverlayEnabled, setContractOverlayEnabled] = React.useState(
    String(params.get("contract_overlay") || "0") === "1"
  );
  const [contractTimeline, setContractTimeline] = React.useState([]);
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

  const openGateEvidenceFromTimeline = React.useCallback((row) => {
    const eventRow = row && typeof row === "object" ? row : {};
    const note = eventRow.note && typeof eventRow.note === "object" ? eventRow.note : {};
    const runId = String(eventRow.graph_run_id || "").trim();
    const gateFailed = Boolean(note.gate_failed);
    const rules = Array.isArray(note.failure_rules) ? note.failure_rules : [];
    const lines = [
      `policy_eval_id: ${String(note.policy_eval_id || "-")}`,
      `gate_failed: ${gateFailed}`,
      `recommendation: ${String(note.recommendation || "-")}`,
      `baseline_id: ${String(note.baseline_id || "-")}`,
      `graph_run_id: ${runId || "-"}`,
      `failure_count: ${Number(note.failure_count || 0)}`,
      "",
      "gate_failures:",
      ...(rules.length > 0 ? rules.map((rule, idx) => `- [${Number(idx) + 1}] ${rule}`) : ["- none"]),
      "",
      `source_event: ${String(eventRow.event_source || "-")}`,
      `timestamp_ms: ${Number(eventRow.timestamp_ms || 0)}`,
      `contract_delta: ${Number(eventRow?.delta?.unique_warning_count || 0)}/${Number(eventRow?.delta?.attempt_count_total || 0)}`,
    ];
    setGateResultText(lines.join("\n"));
    if (runId) setLastGraphRunId(runId);
    setStatus(
      gateFailed ? `gate evidence opened (HOLD): ${runId || "-"}` : `gate evidence opened (ADOPT): ${runId || "-"}`,
      gateFailed ? "status-warn" : "status-ok"
    );
  }, [setGateResultText, setLastGraphRunId, setStatus]);

  React.useEffect(() => {
    refreshContractWarnings();
  }, [refreshContractWarnings]);

  React.useEffect(() => {
    refreshContractWarnings();
  }, [graphRunText, gateResultText, validationText, refreshContractWarnings]);

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

  const inputPanelModel = React.useMemo(() => normalizeGraphInputsPanelModel({
    values: {
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
      contractTimelineCount: contractTimeline.length,
    },
    setters: {
      setApiBase,
      setGraphId,
      setSceneJsonPath,
      setBaselineId,
      setProfile,
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
