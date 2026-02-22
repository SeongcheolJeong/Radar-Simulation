# AVX-Like Frontend Dashboard Usage

## Purpose

Use a frontend similar to the provided `radar_map_front.jsx.rtf` layout, wired to current simulation outputs.

Frontend entry:

- `/Users/seongcheoljeong/Documents/Codex_test/frontend/avx_like_dashboard.html`

Default data source:

- `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/avx_like_showcase_macos_2026_02_22.json`

## How To Run

1. Start a local static server at repo root:

```bash
cd /Users/seongcheoljeong/Documents/Codex_test
python3 -m http.server 8080
```

2. Open:

- `http://localhost:8080/frontend/avx_like_dashboard.html`

## What The Dashboard Reads

From the summary JSON:

- radar metadata (`fc_hz`, `slope_hz_per_s`, `fs_hz`, chirps/samples, tx/rx)
- first-chirp path list summary
- RD/RA top-peak metadata
- output contract paths (`path_list.json`, `adc_cube.npz`, `radar_map.npz`)

From the demo visual folder (auto-derived):

- `rd_map.png`
- `ra_map.png`
- `adc_tx0_rx0.png`
- `path_scatter_chirp0.png`

## UI Notes

- `Refresh Outputs`: reloads summary JSON and rebinds all views.
- `Upload JSON`: load another summary file without changing code.
- `Upload .ffd`: UI context only (no browser-side FFD parsing).
- Scene viewer uses first-chirp path direction/range.
- Detection table shows first-chirp paths with computed range/velocity/amplitude dB.

## Known Limits

- Browser cannot execute Python simulation directly; backend run is still CLI-based.
- Dashboard is a visualization layer on top of generated artifacts.
- If you open via `file://` instead of `http://`, `fetch` may fail due browser restrictions.

