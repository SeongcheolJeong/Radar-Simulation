export function clampPollIntervalMs(pollIntervalMsText) {
  const raw = Number(pollIntervalMsText);
  if (!Number.isFinite(raw)) return 400;
  return Math.max(100, Math.min(5000, Math.floor(raw)));
}

export function buildGraphRunRecordText(row, graphRunId, extraLines) {
  const recovery = row && row.recovery ? row.recovery : {};
  const hints = Array.isArray(recovery && recovery.hints) ? recovery.hints : [];
  const lines = [
    `graph_run_id: ${graphRunId}`,
    `status: ${String((row && row.status) || "-")}`,
    `error: ${String((row && row.error) || "-")}`,
    `recoverable: ${Boolean(recovery && recovery.recoverable)}`,
    `retry_endpoint: ${String((recovery && recovery.retry_endpoint) || "-")}`,
  ];
  if (Array.isArray(extraLines) && extraLines.length > 0) {
    lines.push(...extraLines.map((x) => String(x)));
  }
  if (hints.length > 0) {
    lines.push("recovery_hints:");
    hints.slice(0, 8).forEach((x) => lines.push(`- ${String(x)}`));
  }
  return lines.join("\n");
}
