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
  getGraphRunSummaryMaybe,
  getGraphTemplates,
  getPolicyEval,
  exportRegressionSession,
  listGraphRuns,
  listPolicyEvals,
  runRegressionSession,
  validateGraphContract,
} from "./api_client.mjs";
import {
  ContractWarningOverlay,
  GraphCanvasPanel,
  GraphInputsPanel,
  NodeInspectorPanel,
  TopBar,
} from "./panels.mjs";
import { buildRunCompareSummary } from "./compare_summary.mjs";
import {
  applyRuntimePurposePreset,
  buildRuntimePurposePresetOverrides,
  getRuntimePurposePairLabel,
  getRuntimePurposePresetLabel,
  RUNTIME_PURPOSE_PRESET_CURRENT_CONFIG,
  RUNTIME_PURPOSE_PRESET_LOW_FIDELITY,
  RUNTIME_PURPOSE_PRESET_OPTIONS,
  RUNTIME_PURPOSE_QUICK_PAIR_OPTIONS,
} from "./runtime_purpose_presets.mjs";
import { splitTokenList } from "./runtime_overrides.mjs";
import { useGateOps } from "./hooks/use_gate_ops.mjs";
import { useGraphRunOps } from "./hooks/use_graph_run_ops.mjs";

const h = React.createElement;
const LAYOUT_MODE_SET = new Set(["triad", "build", "review", "focus"]);
const DENSITY_MODE_SET = new Set(["comfortable", "compact"]);
const COMPARE_SESSION_STORAGE_KEY = "graph_lab_compare_session_history_v1";
const COMPARE_SESSION_HISTORY_LIMIT = 8;
const COMPARE_REPLAY_PAIR_OPTION_LIMIT = 6;
const PINNED_COMPARE_QUICK_ACTION_LIMIT = 3;
const COMPARE_ARTIFACT_PATH_FINGERPRINT_ALGO = "fnv1a32_path_text";
const COMPARE_SESSION_EXPORT_SCHEMA_VERSION = "graph_lab_compare_history_export_v2";
const COMPARE_SESSION_IMPORT_SCHEMA_LEGACY = "legacy_pre_v2";
const COMPARE_SESSION_RETENTION_POLICY_DEFAULT = "retain_8";
const COMPARE_SESSION_RETENTION_POLICY_OPTIONS = [
  { id: "retain_2", label: "Keep Latest 2" },
  { id: "retain_2_preserve_pinned", label: "Keep Latest 2 + Preserve Pinned" },
  { id: "retain_2_preserve_saved", label: "Keep Latest 2 + Preserve Saved" },
  { id: "retain_4", label: "Keep Latest 4" },
  { id: "retain_4_preserve_pinned", label: "Keep Latest 4 + Preserve Pinned" },
  { id: "retain_4_preserve_saved", label: "Keep Latest 4 + Preserve Saved" },
  { id: "retain_8", label: "Keep Latest 8" },
  { id: "retain_8_preserve_pinned", label: "Keep Latest 8 + Preserve Pinned" },
  { id: "retain_8_preserve_saved", label: "Keep Latest 8 + Preserve Saved" },
];

function formatSigned(value) {
  const n = Number(value || 0);
  return `${n >= 0 ? "+" : ""}${n}`;
}

function normalizeLayoutMode(value) {
  const mode = String(value || "").trim().toLowerCase();
  return LAYOUT_MODE_SET.has(mode) ? mode : "triad";
}

function normalizeDensityMode(value) {
  const mode = String(value || "").trim().toLowerCase();
  return DENSITY_MODE_SET.has(mode) ? mode : "comfortable";
}

function normalizeCompareSessionField(value, maxLength) {
  return String(value || "").trim().slice(0, Number(maxLength || 160));
}

function normalizeCompareSessionRetentionPolicy(value, fallback = COMPARE_SESSION_RETENTION_POLICY_DEFAULT) {
  const token = String(value || "").trim().toLowerCase();
  if (
    token === "retain_2"
    || token === "retain_2_preserve_pinned"
    || token === "retain_2_preserve_saved"
    || token === "retain_4"
    || token === "retain_4_preserve_pinned"
    || token === "retain_4_preserve_saved"
    || token === "retain_8"
    || token === "retain_8_preserve_pinned"
    || token === "retain_8_preserve_saved"
  ) {
    return token;
  }
  return String(fallback || "").trim().toLowerCase();
}

function getCompareSessionRetentionLimit(policy) {
  const normalized = normalizeCompareSessionRetentionPolicy(policy, COMPARE_SESSION_RETENTION_POLICY_DEFAULT);
  if (normalized.startsWith("retain_2")) return 2;
  if (normalized.startsWith("retain_4")) return 4;
  return COMPARE_SESSION_HISTORY_LIMIT;
}

function getCompareSessionRetentionPreserveMode(policy) {
  const normalized = normalizeCompareSessionRetentionPolicy(policy, COMPARE_SESSION_RETENTION_POLICY_DEFAULT);
  if (normalized.endsWith("_preserve_saved")) return "saved";
  if (normalized.endsWith("_preserve_pinned")) return "pinned";
  return "none";
}

function shouldCompareSessionRetentionPreservePinned(policy) {
  const mode = getCompareSessionRetentionPreserveMode(policy);
  return mode === "pinned" || mode === "saved";
}

function shouldCompareSessionRetentionPreserveSaved(policy) {
  return getCompareSessionRetentionPreserveMode(policy) === "saved";
}

function summarizeCompareSessionRetentionPolicy(policy, outcome) {
  const normalized = normalizeCompareSessionRetentionPolicy(policy, COMPARE_SESSION_RETENTION_POLICY_DEFAULT);
  const summary = outcome && typeof outcome === "object" ? outcome : {};
  return [
    `compare_history_retention_policy: ${normalized}`,
    `keep_latest=${getCompareSessionRetentionLimit(normalized)}`,
    `preserve_scope=${String(summary.preserveScope || getCompareSessionRetentionPreserveMode(normalized))}`,
    `preserve_pinned=${shouldCompareSessionRetentionPreservePinned(normalized)}`,
    `preserve_saved=${shouldCompareSessionRetentionPreserveSaved(normalized)}`,
    `retained_rows=${Number(summary.retainedRows || 0)}/${Number(summary.availableRows || 0)}`,
    `managed_pinned_pairs=${Number(summary.pinnedPairsManaged || 0)}`,
    `retained_pinned_pairs=${Number(summary.pinnedPairsRetained || 0)}`,
    `extra_pinned_rows=${Number(summary.extraPinnedRowsRetained || 0)}`,
    `managed_saved_pairs=${Number(summary.savedPairsManaged || 0)}`,
    `retained_saved_pairs=${Number(summary.savedPairsRetained || 0)}`,
    `extra_saved_rows=${Number(summary.extraSavedRowsRetained || 0)}`,
  ].join(" | ");
}

function normalizeCompareSessionHistoryEntry(entry, ordinal) {
  const row = entry && typeof entry === "object" ? entry : {};
  return {
    id: normalizeCompareSessionField(row.id, 96) || `cmp_saved_${Number(ordinal) + 1}`,
    timestampUtc: normalizeCompareSessionField(row.timestampUtc, 64),
    source: normalizeCompareSessionField(row.source, 48),
    status: normalizeCompareSessionField(row.status, 48),
    pairLabel: normalizeCompareSessionField(row.pairLabel, 160),
    baselinePresetId: normalizeCompareSessionField(row.baselinePresetId, 96),
    targetPresetId: normalizeCompareSessionField(row.targetPresetId, 96),
    phase: normalizeCompareSessionField(row.phase, 48),
    compareRunId: normalizeCompareSessionField(row.compareRunId, 128),
    currentRunId: normalizeCompareSessionField(row.currentRunId, 128),
    assessment: normalizeCompareSessionField(row.assessment, 48),
    note: normalizeCompareSessionField(row.note, 320),
  };
}

function makeCompareReplayPairId(baselinePresetId, targetPresetId) {
  const baseline = normalizeCompareSessionField(baselinePresetId, 96);
  const target = normalizeCompareSessionField(targetPresetId, 96);
  if (!baseline || !target) return "";
  return `${baseline}::${target}`;
}

function normalizeCompareReplayPairMetaEntry(entry) {
  const row = entry && typeof entry === "object" ? entry : {};
  return {
    customLabel: normalizeCompareSessionField(row.customLabel, 160),
    pinned: row.pinned === true,
  };
}

function normalizeCompareReplayPairMetaMap(metaMap) {
  const raw = metaMap && typeof metaMap === "object" && !Array.isArray(metaMap) ? metaMap : {};
  const normalized = {};
  Object.entries(raw).forEach(([rawId, rawMeta]) => {
    const pairId = normalizeCompareSessionField(rawId, 192);
    if (!pairId) return;
    const meta = normalizeCompareReplayPairMetaEntry(rawMeta);
    if (!meta.customLabel && meta.pinned !== true) return;
    normalized[pairId] = meta;
  });
  return normalized;
}

function computeComparePathFingerprintHex(text) {
  const src = String(text || "");
  let hash = 0x811c9dc5;
  for (let idx = 0; idx < src.length; idx += 1) {
    hash ^= src.charCodeAt(idx);
    hash = Math.imul(hash, 0x01000193);
  }
  return (hash >>> 0).toString(16).padStart(8, "0");
}

function summarizeArtifactPathLabel(value) {
  const text = String(value || "").trim();
  if (!text) return "";
  const segments = text.split(/[\\/]+/).filter(Boolean);
  const base = String(segments[segments.length - 1] || "").trim();
  return normalizeCompareSessionField(base || text, 96);
}

function normalizeCompareArtifactPathFingerprintEntry(entry) {
  const row = entry && typeof entry === "object" ? entry : {};
  const currentPath = normalizeCompareSessionField(row.currentPath || row.current_path, 512);
  const comparePath = normalizeCompareSessionField(row.comparePath || row.compare_path, 512);
  return {
    currentPath,
    currentLabel: normalizeCompareSessionField(
      row.currentLabel || row.current_label || summarizeArtifactPathLabel(currentPath),
      96
    ),
    currentHash: normalizeCompareSessionField(row.currentHash || row.current_hash, 64).toLowerCase(),
    comparePath,
    compareLabel: normalizeCompareSessionField(
      row.compareLabel || row.compare_label || summarizeArtifactPathLabel(comparePath),
      96
    ),
    compareHash: normalizeCompareSessionField(row.compareHash || row.compare_hash, 64).toLowerCase(),
  };
}

function normalizeCompareArtifactPathFingerprintMap(value) {
  const raw = value && typeof value === "object" && !Array.isArray(value) ? value : {};
  const normalized = {};
  Object.entries(raw).forEach(([rawName, rawEntry]) => {
    const name = normalizeCompareSessionField(rawName, 96);
    if (!name) return;
    const entry = normalizeCompareArtifactPathFingerprintEntry(rawEntry);
    if (!entry.currentPath && !entry.comparePath && !entry.currentHash && !entry.compareHash) return;
    normalized[name] = entry;
  });
  return normalized;
}

function buildCompareArtifactPathFingerprintMap(currentSummary, compareSummary) {
  const artifactNames = [
    "path_list_json",
    "adc_cube_npz",
    "radar_map_npz",
    "graph_run_summary_json",
    "lgit_customized_output_npz",
  ];
  return artifactNames.reduce((acc, name) => {
    const currentPath = normalizeCompareSessionField(currentSummary?.outputs?.[name], 512);
    const comparePath = normalizeCompareSessionField(compareSummary?.outputs?.[name], 512);
    if (!currentPath && !comparePath) return acc;
    acc[name] = normalizeCompareArtifactPathFingerprintEntry({
      currentPath,
      currentLabel: summarizeArtifactPathLabel(currentPath),
      currentHash: currentPath ? computeComparePathFingerprintHex(currentPath) : "",
      comparePath,
      compareLabel: summarizeArtifactPathLabel(comparePath),
      compareHash: comparePath ? computeComparePathFingerprintHex(comparePath) : "",
    });
    return acc;
  }, {});
}

function countCompareArtifactPathFingerprintRows(value) {
  return Object.values(normalizeCompareArtifactPathFingerprintMap(value)).filter((row) => {
    return Boolean(row.currentHash || row.compareHash);
  }).length;
}

function buildCompareArtifactPathFingerprintDetailLines(value) {
  const rows = Object.entries(normalizeCompareArtifactPathFingerprintMap(value));
  if (rows.length === 0) {
    return [
      `artifact_path_fingerprint_algo: ${COMPARE_ARTIFACT_PATH_FINGERPRINT_ALGO}`,
      "artifact_path_fingerprints: unavailable",
    ];
  }
  return [
    `artifact_path_fingerprint_algo: ${COMPARE_ARTIFACT_PATH_FINGERPRINT_ALGO}`,
    "artifact_path_fingerprints:",
    ...rows.map(([name, row]) => (
      `- ${String(name || "-")}: current=${String(row.currentLabel || "-")}#${String(row.currentHash || "-")} compare=${String(row.compareLabel || "-")}#${String(row.compareHash || "-")}`
    )),
  ];
}

function summarizeCompareArtifactPathFingerprintCompact(value) {
  const rows = Object.entries(normalizeCompareArtifactPathFingerprintMap(value)).slice(0, 2);
  if (rows.length === 0) {
    return "path_hashes=0";
  }
  return [
    `path_hashes=${countCompareArtifactPathFingerprintRows(value)}`,
    ...rows.map(([name, row]) => `${name}:${String(row.currentHash || "-")}/${String(row.compareHash || "-")}`),
  ].join(" | ");
}

function summarizeCompareArtifactPathFingerprintStats(value) {
  const rows = Object.values(normalizeCompareArtifactPathFingerprintMap(value));
  return rows.reduce((acc, row) => {
    const currentHash = String(row?.currentHash || "").trim().toLowerCase();
    const compareHash = String(row?.compareHash || "").trim().toLowerCase();
    if (!currentHash && !compareHash) return acc;
    acc.total += 1;
    if (currentHash && compareHash && currentHash === compareHash) {
      acc.exact += 1;
      return acc;
    }
    if (!currentHash || !compareHash) {
      acc.missing += 1;
    }
    acc.delta += 1;
    return acc;
  }, {
    total: 0,
    exact: 0,
    delta: 0,
    missing: 0,
  });
}

function normalizeCompareAssessmentToken(value) {
  const token = String(value || "").trim().toLowerCase();
  if (token === "aligned" || token === "review" || token === "hold") return token;
  if (token === "planned" || token === "unavailable" || token === "unknown") return token;
  return "";
}

function toneForCompareAssessmentToken(value) {
  const token = normalizeCompareAssessmentToken(value);
  if (token === "aligned") return "status-ok";
  if (token === "review") return "status-warn";
  if (token === "hold") return "status-err";
  return "status-neutral";
}

function inferCompareArtifactExpectationAssessment(entry) {
  const row = normalizeCompareArtifactExpectationEntry(entry);
  const summaryMatch = String(row.summaryText || "").match(/(?:^|\|\s*)assessment=([a-z_]+)/i);
  const detailMatch = String(row.detailText || "").match(/observed_assessment:\s*([a-z_]+)/i);
  const token = normalizeCompareAssessmentToken(
    summaryMatch?.[1]
    || detailMatch?.[1]
    || (row.source === "planned_default" ? "planned" : "")
  );
  return token || "unknown";
}

function shortCompareArtifactExpectationSourceLabel(value) {
  const source = String(value || "").trim().toLowerCase();
  if (source === "observed_ready_pair") return "observed";
  if (source === "planned_default") return "planned";
  return source || "-";
}

function toneForCompareArtifactExpectationSource(value) {
  const source = String(value || "").trim().toLowerCase();
  if (source === "observed_ready_pair") return "status-ok";
  if (source === "planned_default" || !source) return "status-neutral";
  return "status-warn";
}

function buildPinnedCompareQuickActionBadges(entry) {
  const normalized = normalizeCompareArtifactExpectationEntry(entry);
  const assessment = inferCompareArtifactExpectationAssessment(normalized);
  const fingerprintStats = summarizeCompareArtifactPathFingerprintStats(
    normalized.artifactPathFingerprintsByArtifact
  );
  return [
    {
      label: `assessment:${assessment}`,
      tone: toneForCompareAssessmentToken(assessment),
    },
    {
      label: fingerprintStats.total > 0
        ? (
          fingerprintStats.delta === 0
            ? `fp:match:${fingerprintStats.exact}/${fingerprintStats.total}`
            : `fp:delta:${fingerprintStats.delta}/${fingerprintStats.total}`
        )
        : "fp:unseen",
      tone: fingerprintStats.total === 0
        ? "status-neutral"
        : (fingerprintStats.delta === 0 ? "status-ok" : "status-warn"),
    },
    {
      label: `source:${shortCompareArtifactExpectationSourceLabel(normalized.source)}`,
      tone: toneForCompareArtifactExpectationSource(normalized.source),
    },
  ];
}

function normalizeCompareArtifactExpectationEntry(entry) {
  const row = entry && typeof entry === "object" ? entry : {};
  return {
    source: normalizeCompareSessionField(row.source, 64),
    observedAtUtc: normalizeCompareSessionField(row.observedAtUtc || row.observed_at_utc, 64),
    summaryText: normalizeCompareSessionField(row.summaryText || row.summary_text, 640),
    detailText: normalizeCompareSessionField(row.detailText || row.detail_text, 4000),
    artifactPathFingerprintAlgo: normalizeCompareSessionField(
      row.artifactPathFingerprintAlgo || row.artifact_path_fingerprint_algo || COMPARE_ARTIFACT_PATH_FINGERPRINT_ALGO,
      64
    ),
    artifactPathFingerprintsByArtifact: normalizeCompareArtifactPathFingerprintMap(
      row.artifactPathFingerprintsByArtifact || row.artifact_path_fingerprints_by_artifact
    ),
  };
}

function normalizeCompareArtifactExpectationMap(expectationMap) {
  const raw = expectationMap && typeof expectationMap === "object" && !Array.isArray(expectationMap) ? expectationMap : {};
  const normalized = {};
  Object.entries(raw).forEach(([rawId, rawEntry]) => {
    const pairId = normalizeCompareSessionField(rawId, 192);
    if (!pairId) return;
    const entry = normalizeCompareArtifactExpectationEntry(rawEntry);
    if (!entry.summaryText && !entry.detailText) return;
    normalized[pairId] = entry;
  });
  return normalized;
}

function buildPlannedCompareArtifactExpectationEntry(pairLabel) {
  const label = normalizeCompareSessionField(pairLabel, 160) || "-";
  return normalizeCompareArtifactExpectationEntry({
    source: "planned_default",
    summaryText: "source=planned_default | required=4/4/4 | optional=lgit_customized_output_npz | artifact_delta=none expected | path_hashes=0",
    artifactPathFingerprintAlgo: COMPARE_ARTIFACT_PATH_FINGERPRINT_ALGO,
    detailText: [
      "artifact_expectation_source: planned_default",
      `pair_label: ${label}`,
      "required_artifacts: path_list_json, adc_cube_npz, radar_map_npz, graph_run_summary_json",
      "optional_artifacts: lgit_customized_output_npz",
      "artifact_presence_delta: none expected",
      `artifact_path_fingerprint_algo: ${COMPARE_ARTIFACT_PATH_FINGERPRINT_ALGO}`,
      "artifact_path_fingerprints: unavailable until pair is observed or imported",
      "note: run the preset pair once to capture an observed artifact expectation snapshot",
    ].join("\n"),
  });
}

function buildObservedCompareArtifactExpectationEntry(pairLabel, currentSummary, compareSummary) {
  const compare = buildRunCompareSummary(currentSummary, compareSummary);
  if (!compare.available) return null;
  const artifactPathFingerprintsByArtifact = buildCompareArtifactPathFingerprintMap(currentSummary, compareSummary);
  const pathFingerprintCount = countCompareArtifactPathFingerprintRows(artifactPathFingerprintsByArtifact);
  const requiredMissingCurrent = compare.artifactRows
    .filter((row) => row.required && !row.currentPresent)
    .map((row) => row.name)
    .join(",") || "none";
  const requiredMissingCompare = compare.artifactRows
    .filter((row) => row.required && !row.comparePresent)
    .map((row) => row.name)
    .join(",") || "none";
  return normalizeCompareArtifactExpectationEntry({
    source: "observed_ready_pair",
    observedAtUtc: new Date().toISOString(),
    summaryText: [
      "source=observed_ready_pair",
      `assessment=${String(compare.assessment || "-")}`,
      `required=${Number(compare.requiredArtifactCounts?.currentPresent || 0)}/${Number(compare.requiredArtifactCounts?.comparePresent || 0)}/${Number(compare.requiredArtifactCounts?.total || 0)}`,
      `artifact_delta=${String(compare.artifactPresenceDeltaText || "none")}`,
      `path_hashes=${pathFingerprintCount}`,
    ].join(" | "),
    artifactPathFingerprintAlgo: COMPARE_ARTIFACT_PATH_FINGERPRINT_ALGO,
    artifactPathFingerprintsByArtifact,
    detailText: [
      "artifact_expectation_source: observed_ready_pair",
      `pair_label: ${normalizeCompareSessionField(pairLabel, 160) || "-"}`,
      `observed_at_utc: ${new Date().toISOString()}`,
      `observed_assessment: ${String(compare.assessment || "-")}`,
      `required_artifacts(current/compare/total): ${Number(compare.requiredArtifactCounts?.currentPresent || 0)}/${Number(compare.requiredArtifactCounts?.comparePresent || 0)}/${Number(compare.requiredArtifactCounts?.total || 0)}`,
      `artifact_presence_delta: ${String(compare.artifactPresenceDeltaText || "none")}`,
      `optional_artifact_delta: ${String(compare.optionalPresenceDeltaText || "none")}`,
      `current_required_missing: ${requiredMissingCurrent}`,
      `compare_required_missing: ${requiredMissingCompare}`,
      ...buildCompareArtifactPathFingerprintDetailLines(artifactPathFingerprintsByArtifact),
      "artifact_rows:",
      ...compare.artifactRows.map((row) => (
        `- ${String(row.name || "-")}: required=${row.required === true} current=${row.currentPresent === true} compare=${row.comparePresent === true}`
      )),
    ].join("\n"),
  });
}

function parseCompareSessionTimestampMs(entry) {
  const raw = String(entry?.timestampUtc || "").trim();
  const ts = Date.parse(raw);
  return Number.isFinite(ts) ? ts : 0;
}

function sortCompareSessionHistoryEntries(entries) {
  return (Array.isArray(entries) ? entries : [])
    .map((row, idx) => normalizeCompareSessionHistoryEntry(row, idx))
    .sort((left, right) => parseCompareSessionTimestampMs(right) - parseCompareSessionTimestampMs(left));
}

function buildCompareSessionRetainedHistory(entries, pairMetaById, retentionPolicy) {
  const normalizedEntries = sortCompareSessionHistoryEntries(entries).slice(0, COMPARE_SESSION_HISTORY_LIMIT);
  const limit = Math.min(getCompareSessionRetentionLimit(retentionPolicy), COMPARE_SESSION_HISTORY_LIMIT);
  const latestEntries = normalizedEntries.slice(0, limit);
  const preserveMode = getCompareSessionRetentionPreserveMode(retentionPolicy);
  if (preserveMode === "none") {
    return latestEntries;
  }
  const normalizedMeta = normalizeCompareReplayPairMetaMap(pairMetaById);
  const preservedPairIds = new Set(
    Object.entries(normalizedMeta)
      .filter(([, meta]) => (
        preserveMode === "saved"
          ? (meta?.pinned === true || Boolean(String(meta?.customLabel || "").trim()))
          : meta?.pinned === true
      ))
      .map(([pairId]) => String(pairId || "").trim())
      .filter(Boolean)
  );
  if (preservedPairIds.size === 0) {
    return latestEntries;
  }
  const retainedEntryIds = new Set(latestEntries.map((row) => String(row?.id || "").trim()).filter(Boolean));
  const retainedPreservedPairIds = new Set(
    latestEntries
      .map((row) => String(getCompareSessionReplayPair(row)?.pairId || "").trim())
      .filter((pairId) => preservedPairIds.has(pairId))
  );
  const extraPreservedEntries = [];
  normalizedEntries.slice(limit).forEach((row) => {
    if (latestEntries.length + extraPreservedEntries.length >= COMPARE_SESSION_HISTORY_LIMIT) {
      return;
    }
    const pairId = String(getCompareSessionReplayPair(row)?.pairId || "").trim();
    const rowId = String(row?.id || "").trim();
    if (!pairId || !rowId || !preservedPairIds.has(pairId) || retainedEntryIds.has(rowId) || retainedPreservedPairIds.has(pairId)) {
      return;
    }
    retainedEntryIds.add(rowId);
    retainedPreservedPairIds.add(pairId);
    extraPreservedEntries.push(row);
  });
  return [...latestEntries, ...extraPreservedEntries];
}

function analyzeCompareSessionRetentionOutcome(entries, pairMetaById, retentionPolicy) {
  const normalizedEntries = sortCompareSessionHistoryEntries(entries).slice(0, COMPARE_SESSION_HISTORY_LIMIT);
  const retainedHistory = buildCompareSessionRetainedHistory(normalizedEntries, pairMetaById, retentionPolicy);
  const latestIds = new Set(
    normalizedEntries
      .slice(0, Math.min(getCompareSessionRetentionLimit(retentionPolicy), COMPARE_SESSION_HISTORY_LIMIT))
      .map((row) => String(row?.id || "").trim())
      .filter(Boolean)
  );
  const normalizedMeta = normalizeCompareReplayPairMetaMap(pairMetaById);
  const managedPinnedPairIds = new Set(
    Object.entries(normalizedMeta)
      .filter(([, meta]) => meta?.pinned === true)
      .map(([pairId]) => String(pairId || "").trim())
      .filter(Boolean)
  );
  const managedSavedPairIds = new Set(
    Object.entries(normalizedMeta)
      .filter(([, meta]) => meta?.pinned === true || Boolean(String(meta?.customLabel || "").trim()))
      .map(([pairId]) => String(pairId || "").trim())
      .filter(Boolean)
  );
  const retainedPairIds = new Set(
    retainedHistory
      .map((row) => String(getCompareSessionReplayPair(row)?.pairId || "").trim())
      .filter(Boolean)
  );
  return {
    availableRows: normalizedEntries.length,
    retainedRows: retainedHistory.length,
    keepLatest: getCompareSessionRetentionLimit(retentionPolicy),
    preserveScope: getCompareSessionRetentionPreserveMode(retentionPolicy),
    preservePinned: shouldCompareSessionRetentionPreservePinned(retentionPolicy),
    preserveSaved: shouldCompareSessionRetentionPreserveSaved(retentionPolicy),
    pinnedPairsManaged: managedPinnedPairIds.size,
    pinnedPairsRetained: Array.from(managedPinnedPairIds).filter((pairId) => retainedPairIds.has(pairId)).length,
    extraPinnedRowsRetained: retainedHistory.filter((row) => !latestIds.has(String(row?.id || "").trim())).length,
    savedPairsManaged: managedSavedPairIds.size,
    savedPairsRetained: Array.from(managedSavedPairIds).filter((pairId) => retainedPairIds.has(pairId)).length,
    extraSavedRowsRetained: retainedHistory
      .filter((row) => !latestIds.has(String(row?.id || "").trim()))
      .filter((row) => managedSavedPairIds.has(String(getCompareSessionReplayPair(row)?.pairId || "").trim()))
      .length,
  };
}

function summarizeCompareSessionRetentionRowLabel(row, pairMetaById) {
  const replayPair = applyCompareReplayPairMeta(getCompareSessionReplayPair(row), pairMetaById);
  return normalizeCompareSessionField(
    replayPair?.pairLabel
    || row?.pairLabel
    || `${String(row?.baselinePresetId || "-")} -> ${String(row?.targetPresetId || "-")}`,
    160
  ) || "-";
}

function collectCompareSessionRetentionPreview(entries, pairMetaById, retentionPolicy) {
  const normalizedEntries = sortCompareSessionHistoryEntries(entries).slice(0, COMPARE_SESSION_HISTORY_LIMIT);
  const keepLatest = Math.min(getCompareSessionRetentionLimit(retentionPolicy), COMPARE_SESSION_HISTORY_LIMIT);
  const latestEntries = normalizedEntries.slice(0, keepLatest);
  const retainedHistory = buildCompareSessionRetainedHistory(normalizedEntries, pairMetaById, retentionPolicy);
  const latestIds = new Set(latestEntries.map((row) => String(row?.id || "").trim()).filter(Boolean));
  const retainedIds = new Set(retainedHistory.map((row) => String(row?.id || "").trim()).filter(Boolean));
  const extraEntries = retainedHistory.filter((row) => !latestIds.has(String(row?.id || "").trim()));
  const droppedEntries = normalizedEntries.filter((row) => !retainedIds.has(String(row?.id || "").trim()));
  const mapLabels = (rows) => Array.from(new Set(
    (Array.isArray(rows) ? rows : [])
      .map((row) => summarizeCompareSessionRetentionRowLabel(row, pairMetaById))
      .filter(Boolean)
  ));
  return {
    keepLatest,
    latestPairLabels: mapLabels(latestEntries),
    extraPairLabels: mapLabels(extraEntries),
    droppedPairLabels: mapLabels(droppedEntries),
    visibleRowCount: normalizedEntries.length,
    retainedRowCount: retainedHistory.length,
  };
}

function buildCompareSessionRetentionPreviewText(entries, pairMetaById, retentionPolicy, prefix = "retention_pairs") {
  const preview = collectCompareSessionRetentionPreview(entries, pairMetaById, retentionPolicy);
  const latestLabels = preview.latestPairLabels.length > 0 ? preview.latestPairLabels.join(" | ") : "-";
  const extraLabels = preview.extraPairLabels.length > 0 ? preview.extraPairLabels.join(" | ") : "-";
  const droppedLabels = preview.droppedPairLabels.length > 0 ? preview.droppedPairLabels.join(" | ") : "-";
  const label = String(prefix || "").includes("(")
    ? String(prefix || "retention_pairs")
    : `${String(prefix || "retention_pairs")}(latest/extra/dropped)`;
  return [
    `${label}: ${latestLabels} / ${extraLabels} / ${droppedLabels}`,
    `retention_rows(visible/retained): ${Number(preview.visibleRowCount || 0)}/${Number(preview.retainedRowCount || 0)}`,
  ].join("\n");
}

function analyzeCompareSessionSelectedPairRetention(entries, pairMetaById, retentionPolicy, replayPair) {
  const pair = replayPair && typeof replayPair === "object" ? replayPair : null;
  const pairId = normalizeCompareSessionField(
    pair?.id
    || pair?.pairId
    || makeCompareReplayPairId(pair?.baselinePresetId, pair?.targetPresetId),
    192
  );
  const pairLabel = normalizeCompareSessionField(pair?.pairLabel || pair?.label, 160) || "-";
  if (!pairId) {
    return {
      pairId: "",
      pairLabel: "-",
      state: "none",
      pinned: false,
      saved: false,
      visibleRows: 0,
      latestRows: 0,
      retainedRows: 0,
      keepLatest: Math.min(getCompareSessionRetentionLimit(retentionPolicy), COMPARE_SESSION_HISTORY_LIMIT),
      retentionPolicy: normalizeCompareSessionRetentionPolicy(
        retentionPolicy,
        COMPARE_SESSION_RETENTION_POLICY_DEFAULT
      ),
    };
  }
  const normalizedEntries = sortCompareSessionHistoryEntries(entries).slice(0, COMPARE_SESSION_HISTORY_LIMIT);
  const keepLatest = Math.min(getCompareSessionRetentionLimit(retentionPolicy), COMPARE_SESSION_HISTORY_LIMIT);
  const latestEntries = normalizedEntries.slice(0, keepLatest);
  const retainedHistory = buildCompareSessionRetainedHistory(normalizedEntries, pairMetaById, retentionPolicy);
  const byPairId = (rows) => (Array.isArray(rows) ? rows : []).filter(
    (row) => String(getCompareSessionReplayPair(row)?.pairId || "").trim() === pairId
  );
  const meta = normalizeCompareReplayPairMetaEntry(pairMetaById?.[pairId] || pair || {});
  const visibleRows = byPairId(normalizedEntries).length;
  const latestRows = byPairId(latestEntries).length;
  const retainedRows = byPairId(retainedHistory).length;
  const state = retainedRows > 0
    ? (latestRows > 0 ? "latest_window" : "retained_extra")
    : visibleRows > 0
      ? "dropped"
      : "missing";
  return {
    pairId,
    pairLabel,
    state,
    pinned: meta.pinned === true,
    saved: Boolean(String(meta.customLabel || "").trim()),
    visibleRows,
    latestRows,
    retainedRows,
    keepLatest,
    retentionPolicy: normalizeCompareSessionRetentionPolicy(
      retentionPolicy,
      COMPARE_SESSION_RETENTION_POLICY_DEFAULT
    ),
  };
}

function buildCompareSessionSelectedPairRetentionText(entries, pairMetaById, retentionPolicy, replayPair) {
  const summary = analyzeCompareSessionSelectedPairRetention(entries, pairMetaById, retentionPolicy, replayPair);
  if (!summary.pairId) {
    return [
      "selected_history_pair_retention: -",
      `retention_window: keep_latest=${Number(summary.keepLatest || 0)} | policy=${String(summary.retentionPolicy || "-")}`,
    ].join("\n");
  }
  return [
    `selected_history_pair_retention: state=${String(summary.state || "-")} | managed=pinned=${summary.pinned === true},saved=${summary.saved === true} | rows(visible/latest/retained)=${Number(summary.visibleRows || 0)}/${Number(summary.latestRows || 0)}/${Number(summary.retainedRows || 0)}`,
    `retention_window: keep_latest=${Number(summary.keepLatest || 0)} | policy=${String(summary.retentionPolicy || "-")} | pair=${String(summary.pairLabel || "-")}`,
  ].join("\n");
}

function mergeCompareSessionHistoryEntries(existingEntries, importedEntries) {
  const existing = Array.isArray(existingEntries) ? existingEntries : [];
  const incoming = Array.isArray(importedEntries) ? importedEntries : [];
  const byId = new Map();
  [...existing, ...incoming].forEach((row, idx) => {
    const normalized = normalizeCompareSessionHistoryEntry(row, idx);
    const key = String(normalized.id || `cmp_merge_${idx}`).trim();
    if (!key) return;
    const prior = byId.get(key);
    if (!prior || parseCompareSessionTimestampMs(normalized) >= parseCompareSessionTimestampMs(prior)) {
      byId.set(key, normalized);
    }
  });
  return Array.from(byId.values())
    .sort((left, right) => parseCompareSessionTimestampMs(right) - parseCompareSessionTimestampMs(left))
    .slice(0, COMPARE_SESSION_HISTORY_LIMIT);
}

function collectCompareSessionReplayPairIds(entries) {
  return Array.from(new Set(
    (Array.isArray(entries) ? entries : [])
      .map((row) => String(getCompareSessionReplayPair(row)?.pairId || "").trim())
      .filter(Boolean)
  ));
}

function buildCompareSessionRetainedState(stateInput) {
  const row = stateInput && typeof stateInput === "object" ? stateInput : {};
  const retentionPolicy = normalizeCompareSessionRetentionPolicy(
    row.retentionPolicy,
    COMPARE_SESSION_RETENTION_POLICY_DEFAULT
  );
  const normalizedPairMetaById = normalizeCompareReplayPairMetaMap(row.pairMetaById);
  const history = buildCompareSessionRetainedHistory(
    Array.isArray(row.history) ? row.history : [],
    normalizedPairMetaById,
    retentionPolicy
  );
  const activePairIds = new Set(collectCompareSessionReplayPairIds(history));
  const pairMetaById = {};
  Object.entries(normalizedPairMetaById).forEach(([pairId, meta]) => {
    if (activePairIds.has(pairId)) {
      pairMetaById[pairId] = meta;
    }
  });
  const pairArtifactExpectationById = {};
  Object.entries(normalizeCompareArtifactExpectationMap(row.pairArtifactExpectationById)).forEach(([pairId, entry]) => {
    if (activePairIds.has(pairId)) {
      pairArtifactExpectationById[pairId] = entry;
    }
  });
  const firstReplayPairId = collectCompareSessionReplayPairIds(history)[0] || "";
  const selectedReplayPairIdRaw = normalizeCompareSessionField(row.selectedReplayPairId, 192);
  const selectedReplayPairId = activePairIds.has(selectedReplayPairIdRaw)
    ? selectedReplayPairIdRaw
    : firstReplayPairId;
  return {
    retentionPolicy,
    history,
    pairMetaById,
    pairArtifactExpectationById,
    selectedReplayPairId,
  };
}

function normalizeCompareSessionImportSchemaVersion(value) {
  const raw = normalizeCompareSessionField(value, 96);
  if (!raw) return COMPARE_SESSION_IMPORT_SCHEMA_LEGACY;
  return raw;
}

function summarizeCompareSessionSchemaCompatibility(value) {
  const schemaVersion = normalizeCompareSessionImportSchemaVersion(value);
  if (schemaVersion === COMPARE_SESSION_EXPORT_SCHEMA_VERSION) {
    return {
      schemaVersion,
      compatibility: "exact",
    };
  }
  if (schemaVersion === COMPARE_SESSION_IMPORT_SCHEMA_LEGACY) {
    return {
      schemaVersion,
      compatibility: "legacy_compatible",
    };
  }
  return {
    schemaVersion,
    compatibility: "forward_compatible_best_effort",
  };
}

function toneForCompareSessionSchemaCompatibility(value) {
  const token = String(value || "").trim().toLowerCase();
  if (token === "exact") return "status-ok";
  if (token === "legacy_compatible") return "status-neutral";
  if (token === "forward_compatible_best_effort") return "status-warn";
  return "status-neutral";
}

function buildCompareSessionTransferBadges(entry) {
  const row = entry && typeof entry === "object" ? entry : {};
  const direction = normalizeCompareSessionField(row.direction, 32) || "idle";
  const schemaVersion = normalizeCompareSessionImportSchemaVersion(row.schemaVersion);
  const compatibility = normalizeCompareSessionField(row.compatibility, 64) || "";
  const failed = row.failed === true;
  const badges = [];
  badges.push({
    label: `transfer:${direction}`,
    tone: failed === true
      ? "status-err"
      : direction === "import" || direction === "export"
        ? "status-ok"
        : "status-neutral",
  });
  if (schemaVersion && schemaVersion !== COMPARE_SESSION_IMPORT_SCHEMA_LEGACY) {
    badges.push({
      label: `schema:${schemaVersion}`,
      tone: "status-neutral",
    });
  }
  if (compatibility) {
    badges.push({
      label: `compat:${compatibility}`,
      tone: toneForCompareSessionSchemaCompatibility(compatibility),
    });
  }
  if (compatibility === "forward_compatible_best_effort") {
    badges.push({
      label: "warning:future-schema",
      tone: "status-warn",
    });
  }
  if (failed === true) {
    badges.push({
      label: "warning:transfer-failed",
      tone: "status-err",
    });
  }
  return badges;
}

function summarizeCompareSessionTransferBadgeLabels(badgeRows) {
  const rows = Array.isArray(badgeRows) ? badgeRows : [];
  const labels = rows
    .map((row) => String(row?.label || "").trim())
    .filter(Boolean);
  return labels.length > 0 ? labels.join(" | ") : "transfer:idle";
}

function normalizeArtifactInspectorStatusSummary(value) {
  const row = value && typeof value === "object" ? value : {};
  return {
    layoutStateText: normalizeCompareSessionField(row.layoutStateText, 320) || "layout_state: -",
    probeStateText: normalizeCompareSessionField(row.probeStateText, 320) || "probe_state: -",
    statusBadgesText: normalizeCompareSessionField(row.statusBadgesText, 320) || "status_badges: -",
  };
}

function toneForArtifactInspectorStatusBadge(label) {
  const text = String(label || "").trim().toLowerCase();
  if (text.startsWith("layout:")) {
    return text.endsWith("default") ? "status-ok" : "status-warn";
  }
  if (text.startsWith("probe:")) {
    return text.endsWith("default") ? "status-ok" : "status-warn";
  }
  if (text.startsWith("reset:")) {
    return text.endsWith("clean") ? "status-ok" : "status-warn";
  }
  return "status-neutral";
}

function buildArtifactInspectorStatusBadgeRows(rawText) {
  const text = String(rawText || "").trim();
  const suffix = text.startsWith("status_badges:")
    ? text.slice("status_badges:".length)
    : text;
  return suffix
    .split("|")
    .map((part) => String(part || "").trim())
    .filter(Boolean)
    .filter((part) => part !== "-")
    .map((label) => ({
      label,
      tone: toneForArtifactInspectorStatusBadge(label),
    }));
}

function buildArtifactInspectorDecisionLine(rawText, panelPrefix, decisionPrefix) {
  const text = String(rawText || "").trim();
  if (!text) return `${decisionPrefix}: -`;
  if (text.startsWith(`${panelPrefix}:`)) {
    return `${decisionPrefix}:${text.slice(panelPrefix.length + 1)}`;
  }
  return `${decisionPrefix}: ${text}`;
}

function buildCompareSessionImportPreviewSummary(
  stagedEntry,
  existingHistoryEntries,
  existingPairMetaById,
  existingArtifactExpectationById,
  currentRetentionPolicy
) {
  const staged = stagedEntry && typeof stagedEntry === "object" ? stagedEntry : null;
  if (!staged || !staged.imported || typeof staged.imported !== "object") {
    return {
      ready: false,
      summaryText: "import_preview: none",
      previewText: [
        "import_preview_source: -",
        "schema_version: -",
        "schema_compatibility: -",
        `retention_policy(current/imported/effective): ${normalizeCompareSessionRetentionPolicy(currentRetentionPolicy, COMPARE_SESSION_RETENTION_POLICY_DEFAULT)}/-/-`,
        "retention_effect(available/retained/pinned_pairs/extra_pinned_rows): 0/0/0/0",
        "retention_pairs(merged_latest/merged_extra/merged_dropped): - / - / -",
        "history_merge(existing/imported/new/overlap/merged): 0/0/0/0/0",
        "pair_meta(existing/imported/merged): 0/0/0",
        "artifact_expectations(existing/imported/merged): 0/0/0",
        "selected_replay_pair(import): -",
        "selected_replay_pair_after_merge: unchanged",
        "selected_replay_pair_retention_after_merge: unchanged",
        "import_pair_labels: -",
        "apply_note: choose Import History to stage a bundle before merge",
      ].join("\n"),
    };
  }

  const sourceLabel = normalizeCompareSessionField(staged.sourceLabel, 192) || "compare_history.json";
  const imported = staged.imported;
  const importSchema = summarizeCompareSessionSchemaCompatibility(imported.schemaVersion);
  const effectiveRetentionPolicy = normalizeCompareSessionRetentionPolicy(
    imported.retentionPolicy || currentRetentionPolicy,
    COMPARE_SESSION_RETENTION_POLICY_DEFAULT
  );
  const importedRetentionPolicy = normalizeCompareSessionRetentionPolicy(imported.retentionPolicy, "");
  const existingHistory = (Array.isArray(existingHistoryEntries) ? existingHistoryEntries : [])
    .map((row, idx) => normalizeCompareSessionHistoryEntry(row, idx));
  const importedHistory = (Array.isArray(imported.history) ? imported.history : [])
    .map((row, idx) => normalizeCompareSessionHistoryEntry(row, idx));
  const existingHistoryIds = new Set(existingHistory.map((row) => String(row.id || "").trim()).filter(Boolean));
  const importedHistoryIds = Array.from(new Set(importedHistory.map((row) => String(row.id || "").trim()).filter(Boolean)));
  const newHistoryCount = importedHistoryIds.filter((id) => !existingHistoryIds.has(id)).length;
  const overlapHistoryCount = importedHistoryIds.filter((id) => existingHistoryIds.has(id)).length;
  const mergedHistory = mergeCompareSessionHistoryEntries(existingHistory, importedHistory);

  const existingPairMeta = normalizeCompareReplayPairMetaMap(existingPairMetaById);
  const importedPairMeta = normalizeCompareReplayPairMetaMap(imported.pairMetaById);
  const mergedPairMeta = {
    ...existingPairMeta,
    ...importedPairMeta,
  };

  const existingArtifactExpectation = normalizeCompareArtifactExpectationMap(existingArtifactExpectationById);
  const importedArtifactExpectation = normalizeCompareArtifactExpectationMap(imported.pairArtifactExpectationById);
  const mergedArtifactExpectation = {
    ...existingArtifactExpectation,
    ...importedArtifactExpectation,
  };
  const mergedState = buildCompareSessionRetainedState({
    history: mergedHistory,
    pairMetaById: mergedPairMeta,
    pairArtifactExpectationById: mergedArtifactExpectation,
    selectedReplayPairId: normalizeCompareSessionField(imported.selectedReplayPairId, 192),
    retentionPolicy: effectiveRetentionPolicy,
  });
  const retentionOutcome = analyzeCompareSessionRetentionOutcome(
    mergedHistory,
    mergedPairMeta,
    effectiveRetentionPolicy
  );
  const retentionPreviewText = buildCompareSessionRetentionPreviewText(
    mergedHistory,
    mergedPairMeta,
    effectiveRetentionPolicy,
    "retention_pairs(merged_latest/merged_extra/merged_dropped)"
  );
  const selectedReplayPairId = normalizeCompareSessionField(imported.selectedReplayPairId, 192);
  const mergedReplayOptions = buildCompareSessionReplayOptions(
    mergedState.history,
    mergedState.pairMetaById,
    effectiveRetentionPolicy
  );
  const selectedReplayPairAvailable = selectedReplayPairId
    ? mergedReplayOptions.some((row) => String(row?.id || "") === selectedReplayPairId)
    : false;
  const selectedReplayPairSource = selectedReplayPairId
    ? mergedHistory.find((row) => String(getCompareSessionReplayPair(row)?.pairId || "").trim() === selectedReplayPairId)
    : null;
  const selectedReplayPairRetentionSummary = selectedReplayPairId
    ? analyzeCompareSessionSelectedPairRetention(
      mergedHistory,
      mergedPairMeta,
      effectiveRetentionPolicy,
      selectedReplayPairSource
        ? applyCompareReplayPairMeta(getCompareSessionReplayPair(selectedReplayPairSource), mergedPairMeta)
        : { id: selectedReplayPairId, pairId: selectedReplayPairId, pairLabel: selectedReplayPairId }
    )
    : null;
  const importedPairLabels = Array.from(new Set(importedHistory.map((row) => String(row.pairLabel || "").trim()).filter(Boolean)));

  return {
    ready: true,
    summaryText: [
      `import_preview: ready`,
      `source=${sourceLabel}`,
      `schema=${importSchema.schemaVersion}`,
      `compatibility=${importSchema.compatibility}`,
      `rows=${Number(importedHistory.length || 0)}`,
      `retention=${effectiveRetentionPolicy}`,
      `selected_pair_retention=${selectedReplayPairId
        ? `${String(selectedReplayPairRetentionSummary?.state || "missing")}(${Number(selectedReplayPairRetentionSummary?.visibleRows || 0)}/${Number(selectedReplayPairRetentionSummary?.latestRows || 0)}/${Number(selectedReplayPairRetentionSummary?.retainedRows || 0)})`
        : "unchanged"}`,
      "apply_required=true",
    ].join(" | "),
    previewText: [
      `import_preview_source: ${sourceLabel}`,
      `schema_version: ${importSchema.schemaVersion}`,
      `schema_compatibility: ${importSchema.compatibility}`,
      `retention_policy(current/imported/effective): ${normalizeCompareSessionRetentionPolicy(currentRetentionPolicy, COMPARE_SESSION_RETENTION_POLICY_DEFAULT)}/${importedRetentionPolicy || "unchanged"}/${effectiveRetentionPolicy}`,
      `retention_effect(available/retained/pinned_pairs/extra_pinned_rows): ${Number(retentionOutcome.availableRows || 0)}/${Number(retentionOutcome.retainedRows || 0)}/${Number(retentionOutcome.pinnedPairsRetained || 0)}/${Number(retentionOutcome.extraPinnedRowsRetained || 0)}`,
      retentionPreviewText,
      `history_merge(existing/imported/new/overlap/merged): ${Number(existingHistory.length || 0)}/${Number(importedHistory.length || 0)}/${Number(newHistoryCount || 0)}/${Number(overlapHistoryCount || 0)}/${Number(mergedState.history.length || 0)}`,
      `pair_meta(existing/imported/merged): ${Number(Object.keys(existingPairMeta).length || 0)}/${Number(Object.keys(importedPairMeta).length || 0)}/${Number(Object.keys(mergedPairMeta).length || 0)}`,
      `artifact_expectations(existing/imported/merged): ${Number(Object.keys(existingArtifactExpectation).length || 0)}/${Number(Object.keys(importedArtifactExpectation).length || 0)}/${Number(Object.keys(mergedArtifactExpectation).length || 0)}`,
      `selected_replay_pair(import): ${selectedReplayPairId || "-"}`,
      `selected_replay_pair_after_merge: ${selectedReplayPairId ? (selectedReplayPairAvailable ? "available" : "missing") : "unchanged"}`,
      `selected_replay_pair_retention_after_merge: ${selectedReplayPairId
        ? `state=${String(selectedReplayPairRetentionSummary?.state || "missing")} | rows(visible/latest/retained)=${Number(selectedReplayPairRetentionSummary?.visibleRows || 0)}/${Number(selectedReplayPairRetentionSummary?.latestRows || 0)}/${Number(selectedReplayPairRetentionSummary?.retainedRows || 0)}`
        : "unchanged"}`,
      `import_pair_labels: ${importedPairLabels.length > 0 ? importedPairLabels.join(" | ") : "-"}`,
      importSchema.compatibility === "forward_compatible_best_effort"
        ? "warning: future schema will be parsed with best-effort compatibility"
        : "warning: none",
      "apply_note: preview only; click Apply Import Merge to persist",
    ].join("\n"),
  };
}

function serializeCompareSessionExportBundle(bundle) {
  const row = bundle && typeof bundle === "object" ? bundle : {};
  const retentionPolicy = normalizeCompareSessionRetentionPolicy(
    row.retentionPolicy,
    COMPARE_SESSION_RETENTION_POLICY_DEFAULT
  );
  return JSON.stringify({
    schema_version: COMPARE_SESSION_EXPORT_SCHEMA_VERSION,
    exported_at_utc: new Date().toISOString(),
    retention_policy: retentionPolicy,
    history: (Array.isArray(row.history) ? row.history : [])
      .map((item, idx) => normalizeCompareSessionHistoryEntry(item, idx))
      .slice(0, COMPARE_SESSION_HISTORY_LIMIT),
    pair_meta_by_id: normalizeCompareReplayPairMetaMap(row.pairMetaById),
    pair_artifact_expectation_by_id: normalizeCompareArtifactExpectationMap(row.pairArtifactExpectationById),
    selected_replay_pair_id: normalizeCompareSessionField(row.selectedReplayPairId, 192),
  }, null, 2);
}

function parseCompareSessionImportBundle(text) {
  const parsed = JSON.parse(String(text || ""));
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new Error("compare history import must be a JSON object");
  }
  return {
    schemaVersion: normalizeCompareSessionImportSchemaVersion(parsed.schema_version || parsed.schemaVersion),
    retentionPolicy: normalizeCompareSessionRetentionPolicy(
      parsed.retention_policy || parsed.retentionPolicy,
      ""
    ),
    history: (Array.isArray(parsed.history) ? parsed.history : [])
      .map((row, idx) => normalizeCompareSessionHistoryEntry(row, idx))
      .slice(0, COMPARE_SESSION_HISTORY_LIMIT),
    pairMetaById: normalizeCompareReplayPairMetaMap(parsed.pair_meta_by_id || parsed.pairMetaById),
    pairArtifactExpectationById: normalizeCompareArtifactExpectationMap(
      parsed.pair_artifact_expectation_by_id || parsed.pairArtifactExpectationById
    ),
    selectedReplayPairId: normalizeCompareSessionField(
      parsed.selected_replay_pair_id || parsed.selectedReplayPairId,
      192
    ),
  };
}

function loadCompareSessionPrefs() {
  try {
    if (typeof window === "undefined" || !window.localStorage) {
      return buildCompareSessionRetainedState({
        history: [],
        selectedReplayPairId: "",
        pairMetaById: {},
        pairArtifactExpectationById: {},
        retentionPolicy: COMPARE_SESSION_RETENTION_POLICY_DEFAULT,
      });
    }
    const raw = String(window.localStorage.getItem(COMPARE_SESSION_STORAGE_KEY) || "").trim();
    if (!raw) {
      return buildCompareSessionRetainedState({
        history: [],
        selectedReplayPairId: "",
        pairMetaById: {},
        pairArtifactExpectationById: {},
        retentionPolicy: COMPARE_SESSION_RETENTION_POLICY_DEFAULT,
      });
    }
    const parsed = JSON.parse(raw);
    return buildCompareSessionRetainedState({
      history: parsed?.history,
      selectedReplayPairId: parsed?.selectedReplayPairId,
      pairMetaById: parsed?.pairMetaById,
      pairArtifactExpectationById: parsed?.pairArtifactExpectationById,
      retentionPolicy: parsed?.retentionPolicy,
    });
  } catch (_) {
    return buildCompareSessionRetainedState({
      history: [],
      selectedReplayPairId: "",
      pairMetaById: {},
      pairArtifactExpectationById: {},
      retentionPolicy: COMPARE_SESSION_RETENTION_POLICY_DEFAULT,
    });
  }
}

function saveCompareSessionPrefs(prefs) {
  try {
    if (typeof window === "undefined" || !window.localStorage) return;
    const payload = buildCompareSessionRetainedState(prefs);
    window.localStorage.setItem(
      COMPARE_SESSION_STORAGE_KEY,
      JSON.stringify({
        history: payload.history,
        selectedReplayPairId: payload.selectedReplayPairId,
        pairMetaById: payload.pairMetaById,
        pairArtifactExpectationById: payload.pairArtifactExpectationById,
        retentionPolicy: payload.retentionPolicy,
      })
    );
  } catch (_) {
    // localStorage may be blocked; ignore and continue with in-memory state
  }
}

function summarizeRuntimeTrack(summary, fallbackConfig) {
  const summaryObj = summary && typeof summary === "object" ? summary : {};
  const fallback = fallbackConfig && typeof fallbackConfig === "object" ? fallbackConfig : {};
  const meta = summaryObj?.radar_map_summary?.metadata && typeof summaryObj.radar_map_summary.metadata === "object"
    ? summaryObj.radar_map_summary.metadata
    : {};
  const runtimeResolution = meta?.runtime_resolution && typeof meta.runtime_resolution === "object"
    ? meta.runtime_resolution
    : {};
  const antennaSummary = meta?.antenna_summary && typeof meta.antenna_summary === "object"
    ? meta.antenna_summary
    : {};
  const providerInfo = runtimeResolution?.provider_runtime_info && typeof runtimeResolution.provider_runtime_info === "object"
    ? runtimeResolution.provider_runtime_info
    : {};

  const backendTypeObserved = String(meta?.backend_type || fallback.backendType || "").trim();
  const runtimeModeObserved = String(runtimeResolution?.mode || fallback.runtimeMode || "").trim();
  const simulationBackendObserved = String(
    providerInfo?.simulation_backend || providerInfo?.generator || fallback.simulationBackend || ""
  ).trim();
  const multiplexingObserved = String(
    providerInfo?.multiplexing_mode || fallback.multiplexingMode || ""
  ).trim();
  const licenseObserved = String(
    providerInfo?.license_file || providerInfo?.license_file_hint || fallback.licenseObserved || ""
  ).trim();
  const antennaModeObserved = String(antennaSummary?.antenna_mode || fallback.antennaMode || "").trim();
  const licenseStatus = licenseObserved ? "set" : String(fallback.licenseStatus || "none").trim();
  const graphRunId = String(summaryObj?.graph_run_id || summaryObj?.run_id || "").trim();
  const runtimeStatusLine = [
    `backend=${backendTypeObserved || "-"}`,
    `mode=${runtimeModeObserved || "-"}`,
    `sim=${simulationBackendObserved || "-"}`,
    `mux=${multiplexingObserved || "-"}`,
    `ant=${antennaModeObserved || "-"}`,
    `license=${licenseStatus || "-"}`,
  ].join(" | ");
  const trackLabel = [
    `backend=${backendTypeObserved || "-"}`,
    `sim=${simulationBackendObserved || runtimeModeObserved || "-"}`,
    `mux=${multiplexingObserved || "-"}`,
    `ant=${antennaModeObserved || "-"}`,
    `license=${licenseStatus || "-"}`,
  ].join(" | ");

  return {
    backendTypeObserved,
    runtimeModeObserved,
    simulationBackendObserved,
    multiplexingObserved,
    antennaModeObserved,
    licenseObserved,
    licenseStatus,
    graphRunId,
    runtimeStatusLine,
    trackLabel,
  };
}

function shortAdcSource(value) {
  const text = String(value || "").trim();
  if (!text) return "-";
  if (text === "runtime_payload_adc_sctr") return "runtime";
  if (text.startsWith("synth_")) return "synth";
  return text;
}

function deriveTrackCompareRunnerStatus(statusText) {
  const text = String(statusText || "").trim();
  if (!text || text === "-") return "not_run";
  if (text.includes("track_compare_runner=ready")) return "ready";
  if (text.includes("track_compare_runner_blocked")) return "blocked";
  if (text.includes("track_compare_runner_failed")) return "failed";
  if (text.includes("phase=")) return "running";
  return "manual_or_other";
}

function summarizeRuntimeDiagnostics(summary, fallbackConfig) {
  const summaryObj = summary && typeof summary === "object" ? summary : {};
  const fallback = fallbackConfig && typeof fallbackConfig === "object" ? fallbackConfig : {};
  const meta = summaryObj?.radar_map_summary?.metadata && typeof summaryObj.radar_map_summary.metadata === "object"
    ? summaryObj.radar_map_summary.metadata
    : {};
  const runtimeResolution = meta?.runtime_resolution && typeof meta.runtime_resolution === "object"
    ? meta.runtime_resolution
    : {};
  const providerInfo = runtimeResolution?.provider_runtime_info && typeof runtimeResolution.provider_runtime_info === "object"
    ? runtimeResolution.provider_runtime_info
    : {};
  const runtimeInfo = runtimeResolution?.runtime_info && typeof runtimeResolution.runtime_info === "object"
    ? runtimeResolution.runtime_info
    : {};
  const moduleReport = runtimeInfo?.module_report && typeof runtimeInfo.module_report === "object"
    ? runtimeInfo.module_report
    : {};
  const configuredModules = Array.isArray(fallback.requiredModules) ? fallback.requiredModules : [];
  const moduleNames = Object.keys(moduleReport);
  const effectiveModules = moduleNames.length > 0 ? moduleNames : configuredModules;
  const moduleRows = effectiveModules.map((name) => {
    const row = moduleReport?.[name] && typeof moduleReport[name] === "object" ? moduleReport[name] : {};
    const available = typeof row.available === "boolean" ? Boolean(row.available) : null;
    return {
      name: String(name || "").trim(),
      available,
      version: String(row.module_version || row.version || "").trim(),
      error: String(row.error || "").trim(),
    };
  });
  const availableCount = moduleRows.filter((row) => row.available === true).length;
  const missingCount = moduleRows.filter((row) => row.available === false).length;
  const graphRunId = String(summaryObj?.graph_run_id || summaryObj?.run_id || "").trim();
  const providerSpec = String(
    runtimeResolution?.runtime_provider || runtimeInfo?.provider_spec || fallback.providerSpec || ""
  ).trim();
  const runtimeMode = String(runtimeResolution?.mode || fallback.runtimeMode || "").trim();
  const backendType = String(meta?.backend_type || fallback.backendType || "").trim();
  const simulationUsed = typeof providerInfo?.simulation_used === "boolean" ? Boolean(providerInfo.simulation_used) : null;
  const simulationLabel = simulationUsed === true
    ? "adc"
    : simulationUsed === false
      ? "path"
      : String(fallback.simulationMode || fallback.simulationBackend || "-").trim() || "-";
  const adcSource = String(runtimeResolution?.adc_source || "").trim();
  const runtimeError = String(runtimeResolution?.runtime_error || providerInfo?.simulation_error || "").trim();
  const licenseSource = String(
    providerInfo?.license_source
      || (providerInfo?.license_file ? "env" : "")
      || fallback.licenseSource
      || (fallback.licenseFile ? "runtime_input" : "")
      || fallback.licenseStatus
      || ""
  ).trim();

  let overallStatus = "idle";
  if (runtimeError) {
    overallStatus = "error";
  } else if (missingCount > 0) {
    overallStatus = "blocked";
  } else if (graphRunId || adcSource || simulationUsed !== null || moduleNames.length > 0) {
    overallStatus = "ready";
  } else if (providerSpec || backendType || effectiveModules.length > 0) {
    overallStatus = "planned";
  }

  const badges = [
    {
      label: `state:${overallStatus}`,
      tone: overallStatus === "ready"
        ? "status-ok"
        : (overallStatus === "blocked" || overallStatus === "error")
          ? "status-warn"
          : "status-neutral",
    },
  ];
  if (effectiveModules.length > 0) {
    badges.push({
      label: moduleNames.length > 0
        ? `modules:${availableCount}/${effectiveModules.length}`
        : `modules:planned:${effectiveModules.length}`,
      tone: moduleNames.length > 0
        ? (missingCount > 0 ? "status-warn" : "status-ok")
        : "status-neutral",
    });
  }
  if (simulationLabel && simulationLabel !== "-") {
    badges.push({
      label: `sim:${simulationLabel}`,
      tone: simulationUsed === true ? "status-ok" : "status-neutral",
    });
  }
  if (adcSource) {
    badges.push({
      label: `adc:${shortAdcSource(adcSource)}`,
      tone: shortAdcSource(adcSource) === "runtime" ? "status-ok" : "status-neutral",
    });
  }
  if (licenseSource) {
    badges.push({
      label: `license:${licenseSource}`,
      tone: licenseSource === "none" ? "status-neutral" : "status-ok",
    });
  }

  const moduleLines = moduleRows.length > 0
    ? moduleRows.map((row) => {
      if (row.available === true) {
        return `- ${row.name}: ok${row.version ? ` @${row.version}` : ""}`;
      }
      if (row.available === false) {
        return `- ${row.name}: missing${row.error ? ` | ${row.error}` : ""}`;
      }
      return `- ${row.name}: planned`;
    })
    : ["- none"];
  const summaryText = [
    `state: ${overallStatus}`,
    `backend: ${backendType || "-"}`,
    `provider: ${providerSpec || "-"}`,
    `mode: ${runtimeMode || "-"}`,
    `simulation_used: ${simulationUsed === null ? "-" : String(simulationUsed)}`,
    `adc_source: ${adcSource || "-"}`,
    `license_source: ${licenseSource || "-"}`,
    "module_report:",
    ...moduleLines,
    `runtime_error: ${runtimeError || "-"}`,
  ].join("\n");

  return {
    overallStatus,
    providerSpec,
    runtimeMode,
    simulationUsed,
    adcSource,
    licenseSource,
    badges,
    badgeLine: badges.map((row) => String(row.label || "").trim()).filter(Boolean).join(" | ") || "-",
    summaryText,
  };
}

function buildRuntimeDiagnosticsFallbackFromOverrides(overrides) {
  const row = overrides && typeof overrides === "object" ? overrides : {};
  const requiredModules = splitTokenList(row.runtimeRequiredModulesText || "");
  const licenseFile = String(row.runtimeLicenseFile || "").trim();
  return {
    backendType: String(row.runtimeBackendType || "").trim() || "-",
    providerSpec: String(row.runtimeProviderSpec || "").trim(),
    requiredModules,
    simulationMode: String(row.runtimeSimulationMode || "").trim() || "-",
    licenseStatus: licenseFile ? "requested" : "none",
    licenseSource: licenseFile ? "runtime_input" : "none",
    licenseFile,
  };
}

function buildCurrentRuntimeOverrides(config) {
  const row = config && typeof config === "object" ? config : {};
  return {
    runtimeBackendType: String(row.runtimeBackendType || "").trim(),
    runtimeProviderSpec: String(row.runtimeProviderSpec || "").trim(),
    runtimeRequiredModulesText: String(row.runtimeRequiredModulesText || "").trim(),
    runtimeSimulationMode: String(row.runtimeSimulationMode || "").trim(),
    runtimeLicenseFile: String(row.runtimeLicenseFile || "").trim(),
  };
}

function formatRuntimePreviewValue(value) {
  const text = String(value || "").trim();
  return text || "-";
}

function buildRuntimePairPreviewText(options) {
  const opts = options && typeof options === "object" ? options : {};
  const baselinePresetId = String(opts.baselinePresetId || "").trim();
  const targetPresetId = String(opts.targetPresetId || "").trim();
  const currentConfigLabel = String(opts.currentConfigLabel || "").trim();
  const pairLabel = String(
    opts.pairLabel || getRuntimePurposePairLabel(baselinePresetId, targetPresetId, currentConfigLabel)
  ).trim();
  const currentOverrides = buildCurrentRuntimeOverrides(opts.currentOverrides);
  const baselineOverrides = buildRuntimePurposePresetOverrides(baselinePresetId) || {};
  const targetOverrides = targetPresetId === RUNTIME_PURPOSE_PRESET_CURRENT_CONFIG
    ? currentOverrides
    : (buildRuntimePurposePresetOverrides(targetPresetId) || {});
  const baselineFallback = buildRuntimeDiagnosticsFallbackFromOverrides(baselineOverrides);
  const targetFallback = buildRuntimeDiagnosticsFallbackFromOverrides(targetOverrides);
  const baselineForecast = summarizeRuntimeDiagnostics(null, baselineFallback);
  const targetForecast = summarizeRuntimeDiagnostics(null, targetFallback);
  const deltaLines = [];
  const pushDelta = (label, leftValue, rightValue) => {
    const left = formatRuntimePreviewValue(leftValue);
    const right = formatRuntimePreviewValue(rightValue);
    if (left === right) return;
    deltaLines.push(`- ${label}: ${left} -> ${right}`);
  };
  pushDelta("backend", baselineFallback.backendType, targetFallback.backendType);
  pushDelta("provider", baselineFallback.providerSpec, targetFallback.providerSpec);
  pushDelta("simulation_mode", baselineFallback.simulationMode, targetFallback.simulationMode);
  pushDelta(
    "required_modules",
    (Array.isArray(baselineFallback.requiredModules) ? baselineFallback.requiredModules : []).join(","),
    (Array.isArray(targetFallback.requiredModules) ? targetFallback.requiredModules : []).join(",")
  );
  pushDelta("license_status", baselineFallback.licenseStatus, targetFallback.licenseStatus);
  pushDelta("license_source", baselineFallback.licenseSource, targetFallback.licenseSource);
  if (targetPresetId === RUNTIME_PURPOSE_PRESET_CURRENT_CONFIG) {
    deltaLines.push(`- target_mode: current_config -> ${formatRuntimePreviewValue(currentConfigLabel)}`);
  }
  return [
    `selected_pair: ${pairLabel || "-"}`,
    `baseline_forecast: ${baselineForecast.badgeLine}`,
    `target_forecast: ${targetForecast.badgeLine}`,
    "planned_deltas:",
    ...(deltaLines.length > 0 ? deltaLines : ["- none"]),
  ].join("\n");
}

function getCompareSessionReplayPair(entry) {
  const row = entry && typeof entry === "object" ? entry : {};
  const baselinePresetId = String(row.baselinePresetId || "").trim();
  const targetPresetId = String(row.targetPresetId || "").trim();
  if (!baselinePresetId || !targetPresetId) {
    return null;
  }
  return {
    baselinePresetId,
    targetPresetId,
    pairId: makeCompareReplayPairId(baselinePresetId, targetPresetId),
    pairLabel: String(row.pairLabel || `${baselinePresetId} -> ${targetPresetId}`).trim(),
  };
}

function applyCompareReplayPairMeta(pair, pairMetaById) {
  const basePair = pair && typeof pair === "object" ? pair : null;
  if (!basePair) return null;
  const pairId = String(basePair.pairId || makeCompareReplayPairId(basePair.baselinePresetId, basePair.targetPresetId)).trim();
  const metaMap = pairMetaById && typeof pairMetaById === "object" ? pairMetaById : {};
  const meta = normalizeCompareReplayPairMetaEntry(metaMap[pairId]);
  const defaultPairLabel = String(
    basePair.defaultPairLabel || basePair.pairLabel || `${String(basePair.baselinePresetId || "")} -> ${String(basePair.targetPresetId || "")}`
  ).trim();
  const customLabel = String(meta.customLabel || "").trim();
  return {
    ...basePair,
    pairId,
    defaultPairLabel,
    customLabel,
    pinned: meta.pinned === true,
    pairLabel: customLabel || defaultPairLabel,
  };
}

function formatCompareSessionHistoryEntry(entry, ordinal, pairMetaById) {
  const row = entry && typeof entry === "object" ? entry : {};
  const indexPrefix = Number.isFinite(Number(ordinal)) && Number(ordinal) > 0 ? `[${Number(ordinal)}] ` : "";
  const parts = [
    `${indexPrefix}${String(row.timestampUtc || "-")}`,
    `source=${String(row.source || "-")}`,
    `status=${String(row.status || "-")}`,
  ];
  const replayPair = applyCompareReplayPairMeta(getCompareSessionReplayPair(row), pairMetaById);
  const pairLabel = String(replayPair?.pairLabel || row.pairLabel || "").trim();
  if (pairLabel) {
    parts.push(`pair=${pairLabel}`);
  }
  if (replayPair?.pinned === true) {
    parts.push("pin=yes");
  }
  const phase = String(row.phase || "").trim();
  if (phase) {
    parts.push(`phase=${phase}`);
  }
  const compareRunId = String(row.compareRunId || "").trim();
  if (compareRunId) {
    parts.push(`compare=${compareRunId}`);
  }
  const currentRunId = String(row.currentRunId || "").trim();
  if (currentRunId) {
    parts.push(`current=${currentRunId}`);
  }
  const assessment = String(row.assessment || "").trim();
  if (assessment) {
    parts.push(`assessment=${assessment}`);
  }
  const note = String(row.note || "").trim();
  if (note) {
    parts.push(`note=${note}`);
  }
  return parts.join(" | ");
}

function summarizeCompareSessionHistory(entries, pairMetaById) {
  const rows = Array.isArray(entries) ? entries : [];
  if (rows.length === 0) {
    return "no compare sessions recorded";
  }
  return rows
    .slice(0, 6)
    .map((row, idx) => formatCompareSessionHistoryEntry(row, idx + 1, pairMetaById))
    .join("\n");
}

function compactCompareQuickActionLabel(value, maxLength = 28) {
  const text = String(value || "").trim();
  const limit = Math.max(12, Number(maxLength || 28));
  if (!text) return "-";
  if (text.length <= limit) return text;
  return `${text.slice(0, limit - 3)}...`;
}

function buildCompareSessionReplayOptions(entries, pairMetaById, retentionPolicy) {
  const rows = Array.isArray(entries) ? entries : [];
  const seen = new Set();
  const options = [];
  rows.forEach((row) => {
    const pair = applyCompareReplayPairMeta(getCompareSessionReplayPair(row), pairMetaById);
    if (!pair) return;
    const key = String(pair.pairId || "").trim();
    if (seen.has(key)) return;
    seen.add(key);
    const retention = analyzeCompareSessionSelectedPairRetention(entries, pairMetaById, retentionPolicy, pair);
    const retentionBadge = retention.state === "latest_window"
      ? "KEEP:latest"
      : retention.state === "retained_extra"
        ? "KEEP:extra"
        : `KEEP:${String(retention.state || "unknown")}`;
    options.push({
      id: key,
      baselinePresetId: pair.baselinePresetId,
      targetPresetId: pair.targetPresetId,
      pairLabel: pair.pairLabel,
      defaultPairLabel: pair.defaultPairLabel,
      customLabel: pair.customLabel,
      pinned: pair.pinned === true,
      retentionState: retention.state,
      label: `${pair.pinned === true ? "PIN | " : ""}${retentionBadge} | ${pair.pairLabel} | ${String(row?.status || "-")} | ${String(row?.source || "-")}`,
      sortOrder: options.length,
    });
  });
  return options
    .sort((left, right) => {
      const pinDelta = Number(Boolean(right?.pinned)) - Number(Boolean(left?.pinned));
      if (pinDelta !== 0) return pinDelta;
      return Number(left?.sortOrder || 0) - Number(right?.sortOrder || 0);
    })
    .slice(0, COMPARE_REPLAY_PAIR_OPTION_LIMIT);
}

function countCompareReplayPairOptionsByRetentionState(options, state) {
  return (Array.isArray(options) ? options : []).filter(
    (row) => String(row?.retentionState || "").trim() === String(state || "").trim()
  ).length;
}

function isRuntimeBlockedError(message) {
  const text = String(message || "").trim().toLowerCase();
  return text.includes("required runtime modules unavailable") || text.includes("runtime provider failed");
}

export function App() {
  const params = new URLSearchParams(window.location.search);
  const initialCompareSessionPrefs = React.useMemo(() => loadCompareSessionPrefs(), []);
  const [layoutMode, setLayoutMode] = React.useState(
    normalizeLayoutMode(params.get("view") || "triad")
  );
  const [densityMode, setDensityMode] = React.useState(
    normalizeDensityMode(params.get("density") || "comfortable")
  );
  const [focusLeftOpen, setFocusLeftOpen] = React.useState(false);
  const [focusRightOpen, setFocusRightOpen] = React.useState(false);
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
  const [runtimeBackendType, setRuntimeBackendType] = React.useState(
    String(params.get("backend") || "analytic_targets")
  );
  const [runtimeProviderSpec, setRuntimeProviderSpec] = React.useState(
    String(params.get("runtime_provider") || "")
  );
  const [runtimeRequiredModulesText, setRuntimeRequiredModulesText] = React.useState(
    String(params.get("runtime_required_modules") || "")
  );
  const [runtimeFailurePolicy, setRuntimeFailurePolicy] = React.useState(
    String(params.get("runtime_failure_policy") || "error")
  );
  const [runtimeSimulationMode, setRuntimeSimulationMode] = React.useState(
    String(params.get("simulation_mode") || "auto")
  );
  const [runtimeMultiplexingMode, setRuntimeMultiplexingMode] = React.useState(
    String(params.get("runtime_multiplexing_mode") || "tdm")
  );
  const [runtimeBpmPhaseCodeText, setRuntimeBpmPhaseCodeText] = React.useState(
    String(params.get("runtime_bpm_phase_code") || "")
  );
  const [runtimeMultiplexingPlanJson, setRuntimeMultiplexingPlanJson] = React.useState(
    String(params.get("runtime_multiplexing_plan_json") || "")
  );
  const [runtimeDevice, setRuntimeDevice] = React.useState(
    String(params.get("runtime_device") || "cpu")
  );
  const [runtimeLicenseTier, setRuntimeLicenseTier] = React.useState(
    String(params.get("runtime_license_tier") || "trial")
  );
  const [runtimeLicenseFile, setRuntimeLicenseFile] = React.useState(
    String(params.get("runtime_license_file") || "")
  );
  const [runtimeTxFfdFilesText, setRuntimeTxFfdFilesText] = React.useState(
    String(params.get("runtime_tx_ffd_files") || "")
  );
  const [runtimeRxFfdFilesText, setRuntimeRxFfdFilesText] = React.useState(
    String(params.get("runtime_rx_ffd_files") || "")
  );
  const [runtimeMitsubaEgoOriginText, setRuntimeMitsubaEgoOriginText] = React.useState(
    String(params.get("runtime_mitsuba_ego_origin") || "")
  );
  const [runtimeMitsubaChirpIntervalText, setRuntimeMitsubaChirpIntervalText] = React.useState(
    String(params.get("runtime_mitsuba_chirp_interval") || "")
  );
  const [runtimeMitsubaMinRangeText, setRuntimeMitsubaMinRangeText] = React.useState(
    String(params.get("runtime_mitsuba_min_range") || "")
  );
  const [runtimeMitsubaSpheresJson, setRuntimeMitsubaSpheresJson] = React.useState(
    String(params.get("runtime_mitsuba_spheres_json") || "")
  );
  const [runtimePoSbrRepoRoot, setRuntimePoSbrRepoRoot] = React.useState(
    String(params.get("runtime_po_sbr_repo_root") || "")
  );
  const [runtimePoSbrGeometryPath, setRuntimePoSbrGeometryPath] = React.useState(
    String(params.get("runtime_po_sbr_geometry_path") || "")
  );
  const [runtimePoSbrChirpIntervalText, setRuntimePoSbrChirpIntervalText] = React.useState(
    String(params.get("runtime_po_sbr_chirp_interval") || "")
  );
  const [runtimePoSbrBouncesText, setRuntimePoSbrBouncesText] = React.useState(
    String(params.get("runtime_po_sbr_bounces") || "")
  );
  const [runtimePoSbrRaysPerLambdaText, setRuntimePoSbrRaysPerLambdaText] = React.useState(
    String(params.get("runtime_po_sbr_rays_per_lambda") || "")
  );
  const [runtimePoSbrAlphaDegText, setRuntimePoSbrAlphaDegText] = React.useState(
    String(params.get("runtime_po_sbr_alpha_deg") || "")
  );
  const [runtimePoSbrPhiDegText, setRuntimePoSbrPhiDegText] = React.useState(
    String(params.get("runtime_po_sbr_phi_deg") || "")
  );
  const [runtimePoSbrThetaDegText, setRuntimePoSbrThetaDegText] = React.useState(
    String(params.get("runtime_po_sbr_theta_deg") || "")
  );
  const [runtimePoSbrRadialVelocityText, setRuntimePoSbrRadialVelocityText] = React.useState(
    String(params.get("runtime_po_sbr_radial_velocity") || "")
  );
  const [runtimePoSbrMinRangeText, setRuntimePoSbrMinRangeText] = React.useState(
    String(params.get("runtime_po_sbr_min_range") || "")
  );
  const [runtimePoSbrMaterialTag, setRuntimePoSbrMaterialTag] = React.useState(
    String(params.get("runtime_po_sbr_material_tag") || "")
  );
  const [runtimePoSbrPathIdPrefix, setRuntimePoSbrPathIdPrefix] = React.useState(
    String(params.get("runtime_po_sbr_path_id_prefix") || "")
  );
  const [runtimePoSbrComponentsJson, setRuntimePoSbrComponentsJson] = React.useState(
    String(params.get("runtime_po_sbr_components_json") || "")
  );
  const [compareGraphRunId, setCompareGraphRunId] = React.useState(
    String(params.get("compare_run_id") || "")
  );
  const [compareGraphRunSummary, setCompareGraphRunSummary] = React.useState(null);
  const [compareRunStatusText, setCompareRunStatusText] = React.useState("-");
  const [compareRunPinnedManual, setCompareRunPinnedManual] = React.useState(
    String(params.get("compare_run_id") || "").trim() !== ""
  );
  const [compareAutoSkipForRunId, setCompareAutoSkipForRunId] = React.useState("");
  const compareSessionImportFileInputRef = React.useRef(null);
  const compareSessionRetentionSnapshotRef = React.useRef({
    initialized: false,
    extraCount: 0,
    policy: COMPARE_SESSION_RETENTION_POLICY_DEFAULT,
  });
  const [lastRegressionSession, setLastRegressionSession] = React.useState(null);
  const [lastRegressionExport, setLastRegressionExport] = React.useState(null);
  const [decisionOpsStatusText, setDecisionOpsStatusText] = React.useState("-");
  const [trackCompareRunnerStatusText, setTrackCompareRunnerStatusText] = React.useState("-");
  const [compareSessionTransferStatusText, setCompareSessionTransferStatusText] = React.useState("-");
  const [compareSessionTransferBadgeRows, setCompareSessionTransferBadgeRows] = React.useState(() => (
    buildCompareSessionTransferBadges({ direction: "idle" })
  ));
  const [stagedCompareSessionImport, setStagedCompareSessionImport] = React.useState(null);
  const [compareSessionRetentionGroupHintText, setCompareSessionRetentionGroupHintText] = React.useState(
    "retention_group_hint: none"
  );
  const [compareSessionRetentionPolicy, setCompareSessionRetentionPolicy] = React.useState(
    () => initialCompareSessionPrefs.retentionPolicy || COMPARE_SESSION_RETENTION_POLICY_DEFAULT
  );
  const [compareSessionHistory, setCompareSessionHistory] = React.useState(
    () => initialCompareSessionPrefs.history
  );
  const [compareReplayPairMetaById, setCompareReplayPairMetaById] = React.useState(
    () => initialCompareSessionPrefs.pairMetaById || {}
  );
  const [comparePairArtifactExpectationById, setComparePairArtifactExpectationById] = React.useState(
    () => initialCompareSessionPrefs.pairArtifactExpectationById || {}
  );
  const [selectedCompareReplayPairId, setSelectedCompareReplayPairId] = React.useState(
    () => initialCompareSessionPrefs.selectedReplayPairId
  );
  const [expandedPinnedCompareQuickActionId, setExpandedPinnedCompareQuickActionId] = React.useState("");
  const [selectedCompareReplayPairLabelDraft, setSelectedCompareReplayPairLabelDraft] = React.useState("");
  const [trackCompareBaselinePresetId, setTrackCompareBaselinePresetId] = React.useState(
    RUNTIME_PURPOSE_PRESET_LOW_FIDELITY
  );
  const [trackCompareTargetPresetId, setTrackCompareTargetPresetId] = React.useState(
    RUNTIME_PURPOSE_PRESET_CURRENT_CONFIG
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
  const [artifactInspectorStatusSummary, setArtifactInspectorStatusSummary] = React.useState(() => (
    normalizeArtifactInspectorStatusSummary({})
  ));
  const [contractOverlayEnabled, setContractOverlayEnabled] = React.useState(
    String(params.get("contract_overlay") || "0") === "1"
  );
  const [contractTimeline, setContractTimeline] = React.useState([]);
  const [selectedNodeId, setSelectedNodeId] = React.useState("");
  const [selectedNodeParamsText, setSelectedNodeParamsText] = React.useState("{}");
  const policyEvalListCacheRef = React.useRef(new Map());

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

  React.useEffect(() => {
    const query = new URLSearchParams(window.location.search);
    query.set("view", layoutMode);
    query.set("density", densityMode);
    const next = `${window.location.pathname}?${query.toString()}`;
    window.history.replaceState(null, "", next);
  }, [densityMode, layoutMode]);

  React.useEffect(() => {
    if (layoutMode === "focus") return;
    setFocusLeftOpen(false);
    setFocusRightOpen(false);
  }, [layoutMode]);

  const setStatus = React.useCallback((text, tone) => {
    setStatusText(String(text || "idle"));
    setStatusTone(String(tone || "status-neutral"));
  }, []);

  const applyCompareSessionState = React.useCallback((stateInput) => {
    const next = buildCompareSessionRetainedState(stateInput);
    setCompareSessionRetentionPolicy(next.retentionPolicy);
    setCompareSessionHistory(next.history);
    setCompareReplayPairMetaById(next.pairMetaById);
    setComparePairArtifactExpectationById(next.pairArtifactExpectationById);
    setSelectedCompareReplayPairId(next.selectedReplayPairId);
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

  const appendCompareSession = React.useCallback((entryInput) => {
    const row = entryInput && typeof entryInput === "object" ? entryInput : {};
    const nextRow = {
      id: `cmp_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
      timestampUtc: new Date().toISOString(),
      ...row,
    };
    setCompareSessionHistory((prev) => buildCompareSessionRetainedHistory(
      [nextRow, ...(Array.isArray(prev) ? prev : [])],
      compareReplayPairMetaById,
      compareSessionRetentionPolicy
    ));
  }, [
    compareReplayPairMetaById,
    compareSessionRetentionPolicy,
  ]);

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

  React.useEffect(() => {
    policyEvalListCacheRef.current.clear();
  }, [apiBase]);

  const fetchPolicyEvalListCached = React.useCallback(async (options) => {
    const opts = options && typeof options === "object" ? options : {};
    const candidateRunId = String(opts.candidateRunId || "").trim();
    const baselineId = String(opts.baselineId || "").trim();
    const limit = Number(opts.limit || 0);
    const offset = Number(opts.offset || 0);
    const normalized = {
      candidateRunId,
      baselineId,
      limit: Number.isFinite(limit) && limit > 0 ? Math.floor(limit) : 0,
      offset: Number.isFinite(offset) && offset > 0 ? Math.floor(offset) : 0,
    };
    const key = JSON.stringify(normalized);
    const nowMs = Date.now();
    const ttlMs = 20_000;
    const cache = policyEvalListCacheRef.current;
    const cached = cache.get(key);
    if (
      cached &&
      typeof cached === "object" &&
      Number.isFinite(Number(cached.timestamp_ms || 0)) &&
      (nowMs - Number(cached.timestamp_ms || 0)) <= ttlMs
    ) {
      return { payload: cached.payload || {}, cacheHit: true };
    }
    const payload = await listPolicyEvals(apiBase, normalized);
    cache.set(key, { timestamp_ms: nowMs, payload });
    if (cache.size > 24) {
      const entries = Array.from(cache.entries());
      entries.sort((a, b) => Number(a?.[1]?.timestamp_ms || 0) - Number(b?.[1]?.timestamp_ms || 0));
      while (entries.length > 16) {
        const removed = entries.shift();
        if (!removed) break;
        cache.delete(String(removed[0]));
      }
    }
    return { payload, cacheHit: false };
  }, [apiBase]);

  const loadCompareGraphRunById = React.useCallback(async (graphRunIdInput, options) => {
    const opts = options && typeof options === "object" ? options : {};
    const mode = String(opts.mode || "manual");
    const graphRunId = String(graphRunIdInput || "").trim();
    const shouldSetStatus = Boolean(opts.setStatus !== false);
    const pinManual = mode === "manual" || Boolean(opts.pinManual);

    if (!graphRunId) {
      if (mode === "manual" && shouldSetStatus) {
        setStatus("compare graph run id is required", "status-warn");
      }
      setCompareGraphRunId("");
      setCompareGraphRunSummary(null);
      setCompareRunStatusText("compare: not set");
      setCompareRunPinnedManual(false);
      setTrackCompareRunnerStatusText("-");
      return false;
    }

    if (mode === "manual" && shouldSetStatus) {
      setStatus(`loading compare graph run: ${graphRunId}`, "status-warn");
    }

    try {
      const sumRes = await getGraphRunSummaryMaybe(apiBase, graphRunId);
      if (!sumRes.ok) {
        throw new Error(`graph summary request failed (${Number(sumRes.status)})`);
      }
      const summary = sumRes.payload || {};
      const completedAt = String(summary.completed_at || summary.created_at || "-");
      const status = String(summary.status || "-");
      setCompareGraphRunId(graphRunId);
      setCompareGraphRunSummary(summary);
      setCompareRunPinnedManual(pinManual);
      setCompareAutoSkipForRunId("");
      setCompareRunStatusText(
        `compare_mode=${mode} | run=${graphRunId} | status=${status} | completed_at=${completedAt}`
      );
      if (mode === "manual") {
        setTrackCompareRunnerStatusText("manual_compare_loaded");
        appendCompareSession({
          source: "manual_load",
          status: "loaded",
          pairLabel: `${trackCompareBaselinePresetId} -> ${trackCompareTargetPresetId}`,
          baselinePresetId: trackCompareBaselinePresetId,
          targetPresetId: trackCompareTargetPresetId,
          compareRunId: graphRunId,
          note: `graph_status=${status}`,
        });
      }
      if (mode === "manual" && shouldSetStatus) {
        setStatus(`compare graph run loaded: ${graphRunId}`, "status-ok");
      }
      return true;
    } catch (err) {
      setCompareGraphRunSummary(null);
      if (pinManual) {
        setCompareRunPinnedManual(true);
      }
      setCompareRunStatusText(
        `compare_mode=${mode} | run=${graphRunId} | load_failed=${String(err.message || err)}`
      );
      if (mode === "manual" && shouldSetStatus) {
        setStatus(`compare graph run load failed: ${String(err.message || err)}`, "status-err");
      }
      if (mode === "manual") {
        appendCompareSession({
          source: "manual_load",
          status: "failed",
          pairLabel: `${trackCompareBaselinePresetId} -> ${trackCompareTargetPresetId}`,
          baselinePresetId: trackCompareBaselinePresetId,
          targetPresetId: trackCompareTargetPresetId,
          compareRunId: graphRunId,
          note: String(err.message || err),
        });
      }
      return false;
    }
  }, [
    apiBase,
    appendCompareSession,
    setStatus,
    trackCompareBaselinePresetId,
    trackCompareTargetPresetId,
  ]);

  const clearCompareGraphRun = React.useCallback(() => {
    setCompareGraphRunId("");
    setCompareGraphRunSummary(null);
    setCompareRunPinnedManual(false);
    setCompareAutoSkipForRunId(String(graphRunSummary?.graph_run_id || "").trim());
    setCompareRunStatusText("compare: cleared");
    setTrackCompareRunnerStatusText("-");
    setStatus("compare graph run cleared", "status-ok");
  }, [graphRunSummary?.graph_run_id, setStatus]);

  const pinCurrentGraphRunAsCompare = React.useCallback(() => {
    const graphRunId = String(
      graphRunSummary?.graph_run_id || graphRunSummary?.run_id || ""
    ).trim();
    if (!graphRunId || !graphRunSummary) {
      setStatus("run graph first to pin current as compare", "status-warn");
      return;
    }
    setCompareGraphRunId(graphRunId);
    setCompareGraphRunSummary(graphRunSummary);
    setCompareRunPinnedManual(true);
    setCompareAutoSkipForRunId("");
    setCompareRunStatusText(
      `compare_mode=pinned_current | run=${graphRunId} | waiting_for_next_run=true`
    );
    setTrackCompareRunnerStatusText("manual_compare_pinned_current");
    appendCompareSession({
      source: "pin_current",
      status: "pinned",
      pairLabel: `${trackCompareBaselinePresetId} -> ${trackCompareTargetPresetId}`,
      baselinePresetId: trackCompareBaselinePresetId,
      targetPresetId: trackCompareTargetPresetId,
      compareRunId: graphRunId,
    });
    setStatus(`current run pinned as compare: ${graphRunId}`, "status-ok");
  }, [
    appendCompareSession,
    graphRunSummary,
    setStatus,
    trackCompareBaselinePresetId,
    trackCompareTargetPresetId,
  ]);

  const setCompareGraphRunIdDraft = React.useCallback((nextText) => {
    const text = String(nextText || "");
    setCompareGraphRunId(text);
    setCompareRunPinnedManual(text.trim() !== "");
  }, []);

  const openGateEvidenceFromTimeline = React.useCallback(async (row, lookupOptions) => {
    const eventRow = row && typeof row === "object" ? row : {};
    const note = eventRow.note && typeof eventRow.note === "object" ? eventRow.note : {};
    const lookup = lookupOptions && typeof lookupOptions === "object" ? lookupOptions : {};
    const normalizeHint = (v) => {
      const text = String(v || "").trim();
      if (text === "" || text === "-") return "";
      const low = text.toLowerCase();
      if (low === "none" || low === "null") return "";
      return text;
    };
    const asPositiveInt = (v, fallback, minValue, maxValue) => {
      const n = Number(v);
      if (!Number.isFinite(n) || n <= 0) return Number(fallback);
      const iv = Math.floor(n);
      return Math.max(Number(minValue), Math.min(Number(maxValue), iv));
    };
    const normalizePath = (v) => String(v || "").replace(/\\/g, "/").trim();
    const pathMatches = (a, b) => {
      const left = normalizePath(a);
      const right = normalizePath(b);
      if (!left || !right) return false;
      return left === right || left.endsWith(right) || right.endsWith(left);
    };

    const policyEvalIdHint = normalizeHint(note.policy_eval_id);
    const runIdHint = normalizeHint(eventRow.graph_run_id);
    const baselineIdHint = normalizeHint(note.baseline_id);
    const summaryHint = normalizeHint(note.candidate_summary_json);
    const historyLimit = asPositiveInt(lookup.historyLimit, 256, 32, 4096);
    const pageBudget = asPositiveInt(lookup.pageBudget, 2, 1, 8);

    setStatus("loading gate evidence...", "status-warn");

    let resolvedEval = null;
    let evidenceSource = "timeline_note";
    let scanCount = 0;
    let cacheHitAny = false;
    let pageCountUsed = 0;
    const lookupErrors = [];

    if (policyEvalIdHint) {
      try {
        const payload = await getPolicyEval(apiBase, policyEvalIdHint);
        if (payload && typeof payload === "object") {
          resolvedEval = payload;
          evidenceSource = "policy_eval_id";
        }
      } catch (err) {
        lookupErrors.push(`get_policy_eval(${policyEvalIdHint}) failed: ${String(err.message || err)}`);
      }
    }

    if (!resolvedEval) {
      const resolveFromRows = (rows, scopeTag, cacheHit, pageIndex) => {
        const list = Array.isArray(rows) ? rows : [];
        const matchRun = (item) =>
          runIdHint !== "" &&
          normalizeHint(item?.candidate?.run_id) === runIdHint;
        const matchSummary = (item) =>
          summaryHint !== "" &&
          pathMatches(item?.candidate?.run_summary_json, summaryHint);

        const byEvalId = policyEvalIdHint !== ""
          ? list.find((item) => normalizeHint(item?.policy_eval_id) === policyEvalIdHint) || null
          : null;
        const byRunAndSummary = list.find((item) => matchRun(item) && matchSummary(item)) || null;
        const byRunOnly = list.find((item) => matchRun(item)) || null;
        const bySummaryOnly = list.find((item) => matchSummary(item)) || null;
        const byBaselineOnly = baselineIdHint !== ""
          ? list.find((item) => normalizeHint(item?.baseline?.baseline_id) === baselineIdHint) || null
          : null;
        const resolved = byEvalId || byRunAndSummary || byRunOnly || bySummaryOnly || byBaselineOnly;
        if (!resolved) return false;

        let matchedBy = "fallback";
        if (byEvalId) matchedBy = "policy_eval_id";
        else if (byRunAndSummary) matchedBy = "run_id+summary_json";
        else if (byRunOnly) matchedBy = "run_id";
        else if (bySummaryOnly) matchedBy = "summary_json";
        else if (byBaselineOnly) matchedBy = "baseline_id";
        resolvedEval = resolved;
        evidenceSource = `policy_eval_list:${scopeTag}:${matchedBy}:page${Number(pageIndex)}${cacheHit ? ":cache_hit" : ""}`;
        return true;
      };

      const queryPlans = [];
      if (runIdHint) {
        queryPlans.push({
          scopeTag: baselineIdHint ? "run_id+baseline_id" : "run_id",
          candidateRunId: runIdHint,
          baselineId: baselineIdHint || "",
        });
      }
      if (baselineIdHint) {
        queryPlans.push({
          scopeTag: "baseline_id",
          baselineId: baselineIdHint,
        });
      }
      queryPlans.push({
        scopeTag: "global",
      });

      const seenPlans = new Set();
      for (const plan of queryPlans) {
        const basePlan = {
          candidateRunId: String(plan.candidateRunId || "").trim(),
          baselineId: String(plan.baselineId || "").trim(),
          limit: historyLimit,
          offset: 0,
        };
        const planKey = JSON.stringify({
          candidateRunId: basePlan.candidateRunId,
          baselineId: basePlan.baselineId,
        });
        if (seenPlans.has(planKey)) continue;
        seenPlans.add(planKey);

        for (let pageIdx = 0; pageIdx < pageBudget; pageIdx += 1) {
          const normalizedPlan = {
            ...basePlan,
            offset: pageIdx * historyLimit,
          };
          try {
            const result = await fetchPolicyEvalListCached(normalizedPlan);
            const payload = result && typeof result === "object" ? result.payload : {};
            const cacheHit = Boolean(result && result.cacheHit);
            cacheHitAny = cacheHitAny || cacheHit;
            const rows = Array.isArray(payload?.policy_evals) ? payload.policy_evals : [];
            const returnedCount = Number(payload?.page?.returned_count);
            const totalCount = Number(payload?.page?.total_count);
            const effectiveReturnedCount =
              Number.isFinite(returnedCount) && returnedCount >= 0
                ? returnedCount
                : rows.length;
            scanCount += effectiveReturnedCount;
            pageCountUsed = Math.max(pageCountUsed, pageIdx + 1);
            if (resolveFromRows(rows, String(plan.scopeTag || "global"), cacheHit, pageIdx + 1)) {
              break;
            }
            const reachedEnd =
              effectiveReturnedCount <= 0 ||
              !Number.isFinite(totalCount) ||
              (normalizedPlan.offset + effectiveReturnedCount) >= totalCount;
            if (reachedEnd) {
              break;
            }
          } catch (err) {
            lookupErrors.push(
              `list_policy_evals(${String(plan.scopeTag || "global")}@page${pageIdx + 1}) failed: ${String(err.message || err)}`
            );
            break;
          }
        }
        if (resolvedEval) {
          break;
        }
      }
    }

    if (resolvedEval && typeof resolvedEval === "object") {
      const candidate = resolvedEval.candidate && typeof resolvedEval.candidate === "object"
        ? resolvedEval.candidate
        : {};
      const baseline = resolvedEval.baseline && typeof resolvedEval.baseline === "object"
        ? resolvedEval.baseline
        : {};
      const parity = resolvedEval.parity && typeof resolvedEval.parity === "object"
        ? resolvedEval.parity
        : {};
      const policy = resolvedEval.policy && typeof resolvedEval.policy === "object"
        ? resolvedEval.policy
        : {};
      const gateFailures = Array.isArray(resolvedEval.gate_failures) ? resolvedEval.gate_failures : [];
      const parityFailures = Array.isArray(parity.failures) ? parity.failures : [];
      const runId = normalizeHint(candidate.run_id) || runIdHint;
      const gateFailed = Boolean(resolvedEval.gate_failed);
      const policyKeys = Object.keys(policy).sort((a, b) => a.localeCompare(b));
      const lines = [
        `policy_eval_id: ${normalizeHint(resolvedEval.policy_eval_id) || policyEvalIdHint || "-"}`,
        `evidence_source: persisted/${evidenceSource}`,
        `gate_failed: ${gateFailed}`,
        `recommendation: ${String(resolvedEval.recommendation || "-")}`,
        `baseline_id: ${normalizeHint(baseline.baseline_id) || baselineIdHint || "-"}`,
        `candidate_run_id: ${runId || "-"}`,
        `candidate_summary_json: ${normalizeHint(candidate.run_summary_json) || summaryHint || "-"}`,
        `parity_pass: ${Boolean(parity.pass)}`,
        `parity_failure_count: ${Number(parityFailures.length || 0)}`,
        `gate_failure_count: ${Number(gateFailures.length || 0)}`,
        `policy_eval_history_limit: ${Number(historyLimit)}`,
        `policy_eval_page_budget: ${Number(pageBudget)}`,
        `policy_eval_page_count_used: ${Number(pageCountUsed || 0)}`,
        `policy_eval_scan_count: ${Number(scanCount || 0)}`,
        `policy_eval_cache_hit_any: ${Boolean(cacheHitAny)}`,
        "",
        "gate_failures:",
      ];
      if (gateFailures.length === 0) {
        lines.push("- none");
      } else {
        gateFailures.slice(0, 12).forEach((failure, idx) => {
          const metric = failure && failure.metric ? ` (${String(failure.metric)})` : "";
          lines.push(
            `- [${Number(idx) + 1}] ${String((failure && failure.rule) || "unknown_rule")}${metric}: ${String(
              (failure && failure.value) ?? "-"
            )} > ${String((failure && failure.limit) ?? "-")}`
          );
        });
      }
      lines.push("", "policy:");
      if (policyKeys.length === 0) {
        lines.push("- none");
      } else {
        policyKeys.forEach((key) => {
          lines.push(`- ${String(key)}: ${String(policy[key])}`);
        });
      }
      lines.push(
        "",
        `source_event: ${String(eventRow.event_source || "-")}`,
        `timestamp_ms: ${Number(eventRow.timestamp_ms || 0)}`,
        `contract_delta: ${Number(eventRow?.delta?.unique_warning_count || 0)}/${Number(eventRow?.delta?.attempt_count_total || 0)}`,
      );
      if (lookupErrors.length > 0) {
        lines.push("", "lookup_warnings:", ...lookupErrors.map((msg) => `- ${msg}`));
      }
      setGateResultText(lines.join("\n"));
      if (runId) setLastGraphRunId(runId);
      setStatus(
        gateFailed ? `gate evidence opened (HOLD): ${runId || "-"}` : `gate evidence opened (ADOPT): ${runId || "-"}`,
        gateFailed ? "status-warn" : "status-ok"
      );
      return;
    }

    const gateFailed = Boolean(note.gate_failed);
    const rules = Array.isArray(note.failure_rules) ? note.failure_rules : [];
    const lines = [
      `policy_eval_id: ${policyEvalIdHint || "-"}`,
      "evidence_source: timeline_note_only",
      `gate_failed: ${gateFailed}`,
      `recommendation: ${String(note.recommendation || "-")}`,
      `baseline_id: ${baselineIdHint || "-"}`,
      `graph_run_id: ${runIdHint || "-"}`,
      `candidate_summary_json: ${summaryHint || "-"}`,
      `failure_count: ${Number(note.failure_count || 0)}`,
      `policy_eval_history_limit: ${Number(historyLimit)}`,
      `policy_eval_page_budget: ${Number(pageBudget)}`,
      `policy_eval_page_count_used: ${Number(pageCountUsed || 0)}`,
      `policy_eval_scan_count: ${Number(scanCount || 0)}`,
      `policy_eval_cache_hit_any: ${Boolean(cacheHitAny)}`,
      "",
      "gate_failures:",
      ...(rules.length > 0 ? rules.map((rule, idx) => `- [${Number(idx) + 1}] ${rule}`) : ["- none"]),
      "",
      `source_event: ${String(eventRow.event_source || "-")}`,
      `timestamp_ms: ${Number(eventRow.timestamp_ms || 0)}`,
      `contract_delta: ${Number(eventRow?.delta?.unique_warning_count || 0)}/${Number(eventRow?.delta?.attempt_count_total || 0)}`,
    ];
    if (lookupErrors.length > 0) {
      lines.push("", "lookup_warnings:", ...lookupErrors.map((msg) => `- ${msg}`));
    }
    setGateResultText(lines.join("\n"));
    if (runIdHint) setLastGraphRunId(runIdHint);
    setStatus(`gate evidence unresolved: ${runIdHint || "-"}`, "status-warn");
  }, [apiBase, fetchPolicyEvalListCached, setGateResultText, setLastGraphRunId, setStatus]);

  React.useEffect(() => {
    refreshContractWarnings();
  }, [refreshContractWarnings]);

  React.useEffect(() => {
    refreshContractWarnings();
  }, [graphRunText, gateResultText, validationText, refreshContractWarnings]);

  React.useEffect(() => {
    const currentGraphRunId = String(graphRunSummary?.graph_run_id || "").trim();
    if (!currentGraphRunId) return;
    if (String(compareAutoSkipForRunId || "").trim() === currentGraphRunId) return;

    const compareLockedByUser = Boolean(compareRunPinnedManual);
    if (compareLockedByUser && String(compareGraphRunId).trim() === currentGraphRunId) {
      if (!compareGraphRunSummary) {
        setCompareRunStatusText("compare: same as current run (disabled)");
      }
      return;
    }
    if (compareLockedByUser) return;

    let canceled = false;
    const loadAutoCompare = async () => {
      const cacheSourceId = String(
        graphRunSummary?.execution?.cache?.source_graph_run_id || ""
      ).trim();
      if (cacheSourceId && cacheSourceId !== currentGraphRunId) {
        if (
          cacheSourceId === String(compareGraphRunId || "").trim()
          && compareGraphRunSummary
        ) {
          return;
        }
        if (canceled) return;
        await loadCompareGraphRunById(cacheSourceId, { mode: "auto_cache_source", setStatus: false });
        return;
      }

      const payload = await listGraphRuns(apiBase);
      const rows = Array.isArray(payload.graph_runs) ? payload.graph_runs : [];
      const candidate = rows.find((row) => {
        const rid = String(row?.graph_run_id || "").trim();
        const status = String(row?.status || "").trim().toLowerCase();
        return rid !== "" && rid !== currentGraphRunId && status === "completed";
      });
      const candidateId = String(candidate?.graph_run_id || "").trim();
      if (!candidateId) {
        setCompareGraphRunSummary(null);
        setCompareRunStatusText("compare_mode=auto_previous | no completed baseline run");
        return;
      }
      if (
        candidateId === String(compareGraphRunId || "").trim()
        && compareGraphRunSummary
      ) {
        return;
      }
      if (canceled) return;
      await loadCompareGraphRunById(candidateId, { mode: "auto_previous", setStatus: false });
    };

    loadAutoCompare().catch((err) => {
      if (canceled) return;
      setCompareGraphRunSummary(null);
      setCompareRunStatusText(`compare_mode=auto | load_failed=${String(err.message || err)}`);
    });
    return () => {
      canceled = true;
    };
  }, [
    apiBase,
    compareGraphRunId,
    compareGraphRunSummary,
    compareAutoSkipForRunId,
    compareRunPinnedManual,
    graphRunSummary,
    loadCompareGraphRunById,
  ]);

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

  const runtimeSummary = React.useMemo(() => {
    const ffdRequested = String(runtimeTxFfdFilesText || "").trim() !== ""
      || String(runtimeRxFfdFilesText || "").trim() !== "";
    return summarizeRuntimeTrack(graphRunSummary, {
      backendType: runtimeBackendType || "-",
      simulationBackend: runtimeSimulationMode || "-",
      multiplexingMode: runtimeMultiplexingMode || "-",
      antennaMode: ffdRequested ? "ffd_requested" : "isotropic",
      licenseStatus: runtimeLicenseFile ? "requested" : "none",
    });
  }, [
    graphRunSummary,
    runtimeBackendType,
    runtimeSimulationMode,
    runtimeLicenseFile,
    runtimeMultiplexingMode,
    runtimeRxFfdFilesText,
    runtimeTxFfdFilesText,
  ]);

  const configuredRequiredModules = React.useMemo(
    () => splitTokenList(runtimeRequiredModulesText),
    [runtimeRequiredModulesText]
  );

  const compareRuntimeSummary = React.useMemo(() => summarizeRuntimeTrack(compareGraphRunSummary, {
    backendType: "-",
    simulationBackend: "-",
    multiplexingMode: "-",
    antennaMode: "-",
    licenseStatus: "none",
  }), [compareGraphRunSummary]);

  const configuredRuntimeSummary = React.useMemo(() => {
    const ffdRequested = String(runtimeTxFfdFilesText || "").trim() !== ""
      || String(runtimeRxFfdFilesText || "").trim() !== "";
    return summarizeRuntimeTrack(null, {
      backendType: runtimeBackendType || "-",
      simulationBackend: runtimeSimulationMode || "-",
      multiplexingMode: runtimeMultiplexingMode || "-",
      antennaMode: ffdRequested ? "ffd_requested" : "isotropic",
      licenseStatus: runtimeLicenseFile ? "requested" : "none",
    });
  }, [
    runtimeBackendType,
    runtimeSimulationMode,
    runtimeMultiplexingMode,
    runtimeLicenseFile,
    runtimeRxFfdFilesText,
    runtimeTxFfdFilesText,
  ]);

  const runtimeDiagnostics = React.useMemo(() => summarizeRuntimeDiagnostics(graphRunSummary, {
    backendType: runtimeBackendType || "-",
    providerSpec: runtimeProviderSpec || "",
    requiredModules: configuredRequiredModules,
    simulationMode: runtimeSimulationMode || "-",
    licenseStatus: runtimeLicenseFile ? "requested" : "none",
    licenseSource: runtimeLicenseFile ? "runtime_input" : "",
    licenseFile: runtimeLicenseFile || "",
  }), [
    configuredRequiredModules,
    graphRunSummary,
    runtimeBackendType,
    runtimeLicenseFile,
    runtimeProviderSpec,
    runtimeSimulationMode,
  ]);

  const compareRuntimeDiagnostics = React.useMemo(() => summarizeRuntimeDiagnostics(compareGraphRunSummary, {
    backendType: "-",
    providerSpec: "",
    requiredModules: [],
    simulationMode: "-",
    licenseStatus: "none",
  }), [compareGraphRunSummary]);

  const trackCompareRunnerState = React.useMemo(
    () => deriveTrackCompareRunnerStatus(trackCompareRunnerStatusText),
    [trackCompareRunnerStatusText]
  );
  const runCompareSummary = React.useMemo(
    () => buildRunCompareSummary(graphRunSummary, compareGraphRunSummary),
    [compareGraphRunSummary, graphRunSummary]
  );

  const trackCompareGuideText = React.useMemo(() => [
    "1. Run the first track and confirm artifacts are produced.",
    "2. Click Use Current as Compare to lock that run as the reference.",
    "3. Switch runtime preset or advanced controls for the alternate track.",
    "4. Run Graph (API) again and inspect Artifact Inspector diff.",
    "5. Use Policy Gate / Run Session when the current-vs-compare pair is final.",
    "6. Or click Run Low -> Current Compare to build the default pair automatically.",
    "7. Or use Run Preset Pair Compare to execute any preset-to-preset sequence.",
  ].join("\n"), []);

  const applyRuntimePurposePresetToUi = React.useCallback((presetId) => {
    return applyRuntimePurposePreset(presetId, {
      setRuntimeBackendType,
      setRuntimeProviderSpec,
      setRuntimeRequiredModulesText,
      setRuntimeFailurePolicy,
      setRuntimeSimulationMode,
      setRuntimeDevice,
      setRuntimeMitsubaEgoOriginText,
      setRuntimeMitsubaChirpIntervalText,
      setRuntimeMitsubaMinRangeText,
      setRuntimeMitsubaSpheresJson,
      setRuntimePoSbrRepoRoot,
      setRuntimePoSbrGeometryPath,
      setRuntimePoSbrChirpIntervalText,
      setRuntimePoSbrBouncesText,
      setRuntimePoSbrRaysPerLambdaText,
      setRuntimePoSbrAlphaDegText,
      setRuntimePoSbrPhiDegText,
      setRuntimePoSbrThetaDegText,
      setRuntimePoSbrRadialVelocityText,
      setRuntimePoSbrMinRangeText,
      setRuntimePoSbrMaterialTag,
      setRuntimePoSbrPathIdPrefix,
      setRuntimePoSbrComponentsJson,
    });
  }, [
    setRuntimeBackendType,
    setRuntimeDevice,
    setRuntimeFailurePolicy,
    setRuntimeMitsubaChirpIntervalText,
    setRuntimeMitsubaEgoOriginText,
    setRuntimeMitsubaMinRangeText,
    setRuntimeMitsubaSpheresJson,
    setRuntimePoSbrAlphaDegText,
    setRuntimePoSbrBouncesText,
    setRuntimePoSbrChirpIntervalText,
    setRuntimePoSbrComponentsJson,
    setRuntimePoSbrGeometryPath,
    setRuntimePoSbrMaterialTag,
    setRuntimePoSbrMinRangeText,
    setRuntimePoSbrPathIdPrefix,
    setRuntimePoSbrPhiDegText,
    setRuntimePoSbrRadialVelocityText,
    setRuntimePoSbrRaysPerLambdaText,
    setRuntimePoSbrRepoRoot,
    setRuntimePoSbrThetaDegText,
    setRuntimeProviderSpec,
    setRuntimeRequiredModulesText,
    setRuntimeSimulationMode,
  ]);
  const applyTrackCompareQuickPair = React.useCallback((row) => {
    const pair = row && typeof row === "object" ? row : {};
    setTrackCompareBaselinePresetId(String(pair.baselinePresetId || RUNTIME_PURPOSE_PRESET_LOW_FIDELITY));
    setTrackCompareTargetPresetId(String(pair.targetPresetId || RUNTIME_PURPOSE_PRESET_CURRENT_CONFIG));
  }, []);
  const trackCompareSelectedPairSummaryText = React.useMemo(
    () => getRuntimePurposePairLabel(
      trackCompareBaselinePresetId,
      trackCompareTargetPresetId,
      configuredRuntimeSummary.trackLabel
    ),
    [
      configuredRuntimeSummary.trackLabel,
      trackCompareBaselinePresetId,
      trackCompareTargetPresetId,
    ]
  );
  const trackCompareSelectedPairForecastText = React.useMemo(() => {
    return buildRuntimePairPreviewText({
      baselinePresetId: trackCompareBaselinePresetId,
      targetPresetId: trackCompareTargetPresetId,
      pairLabel: trackCompareSelectedPairSummaryText,
      currentConfigLabel: configuredRuntimeSummary.trackLabel,
      currentOverrides: {
        runtimeBackendType,
        runtimeProviderSpec,
        runtimeRequiredModulesText,
        runtimeSimulationMode,
        runtimeLicenseFile,
      },
    });
  }, [
    configuredRuntimeSummary.trackLabel,
    runtimeBackendType,
    runtimeLicenseFile,
    runtimeProviderSpec,
    runtimeRequiredModulesText,
    runtimeSimulationMode,
    trackCompareBaselinePresetId,
    trackCompareSelectedPairSummaryText,
    trackCompareTargetPresetId,
  ]);
  const compareSessionHistoryText = React.useMemo(
    () => summarizeCompareSessionHistory(compareSessionHistory, compareReplayPairMetaById),
    [compareReplayPairMetaById, compareSessionHistory]
  );
  const compareSessionRetentionOutcome = React.useMemo(
    () => analyzeCompareSessionRetentionOutcome(
      compareSessionHistory,
      compareReplayPairMetaById,
      compareSessionRetentionPolicy
    ),
    [compareReplayPairMetaById, compareSessionHistory, compareSessionRetentionPolicy]
  );
  const compareSessionRetentionPolicySummaryText = React.useMemo(
    () => summarizeCompareSessionRetentionPolicy(compareSessionRetentionPolicy, compareSessionRetentionOutcome),
    [compareSessionRetentionOutcome, compareSessionRetentionPolicy]
  );
  const compareSessionRetentionPreviewText = React.useMemo(
    () => buildCompareSessionRetentionPreviewText(
      compareSessionHistory,
      compareReplayPairMetaById,
      compareSessionRetentionPolicy
    ),
    [compareReplayPairMetaById, compareSessionHistory, compareSessionRetentionPolicy]
  );
  const compareSessionRetentionPreviewCompactSummaryText = React.useMemo(
    () => String(compareSessionRetentionPreviewText || "-").split("\n").filter(Boolean)[0] || "retention_pairs(latest/extra/dropped): - / - / -",
    [compareSessionRetentionPreviewText]
  );
  const stagedCompareSessionImportSummary = React.useMemo(
    () => buildCompareSessionImportPreviewSummary(
      stagedCompareSessionImport,
      compareSessionHistory,
      compareReplayPairMetaById,
      comparePairArtifactExpectationById,
      compareSessionRetentionPolicy
    ),
    [
      comparePairArtifactExpectationById,
      compareReplayPairMetaById,
      compareSessionHistory,
      compareSessionRetentionPolicy,
      stagedCompareSessionImport,
    ]
  );
  const compareSessionImportPreviewSummaryText = React.useMemo(
    () => String(stagedCompareSessionImportSummary?.summaryText || "import_preview: none"),
    [stagedCompareSessionImportSummary]
  );
  const compareSessionImportPreviewCompactSummaryText = React.useMemo(() => {
    const summary = String(stagedCompareSessionImportSummary?.summaryText || "import_preview: none").trim();
    if (!summary || summary === "import_preview: none") {
      return "compare_history_import_preview: none | selected_pair_retention=unchanged";
    }
    if (summary.startsWith("import_preview:")) {
      return summary.includes("selected_pair_retention=")
        ? `compare_history_${summary}`
        : `compare_history_${summary} | selected_pair_retention=unchanged`;
    }
    return summary.includes("selected_pair_retention=")
      ? `compare_history_import_preview: ${summary}`
      : `compare_history_import_preview: ${summary} | selected_pair_retention=unchanged`;
  }, [stagedCompareSessionImportSummary]);
  const compareSessionImportPreviewText = React.useMemo(
    () => String(stagedCompareSessionImportSummary?.previewText || "-"),
    [stagedCompareSessionImportSummary]
  );
  const compareSessionTransferCompactSummaryText = React.useMemo(() => {
    const badgeSummary = summarizeCompareSessionTransferBadgeLabels(compareSessionTransferBadgeRows);
    const importCompactSummary = String(compareSessionImportPreviewCompactSummaryText || "compare_history_import_preview: none")
      .replace(/^compare_history_import_preview:\s*/i, "")
      .trim();
    return `compare_history_transfer_compact: ${badgeSummary} | ${importCompactSummary || "none"}`;
  }, [compareSessionImportPreviewCompactSummaryText, compareSessionTransferBadgeRows]);
  const artifactInspectorDecisionLayoutStateText = React.useMemo(
    () => buildArtifactInspectorDecisionLine(
      artifactInspectorStatusSummary.layoutStateText,
      "layout_state",
      "artifact_inspector_layout_state"
    ),
    [artifactInspectorStatusSummary.layoutStateText]
  );
  const artifactInspectorDecisionProbeStateText = React.useMemo(
    () => buildArtifactInspectorDecisionLine(
      artifactInspectorStatusSummary.probeStateText,
      "probe_state",
      "artifact_inspector_probe_state"
    ),
    [artifactInspectorStatusSummary.probeStateText]
  );
  const artifactInspectorDecisionStatusBadgesText = React.useMemo(
    () => buildArtifactInspectorDecisionLine(
      artifactInspectorStatusSummary.statusBadgesText,
      "status_badges",
      "artifact_inspector_status_badges"
    ),
    [artifactInspectorStatusSummary.statusBadgesText]
  );
  const artifactInspectorDecisionStatusBadgeRows = React.useMemo(
    () => buildArtifactInspectorStatusBadgeRows(artifactInspectorStatusSummary.statusBadgesText),
    [artifactInspectorStatusSummary.statusBadgesText]
  );
  const latestCompareSessionText = React.useMemo(
    () => compareSessionHistory.length > 0
      ? formatCompareSessionHistoryEntry(compareSessionHistory[0], null, compareReplayPairMetaById)
      : "-",
    [compareReplayPairMetaById, compareSessionHistory]
  );
  const handleArtifactInspectorStatusChange = React.useCallback((statusInput) => {
    setArtifactInspectorStatusSummary(normalizeArtifactInspectorStatusSummary(statusInput));
  }, []);
  const latestReplayableCompareSession = React.useMemo(
    () => compareSessionHistory
      .map((row) => applyCompareReplayPairMeta(getCompareSessionReplayPair(row), compareReplayPairMetaById))
      .find(Boolean) || null,
    [compareReplayPairMetaById, compareSessionHistory]
  );
  const compareReplayPairOptions = React.useMemo(
    () => buildCompareSessionReplayOptions(
      compareSessionHistory,
      compareReplayPairMetaById,
      compareSessionRetentionPolicy
    ),
    [compareReplayPairMetaById, compareSessionHistory, compareSessionRetentionPolicy]
  );
  const pinnedCompareQuickActionOptions = React.useMemo(
    () => compareReplayPairOptions
      .filter((row) => row?.pinned === true)
      .slice(0, PINNED_COMPARE_QUICK_ACTION_LIMIT)
      .map((row) => {
        const pairId = String(row?.id || row?.pairId || "").trim();
        const storedEntry = normalizeCompareArtifactExpectationEntry(comparePairArtifactExpectationById[pairId]);
        const fallbackEntry = buildPlannedCompareArtifactExpectationEntry(row?.pairLabel);
        const effectiveEntry = normalizeCompareArtifactExpectationEntry({
          ...fallbackEntry,
          ...storedEntry,
          artifactPathFingerprintsByArtifact: Object.keys(storedEntry.artifactPathFingerprintsByArtifact || {}).length > 0
            ? storedEntry.artifactPathFingerprintsByArtifact
            : fallbackEntry.artifactPathFingerprintsByArtifact,
        });
        const quickActionBadges = buildPinnedCompareQuickActionBadges(effectiveEntry);
        return {
          ...row,
          shortLabel: compactCompareQuickActionLabel(row?.pairLabel || row?.label || row?.id || "-"),
          artifactExpectationEntry: effectiveEntry,
          artifactExpectationSummaryText: effectiveEntry.summaryText || fallbackEntry.summaryText,
          artifactPathFingerprintSummaryText: summarizeCompareArtifactPathFingerprintCompact(
            effectiveEntry.artifactPathFingerprintsByArtifact
          ),
          quickActionBadges,
          quickActionBadgeSummaryText: quickActionBadges
            .map((badge) => String(badge?.label || "").trim())
            .filter(Boolean)
            .join(" | ") || "-",
          previewText: buildRuntimePairPreviewText({
            baselinePresetId: row?.baselinePresetId,
            targetPresetId: row?.targetPresetId,
            pairLabel: row?.pairLabel,
            currentConfigLabel: configuredRuntimeSummary.trackLabel,
            currentOverrides: {
              runtimeBackendType,
              runtimeProviderSpec,
              runtimeRequiredModulesText,
              runtimeSimulationMode,
              runtimeLicenseFile,
            },
          }),
          artifactExpectationDetailText: effectiveEntry.detailText || fallbackEntry.detailText,
        };
      }),
    [
      comparePairArtifactExpectationById,
      compareReplayPairOptions,
      configuredRuntimeSummary.trackLabel,
      runtimeBackendType,
      runtimeLicenseFile,
      runtimeProviderSpec,
      runtimeRequiredModulesText,
      runtimeSimulationMode,
    ]
  );
  const pinnedCompareQuickActionSummaryText = React.useMemo(() => {
    if (pinnedCompareQuickActionOptions.length === 0) {
      return "pinned_quick_actions: -";
    }
    return `pinned_quick_actions: ${pinnedCompareQuickActionOptions.map((row) => row.pairLabel).join(" | ")}`;
  }, [pinnedCompareQuickActionOptions]);
  const pinnedCompareQuickActionDetailText = React.useMemo(() => {
    if (pinnedCompareQuickActionOptions.length === 0) {
      return [
        "pinned_quick_action_count: 0",
        "Pin a selected history pair below to promote it here.",
      ].join("\n");
    }
    return [
      `pinned_quick_action_count: ${Number(pinnedCompareQuickActionOptions.length || 0)}`,
      ...pinnedCompareQuickActionOptions.flatMap((row, idx) => ([
        `- [${Number(idx) + 1}] ${String(row.pairLabel || "-")} | baseline=${String(row.baselinePresetId || "-")} | target=${String(row.targetPresetId || "-")}`,
        `  badges: ${String(row.quickActionBadgeSummaryText || "-")}`,
        `  preview: ${String(row?.previewText || "").split("\n").slice(1).join(" | ") || "-"}`,
        `  artifact_expectation: ${String(row.artifactExpectationSummaryText || "-")}`,
        `  artifact_path_hashes: ${String(row.artifactPathFingerprintSummaryText || "-")}`,
      ])),
    ].join("\n");
  }, [pinnedCompareQuickActionOptions]);
  const latestReplayableCompareSessionText = React.useMemo(() => {
    if (!latestReplayableCompareSession) {
      return "latest_replayable_pair: -";
    }
    return `latest_replayable_pair: ${String(latestReplayableCompareSession.pairLabel || "-")} | pinned=${latestReplayableCompareSession.pinned === true}`;
  }, [latestReplayableCompareSession]);
  const selectedReplayableCompareSession = React.useMemo(() => {
    const selectedId = String(selectedCompareReplayPairId || "").trim();
    if (!selectedId) {
      return compareReplayPairOptions[0] || null;
    }
    return compareReplayPairOptions.find((row) => String(row?.id || "") === selectedId) || compareReplayPairOptions[0] || null;
  }, [compareReplayPairOptions, selectedCompareReplayPairId]);
  const selectedReplayableCompareSessionText = React.useMemo(() => {
    if (!selectedReplayableCompareSession) {
      return "selected_history_pair: -";
    }
    return `selected_history_pair: ${String(selectedReplayableCompareSession.pairLabel || "-")}`;
  }, [selectedReplayableCompareSession]);
  const selectedReplayableCompareSessionPreviewText = React.useMemo(() => {
    if (!selectedReplayableCompareSession) {
      return [
        "selected_pair: -",
        "baseline_forecast: -",
        "target_forecast: -",
        "planned_deltas:",
        "- none",
      ].join("\n");
    }
    return buildRuntimePairPreviewText({
      baselinePresetId: selectedReplayableCompareSession.baselinePresetId,
      targetPresetId: selectedReplayableCompareSession.targetPresetId,
      pairLabel: selectedReplayableCompareSession.pairLabel,
      currentConfigLabel: configuredRuntimeSummary.trackLabel,
      currentOverrides: {
        runtimeBackendType,
        runtimeProviderSpec,
        runtimeRequiredModulesText,
        runtimeSimulationMode,
        runtimeLicenseFile,
      },
    });
  }, [
    configuredRuntimeSummary.trackLabel,
    runtimeBackendType,
    runtimeLicenseFile,
    runtimeProviderSpec,
    runtimeRequiredModulesText,
    runtimeSimulationMode,
    selectedReplayableCompareSession,
  ]);
  const selectedReplayableCompareSessionArtifactExpectationEntry = React.useMemo(() => {
    if (!selectedReplayableCompareSession) {
      return buildPlannedCompareArtifactExpectationEntry("-");
    }
    const pairId = String(
      selectedReplayableCompareSession.id
      || selectedReplayableCompareSession.pairId
      || makeCompareReplayPairId(
        selectedReplayableCompareSession.baselinePresetId,
        selectedReplayableCompareSession.targetPresetId
      )
    ).trim();
    const stored = normalizeCompareArtifactExpectationEntry(comparePairArtifactExpectationById[pairId]);
    if (stored.summaryText || stored.detailText) {
      return stored;
    }
    return buildPlannedCompareArtifactExpectationEntry(selectedReplayableCompareSession.pairLabel);
  }, [comparePairArtifactExpectationById, selectedReplayableCompareSession]);
  const selectedReplayableCompareSessionArtifactExpectationSummaryText = React.useMemo(
    () => `selected_history_artifact_expectation: ${String(selectedReplayableCompareSessionArtifactExpectationEntry.summaryText || "-")}`,
    [selectedReplayableCompareSessionArtifactExpectationEntry]
  );
  const selectedReplayableCompareSessionArtifactExpectationText = React.useMemo(
    () => String(
      selectedReplayableCompareSessionArtifactExpectationEntry.detailText
      || buildPlannedCompareArtifactExpectationEntry(selectedReplayableCompareSession?.pairLabel).detailText
      || "-"
    ),
    [selectedReplayableCompareSession?.pairLabel, selectedReplayableCompareSessionArtifactExpectationEntry]
  );
  const selectedReplayableCompareSessionMetaText = React.useMemo(() => {
    if (!selectedReplayableCompareSession) {
      return "selected_history_pair_meta: -";
    }
    return [
      `selected_history_pair_meta: pinned=${selectedReplayableCompareSession.pinned === true}`,
      `custom_label=${String(selectedReplayableCompareSession.customLabel || "-")}`,
    ].join(" | ");
  }, [selectedReplayableCompareSession]);
  const selectedReplayableCompareSessionRetentionText = React.useMemo(
    () => buildCompareSessionSelectedPairRetentionText(
      compareSessionHistory,
      compareReplayPairMetaById,
      compareSessionRetentionPolicy,
      selectedReplayableCompareSession
    ),
    [
      compareReplayPairMetaById,
      compareSessionHistory,
      compareSessionRetentionPolicy,
      selectedReplayableCompareSession,
    ]
  );
  const managedCompareReplayPairCount = React.useMemo(
    () => Object.values(compareReplayPairMetaById || {}).filter((row) => {
      const meta = normalizeCompareReplayPairMetaEntry(row);
      return meta.pinned === true || meta.customLabel !== "";
    }).length,
    [compareReplayPairMetaById]
  );

  React.useEffect(() => {
    const currentPolicy = normalizeCompareSessionRetentionPolicy(
      compareSessionRetentionPolicy,
      COMPARE_SESSION_RETENTION_POLICY_DEFAULT
    );
    const currentExtraCount = countCompareReplayPairOptionsByRetentionState(compareReplayPairOptions, "retained_extra");
    const snapshot = compareSessionRetentionSnapshotRef.current || {
      initialized: false,
      extraCount: 0,
      policy: currentPolicy,
    };
    if (compareSessionHistory.length === 0 && compareReplayPairOptions.length === 0) {
      compareSessionRetentionSnapshotRef.current = {
        initialized: true,
        extraCount: 0,
        policy: currentPolicy,
      };
      return;
    }
    if (snapshot.initialized !== true) {
      compareSessionRetentionSnapshotRef.current = {
        initialized: true,
        extraCount: currentExtraCount,
        policy: currentPolicy,
      };
      return;
    }
    const previousExtraCount = Number(snapshot.extraCount || 0);
    const policyChanged = String(snapshot.policy || "") !== currentPolicy;
    const extraChanged = previousExtraCount !== currentExtraCount;
    if (policyChanged || extraChanged) {
      if (previousExtraCount === 0 && currentExtraCount > 0) {
        setCompareSessionRetentionGroupHintText(
          `retention_group_hint: Extra Preserved shown under ${currentPolicy} | previous=${previousExtraCount} | current=${currentExtraCount}`
        );
      } else if (previousExtraCount > 0 && currentExtraCount === 0) {
        setCompareSessionRetentionGroupHintText(
          `retention_group_hint: Extra Preserved hidden under ${currentPolicy} | previous=${previousExtraCount} | current=${currentExtraCount}`
        );
      } else if (policyChanged) {
        setCompareSessionRetentionGroupHintText(
          `retention_group_hint: unchanged under ${currentPolicy} | extra_preserved=${currentExtraCount}`
        );
      } else {
        setCompareSessionRetentionGroupHintText(
          `retention_group_hint: Extra Preserved updated under ${currentPolicy} | previous=${previousExtraCount} | current=${currentExtraCount}`
        );
      }
    }
    compareSessionRetentionSnapshotRef.current = {
      initialized: true,
      extraCount: currentExtraCount,
      policy: currentPolicy,
    };
  }, [compareReplayPairOptions, compareSessionHistory.length, compareSessionRetentionPolicy]);

  React.useEffect(() => {
    const selectedId = String(selectedCompareReplayPairId || "").trim();
    const firstId = String(compareReplayPairOptions[0]?.id || "").trim();
    const hasSelected = selectedId !== ""
      && compareReplayPairOptions.some((row) => String(row?.id || "") === selectedId);
    if (hasSelected) return;
    if (selectedId === firstId) return;
    setSelectedCompareReplayPairId(firstId);
  }, [compareReplayPairOptions, selectedCompareReplayPairId]);

  React.useEffect(() => {
    const expandedId = String(expandedPinnedCompareQuickActionId || "").trim();
    if (!expandedId) return;
    const stillExists = pinnedCompareQuickActionOptions.some((row) => String(row?.id || row?.pairId || "").trim() === expandedId);
    if (stillExists) return;
    setExpandedPinnedCompareQuickActionId("");
  }, [expandedPinnedCompareQuickActionId, pinnedCompareQuickActionOptions]);

  React.useEffect(() => {
    const nextDraft = String(
      selectedReplayableCompareSession?.customLabel
      || selectedReplayableCompareSession?.pairLabel
      || ""
    );
    setSelectedCompareReplayPairLabelDraft(nextDraft);
  }, [
    selectedReplayableCompareSession?.customLabel,
    selectedReplayableCompareSession?.id,
    selectedReplayableCompareSession?.pairLabel,
  ]);

  React.useEffect(() => {
    saveCompareSessionPrefs({
      history: compareSessionHistory,
      pairMetaById: compareReplayPairMetaById,
      pairArtifactExpectationById: comparePairArtifactExpectationById,
      selectedReplayPairId: selectedCompareReplayPairId,
      retentionPolicy: compareSessionRetentionPolicy,
    });
  }, [
    comparePairArtifactExpectationById,
    compareReplayPairMetaById,
    compareSessionHistory,
    compareSessionRetentionPolicy,
    selectedCompareReplayPairId,
  ]);

  React.useEffect(() => {
    const normalized = buildCompareSessionRetainedState({
      history: compareSessionHistory,
      pairMetaById: compareReplayPairMetaById,
      pairArtifactExpectationById: comparePairArtifactExpectationById,
      selectedReplayPairId: selectedCompareReplayPairId,
      retentionPolicy: compareSessionRetentionPolicy,
    });
    const historyChanged = JSON.stringify(normalized.history) !== JSON.stringify(compareSessionHistory);
    const metaChanged = JSON.stringify(normalized.pairMetaById) !== JSON.stringify(compareReplayPairMetaById || {});
    const artifactChanged = JSON.stringify(normalized.pairArtifactExpectationById) !== JSON.stringify(comparePairArtifactExpectationById || {});
    const selectedChanged = String(normalized.selectedReplayPairId || "") !== String(selectedCompareReplayPairId || "");
    const retentionChanged = String(normalized.retentionPolicy || "") !== String(compareSessionRetentionPolicy || "");
    if (!historyChanged && !metaChanged && !artifactChanged && !selectedChanged && !retentionChanged) {
      return;
    }
    applyCompareSessionState(normalized);
  }, [
    applyCompareSessionState,
    comparePairArtifactExpectationById,
    compareReplayPairMetaById,
    compareSessionHistory,
    compareSessionRetentionPolicy,
    selectedCompareReplayPairId,
  ]);

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
    runtimeBackendType,
    runtimeProviderSpec,
    runtimeRequiredModulesText,
    runtimeFailurePolicy,
    runtimeSimulationMode,
    runtimeMultiplexingMode,
    runtimeBpmPhaseCodeText,
    runtimeMultiplexingPlanJson,
    runtimeDevice,
    runtimeLicenseTier,
    runtimeLicenseFile,
    runtimeTxFfdFilesText,
    runtimeRxFfdFilesText,
    runtimeMitsubaEgoOriginText,
    runtimeMitsubaChirpIntervalText,
    runtimeMitsubaMinRangeText,
    runtimeMitsubaSpheresJson,
    runtimePoSbrRepoRoot,
    runtimePoSbrGeometryPath,
    runtimePoSbrChirpIntervalText,
    runtimePoSbrBouncesText,
    runtimePoSbrRaysPerLambdaText,
    runtimePoSbrAlphaDegText,
    runtimePoSbrPhiDegText,
    runtimePoSbrThetaDegText,
    runtimePoSbrRadialVelocityText,
    runtimePoSbrMinRangeText,
    runtimePoSbrMaterialTag,
    runtimePoSbrPathIdPrefix,
    runtimePoSbrComponentsJson,
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

  const runDecisionRegressionSession = React.useCallback(async () => {
    const currentRunIdRaw = String(
      graphRunSummary?.graph_run_id || graphRunSummary?.run_id || ""
    ).trim();
    const currentRunId = currentRunIdRaw.startsWith("run_") ? currentRunIdRaw : "";
    const currentSummary = String(graphRunSummary?.outputs?.graph_run_summary_json || "").trim();
    const compareRunIdRaw = String(compareGraphRunId || "").trim();
    const compareRunId = compareRunIdRaw.startsWith("run_") ? compareRunIdRaw : "";
    const compareSummary = String(
      compareGraphRunSummary?.outputs?.graph_run_summary_json || ""
    ).trim();
    const baseline = String(baselineId || "").trim();

    if (!baseline) {
      setStatus("baseline id is required for regression session", "status-warn");
      return;
    }
    if (!currentRunIdRaw && !currentSummary) {
      setStatus("run graph first before regression session", "status-warn");
      return;
    }

    const candidatesRaw = [];
    if (compareRunId || compareSummary) {
      candidatesRaw.push({
        label: "compare",
        run_id: compareRunId || undefined,
        summary_json: compareSummary || undefined,
      });
    }
    if (currentRunId || currentSummary) {
      candidatesRaw.push({
        label: "current",
        run_id: currentRunId || undefined,
        summary_json: currentSummary || undefined,
      });
    }
    const seen = new Set();
    const candidates = candidatesRaw.filter((row) => {
      const key = `${String(row.run_id || "")}::${String(row.summary_json || "")}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
    if (candidates.length === 0) {
      setStatus("no candidates available for regression session", "status-warn");
      return;
    }

    const sessionId = `dssn_${Date.now()}`;
    setStatus(`running regression session: ${sessionId}`, "status-warn");
    try {
      const payload = await runRegressionSession(apiBase, {
        session_id: sessionId,
        baseline_id: baseline,
        candidates,
        stop_on_first_fail: false,
        overwrite: true,
        note: "decision pane quick session",
        tag: "graph_lab_decision_pane",
      });
      const row = payload.regression_session || {};
      setLastRegressionSession(row);
      setDecisionOpsStatusText(
        `regression_session_id=${String(row.session_id || sessionId)} | evaluated=${Number(row.evaluated_candidate_count || 0)} | held=${Number(row.held_count || 0)} | recommendation=${String(row.recommendation || "-")}`
      );
      setStatus(`regression session completed: ${String(row.session_id || sessionId)}`, "status-ok");
    } catch (err) {
      setDecisionOpsStatusText(`regression_session_failed: ${String(err.message || err)}`);
      setStatus(`regression session failed: ${String(err.message || err)}`, "status-err");
    }
  }, [
    apiBase,
    baselineId,
    compareGraphRunId,
    compareGraphRunSummary,
    graphRunSummary,
    setStatus,
  ]);

  const runPresetPairTrackCompare = React.useCallback(async (options) => {
    const opts = options && typeof options === "object" ? options : {};
    const baselinePresetId = String(
      opts.baselinePresetId || trackCompareBaselinePresetId || RUNTIME_PURPOSE_PRESET_LOW_FIDELITY
    ).trim() || RUNTIME_PURPOSE_PRESET_LOW_FIDELITY;
    const targetPresetId = String(
      opts.targetPresetId || trackCompareTargetPresetId || RUNTIME_PURPOSE_PRESET_CURRENT_CONFIG
    ).trim() || RUNTIME_PURPOSE_PRESET_CURRENT_CONFIG;
    const baselinePresetLabel = getRuntimePurposePresetLabel(baselinePresetId);
    const targetPresetLabel = targetPresetId === RUNTIME_PURPOSE_PRESET_CURRENT_CONFIG
      ? String(configuredRuntimeSummary.trackLabel || getRuntimePurposePresetLabel(targetPresetId))
      : getRuntimePurposePresetLabel(targetPresetId);
    setTrackCompareRunnerStatusText(
      `track_compare_runner: mode=preset_pair | baseline_preset=${baselinePresetId} | target_preset=${targetPresetId} | phase=baseline`
    );
    setDecisionOpsStatusText(
      `track_compare_runner: mode=preset_pair | baseline_preset=${baselinePresetId} | target_preset=${targetPresetId} | phase=baseline`
    );
    setStatus(`running preset-pair compare: ${baselinePresetLabel} -> ${targetPresetLabel}`, "status-warn");

    const baselineOverrides = buildRuntimePurposePresetOverrides(baselinePresetId);
    const lowResult = await runGraphViaApi({
      runModeOverride: "sync",
      tag: `graph_lab_track_compare_${baselinePresetId}`,
      runtimeOverrides: baselineOverrides || undefined,
    });
    if (!lowResult?.ok || !lowResult?.summary) {
      const lowError = String(lowResult?.error || lowResult?.status || "unknown");
      const blocked = isRuntimeBlockedError(lowError);
      setTrackCompareRunnerStatusText(
        `${blocked ? "track_compare_runner_blocked" : "track_compare_runner_failed"}: mode=preset_pair | phase=baseline | baseline_preset=${baselinePresetId} | error=${lowError}`
      );
      setDecisionOpsStatusText(
        `${blocked ? "track_compare_runner_blocked" : "track_compare_runner_failed"}: mode=preset_pair | phase=baseline | baseline_preset=${baselinePresetId} | error=${lowError}`
      );
      appendCompareSession({
        source: "preset_pair",
        status: blocked ? "blocked" : "failed",
        pairLabel: `${baselinePresetLabel} -> ${targetPresetLabel}`,
        baselinePresetId,
        targetPresetId,
        phase: "baseline",
        note: lowError,
      });
      setStatus(
        blocked ? `track compare blocked at baseline preset: ${baselinePresetLabel}` : `track compare failed at baseline preset: ${baselinePresetLabel}`,
        blocked ? "status-warn" : "status-err"
      );
      return;
    }

    const compareRunId = String(
      lowResult.graphRunId || lowResult.summary?.graph_run_id || lowResult.summary?.run_id || ""
    ).trim();
    setCompareGraphRunId(compareRunId);
    setCompareGraphRunSummary(lowResult.summary);
    setCompareRunPinnedManual(true);
    setCompareAutoSkipForRunId("");
    setCompareRunStatusText(
      `compare_mode=runner_preset_pair | baseline_preset=${baselinePresetId} | run=${compareRunId || "-"} | status=${String(lowResult.status || lowResult.summary?.status || "completed")}`
    );
    if (targetPresetId !== RUNTIME_PURPOSE_PRESET_CURRENT_CONFIG) {
      applyRuntimePurposePresetToUi(targetPresetId);
    }
    setTrackCompareRunnerStatusText(
      `track_compare_runner: mode=preset_pair | baseline_ready=${compareRunId || "-"} | baseline_preset=${baselinePresetId} | target_preset=${targetPresetId} | phase=current`
    );
    setDecisionOpsStatusText(
      `track_compare_runner: mode=preset_pair | baseline_ready=${compareRunId || "-"} | baseline_preset=${baselinePresetId} | target_preset=${targetPresetId} | phase=current`
    );

    const targetOverrides = buildRuntimePurposePresetOverrides(targetPresetId);
    const currentResult = await runGraphViaApi({
      runModeOverride: "sync",
      tag: `graph_lab_track_compare_${targetPresetId}`,
      runtimeOverrides: targetOverrides || undefined,
    });
    if (!currentResult?.ok || !currentResult?.summary) {
      const currentError = String(currentResult?.error || currentResult?.status || "unknown");
      const blocked = isRuntimeBlockedError(currentError);
      setTrackCompareRunnerStatusText(
        `${blocked ? "track_compare_runner_blocked" : "track_compare_runner_failed"}: mode=preset_pair | phase=current | baseline_preset=${baselinePresetId} | target_preset=${targetPresetId} | compare=${compareRunId || "-"} | error=${currentError}`
      );
      setDecisionOpsStatusText(
        `${blocked ? "track_compare_runner_blocked" : "track_compare_runner_failed"}: mode=preset_pair | phase=current | baseline_preset=${baselinePresetId} | target_preset=${targetPresetId} | compare=${compareRunId || "-"} | error=${currentError}`
      );
      appendCompareSession({
        source: "preset_pair",
        status: blocked ? "blocked" : "failed",
        pairLabel: `${baselinePresetLabel} -> ${targetPresetLabel}`,
        baselinePresetId,
        targetPresetId,
        phase: "current",
        compareRunId,
        note: currentError,
      });
      setStatus(
        blocked ? `track compare blocked at target preset: ${targetPresetLabel}` : `track compare failed at target preset: ${targetPresetLabel}`,
        blocked ? "status-warn" : "status-err"
      );
      return;
    }

    const currentRunId = String(
      currentResult.graphRunId || currentResult.summary?.graph_run_id || currentResult.summary?.run_id || ""
    ).trim();
    const compareAssessment = buildRunCompareSummary(currentResult.summary, lowResult.summary);
    const pairId = makeCompareReplayPairId(baselinePresetId, targetPresetId);
    const observedArtifactExpectation = buildObservedCompareArtifactExpectationEntry(
      `${baselinePresetLabel} -> ${targetPresetLabel}`,
      currentResult.summary,
      lowResult.summary
    );
    if (pairId && observedArtifactExpectation) {
      setComparePairArtifactExpectationById((prev) => ({
        ...(prev && typeof prev === "object" ? prev : {}),
        [pairId]: observedArtifactExpectation,
      }));
    }
    appendCompareSession({
      source: "preset_pair",
      status: "ready",
      pairLabel: `${baselinePresetLabel} -> ${targetPresetLabel}`,
      baselinePresetId,
      targetPresetId,
      phase: "current",
      compareRunId,
      currentRunId,
      assessment: String(compareAssessment.assessment || "-"),
    });
    setTrackCompareRunnerStatusText(
      `track_compare_runner=ready | mode=preset_pair | baseline_preset=${baselinePresetId} | target_preset=${targetPresetId} | compare=${compareRunId || "-"} | current=${currentRunId || "-"}`
    );
    setDecisionOpsStatusText(
      `track_compare_runner=ready | mode=preset_pair | baseline_preset=${baselinePresetId} | target_preset=${targetPresetId} | compare=${compareRunId || "-"} | current=${currentRunId || "-"}`
    );
    setStatus(`track compare ready: ${baselinePresetLabel} -> ${targetPresetLabel}`, "status-ok");
  }, [
    configuredRuntimeSummary.trackLabel,
    appendCompareSession,
    applyRuntimePurposePresetToUi,
    runGraphViaApi,
    setComparePairArtifactExpectationById,
    setStatus,
    trackCompareBaselinePresetId,
    trackCompareTargetPresetId,
    setTrackCompareRunnerStatusText,
  ]);

  const runLowVsCurrentTrackCompare = React.useCallback(async () => {
    return runPresetPairTrackCompare({
      baselinePresetId: RUNTIME_PURPOSE_PRESET_LOW_FIDELITY,
      targetPresetId: RUNTIME_PURPOSE_PRESET_CURRENT_CONFIG,
    });
  }, [runPresetPairTrackCompare]);

  const applyCompareSessionReplayPair = React.useCallback((pair) => {
    const row = pair && typeof pair === "object" ? pair : null;
    if (!row) {
      setStatus("no replayable compare session recorded yet", "status-warn");
      return false;
    }
    setTrackCompareBaselinePresetId(String(row.baselinePresetId || RUNTIME_PURPOSE_PRESET_LOW_FIDELITY));
    setTrackCompareTargetPresetId(String(row.targetPresetId || RUNTIME_PURPOSE_PRESET_CURRENT_CONFIG));
    setStatus(`applied compare session pair: ${String(row.pairLabel || "-")}`, "status-ok");
    return true;
  }, [setStatus]);

  const runCompareSessionReplayPair = React.useCallback(async (pair) => {
    const row = pair && typeof pair === "object" ? pair : null;
    if (!row) {
      setStatus("no replayable compare session recorded yet", "status-warn");
      return;
    }
    setTrackCompareBaselinePresetId(String(row.baselinePresetId || RUNTIME_PURPOSE_PRESET_LOW_FIDELITY));
    setTrackCompareTargetPresetId(String(row.targetPresetId || RUNTIME_PURPOSE_PRESET_CURRENT_CONFIG));
    return runPresetPairTrackCompare({
      baselinePresetId: row.baselinePresetId,
      targetPresetId: row.targetPresetId,
    });
  }, [runPresetPairTrackCompare, setStatus]);

  const applyLatestCompareSessionPair = React.useCallback(() => {
    return applyCompareSessionReplayPair(latestReplayableCompareSession);
  }, [applyCompareSessionReplayPair, latestReplayableCompareSession]);

  const runLatestCompareSessionPair = React.useCallback(async () => {
    return runCompareSessionReplayPair(latestReplayableCompareSession);
  }, [latestReplayableCompareSession, runCompareSessionReplayPair]);

  const applySelectedCompareSessionPair = React.useCallback(() => {
    return applyCompareSessionReplayPair(selectedReplayableCompareSession);
  }, [applyCompareSessionReplayPair, selectedReplayableCompareSession]);

  const runSelectedCompareSessionPair = React.useCallback(async () => {
    return runCompareSessionReplayPair(selectedReplayableCompareSession);
  }, [runCompareSessionReplayPair, selectedReplayableCompareSession]);

  const applyPinnedCompareQuickAction = React.useCallback((pairId) => {
    const selectedId = String(pairId || "").trim();
    const row = pinnedCompareQuickActionOptions.find((item) => String(item?.id || item?.pairId || "").trim() === selectedId) || null;
    if (!row) {
      setStatus("selected pinned quick action is unavailable", "status-warn");
      return false;
    }
    setSelectedCompareReplayPairId(String(row.id || row.pairId || ""));
    return applyCompareSessionReplayPair(row);
  }, [
    applyCompareSessionReplayPair,
    pinnedCompareQuickActionOptions,
    setStatus,
  ]);

  const runPinnedCompareQuickAction = React.useCallback(async (pairId) => {
    const selectedId = String(pairId || "").trim();
    const row = pinnedCompareQuickActionOptions.find((item) => String(item?.id || item?.pairId || "").trim() === selectedId) || null;
    if (!row) {
      setStatus("selected pinned quick action is unavailable", "status-warn");
      return;
    }
    setSelectedCompareReplayPairId(String(row.id || row.pairId || ""));
    return runCompareSessionReplayPair(row);
  }, [
    pinnedCompareQuickActionOptions,
    runCompareSessionReplayPair,
    setStatus,
  ]);

  const togglePinnedCompareQuickActionExpanded = React.useCallback((pairId) => {
    const selectedId = String(pairId || "").trim();
    if (!selectedId) return;
    setExpandedPinnedCompareQuickActionId((prev) => String(prev || "").trim() === selectedId ? "" : selectedId);
  }, []);

  const saveSelectedCompareSessionPairLabel = React.useCallback(() => {
    const selectedPair = selectedReplayableCompareSession;
    if (!selectedPair) {
      setStatus("no replayable compare session selected", "status-warn");
      return;
    }
    const pairId = String(selectedPair.id || selectedPair.pairId || "").trim();
    if (!pairId) {
      setStatus("selected compare session pair id is missing", "status-warn");
      return;
    }
    const nextLabel = normalizeCompareSessionField(selectedCompareReplayPairLabelDraft, 160);
    setCompareReplayPairMetaById((prev) => {
      const next = { ...(prev || {}) };
      const prior = normalizeCompareReplayPairMetaEntry(next[pairId]);
      const merged = {
        customLabel: nextLabel,
        pinned: prior.pinned === true,
      };
      if (!merged.customLabel && merged.pinned !== true) {
        delete next[pairId];
      } else {
        next[pairId] = merged;
      }
      return next;
    });
    setStatus(nextLabel
      ? `saved selected history pair label: ${nextLabel}`
      : "cleared selected history pair label",
    "status-ok");
  }, [
    selectedCompareReplayPairLabelDraft,
    selectedReplayableCompareSession,
    setStatus,
  ]);

  const togglePinSelectedCompareSessionPair = React.useCallback(() => {
    const selectedPair = selectedReplayableCompareSession;
    if (!selectedPair) {
      setStatus("no replayable compare session selected", "status-warn");
      return;
    }
    const pairId = String(selectedPair.id || selectedPair.pairId || "").trim();
    if (!pairId) {
      setStatus("selected compare session pair id is missing", "status-warn");
      return;
    }
    let nextPinned = false;
    setCompareReplayPairMetaById((prev) => {
      const next = { ...(prev || {}) };
      const prior = normalizeCompareReplayPairMetaEntry(next[pairId]);
      nextPinned = prior.pinned !== true;
      const merged = {
        customLabel: prior.customLabel,
        pinned: nextPinned,
      };
      if (!merged.customLabel && merged.pinned !== true) {
        delete next[pairId];
      } else {
        next[pairId] = merged;
      }
      return next;
    });
    setStatus(
      `${nextPinned ? "pinned" : "unpinned"} selected history pair: ${String(selectedPair.pairLabel || "-")}`,
      "status-ok"
    );
  }, [selectedReplayableCompareSession, setStatus]);

  const deleteSelectedCompareSessionPair = React.useCallback(() => {
    const selectedPair = selectedReplayableCompareSession;
    if (!selectedPair) {
      setStatus("no replayable compare session selected", "status-warn");
      return;
    }
    const pairId = String(selectedPair.id || selectedPair.pairId || "").trim();
    if (!pairId) {
      setStatus("selected compare session pair id is missing", "status-warn");
      return;
    }
    const nextMeta = { ...(compareReplayPairMetaById || {}) };
    const nextArtifactExpectation = { ...(comparePairArtifactExpectationById || {}) };
    delete nextMeta[pairId];
    delete nextArtifactExpectation[pairId];
    applyCompareSessionState({
      history: (Array.isArray(compareSessionHistory) ? compareSessionHistory : []).filter((row) => {
        const replayPair = getCompareSessionReplayPair(row);
        return String(replayPair?.pairId || "") !== pairId;
      }),
      pairMetaById: nextMeta,
      pairArtifactExpectationById: nextArtifactExpectation,
      selectedReplayPairId: selectedCompareReplayPairId === pairId ? "" : selectedCompareReplayPairId,
      retentionPolicy: compareSessionRetentionPolicy,
    });
    setStatus(`deleted history pair: ${String(selectedPair.pairLabel || "-")}`, "status-ok");
  }, [
    applyCompareSessionState,
    comparePairArtifactExpectationById,
    compareReplayPairMetaById,
    compareSessionHistory,
    compareSessionRetentionPolicy,
    selectedCompareReplayPairId,
    selectedReplayableCompareSession,
    setStatus,
  ]);

  const updateCompareSessionRetentionPolicy = React.useCallback((nextPolicyInput) => {
    const nextPolicy = normalizeCompareSessionRetentionPolicy(
      nextPolicyInput,
      COMPARE_SESSION_RETENTION_POLICY_DEFAULT
    );
    applyCompareSessionState({
      history: compareSessionHistory,
      pairMetaById: compareReplayPairMetaById,
      pairArtifactExpectationById: comparePairArtifactExpectationById,
      selectedReplayPairId: selectedCompareReplayPairId,
      retentionPolicy: nextPolicy,
    });
    setStatus(
      `compare history retention updated: ${nextPolicy} (keep_latest=${getCompareSessionRetentionLimit(nextPolicy)}, preserve_scope=${getCompareSessionRetentionPreserveMode(nextPolicy)}, preserve_pinned=${shouldCompareSessionRetentionPreservePinned(nextPolicy)}, preserve_saved=${shouldCompareSessionRetentionPreserveSaved(nextPolicy)})`,
      "status-ok"
    );
  }, [
    applyCompareSessionState,
    comparePairArtifactExpectationById,
    compareReplayPairMetaById,
    compareSessionHistory,
    selectedCompareReplayPairId,
    setStatus,
  ]);

  const clearAllCompareSessionHistory = React.useCallback(() => {
    applyCompareSessionState({
      history: [],
      pairMetaById: {},
      pairArtifactExpectationById: {},
      selectedReplayPairId: "",
      retentionPolicy: compareSessionRetentionPolicy,
    });
    setStagedCompareSessionImport(null);
    setCompareSessionTransferStatusText("compare history cleared");
    setCompareSessionTransferBadgeRows(buildCompareSessionTransferBadges({ direction: "idle" }));
    setCompareSessionRetentionGroupHintText("retention_group_hint: none");
    compareSessionRetentionSnapshotRef.current = {
      initialized: false,
      extraCount: 0,
      policy: compareSessionRetentionPolicy,
    };
    setStatus("compare history cleared", "status-ok");
  }, [applyCompareSessionState, compareSessionRetentionPolicy, setStatus]);

  const exportCompareSessionHistory = React.useCallback(() => {
    const jsonText = serializeCompareSessionExportBundle({
      history: compareSessionHistory,
      pairMetaById: compareReplayPairMetaById,
      pairArtifactExpectationById: comparePairArtifactExpectationById,
      selectedReplayPairId: selectedCompareReplayPairId,
      retentionPolicy: compareSessionRetentionPolicy,
    });
    try {
      if (typeof window === "undefined" || typeof document === "undefined" || !window.URL) {
        setCompareSessionTransferStatusText("compare history export prepared (download unavailable)");
        setCompareSessionTransferBadgeRows(buildCompareSessionTransferBadges({
          direction: "export",
          schemaVersion: COMPARE_SESSION_EXPORT_SCHEMA_VERSION,
          compatibility: "exact",
        }));
        setStatus("compare history exported to memory buffer", "status-ok");
        return;
      }
      const blob = new Blob([jsonText], { type: "application/json;charset=utf-8" });
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      const ts = new Date().toISOString().replace(/[:.]/g, "-");
      anchor.href = url;
      anchor.download = `graph_lab_compare_history_${ts}.json`;
      document.body.appendChild(anchor);
      anchor.click();
      document.body.removeChild(anchor);
      window.URL.revokeObjectURL(url);
      setCompareSessionTransferStatusText(
        `exported ${Number(compareSessionHistory.length || 0)} history row(s), ${Number(managedCompareReplayPairCount || 0)} managed pair(s), and ${Number(Object.keys(comparePairArtifactExpectationById || {}).length || 0)} artifact expectation snapshot(s) | schema=${COMPARE_SESSION_EXPORT_SCHEMA_VERSION}`
      );
      setCompareSessionTransferBadgeRows(buildCompareSessionTransferBadges({
        direction: "export",
        schemaVersion: COMPARE_SESSION_EXPORT_SCHEMA_VERSION,
        compatibility: "exact",
      }));
      setStatus(`compare history exported: schema=${COMPARE_SESSION_EXPORT_SCHEMA_VERSION}`, "status-ok");
    } catch (err) {
      setCompareSessionTransferStatusText(`compare history export failed: ${String(err.message || err)}`);
      setCompareSessionTransferBadgeRows(buildCompareSessionTransferBadges({
        direction: "export",
        failed: true,
      }));
      setStatus(`compare history export failed: ${String(err.message || err)}`, "status-err");
    }
  }, [
    comparePairArtifactExpectationById,
    compareReplayPairMetaById,
    compareSessionHistory,
    compareSessionRetentionPolicy,
    managedCompareReplayPairCount,
    selectedCompareReplayPairId,
    setStatus,
  ]);

  const triggerCompareSessionImportFilePick = React.useCallback(() => {
    const input = compareSessionImportFileInputRef.current;
    if (!input || typeof input.click !== "function") return;
    input.click();
  }, []);

  const previewCompareSessionHistoryText = React.useCallback((rawText, sourceLabel) => {
    try {
      const imported = parseCompareSessionImportBundle(rawText);
      const importSchema = summarizeCompareSessionSchemaCompatibility(imported.schemaVersion);
      setStagedCompareSessionImport({
        sourceLabel: normalizeCompareSessionField(sourceLabel, 192) || "compare_history.json",
        imported,
      });
      setCompareSessionTransferStatusText(
        `compare history import preview ready: ${String(sourceLabel || "text")} | rows=${Number(imported.history.length || 0)} | schema=${importSchema.schemaVersion} | compatibility=${importSchema.compatibility} | apply merge to persist`
      );
      setCompareSessionTransferBadgeRows(buildCompareSessionTransferBadges({
        direction: "import",
        schemaVersion: importSchema.schemaVersion,
        compatibility: importSchema.compatibility,
      }));
      setStatus(
        `compare history import preview ready: ${String(sourceLabel || "text")} (schema=${importSchema.schemaVersion}, compatibility=${importSchema.compatibility})`,
        "status-warn"
      );
    } catch (err) {
      setStagedCompareSessionImport(null);
      setCompareSessionTransferStatusText(`compare history import failed: ${String(err.message || err)}`);
      setCompareSessionTransferBadgeRows(buildCompareSessionTransferBadges({
        direction: "import",
        failed: true,
      }));
      setStatus(`compare history import failed: ${String(err.message || err)}`, "status-err");
    }
  }, [setStatus]);

  const applyCompareSessionImportPreview = React.useCallback(() => {
    const staged = stagedCompareSessionImport;
    if (!staged || !staged.imported || typeof staged.imported !== "object") {
      setStatus("stage compare history import first", "status-warn");
      return;
    }
    try {
      const imported = staged.imported;
      const sourceLabel = normalizeCompareSessionField(staged.sourceLabel, 192) || "text";
      const importSchema = summarizeCompareSessionSchemaCompatibility(imported.schemaVersion);
      const effectiveRetentionPolicy = normalizeCompareSessionRetentionPolicy(
        imported.retentionPolicy || compareSessionRetentionPolicy,
        COMPARE_SESSION_RETENTION_POLICY_DEFAULT
      );
      applyCompareSessionState({
        history: mergeCompareSessionHistoryEntries(compareSessionHistory, imported.history),
        pairMetaById: {
          ...(compareReplayPairMetaById && typeof compareReplayPairMetaById === "object" ? compareReplayPairMetaById : {}),
          ...(imported.pairMetaById || {}),
        },
        pairArtifactExpectationById: {
          ...(comparePairArtifactExpectationById && typeof comparePairArtifactExpectationById === "object" ? comparePairArtifactExpectationById : {}),
          ...(imported.pairArtifactExpectationById || {}),
        },
        selectedReplayPairId: String(imported.selectedReplayPairId || "").trim() || selectedCompareReplayPairId,
        retentionPolicy: effectiveRetentionPolicy,
      });
      setStagedCompareSessionImport(null);
      setCompareSessionTransferStatusText(
        `imported ${Number(imported.history.length || 0)} history row(s) and ${Number(Object.keys(imported.pairArtifactExpectationById || {}).length || 0)} artifact expectation snapshot(s) from ${sourceLabel} | schema=${importSchema.schemaVersion} | compatibility=${importSchema.compatibility}`
      );
      setCompareSessionTransferBadgeRows(buildCompareSessionTransferBadges({
        direction: "import",
        schemaVersion: importSchema.schemaVersion,
        compatibility: importSchema.compatibility,
      }));
      setStatus(
        `compare history imported: ${sourceLabel} (schema=${importSchema.schemaVersion}, compatibility=${importSchema.compatibility})`,
        "status-ok"
      );
    } catch (err) {
      setCompareSessionTransferStatusText(`compare history import merge failed: ${String(err.message || err)}`);
      setCompareSessionTransferBadgeRows(buildCompareSessionTransferBadges({
        direction: "import",
        failed: true,
      }));
      setStatus(`compare history import merge failed: ${String(err.message || err)}`, "status-err");
    }
  }, [
    applyCompareSessionState,
    comparePairArtifactExpectationById,
    compareReplayPairMetaById,
    compareSessionHistory,
    compareSessionRetentionPolicy,
    selectedCompareReplayPairId,
    setStatus,
    stagedCompareSessionImport,
  ]);

  const clearCompareSessionImportPreview = React.useCallback(() => {
    if (!stagedCompareSessionImport) {
      setStatus("no staged compare history import preview", "status-warn");
      return;
    }
    setStagedCompareSessionImport(null);
    setCompareSessionTransferStatusText("compare history import preview cleared");
    setCompareSessionTransferBadgeRows(buildCompareSessionTransferBadges({ direction: "idle" }));
    setStatus("compare history import preview cleared", "status-ok");
  }, [setStatus, stagedCompareSessionImport]);

  const handleCompareSessionImportFileChange = React.useCallback((evt) => {
    const file = evt?.target?.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      previewCompareSessionHistoryText(String(reader.result || ""), String(file.name || "compare_history.json"));
    };
    reader.onerror = () => {
      const label = String(file.name || "-");
      setStagedCompareSessionImport(null);
      setCompareSessionTransferStatusText(`failed to read compare history file: ${label}`);
      setStatus(`compare history import read failed: ${label}`, "status-err");
    };
    reader.readAsText(file);
    if (evt?.target) evt.target.value = "";
  }, [previewCompareSessionHistoryText, setStatus]);

  const exportDecisionRegressionSession = React.useCallback(async () => {
    const sessionId = String(lastRegressionSession?.session_id || "").trim();
    if (!sessionId) {
      setStatus("run regression session first", "status-warn");
      return;
    }
    setStatus(`exporting regression session: ${sessionId}`, "status-warn");
    try {
      const payload = await exportRegressionSession(apiBase, {
        session_id: sessionId,
        overwrite: true,
        include_policy_payload: false,
        note: "decision pane export",
        tag: "graph_lab_decision_pane",
      });
      const row = payload.regression_export || {};
      setLastRegressionExport(row);
      setDecisionOpsStatusText(
        `regression_export_id=${String(row.export_id || "-")} | rows=${Number(row.row_count || 0)} | recommendation=${String(row.session_recommendation || "-")}`
      );
      setStatus(`regression export completed: ${String(row.export_id || "-")}`, "status-ok");
    } catch (err) {
      setDecisionOpsStatusText(`regression_export_failed: ${String(err.message || err)}`);
      setStatus(`regression export failed: ${String(err.message || err)}`, "status-err");
    }
  }, [apiBase, lastRegressionSession, setStatus]);

  const decisionSummaryText = React.useMemo(() => {
    const nowIso = new Date().toISOString();
    const currentRunId = String(
      graphRunSummary?.graph_run_id || graphRunSummary?.run_id || ""
    ).trim() || "-";
    const compareRunId = String(compareGraphRunSummary?.graph_run_id || compareGraphRunId || "").trim() || "-";
    const recommendation = String(lastPolicyEval?.recommendation || "unknown");
    const compareRunnerStatus = String(trackCompareRunnerState || "not_run");
    const gateKnown = typeof lastPolicyEval?.gate_failed === "boolean";
    const gateFailed = gateKnown ? Boolean(lastPolicyEval?.gate_failed) : null;
    const decision = gateKnown ? (gateFailed ? "HOLD" : "ADOPT") : "UNKNOWN";
    const failureRows = Array.isArray(lastPolicyEval?.gate_failures) ? lastPolicyEval.gate_failures : [];

    const lines = [
      `generated_at_utc: ${nowIso}`,
      `decision: ${decision}`,
      `recommendation: ${recommendation}`,
      `baseline_id: ${String(baselineId || "-")}`,
      `current_run_id: ${currentRunId}`,
      `compare_run_id: ${compareRunId}`,
      `compare_runner_status: ${compareRunnerStatus}`,
      `selected_preset_pair: ${trackCompareBaselinePresetId} -> ${trackCompareTargetPresetId}`,
      `selected_preset_pair_label: ${trackCompareSelectedPairSummaryText}`,
      `selected_preset_pair_forecast: ${trackCompareSelectedPairForecastText.split("\n").slice(1).join(" | ")}`,
      `compare_session_count: ${Number(compareSessionHistory.length || 0)}`,
      `${compareSessionRetentionPolicySummaryText}`,
      `${compareSessionRetentionGroupHintText}`,
      `${compareSessionRetentionPreviewCompactSummaryText}`,
      `managed_history_pair_count: ${Number(managedCompareReplayPairCount || 0)}`,
      `${pinnedCompareQuickActionSummaryText}`,
      `latest_compare_session: ${latestCompareSessionText}`,
      `${latestReplayableCompareSessionText}`,
      `${selectedReplayableCompareSessionText}`,
      `${selectedReplayableCompareSessionMetaText}`,
      `${String(selectedReplayableCompareSessionRetentionText || "-").split("\n").join(" | ")}`,
      `${selectedReplayableCompareSessionArtifactExpectationSummaryText}`,
      `selected_history_pair_preview: ${selectedReplayableCompareSessionPreviewText.split("\n").slice(1).join(" | ")}`,
      `${compareSessionTransferCompactSummaryText}`,
      `compare_history_transfer: ${String(compareSessionTransferStatusText || "-")}`,
      `${compareSessionImportPreviewCompactSummaryText}`,
      `current_track: ${runtimeSummary.trackLabel}`,
      `compare_track: ${compareRuntimeSummary.trackLabel}`,
      `current_runtime: ${runtimeDiagnostics.badgeLine}`,
      `compare_runtime: ${compareRuntimeDiagnostics.badgeLine}`,
      `compare_assessment: ${runCompareSummary.assessment}`,
      `compare_flags: ${runCompareSummary.flagSummary}`,
      `${artifactInspectorDecisionStatusBadgesText}`,
      `${artifactInspectorDecisionLayoutStateText}`,
      `${artifactInspectorDecisionProbeStateText}`,
      `gate_failure_count: ${Number(failureRows.length || 0)}`,
      `path_count_delta(current-compare): ${runCompareSummary.available ? formatSigned(runCompareSummary.pathCountDelta) : "-"}`,
    ];

    if (runCompareSummary.rdPeakDelta) {
      lines.push(
        `rd_peak_delta(range/doppler): ${formatSigned(runCompareSummary.rdPeakDelta.rangeBinDelta)}/${formatSigned(runCompareSummary.rdPeakDelta.dopplerBinDelta)}`
      );
    }
    if (runCompareSummary.raPeakDelta) {
      lines.push(
        `ra_peak_delta(range/angle): ${formatSigned(runCompareSummary.raPeakDelta.rangeBinDelta)}/${formatSigned(runCompareSummary.raPeakDelta.angleBinDelta)}`
      );
    }
    if (failureRows.length > 0) {
      lines.push("top_failure_evidence:");
      failureRows.slice(0, 3).forEach((row, idx) => {
        const metric = row?.metric ? `(${String(row.metric)})` : "";
        lines.push(
          `- [${Number(idx) + 1}] ${String(row?.rule || "unknown_rule")}${metric} value=${String(row?.value ?? "-")} limit=${String(row?.limit ?? "-")}`
        );
      });
    }
    return lines.join("\n");
  }, [
    baselineId,
    compareSessionHistory.length,
    compareGraphRunId,
    compareGraphRunSummary,
    compareSessionRetentionPolicySummaryText,
    compareSessionRetentionGroupHintText,
    compareSessionRetentionPreviewCompactSummaryText,
    managedCompareReplayPairCount,
    pinnedCompareQuickActionSummaryText,
    runCompareSummary,
    compareRuntimeDiagnostics.badgeLine,
    compareRuntimeSummary.trackLabel,
    compareSessionImportPreviewCompactSummaryText,
    compareSessionTransferCompactSummaryText,
    compareSessionTransferStatusText,
    artifactInspectorDecisionStatusBadgesText,
    artifactInspectorDecisionLayoutStateText,
    artifactInspectorDecisionProbeStateText,
    graphRunSummary,
    latestCompareSessionText,
    latestReplayableCompareSessionText,
    lastPolicyEval,
    runtimeDiagnostics.badgeLine,
    runtimeSummary.trackLabel,
    selectedReplayableCompareSessionText,
    selectedReplayableCompareSessionMetaText,
    selectedReplayableCompareSessionRetentionText,
    selectedReplayableCompareSessionArtifactExpectationSummaryText,
    selectedReplayableCompareSessionPreviewText,
    trackCompareBaselinePresetId,
    trackCompareSelectedPairForecastText,
    trackCompareSelectedPairSummaryText,
    trackCompareTargetPresetId,
    trackCompareRunnerState,
  ]);

  const exportDecisionBriefMd = React.useCallback(() => {
    const nowIso = new Date().toISOString();
    const fileStamp = nowIso.slice(0, 19).replace(/[:T]/g, "_");
    const currentOutputs = graphRunSummary?.outputs && typeof graphRunSummary.outputs === "object"
      ? graphRunSummary.outputs
      : {};
    const compareOutputs = compareGraphRunSummary?.outputs && typeof compareGraphRunSummary.outputs === "object"
      ? compareGraphRunSummary.outputs
      : {};
    const failures = Array.isArray(lastPolicyEval?.gate_failures) ? lastPolicyEval.gate_failures : [];
    const lines = [
      "# Radar Decision Brief",
      "",
      `- generated_at_utc: ${nowIso}`,
      `- graph_id: ${String(graphId || "-")}`,
      "",
      "## Decision Snapshot",
      "```text",
      decisionSummaryText,
      "```",
      "",
      "## Runtime Compare",
      `- selected_preset_pair: ${trackCompareBaselinePresetId} -> ${trackCompareTargetPresetId}`,
      `- selected_preset_pair_label: ${trackCompareSelectedPairSummaryText}`,
      `- current_track: ${runtimeSummary.trackLabel}`,
      `- compare_track: ${compareRuntimeSummary.trackLabel}`,
      `- compare_runner_status: ${String(trackCompareRunnerStatusText || "-")}`,
      `- compare_status: ${String(compareRunStatusText || "-")}`,
      `- ${latestReplayableCompareSessionText}`,
      `- ${selectedReplayableCompareSessionText}`,
      `- ${selectedReplayableCompareSessionMetaText}`,
      `- ${String(selectedReplayableCompareSessionRetentionText || "-").split("\n").join(" | ")}`,
      `- ${selectedReplayableCompareSessionArtifactExpectationSummaryText}`,
      `- ${compareSessionRetentionPolicySummaryText}`,
      `- ${compareSessionRetentionGroupHintText}`,
      `- ${compareSessionRetentionPreviewCompactSummaryText}`,
      `- ${compareSessionTransferCompactSummaryText}`,
      `- ${compareSessionImportPreviewCompactSummaryText}`,
      `- managed_history_pair_count: ${Number(managedCompareReplayPairCount || 0)}`,
      `- ${pinnedCompareQuickActionSummaryText}`,
      "",
      "## Selected Pair Forecast",
      "```text",
      trackCompareSelectedPairForecastText,
      "```",
      "",
      "## Pinned Pair Quick Actions",
      "```text",
      pinnedCompareQuickActionDetailText,
      "```",
      "",
      "## Compare Session History",
      "```text",
      compareSessionRetentionPolicySummaryText,
      compareSessionRetentionGroupHintText,
      compareSessionRetentionPreviewText,
      compareSessionTransferCompactSummaryText,
      "",
      selectedReplayableCompareSessionRetentionText,
      "",
      compareSessionHistoryText,
      "```",
      "",
      "## Compare History Import Preview",
      "```text",
      compareSessionImportPreviewText,
      "```",
      "",
      "## Selected History Pair Preview",
      "```text",
      selectedReplayableCompareSessionPreviewText,
      "```",
      "",
      "## Selected History Pair Artifact Expectation",
      "```text",
      selectedReplayableCompareSessionArtifactExpectationText,
      "```",
      "",
      "### Current Runtime Diagnostics",
      "```text",
      runtimeDiagnostics.summaryText,
      "```",
      "",
      "### Compare Runtime Diagnostics",
      "```text",
      compareRuntimeDiagnostics.summaryText,
      "```",
      "",
      "## Compare Assessment",
      "```text",
      ...runCompareSummary.detailLines,
      "```",
      "",
      "## Artifact Inspector State",
      "```text",
      artifactInspectorDecisionStatusBadgesText,
      artifactInspectorDecisionLayoutStateText,
      artifactInspectorDecisionProbeStateText,
      "```",
      "",
      "## Current Artifacts",
      `- graph_run_summary_json: ${String(currentOutputs.graph_run_summary_json || "-")}`,
      `- radar_map_npz: ${String(currentOutputs.radar_map_npz || "-")}`,
      `- adc_cube_npz: ${String(currentOutputs.adc_cube_npz || "-")}`,
      `- path_list_json: ${String(currentOutputs.path_list_json || "-")}`,
      "",
      "## Compare Artifacts",
      `- graph_run_summary_json: ${String(compareOutputs.graph_run_summary_json || "-")}`,
      `- radar_map_npz: ${String(compareOutputs.radar_map_npz || "-")}`,
      `- adc_cube_npz: ${String(compareOutputs.adc_cube_npz || "-")}`,
      `- path_list_json: ${String(compareOutputs.path_list_json || "-")}`,
      "",
      "## Gate Evidence",
    ];
    if (failures.length === 0) {
      lines.push("- none");
    } else {
      failures.slice(0, 8).forEach((row, idx) => {
        const metric = row?.metric ? ` (${String(row.metric)})` : "";
        lines.push(
          `- [${Number(idx) + 1}] ${String(row?.rule || "unknown_rule")}${metric}: value=${String(row?.value ?? "-")} limit=${String(row?.limit ?? "-")}`
        );
      });
    }
    lines.push(
      "",
      "## Regression Session",
      `- session_id: ${String(lastRegressionSession?.session_id || "-")}`,
      `- session_recommendation: ${String(lastRegressionSession?.recommendation || "-")}`,
      `- export_id: ${String(lastRegressionExport?.export_id || "-")}`,
      `- export_package_json: ${String(lastRegressionExport?.artifacts?.package_json || "-")}`
    );

    const text = lines.join("\n");
    const blob = new Blob([text], { type: "text/markdown;charset=utf-8" });
    const href = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = href;
    a.download = `decision_brief_${String(graphId || "graph")}_${fileStamp}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.setTimeout(() => URL.revokeObjectURL(href), 1000);
    setDecisionOpsStatusText(`decision_brief_exported_at=${nowIso}`);
    setStatus("decision brief exported", "status-ok");
  }, [
    compareGraphRunSummary,
    compareRunStatusText,
    compareSessionHistoryText,
    compareSessionImportPreviewCompactSummaryText,
    compareSessionImportPreviewText,
    compareSessionRetentionPolicySummaryText,
    compareSessionRetentionGroupHintText,
    compareSessionRetentionPreviewCompactSummaryText,
    compareSessionRetentionPreviewText,
    compareSessionTransferCompactSummaryText,
    artifactInspectorDecisionStatusBadgesText,
    artifactInspectorDecisionLayoutStateText,
    artifactInspectorDecisionProbeStateText,
    runCompareSummary,
    compareRuntimeDiagnostics.summaryText,
    compareRuntimeSummary.trackLabel,
    decisionSummaryText,
    graphId,
    graphRunSummary,
    lastPolicyEval,
    lastRegressionExport,
    lastRegressionSession,
    runtimeDiagnostics.summaryText,
    runtimeSummary.trackLabel,
    selectedReplayableCompareSessionText,
    selectedReplayableCompareSessionMetaText,
    selectedReplayableCompareSessionRetentionText,
    selectedReplayableCompareSessionArtifactExpectationSummaryText,
    selectedReplayableCompareSessionArtifactExpectationText,
    selectedReplayableCompareSessionPreviewText,
    managedCompareReplayPairCount,
    setStatus,
    latestReplayableCompareSessionText,
    trackCompareBaselinePresetId,
    pinnedCompareQuickActionDetailText,
    pinnedCompareQuickActionSummaryText,
    trackCompareSelectedPairForecastText,
    trackCompareSelectedPairSummaryText,
    trackCompareTargetPresetId,
    trackCompareRunnerStatusText,
  ]);

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

  const pipelineStages = React.useMemo(() => {
    const hasDesign = Number(nodes.length || 0) > 0;
    const hasRun = Boolean(graphRunSummary && (graphRunSummary.graph_run_id || graphRunSummary.run_id));
    const hasInspect = Boolean(
      hasRun && (
        compareGraphRunSummary
        || (graphRunSummary && typeof graphRunSummary === "object")
      )
    );
    const hasGate = typeof lastPolicyEval?.gate_failed === "boolean";
    const hasExport = Boolean(lastRegressionExport || lastRegressionSession);
    const activeId = hasExport
      ? "export"
      : hasGate
        ? "gate"
        : hasInspect
          ? "inspect"
          : hasRun
            ? "run"
            : "design";
    return [
      { id: "design", label: "Design", done: hasDesign, active: activeId === "design" },
      { id: "run", label: "Run", done: hasRun, active: activeId === "run" },
      { id: "inspect", label: "Inspect", done: hasInspect, active: activeId === "inspect" },
      { id: "gate", label: "Gate", done: hasGate, active: activeId === "gate" },
      { id: "export", label: "Export", done: hasExport, active: activeId === "export" },
    ];
  }, [
    compareGraphRunSummary,
    graphRunSummary,
    lastPolicyEval,
    lastRegressionExport,
    lastRegressionSession,
    nodes.length,
  ]);

  const toggleFocusLeftDrawer = React.useCallback(() => {
    setFocusLeftOpen((prev) => !prev);
  }, []);

  const toggleFocusRightDrawer = React.useCallback(() => {
    setFocusRightOpen((prev) => !prev);
  }, []);

  const closeFocusDrawers = React.useCallback(() => {
    setFocusLeftOpen(false);
    setFocusRightOpen(false);
  }, []);

  const focusAnyOpen = layoutMode === "focus" && (focusLeftOpen || focusRightOpen);
  React.useEffect(() => {
    if (layoutMode !== "focus" || !focusAnyOpen) return undefined;
    const onKeyDown = (event) => {
      if (String(event?.key || "") !== "Escape") return;
      const target = event?.target;
      const tag = String(target?.tagName || "").toLowerCase();
      if (target?.isContentEditable || tag === "input" || tag === "textarea" || tag === "select") {
        return;
      }
      closeFocusDrawers();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [closeFocusDrawers, focusAnyOpen, layoutMode]);

  const contentClassName = `content view-${layoutMode}${focusLeftOpen ? " focus-left-open" : ""}${focusRightOpen ? " focus-right-open" : ""}${focusAnyOpen ? " focus-any-open" : ""}`;

  const inputPanelModel = React.useMemo(() => normalizeGraphInputsPanelModel({
    values: {
      apiBase,
      graphId,
      sceneJsonPath,
      baselineId,
      profile,
      runtimeBackendType,
      runtimeProviderSpec,
      runtimeRequiredModulesText,
      runtimeFailurePolicy,
      runtimeSimulationMode,
      runtimeMultiplexingMode,
      runtimeBpmPhaseCodeText,
      runtimeMultiplexingPlanJson,
      runtimeDevice,
      runtimeLicenseTier,
      runtimeLicenseFile,
      runtimeTxFfdFilesText,
      runtimeRxFfdFilesText,
      runtimeMitsubaEgoOriginText,
      runtimeMitsubaChirpIntervalText,
      runtimeMitsubaMinRangeText,
      runtimeMitsubaSpheresJson,
      runtimePoSbrRepoRoot,
      runtimePoSbrGeometryPath,
      runtimePoSbrChirpIntervalText,
      runtimePoSbrBouncesText,
      runtimePoSbrRaysPerLambdaText,
      runtimePoSbrAlphaDegText,
      runtimePoSbrPhiDegText,
      runtimePoSbrThetaDegText,
      runtimePoSbrRadialVelocityText,
      runtimePoSbrMinRangeText,
      runtimePoSbrMaterialTag,
      runtimePoSbrPathIdPrefix,
      runtimePoSbrComponentsJson,
      runtimeDiagnosticBadges: runtimeDiagnostics.badges,
      runtimeDiagnosticText: runtimeDiagnostics.summaryText,
      runtimeStatusLine: runtimeSummary.runtimeStatusLine,
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
      setRuntimeBackendType,
      setRuntimeProviderSpec,
      setRuntimeRequiredModulesText,
      setRuntimeFailurePolicy,
      setRuntimeSimulationMode,
      setRuntimeMultiplexingMode,
      setRuntimeBpmPhaseCodeText,
      setRuntimeMultiplexingPlanJson,
      setRuntimeDevice,
      setRuntimeLicenseTier,
      setRuntimeLicenseFile,
      setRuntimeTxFfdFilesText,
      setRuntimeRxFfdFilesText,
      setRuntimeMitsubaEgoOriginText,
      setRuntimeMitsubaChirpIntervalText,
      setRuntimeMitsubaMinRangeText,
      setRuntimeMitsubaSpheresJson,
      setRuntimePoSbrRepoRoot,
      setRuntimePoSbrGeometryPath,
      setRuntimePoSbrChirpIntervalText,
      setRuntimePoSbrBouncesText,
      setRuntimePoSbrRaysPerLambdaText,
      setRuntimePoSbrAlphaDegText,
      setRuntimePoSbrPhiDegText,
      setRuntimePoSbrThetaDegText,
      setRuntimePoSbrRadialVelocityText,
      setRuntimePoSbrMinRangeText,
      setRuntimePoSbrMaterialTag,
      setRuntimePoSbrPathIdPrefix,
      setRuntimePoSbrComponentsJson,
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
    runtimeBackendType,
    runtimeProviderSpec,
    runtimeRequiredModulesText,
    runtimeFailurePolicy,
    runtimeSimulationMode,
    runtimeMultiplexingMode,
    runtimeBpmPhaseCodeText,
    runtimeMultiplexingPlanJson,
    runtimeDevice,
    runtimeLicenseTier,
    runtimeLicenseFile,
    runtimeTxFfdFilesText,
    runtimeRxFfdFilesText,
    runtimeMitsubaEgoOriginText,
    runtimeMitsubaChirpIntervalText,
    runtimeMitsubaMinRangeText,
    runtimeMitsubaSpheresJson,
    runtimePoSbrRepoRoot,
    runtimePoSbrGeometryPath,
    runtimePoSbrChirpIntervalText,
    runtimePoSbrBouncesText,
    runtimePoSbrRaysPerLambdaText,
    runtimePoSbrAlphaDegText,
    runtimePoSbrPhiDegText,
    runtimePoSbrThetaDegText,
    runtimePoSbrRadialVelocityText,
    runtimePoSbrMinRangeText,
    runtimePoSbrMaterialTag,
    runtimePoSbrPathIdPrefix,
    runtimePoSbrComponentsJson,
    runtimeDiagnostics.badges,
    runtimeDiagnostics.summaryText,
    runtimeSummary.runtimeStatusLine,
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

  return h("div", { className: `page density-${densityMode}` }, [
    h(TopBar, {
      key: "topbar",
      statusTone,
      statusText,
      nodeCount: nodes.length,
      edgeCount: edges.length,
      runtimeBackendType: runtimeSummary.backendTypeObserved || runtimeBackendType,
      runtimeMode: runtimeSummary.runtimeModeObserved || runtimeSimulationMode,
      runtimeLicenseTier,
      runtimeLicenseSet: Boolean(runtimeSummary.licenseObserved || runtimeLicenseFile),
      layoutMode,
      setLayoutMode,
      densityMode,
      setDensityMode,
      pipelineStages,
      focusLeftOpen,
      focusRightOpen,
      onToggleFocusLeft: toggleFocusLeftDrawer,
      onToggleFocusRight: toggleFocusRightDrawer,
    }),
    h("main", { className: contentClassName, key: "ct" }, [
      h("button", {
        type: "button",
        className: "focus-backdrop",
        key: "focus_backdrop",
        onClick: closeFocusDrawers,
        "aria-label": "Close focus drawers",
      }),
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
        compareGraphRunId,
        setCompareGraphRunId: setCompareGraphRunIdDraft,
        compareRunStatusText,
        compareGraphRunSummary,
        loadCompareGraphRunById,
        clearCompareGraphRun,
        pinCurrentGraphRunAsCompare,
        baselineId,
        pinBaselineFromGraphRun,
        runPolicyGateForGraphRun,
        runDecisionRegressionSession,
        runLowVsCurrentTrackCompare,
        trackCompareBaselinePresetId,
        setTrackCompareBaselinePresetId,
        trackCompareTargetPresetId,
        setTrackCompareTargetPresetId,
        trackComparePresetOptions: RUNTIME_PURPOSE_PRESET_OPTIONS,
        trackCompareQuickPairOptions: RUNTIME_PURPOSE_QUICK_PAIR_OPTIONS,
        applyTrackCompareQuickPair,
        trackCompareSelectedPairSummaryText,
        trackCompareSelectedPairForecastText,
        pinnedCompareQuickActionOptions,
        pinnedCompareQuickActionSummaryText,
        pinnedCompareQuickActionDetailText,
        expandedPinnedCompareQuickActionId,
        applyPinnedCompareQuickAction,
        runPinnedCompareQuickAction,
        togglePinnedCompareQuickActionExpanded,
        compareSessionHistoryText,
        compareReplayPairOptions,
        selectedCompareReplayPairId,
        setSelectedCompareReplayPairId,
        selectedCompareReplayPairLabelDraft,
        setSelectedCompareReplayPairLabelDraft,
        latestReplayableCompareSessionText,
        canReplayLatestCompareSession: Boolean(latestReplayableCompareSession),
        applyLatestCompareSessionPair,
        runLatestCompareSessionPair,
        selectedReplayableCompareSessionText,
        selectedReplayableCompareSessionMetaText,
        selectedReplayableCompareSessionRetentionText,
        selectedReplayableCompareSessionArtifactExpectationSummaryText,
        selectedReplayableCompareSessionArtifactExpectationText,
        selectedReplayableCompareSessionPreviewText,
        canReplaySelectedCompareSession: Boolean(selectedReplayableCompareSession),
        applySelectedCompareSessionPair,
        runSelectedCompareSessionPair,
        saveSelectedCompareSessionPairLabel,
        togglePinSelectedCompareSessionPair,
        deleteSelectedCompareSessionPair,
        compareSessionImportFileInputRef,
        compareSessionRetentionPolicy,
        compareSessionRetentionPolicyOptions: COMPARE_SESSION_RETENTION_POLICY_OPTIONS,
        compareSessionRetentionPolicySummaryText,
        compareSessionRetentionGroupHintText,
        compareSessionRetentionPreviewText,
        compareSessionTransferCompactSummaryText,
        compareSessionTransferStatusText,
        compareSessionTransferBadgeRows,
        hasCompareSessionImportPreview: stagedCompareSessionImportSummary.ready === true,
        compareSessionImportPreviewSummaryText,
        compareSessionImportPreviewText,
        triggerCompareSessionImportFilePick,
        handleCompareSessionImportFileChange,
        updateCompareSessionRetentionPolicy,
        clearAllCompareSessionHistory,
        applyCompareSessionImportPreview,
        clearCompareSessionImportPreview,
        exportCompareSessionHistory,
        runPresetPairTrackCompare,
        exportGateReport,
        exportDecisionRegressionSession,
        exportDecisionBriefMd,
        currentTrackLabel: configuredRuntimeSummary.trackLabel,
        compareTrackLabel: compareRuntimeSummary.trackLabel,
        trackCompareGuideText,
        decisionSummaryText,
        decisionOpsStatusText,
        artifactInspectorDecisionStatusBadgesText,
        artifactInspectorDecisionStatusBadgeRows,
        artifactInspectorDecisionLayoutStateText,
        artifactInspectorDecisionProbeStateText,
        trackCompareRunnerStatusText,
        lastRegressionSession,
        lastRegressionExport,
        contractDebugText,
        onArtifactInspectorStatusChange: handleArtifactInspectorStatusChange,
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
