# AVX-Style FMCW/TDM Radar Simulator (Reference Build)

This repository is being organized toward an AVX-like radar simulation pipeline:

1. Path list output (for debug and physical interpretation)
2. Raw ADC cube output (for DSP compatibility)

Current implementation status is tracked in `/Users/seongcheoljeong/Documents/Codex_test/docs/01_execution_plan.md`.

## Quick Start

Use this Python binary in this workspace:

```bash
PY=/Library/Developer/CommandLineTools/usr/bin/python3
```

Install dependency:

```bash
$PY -m pip install --user numpy
```

Run step-1 validation:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_step1.py
```

Run adapter smoke validation:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_adapter_smoke.py
```

Run Hybrid frame adapter validation:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_hybrid_frame_adapter.py
```

Run Hybrid pipeline output validation:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_hybrid_pipeline_output.py
```

Run P-code replacement step-1 validation (`generate_channel`):

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_hybrid_generate_channel.py
```

Run ingest pipeline (example):

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/run_hybrid_ingest_to_adc.py \
  --frames-root /path/to/render \
  --radar-json /path/to/radar_parameters_hybrid.json \
  --frame-start 1 \
  --frame-end 64 \
  --camera-fov-deg 90 \
  --mode reflection \
  --file-ext .exr \
  --output-dir /path/to/out
```

Fetch reference repositories:

```bash
bash /Users/seongcheoljeong/Documents/Codex_test/scripts/fetch_references.sh
```

## Working Docs

- `/Users/seongcheoljeong/Documents/Codex_test/docs/01_execution_plan.md`
- `/Users/seongcheoljeong/Documents/Codex_test/docs/02_output_contracts.md`
- `/Users/seongcheoljeong/Documents/Codex_test/docs/03_architecture.md`
- `/Users/seongcheoljeong/Documents/Codex_test/docs/04_validation_checkpoints.md`
- `/Users/seongcheoljeong/Documents/Codex_test/docs/05_workflow_rules.md`
- `/Users/seongcheoljeong/Documents/Codex_test/docs/06_ffd_integration_plan.md`
- `/Users/seongcheoljeong/Documents/Codex_test/docs/07_reference_repo_strategy.md`
- `/Users/seongcheoljeong/Documents/Codex_test/docs/08_git_workflow.md`
- `/Users/seongcheoljeong/Documents/Codex_test/docs/09_hybrid_frame_adapter.md`
- `/Users/seongcheoljeong/Documents/Codex_test/docs/10_hybrid_ingest_pipeline.md`
- `/Users/seongcheoljeong/Documents/Codex_test/docs/11_pcode_reimplementation_plan.md`
