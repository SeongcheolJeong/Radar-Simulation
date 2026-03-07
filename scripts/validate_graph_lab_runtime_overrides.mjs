#!/usr/bin/env node
import assert from "node:assert/strict";

import { buildSceneOverrides } from "../frontend/graph_lab/runtime_overrides.mjs";

function expectThrow(fn, text) {
  let thrown = false;
  try {
    fn();
  } catch (err) {
    thrown = true;
    const msg = String(err?.message || err);
    assert.ok(
      msg.includes(text),
      `expected error message to include "${text}", got "${msg}"`
    );
  }
  assert.ok(thrown, `expected function to throw: ${text}`);
}

const base = {
  runtimeBackendType: "radarsimpy_rt",
  runtimeProviderSpec: "avxsim.runtime_providers.radarsimpy_rt_provider:generate_radarsimpy_like_paths",
  runtimeRequiredModulesText: "radarsimpy",
  runtimeFailurePolicy: "error",
  runtimeSimulationMode: "radarsimpy_adc",
  runtimeDevice: "cpu",
  runtimeLicenseTier: "production",
  runtimeLicenseFile: "/tmp/license.lic",
};

{
  const out = buildSceneOverrides({
    ...base,
    runtimeMultiplexingMode: "bpm",
    runtimeBpmPhaseCodeText: "0,180,0,180",
    runtimeMultiplexingPlanJson: "",
  });
  assert.equal(out.backend.type, "radarsimpy_rt");
  assert.equal(out.backend.runtime_input.multiplexing_mode, "bpm");
  assert.deepEqual(out.backend.runtime_input.bpm_phase_code_deg, [0, 180, 0, 180]);
}

{
  const out = buildSceneOverrides({
    ...base,
    runtimeMultiplexingMode: "custom",
    runtimeMultiplexingPlanJson: JSON.stringify({
      mode: "custom",
      pulse_amp: [[1, 1], [1, 1]],
      pulse_phs_deg: [[0, 0], [0, 180]],
    }),
  });
  assert.equal(out.backend.runtime_input.multiplexing_mode, "custom");
  assert.equal(out.backend.runtime_input.tx_multiplexing_plan.mode, "custom");
}

{
  const out = buildSceneOverrides({
    ...base,
    runtimeTxFfdFilesText: "/tmp/tx0.ffd,\n/tmp/tx1.ffd",
    runtimeRxFfdFilesText: "/tmp/rx0.ffd\n/tmp/rx1.ffd",
  });
  assert.deepEqual(out.backend.tx_ffd_files, ["/tmp/tx0.ffd", "/tmp/tx1.ffd"]);
  assert.deepEqual(out.backend.rx_ffd_files, ["/tmp/rx0.ffd", "/tmp/rx1.ffd"]);
}

expectThrow(
  () => buildSceneOverrides({ ...base, runtimeMultiplexingMode: "invalid_mode" }),
  "runtime multiplexing mode must be one of"
);
expectThrow(
  () => buildSceneOverrides({ ...base, runtimeMultiplexingMode: "bpm", runtimeBpmPhaseCodeText: "0,abc" }),
  "contains non-numeric token"
);
expectThrow(
  () => buildSceneOverrides({
    ...base,
    runtimeMultiplexingMode: "custom",
    runtimeMultiplexingPlanJson: "{\"mode\":\"custom\",\"pulse_amp\":\"bad\"}",
  }),
  "pulse_amp"
);
expectThrow(
  () => buildSceneOverrides({ ...base, runtimeTxFfdFilesText: "/tmp/tx0.ffd" }),
  "runtime tx/rx FFD files must be provided together"
);

console.log("validate_graph_lab_runtime_overrides: pass");
