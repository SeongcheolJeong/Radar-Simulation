# Architecture

## Module Split

1. `PathGenerator`
- Input: scene state, ego pose, target state, time
- Output: `paths_by_chirp`

2. `AntennaModel`
- Input: `(tx_id, rx_id, direction, polarization)`
- Output: complex gains (`g_tx`, `g_rx`)

3. `FmcwMultiplexingSynthesizer`
- Input: radar params + positions + paths + antenna gains + multiplexing plan (`tx_schedule`, `pulse_amp`, `pulse_phs`)
- Output: `adc[sample, chirp, tx, rx]`

4. `OutputWriter`
- Input: path list + ADC + metadata
- Output: persisted artifacts (`path_list.json`, `adc_cube.npz`, `radar_map.npz`, optional `lgit_customized_output.npz`)

## Dependency Direction

`PathGenerator -> Synthesizer <- AntennaModel`

`OutputWriter` must depend only on contracts, not on generator internals.

## Engineering Constraints

- Keep path and ADC interfaces stable while swapping RT backends.
- Keep multiplexing timing explicit via `tx_schedule` and optional `pulse_amp` / `pulse_phs`.
- Handle phase in complex domain from first implementation.
