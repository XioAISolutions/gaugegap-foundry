# Advanced Mathematical Infrastructure

This document describes the advanced mathematical infrastructure for theorem-relevant progress on Millennium Prize problems in the GaugeGap Foundry project.

## Overview

The infrastructure provides rigorous mathematical tools for:

1. **Finite-size scaling analysis** - Extrapolation from finite systems to continuum limits
2. **Continuum limit extrapolation** - Richardson and Symanzik improvement methods
3. **Hypothesis pruning** - Bayesian model comparison and falsification
4. **Tensor network baselines** - Classical benchmarks using DMRG, PEPS, TEBD
5. **Advanced error mitigation** - PEC, CDR, symmetry verification, virtual distillation

## Claim Boundary Compliance

**IMPORTANT**: All modules maintain strict claim boundary compliance:

- Results are **finite-system benchmarks** and **hypothesis tests**
- Extrapolation to continuum limits includes **quantified uncertainties**
- Surviving hypotheses are **candidates for further testing**, NOT proofs
- No module claims to solve, prove, or experimentally resolve any Millennium Prize problem

## Module Documentation

### 1. Finite-Size Scaling Analysis

**Location**: `src/gaugegap/analysis/finite_size_scaling.py`

**Purpose**: Extrapolate finite-system results to continuum/thermodynamic limits with rigorous uncertainty quantification.

**Mathematical Framework**:

For a finite system of size L with observable O(L):

```
Power-law:     O(L) = O_∞ + A·L^(-ω) + B·L^(-2ω) + ...
Exponential:   O(L) = O_∞ + A·exp(-L/ξ)
```

**Key Classes**:

- `FiniteSizeScaling`: Unified interface with automatic method selection
- `PowerLawExtrapolation`: For algebraic corrections (typical in critical systems)
- `ExponentialExtrapolation`: For gapped systems with finite correlation length

**Usage Example**:

```python
from gaugegap.analysis import FiniteSizeScaling

# System sizes and measured observables
sizes = np.array([4, 8, 16, 32, 64])
observables = np.array([1.5, 1.25, 1.125, 1.0625, 1.03125])
errors = np.array([0.05, 0.03, 0.02, 0.015, 0.01])

# Perform finite-size scaling
analyzer = FiniteSizeScaling()
result = analyzer.analyze(sizes, observables, errors, method="auto")

print(f"Continuum value: {result.continuum_value:.4f} ± {result.total_error():.4f}")
print(f"Extrapolation type: {result.extrapolation_type}")
print(f"Chi-squared: {result.chi_squared:.2f}")
```

**Uncertainty Quantification**:

- Statistical error from fit covariance
- Systematic error from truncation of higher-order terms
- Bootstrap confidence intervals for non-Gaussian distributions
- Jackknife variance estimation

### 2. Continuum Limit Extrapolation

**Location**: `src/gaugegap/analysis/continuum_extrapolation.py`

**Purpose**: Extrapolate lattice gauge theory results to continuum limit (lattice spacing a → 0).

**Mathematical Framework**:

```
Symanzik:    O(a) = O_cont + c₂·a² + c₄·a⁴ + ...
Richardson:  O_ext = (r^p·O(a/r) - O(a)) / (r^p - 1)
```

**Key Classes**:

- `ContinuumExtrapolation`: Unified interface for continuum extrapolation
- `richardson_extrapolation()`: Accelerated convergence using multiple spacings
- `symanzik_improvement()`: Systematic O(a²) error removal
- `detect_convergence_order()`: Automatic convergence order detection

**Usage Example**:

```python
from gaugegap.analysis import ContinuumExtrapolation

# Lattice spacings and measured values
spacings = np.array([0.1, 0.08, 0.06, 0.04, 0.02])
values = np.array([0.52, 0.51, 0.505, 0.502, 0.501])
errors = np.array([0.02, 0.015, 0.012, 0.01, 0.008])

# Extrapolate to continuum
extrapolator = ContinuumExtrapolation()
result = extrapolator.extrapolate(spacings, values, errors, method="symanzik")

print(f"Continuum limit: {result.continuum_value:.4f} ± {result.total_error():.4f}")
print(f"Convergence order: O(a^{result.convergence_order})")
print(f"Improvement type: {result.improvement_type}")
```

**For Yang-Mills Mass Gap**:

- Tree-level: O(a²) corrections
- One-loop: O(a⁴) with improved actions
- Tadpole improvement: O(αₛ·a²) resummation

### 3. Hypothesis Pruning Engine

**Location**: `src/gaugegap/analysis/hypothesis_pruning.py`

**Purpose**: Bayesian model comparison and systematic hypothesis falsification.

**Mathematical Framework**:

```
Bayes Factor:  BF₁₂ = P(D|H₁) / P(D|H₂)
Posterior:     P(Hᵢ|D) ∝ P(D|Hᵢ)·P(Hᵢ)
AIC:           2k - 2ln(L)
BIC:           k·ln(n) - 2ln(L)
```

**Key Classes**:

- `HypothesisPruner`: Lifecycle tracking and automatic pruning
- `BayesianModelComparison`: Evidence computation and model selection
- `Hypothesis`: Individual hypothesis with evidence tracking

**Usage Example**:

```python
from gaugegap.analysis import HypothesisPruner, Hypothesis

# Create pruner
pruner = HypothesisPruner(
    falsification_threshold=-10.0,  # ln(BF) < -10 → falsified
    survival_threshold=10.0,         # ln(BF) > 10 → strong evidence
)

# Register hypotheses
h1 = Hypothesis(
    id="gaugegap-power-law",
    description="Mass gap scales as L^(-2)",
    track="gaugegap",
    n_parameters=2,
)
h2 = Hypothesis(
    id="gaugegap-exponential",
    description="Mass gap has exponential corrections",
    track="gaugegap",
    n_parameters=3,
)

pruner.register_hypothesis(h1)
pruner.register_hypothesis(h2)

# Update with experimental data
pruner.update_evidence("gaugegap-power-law", log_likelihood=5.2)
pruner.update_evidence("gaugegap-exponential", log_likelihood=-12.3)

# Prune falsified hypotheses
falsified = pruner.prune_falsified()
print(f"Falsified: {falsified}")

# Get status summary
summary = pruner.get_status_summary()
print(f"Active: {summary['active']}, Falsified: {summary['falsified']}")
```

**Interpretation Guidelines**:

- BF > 10: Strong evidence for hypothesis
- BF > 100: Decisive evidence
- BF < 0.1: Strong evidence against
- Falsification is rigorous; survival is NOT proof

### 4. Tensor Network Baselines

**Location**: `src/gaugegap/classical/tensor_networks.py`

**Purpose**: Classical benchmarks using state-of-the-art tensor network methods.

**Mathematical Framework**:

```
MPS:   |ψ⟩ = Σ A¹[i₁]A²[i₂]...Aᴺ[iₙ] |i₁i₂...iₙ⟩
PEPS:  2D generalization with tensor at each site
TEBD:  Time evolution with Trotter decomposition
```

**Key Classes**:

- `DMRGSolver`: Density Matrix Renormalization Group for 1D systems
- `PEPSSolver`: Projected Entangled Pair States for 2D systems
- `TEBDSolver`: Time Evolution Block Decimation for dynamics

**Usage Example**:

```python
from gaugegap.classical import DMRGSolver
import numpy as np

# Define Hamiltonian (e.g., Heisenberg chain)
n_sites = 8
local_dim = 2
dim = local_dim**n_sites

# Build Hamiltonian matrix
H = build_heisenberg_hamiltonian(n_sites)  # Your Hamiltonian

# Solve with DMRG
solver = DMRGSolver(
    max_bond_dim=100,
    convergence_tol=1e-8,
    max_sweeps=20,
)

result = solver.solve(H, n_sites, local_dim)

print(f"Ground state energy: {result.ground_state_energy:.6f}")
print(f"Bond dimension: {result.bond_dimension}")
print(f"Truncation error: {result.truncation_error:.2e}")
print(f"Entanglement entropy: {result.entanglement_entropy}")
```

**For Gauge Theories**:

- Electric field truncation: |E| ≤ E_max
- Gauge-invariant subspace projection
- Wilson loops as observables
- Plaquette operators for field strength

### 5. Advanced Error Mitigation

**Location**: `src/gaugegap/mitigation/advanced_mitigation.py`

**Purpose**: Reduce quantum noise without full error correction.

**Methods**:

1. **Probabilistic Error Cancellation (PEC)**:
   - Represent noisy channel as quasi-probability distribution
   - Sample with negative weights to cancel errors
   - Overhead: exponential in circuit depth

2. **Clifford Data Regression (CDR)**:
   - Train on classically simulable Clifford circuits
   - Learn noise model from data
   - Overhead: polynomial

3. **Symmetry Verification**:
   - Post-select on symmetry-preserving outcomes
   - For gauge theories: Gauss law, charge conservation
   - Overhead: depends on violation rate

4. **Virtual Distillation**:
   - Combine M copies for exponential error suppression
   - Error reduced by factor ε^M
   - Overhead: M copies

**Usage Example**:

```python
from gaugegap.mitigation import AdaptiveMitigation

# Create adaptive mitigation
mitigator = AdaptiveMitigation()

# Automatically select best strategy
strategy = mitigator.select_strategy(
    circuit_depth=10,
    has_symmetries=True,
    has_training_data=False,
    n_copies=1,
    max_overhead=10.0,
)
print(f"Selected strategy: {strategy}")

# Apply mitigation
circuit_results = [0.48, 0.52, 0.49, 0.51, 0.50]
result = mitigator.mitigate(
    circuit_results,
    strategy=strategy,
    circuit_depth=10,
    gate_types=["rx", "ry", "cnot"],
)

print(f"Raw value: {result.raw_value:.4f}")
print(f"Mitigated value: {result.mitigated_value:.4f}")
print(f"Overhead: {result.mitigation_overhead:.2f}x")
print(f"Error estimate: {result.error_estimate:.4f}")
```

## Testing

Comprehensive tests are provided in:

- `tests/test_finite_size_scaling.py`
- `tests/test_continuum_extrapolation.py`
- `tests/test_analysis_modules.py`

Run tests with:

```bash
python -m pytest tests/test_finite_size_scaling.py -v
python -m pytest tests/test_continuum_extrapolation.py -v
python -m pytest tests/test_analysis_modules.py -v
```

## Integration with Existing Infrastructure

### With GaugeGap Track

```python
from gaugegap.analysis import FiniteSizeScaling, ContinuumExtrapolation
from gaugegap.solvers import exact_gap

# Compute mass gaps at different system sizes
sizes = [4, 6, 8, 10]
gaps = []
for n in sizes:
    gap = exact_gap(n, g_mag=1.0)
    gaps.append(gap)

# Finite-size scaling
fss = FiniteSizeScaling()
result = fss.analyze(np.array(sizes), np.array(gaps))

print(f"Continuum mass gap estimate: {result.continuum_value:.4f}")
```

### With FlowGap Track

```python
from gaugegap.analysis import ContinuumExtrapolation
from gaugegap.flowgap_burgers import solve_burgers

# Solve at different resolutions
resolutions = [16, 32, 64, 128]
energies = []
for nx in resolutions:
    result = solve_burgers(nx=nx, nu=0.01, n_steps=100)
    energies.append(result['energy'])

# Continuum extrapolation
spacings = 1.0 / np.array(resolutions)
extrapolator = ContinuumExtrapolation()
result = extrapolator.extrapolate(spacings, np.array(energies))

print(f"Continuum energy: {result.continuum_value:.6f}")
```

### With CurveRank Track

```python
from gaugegap.analysis import HypothesisPruner, Hypothesis
from gaugegap.curverank_spectral import screen_operator

# Create hypotheses for different operator families
pruner = HypothesisPruner()

h1 = Hypothesis(
    id="curverank-xp",
    description="x·p operator family",
    track="curverank",
)
h2 = Hypothesis(
    id="curverank-x2p2",
    description="x²+p² operator family",
    track="curverank",
)

pruner.register_hypothesis(h1)
pruner.register_hypothesis(h2)

# Test against Riemann zeros
for family in ["xp", "x2p2"]:
    result = screen_operator(family, n_basis=20, k_zeros=10)
    log_likelihood = -result['mismatch']
    pruner.update_evidence(f"curverank-{family}", log_likelihood)

# Check which hypotheses survive
summary = pruner.get_status_summary()
```

## Best Practices

1. **Always report uncertainties**: Use `total_error()` to combine statistical and systematic errors

2. **Document extrapolation assumptions**: State convergence order, truncation effects, and validity range

3. **Compare multiple methods**: Use `compare_methods()` to check consistency

4. **Track hypothesis lifecycle**: Use `HypothesisPruner` for systematic testing

5. **Validate with known cases**: Test extrapolation on systems with known continuum limits

6. **Report mitigation overhead**: Always include sampling/computational cost

7. **Maintain claim boundaries**: Results are benchmarks and hypothesis tests, not proofs

## References

### Finite-Size Scaling
- Cardy, J. (1988). *Finite-Size Scaling*. North-Holland.
- Privman, V. (1990). *Finite Size Scaling and Numerical Simulation*.

### Continuum Extrapolation
- Symanzik, K. (1983). *Continuum limit and improved action*.
- Lüscher, M. (2010). *Properties and uses of the Wilson flow*.

### Bayesian Model Comparison
- Kass & Raftery (1995). *Bayes Factors*. JASA.
- Burnham & Anderson (2002). *Model Selection and Multimodel Inference*.

### Tensor Networks
- Schollwöck, U. (2011). *The density-matrix renormalization group*.
- Verstraete, F. & Cirac, J.I. (2004). *Renormalization algorithms for PEPS*.

### Error Mitigation
- Temme et al. (2017). *Error mitigation for short-depth quantum circuits*.
- Czarnik et al. (2021). *Error mitigation with Clifford quantum-circuit data*.
- Huggins et al. (2021). *Virtual distillation for quantum error mitigation*.

## Support

For questions or issues with the mathematical infrastructure:

1. Check the module docstrings for detailed mathematical derivations
2. Review the test files for usage examples
3. Consult the references for theoretical background
4. Open an issue on GitHub with the `mathematical-infrastructure` label