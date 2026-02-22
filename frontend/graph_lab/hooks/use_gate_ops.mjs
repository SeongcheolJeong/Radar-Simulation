import { React } from "../deps.mjs";
import {
  getContractWarningSnapshot,
  normalizeGateOpsOptions,
} from "../contracts.mjs";
import { createBaseline, evaluatePolicyGate } from "../api_client.mjs";

export function useGateOps(opts) {
  const safeOpts = normalizeGateOpsOptions(opts);
  const {
    apiBase,
    graphRunSummary,
    baselineId,
    graphId,
    lastPolicyEval,
    setStatus,
    setGateResultText,
    setLastPolicyEval,
    onContractDiagnosticsEvent,
  } = safeOpts;

  const collectContractDiagnostics = React.useCallback((beforeSnapshot) => {
    const beforeUnique = Number(beforeSnapshot?.unique_warning_count || 0);
    const beforeAttempts = Number(beforeSnapshot?.attempt_count_total || 0);
    const snapshot = getContractWarningSnapshot();
    const uniqueNow = Number(snapshot.unique_warning_count || 0);
    const attemptsNow = Number(snapshot.attempt_count_total || 0);
    return {
      baseline: {
        unique_warning_count: beforeUnique,
        attempt_count_total: beforeAttempts,
      },
      snapshot,
      delta: {
        unique_warning_count: uniqueNow - beforeUnique,
        attempt_count_total: attemptsNow - beforeAttempts,
      },
      lines: [
        `contract_warning_unique: ${uniqueNow}`,
        `contract_warning_attempts: ${attemptsNow}`,
        `contract_warning_delta_unique: ${(uniqueNow - beforeUnique) >= 0 ? "+" : ""}${uniqueNow - beforeUnique}`,
        `contract_warning_delta_attempts: ${(attemptsNow - beforeAttempts) >= 0 ? "+" : ""}${attemptsNow - beforeAttempts}`,
      ],
    };
  }, []);

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
    const beforeContractSnapshot = getContractWarningSnapshot();
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
      const contract = collectContractDiagnostics(beforeContractSnapshot);
      lines.push(...contract.lines);
      setGateResultText(lines.join("\n"));
      const runtimeDiag = {
        version: "policy_gate_contract_diagnostics_v1",
        source: "policy_gate_eval",
        graph_run_id: String(graphRunSummary?.graph_run_id || graphRunSummary?.run_id || ""),
        baseline: contract.baseline,
        snapshot: {
          contract_debug_version: String(contract.snapshot?.contract_debug_version || "-"),
          unique_warning_count: Number(contract.snapshot?.unique_warning_count || 0),
          attempt_count_total: Number(contract.snapshot?.attempt_count_total || 0),
        },
        delta: contract.delta,
        timestamp_ms: Date.now(),
      };
      const policyEvalWithDiagnostics = {
        ...row,
        runtime_contract_diagnostics: runtimeDiag,
      };
      setLastPolicyEval(policyEvalWithDiagnostics);
      onContractDiagnosticsEvent({
        event_source: "policy_gate_eval",
        graph_run_id: runtimeDiag.graph_run_id,
        timestamp_ms: runtimeDiag.timestamp_ms,
        baseline: contract.baseline,
        snapshot: contract.snapshot,
        delta: contract.delta,
        note: { gate_failed: Boolean(row.gate_failed), baseline_id: bId },
      });
      setStatus(
        Boolean(row.gate_failed) ? "policy gate: HOLD" : "policy gate: ADOPT",
        Boolean(row.gate_failed) ? "status-warn" : "status-ok"
      );
    } catch (err) {
      setGateResultText(`gate failed\n- ${String(err.message || err)}`);
      setLastPolicyEval(null);
      setStatus(`policy gate failed: ${String(err.message || err)}`, "status-err");
    }
  }, [
    apiBase,
    baselineId,
    collectContractDiagnostics,
    graphRunSummary,
    onContractDiagnosticsEvent,
    setGateResultText,
    setLastPolicyEval,
    setStatus,
  ]);

  const exportGateReport = React.useCallback(() => {
    const summaryPath = String(graphRunSummary?.outputs?.graph_run_summary_json || "").trim() || "-";
    const p = lastPolicyEval || {};
    const failures = Array.isArray(p.gate_failures) ? p.gate_failures : [];
    const runContract = graphRunSummary?.runtime_contract_diagnostics || null;
    const gateContract = p?.runtime_contract_diagnostics || null;
    const formatContractBlock = (label, row) => {
      if (!row || typeof row !== "object") return [];
      return [
        `- ${label}.source: ${String(row.source || "-")}`,
        `- ${label}.delta_unique: ${Number(row?.delta?.unique_warning_count || 0)}`,
        `- ${label}.delta_attempts: ${Number(row?.delta?.attempt_count_total || 0)}`,
        `- ${label}.total_unique: ${Number(row?.snapshot?.unique_warning_count || 0)}`,
        `- ${label}.total_attempts: ${Number(row?.snapshot?.attempt_count_total || 0)}`,
      ];
    };
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
    reportLines.push(
      "",
      "## Contract Diagnostics",
      `- contract_debug_version: ${String(gateContract?.snapshot?.contract_debug_version || runContract?.snapshot?.contract_debug_version || "-")}`,
      ...formatContractBlock("run", runContract),
      ...formatContractBlock("gate", gateContract)
    );
    if (!runContract && !gateContract) {
      reportLines.push("- none");
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
