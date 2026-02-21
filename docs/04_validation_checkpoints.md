# Validation Checkpoints

## Common Setup

- Carrier: `fc_hz = 77e9`
- Chirp slope: `slope_hz_per_s = 20e12`
- Sampling: `fs_hz = 20e6`, `samples = 8192`
- TDM schedule: alternating TX (`0, 1, 0, 1, ...`)

Tolerance:

- Frequency peak error: <= `1.5 * (fs_hz / samples)`

## CP-1: Static Point Target

Input:
- one path
- `delay_s = 2R/c`
- `doppler_hz = 0`

Pass criteria:
- dominant beat frequency ~= `slope * delay`

## CP-2: Constant Velocity Target

Input:
- one path
- `doppler_hz = 2v/lambda`

Pass criteria:
- dominant frequency ~= `slope * delay + doppler`

## CP-3: Two-Path Multipath

Input:
- two paths with separate delays

Pass criteria:
- top-2 spectral peaks align with both expected frequencies

## CP-4: TDM TX Gating

Input:
- alternating `tx_schedule`

Pass criteria:
- for each chirp, only scheduled TX slice contains non-trivial energy

