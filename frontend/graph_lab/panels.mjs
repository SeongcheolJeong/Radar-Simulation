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
  const [sourceFilter, setSourceFilter] = React.useState("all");
  const [pinnedRunId, setPinnedRunId] = React.useState("all");
  const [nonZeroOnly, setNonZeroOnly] = React.useState(false);
  const [compactMode, setCompactMode] = React.useState(false);
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
  const filteredRows = React.useMemo(() => rows.filter((row) => {
    const source = String(row?.event_source || "-");
    if (sourceFilter !== "all" && source !== sourceFilter) return false;
    const runId = String(row?.graph_run_id || "");
    if (pinnedRunId !== "all" && runId !== pinnedRunId) return false;
    if (!nonZeroOnly) return true;
    const du = Number(row?.delta?.unique_warning_count || 0);
    const da = Number(row?.delta?.attempt_count_total || 0);
    return du !== 0 || da !== 0;
  }), [nonZeroOnly, pinnedRunId, rows, sourceFilter]);
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
      h("span", { key: "co_filter_count", style: { marginLeft: "auto", color: "#8eb6ca" } }, `showing ${filteredRows.length}/${rows.length}`),
    ]),
    h("div", { className: "contract-overlay-bd", key: "co_bd" }, filteredRows.length === 0
      ? h("pre", { className: "result-box", key: "co_empty" }, "no contract events yet")
      : filteredRows.map((row, idx) =>
        (() => {
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
                      onClick: () => gateOpenHandler(row),
                    }, "Open Gate")
                  : null,
              ]),
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
                        onClick: () => gateOpenHandler(row),
                      }, "Open Gate")
                    : null,
                ])
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
