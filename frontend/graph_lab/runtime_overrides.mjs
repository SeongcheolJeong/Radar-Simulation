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
  if (Object.keys(runtimeInput).length > 0) {
    backend.runtime_input = runtimeInput;
  }

  return { backend };
}
