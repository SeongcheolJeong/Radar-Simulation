export const RUNTIME_PURPOSE_PRESET_CURRENT_CONFIG = "current_config";
export const RUNTIME_PURPOSE_PRESET_LOW_FIDELITY = "low_fidelity_radarsimpy_ffd";
export const RUNTIME_PURPOSE_PRESET_HIGH_FIDELITY_SIONNA = "high_fidelity_sionna_rt";
export const RUNTIME_PURPOSE_PRESET_HIGH_FIDELITY_PO_SBR = "high_fidelity_po_sbr_rt";

const MITSUBA_SAMPLE_SPHERES_JSON = JSON.stringify([
  {
    center_m: [22.0, 0.0, 0.0],
    radius_m: 0.45,
    velocity_mps: [-1.5, 0.0, 0.0],
    amp: { re: 1.0, im: 0.0 },
    range_amp_exponent: 2.0,
    path_id_prefix: "mitsuba_vehicle_a",
    material_tag: "vehicle_body",
    reflection_order: 1,
  },
  {
    center_m: [34.0, 4.0, 0.0],
    radius_m: 0.65,
    velocity_mps: [0.0, -0.8, 0.0],
    amp: { re: 0.7, im: 0.1 },
    range_amp_exponent: 2.0,
    path_id_prefix: "mitsuba_vehicle_b",
    material_tag: "vehicle_body",
    reflection_order: 1,
  },
], null, 2);

const PO_SBR_SAMPLE_COMPONENTS_JSON = JSON.stringify([
  {
    phi_deg: 78.0,
    theta_deg: 90.0,
    radial_velocity_mps: -2.0,
    path_id_prefix: "po_lane_left",
    material_tag: "guardrail",
  },
  {
    phi_deg: 102.0,
    theta_deg: 90.0,
    radial_velocity_mps: 1.5,
    path_id_prefix: "po_lane_right",
    material_tag: "vehicle_body",
  },
], null, 2);

export const RUNTIME_PURPOSE_PRESET_OPTIONS = [
  { id: RUNTIME_PURPOSE_PRESET_CURRENT_CONFIG, label: "Current Config (As-Is)" },
  { id: RUNTIME_PURPOSE_PRESET_LOW_FIDELITY, label: "Low Fidelity: RadarSimPy + FFD" },
  { id: RUNTIME_PURPOSE_PRESET_HIGH_FIDELITY_SIONNA, label: "High Fidelity: Sionna-style RT" },
  { id: RUNTIME_PURPOSE_PRESET_HIGH_FIDELITY_PO_SBR, label: "High Fidelity: PO-SBR" },
];

export const RUNTIME_PURPOSE_QUICK_PAIR_OPTIONS = [
  {
    id: "low_to_current",
    label: "Low -> Current",
    baselinePresetId: RUNTIME_PURPOSE_PRESET_LOW_FIDELITY,
    targetPresetId: RUNTIME_PURPOSE_PRESET_CURRENT_CONFIG,
  },
  {
    id: "low_to_sionna",
    label: "Low -> Sionna",
    baselinePresetId: RUNTIME_PURPOSE_PRESET_LOW_FIDELITY,
    targetPresetId: RUNTIME_PURPOSE_PRESET_HIGH_FIDELITY_SIONNA,
  },
  {
    id: "low_to_po_sbr",
    label: "Low -> PO-SBR",
    baselinePresetId: RUNTIME_PURPOSE_PRESET_LOW_FIDELITY,
    targetPresetId: RUNTIME_PURPOSE_PRESET_HIGH_FIDELITY_PO_SBR,
  },
];

export function getRuntimePurposePresetLabel(presetId) {
  const pid = String(presetId || "").trim();
  const row = RUNTIME_PURPOSE_PRESET_OPTIONS.find((item) => String(item.id || "") === pid);
  return String(row?.label || pid || RUNTIME_PURPOSE_PRESET_CURRENT_CONFIG);
}

export function getRuntimePurposePairLabel(baselinePresetId, targetPresetId, currentConfigLabel) {
  const baselineLabel = getRuntimePurposePresetLabel(baselinePresetId);
  const targetId = String(targetPresetId || "").trim();
  const targetLabel = targetId === RUNTIME_PURPOSE_PRESET_CURRENT_CONFIG
    ? String(currentConfigLabel || getRuntimePurposePresetLabel(targetId || RUNTIME_PURPOSE_PRESET_CURRENT_CONFIG))
    : getRuntimePurposePresetLabel(targetId);
  return `${baselineLabel} -> ${targetLabel}`;
}

export function buildRuntimePurposePresetOverrides(presetId) {
  const pid = String(presetId || "").trim();
  if (!pid || pid === RUNTIME_PURPOSE_PRESET_CURRENT_CONFIG) return null;
  if (pid === RUNTIME_PURPOSE_PRESET_LOW_FIDELITY) {
    return {
      runtimeBackendType: "radarsimpy_rt",
      runtimeProviderSpec: "avxsim.runtime_providers.radarsimpy_rt_provider:generate_radarsimpy_like_paths",
      runtimeRequiredModulesText: "radarsimpy",
      runtimeFailurePolicy: "error",
      runtimeSimulationMode: "radarsimpy_adc",
      runtimeDevice: "cpu",
    };
  }
  if (pid === RUNTIME_PURPOSE_PRESET_HIGH_FIDELITY_SIONNA) {
    return {
      runtimeBackendType: "sionna_rt",
      runtimeProviderSpec: "avxsim.runtime_providers.mitsuba_rt_provider:generate_sionna_like_paths_from_mitsuba",
      runtimeRequiredModulesText: "mitsuba,drjit",
      runtimeFailurePolicy: "error",
      runtimeSimulationMode: "auto",
      runtimeDevice: "gpu",
      runtimeMitsubaEgoOriginText: "0,0,0",
      runtimeMitsubaChirpIntervalText: "4.0e-5",
      runtimeMitsubaMinRangeText: "0.5",
      runtimeMitsubaSpheresJson: MITSUBA_SAMPLE_SPHERES_JSON,
    };
  }
  if (pid === RUNTIME_PURPOSE_PRESET_HIGH_FIDELITY_PO_SBR) {
    return {
      runtimeBackendType: "po_sbr_rt",
      runtimeProviderSpec: "avxsim.runtime_providers.po_sbr_rt_provider:generate_po_sbr_like_paths_from_posbr",
      runtimeRequiredModulesText: "rtxpy,igl",
      runtimeFailurePolicy: "error",
      runtimeSimulationMode: "auto",
      runtimeDevice: "gpu",
      runtimePoSbrRepoRoot: "external/PO-SBR-Python",
      runtimePoSbrGeometryPath: "geometries/plate.obj",
      runtimePoSbrChirpIntervalText: "4.0e-5",
      runtimePoSbrBouncesText: "2",
      runtimePoSbrRaysPerLambdaText: "3.0",
      runtimePoSbrAlphaDegText: "180",
      runtimePoSbrPhiDegText: "90",
      runtimePoSbrThetaDegText: "90",
      runtimePoSbrRadialVelocityText: "0.0",
      runtimePoSbrMinRangeText: "0.5",
      runtimePoSbrMaterialTag: "po_sbr_runtime",
      runtimePoSbrPathIdPrefix: "po_sbr_runtime",
      runtimePoSbrComponentsJson: PO_SBR_SAMPLE_COMPONENTS_JSON,
    };
  }
  return null;
}

function maybeSet(setters, key, value) {
  const fn = setters?.[key];
  if (typeof fn === "function") {
    fn(value);
  }
}

export function applyRuntimePurposePreset(presetId, setters) {
  const overrides = buildRuntimePurposePresetOverrides(presetId);
  if (!overrides) return false;
  Object.entries(overrides).forEach(([key, value]) => {
    const setterKey = `set${String(key).slice(0, 1).toUpperCase()}${String(key).slice(1)}`;
    maybeSet(setters, setterKey, value);
  });
  return true;
}
