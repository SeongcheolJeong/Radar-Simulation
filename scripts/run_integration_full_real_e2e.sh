#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${ROOT_DIR}" ]]; then
  ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fi
cd "${ROOT_DIR}"

PYTHON_BIN="${PYTHON_BIN:-}"
if [[ -z "${PYTHON_BIN}" ]]; then
  for candidate in \
    "${ROOT_DIR}/.venv/bin/python" \
    "${ROOT_DIR}/.venv-po-sbr/bin/python" \
    "python3"; do
    if [[ "${candidate}" == "python3" ]]; then
      if command -v python3 >/dev/null 2>&1; then
        PYTHON_BIN="python3"
        break
      fi
    elif [[ -x "${candidate}" ]]; then
      PYTHON_BIN="${candidate}"
      break
    fi
  done
fi

if [[ -z "${PYTHON_BIN}" ]]; then
  echo "[real-e2e] error: python runtime not found (.venv/.venv-po-sbr/python3)" >&2
  exit 1
fi

abspath() {
  "${PYTHON_BIN}" - "$1" <<'PY'
import os
import sys

print(os.path.abspath(os.path.expanduser(sys.argv[1])))
PY
}

NOW_STAMP="$(date -u +%Y_%m_%d_%H%M%S)"
OUTPUT_ROOT_RAW="${1:-${ROOT_DIR}/docs/reports/integration_full_real_e2e_${NOW_STAMP}}"
OUTPUT_ROOT="$(abspath "${OUTPUT_ROOT_RAW}")"
mkdir -p "${OUTPUT_ROOT}"

CARLA_RUNTIME_ROOT_RAW="${CARLA_RUNTIME_ROOT:-${ROOT_DIR}/external/carla_runtime}"
CARLA_RUNTIME_ROOT="$(abspath "${CARLA_RUNTIME_ROOT_RAW}")"
CARLA_PORT="${CARLA_PORT:-2000}"
CARLA_WAIT_SECONDS="${CARLA_WAIT_SECONDS:-90}"
START_CARLA_IF_NEEDED="${START_CARLA_IF_NEEDED:-1}"
INSTALL_CARLA_WHEEL="${INSTALL_CARLA_WHEEL:-1}"

RADARSIMPY_PACKAGE_ROOT_RAW="${RADARSIMPY_PACKAGE_ROOT:-${ROOT_DIR}/external/radarsimpy_trial/Ubuntu24_x86_64_CPU/Ubuntu24_x86_64_CPU}"
RADARSIMPY_LIB_ROOT_RAW="${RADARSIMPY_LIB_ROOT:-${ROOT_DIR}/external/radarsimpy_trial/libcompat/usr/lib/x86_64-linux-gnu}"
RADARSIMPY_PACKAGE_ROOT="$(abspath "${RADARSIMPY_PACKAGE_ROOT_RAW}")"
RADARSIMPY_LIB_ROOT="$(abspath "${RADARSIMPY_LIB_ROOT_RAW}")"
RADARSIMPY_PILOT_TRIAL_FREE_TIER_GEOMETRY="${RADARSIMPY_PILOT_TRIAL_FREE_TIER_GEOMETRY:-1}"
RUN_RADARSIMPY_MIGRATION_STEPWISE="${RUN_RADARSIMPY_MIGRATION_STEPWISE:-1}"
RADARSIMPY_MIGRATION_TRIAL_FREE_TIER_GEOMETRY="${RADARSIMPY_MIGRATION_TRIAL_FREE_TIER_GEOMETRY:-${RADARSIMPY_PILOT_TRIAL_FREE_TIER_GEOMETRY}}"

log() {
  echo "[real-e2e] $*"
}

port_listening() {
  local port="$1"
  ss -ltn | rg -q ":${port}[[:space:]]"
}

install_matching_carla_wheel() {
  if [[ "${INSTALL_CARLA_WHEEL}" != "1" ]]; then
    log "skip CARLA wheel installation (INSTALL_CARLA_WHEEL=${INSTALL_CARLA_WHEEL})"
    return 0
  fi

  local dist_dir="${CARLA_RUNTIME_ROOT}/PythonAPI/carla/dist"
  if [[ ! -d "${dist_dir}" ]]; then
    log "CARLA wheel dist directory missing: ${dist_dir} (skip install)"
    return 0
  fi

  local py_tag
  py_tag="$("${PYTHON_BIN}" - <<'PY'
import sys
print(f"cp{sys.version_info.major}{sys.version_info.minor}")
PY
)"

  local wheel_path
  wheel_path="$(ls -1 "${dist_dir}"/carla-*-"${py_tag}"-"${py_tag}"-manylinux*_x86_64.whl 2>/dev/null | head -n 1 || true)"
  if [[ -z "${wheel_path}" ]]; then
    log "matching CARLA wheel not found for ${py_tag} under ${dist_dir} (skip install)"
    return 0
  fi

  log "install CARLA wheel: ${wheel_path}"
  "${PYTHON_BIN}" -m pip install --force-reinstall --no-deps "${wheel_path}" >/dev/null
}

start_carla_server_if_needed() {
  if port_listening "${CARLA_PORT}"; then
    log "CARLA RPC port ${CARLA_PORT} already listening; reuse existing server"
    return 0
  fi

  if [[ "${START_CARLA_IF_NEEDED}" != "1" ]]; then
    log "CARLA is not listening on ${CARLA_PORT} and START_CARLA_IF_NEEDED=${START_CARLA_IF_NEEDED}"
    return 1
  fi

  local entry="${CARLA_RUNTIME_ROOT}/CarlaUE4.sh"
  if [[ ! -x "${entry}" ]]; then
    log "CARLA launcher missing: ${entry}"
    return 1
  fi

  local server_log="${OUTPUT_ROOT}/carla_server.log"
  local server_pid_file="${OUTPUT_ROOT}/carla_server.pid"

  log "starting CARLA server from ${entry} on port ${CARLA_PORT}"
  (
    cd "${CARLA_RUNTIME_ROOT}"
    nohup ./CarlaUE4.sh \
      -RenderOffScreen \
      -nosound \
      -quality-level=Low \
      -carla-rpc-port="${CARLA_PORT}" \
      > "${server_log}" 2>&1 &
    echo "$!" > "${server_pid_file}"
  )

  local pid
  pid="$(cat "${server_pid_file}")"
  for ((i=1; i<=CARLA_WAIT_SECONDS; i++)); do
    if ! ps -p "${pid}" >/dev/null 2>&1; then
      log "CARLA process exited before port became ready (pid=${pid})"
      [[ -f "${server_log}" ]] && tail -n 80 "${server_log}" || true
      return 1
    fi
    if port_listening "${CARLA_PORT}"; then
      log "CARLA port ${CARLA_PORT} is now listening (pid=${pid})"
      return 0
    fi
    sleep 1
  done

  log "CARLA did not become ready within ${CARLA_WAIT_SECONDS}s"
  [[ -f "${server_log}" ]] && tail -n 120 "${server_log}" || true
  return 1
}

require_script() {
  local path="$1"
  if [[ ! -f "${path}" ]]; then
    echo "[real-e2e] error: missing script ${path}" >&2
    exit 1
  fi
}

require_script "scripts/run_scene_runtime_env_probe.py"
require_script "scripts/run_scene_runtime_blocker_report.py"
require_script "scripts/run_scene_runtime_radarsimpy_pilot.py"
require_script "scripts/run_radarsimpy_migration_stepwise.py"
require_script "scripts/run_scene_runtime_mitsuba_pilot.py"
require_script "scripts/run_scene_runtime_po_sbr_pilot.py"
require_script "scripts/run_scene_backend_golden_path.py"
require_script "scripts/run_scene_backend_kpi_scenario_matrix.py"

if [[ -d "${RADARSIMPY_PACKAGE_ROOT}" ]]; then
  export PYTHONPATH="src:${RADARSIMPY_PACKAGE_ROOT}${PYTHONPATH:+:${PYTHONPATH}}"
else
  export PYTHONPATH="src${PYTHONPATH:+:${PYTHONPATH}}"
  log "warning: RADARSIMPY package path not found: ${RADARSIMPY_PACKAGE_ROOT}"
fi

if [[ -d "${RADARSIMPY_LIB_ROOT}" ]]; then
  export LD_LIBRARY_PATH="${RADARSIMPY_LIB_ROOT}${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
else
  log "warning: RADARSIMPY lib path not found: ${RADARSIMPY_LIB_ROOT}"
fi

log "ROOT_DIR=${ROOT_DIR}"
log "OUTPUT_ROOT=${OUTPUT_ROOT}"
log "PYTHON_BIN=${PYTHON_BIN}"
log "CARLA_RUNTIME_ROOT=${CARLA_RUNTIME_ROOT}"
log "CARLA_PORT=${CARLA_PORT}"
log "RADARSIMPY_PACKAGE_ROOT=${RADARSIMPY_PACKAGE_ROOT}"
log "RADARSIMPY_LIB_ROOT=${RADARSIMPY_LIB_ROOT}"

install_matching_carla_wheel
start_carla_server_if_needed

declare -a FAILED_STEPS=()

run_step() {
  local name="$1"
  shift
  local log_path="${OUTPUT_ROOT}/${name}.log"
  local meta_path="${OUTPUT_ROOT}/${name}.meta"
  local cmd_path="${OUTPUT_ROOT}/${name}.meta.cmd"
  local rc_path="${OUTPUT_ROOT}/${name}.rc"

  {
    echo "timestamp=$(date -Iseconds)"
    echo "cwd=${ROOT_DIR}"
  } > "${meta_path}"

  printf 'cmd=%q ' "$@" > "${cmd_path}"
  echo >> "${cmd_path}"

  log "step=${name}"
  set +e
  "$@" > "${log_path}" 2>&1
  local rc=$?
  set -e
  echo "${rc}" > "${rc_path}"
  echo "rc=${rc}" >> "${meta_path}"

  if [[ "${rc}" -ne 0 ]]; then
    FAILED_STEPS+=("${name}")
    log "step=${name} failed (rc=${rc})"
  else
    log "step=${name} passed"
  fi
}

CARLA_PROBE_PY="${OUTPUT_ROOT}/_carla_client_probe.py"
cat > "${CARLA_PROBE_PY}" <<'PY'
import json
import sys
import time

import carla

if len(sys.argv) != 3:
    raise SystemExit("usage: _carla_client_probe.py <out_json> <port>")

out_json = str(sys.argv[1]).strip()
port = int(sys.argv[2])
payload = {"connect_target": f"127.0.0.1:{port}"}

try:
    client = carla.Client("127.0.0.1", port)
    client.set_timeout(20.0)
    world = client.get_world()
    payload["ok"] = True
    payload["server_version"] = client.get_server_version()
    payload["client_version"] = client.get_client_version()
    payload["map_name"] = world.get_map().name
    payload["actor_count"] = len(world.get_actors())
except Exception as exc:
    payload["ok"] = False
    payload["error"] = f"{type(exc).__name__}: {exc}"

payload["timestamp"] = time.time()
with open(out_json, "w", encoding="utf-8") as f:
    json.dump(payload, f, indent=2)
print(json.dumps(payload, indent=2))
PY

run_step runtime_probe \
  "${PYTHON_BIN}" scripts/run_scene_runtime_env_probe.py \
  --workspace-root "${ROOT_DIR}" \
  --output-summary-json "${OUTPUT_ROOT}/runtime_probe.json"

run_step runtime_blockers \
  "${PYTHON_BIN}" scripts/run_scene_runtime_blocker_report.py \
  --probe-summary-json "${OUTPUT_ROOT}/runtime_probe.json" \
  --output-report-json "${OUTPUT_ROOT}/runtime_blockers.json"

run_step carla_client_probe \
  "${PYTHON_BIN}" "${CARLA_PROBE_PY}" \
  "${OUTPUT_ROOT}/carla_client_probe.json" \
  "${CARLA_PORT}"

run_step radarsimpy_pilot \
  "${PYTHON_BIN}" scripts/run_scene_runtime_radarsimpy_pilot.py \
  --output-root "${OUTPUT_ROOT}/radarsimpy_pilot" \
  --output-summary-json "${OUTPUT_ROOT}/radarsimpy_pilot_summary.json" \
  --runtime-failure-policy error \
  $([[ "${RADARSIMPY_PILOT_TRIAL_FREE_TIER_GEOMETRY}" == "1" ]] && echo "--trial-free-tier-geometry")

if [[ "${RUN_RADARSIMPY_MIGRATION_STEPWISE}" == "1" ]]; then
  run_step radarsimpy_migration_stepwise \
    "${PYTHON_BIN}" scripts/run_radarsimpy_migration_stepwise.py \
    --output-root "${OUTPUT_ROOT}/radarsimpy_migration_stepwise" \
    --output-summary-json "${OUTPUT_ROOT}/radarsimpy_migration_stepwise_summary.json" \
    --n-chirps 6 \
    --samples-per-chirp 512 \
    --runtime-failure-policy error \
    --require-runtime-provider-mode \
    --require-radarsimpy-simulation-used \
    $([[ "${RADARSIMPY_MIGRATION_TRIAL_FREE_TIER_GEOMETRY}" == "1" ]] && echo "--trial-free-tier-geometry")
else
  log "skip radarsimpy migration stepwise gate (RUN_RADARSIMPY_MIGRATION_STEPWISE=${RUN_RADARSIMPY_MIGRATION_STEPWISE})"
fi

run_step mitsuba_pilot \
  "${PYTHON_BIN}" scripts/run_scene_runtime_mitsuba_pilot.py \
  --output-root "${OUTPUT_ROOT}/mitsuba_pilot" \
  --output-summary-json "${OUTPUT_ROOT}/mitsuba_pilot_summary.json"

run_step po_sbr_pilot \
  "${PYTHON_BIN}" scripts/run_scene_runtime_po_sbr_pilot.py \
  --output-root "${OUTPUT_ROOT}/po_sbr_pilot" \
  --output-summary-json "${OUTPUT_ROOT}/po_sbr_pilot_summary.json"

run_step golden_path \
  "${PYTHON_BIN}" scripts/run_scene_backend_golden_path.py \
  --strict-nonexecuted \
  --output-root "${OUTPUT_ROOT}/golden_path_outputs" \
  --output-summary-json "${OUTPUT_ROOT}/scene_backend_golden_path.json"

run_step kpi_matrix \
  "${PYTHON_BIN}" scripts/run_scene_backend_kpi_scenario_matrix.py \
  --strict-all-ready \
  --python-bin "${PYTHON_BIN}" \
  --output-root "${OUTPUT_ROOT}/kpi_matrix_outputs" \
  --output-summary-json "${OUTPUT_ROOT}/scene_backend_kpi_scenario_matrix.json"

STATUS_ROLLUP_JSON="${OUTPUT_ROOT}/_status_rollup.json"
"${PYTHON_BIN}" - "${OUTPUT_ROOT}" "${STATUS_ROLLUP_JSON}" <<'PY'
import glob
import json
import os
import sys

out_root = str(sys.argv[1]).strip()
out_json = str(sys.argv[2]).strip()
rc_map = {}
for path in sorted(glob.glob(os.path.join(out_root, "*.rc"))):
    key = os.path.basename(path)[:-3]
    try:
        rc_map[key] = int(open(path, "r", encoding="utf-8").read().strip())
    except Exception:
        rc_map[key] = 255

rollup = {
    "output_root": out_root,
    "step_rcs": rc_map,
    "failed_steps": sorted([k for k, v in rc_map.items() if int(v) != 0]),
    "all_steps_passed": all(int(v) == 0 for v in rc_map.values()),
}
with open(out_json, "w", encoding="utf-8") as f:
    json.dump(rollup, f, indent=2)
print(json.dumps(rollup, indent=2))
PY

if [[ "${#FAILED_STEPS[@]}" -gt 0 ]]; then
  log "completed with failures: ${FAILED_STEPS[*]}"
  log "report bundle: ${OUTPUT_ROOT}"
  exit 1
fi

log "completed successfully"
log "report bundle: ${OUTPUT_ROOT}"
exit 0
