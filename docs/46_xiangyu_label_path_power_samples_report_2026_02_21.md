# Xiangyu Label-Based Path-Power Samples Report (2026-02-21)

## Source Data

- ZIP: `/Users/seongcheoljeong/Documents/Codex_test/data/public/xiangyu_raw_adc.zip`
- Extracted labels:
  - `/Users/seongcheoljeong/Documents/Codex_test/data/public/xiangyu_raw_adc_extracted/Automotive/2019_04_09_bms1000/text_labels`
  - `/Users/seongcheoljeong/Documents/Codex_test/data/public/xiangyu_raw_adc_extracted/Automotive/2019_04_09_cms1000/text_labels`

## Generated CSVs

- BMS1000 (128-frame run):
  - `/Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/bms1000_path_power_samples_128.csv`
  - `/Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/bms1000_path_power_samples_128.meta.json`
- CMS1000 (128-frame run):
  - `/Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/cms1000_path_power_samples_128.csv`
  - `/Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/cms1000_path_power_samples_128.meta.json`

## Snapshot

- BMS selected rows: `128`
- CMS selected rows: `127`
- Output schema includes `range_m, az_rad, el_rad, observed_amp` and label trace fields.

## Follow-up Fit Batch

Batch fit summary from those CSVs:

- `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/path_power_fit_batch_xiangyu_labels_2026_02_21.json`

Best reflection fit:

- case: `bms1000_128`
- `range_power_exponent=2.5`

Best scattering fit:

- case: `bms1000_128`
- `range_power_exponent=2.5`, `elevation_power=0.5`, `azimuth_mix=0.2`, `azimuth_power=4.0`

## Note

This is label-anchored pseudo-measurement sampling from measured ADC (not chamber `measurement.csv` format).
