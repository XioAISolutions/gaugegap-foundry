"""CurveRank: spectral scoring engine for candidate Hilbert-Polya operators.

Compares truncated operator spectra against known Riemann zeta zeros and
evaluates GUE-like spacing statistics.  This is spectral screening of toy
operators, not a proof of the Riemann Hypothesis.
"""
from __future__ import annotations

import numpy as np

_RIEMANN_ZEROS_100 = [
    14.134725141734695, 21.022039638771556, 25.01085758014569,
    30.424876125859512, 32.93506158773919, 37.586178158825675,
    40.9187190121475, 43.327073280915, 48.00515088116716,
    49.7738324776723, 52.970321477714464, 56.44624769706339,
    59.34704400260235, 60.83177852460981, 65.1125440480816,
    67.07981052949417, 69.54640171117398, 72.0671576744819,
    75.70469069908393, 77.1448400688748, 79.33737502024937,
    82.91038085408603, 84.73549298051705, 87.42527461312523,
    88.80911120763446, 92.49189927055849, 94.65134404051989,
    95.87063422824531, 98.83119421819369, 101.31785100573138,
    103.72553804047834, 105.44662305232609, 107.1686111842764,
    111.02953554316967, 111.87465917699264, 114.32022091545271,
    116.22668032085755, 118.79078286597621, 121.37012500242065,
    122.94682929355258, 124.25681855434577, 127.5166838795965,
    129.57870419995606, 131.08768853093267, 133.4977372029976,
    134.75650975337388, 138.11604205453344, 139.7362089521214,
    141.12370740402113, 143.11184580762063, 146.0009824867655,
    147.42276534255961, 150.05352042078488, 150.92525761224147,
    153.0246938111989, 156.11290929423788, 157.59759181759406,
    158.8499881714205, 161.18896413759603, 163.030709687182,
    165.5370691879004, 167.1844399781745, 169.09451541556882,
    169.9119764794117, 173.41153651959155, 174.75419152336573,
    176.44143429771043, 178.37740777609997, 179.916484020257,
    182.20707848436646, 184.8744678483875, 185.59878367770747,
    187.22892258350186, 189.41615865601693, 192.0266563607138,
    193.0797266038457, 195.26539667952923, 196.87648184095832,
    198.01530967625192, 201.2647519437038, 202.49359451414054,
    204.18967180310455, 205.3946972021633, 207.90625888780622,
    209.57650971685626, 211.6908625953653, 213.34791935971268,
    214.54704478349143, 216.1695385082637, 219.0675963490214,
    220.714918839314, 221.43070555469333, 224.00700025460432,
    224.9833246695823, 227.4214442796793, 229.33741330552536,
    231.25018870049917, 231.98723525318024, 233.6934041789083,
    236.5242296658162,
]


def riemann_zero_targets(k: int) -> np.ndarray:
    """Return imaginary parts of the first *k* non-trivial Riemann zeta zeros.

    The zeros are on the critical line Re(s) = 1/2.  Values are the positive
    imaginary parts, rounded to nearest float64 from Arb's rigorous enclosures
    (``acb.zeta_zeros`` at 128-bit precision), i.e. accurate to float64
    resolution (~1e-14 absolute at t ~ 240).
    """
    if k < 1:
        raise ValueError("k must be at least 1")
    if k > len(_RIEMANN_ZEROS_100):
        raise ValueError(
            f"only {len(_RIEMANN_ZEROS_100)} zeros available, requested {k}"
        )
    return np.array(_RIEMANN_ZEROS_100[:k], dtype=np.float64)


def spectral_mismatch(
    eigenvalues: np.ndarray,
    targets: np.ndarray,
    zero_tol: float = 1e-9,
) -> float:
    """L2 distance between sorted positive eigenvalues and target zero list.

    Structural zero modes (``|eig| <= zero_tol``) are dropped before sorting, so
    a symmetric spectrum's spurious zero eigenvalue is not paired with the first
    Riemann zero. Only compares up to ``min(#nonzero eigenvalues, #targets)``
    values.
    """
    eigs = np.sort(np.abs(eigenvalues))
    eigs = eigs[eigs > zero_tol]
    n = min(len(eigs), len(targets))
    if n == 0:
        return float("inf")
    return float(np.linalg.norm(eigs[:n] - targets[:n]) / np.sqrt(n))


def riemann_zero_intervals(k: int, method: str = "auto"):
    """Return certified interval enclosures of the first *k* Riemann zeros.

    Unlike :func:`riemann_zero_targets` (hardcoded ~12-digit floats), each
    returned :class:`Interval` rigorously brackets the true zero.

    Trust model by ``method``:

    - ``"arb"``      -- rigorous, index-correct ball enclosures from Arb
      (``acb.zeta_zeros``, Turing's method internally).  Independent of
      mpmath; requires the optional ``python-flint >= 0.7``.
    - ``"zetazero"`` -- ``mpmath.zetazero`` at the active working precision
      with a conservative radius; *trusts* mpmath's root finding.
    - ``"auto"``     -- ``"arb"`` when available, else ``"zetazero"``.

    Returns
    -------
    list[Interval]
        Enclosures of the positive imaginary parts, ascending.
    """
    if k < 1:
        raise ValueError("k must be at least 1")
    if method not in ("auto", "arb", "zetazero"):
        raise ValueError(
            f"unknown method {method!r}; choose 'auto', 'arb', or 'zetazero'"
        )

    if method in ("auto", "arb"):
        from gaugegap.rigorous.certified_zeros import arb_available, arb_zero_intervals

        if arb_available():
            return arb_zero_intervals(k)
        if method == "arb":
            raise ImportError(
                "method='arb' requires python-flint >= 0.7 "
                "(pip install 'python-flint>=0.7')"
            )

    import mpmath as mp
    from gaugegap.rigorous.interval_arithmetic import Interval

    # zetazero is accurate to the working precision; use a conservative radius
    # several digits inside that precision as the certified half-width.
    eps = mp.mpf(10) ** (-(mp.mp.dps - 5))
    intervals = []
    for j in range(1, k + 1):
        t = mp.zetazero(j).imag
        intervals.append(Interval(t - eps, t + eps))
    return intervals


def certified_spectral_mismatch(eig_intervals, zero_intervals):
    """Certified enclosure of the L2 spectral mismatch ``M_n``.

    Interval-arithmetic analogue of :func:`spectral_mismatch`: given certified
    eigenvalue enclosures and certified Riemann-zero enclosures, returns an
    :class:`Interval` ``[M_lower, M_upper]`` guaranteed to contain

        M_n = || sort(|eig|)[:n] - zeros[:n] ||_2 / sqrt(n).

    The lower endpoint is a *rigorous lower bound* on the mismatch (the
    quantity that certifies how far the operator spectrum is from the zeros);
    it is conservative whenever an eigenvalue enclosure overlaps a zero
    enclosure (that pair contributes 0).

    Rigour under overlapping enclosures: the metric pairs the i-th smallest
    ``|eig|`` with the i-th zero, but if two ``|eig|`` enclosures overlap the
    true sort order is ambiguous, so pairing whole enclosures sorted by
    midpoint would not be a valid certificate. We instead use *order-statistic
    enclosures*: for interval data, the k-th smallest true value provably lies
    in ``[k-th smallest lower endpoint, k-th smallest upper endpoint]``. Pairing
    those per-rank enclosures yields a rigorous lower bound for every ordering
    consistent with the intervals, and reduces to the naive pairing when the
    enclosures are disjoint.
    """
    import mpmath as mp
    from gaugegap.rigorous.interval_arithmetic import Interval

    # Drop structural zero modes (enclosures that contain 0, i.e. not certifiably
    # nonzero) so a symmetric spectrum's zero eigenvalue is not paired with the
    # first Riemann zero. This mirrors the zero-mode filtering in
    # :func:`spectral_mismatch`.
    abs_eigs = [abs(e) for e in eig_intervals if not (e.lower <= 0 <= e.upper)]
    n = min(len(abs_eigs), len(zero_intervals))
    if n == 0:
        return Interval(mp.inf, mp.inf)

    # Order-statistic enclosures: sort lower and upper endpoints independently.
    # The k-th smallest true value lies in [e_lowers[k], e_uppers[k]] (and
    # likewise for the zeros), regardless of how the enclosures overlap.
    e_lowers = sorted(e.lower for e in abs_eigs)
    e_uppers = sorted(e.upper for e in abs_eigs)
    z_lowers = sorted(z.lower for z in zero_intervals)
    z_uppers = sorted(z.upper for z in zero_intervals)

    # Accumulate in the directed-rounding iv context so M_lower is rounded
    # strictly down and M_upper strictly up: the returned interval is a
    # guaranteed enclosure of M_n, not a round-to-nearest estimate.
    sum_lo = mp.iv.mpf(0)
    sum_hi = mp.iv.mpf(0)
    for i in range(n):
        a_lo, a_hi = e_lowers[i], e_uppers[i]
        z_lo, z_hi = z_lowers[i], z_uppers[i]
        # Lower bound on |a - z| over the two order-statistic enclosures
        # (0 if they overlap); rounded down so it stays a lower bound.
        if a_hi < z_lo:
            d_lo = (mp.iv.mpf([z_lo, z_lo]) - mp.iv.mpf([a_hi, a_hi])).a
        elif a_lo > z_hi:
            d_lo = (mp.iv.mpf([a_lo, a_lo]) - mp.iv.mpf([z_hi, z_hi])).a
        else:
            d_lo = mp.mpf(0)
        # Upper bound on |a - z| over the two enclosures, rounded up.
        diff1 = mp.iv.mpf([a_hi, a_hi]) - mp.iv.mpf([z_lo, z_lo])
        diff2 = mp.iv.mpf([a_lo, a_lo]) - mp.iv.mpf([z_hi, z_hi])
        d_hi = max(abs(diff1.a), abs(diff1.b), abs(diff2.a), abs(diff2.b))
        d_lo_iv = mp.iv.mpf([d_lo, d_lo])
        d_hi_iv = mp.iv.mpf([d_hi, d_hi])
        sum_lo = sum_lo + d_lo_iv * d_lo_iv
        sum_hi = sum_hi + d_hi_iv * d_hi_iv

    nn = mp.iv.mpf(n)
    m_lower = mp.iv.sqrt(sum_lo / nn).a
    m_upper = mp.iv.sqrt(sum_hi / nn).b
    return Interval(mp.mpf(m_lower), mp.mpf(m_upper))


def gue_spacing_statistic(eigenvalues: np.ndarray) -> dict[str, float]:
    """Nearest-neighbor spacing ratio statistic for GUE comparison.

    Returns the mean ratio <r> and Wigner-surmise KL proxy.
    For GUE, <r> ~ 0.5996.  For Poisson, <r> ~ 0.3863.
    """
    eigs = np.sort(eigenvalues.real)
    spacings = np.diff(eigs)
    spacings = spacings[spacings > 1e-14]

    if len(spacings) < 2:
        return {"mean_ratio": float("nan"), "std_ratio": float("nan")}

    ratios = np.minimum(spacings[:-1], spacings[1:]) / np.maximum(spacings[:-1], spacings[1:])

    return {
        "mean_ratio": float(np.mean(ratios)),
        "std_ratio": float(np.std(ratios)),
    }


def truncation_stability(
    operator_fn,
    n_range: list[int],
    k: int = 10,
) -> list[dict[str, object]]:
    """Measure eigenvalue drift as truncation size grows.

    Parameters
    ----------
    operator_fn : callable
        Function n_basis -> matrix.
    n_range : list of int
        Truncation sizes to sweep.
    k : int
        Number of low-lying eigenvalues to track.
    """
    results = []
    prev_eigs = None

    for n in sorted(n_range):
        H = operator_fn(n)
        eigs = np.sort(np.linalg.eigvalsh(H))
        pos_eigs = eigs[eigs > 0]
        tracked = pos_eigs[:k] if len(pos_eigs) >= k else pos_eigs

        drift = float("nan")
        if prev_eigs is not None:
            overlap = min(len(tracked), len(prev_eigs))
            if overlap > 0:
                drift = float(np.linalg.norm(tracked[:overlap] - prev_eigs[:overlap]))

        results.append({
            "n_basis": n,
            "dim": H.shape[0],
            "n_tracked": len(tracked),
            "eigenvalues": tracked.tolist(),
            "drift_from_previous": drift,
        })
        prev_eigs = tracked

    return results


def rank_candidates(
    candidates: list[dict[str, object]],
    k: int = 20,
) -> list[dict[str, object]]:
    """Score and rank candidate operators against Riemann zero targets.

    Each candidate dict must have 'operator' (matrix) and 'family', 'n_basis'.
    """
    targets = riemann_zero_targets(min(k, len(_RIEMANN_ZEROS_100)))
    scored = []

    for cand in candidates:
        H = cand["operator"]
        eigs = np.linalg.eigvalsh(H)
        mismatch = spectral_mismatch(eigs, targets)
        spacing = gue_spacing_statistic(eigs)

        gue_target = 0.5996
        gue_penalty = abs(spacing["mean_ratio"] - gue_target) if not np.isnan(spacing["mean_ratio"]) else 1.0

        composite = mismatch + 10.0 * gue_penalty

        scored.append({
            "family": cand["family"],
            "n_basis": cand["n_basis"],
            "dim": cand.get("dim", H.shape[0]),
            "spectral_mismatch": mismatch,
            "gue_mean_ratio": spacing["mean_ratio"],
            "gue_std_ratio": spacing["std_ratio"],
            "gue_penalty": gue_penalty,
            "composite_score": composite,
        })

    scored.sort(key=lambda s: s["composite_score"])
    for rank, s in enumerate(scored):
        s["rank"] = rank + 1

    return scored
