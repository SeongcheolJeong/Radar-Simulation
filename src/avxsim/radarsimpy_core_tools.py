from __future__ import annotations

from typing import Any

import numpy as np
from scipy.special import erfc, erfcinv, gammainc, gammaincinv, iv
from scipy.stats import distributions


def _marcumq(a: float | np.ndarray, x: float | np.ndarray, m: int = 1) -> float | np.ndarray:
    return 1.0 - distributions.ncx2.cdf(df=int(m) * 2, nc=np.asarray(a) ** 2, x=np.asarray(x) ** 2)


def _log_factorial(n: int | np.ndarray) -> float | np.ndarray:
    if np.isscalar(n):
        ni = int(n)
        if ni <= 1:
            return 0.0
        return float(np.sum(np.log(np.arange(1, ni + 1, dtype=np.float64))))
    arr = np.asarray(n, dtype=np.int64)
    out = np.zeros_like(arr, dtype=np.float64)
    it = np.nditer(arr, flags=["multi_index"])
    while not it.finished:
        v = int(it[0])
        if v <= 1:
            out[it.multi_index] = 0.0
        else:
            out[it.multi_index] = float(np.sum(np.log(np.arange(1, v + 1, dtype=np.float64))))
        it.iternext()
    return out


def _threshold(pfa: float, npulses: int) -> float:
    return float(gammaincinv(int(npulses), 1.0 - float(pfa)))


def _pd_swerling0(npulses: int, snr: float | np.ndarray, thred: float) -> float | np.ndarray:
    n = int(npulses)
    s = np.asarray(snr, dtype=np.float64)
    if n <= 50:
        if np.isscalar(s):
            sum_array = np.arange(2, n + 1)
            with np.errstate(over="ignore", under="ignore", invalid="ignore"):
                var_1 = np.exp(-(thred + n * s)) * np.sum(
                    (thred / (n * s)) ** ((sum_array - 1) / 2.0)
                    * iv(sum_array - 1, 2.0 * np.sqrt(n * s * thred))
                )
            if np.isnan(var_1):
                var_1 = 0.0
        else:
            s_flat = s.reshape(-1)
            sum_array = np.arange(2, n + 1)
            sum_array = np.repeat(sum_array[np.newaxis, :], s_flat.shape[0], axis=0)
            snr_mat = np.repeat(s_flat[:, np.newaxis], sum_array.shape[1], axis=1)
            with np.errstate(over="ignore", under="ignore", invalid="ignore"):
                var_1 = np.exp(-(thred + n * s_flat)) * np.sum(
                    (thred / (n * snr_mat)) ** ((sum_array - 1) / 2.0)
                    * iv(sum_array - 1, 2.0 * np.sqrt(n * snr_mat * thred)),
                    axis=1,
                )
            var_1[np.isnan(var_1)] = 0.0
            var_1 = var_1.reshape(s.shape)
        return _marcumq(np.sqrt(2.0 * n * s), np.sqrt(2.0 * thred)) + var_1

    temp_1 = 2.0 * s + 1.0
    omegabar = np.sqrt(n * temp_1)
    c3 = -(s + 1.0 / 3.0) / (np.sqrt(n) * temp_1**1.5)
    c4 = (s + 0.25) / (n * temp_1**2.0)
    c6 = c3 * c3 / 2.0
    v = (thred - n * (1.0 + s)) / omegabar
    v2 = v * v
    val1 = np.exp(-v2 / 2.0) / np.sqrt(2.0 * np.pi)
    val2 = c3 * (v2 - 1.0) + c4 * v * (3.0 - v2) - c6 * v * (v**4 - 10.0 * v2 + 15.0)
    q = 0.5 * erfc(v / np.sqrt(2.0))
    return q - val1 * val2


def _pd_swerling1(npulses: int, snr: float | np.ndarray, thred: float) -> float | np.ndarray:
    n = int(npulses)
    s = np.asarray(snr, dtype=np.float64)
    if n == 1:
        return np.exp(-thred / (1.0 + s))
    temp = 1.0 + 1.0 / (n * s)
    igf1 = gammainc(n - 1, thred)
    igf2 = gammainc(n - 1, thred / temp)
    return 1.0 - igf1 + (temp ** (n - 1)) * igf2 * np.exp(-thred / (1.0 + n * s))


def _pd_swerling2(npulses: int, snr: float | np.ndarray, thred: float) -> float | np.ndarray:
    return 1.0 - gammainc(int(npulses), (thred / (1.0 + np.asarray(snr, dtype=np.float64))))


def _pd_swerling3(npulses: int, snr: float | np.ndarray, thred: float) -> float | np.ndarray:
    n = int(npulses)
    s = np.asarray(snr, dtype=np.float64)
    temp_1 = thred / (1.0 + 0.5 * n * s)
    ko = (
        np.exp(-temp_1)
        * (1.0 + 2.0 / (n * s)) ** (n - 2)
        * (1.0 + temp_1 - 2.0 * (n - 2) / (n * s))
    )
    if n <= 2:
        return ko
    var_1 = np.exp((n - 1) * np.log(thred) - thred - _log_factorial(n - 2.0)) / (1.0 + 0.5 * n * s)
    pd = var_1 + 1.0 - gammainc(n - 1, thred) + ko * gammainc(n - 1, thred / (1.0 + 2.0 / (n * s)))
    return pd


def _pd_swerling4(npulses: int, snr: float | np.ndarray, thred: float) -> float | np.ndarray:
    n = int(npulses)
    s = np.asarray(snr, dtype=np.float64)
    beta = 1.0 + s / 2.0
    if n >= 50:
        omegabar = np.sqrt(n * (2.0 * beta**2 - 1.0))
        c3 = (2.0 * beta**3 - 1.0) / (3.0 * (2.0 * beta**2 - 1.0) * omegabar)
        c4 = (2.0 * beta**4 - 1.0) / (4.0 * n * (2.0 * beta**2 - 1.0) ** 2)
        c6 = c3**2 / 2.0
        v = (thred - n * (1.0 + s)) / omegabar
        v2 = v * v
        val1 = np.exp(-v2 / 2.0) / np.sqrt(2.0 * np.pi)
        val2 = c3 * (v2 - 1.0) + c4 * v * (3.0 - v2) - c6 * v * (v**4 - 10.0 * v2 + 15.0)
        return 0.5 * erfc(v / np.sqrt(2.0)) - val1 * val2

    gamma0 = gammainc(n, thred / beta)
    a1 = (thred / beta) ** n / (np.exp(_log_factorial(n)) * np.exp(thred / beta))
    sum_var = gamma0
    for idx in range(1, n + 1):
        if idx == 1:
            ai = a1
        else:
            ai = (thred / beta) * a1 / (n + idx - 1)
        a1 = ai
        gammai = gamma0 - ai
        gamma0 = gammai
        temp = np.sum(np.log(n + 1 - np.arange(1, idx + 1)))
        with np.errstate(over="ignore", under="ignore", invalid="ignore"):
            term = (s / 2.0) ** idx * gammai * np.exp(temp - _log_factorial(idx))
        sum_var = sum_var + term
    return 1.0 - sum_var / beta**n


def core_roc_pd(
    pfa: float | np.ndarray,
    snr: float | np.ndarray,
    npulses: int = 1,
    stype: str = "Coherent",
) -> float | np.ndarray | None:
    pfa_arr = np.asarray(pfa, dtype=np.float64)
    snr_db = np.asarray(snr, dtype=np.float64)
    snr_lin = 10.0 ** (snr_db / 10.0)

    size_pfa = int(np.size(pfa_arr))
    size_snr = int(np.size(snr_lin))
    pd = np.zeros((size_pfa, size_snr), dtype=np.float64)

    pflat = pfa_arr.reshape(-1)
    sflat = snr_lin.reshape(-1)
    for i, p in enumerate(pflat):
        thred = _threshold(float(p), int(npulses))

        if stype == "Swerling 1":
            vals = _pd_swerling1(int(npulses), sflat, thred)
        elif stype == "Swerling 2":
            vals = _pd_swerling2(int(npulses), sflat, thred)
        elif stype == "Swerling 3":
            vals = _pd_swerling3(int(npulses), sflat, thred)
        elif stype == "Swerling 4":
            vals = _pd_swerling4(int(npulses), sflat, thred)
        elif stype in ("Swerling 5", "Swerling 0"):
            vals = _pd_swerling0(int(npulses), sflat, thred)
        elif stype == "Coherent":
            vals = erfc(erfcinv(2.0 * p) - np.sqrt(sflat * float(npulses))) / 2.0
        elif stype == "Real":
            vals = erfc(erfcinv(2.0 * p) - np.sqrt(sflat * float(npulses) / 2.0)) / 2.0
        else:
            return None

        pd[i, :] = np.asarray(vals, dtype=np.float64).reshape(-1)

    if size_pfa == 1 and size_snr == 1:
        return float(pd[0, 0])
    if size_pfa == 1 and size_snr > 1:
        return pd[0, :]
    if size_pfa > 1 and size_snr == 1:
        return pd[:, 0]
    return pd


def core_roc_snr(
    pfa: float | np.ndarray,
    pd: float | np.ndarray,
    npulses: int = 1,
    stype: str = "Coherent",
) -> float | np.ndarray | None:
    pfa_arr = np.asarray(pfa, dtype=np.float64).reshape(-1)
    pd_arr = np.asarray(pd, dtype=np.float64).reshape(-1)

    max_iter = 1000
    snra = 40.0
    snrb = -40.0 if stype in ("Coherent", "Real") else -20.0
    out = np.zeros((pfa_arr.size, pd_arr.size), dtype=np.float64)

    def _fun(p: float, d: float, s_db: float) -> float:
        v = core_roc_pd(p, s_db, npulses=npulses, stype=stype)
        if v is None:
            return float("nan")
        return float(v) - d

    for i, p in enumerate(pfa_arr):
        for j, d in enumerate(pd_arr):
            fa = _fun(float(p), float(d), snra)
            fb = _fun(float(p), float(d), snrb)
            if np.isnan(fa) or np.isnan(fb) or fa * fb >= 0:
                return None
            a_n = snra
            b_n = snrb
            for _ in range(max_iter):
                fa = _fun(float(p), float(d), a_n)
                fb = _fun(float(p), float(d), b_n)
                den = fb - fa
                if den == 0:
                    break
                m_n = a_n - fa * (b_n - a_n) / den
                fm = _fun(float(p), float(d), m_n)
                if fm == 0 or abs(fm) < 1e-5:
                    a_n = float(m_n)
                    b_n = float(m_n)
                    break
                if fa * fm < 0:
                    b_n = float(m_n)
                elif fb * fm < 0:
                    a_n = float(m_n)
                else:
                    out[i, j] = float("nan")
                    break
            den = _fun(float(p), float(d), b_n) - _fun(float(p), float(d), a_n)
            if den == 0:
                out[i, j] = float(a_n)
            else:
                out[i, j] = float(a_n - _fun(float(p), float(d), a_n) * (b_n - a_n) / den)

    if pfa_arr.size == 1 and pd_arr.size == 1:
        return float(out[0, 0])
    if pfa_arr.size == 1 and pd_arr.size > 1:
        return out[0, :]
    if pfa_arr.size > 1 and pd_arr.size == 1:
        return out[:, 0]
    return out


__all__ = [
    "core_roc_pd",
    "core_roc_snr",
]
