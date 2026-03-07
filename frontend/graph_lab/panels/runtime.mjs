import { React } from "../deps.mjs";

const h = React.createElement;

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
  runtimeStatusLine,
}) {
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
    setRuntimeRequiredModulesText("mitsuba");
    setRuntimeFailurePolicy("error");
    setRuntimeSimulationMode("auto");
    setRuntimeDevice("gpu");
  };

  const applyHighFidelityPoSbrPreset = () => {
    setRuntimeBackendType("po_sbr_rt");
    setRuntimeProviderSpec(
      "avxsim.runtime_providers.po_sbr_rt_provider:generate_po_sbr_like_paths_from_posbr"
    );
    setRuntimeRequiredModulesText("");
    setRuntimeFailurePolicy("error");
    setRuntimeSimulationMode("auto");
    setRuntimeDevice("gpu");
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
    h("div", { className: "hint", key: "runtime_status_hint" }, `runtime_status: ${String(runtimeStatusLine || "-")}`),
  ]);
}
