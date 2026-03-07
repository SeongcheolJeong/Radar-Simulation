import { React } from "../deps.mjs";

const h = React.createElement;

export function DecisionPane({
  baselineId,
  compareGraphRunId,
  setCompareGraphRunId,
  loadCompareGraphRunById,
  clearCompareGraphRun,
  pinCurrentGraphRunAsCompare,
  pinBaselineFromGraphRun,
  runPolicyGateForGraphRun,
  runDecisionRegressionSession,
  runLowVsCurrentTrackCompare,
  exportGateReport,
  exportDecisionRegressionSession,
  exportDecisionBriefMd,
  currentTrackLabel,
  compareTrackLabel,
  trackCompareGuideText,
  decisionSummaryText,
  decisionOpsStatusText,
  trackCompareRunnerStatusText,
  compareRunStatusText,
  lastRegressionSession,
  lastRegressionExport,
}) {
  return h("div", { className: "field", key: "decision_surface" }, [
    h("label", { className: "label", key: "lbl_decision_surface" }, "Decision Pane"),
    h("div", { className: "hint", key: "decision_scope_hint" }, `baseline_id: ${String(baselineId || "-")}`),
    h("input", {
      className: "input",
      value: String(compareGraphRunId || ""),
      onChange: (e) => setCompareGraphRunId(String(e.target.value || "")),
      placeholder: "compare graph_run_id (grun_...)",
    }),
    h("div", { className: "btn-row", key: "decision_compare_row" }, [
      h("button", {
        className: "btn",
        key: "decision_load_compare",
        onClick: () => loadCompareGraphRunById(String(compareGraphRunId || ""), { mode: "manual" }),
      }, "Load Compare"),
      h("button", {
        className: "btn",
        key: "decision_pin_current_compare",
        onClick: pinCurrentGraphRunAsCompare,
      }, "Use Current as Compare"),
      h("button", {
        className: "btn",
        key: "decision_clear_compare",
        onClick: clearCompareGraphRun,
      }, "Clear Compare"),
    ]),
    h("div", { className: "field", key: "decision_track_workflow" }, [
      h("label", { className: "label", key: "lbl_decision_track_workflow" }, "Track Compare Workflow"),
      h("div", { className: "hint", key: "decision_current_track_hint" }, `current_track: ${String(currentTrackLabel || "-")}`),
      h("div", { className: "hint", key: "decision_compare_track_hint" }, `compare_track: ${String(compareTrackLabel || "-")}`),
      h("pre", { className: "result-box", key: "decision_track_workflow_box" }, String(trackCompareGuideText || "-")),
    ]),
    h("div", { className: "btn-row", key: "decision_gate_row" }, [
      h("button", {
        className: "btn",
        key: "decision_pin_baseline",
        onClick: pinBaselineFromGraphRun,
      }, "Pin Baseline"),
      h("button", {
        className: "btn",
        key: "decision_policy_gate",
        onClick: runPolicyGateForGraphRun,
      }, "Policy Gate"),
      h("button", {
        className: "btn",
        key: "decision_run_track_compare",
        onClick: runLowVsCurrentTrackCompare,
      }, "Run Low -> Current Compare"),
    ]),
    h("div", { className: "btn-row", key: "decision_session_row" }, [
      h("button", {
        className: "btn",
        key: "decision_run_session",
        onClick: runDecisionRegressionSession,
      }, "Run Session"),
      h("button", {
        className: "btn",
        key: "decision_export_session",
        onClick: exportDecisionRegressionSession,
      }, "Export Session"),
    ]),
    h("div", { className: "btn-row", key: "decision_export_row" }, [
      h("button", {
        className: "btn",
        key: "decision_export_gate",
        onClick: exportGateReport,
      }, "Export Gate"),
      h("button", {
        className: "btn",
        key: "decision_export_brief",
        onClick: exportDecisionBriefMd,
      }, "Export Brief"),
    ]),
    h("pre", { className: "result-box", key: "decision_summary_box" }, String(decisionSummaryText || "-")),
    h("div", { className: "hint", key: "decision_status_hint" }, `decision_ops: ${String(decisionOpsStatusText || "-")}`),
    h("div", { className: "hint", key: "track_compare_status_hint" }, `track_compare_status: ${String(trackCompareRunnerStatusText || "-")}`),
    h("div", { className: "hint", key: "compare_status_hint" }, `compare_status: ${String(compareRunStatusText || "-")}`),
    h("div", { className: "hint", key: "session_status_hint" }, [
      `session_id=${String(lastRegressionSession?.session_id || "-")} | `,
      `export_id=${String(lastRegressionExport?.export_id || "-")}`,
    ]),
  ]);
}
