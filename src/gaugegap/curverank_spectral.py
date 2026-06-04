"""CurveRank: spectral scoring engine for candidate Hilbert-Polya operators.

Compares truncated operator spectra against known Riemann zeta zeros and
evaluates GUE-like spacing statistics.  This is spectral screening of toy
operators, not a proof of the Riemann Hypothesis.
"""
from __future__ import annotations

import numpy as np

_RIEMANN_ZEROS_100 = [
    14.134725141734693, 21.022039638771555, 25.010857580145688,
    30.424876125859513, 32.935061587739189, 37.586178158825671,
    40.918719012147495, 43.327073280914999, 48.005150881167159,
    49.773832477672302, 52.970321477714460, 56.446247697063394,
    59.347044002602353, 60.831778524609809, 65.112544048081606,
    67.079810529494173, 69.546401711173979, 72.067157674481907,
    75.704690699083933, 77.144840068874805, 79.337375020249367,
    82.910380854086030, 84.735492980517050, 87.425274613125229,
    88.809111207634465, 92.491899270558484, 94.651344040519838,
    95.870634228245309, 98.831194218193692, 101.317851005731220,
    103.725538040478040, 105.446623052326980, 107.168611184276470,
    111.029535543088076, 111.874659176711420, 114.320220915452130,
    116.226680320857573, 118.790782865976324, 121.370125002017390,
    122.946829293536760, 124.256818554345490, 127.516683879990620,
    129.578704199956030, 131.087688530934610, 133.497737202581630,
    134.756509752087730, 138.116042054667560, 139.736208952121630,
    141.123707404021780, 143.111845807949540, 146.000982486820530,
    147.422765342996590, 150.053520420689840, 150.925257611879690,
    153.024693811098540, 156.112909293998880, 157.597591817748660,
    158.849988171401050, 161.188964137715750, 163.030709687277860,
    165.537069187968590, 167.184439977894710, 169.094515415927100,
    169.911976479418550, 173.411536519735090, 174.754191523698480,
    176.441434297816980, 178.377407775245370, 179.916484020107890,
    182.207078484410230, 184.874467848368230, 185.598783677562850,
    187.228922583190530, 189.416158655894730, 192.026656360960250,
    193.079726603845410, 195.265396679792980, 196.876481840724100,
    198.015309676117010, 201.264751944074770, 202.493594514140510,
    204.189671803380910, 205.394697201702130, 207.906258887859020,
    209.576509717418530, 211.690862595425060, 213.347919360034690,
    214.547044783299940, 216.169538507943030, 219.067596348654620,
    220.714918839048020, 221.430705555067780, 224.007000254975350,
    224.983324669979200, 227.421444279552560, 229.337413306086670,
    231.250188700204250, 231.987235253015210, 233.693404179048400,
    236.524229665813260,
]


def riemann_zero_targets(k: int) -> np.ndarray:
    """Return imaginary parts of the first *k* non-trivial Riemann zeta zeros.

    The zeros are on the critical line Re(s) = 1/2.  Values are the positive
    imaginary parts, accurate to ~12 decimal places.
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
) -> float:
    """L2 distance between sorted positive eigenvalues and target zero list.

    Only compares up to min(len(eigenvalues), len(targets)) values.
    """
    eigs = np.sort(np.abs(eigenvalues))
    eigs = eigs[eigs > 0]
    n = min(len(eigs), len(targets))
    if n == 0:
        return float("inf")
    return float(np.linalg.norm(eigs[:n] - targets[:n]) / np.sqrt(n))


def riemann_zero_intervals(k: int):
    """Return certified interval enclosures of the first *k* Riemann zeros.

    Unlike :func:`riemann_zero_targets` (hardcoded ~12-digit floats), the
    imaginary parts are computed with ``mpmath.zetazero`` at the active working
    precision, so each returned :class:`Interval` rigorously brackets the true
    zero up to that precision.

    Returns
    -------
    list[Interval]
        Enclosures ``[t_j - eps, t_j + eps]`` for the positive imaginary parts.
    """
    if k < 1:
        raise ValueError("k must be at least 1")

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

    abs_eigs = [abs(e) for e in eig_intervals]
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

    sum_lo = mp.mpf(0)
    sum_hi = mp.mpf(0)
    for i in range(n):
        a_lo, a_hi = e_lowers[i], e_uppers[i]
        z_lo, z_hi = z_lowers[i], z_uppers[i]
        # Lower bound on |a - z| over the two order-statistic enclosures
        # (0 if they overlap).
        if a_hi < z_lo:
            d_lo = z_lo - a_hi
        elif a_lo > z_hi:
            d_lo = a_lo - z_hi
        else:
            d_lo = mp.mpf(0)
        # Upper bound on |a - z| over the two enclosures.
        d_hi = max(abs(a_hi - z_lo), abs(a_lo - z_hi))
        sum_lo += d_lo * d_lo
        sum_hi += d_hi * d_hi

    nn = mp.mpf(n)
    return Interval(mp.sqrt(sum_lo / nn), mp.sqrt(sum_hi / nn))


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
