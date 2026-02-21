# Path Power Fit Cycle Contract

## Goal

Automate one cycle:

1. baseline ingest
2. build `path_power_samples.csv` from baseline `path_list.json`
3. fit path-power parameters
4. tuned ingest with `--path-power-fit-json`
5. summarize amplitude-vs-range slope change

## CLI

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_path_power_fit_cycle.py \
  --frames-root /path/to/frames_root \
  --radar-json /path/to/radar_parameters_hybrid.json \
  --frame-start 1 \
  --frame-end 64 \
  --camera-fov-deg 90 \
  --mode reflection \
  --file-ext .npy \
  --path-power-apply-mode replace \
  --work-root /path/to/cycle_work \
  --scenario-id scenario_name
```

## Main Outputs

- `<work-root>/baseline_ingest`
- `<work-root>/path_power_samples.csv`
- `<work-root>/path_power_fit_<mode>.json`
- `<work-root>/tuned_ingest`
- `<work-root>/path_power_cycle_summary.json`

## Summary JSON

Contains:

- selected commands
- fit parameters/metrics
- baseline/tuned `log_slope` of `log(amplitude)` vs `log(range)`
- optional parity comparison (when `--run-hybrid-estimation` is used)

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_path_power_fit_cycle.py
```
