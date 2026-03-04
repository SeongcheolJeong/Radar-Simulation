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
  runtimeDevice,
  setRuntimeDevice,
  runtimeLicenseTier,
  setRuntimeLicenseTier,
  runtimeLicenseFile,
  setRuntimeLicenseFile,
  runtimeStatusLine,
}) {
  return h(React.Fragment, null, [
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
    h("div", { className: "hint", key: "runtime_status_hint" }, `runtime_status: ${String(runtimeStatusLine || "-")}`),
  ]);
}
