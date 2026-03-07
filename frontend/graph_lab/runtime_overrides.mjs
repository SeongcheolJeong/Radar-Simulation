const MULTIPLEXING_MODE_SET = new Set(["tdm", "bpm", "custom"]);

export function splitTokenList(rawText) {
  return String(rawText || "")
    .split(/[,\n]/)
    .map((x) => String(x || "").trim())
    .filter((x) => x.length > 0);
}

export function parseNumericTokenList(rawText, fieldLabel) {
  const tokens = splitTokenList(rawText);
  if (tokens.length <= 0) return null;
  return tokens.map((token, idx) => {
    const value = Number(token);
    if (!Number.isFinite(value)) {
      throw new Error(`${fieldLabel} contains non-numeric token at index ${idx}: "${token}"`);
    }
    return Number(value);
  });
}

export function parseOptionalJsonObject(rawText, fieldLabel) {
  const text = String(rawText || "").trim();
  if (!text) return null;
  let parsed = null;
  try {
    parsed = JSON.parse(text);
  } catch (err) {
    throw new Error(`${fieldLabel} must be valid JSON: ${String(err.message || err)}`);
  }
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new Error(`${fieldLabel} must decode to a JSON object`);
  }
  return parsed;
}

export function parseOptionalJsonArray(rawText, fieldLabel) {
  const text = String(rawText || "").trim();
  if (!text) return null;
  let parsed = null;
  try {
    parsed = JSON.parse(text);
  } catch (err) {
    throw new Error(`${fieldLabel} must be valid JSON: ${String(err.message || err)}`);
  }
  if (!Array.isArray(parsed)) {
    throw new Error(`${fieldLabel} must decode to a JSON array`);
  }
  return parsed;
}

export function parseOptionalNumber(rawText, fieldLabel, options) {
  const text = String(rawText || "").trim();
  if (!text) return null;
  const value = Number(text);
  if (!Number.isFinite(value)) {
    throw new Error(`${fieldLabel} must be numeric`);
  }
  const opts = options && typeof options === "object" ? options : {};
  if (opts.integer && !Number.isInteger(value)) {
    throw new Error(`${fieldLabel} must be an integer`);
  }
  if (Number.isFinite(opts.min) && value < Number(opts.min)) {
    throw new Error(`${fieldLabel} must be >= ${Number(opts.min)}`);
  }
  if (Number.isFinite(opts.gt) && value <= Number(opts.gt)) {
    throw new Error(`${fieldLabel} must be > ${Number(opts.gt)}`);
  }
  return value;
}

export function parseOptionalFixedNumericList(rawText, fieldLabel, expectedLength) {
  const values = parseNumericTokenList(rawText, fieldLabel);
  if (values === null) return null;
  if (values.length !== Number(expectedLength)) {
    throw new Error(`${fieldLabel} must have exactly ${Number(expectedLength)} numeric values`);
  }
  return values;
}

function assertNumericContainer(value, fieldLabel, depth) {
  const d = Number(depth || 0);
  if (d > 10) {
    throw new Error(`${fieldLabel} nesting depth is too large`);
  }
  if (value === null || value === undefined) return;
  if (typeof value === "number") {
    if (!Number.isFinite(value)) {
      throw new Error(`${fieldLabel} contains non-finite number`);
    }
    return;
  }
  if (Array.isArray(value)) {
    value.forEach((row, idx) => assertNumericContainer(row, `${fieldLabel}[${idx}]`, d + 1));
    return;
  }
  if (typeof value === "object") {
    Object.entries(value).forEach(([k, v]) => {
      assertNumericContainer(v, `${fieldLabel}.${String(k)}`, d + 1);
    });
    return;
  }
  throw new Error(`${fieldLabel} must contain only numeric/list/object values`);
}

function validateMultiplexingPlanObject(planObj) {
  if (!planObj || typeof planObj !== "object" || Array.isArray(planObj)) {
    throw new Error("runtime multiplexing plan JSON must decode to an object");
  }
  const modeRaw = String(planObj.mode || "").trim().toLowerCase();
  if (modeRaw && !MULTIPLEXING_MODE_SET.has(modeRaw)) {
    throw new Error(`runtime multiplexing plan mode must be one of: tdm, bpm, custom (got "${modeRaw}")`);
  }
  if (Object.prototype.hasOwnProperty.call(planObj, "pulse_amp")) {
    assertNumericContainer(planObj.pulse_amp, "runtime multiplexing plan pulse_amp", 0);
  }
  if (Object.prototype.hasOwnProperty.call(planObj, "pulse_phs_deg")) {
    assertNumericContainer(planObj.pulse_phs_deg, "runtime multiplexing plan pulse_phs_deg", 0);
  }
  if (Object.prototype.hasOwnProperty.call(planObj, "bpm_phase_code_deg")) {
    assertNumericContainer(planObj.bpm_phase_code_deg, "runtime multiplexing plan bpm_phase_code_deg", 0);
  }
}

function validateArrayItemsAreObjects(rows, fieldLabel) {
  if (rows === null || rows === undefined) return;
  if (!Array.isArray(rows)) {
    throw new Error(`${fieldLabel} must be an array`);
  }
  rows.forEach((row, idx) => {
    if (!row || typeof row !== "object" || Array.isArray(row)) {
      throw new Error(`${fieldLabel}[${idx}] must be an object`);
    }
  });
}

export function buildSceneOverrides(options) {
  const opts = options && typeof options === "object" ? options : {};
  const backendType = String(opts.runtimeBackendType || "").trim().toLowerCase();
  if (!backendType) return null;
  const runtimeProviderSpec = String(opts.runtimeProviderSpec || "").trim();
  const runtimeFailurePolicy = String(opts.runtimeFailurePolicy || "").trim().toLowerCase();
  const runtimeSimulationMode = String(opts.runtimeSimulationMode || "").trim().toLowerCase();
  const runtimeMultiplexingMode = String(opts.runtimeMultiplexingMode || "").trim().toLowerCase();
  const runtimeBpmPhaseCode = parseNumericTokenList(
    opts.runtimeBpmPhaseCodeText || "",
    "runtime BPM phase code"
  );
  const runtimeMultiplexingPlan = parseOptionalJsonObject(
    opts.runtimeMultiplexingPlanJson || "",
    "runtime multiplexing plan JSON"
  );
  const runtimeDevice = String(opts.runtimeDevice || "").trim().toLowerCase();
  const runtimeLicenseTier = String(opts.runtimeLicenseTier || "").trim().toLowerCase();
  const runtimeLicenseFile = String(opts.runtimeLicenseFile || "").trim();
  const runtimeRequiredModules = splitTokenList(opts.runtimeRequiredModulesText || "");
  const runtimeTxFfdFiles = splitTokenList(opts.runtimeTxFfdFilesText || "");
  const runtimeRxFfdFiles = splitTokenList(opts.runtimeRxFfdFilesText || "");
  const runtimeProviderSpecLower = runtimeProviderSpec.toLowerCase();
  const isSionnaStyleProvider = (
    backendType === "sionna_rt"
    || runtimeProviderSpecLower.includes("mitsuba_rt_provider")
  );
  const isPoSbrProvider = (
    backendType === "po_sbr_rt"
    || runtimeProviderSpecLower.includes("po_sbr_rt_provider")
  );
  const runtimeMitsubaEgoOrigin = parseOptionalFixedNumericList(
    opts.runtimeMitsubaEgoOriginText || "",
    "runtime Mitsuba ego origin",
    3
  );
  const runtimeMitsubaChirpInterval = parseOptionalNumber(
    opts.runtimeMitsubaChirpIntervalText || "",
    "runtime Mitsuba chirp interval",
    { gt: 0 }
  );
  const runtimeMitsubaMinRange = parseOptionalNumber(
    opts.runtimeMitsubaMinRangeText || "",
    "runtime Mitsuba min range",
    { gt: 0 }
  );
  const runtimeMitsubaSpheres = parseOptionalJsonArray(
    opts.runtimeMitsubaSpheresJson || "",
    "runtime Mitsuba spheres JSON"
  );
  const runtimePoSbrRepoRoot = String(opts.runtimePoSbrRepoRoot || "").trim();
  const runtimePoSbrGeometryPath = String(opts.runtimePoSbrGeometryPath || "").trim();
  const runtimePoSbrChirpInterval = parseOptionalNumber(
    opts.runtimePoSbrChirpIntervalText || "",
    "runtime PO-SBR chirp interval",
    { gt: 0 }
  );
  const runtimePoSbrBounces = parseOptionalNumber(
    opts.runtimePoSbrBouncesText || "",
    "runtime PO-SBR bounces",
    { integer: true, min: 0 }
  );
  const runtimePoSbrRaysPerLambda = parseOptionalNumber(
    opts.runtimePoSbrRaysPerLambdaText || "",
    "runtime PO-SBR rays per lambda",
    { gt: 0 }
  );
  const runtimePoSbrAlphaDeg = parseOptionalNumber(
    opts.runtimePoSbrAlphaDegText || "",
    "runtime PO-SBR alpha",
    {}
  );
  const runtimePoSbrPhiDeg = parseOptionalNumber(
    opts.runtimePoSbrPhiDegText || "",
    "runtime PO-SBR phi",
    {}
  );
  const runtimePoSbrThetaDeg = parseOptionalNumber(
    opts.runtimePoSbrThetaDegText || "",
    "runtime PO-SBR theta",
    {}
  );
  const runtimePoSbrRadialVelocity = parseOptionalNumber(
    opts.runtimePoSbrRadialVelocityText || "",
    "runtime PO-SBR radial velocity",
    {}
  );
  const runtimePoSbrMinRange = parseOptionalNumber(
    opts.runtimePoSbrMinRangeText || "",
    "runtime PO-SBR min range",
    { gt: 0 }
  );
  const runtimePoSbrMaterialTag = String(opts.runtimePoSbrMaterialTag || "").trim();
  const runtimePoSbrPathIdPrefix = String(opts.runtimePoSbrPathIdPrefix || "").trim();
  const runtimePoSbrComponents = parseOptionalJsonArray(
    opts.runtimePoSbrComponentsJson || "",
    "runtime PO-SBR components JSON"
  );

  if (runtimeMultiplexingMode && !MULTIPLEXING_MODE_SET.has(runtimeMultiplexingMode)) {
    throw new Error(
      `runtime multiplexing mode must be one of: tdm, bpm, custom (got "${runtimeMultiplexingMode}")`
    );
  }
  if ((runtimeTxFfdFiles.length > 0) !== (runtimeRxFfdFiles.length > 0)) {
    throw new Error("runtime tx/rx FFD files must be provided together");
  }
  if (runtimeMultiplexingPlan) {
    validateMultiplexingPlanObject(runtimeMultiplexingPlan);
  }
  if (runtimeMitsubaSpheres) {
    validateArrayItemsAreObjects(runtimeMitsubaSpheres, "runtime Mitsuba spheres JSON");
  }
  if (runtimePoSbrComponents) {
    validateArrayItemsAreObjects(runtimePoSbrComponents, "runtime PO-SBR components JSON");
  }

  const backend = { type: backendType };
  if (runtimeProviderSpec) backend.runtime_provider = runtimeProviderSpec;
  if (runtimeRequiredModules.length > 0) backend.runtime_required_modules = runtimeRequiredModules;
  if (runtimeFailurePolicy) backend.runtime_failure_policy = runtimeFailurePolicy;
  if (runtimeTxFfdFiles.length > 0) backend.tx_ffd_files = runtimeTxFfdFiles;
  if (runtimeRxFfdFiles.length > 0) backend.rx_ffd_files = runtimeRxFfdFiles;

  const runtimeInput = {};
  if (runtimeSimulationMode) runtimeInput.simulation_mode = runtimeSimulationMode;
  if (runtimeMultiplexingMode) runtimeInput.multiplexing_mode = runtimeMultiplexingMode;
  if (Array.isArray(runtimeBpmPhaseCode) && runtimeBpmPhaseCode.length > 0) {
    runtimeInput.bpm_phase_code_deg = runtimeBpmPhaseCode;
  }
  if (runtimeMultiplexingPlan) {
    runtimeInput.tx_multiplexing_plan = runtimeMultiplexingPlan;
  }
  if (runtimeDevice) runtimeInput.device = runtimeDevice;
  if (runtimeLicenseTier) runtimeInput.license_tier_hint = runtimeLicenseTier;
  if (runtimeLicenseFile) runtimeInput.license_file = runtimeLicenseFile;
  if (isSionnaStyleProvider) {
    if (runtimeMitsubaEgoOrigin) runtimeInput.ego_origin_m = runtimeMitsubaEgoOrigin;
    if (runtimeMitsubaChirpInterval !== null) runtimeInput.chirp_interval_s = runtimeMitsubaChirpInterval;
    if (runtimeMitsubaMinRange !== null) runtimeInput.min_range_m = runtimeMitsubaMinRange;
    if (runtimeMitsubaSpheres) runtimeInput.spheres = runtimeMitsubaSpheres;
  }
  if (isPoSbrProvider) {
    if (runtimePoSbrRepoRoot) runtimeInput.po_sbr_repo_root = runtimePoSbrRepoRoot;
    if (runtimePoSbrGeometryPath) runtimeInput.geometry_path = runtimePoSbrGeometryPath;
    if (runtimePoSbrChirpInterval !== null) runtimeInput.chirp_interval_s = runtimePoSbrChirpInterval;
    if (runtimePoSbrBounces !== null) runtimeInput.bounces = runtimePoSbrBounces;
    if (runtimePoSbrRaysPerLambda !== null) runtimeInput.rays_per_lambda = runtimePoSbrRaysPerLambda;
    if (runtimePoSbrAlphaDeg !== null) runtimeInput.alpha_deg = runtimePoSbrAlphaDeg;
    if (runtimePoSbrPhiDeg !== null) runtimeInput.phi_deg = runtimePoSbrPhiDeg;
    if (runtimePoSbrThetaDeg !== null) runtimeInput.theta_deg = runtimePoSbrThetaDeg;
    if (runtimePoSbrRadialVelocity !== null) runtimeInput.radial_velocity_mps = runtimePoSbrRadialVelocity;
    if (runtimePoSbrMinRange !== null) runtimeInput.min_range_m = runtimePoSbrMinRange;
    if (runtimePoSbrMaterialTag) runtimeInput.material_tag = runtimePoSbrMaterialTag;
    if (runtimePoSbrPathIdPrefix) runtimeInput.path_id_prefix = runtimePoSbrPathIdPrefix;
    if (runtimePoSbrComponents) runtimeInput.components = runtimePoSbrComponents;
  }
  if (Object.keys(runtimeInput).length > 0) {
    backend.runtime_input = runtimeInput;
  }

  return { backend };
}
