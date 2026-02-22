import { React } from "../deps.mjs";
import { createBaseline, evaluatePolicyGate } from "../api_client.mjs";

export function useGateOps(opts) {
  const {
    apiBase,
    graphRunSummary,
    baselineId,
    graphId,
    lastPolicyEval,
    setStatus,
    setGateResultText,
    setLastPolicyEval,
  } = opts;

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
  }, [apiBase, baselineId, graphRunSummary, setGateResultText, setLastPolicyEval, setStatus]);

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

  return {
    pinBaselineFromGraphRun,
    runPolicyGateForGraphRun,
    exportGateReport,
  };
}
