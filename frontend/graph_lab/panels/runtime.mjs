import { React } from "../deps.mjs";

const h = React.createElement;
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

function isSionnaStyleProvider(runtimeBackendType, runtimeProviderSpec) {
  const backend = String(runtimeBackendType || "").trim().toLowerCase();
  const provider = String(runtimeProviderSpec || "").trim().toLowerCase();
  return backend === "sionna_rt" || provider.includes("mitsuba_rt_provider");
}

function isPoSbrProvider(runtimeBackendType, runtimeProviderSpec) {
  const backend = String(runtimeBackendType || "").trim().toLowerCase();
  const provider = String(runtimeProviderSpec || "").trim().toLowerCase();
  return backend === "po_sbr_rt" || provider.includes("po_sbr_rt_provider");
}

export function RuntimeConfigSection({
  runtimeBackendType,
  setRuntimeBackendType,
  runtimeProviderSpec,
  setRuntimeProviderSpec,
  runtimeRequiredModulesText,
  setRuntimeRequiredModulesText,
  runtimeFailurePolicy,
  setRuntimeFailurePolicy,
  runtimeSimulationMode,
  setRuntimeSimulationMode,
  runtimeMultiplexingMode,
  setRuntimeMultiplexingMode,
  runtimeBpmPhaseCodeText,
  setRuntimeBpmPhaseCodeText,
  runtimeMultiplexingPlanJson,
  setRuntimeMultiplexingPlanJson,
  runtimeDevice,
  setRuntimeDevice,
  runtimeLicenseTier,
  setRuntimeLicenseTier,
  runtimeLicenseFile,
  setRuntimeLicenseFile,
  runtimeTxFfdFilesText,
  setRuntimeTxFfdFilesText,
  runtimeRxFfdFilesText,
  setRuntimeRxFfdFilesText,
  runtimeMitsubaEgoOriginText,
  setRuntimeMitsubaEgoOriginText,
  runtimeMitsubaChirpIntervalText,
  setRuntimeMitsubaChirpIntervalText,
  runtimeMitsubaMinRangeText,
  setRuntimeMitsubaMinRangeText,
  runtimeMitsubaSpheresJson,
  setRuntimeMitsubaSpheresJson,
  runtimePoSbrRepoRoot,
  setRuntimePoSbrRepoRoot,
  runtimePoSbrGeometryPath,
  setRuntimePoSbrGeometryPath,
  runtimePoSbrChirpIntervalText,
  setRuntimePoSbrChirpIntervalText,
  runtimePoSbrBouncesText,
  setRuntimePoSbrBouncesText,
  runtimePoSbrRaysPerLambdaText,
  setRuntimePoSbrRaysPerLambdaText,
  runtimePoSbrAlphaDegText,
  setRuntimePoSbrAlphaDegText,
  runtimePoSbrPhiDegText,
  setRuntimePoSbrPhiDegText,
  runtimePoSbrThetaDegText,
  setRuntimePoSbrThetaDegText,
  runtimePoSbrRadialVelocityText,
  setRuntimePoSbrRadialVelocityText,
  runtimePoSbrMinRangeText,
  setRuntimePoSbrMinRangeText,
  runtimePoSbrMaterialTag,
  setRuntimePoSbrMaterialTag,
  runtimePoSbrPathIdPrefix,
  setRuntimePoSbrPathIdPrefix,
  runtimePoSbrComponentsJson,
  setRuntimePoSbrComponentsJson,
  runtimeDiagnosticBadges,
  runtimeDiagnosticText,
  runtimeStatusLine,
}) {
  const applyMitsubaAdvancedSample = () => {
    setRuntimeMitsubaEgoOriginText("0,0,0");
    setRuntimeMitsubaChirpIntervalText("4.0e-5");
    setRuntimeMitsubaMinRangeText("0.5");
    setRuntimeMitsubaSpheresJson(MITSUBA_SAMPLE_SPHERES_JSON);
  };

  const applyPoSbrAdvancedSample = () => {
    setRuntimePoSbrRepoRoot("external/PO-SBR-Python");
    setRuntimePoSbrGeometryPath("geometries/plate.obj");
    setRuntimePoSbrChirpIntervalText("4.0e-5");
    setRuntimePoSbrBouncesText("2");
    setRuntimePoSbrRaysPerLambdaText("3.0");
    setRuntimePoSbrAlphaDegText("180");
    setRuntimePoSbrPhiDegText("90");
    setRuntimePoSbrThetaDegText("90");
    setRuntimePoSbrRadialVelocityText("0.0");
    setRuntimePoSbrMinRangeText("0.5");
    setRuntimePoSbrMaterialTag("po_sbr_runtime");
    setRuntimePoSbrPathIdPrefix("po_sbr_runtime");
    setRuntimePoSbrComponentsJson(PO_SBR_SAMPLE_COMPONENTS_JSON);
  };

  const applyLowFidelityPreset = () => {
    setRuntimeBackendType("radarsimpy_rt");
    setRuntimeProviderSpec(
      "avxsim.runtime_providers.radarsimpy_rt_provider:generate_radarsimpy_like_paths"
    );
    setRuntimeRequiredModulesText("radarsimpy");
    setRuntimeFailurePolicy("error");
    setRuntimeSimulationMode("radarsimpy_adc");
    setRuntimeDevice("cpu");
  };

  const applyHighFidelitySionnaPreset = () => {
    setRuntimeBackendType("sionna_rt");
    setRuntimeProviderSpec(
      "avxsim.runtime_providers.mitsuba_rt_provider:generate_sionna_like_paths_from_mitsuba"
    );
    setRuntimeRequiredModulesText("mitsuba,drjit");
    setRuntimeFailurePolicy("error");
    setRuntimeSimulationMode("auto");
    setRuntimeDevice("gpu");
    applyMitsubaAdvancedSample();
  };

  const applyHighFidelityPoSbrPreset = () => {
    setRuntimeBackendType("po_sbr_rt");
    setRuntimeProviderSpec(
      "avxsim.runtime_providers.po_sbr_rt_provider:generate_po_sbr_like_paths_from_posbr"
    );
    setRuntimeRequiredModulesText("rtxpy,igl");
    setRuntimeFailurePolicy("error");
    setRuntimeSimulationMode("auto");
    setRuntimeDevice("gpu");
    applyPoSbrAdvancedSample();
  };

  const applyTdmPreset = () => {
    setRuntimeMultiplexingMode("tdm");
    setRuntimeBpmPhaseCodeText("");
    setRuntimeMultiplexingPlanJson("");
  };

  const applyBpmPreset = () => {
    setRuntimeMultiplexingMode("bpm");
    setRuntimeBpmPhaseCodeText("0,180,0,180");
    setRuntimeMultiplexingPlanJson("");
  };

  const applyCustomPreset = () => {
    setRuntimeMultiplexingMode("custom");
    setRuntimeBpmPhaseCodeText("");
    setRuntimeMultiplexingPlanJson(
      "{\"mode\":\"custom\",\"pulse_amp\":[[1,1,1,1],[1,1,1,1]],\"pulse_phs_deg\":[[0,0,0,0],[0,180,0,180]]}"
    );
  };

  const showMitsubaAdvanced = isSionnaStyleProvider(runtimeBackendType, runtimeProviderSpec);
  const showPoSbrAdvanced = isPoSbrProvider(runtimeBackendType, runtimeProviderSpec);

  return h(React.Fragment, null, [
    h("div", { className: "field", key: "runtime_purpose_presets" }, [
      h("label", { className: "label", key: "lbl_runtime_purpose_presets" }, "Purpose Presets"),
      h("div", { className: "btn-row", key: "runtime_purpose_preset_row" }, [
        h("button", {
          type: "button",
          className: "btn",
          key: "purpose_low_fidelity",
          onClick: applyLowFidelityPreset,
        }, "Low Fidelity: RadarSimPy + FFD"),
        h("button", {
          type: "button",
          className: "btn",
          key: "purpose_high_fidelity_sionna",
          onClick: applyHighFidelitySionnaPreset,
        }, "High Fidelity: Sionna-style RT"),
        h("button", {
          type: "button",
          className: "btn",
          key: "purpose_high_fidelity_po_sbr",
          onClick: applyHighFidelityPoSbrPreset,
        }, "High Fidelity: PO-SBR"),
      ]),
      h(
        "div",
        { className: "hint", key: "runtime_purpose_hint" },
        "Low fidelity uses RadarSimPy runtime; when FFD files are set, the repo synth applies antenna patterns on the returned paths. High fidelity maps to the Sionna-style or PO-SBR ray-tracing providers available in this repo."
      ),
    ]),
    h("div", { className: "field", key: "runtime_backend" }, [
      h("label", { className: "label", key: "lbl_runtime_backend" }, "Runtime Backend"),
      h("select", {
        className: "select",
        value: runtimeBackendType,
        onChange: (e) => setRuntimeBackendType(String(e.target.value || "analytic_targets")),
      }, [
        h("option", { value: "analytic_targets", key: "rb1" }, "analytic_targets"),
        h("option", { value: "radarsimpy_rt", key: "rb2" }, "radarsimpy_rt"),
        h("option", { value: "sionna_rt", key: "rb3" }, "sionna_rt"),
        h("option", { value: "po_sbr_rt", key: "rb4" }, "po_sbr_rt"),
      ]),
    ]),
    h("div", { className: "field", key: "runtime_provider" }, [
      h("label", { className: "label", key: "lbl_runtime_provider" }, "Runtime Provider (module:function)"),
      h("input", {
        className: "input",
        value: runtimeProviderSpec,
        onChange: (e) => setRuntimeProviderSpec(e.target.value),
        placeholder: "avxsim.runtime_providers.radarsimpy_rt_provider:generate_radarsimpy_like_paths",
      }),
    ]),
    h("div", { className: "field", key: "runtime_modules" }, [
      h("label", { className: "label", key: "lbl_runtime_modules" }, "Runtime Required Modules (comma/newline)"),
      h("textarea", {
        className: "textarea",
        value: runtimeRequiredModulesText,
        onChange: (e) => setRuntimeRequiredModulesText(e.target.value),
        placeholder: "radarsimpy",
        style: { minHeight: "62px" },
      }),
    ]),
    h("div", { className: "btn-row", key: "runtime_policy_row" }, [
      h("div", { className: "field", key: "runtime_failure_policy" }, [
        h("label", { className: "label", key: "lbl_runtime_failure_policy" }, "Failure Policy"),
        h("select", {
          className: "select",
          value: runtimeFailurePolicy,
          onChange: (e) => setRuntimeFailurePolicy(String(e.target.value || "error")),
        }, [
          h("option", { value: "error", key: "rfp1" }, "error"),
          h("option", { value: "use_static", key: "rfp2" }, "use_static"),
        ]),
      ]),
      h("div", { className: "field", key: "runtime_simulation_mode" }, [
        h("label", { className: "label", key: "lbl_runtime_simulation_mode" }, "Simulation Mode"),
        h("select", {
          className: "select",
          value: runtimeSimulationMode,
          onChange: (e) => setRuntimeSimulationMode(String(e.target.value || "auto")),
        }, [
          h("option", { value: "auto", key: "rsm1" }, "auto"),
          h("option", { value: "analytic_paths", key: "rsm2" }, "analytic_paths"),
          h("option", { value: "radarsimpy_adc", key: "rsm3" }, "radarsimpy_adc"),
        ]),
      ]),
      h("div", { className: "field", key: "runtime_multiplexing_mode" }, [
        h("label", { className: "label", key: "lbl_runtime_multiplexing_mode" }, "Multiplexing Mode"),
        h("select", {
          className: "select",
          value: runtimeMultiplexingMode,
          onChange: (e) => setRuntimeMultiplexingMode(String(e.target.value || "tdm")),
        }, [
          h("option", { value: "tdm", key: "rmm1" }, "tdm"),
          h("option", { value: "bpm", key: "rmm2" }, "bpm"),
          h("option", { value: "custom", key: "rmm3" }, "custom"),
        ]),
      ]),
    ]),
    h("div", { className: "btn-row", key: "runtime_license_row" }, [
      h("div", { className: "field", key: "runtime_device" }, [
        h("label", { className: "label", key: "lbl_runtime_device" }, "Runtime Device"),
        h("select", {
          className: "select",
          value: runtimeDevice,
          onChange: (e) => setRuntimeDevice(String(e.target.value || "cpu")),
        }, [
          h("option", { value: "cpu", key: "rdv1" }, "cpu"),
          h("option", { value: "gpu", key: "rdv2" }, "gpu"),
        ]),
      ]),
      h("div", { className: "field", key: "runtime_license_tier" }, [
        h("label", { className: "label", key: "lbl_runtime_license_tier" }, "License Tier"),
        h("select", {
          className: "select",
          value: runtimeLicenseTier,
          onChange: (e) => setRuntimeLicenseTier(String(e.target.value || "trial")),
        }, [
          h("option", { value: "trial", key: "rlt1" }, "trial"),
          h("option", { value: "production", key: "rlt2" }, "production"),
        ]),
      ]),
    ]),
    h("div", { className: "field", key: "runtime_license_file" }, [
      h("label", { className: "label", key: "lbl_runtime_license_file" }, "License File (runtime_input.license_file)"),
      h("input", {
        className: "input",
        value: runtimeLicenseFile,
        onChange: (e) => setRuntimeLicenseFile(e.target.value),
        placeholder: "/abs/path/license_RadarSimPy_*.lic",
      }),
    ]),
    h("div", { className: "field", key: "runtime_tx_ffd_files" }, [
      h("label", { className: "label", key: "lbl_runtime_tx_ffd_files" }, "TX FFD Files (comma/newline)"),
      h("textarea", {
        className: "textarea",
        value: runtimeTxFfdFilesText,
        onChange: (e) => setRuntimeTxFfdFilesText(e.target.value),
        placeholder: "/abs/path/tx0.ffd\n/abs/path/tx1.ffd",
        style: { minHeight: "62px" },
      }),
    ]),
    h("div", { className: "field", key: "runtime_rx_ffd_files" }, [
      h("label", { className: "label", key: "lbl_runtime_rx_ffd_files" }, "RX FFD Files (comma/newline)"),
      h("textarea", {
        className: "textarea",
        value: runtimeRxFfdFilesText,
        onChange: (e) => setRuntimeRxFfdFilesText(e.target.value),
        placeholder: "/abs/path/rx0.ffd\n/abs/path/rx1.ffd",
        style: { minHeight: "62px" },
      }),
      h(
        "div",
        { className: "hint", key: "runtime_ffd_hint" },
        "Provide both TX and RX lists together. FFD input is applied by the common FMCW synth path for RadarSimPy, Sionna-style RT, and PO-SBR backends."
      ),
    ]),
    showMitsubaAdvanced ? h(React.Fragment, { key: "runtime_mitsuba_advanced" }, [
      h("div", { className: "field", key: "runtime_mitsuba_header" }, [
        h("label", { className: "label", key: "lbl_runtime_mitsuba_header" }, "Sionna-style RT Advanced"),
        h("div", { className: "btn-row", key: "runtime_mitsuba_actions" }, [
          h("button", {
            type: "button",
            className: "btn",
            key: "runtime_mitsuba_sample",
            onClick: applyMitsubaAdvancedSample,
          }, "Load Mitsuba Sample"),
        ]),
        h(
          "div",
          { className: "hint", key: "runtime_mitsuba_hint" },
          "These fields map into runtime_input for the Mitsuba-backed path generator. A non-empty spheres JSON array is required."
        ),
      ]),
      h("div", { className: "btn-row", key: "runtime_mitsuba_numeric_row" }, [
        h("div", { className: "field", key: "runtime_mitsuba_ego_origin" }, [
          h("label", { className: "label", key: "lbl_runtime_mitsuba_ego_origin" }, "Mitsuba Ego Origin (x,y,z m)"),
          h("input", {
            className: "input",
            value: runtimeMitsubaEgoOriginText,
            onChange: (e) => setRuntimeMitsubaEgoOriginText(e.target.value),
            placeholder: "0,0,0",
          }),
        ]),
        h("div", { className: "field", key: "runtime_mitsuba_chirp_interval" }, [
          h("label", { className: "label", key: "lbl_runtime_mitsuba_chirp_interval" }, "Mitsuba Chirp Interval (s)"),
          h("input", {
            className: "input",
            value: runtimeMitsubaChirpIntervalText,
            onChange: (e) => setRuntimeMitsubaChirpIntervalText(e.target.value),
            placeholder: "4.0e-5",
          }),
        ]),
        h("div", { className: "field", key: "runtime_mitsuba_min_range" }, [
          h("label", { className: "label", key: "lbl_runtime_mitsuba_min_range" }, "Mitsuba Min Range (m)"),
          h("input", {
            className: "input",
            value: runtimeMitsubaMinRangeText,
            onChange: (e) => setRuntimeMitsubaMinRangeText(e.target.value),
            placeholder: "0.5",
          }),
        ]),
      ]),
      h("div", { className: "field", key: "runtime_mitsuba_spheres_json" }, [
        h("label", { className: "label", key: "lbl_runtime_mitsuba_spheres_json" }, "Mitsuba Spheres JSON"),
        h("textarea", {
          className: "textarea",
          value: runtimeMitsubaSpheresJson,
          onChange: (e) => setRuntimeMitsubaSpheresJson(e.target.value),
          placeholder: "[{\"center_m\":[22,0,0],\"radius_m\":0.45}]",
          style: { minHeight: "144px" },
        }),
      ]),
    ]) : null,
    showPoSbrAdvanced ? h(React.Fragment, { key: "runtime_po_sbr_advanced" }, [
      h("div", { className: "field", key: "runtime_po_sbr_header" }, [
        h("label", { className: "label", key: "lbl_runtime_po_sbr_header" }, "PO-SBR Advanced"),
        h("div", { className: "btn-row", key: "runtime_po_sbr_actions" }, [
          h("button", {
            type: "button",
            className: "btn",
            key: "runtime_po_sbr_sample",
            onClick: applyPoSbrAdvancedSample,
          }, "Load PO-SBR Sample"),
        ]),
        h(
          "div",
          { className: "hint", key: "runtime_po_sbr_hint" },
          "Repo root is resolved relative to the current working directory. Geometry path is resolved relative to that repo root when not absolute."
        ),
      ]),
      h("div", { className: "btn-row", key: "runtime_po_sbr_paths_row" }, [
        h("div", { className: "field", key: "runtime_po_sbr_repo_root" }, [
          h("label", { className: "label", key: "lbl_runtime_po_sbr_repo_root" }, "PO-SBR Repo Root"),
          h("input", {
            className: "input",
            value: runtimePoSbrRepoRoot,
            onChange: (e) => setRuntimePoSbrRepoRoot(e.target.value),
            placeholder: "external/PO-SBR-Python",
          }),
        ]),
        h("div", { className: "field", key: "runtime_po_sbr_geometry_path" }, [
          h("label", { className: "label", key: "lbl_runtime_po_sbr_geometry_path" }, "PO-SBR Geometry Path"),
          h("input", {
            className: "input",
            value: runtimePoSbrGeometryPath,
            onChange: (e) => setRuntimePoSbrGeometryPath(e.target.value),
            placeholder: "geometries/plate.obj",
          }),
        ]),
      ]),
      h("div", { className: "btn-row", key: "runtime_po_sbr_numeric_row_1" }, [
        h("div", { className: "field", key: "runtime_po_sbr_chirp_interval" }, [
          h("label", { className: "label", key: "lbl_runtime_po_sbr_chirp_interval" }, "PO-SBR Chirp Interval (s)"),
          h("input", {
            className: "input",
            value: runtimePoSbrChirpIntervalText,
            onChange: (e) => setRuntimePoSbrChirpIntervalText(e.target.value),
            placeholder: "4.0e-5",
          }),
        ]),
        h("div", { className: "field", key: "runtime_po_sbr_bounces" }, [
          h("label", { className: "label", key: "lbl_runtime_po_sbr_bounces" }, "PO-SBR Bounces"),
          h("input", {
            className: "input",
            value: runtimePoSbrBouncesText,
            onChange: (e) => setRuntimePoSbrBouncesText(e.target.value),
            placeholder: "2",
          }),
        ]),
        h("div", { className: "field", key: "runtime_po_sbr_rays_per_lambda" }, [
          h("label", { className: "label", key: "lbl_runtime_po_sbr_rays_per_lambda" }, "PO-SBR Rays/Lambda"),
          h("input", {
            className: "input",
            value: runtimePoSbrRaysPerLambdaText,
            onChange: (e) => setRuntimePoSbrRaysPerLambdaText(e.target.value),
            placeholder: "3.0",
          }),
        ]),
      ]),
      h("div", { className: "btn-row", key: "runtime_po_sbr_numeric_row_2" }, [
        h("div", { className: "field", key: "runtime_po_sbr_alpha_deg" }, [
          h("label", { className: "label", key: "lbl_runtime_po_sbr_alpha_deg" }, "PO-SBR Alpha (deg)"),
          h("input", {
            className: "input",
            value: runtimePoSbrAlphaDegText,
            onChange: (e) => setRuntimePoSbrAlphaDegText(e.target.value),
            placeholder: "180",
          }),
        ]),
        h("div", { className: "field", key: "runtime_po_sbr_phi_deg" }, [
          h("label", { className: "label", key: "lbl_runtime_po_sbr_phi_deg" }, "PO-SBR Phi (deg)"),
          h("input", {
            className: "input",
            value: runtimePoSbrPhiDegText,
            onChange: (e) => setRuntimePoSbrPhiDegText(e.target.value),
            placeholder: "90",
          }),
        ]),
        h("div", { className: "field", key: "runtime_po_sbr_theta_deg" }, [
          h("label", { className: "label", key: "lbl_runtime_po_sbr_theta_deg" }, "PO-SBR Theta (deg)"),
          h("input", {
            className: "input",
            value: runtimePoSbrThetaDegText,
            onChange: (e) => setRuntimePoSbrThetaDegText(e.target.value),
            placeholder: "90",
          }),
        ]),
      ]),
      h("div", { className: "btn-row", key: "runtime_po_sbr_numeric_row_3" }, [
        h("div", { className: "field", key: "runtime_po_sbr_radial_velocity" }, [
          h("label", { className: "label", key: "lbl_runtime_po_sbr_radial_velocity" }, "PO-SBR Radial Velocity (m/s)"),
          h("input", {
            className: "input",
            value: runtimePoSbrRadialVelocityText,
            onChange: (e) => setRuntimePoSbrRadialVelocityText(e.target.value),
            placeholder: "0.0",
          }),
        ]),
        h("div", { className: "field", key: "runtime_po_sbr_min_range" }, [
          h("label", { className: "label", key: "lbl_runtime_po_sbr_min_range" }, "PO-SBR Min Range (m)"),
          h("input", {
            className: "input",
            value: runtimePoSbrMinRangeText,
            onChange: (e) => setRuntimePoSbrMinRangeText(e.target.value),
            placeholder: "0.5",
          }),
        ]),
      ]),
      h("div", { className: "btn-row", key: "runtime_po_sbr_text_row" }, [
        h("div", { className: "field", key: "runtime_po_sbr_material_tag" }, [
          h("label", { className: "label", key: "lbl_runtime_po_sbr_material_tag" }, "PO-SBR Material Tag"),
          h("input", {
            className: "input",
            value: runtimePoSbrMaterialTag,
            onChange: (e) => setRuntimePoSbrMaterialTag(e.target.value),
            placeholder: "po_sbr_runtime",
          }),
        ]),
        h("div", { className: "field", key: "runtime_po_sbr_path_id_prefix" }, [
          h("label", { className: "label", key: "lbl_runtime_po_sbr_path_id_prefix" }, "PO-SBR Path ID Prefix"),
          h("input", {
            className: "input",
            value: runtimePoSbrPathIdPrefix,
            onChange: (e) => setRuntimePoSbrPathIdPrefix(e.target.value),
            placeholder: "po_sbr_runtime",
          }),
        ]),
      ]),
      h("div", { className: "field", key: "runtime_po_sbr_components_json" }, [
        h("label", { className: "label", key: "lbl_runtime_po_sbr_components_json" }, "PO-SBR Components JSON"),
        h("textarea", {
          className: "textarea",
          value: runtimePoSbrComponentsJson,
          onChange: (e) => setRuntimePoSbrComponentsJson(e.target.value),
          placeholder: "[{\"phi_deg\":78,\"theta_deg\":90,\"path_id_prefix\":\"po_lane_left\"}]",
          style: { minHeight: "132px" },
        }),
      ]),
    ]) : null,
    h("div", { className: "field", key: "runtime_mux_presets" }, [
      h("label", { className: "label", key: "lbl_runtime_mux_presets" }, "Multiplexing Presets"),
      h("div", { className: "btn-row", key: "runtime_mux_preset_row" }, [
        h("button", {
          type: "button",
          className: "btn",
          key: "mux_preset_tdm",
          onClick: applyTdmPreset,
        }, "Preset: TDM"),
        h("button", {
          type: "button",
          className: "btn",
          key: "mux_preset_bpm",
          onClick: applyBpmPreset,
        }, "Preset: BPM 2TX"),
        h("button", {
          type: "button",
          className: "btn",
          key: "mux_preset_custom",
          onClick: applyCustomPreset,
        }, "Preset: Custom"),
      ]),
    ]),
    h("div", { className: "field", key: "runtime_bpm_phase_code" }, [
      h("label", { className: "label", key: "lbl_runtime_bpm_phase_code" }, "BPM Phase Code (deg, comma/newline)"),
      h("input", {
        className: "input",
        value: runtimeBpmPhaseCodeText,
        onChange: (e) => setRuntimeBpmPhaseCodeText(e.target.value),
        placeholder: "0,180,0,180",
      }),
    ]),
    h("div", { className: "field", key: "runtime_multiplexing_plan_json" }, [
      h("label", { className: "label", key: "lbl_runtime_multiplexing_plan_json" }, "Multiplexing Plan JSON (optional)"),
      h("textarea", {
        className: "textarea",
        value: runtimeMultiplexingPlanJson,
        onChange: (e) => setRuntimeMultiplexingPlanJson(e.target.value),
        placeholder: "{\"mode\":\"custom\",\"pulse_amp\":[[1,1,1,1],[1,1,1,1]],\"pulse_phs_deg\":[[0,0,0,0],[0,180,0,180]]}",
        style: { minHeight: "72px" },
      }),
    ]),
    h("div", { className: "field", key: "runtime_diagnostics" }, [
      h("label", { className: "label", key: "lbl_runtime_diagnostics" }, "Runtime Diagnostics"),
      h("div", { className: "chip-list", key: "runtime_diagnostics_chips" }, (
        Array.isArray(runtimeDiagnosticBadges) && runtimeDiagnosticBadges.length > 0
          ? runtimeDiagnosticBadges
          : [{ label: "state:idle", tone: "status-neutral" }]
      ).map((row, idx) =>
        h("span", {
          className: `chip ${String(row?.tone || "status-neutral")}`,
          key: `runtime_diag_chip_${idx}`,
        }, String(row?.label || "-"))
      )),
      h("pre", {
        className: "result-box",
        key: "runtime_diagnostics_box",
        style: { minHeight: "86px" },
      }, String(runtimeDiagnosticText || `runtime_status: ${String(runtimeStatusLine || "-")}`)),
      h("div", { className: "hint", key: "runtime_status_hint" }, `runtime_status: ${String(runtimeStatusLine || "-")}`),
    ]),
  ]);
}
