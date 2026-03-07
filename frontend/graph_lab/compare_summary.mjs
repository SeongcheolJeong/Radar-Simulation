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

function safeShapeLabel(shape) {
  return Array.isArray(shape) && shape.length > 0 ? shape.join("x") : "-";
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
        relDb: Number(peak?.rel_db || 0),
      };
    })
    .filter(Boolean);
}

function shortAdcSource(value) {
  const text = String(value || "").trim();
  if (!text) return "-";
  if (text === "runtime_payload_adc_sctr") return "runtime";
  if (text.startsWith("synth_")) return "synth";
  return text;
}

function getRuntimeResolution(summary) {
  const meta = summary?.radar_map_summary?.metadata && typeof summary.radar_map_summary.metadata === "object"
    ? summary.radar_map_summary.metadata
    : {};
  return meta?.runtime_resolution && typeof meta.runtime_resolution === "object"
    ? meta.runtime_resolution
    : {};
}

function buildArtifactRows(currentSummary, compareSummary) {
  const defs = [
    { name: "path_list_json", required: true },
    { name: "adc_cube_npz", required: true },
    { name: "radar_map_npz", required: true },
    { name: "graph_run_summary_json", required: true },
    { name: "lgit_customized_output_npz", required: false },
  ];
  return defs.map((def) => {
    const currentPresent = String(currentSummary?.outputs?.[def.name] || "").trim() !== "";
    const comparePresent = String(compareSummary?.outputs?.[def.name] || "").trim() !== "";
    return {
      ...def,
      currentPresent,
      comparePresent,
      same: currentPresent === comparePresent,
    };
  });
}

export function buildRunCompareSummary(currentSummary, compareSummary) {
  const current = currentSummary && typeof currentSummary === "object" ? currentSummary : null;
  const compare = compareSummary && typeof compareSummary === "object" ? compareSummary : null;
  if (!current || !compare) {
    return {
      available: false,
      assessment: "unavailable",
      flags: [],
      flagSummary: "none",
      summaryLine: "assessment=unavailable | compare run not loaded",
      detailLines: [
        "assessment: unavailable",
        "flags: none",
        "reason: compare run not loaded",
      ],
    };
  }

  const currentAdcShape = normalizeShape(current?.adc_summary?.shape);
  const currentRdShape = normalizeShape(current?.radar_map_summary?.rd_shape);
  const currentRaShape = normalizeShape(current?.radar_map_summary?.ra_shape);
  const compareAdcShape = normalizeShape(compare?.adc_summary?.shape);
  const compareRdShape = normalizeShape(compare?.radar_map_summary?.rd_shape);
  const compareRaShape = normalizeShape(compare?.radar_map_summary?.ra_shape);

  const currentRdPeak = normalizePeakList(current?.quicklook?.rd_top_peaks, "doppler_bin", "range_bin")[0] || null;
  const compareRdPeak = normalizePeakList(compare?.quicklook?.rd_top_peaks, "doppler_bin", "range_bin")[0] || null;
  const currentRaPeak = normalizePeakList(current?.quicklook?.ra_top_peaks, "angle_bin", "range_bin")[0] || null;
  const compareRaPeak = normalizePeakList(compare?.quicklook?.ra_top_peaks, "angle_bin", "range_bin")[0] || null;

  const currentRuntimeResolution = getRuntimeResolution(current);
  const compareRuntimeResolution = getRuntimeResolution(compare);

  const shapeEq = {
    adc: safeShapeLabel(currentAdcShape) === safeShapeLabel(compareAdcShape),
    rd: safeShapeLabel(currentRdShape) === safeShapeLabel(compareRdShape),
    ra: safeShapeLabel(currentRaShape) === safeShapeLabel(compareRaShape),
  };
  const shapeText = {
    adc: `${safeShapeLabel(currentAdcShape)} vs ${safeShapeLabel(compareAdcShape)}`,
    rd: `${safeShapeLabel(currentRdShape)} vs ${safeShapeLabel(compareRdShape)}`,
    ra: `${safeShapeLabel(currentRaShape)} vs ${safeShapeLabel(compareRaShape)}`,
  };
  const pathCountDelta = Number(current?.path_summary?.path_count_total || 0) - Number(compare?.path_summary?.path_count_total || 0);
  const rdPeakDelta = currentRdPeak && compareRdPeak
    ? {
        rangeBinDelta: Number(currentRdPeak.col || 0) - Number(compareRdPeak.col || 0),
        dopplerBinDelta: Number(currentRdPeak.row || 0) - Number(compareRdPeak.row || 0),
        relDbDelta: Number(currentRdPeak.relDb || 0) - Number(compareRdPeak.relDb || 0),
      }
    : null;
  const raPeakDelta = currentRaPeak && compareRaPeak
    ? {
        rangeBinDelta: Number(currentRaPeak.col || 0) - Number(compareRaPeak.col || 0),
        angleBinDelta: Number(currentRaPeak.row || 0) - Number(compareRaPeak.row || 0),
        relDbDelta: Number(currentRaPeak.relDb || 0) - Number(compareRaPeak.relDb || 0),
      }
    : null;

  const currentAdcSource = shortAdcSource(currentRuntimeResolution?.adc_source);
  const compareAdcSource = shortAdcSource(compareRuntimeResolution?.adc_source);
  const artifactRows = buildArtifactRows(current, compare);
  const requiredRows = artifactRows.filter((row) => row.required);
  const optionalRows = artifactRows.filter((row) => !row.required);
  const currentRequiredPresent = requiredRows.filter((row) => row.currentPresent).length;
  const compareRequiredPresent = requiredRows.filter((row) => row.comparePresent).length;
  const missingRequiredCurrent = requiredRows.filter((row) => !row.currentPresent).map((row) => row.name);
  const missingRequiredCompare = requiredRows.filter((row) => !row.comparePresent).map((row) => row.name);
  const artifactPresenceDelta = artifactRows
    .filter((row) => !row.same)
    .map((row) => `${row.name}=${row.currentPresent ? "yes" : "no"}/${row.comparePresent ? "yes" : "no"}`);

  const flags = [];
  const shapeMismatchNames = Object.entries(shapeEq)
    .filter(([, value]) => !value)
    .map(([name]) => name);
  if (shapeMismatchNames.length > 0) flags.push(`shape_mismatch:${shapeMismatchNames.join(",")}`);
  if (missingRequiredCurrent.length > 0) flags.push(`current_missing:${missingRequiredCurrent.join(",")}`);
  if (missingRequiredCompare.length > 0) flags.push(`compare_missing:${missingRequiredCompare.join(",")}`);
  if (pathCountDelta !== 0) flags.push(`path_delta:${formatSigned(pathCountDelta)}`);
  if (
    rdPeakDelta
    && (
      rdPeakDelta.rangeBinDelta !== 0
      || rdPeakDelta.dopplerBinDelta !== 0
      || Math.abs(Number(rdPeakDelta.relDbDelta || 0)) >= 0.01
    )
  ) {
    flags.push(
      `rd_peak_shift:${formatSigned(rdPeakDelta.rangeBinDelta)}/${formatSigned(rdPeakDelta.dopplerBinDelta)}/${Number(rdPeakDelta.relDbDelta).toFixed(2)}`
    );
  }
  if (
    raPeakDelta
    && (
      raPeakDelta.rangeBinDelta !== 0
      || raPeakDelta.angleBinDelta !== 0
      || Math.abs(Number(raPeakDelta.relDbDelta || 0)) >= 0.01
    )
  ) {
    flags.push(
      `ra_peak_shift:${formatSigned(raPeakDelta.rangeBinDelta)}/${formatSigned(raPeakDelta.angleBinDelta)}/${Number(raPeakDelta.relDbDelta).toFixed(2)}`
    );
  }
  if (currentAdcSource !== "-" && compareAdcSource !== "-" && currentAdcSource !== compareAdcSource) {
    flags.push(`adc_source_changed:${currentAdcSource}->${compareAdcSource}`);
  }
  if (artifactPresenceDelta.length > 0) {
    flags.push(`artifact_delta:${artifactPresenceDelta.join(",")}`);
  }

  let assessment = "aligned";
  if (shapeMismatchNames.length > 0 || missingRequiredCurrent.length > 0 || missingRequiredCompare.length > 0) {
    assessment = "hold";
  } else if (flags.length > 0) {
    assessment = "review";
  }

  const flagSummary = flags.length > 0 ? flags.join(" | ") : "none";
  const optionalPresenceDelta = optionalRows
    .filter((row) => !row.same)
    .map((row) => row.name)
    .join(",") || "none";

  return {
    available: true,
    assessment,
    flags,
    flagSummary,
    currentGraphRunId: String(current?.graph_run_id || current?.run_id || "-"),
    compareGraphRunId: String(compare?.graph_run_id || compare?.run_id || "-"),
    shapeEq,
    shapeText,
    pathCountDelta,
    rdPeakDelta,
    raPeakDelta,
    adcSource: {
      current: currentAdcSource,
      compare: compareAdcSource,
      changed: currentAdcSource !== "-" && compareAdcSource !== "-" && currentAdcSource !== compareAdcSource,
    },
    artifactRows,
    requiredArtifactCounts: {
      currentPresent: currentRequiredPresent,
      comparePresent: compareRequiredPresent,
      total: requiredRows.length,
    },
    artifactPresenceDeltaText: artifactPresenceDelta.join(",") || "none",
    optionalPresenceDeltaText: optionalPresenceDelta,
    summaryLine: [
      `assessment=${assessment}`,
      `flags=${flagSummary}`,
      `required_artifacts=${currentRequiredPresent}/${compareRequiredPresent}/${requiredRows.length}`,
      `adc_source=${currentAdcSource}/${compareAdcSource}`,
    ].join(" | "),
    detailLines: [
      `assessment: ${assessment}`,
      `flags: ${flagSummary}`,
      `shape_status(adc/rd/ra): ${shapeEq.adc ? "match" : "mismatch"}/${shapeEq.rd ? "match" : "mismatch"}/${shapeEq.ra ? "match" : "mismatch"}`,
      `shape(adc): ${shapeText.adc}`,
      `shape(rd): ${shapeText.rd}`,
      `shape(ra): ${shapeText.ra}`,
      `adc_source(current/compare): ${currentAdcSource}/${compareAdcSource}`,
      `path_count_delta(current-compare): ${formatSigned(pathCountDelta)}`,
      rdPeakDelta
        ? `rd_peak_delta(range/doppler/rel_db): ${formatSigned(rdPeakDelta.rangeBinDelta)}/${formatSigned(rdPeakDelta.dopplerBinDelta)}/${Number(rdPeakDelta.relDbDelta).toFixed(2)}`
        : "rd_peak_delta(range/doppler/rel_db): unavailable",
      raPeakDelta
        ? `ra_peak_delta(range/angle/rel_db): ${formatSigned(raPeakDelta.rangeBinDelta)}/${formatSigned(raPeakDelta.angleBinDelta)}/${Number(raPeakDelta.relDbDelta).toFixed(2)}`
        : "ra_peak_delta(range/angle/rel_db): unavailable",
      `required_artifacts(current/compare/total): ${currentRequiredPresent}/${compareRequiredPresent}/${requiredRows.length}`,
      `artifact_presence_delta: ${artifactPresenceDelta.join(",") || "none"}`,
      `optional_artifact_delta: ${optionalPresenceDelta}`,
    ],
  };
}

