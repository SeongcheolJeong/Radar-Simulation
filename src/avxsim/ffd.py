import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Literal, Sequence, Tuple

import numpy as np


FieldFormat = Literal["auto", "real_imag", "mag_phase_deg"]


@dataclass(frozen=True)
class FfdPattern:
    theta_deg: np.ndarray
    phi_deg: np.ndarray
    etheta: np.ndarray
    ephi: np.ndarray
    source_path: str

    @staticmethod
    def from_file(path: str, field_format: FieldFormat = "auto") -> "FfdPattern":
        rows = _parse_ffd_rows(path)
        if not rows:
            raise ValueError(f"no parseable data rows found in ffd file: {path}")

        theta = np.asarray([r[0] for r in rows], dtype=np.float64)
        phi = np.asarray([r[1] for r in rows], dtype=np.float64)
        c3 = np.asarray([r[2] for r in rows], dtype=np.float64)
        c4 = np.asarray([r[3] for r in rows], dtype=np.float64)
        c5 = np.asarray([r[4] for r in rows], dtype=np.float64)
        c6 = np.asarray([r[5] for r in rows], dtype=np.float64)

        fmt = _resolve_field_format(field_format, c3, c4, c5, c6)
        if fmt == "real_imag":
            etheta_vec = c3 + 1j * c4
            ephi_vec = c5 + 1j * c6
        elif fmt == "mag_phase_deg":
            etheta_vec = c3 * np.exp(1j * np.deg2rad(c4))
            ephi_vec = c5 * np.exp(1j * np.deg2rad(c6))
        else:
            raise ValueError(f"unsupported field format: {fmt}")

        theta_grid, phi_grid, etheta_grid, ephi_grid = _build_grids(
            theta=theta,
            phi=phi,
            etheta=etheta_vec,
            ephi=ephi_vec,
        )
        return FfdPattern(
            theta_deg=theta_grid,
            phi_deg=phi_grid,
            etheta=etheta_grid,
            ephi=ephi_grid,
            source_path=str(path),
        )

    def gain_from_azel(
        self,
        az_deg: float,
        el_deg: float,
        pol_weights: Tuple[complex, complex] = (1.0 + 0.0j, 0.0 + 0.0j),
    ) -> complex:
        j = self.jones_from_azel(az_deg=az_deg, el_deg=el_deg)
        w_t, w_p = pol_weights
        return complex(w_t) * j[0] + complex(w_p) * j[1]

    def gain_from_unit_direction(
        self,
        unit_direction: Sequence[float],
        pol_weights: Tuple[complex, complex] = (1.0 + 0.0j, 0.0 + 0.0j),
    ) -> complex:
        j = self.jones_from_unit_direction(unit_direction)
        w_t, w_p = pol_weights
        return complex(w_t) * j[0] + complex(w_p) * j[1]

    def jones_from_azel(self, az_deg: float, el_deg: float) -> np.ndarray:
        theta_deg = 90.0 - float(el_deg)
        phi_deg = float(az_deg)
        etheta = _interp2_periodic_phi(
            theta_grid=self.theta_deg,
            phi_grid=self.phi_deg,
            field=self.etheta,
            theta_query=theta_deg,
            phi_query=phi_deg,
        )
        ephi = _interp2_periodic_phi(
            theta_grid=self.theta_deg,
            phi_grid=self.phi_deg,
            field=self.ephi,
            theta_query=theta_deg,
            phi_query=phi_deg,
        )
        return np.asarray([etheta, ephi], dtype=np.complex128)

    def jones_from_unit_direction(self, unit_direction: Sequence[float]) -> np.ndarray:
        u = np.asarray(unit_direction, dtype=np.float64).reshape(-1)
        if u.size != 3:
            raise ValueError("unit_direction must have length 3")
        norm = np.linalg.norm(u)
        if norm <= 0:
            raise ValueError("unit_direction norm must be positive")
        u = u / norm

        az_deg = np.rad2deg(np.arctan2(u[1], u[0]))
        el_deg = np.rad2deg(np.arcsin(np.clip(u[2], -1.0, 1.0)))
        return self.jones_from_azel(az_deg=az_deg, el_deg=el_deg)


def _parse_ffd_rows(path: str) -> List[Tuple[float, float, float, float, float, float]]:
    p = Path(path)
    text = p.read_text(encoding="utf-8", errors="ignore")
    rows: List[Tuple[float, float, float, float, float, float]] = []

    for line in text.splitlines():
        nums = _extract_floats(line)
        if len(nums) >= 6:
            theta, phi = nums[0], nums[1]
            if -1e-6 <= theta <= 180.0 + 1e-6 and -720.0 <= phi <= 720.0:
                rows.append((theta, phi, nums[2], nums[3], nums[4], nums[5]))
    if rows:
        return rows
    return _parse_hfss_grid_format(text)


def _extract_floats(line: str) -> List[float]:
    matches = re.findall(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?", line)
    out: List[float] = []
    for m in matches:
        try:
            out.append(float(m))
        except ValueError:
            continue
    return out


def _resolve_field_format(
    field_format: FieldFormat,
    c3: np.ndarray,
    c4: np.ndarray,
    c5: np.ndarray,
    c6: np.ndarray,
) -> Literal["real_imag", "mag_phase_deg"]:
    if field_format in {"real_imag", "mag_phase_deg"}:
        return field_format

    # Heuristic for auto mode:
    # If many amplitude columns are non-negative and phase-like columns are in [-360, 360],
    # treat as magnitude/phase. Otherwise use real/imag.
    nonneg_ratio = float(np.mean((c3 >= 0.0) & (c5 >= 0.0)))
    phase_range_ratio = float(np.mean((np.abs(c4) <= 360.0) & (np.abs(c6) <= 360.0)))
    if nonneg_ratio > 0.9 and phase_range_ratio > 0.95:
        return "mag_phase_deg"
    return "real_imag"


def _parse_hfss_grid_format(text: str) -> List[Tuple[float, float, float, float, float, float]]:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    triples = []
    for i, ln in enumerate(lines):
        nums = _extract_floats(ln)
        if len(nums) == 3:
            triples.append((i, nums))

    if len(triples) < 2:
        return []

    # Use the first two triple lines as angular ranges.
    i0, r0 = triples[0]
    i1, r1 = triples[1]
    if i1 != i0 + 1:
        return []

    theta_range, phi_range = _resolve_theta_phi_ranges(r0, r1)
    n_theta = int(round(theta_range[2]))
    n_phi = int(round(phi_range[2]))
    if n_theta <= 0 or n_phi <= 0:
        return []
    n_total = n_theta * n_phi

    data_lines = []
    start = i1 + 1
    for ln in lines[start:]:
        # Skip non-data markers like "Frequencies 5", "Frequency ...".
        if ln.lower().startswith("frequenc"):
            continue
        nums = _extract_floats(ln)
        if len(nums) == 4:
            data_lines.append(nums)
        elif len(data_lines) > 0:
            # Stop at first non-data line after data started.
            break

    if len(data_lines) < n_total:
        return []

    data = np.asarray(data_lines[:n_total], dtype=np.float64)
    theta_vals = np.linspace(theta_range[0], theta_range[1], n_theta, dtype=np.float64)
    phi_vals = np.linspace(phi_range[0], phi_range[1], n_phi, dtype=np.float64)

    # HFSS export commonly iterates theta fastest inside each phi sweep.
    rows: List[Tuple[float, float, float, float, float, float]] = []
    idx = 0
    for phi in phi_vals:
        for theta in theta_vals:
            c = data[idx]
            rows.append((float(theta), float(phi), float(c[0]), float(c[1]), float(c[2]), float(c[3])))
            idx += 1
    return rows


def _resolve_theta_phi_ranges(
    r0: Sequence[float],
    r1: Sequence[float],
) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
    a0, b0, n0 = float(r0[0]), float(r0[1]), float(r0[2])
    a1, b1, n1 = float(r1[0]), float(r1[1]), float(r1[2])

    def is_theta(a: float, b: float) -> bool:
        lo, hi = min(a, b), max(a, b)
        return lo >= -1e-6 and hi <= 180.0 + 1e-6

    t0 = is_theta(a0, b0)
    t1 = is_theta(a1, b1)
    if t0 and not t1:
        return (a0, b0, n0), (a1, b1, n1)
    if t1 and not t0:
        return (a1, b1, n1), (a0, b0, n0)

    # fallback: prefer smaller angular span as theta candidate
    span0 = abs(b0 - a0)
    span1 = abs(b1 - a1)
    if span0 <= span1:
        return (a0, b0, n0), (a1, b1, n1)
    return (a1, b1, n1), (a0, b0, n0)


def _build_grids(
    theta: np.ndarray,
    phi: np.ndarray,
    etheta: np.ndarray,
    ephi: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    theta_grid = np.unique(np.round(theta, decimals=9))
    phi_grid = np.unique(np.round(phi, decimals=9))

    etheta_grid = np.full((theta_grid.size, phi_grid.size), np.nan + 1j * np.nan, dtype=np.complex128)
    ephi_grid = np.full((theta_grid.size, phi_grid.size), np.nan + 1j * np.nan, dtype=np.complex128)

    theta_idx = {float(v): i for i, v in enumerate(theta_grid)}
    phi_idx = {float(v): i for i, v in enumerate(phi_grid)}

    for th, ph, et, ep in zip(theta, phi, etheta, ephi):
        i = theta_idx[float(np.round(th, 9))]
        j = phi_idx[float(np.round(ph, 9))]
        etheta_grid[i, j] = et
        ephi_grid[i, j] = ep

    if np.isnan(np.real(etheta_grid)).any() or np.isnan(np.real(ephi_grid)).any():
        raise ValueError("incomplete theta/phi grid in ffd file")

    return theta_grid, phi_grid, etheta_grid, ephi_grid


def _interp2_periodic_phi(
    theta_grid: np.ndarray,
    phi_grid: np.ndarray,
    field: np.ndarray,
    theta_query: float,
    phi_query: float,
) -> complex:
    if theta_grid.ndim != 1 or phi_grid.ndim != 1:
        raise ValueError("theta_grid and phi_grid must be 1D")
    if field.shape != (theta_grid.size, phi_grid.size):
        raise ValueError("field shape mismatch with theta/phi grids")

    tq = float(np.clip(theta_query, float(theta_grid[0]), float(theta_grid[-1])))

    # Periodic phi interpolation via wrapped extension.
    p0 = float(phi_grid[0])
    pq = ((float(phi_query) - p0) % 360.0) + p0
    phi_ext = np.concatenate([phi_grid, [phi_grid[0] + 360.0]])
    field_ext = np.concatenate([field, field[:, :1]], axis=1)

    i0, i1, wt = _find_interval(theta_grid, tq)
    j0, j1, wp = _find_interval(phi_ext, pq)

    f00 = field_ext[i0, j0]
    f01 = field_ext[i0, j1]
    f10 = field_ext[i1, j0]
    f11 = field_ext[i1, j1]
    top = (1.0 - wp) * f00 + wp * f01
    bot = (1.0 - wp) * f10 + wp * f11
    return complex((1.0 - wt) * top + wt * bot)


def _find_interval(grid: np.ndarray, x: float) -> Tuple[int, int, float]:
    if grid.size == 1:
        return 0, 0, 0.0
    if x <= grid[0]:
        return 0, 1, 0.0
    if x >= grid[-1]:
        return grid.size - 2, grid.size - 1, 1.0
    hi = int(np.searchsorted(grid, x, side="right"))
    lo = hi - 1
    x0 = float(grid[lo])
    x1 = float(grid[hi])
    if x1 == x0:
        return lo, hi, 0.0
    w = (x - x0) / (x1 - x0)
    return lo, hi, float(w)
