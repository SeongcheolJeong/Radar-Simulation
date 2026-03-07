import { React } from "../deps.mjs";
import { buildRunCompareSummary } from "../compare_summary.mjs";
import { normalizeRepoPath } from "../graph_helpers.mjs";

const h = React.createElement;
const ARTIFACT_INSPECTOR_PREFS_STORAGE_KEY = "graph_lab_artifact_inspector_prefs_v1";
const ARTIFACT_INSPECTOR_RECENT_ACTION_LIMIT = 3;

function formatSigned(value) {
  const n = Number(value || 0);
  return `${n >= 0 ? "+" : ""}${n}`;
}

function normalizeShape(rawShape) {
  if (!Array.isArray(rawShape)) return [];
  return rawShape
    .map((x) => Number(x))
    .filter((x) => Number.isFinite(x) && x >= 0)
    .map((x) => Math.floor(x));
}

function normalizePeakList(rawPeaks, rowKey, colKey) {
  const rows = Array.isArray(rawPeaks) ? rawPeaks : [];
  return rows
    .map((peak, idx) => {
      const row = Number(peak?.[rowKey]);
      const col = Number(peak?.[colKey]);
      if (!Number.isFinite(row) || !Number.isFinite(col)) return null;
      return {
        index: Number(idx),
        row: Math.floor(row),
        col: Math.floor(col),
        power: Number(peak?.power || 0),
        relDb: Number(peak?.rel_db || 0),
      };
    })
    .filter(Boolean);
}

function clampBin(value, maxSize) {
  const maxIdx = Math.max(0, Number(maxSize || 0) - 1);
  const raw = Number(value);
  const candidate = Number.isFinite(raw) ? Math.floor(raw) : 0;
  return Math.max(0, Math.min(maxIdx, candidate));
}

function parseBinText(rawText, fallback) {
  const raw = Number(rawText);
  if (!Number.isFinite(raw)) return Number(fallback || 0);
  return Math.floor(raw);
}

function safeShapeLabel(shape) {
  return Array.isArray(shape) && shape.length > 0 ? shape.join("x") : "-";
}

function buildArtifactInspectorStatusBadges({
  layoutDefault,
  probesDefault,
  liveCompareEvidenceExpanded,
  historyArtifactExpectationExpanded,
  auditState,
}) {
  return [
    {
      label: `layout:${layoutDefault ? "default" : "customized"}`,
      tone: layoutDefault ? "status-ok" : "status-warn",
    },
    {
      label: `probe:${probesDefault ? "default" : "customized"}`,
      tone: probesDefault ? "status-ok" : "status-warn",
    },
    {
      label: `live:${liveCompareEvidenceExpanded ? "expanded" : "collapsed"}`,
      tone: "status-neutral",
    },
    {
      label: `history:${historyArtifactExpectationExpanded ? "expanded" : "collapsed"}`,
      tone: "status-neutral",
    },
    {
      label: `reset:${layoutDefault ? "clean" : "required"}`,
      tone: layoutDefault ? "status-ok" : "status-warn",
    },
    {
      label: `audit:${String(auditState || "idle").trim() || "idle"}`,
      tone: (
        String(auditState || "").trim() === "trimmed"
          ? "status-warn"
          : String(auditState || "").trim() === "tracking"
            ? "status-ok"
            : "status-neutral"
      ),
    },
  ];
}

function buildDefaultArtifactInspectorProbeState(rdPeaks, raPeaks) {
  const primaryRd = Array.isArray(rdPeaks) && rdPeaks.length > 0 ? rdPeaks[0] : null;
  const primaryRa = Array.isArray(raPeaks) && raPeaks.length > 0 ? raPeaks[0] : null;
  return {
    rdRangeBinText: String(primaryRd ? primaryRd.col : 0),
    rdDopplerBinText: String(primaryRd ? primaryRd.row : 0),
    raRangeBinText: String(primaryRa ? primaryRa.col : 0),
    raAngleBinText: String(primaryRa ? primaryRa.row : 0),
    rdPeakSelectText: primaryRd ? "0" : "-1",
    raPeakSelectText: primaryRa ? "0" : "-1",
    rdPeakLock: false,
    raPeakLock: false,
  };
}

function computeProbe(peaks, rowBin, colBin, shape) {
  const rows = Number(shape?.[0] || 0);
  const cols = Number(shape?.[1] || 0);
  const hasBounds = rows > 0 && cols > 0;
  const clampedRow = hasBounds ? clampBin(rowBin, rows) : Math.max(0, Number(rowBin || 0));
  const clampedCol = hasBounds ? clampBin(colBin, cols) : Math.max(0, Number(colBin || 0));
  const exact = peaks.find((peak) => peak.row === clampedRow && peak.col === clampedCol) || null;
  let nearest = null;
  let nearestDist = Number.POSITIVE_INFINITY;
  peaks.forEach((peak) => {
    const dist = Math.abs(Number(peak.row) - clampedRow) + Math.abs(Number(peak.col) - clampedCol);
    if (dist < nearestDist) {
      nearestDist = dist;
      nearest = peak;
    }
  });
  return {
    row: clampedRow,
    col: clampedCol,
    hasBounds,
    exact,
    nearest,
    nearestDist: Number.isFinite(nearestDist) ? nearestDist : null,
    rowNorm: hasBounds ? clampedRow / Math.max(rows - 1, 1) : 0,
    colNorm: hasBounds ? clampedCol / Math.max(cols - 1, 1) : 0,
  };
}

function normalizeArtifactInspectorPrefs(value) {
  const row = value && typeof value === "object" ? value : {};
  const lastActionSeq = Number(row.lastActionSeq);
  const rawActionTrailTotalCount = Number(row.actionTrailTotalCount);
  const recentActionEntries = Array.isArray(row.recentActionEntries)
    ? row.recentActionEntries.map((entry) => String(entry || "").trim()).filter(Boolean).slice(0, ARTIFACT_INSPECTOR_RECENT_ACTION_LIMIT)
    : [];
  const fallbackActionTrailTotalCount = Math.max(
    recentActionEntries.length,
    Number.isFinite(lastActionSeq) && lastActionSeq >= 0 ? Math.floor(lastActionSeq) : 0
  );
  return {
    liveCompareEvidenceExpanded: row.liveCompareEvidenceExpanded !== false,
    historyArtifactExpectationExpanded: row.historyArtifactExpectationExpanded !== false,
    lastActionSeq: Number.isFinite(lastActionSeq) && lastActionSeq >= 0 ? Math.floor(lastActionSeq) : 0,
    actionTrailTotalCount: Number.isFinite(rawActionTrailTotalCount) && rawActionTrailTotalCount >= 0
      ? Math.floor(rawActionTrailTotalCount)
      : fallbackActionTrailTotalCount,
    lastActionText: String(row.lastActionText || "last_action: seq=0 | idle").trim() || "last_action: seq=0 | idle",
    recentActionEntries,
  };
}

function buildArtifactInspectorRecentActionsText(entries) {
  const rows = Array.isArray(entries) ? entries.map((entry) => String(entry || "").trim()).filter(Boolean) : [];
  if (rows.length <= 0) {
    return "recent_actions: none";
  }
  return `recent_actions: ${rows.map((entry) => `[${entry}]`).join(" ")}`;
}

function buildArtifactInspectorAuditSummaryText(value) {
  const prefs = normalizeArtifactInspectorPrefs(value);
  const retained = Array.isArray(prefs.recentActionEntries) ? prefs.recentActionEntries.length : 0;
  const total = Math.max(0, Number(prefs.actionTrailTotalCount || 0));
  const trimmed = Math.max(0, total - retained);
  const nextSeq = Math.max(0, Number(prefs.lastActionSeq || 0)) + 1;
  return `audit_summary: total=${total} | retained=${retained} | trimmed=${trimmed} | next_seq=${nextSeq} | state=${total > 0 ? "active" : "empty"}`;
}

function buildArtifactInspectorAuditStateText(value) {
  const prefs = normalizeArtifactInspectorPrefs(value);
  const retained = Array.isArray(prefs.recentActionEntries) ? prefs.recentActionEntries.length : 0;
  const total = Math.max(0, Number(prefs.actionTrailTotalCount || 0));
  const trimmed = Math.max(0, total - retained);
  let state = "idle";
  if (trimmed > 0) {
    state = "trimmed";
  } else if (total > 0) {
    state = "tracking";
  }
  return `audit_state: ${state} | total=${total} | retained=${retained}/${ARTIFACT_INSPECTOR_RECENT_ACTION_LIMIT} | trimmed=${trimmed}`;
}

function buildArtifactInspectorAuditCapacityText(value) {
  const prefs = normalizeArtifactInspectorPrefs(value);
  const retained = Array.isArray(prefs.recentActionEntries) ? prefs.recentActionEntries.length : 0;
  const total = Math.max(0, Number(prefs.actionTrailTotalCount || 0));
  const trimmed = Math.max(0, total - retained);
  const headroom = Math.max(0, ARTIFACT_INSPECTOR_RECENT_ACTION_LIMIT - retained);
  return `audit_capacity: retained_limit=${ARTIFACT_INSPECTOR_RECENT_ACTION_LIMIT} | retained=${retained} | total=${total} | headroom=${headroom} | overflow=${trimmed > 0 ? "yes" : "no"}`;
}

function clearArtifactInspectorActionTrailState(value) {
  const prefs = normalizeArtifactInspectorPrefs(value);
  return {
    ...prefs,
    lastActionSeq: 0,
    actionTrailTotalCount: 0,
    lastActionText: "last_action: seq=0 | idle",
    recentActionEntries: [],
  };
}

function buildArtifactInspectorLastActionUpdate(value, label) {
  const prefs = normalizeArtifactInspectorPrefs(value);
  const nextSeq = Math.max(0, Number(prefs.lastActionSeq || 0)) + 1;
  const normalizedLabel = String(label || "unknown").trim() || "unknown";
  const actionEntry = `seq=${nextSeq} | ${normalizedLabel}`;
  return {
    lastActionSeq: nextSeq,
    actionTrailTotalCount: Math.max(0, Number(prefs.actionTrailTotalCount || 0)) + 1,
    lastActionText: `last_action: ${actionEntry}`,
    recentActionEntries: [actionEntry, ...prefs.recentActionEntries].slice(0, ARTIFACT_INSPECTOR_RECENT_ACTION_LIMIT),
  };
}

function applyArtifactInspectorPrefsCommand(value, command) {
  const current = normalizeArtifactInspectorPrefs(value);
  const row = command && typeof command === "object" ? command : {};
  const next = { ...current };
  if (typeof row.liveCompareEvidenceExpanded === "boolean") {
    next.liveCompareEvidenceExpanded = row.liveCompareEvidenceExpanded;
  }
  if (typeof row.historyArtifactExpectationExpanded === "boolean") {
    next.historyArtifactExpectationExpanded = row.historyArtifactExpectationExpanded;
  }
  return normalizeArtifactInspectorPrefs(next);
}

function loadArtifactInspectorPrefs() {
  try {
    if (typeof window === "undefined" || !window.localStorage) {
      return normalizeArtifactInspectorPrefs({});
    }
    const raw = String(window.localStorage.getItem(ARTIFACT_INSPECTOR_PREFS_STORAGE_KEY) || "").trim();
    if (!raw) {
      return normalizeArtifactInspectorPrefs({});
    }
    return normalizeArtifactInspectorPrefs(JSON.parse(raw));
  } catch (_) {
    return normalizeArtifactInspectorPrefs({});
  }
}

function saveArtifactInspectorPrefs(value) {
  try {
    if (typeof window === "undefined" || !window.localStorage) return;
    const prefs = normalizeArtifactInspectorPrefs(value);
    window.localStorage.setItem(ARTIFACT_INSPECTOR_PREFS_STORAGE_KEY, JSON.stringify(prefs));
  } catch (_) {
    // localStorage may be blocked; ignore and continue with in-memory state
  }
}

export function ArtifactInspectorPanel({
  graphRunSummary,
  compareGraphRunSummary,
  compareRunStatusText,
  selectedReplayableCompareSessionText,
  selectedReplayableCompareSessionArtifactExpectationSummaryText,
  selectedReplayableCompareSessionArtifactExpectationText,
  controlRequest,
  onArtifactInspectorStatusChange,
}) {
  const hasGraphRunSummary = Boolean(graphRunSummary);
  const runtimeContract = graphRunSummary?.runtime_contract_diagnostics || null;
  const rdShape = normalizeShape(
    graphRunSummary?.radar_map_summary?.rd_shape || graphRunSummary?.quicklook?.rd_shape
  );
  const raShape = normalizeShape(
    graphRunSummary?.radar_map_summary?.ra_shape || graphRunSummary?.quicklook?.ra_shape
  );
  const rdPeaks = normalizePeakList(graphRunSummary?.quicklook?.rd_top_peaks, "doppler_bin", "range_bin");
  const raPeaks = normalizePeakList(graphRunSummary?.quicklook?.ra_top_peaks, "angle_bin", "range_bin");

  const [rdRangeBinText, setRdRangeBinText] = React.useState("0");
  const [rdDopplerBinText, setRdDopplerBinText] = React.useState("0");
  const [raRangeBinText, setRaRangeBinText] = React.useState("0");
  const [raAngleBinText, setRaAngleBinText] = React.useState("0");
  const [rdPeakSelectText, setRdPeakSelectText] = React.useState("-1");
  const [raPeakSelectText, setRaPeakSelectText] = React.useState("-1");
  const [rdPeakLock, setRdPeakLock] = React.useState(false);
  const [raPeakLock, setRaPeakLock] = React.useState(false);
  const [artifactInspectorPrefs, setArtifactInspectorPrefs] = React.useState(() => loadArtifactInspectorPrefs());
  const lastAppliedControlNonceRef = React.useRef(null);
  const liveCompareEvidenceExpanded = normalizeArtifactInspectorPrefs(
    artifactInspectorPrefs
  ).liveCompareEvidenceExpanded;
  const historyArtifactExpectationExpanded = normalizeArtifactInspectorPrefs(
    artifactInspectorPrefs
  ).historyArtifactExpectationExpanded;
  const defaultProbeState = React.useMemo(
    () => buildDefaultArtifactInspectorProbeState(rdPeaks, raPeaks),
    [raPeaks, rdPeaks]
  );

  const resetArtifactInspectorProbeControls = React.useCallback(() => {
    setRdRangeBinText(defaultProbeState.rdRangeBinText);
    setRdDopplerBinText(defaultProbeState.rdDopplerBinText);
    setRaRangeBinText(defaultProbeState.raRangeBinText);
    setRaAngleBinText(defaultProbeState.raAngleBinText);
    setRdPeakSelectText(defaultProbeState.rdPeakSelectText);
    setRaPeakSelectText(defaultProbeState.raPeakSelectText);
    setRdPeakLock(defaultProbeState.rdPeakLock);
    setRaPeakLock(defaultProbeState.raPeakLock);
  }, [defaultProbeState]);

  React.useEffect(() => {
    resetArtifactInspectorProbeControls();
  }, [graphRunSummary, resetArtifactInspectorProbeControls]);

  React.useEffect(() => {
    if (!rdPeakLock) return;
    const idx = Number(rdPeakSelectText);
    const peak = Number.isFinite(idx) && idx >= 0 ? rdPeaks[Math.floor(idx)] : null;
    if (!peak) return;
    setRdRangeBinText(String(peak.col));
    setRdDopplerBinText(String(peak.row));
  }, [rdPeakLock, rdPeakSelectText, rdPeaks]);

  React.useEffect(() => {
    if (!raPeakLock) return;
    const idx = Number(raPeakSelectText);
    const peak = Number.isFinite(idx) && idx >= 0 ? raPeaks[Math.floor(idx)] : null;
    if (!peak) return;
    setRaRangeBinText(String(peak.col));
    setRaAngleBinText(String(peak.row));
  }, [raPeakLock, raPeakSelectText, raPeaks]);

  const rdProbe = React.useMemo(() => {
    const rangeBin = parseBinText(rdRangeBinText, 0);
    const dopplerBin = parseBinText(rdDopplerBinText, 0);
    return computeProbe(rdPeaks, dopplerBin, rangeBin, rdShape);
  }, [rdDopplerBinText, rdPeaks, rdRangeBinText, rdShape]);

  const raProbe = React.useMemo(() => {
    const rangeBin = parseBinText(raRangeBinText, 0);
    const angleBin = parseBinText(raAngleBinText, 0);
    return computeProbe(raPeaks, angleBin, rangeBin, raShape);
  }, [raAngleBinText, raPeaks, raRangeBinText, raShape]);

  const runCompare = React.useMemo(
    () => buildRunCompareSummary(graphRunSummary, compareGraphRunSummary),
    [compareGraphRunSummary, graphRunSummary]
  );
  const selectedHistoryArtifactExpectationLines = React.useMemo(() => {
    return String(selectedReplayableCompareSessionArtifactExpectationText || "-")
      .split("\n")
      .map((line) => String(line || "").trim())
      .filter(Boolean);
  }, [selectedReplayableCompareSessionArtifactExpectationText]);
  const compareTone = runCompare.assessment === "hold"
    ? "#ff9a9a"
    : runCompare.assessment === "review"
      ? "#f4c265"
      : "#7ee3b8";
  const liveCompareSummaryText = runCompare.available
    ? `compare_assessment: ${runCompare.assessment} | compare_flags: ${runCompare.flagSummary}`
    : String(compareRunStatusText || "compare run not loaded");
  const selectedHistoryArtifactExpectationSummaryLine = String(
    selectedReplayableCompareSessionArtifactExpectationSummaryText || "selected_history_artifact_expectation: -"
  );
  const artifactInspectorProbeState = React.useMemo(() => {
    const probesDefault = (
      String(rdRangeBinText || "") === String(defaultProbeState.rdRangeBinText || "")
      && String(rdDopplerBinText || "") === String(defaultProbeState.rdDopplerBinText || "")
      && String(raRangeBinText || "") === String(defaultProbeState.raRangeBinText || "")
      && String(raAngleBinText || "") === String(defaultProbeState.raAngleBinText || "")
      && String(rdPeakSelectText || "") === String(defaultProbeState.rdPeakSelectText || "")
      && String(raPeakSelectText || "") === String(defaultProbeState.raPeakSelectText || "")
      && rdPeakLock === Boolean(defaultProbeState.rdPeakLock)
      && raPeakLock === Boolean(defaultProbeState.raPeakLock)
    );
    return {
      probesDefault,
      text: `probe_state: ${probesDefault ? "default" : "customized"} | rd_cursor=${Number(rdProbe.row || 0)}/${Number(rdProbe.col || 0)} | rd_lock=${rdPeakLock ? "on" : "off"} | ra_cursor=${Number(raProbe.row || 0)}/${Number(raProbe.col || 0)} | ra_lock=${raPeakLock ? "on" : "off"}`,
    };
  }, [
    defaultProbeState,
    raAngleBinText,
    raPeakLock,
    raPeakSelectText,
    raProbe.col,
    raProbe.row,
    raRangeBinText,
    rdDopplerBinText,
    rdPeakLock,
    rdPeakSelectText,
    rdProbe.col,
    rdProbe.row,
    rdRangeBinText,
  ]);
  const artifactInspectorLayoutStateText = React.useMemo(() => {
    const foldsDefault = liveCompareEvidenceExpanded === true && historyArtifactExpectationExpanded === true;
    const probesDefault = artifactInspectorProbeState.probesDefault === true;
    const overallState = foldsDefault && probesDefault ? "default" : "customized";
    return `layout_state: ${overallState} | live=${liveCompareEvidenceExpanded ? "expanded" : "collapsed"} | history=${historyArtifactExpectationExpanded ? "expanded" : "collapsed"} | probes=${probesDefault ? "default" : "customized"} | reset_required=${overallState === "default" ? "no" : "yes"}`;
  }, [
    artifactInspectorProbeState.probesDefault,
    historyArtifactExpectationExpanded,
    liveCompareEvidenceExpanded,
  ]);
  const artifactInspectorStatusBadges = React.useMemo(() => {
    const layoutDefault = (
      liveCompareEvidenceExpanded === true
      && historyArtifactExpectationExpanded === true
      && artifactInspectorProbeState.probesDefault === true
    );
    const auditStateText = buildArtifactInspectorAuditStateText(artifactInspectorPrefs);
    const auditState = String(auditStateText.split("|")[0] || "")
      .replace(/^audit_state:\s*/i, "")
      .trim()
      .toLowerCase();
    return buildArtifactInspectorStatusBadges({
      layoutDefault,
      probesDefault: artifactInspectorProbeState.probesDefault === true,
      liveCompareEvidenceExpanded,
      historyArtifactExpectationExpanded,
      auditState,
    });
  }, [
    artifactInspectorPrefs,
    artifactInspectorProbeState.probesDefault,
    historyArtifactExpectationExpanded,
    liveCompareEvidenceExpanded,
  ]);
  const artifactInspectorStatusBadgesText = React.useMemo(() => {
    const labels = (Array.isArray(artifactInspectorStatusBadges) ? artifactInspectorStatusBadges : [])
      .map((row) => String(row?.label || "").trim())
      .filter(Boolean);
    return `status_badges: ${labels.length > 0 ? labels.join(" | ") : "-"}`;
  }, [artifactInspectorStatusBadges]);
  const artifactInspectorLastActionText = React.useMemo(
    () => String(normalizeArtifactInspectorPrefs(artifactInspectorPrefs).lastActionText || "last_action: seq=0 | idle"),
    [artifactInspectorPrefs]
  );
  const artifactInspectorRecentActionsText = React.useMemo(
    () => buildArtifactInspectorRecentActionsText(normalizeArtifactInspectorPrefs(artifactInspectorPrefs).recentActionEntries),
    [artifactInspectorPrefs]
  );
  const artifactInspectorAuditSummaryText = React.useMemo(
    () => buildArtifactInspectorAuditSummaryText(artifactInspectorPrefs),
    [artifactInspectorPrefs]
  );
  const artifactInspectorAuditStateText = React.useMemo(
    () => buildArtifactInspectorAuditStateText(artifactInspectorPrefs),
    [artifactInspectorPrefs]
  );
  const artifactInspectorAuditCapacityText = React.useMemo(
    () => buildArtifactInspectorAuditCapacityText(artifactInspectorPrefs),
    [artifactInspectorPrefs]
  );
  const artifactInspectorHasRecentActions = React.useMemo(
    () => normalizeArtifactInspectorPrefs(artifactInspectorPrefs).recentActionEntries.length > 0,
    [artifactInspectorPrefs]
  );
  React.useEffect(() => {
    if (typeof onArtifactInspectorStatusChange !== "function") return;
    onArtifactInspectorStatusChange({
      layoutStateText: artifactInspectorLayoutStateText,
      probeStateText: artifactInspectorProbeState.text,
      statusBadgesText: artifactInspectorStatusBadgesText,
      lastActionText: artifactInspectorLastActionText,
      recentActionsText: artifactInspectorRecentActionsText,
      auditStateText: artifactInspectorAuditStateText,
      auditCapacityText: artifactInspectorAuditCapacityText,
      auditSummaryText: artifactInspectorAuditSummaryText,
    });
  }, [
    artifactInspectorAuditCapacityText,
    artifactInspectorAuditStateText,
    artifactInspectorAuditSummaryText,
    artifactInspectorLayoutStateText,
    artifactInspectorLastActionText,
    artifactInspectorRecentActionsText,
    artifactInspectorProbeState.text,
    artifactInspectorStatusBadgesText,
    onArtifactInspectorStatusChange,
  ]);
  const toggleLiveCompareEvidenceExpanded = React.useCallback(() => {
    setArtifactInspectorPrefs((prev) => {
      const next = normalizeArtifactInspectorPrefs(prev);
      const actionUpdate = buildArtifactInspectorLastActionUpdate(
        next,
        `inspector:live_compare=${next.liveCompareEvidenceExpanded ? "collapsed" : "expanded"}`
      );
      const updated = {
        ...next,
        liveCompareEvidenceExpanded: !next.liveCompareEvidenceExpanded,
        ...actionUpdate,
      };
      saveArtifactInspectorPrefs(updated);
      return updated;
    });
  }, []);
  const toggleHistoryArtifactExpectationExpanded = React.useCallback(() => {
    setArtifactInspectorPrefs((prev) => {
      const next = normalizeArtifactInspectorPrefs(prev);
      const actionUpdate = buildArtifactInspectorLastActionUpdate(
        next,
        `inspector:history_snapshot=${next.historyArtifactExpectationExpanded ? "collapsed" : "expanded"}`
      );
      const updated = {
        ...next,
        historyArtifactExpectationExpanded: !next.historyArtifactExpectationExpanded,
        ...actionUpdate,
      };
      saveArtifactInspectorPrefs(updated);
      return updated;
    });
  }, []);
  const resetArtifactInspectorLayout = React.useCallback(() => {
    const defaults = normalizeArtifactInspectorPrefs({});
    const actionUpdate = buildArtifactInspectorLastActionUpdate(defaults, "inspector:reset_layout");
    const updated = {
      ...defaults,
      ...actionUpdate,
    };
    setArtifactInspectorPrefs(updated);
    saveArtifactInspectorPrefs(updated);
    resetArtifactInspectorProbeControls();
  }, [resetArtifactInspectorProbeControls]);
  const clearArtifactInspectorActionTrail = React.useCallback(() => {
    setArtifactInspectorPrefs((prev) => {
      const updated = clearArtifactInspectorActionTrailState(prev);
      saveArtifactInspectorPrefs(updated);
      return updated;
    });
  }, []);
  React.useEffect(() => {
    const command = controlRequest && typeof controlRequest === "object" ? controlRequest : null;
    const nonce = Number(command?.nonce);
    if (!command || !Number.isFinite(nonce) || nonce <= 0) return;
    if (lastAppliedControlNonceRef.current === nonce) return;
    lastAppliedControlNonceRef.current = nonce;
    setArtifactInspectorPrefs((prev) => {
      const next = applyArtifactInspectorPrefsCommand(prev, command);
      let updated = {
        ...next,
      };
      if (command.clearActionTrail === true) {
        updated = clearArtifactInspectorActionTrailState(updated);
      }
      if (String(command?.lastActionLabel || "").trim()) {
        Object.assign(updated, buildArtifactInspectorLastActionUpdate(next, String(command.lastActionLabel).trim()));
      }
      saveArtifactInspectorPrefs(updated);
      return updated;
    });
    if (command.resetProbeControls === true) {
      resetArtifactInspectorProbeControls();
    }
  }, [controlRequest, resetArtifactInspectorProbeControls]);

  const renderProbeSummary = (probe) => {
    const exact = probe.exact;
    const nearest = probe.nearest;
    const nearestPart = nearest
      ? `nearest_peak=#${nearest.index} d=${Number(probe.nearestDist)} rel_db=${Number(nearest.relDb).toFixed(2)}`
      : "nearest_peak=none";
    const exactPart = exact
      ? `exact_peak=#${exact.index} rel_db=${Number(exact.relDb).toFixed(2)}`
      : "exact_peak=none";
    return [
      `${exactPart} | ${nearestPart}`,
      `cursor_norm=(${Number(probe.rowNorm).toFixed(3)}, ${Number(probe.colNorm).toFixed(3)})`,
    ];
  };

  return h("div", { className: "result-box", key: "aibox" }, [
    h("div", {
      key: "layout_controls",
      style: {
        display: "flex",
        flexDirection: "column",
        gap: "6px",
        marginBottom: "8px",
      },
    }, [
      h("div", {
        key: "layout_controls_header",
        style: {
          display: "flex",
          alignItems: "flex-start",
          justifyContent: "space-between",
          gap: "8px",
          flexWrap: "wrap",
        },
      }, [
        h("div", {
          key: "layout_status_stack",
          style: {
            display: "flex",
            flexDirection: "column",
            gap: "4px",
            minWidth: "280px",
            flex: "1 1 360px",
          },
        }, [
          h("div", {
            key: "layout_state",
            style: { color: "#8fb3c9" },
          }, artifactInspectorLayoutStateText),
        h("div", {
          key: "probe_state",
          style: { color: "#8fb3c9" },
        }, artifactInspectorProbeState.text),
        h("div", {
          key: "audit_state",
          style: { color: "#8fb3c9" },
        }, artifactInspectorAuditStateText),
        h("div", {
          key: "audit_capacity",
          style: { color: "#8fb3c9" },
        }, artifactInspectorAuditCapacityText),
        h("div", {
          key: "audit_summary",
          style: { color: "#8fb3c9" },
        }, artifactInspectorAuditSummaryText),
        h("div", {
          key: "last_action",
          style: { color: "#8fb3c9" },
        }, artifactInspectorLastActionText),
        h("div", {
          key: "recent_actions",
          style: { color: "#8fb3c9" },
        }, artifactInspectorRecentActionsText),
      ]),
        h("button", {
          key: "reset_artifact_inspector_layout",
          className: "btn",
          onClick: resetArtifactInspectorLayout,
        }, "Reset Layout"),
        h("button", {
          key: "clear_artifact_inspector_action_trail",
          className: "btn",
          onClick: clearArtifactInspectorActionTrail,
          disabled: !artifactInspectorHasRecentActions,
        }, "Clear Action Trail"),
      ]),
      h("div", { className: "chip-list", key: "artifact_inspector_status_chips" }, (
        Array.isArray(artifactInspectorStatusBadges) && artifactInspectorStatusBadges.length > 0
          ? artifactInspectorStatusBadges
          : [{ label: "layout:unknown", tone: "status-neutral" }]
      ).map((row, idx) =>
        h("span", {
          className: `chip ${String(row?.tone || "status-neutral")}`,
          key: `artifact_inspector_status_chip_${idx}`,
        }, String(row?.label || "-"))
      )),
    ]),
    hasGraphRunSummary
      ? h("div", { key: "kpi", style: { marginBottom: "8px" } }, [
          `paths=${Number(graphRunSummary?.path_summary?.path_count_total || 0)} | `,
          `adc_shape=${Array.isArray(graphRunSummary?.adc_summary?.shape) ? graphRunSummary.adc_summary.shape.join("x") : "-"} | `,
          `rd=${Array.isArray(graphRunSummary?.radar_map_summary?.rd_shape) ? graphRunSummary.radar_map_summary.rd_shape.join("x") : "-"} | `,
          `ra=${Array.isArray(graphRunSummary?.radar_map_summary?.ra_shape) ? graphRunSummary.radar_map_summary.ra_shape.join("x") : "-"}`,
        ])
      : h("div", { key: "kpi_empty", style: { marginBottom: "8px", color: "#8fb3c9" } }, "run graph first to inspect artifacts"),
    runtimeContract
      ? h("div", { key: "contract_runtime", style: { marginBottom: "8px", color: "#8fb3c9" } }, [
          `contract_delta(unique/attempt): ${formatSigned(runtimeContract?.delta?.unique_warning_count)}/${formatSigned(runtimeContract?.delta?.attempt_count_total)} | `,
          `contract_total(unique/attempt): ${Number(runtimeContract?.snapshot?.unique_warning_count || 0)}/${Number(runtimeContract?.snapshot?.attempt_count_total || 0)}`,
        ])
      : null,
    h("div", { key: "diff_overlay", style: { marginBottom: "8px", padding: "8px", border: "1px solid #284a5d", borderRadius: "6px", background: "rgba(9, 22, 30, 0.62)" } }, [
      h("div", { key: "diff_header", style: { display: "flex", alignItems: "center", justifyContent: "space-between", gap: "8px", marginBottom: "5px" } }, [
        h("div", { key: "diff_title", style: { color: "#8fb3c9" } }, "run-to-run diff overlay:"),
        h("button", {
          key: "toggle_live_compare_evidence",
          className: "btn",
          onClick: toggleLiveCompareEvidenceExpanded,
        }, liveCompareEvidenceExpanded ? "Hide Live Compare Evidence" : "Show Live Compare Evidence"),
      ]),
      h("div", { key: "diff_summary", style: { marginBottom: liveCompareEvidenceExpanded ? "5px" : "0", color: compareTone } }, liveCompareSummaryText),
      liveCompareEvidenceExpanded
        ? (runCompare.available
          ? h("div", { key: "diff_body", style: { display: "flex", flexDirection: "column", gap: "3px" } }, [
              h("div", { key: "diff_hdr" }, `current=${runCompare.currentGraphRunId} | compare=${runCompare.compareGraphRunId}`),
              h("div", { key: "diff_assessment", style: { color: compareTone } }, `compare_assessment: ${runCompare.assessment}`),
              h("div", { key: "diff_flags" }, `compare_flags: ${runCompare.flagSummary}`),
              h("div", { key: "diff_source" }, `adc_source(current/compare): ${runCompare.adcSource.current}/${runCompare.adcSource.compare}`),
              h(
                "div",
                { key: "diff_artifacts" },
                `required_artifacts(current/compare/total): ${runCompare.requiredArtifactCounts.currentPresent}/${runCompare.requiredArtifactCounts.comparePresent}/${runCompare.requiredArtifactCounts.total}`
              ),
              h("div", { key: "diff_artifacts_delta" }, `artifact_presence_delta: ${runCompare.artifactPresenceDeltaText}`),
              h("div", { key: "diff_shape_adc" }, `shape.adc: ${runCompare.shapeText.adc} | eq=${runCompare.shapeEq.adc}`),
              h("div", { key: "diff_shape_rd" }, `shape.rd: ${runCompare.shapeText.rd} | eq=${runCompare.shapeEq.rd}`),
              h("div", { key: "diff_shape_ra" }, `shape.ra: ${runCompare.shapeText.ra} | eq=${runCompare.shapeEq.ra}`),
              h("div", { key: "diff_paths" }, `path_count_delta: ${formatSigned(runCompare.pathCountDelta)}`),
              h(
                "div",
                { key: "diff_rd" },
                runCompare.rdPeakDelta
                  ? `rd_peak_delta(range/doppler/rel_db): ${formatSigned(runCompare.rdPeakDelta.rangeBinDelta)}/${formatSigned(runCompare.rdPeakDelta.dopplerBinDelta)}/${runCompare.rdPeakDelta.relDbDelta.toFixed(2)}`
                  : "rd_peak_delta: unavailable"
              ),
              h(
                "div",
                { key: "diff_ra" },
                runCompare.raPeakDelta
                  ? `ra_peak_delta(range/angle/rel_db): ${formatSigned(runCompare.raPeakDelta.rangeBinDelta)}/${formatSigned(runCompare.raPeakDelta.angleBinDelta)}/${runCompare.raPeakDelta.relDbDelta.toFixed(2)}`
                  : "ra_peak_delta: unavailable"
              ),
            ])
          : h("div", { key: "diff_empty", style: { color: "#86a1b4" } }, String(compareRunStatusText || "compare run not loaded")))
        : null,
    ]),
    h("div", { key: "history_artifact_expectation_overlay", style: { marginBottom: "8px", padding: "8px", border: "1px solid #284a5d", borderRadius: "6px", background: "rgba(9, 22, 30, 0.62)" } }, [
      h("div", { key: "history_artifact_expectation_header", style: { display: "flex", alignItems: "center", justifyContent: "space-between", gap: "8px", marginBottom: "5px" } }, [
        h("div", { key: "history_artifact_expectation_title", style: { color: "#8fb3c9" } }, "selected history pair artifact expectation:"),
        h("button", {
          key: "toggle_history_artifact_expectation",
          className: "btn",
          onClick: toggleHistoryArtifactExpectationExpanded,
        }, historyArtifactExpectationExpanded ? "Hide History Snapshot" : "Show History Snapshot"),
      ]),
      h("div", { key: "history_artifact_expectation_pair", style: { marginBottom: "3px", color: "#b9d5e7" } }, String(selectedReplayableCompareSessionText || "selected_history_pair: -")),
      h("div", { key: "history_artifact_expectation_summary", style: { marginBottom: historyArtifactExpectationExpanded ? "5px" : "0", color: "#9fc1d4" } }, selectedHistoryArtifactExpectationSummaryLine),
      historyArtifactExpectationExpanded
        ? h("div", { key: "history_artifact_expectation_body", style: { display: "flex", flexDirection: "column", gap: "3px" } }, selectedHistoryArtifactExpectationLines.map((line, idx) =>
            h("div", { key: `history_artifact_expectation_line_${idx}`, style: { color: "#cfe2ef" } }, line)
          ))
        : null,
    ]),
    h("div", { key: "probe", style: { marginBottom: "8px", padding: "8px", border: "1px solid #284a5d", borderRadius: "6px", background: "rgba(9, 22, 30, 0.62)" } }, [
      h("div", { key: "probe_title", style: { marginBottom: "6px", color: "#8fb3c9" } }, "cursor probe + peak lock:"),
      h("div", { key: "probe_grid", style: { display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: "8px" } }, [
        h("div", { key: "probe_rd", style: { border: "1px solid #264758", borderRadius: "6px", padding: "6px" } }, [
          h("div", { key: "probe_rd_title", style: { marginBottom: "4px", color: "#9fc1d4" } }, `RD probe (shape=${safeShapeLabel(rdShape)})`),
          h("div", { key: "probe_rd_inputs", style: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: "6px", marginBottom: "6px" } }, [
            h("input", {
              key: "rd_range_bin",
              className: "input",
              value: rdRangeBinText,
              onChange: (e) => setRdRangeBinText(String(e.target.value || "0")),
              placeholder: "range_bin",
            }),
            h("input", {
              key: "rd_doppler_bin",
              className: "input",
              value: rdDopplerBinText,
              onChange: (e) => setRdDopplerBinText(String(e.target.value || "0")),
              placeholder: "doppler_bin",
            }),
          ]),
          h("div", { key: "probe_rd_peakctl", style: { display: "grid", gridTemplateColumns: "1fr auto", gap: "6px", marginBottom: "6px" } }, [
            h("select", {
              key: "rd_peak_select",
              className: "select",
              value: rdPeakSelectText,
              onChange: (e) => setRdPeakSelectText(String(e.target.value || "-1")),
            }, [
              h("option", { key: "rd_peak_none", value: "-1" }, "RD peak: none"),
              ...rdPeaks.map((peak) =>
                h(
                  "option",
                  { key: `rd_peak_${peak.index}`, value: String(peak.index) },
                  `#${peak.index} d=${peak.row} r=${peak.col} rel=${Number(peak.relDb).toFixed(2)}`
                )
              ),
            ]),
            h("button", {
              key: "rd_snap",
              className: "btn",
              onClick: () => {
                const idx = Number(rdPeakSelectText);
                const peak = Number.isFinite(idx) && idx >= 0 ? rdPeaks[Math.floor(idx)] : null;
                if (!peak) return;
                setRdRangeBinText(String(peak.col));
                setRdDopplerBinText(String(peak.row));
              },
            }, "Snap"),
          ]),
          h("label", { key: "rd_lock_lbl", style: { display: "inline-flex", alignItems: "center", gap: "6px", color: "#8fb3c9" } }, [
            h("input", {
              key: "rd_lock_chk",
              type: "checkbox",
              checked: Boolean(rdPeakLock),
              onChange: (e) => setRdPeakLock(Boolean(e.target.checked)),
            }),
            "Peak lock",
          ]),
          ...renderProbeSummary(rdProbe).map((line, idx) =>
            h("div", { key: `rd_probe_line_${idx}`, style: { marginTop: idx === 0 ? "6px" : "2px", color: "#b9d5e7" } }, line)
          ),
        ]),
        h("div", { key: "probe_ra", style: { border: "1px solid #264758", borderRadius: "6px", padding: "6px" } }, [
          h("div", { key: "probe_ra_title", style: { marginBottom: "4px", color: "#9fc1d4" } }, `RA probe (shape=${safeShapeLabel(raShape)})`),
          h("div", { key: "probe_ra_inputs", style: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: "6px", marginBottom: "6px" } }, [
            h("input", {
              key: "ra_range_bin",
              className: "input",
              value: raRangeBinText,
              onChange: (e) => setRaRangeBinText(String(e.target.value || "0")),
              placeholder: "range_bin",
            }),
            h("input", {
              key: "ra_angle_bin",
              className: "input",
              value: raAngleBinText,
              onChange: (e) => setRaAngleBinText(String(e.target.value || "0")),
              placeholder: "angle_bin",
            }),
          ]),
          h("div", { key: "probe_ra_peakctl", style: { display: "grid", gridTemplateColumns: "1fr auto", gap: "6px", marginBottom: "6px" } }, [
            h("select", {
              key: "ra_peak_select",
              className: "select",
              value: raPeakSelectText,
              onChange: (e) => setRaPeakSelectText(String(e.target.value || "-1")),
            }, [
              h("option", { key: "ra_peak_none", value: "-1" }, "RA peak: none"),
              ...raPeaks.map((peak) =>
                h(
                  "option",
                  { key: `ra_peak_${peak.index}`, value: String(peak.index) },
                  `#${peak.index} a=${peak.row} r=${peak.col} rel=${Number(peak.relDb).toFixed(2)}`
                )
              ),
            ]),
            h("button", {
              key: "ra_snap",
              className: "btn",
              onClick: () => {
                const idx = Number(raPeakSelectText);
                const peak = Number.isFinite(idx) && idx >= 0 ? raPeaks[Math.floor(idx)] : null;
                if (!peak) return;
                setRaRangeBinText(String(peak.col));
                setRaAngleBinText(String(peak.row));
              },
            }, "Snap"),
          ]),
          h("label", { key: "ra_lock_lbl", style: { display: "inline-flex", alignItems: "center", gap: "6px", color: "#8fb3c9" } }, [
            h("input", {
              key: "ra_lock_chk",
              type: "checkbox",
              checked: Boolean(raPeakLock),
              onChange: (e) => setRaPeakLock(Boolean(e.target.checked)),
            }),
            "Peak lock",
          ]),
          ...renderProbeSummary(raProbe).map((line, idx) =>
            h("div", { key: `ra_probe_line_${idx}`, style: { marginTop: idx === 0 ? "6px" : "2px", color: "#b9d5e7" } }, line)
          ),
        ]),
      ]),
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
      ).slice(0, 24).map((row, idx) => {
        const artifactMap = row?.artifacts && typeof row.artifacts === "object" ? row.artifacts : {};
        const artifactCount = Object.keys(artifactMap).length;
        const isCacheHit = Boolean(row?.cache_hit) || String(row?.status || "").toLowerCase() === "cached";
        const artifactBadge = artifactCount <= 0 ? "n/a" : (isCacheHit ? "cache-hit" : "recomputed");
        const badgeStyle = artifactBadge === "cache-hit"
          ? { border: "1px solid #2f6f57", color: "#7ee3b8", background: "rgba(53, 200, 133, 0.1)" }
          : artifactBadge === "recomputed"
            ? { border: "1px solid #8a6a2d", color: "#f4c265", background: "rgba(240, 179, 58, 0.1)" }
            : { border: "1px solid #36586d", color: "#8eb6ca", background: "rgba(58, 103, 129, 0.1)" };
        const sourceRun = String(row?.cache_source_graph_run_id || "").trim();
        return h("div", { key: `tr_${idx}` }, [
          `- #${Number(idx)} ${String(row?.node_type || "-")} (${String(row?.node_id || "-")}) | status=${String(row?.status || "-")} | contract=${String(row?.output_contract || "-")} | artifact=`,
          h(
            "span",
            {
              style: {
                display: "inline-flex",
                alignItems: "center",
                borderRadius: "999px",
                padding: "1px 7px",
                fontSize: "10px",
                marginLeft: "5px",
                ...badgeStyle,
              },
            },
            artifactBadge
          ),
          sourceRun && isCacheHit ? ` | source=${sourceRun}` : "",
        ]);
      })),
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
