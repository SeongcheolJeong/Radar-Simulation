import { React } from "../deps.mjs";

const h = React.createElement;

export function ContractDiagnosticsPanel({ contractDebugText }) {
  return h("div", { className: "field", key: "contractdiagauto" }, [
    h("label", { className: "label", key: "lblcda" }, "Contract Diagnostics (Auto)"),
    h("pre", { className: "result-box", key: "contractboxauto" }, String(contractDebugText || "-")),
  ]);
}
