# Xiangyu Label Fit Experiment Contract

## Goal

Run reproducible experiment matrix:

- input: Xiangyu `radar_raw_frame + text_labels`
- intermediate: `path_power_samples.csv` per sequence/per frame-count
- output: fit batch summaries for `reflection` and `scattering`

## CLI

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_xiangyu_label_fit_experiment.py \
  --case bms1000=/path/to/2019_04_09_bms1000/radar_raw_frame::/path/to/2019_04_09_bms1000/text_labels \
  --case cms1000=/path/to/2019_04_09_cms1000/radar_raw_frame::/path/to/2019_04_09_cms1000/text_labels \
  --frame-counts 128,512 \
  --models reflection,scattering \
  --output-root /path/to/xiangyu_label_fit_experiment \
  --output-summary-json /path/to/xiangyu_label_fit_experiment_summary.json
```

## Outputs

- `<output-root>/csv_<frame_count>/*.csv`
- `<output-root>/csv_<frame_count>/*.meta.json`
- `<output-root>/fit_<frame_count>/path_power_fit_batch_summary_<frame_count>.json`
- top-level summary JSON

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_xiangyu_label_fit_experiment.py
```
