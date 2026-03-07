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

const mitsubaBase = {
  ...base,
  runtimeBackendType: "sionna_rt",
  runtimeProviderSpec: "avxsim.runtime_providers.mitsuba_rt_provider:generate_sionna_like_paths_from_mitsuba",
  runtimeRequiredModulesText: "mitsuba,drjit",
};

const poSbrBase = {
  ...base,
  runtimeBackendType: "po_sbr_rt",
  runtimeProviderSpec: "avxsim.runtime_providers.po_sbr_rt_provider:generate_po_sbr_like_paths_from_posbr",
  runtimeRequiredModulesText: "rtxpy,igl",
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

{
  const out = buildSceneOverrides({
    ...mitsubaBase,
    runtimeMitsubaEgoOriginText: "0,1,2",
    runtimeMitsubaChirpIntervalText: "4.0e-5",
    runtimeMitsubaMinRangeText: "0.5",
    runtimeMitsubaSpheresJson: JSON.stringify([
      {
        center_m: [22.0, 0.0, 0.0],
        radius_m: 0.45,
        velocity_mps: [-1.0, 0.0, 0.0],
      },
    ]),
  });
  assert.deepEqual(out.backend.runtime_input.ego_origin_m, [0, 1, 2]);
  assert.equal(out.backend.runtime_input.chirp_interval_s, 4.0e-5);
  assert.equal(out.backend.runtime_input.min_range_m, 0.5);
  assert.equal(Array.isArray(out.backend.runtime_input.spheres), true);
  assert.equal(out.backend.runtime_input.spheres.length, 1);
}

{
  const out = buildSceneOverrides({
    ...poSbrBase,
    runtimePoSbrRepoRoot: "external/PO-SBR-Python",
    runtimePoSbrGeometryPath: "geometries/plate.obj",
    runtimePoSbrChirpIntervalText: "4.0e-5",
    runtimePoSbrBouncesText: "2",
    runtimePoSbrRaysPerLambdaText: "3.0",
    runtimePoSbrAlphaDegText: "180",
    runtimePoSbrPhiDegText: "90",
    runtimePoSbrThetaDegText: "90",
    runtimePoSbrRadialVelocityText: "-2.5",
    runtimePoSbrMinRangeText: "0.5",
    runtimePoSbrMaterialTag: "guardrail",
    runtimePoSbrPathIdPrefix: "po_lane_left",
    runtimePoSbrComponentsJson: JSON.stringify([
      { phi_deg: 78.0, theta_deg: 90.0, path_id_prefix: "po_lane_left" },
    ]),
  });
  assert.equal(out.backend.runtime_input.po_sbr_repo_root, "external/PO-SBR-Python");
  assert.equal(out.backend.runtime_input.geometry_path, "geometries/plate.obj");
  assert.equal(out.backend.runtime_input.bounces, 2);
  assert.equal(out.backend.runtime_input.rays_per_lambda, 3.0);
  assert.equal(out.backend.runtime_input.alpha_deg, 180);
  assert.equal(out.backend.runtime_input.radial_velocity_mps, -2.5);
  assert.equal(out.backend.runtime_input.material_tag, "guardrail");
  assert.equal(out.backend.runtime_input.path_id_prefix, "po_lane_left");
  assert.equal(Array.isArray(out.backend.runtime_input.components), true);
  assert.equal(out.backend.runtime_input.components.length, 1);
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
expectThrow(
  () => buildSceneOverrides({ ...mitsubaBase, runtimeMitsubaEgoOriginText: "0,1" }),
  "must have exactly 3 numeric values"
);
expectThrow(
  () => buildSceneOverrides({ ...mitsubaBase, runtimeMitsubaSpheresJson: "{\"bad\":true}" }),
  "must decode to a JSON array"
);
expectThrow(
  () => buildSceneOverrides({ ...poSbrBase, runtimePoSbrBouncesText: "-1" }),
  "must be >= 0"
);
expectThrow(
  () => buildSceneOverrides({ ...poSbrBase, runtimePoSbrComponentsJson: "[1,2,3]" }),
  "must be an object"
);

console.log("validate_graph_lab_runtime_overrides: pass");
