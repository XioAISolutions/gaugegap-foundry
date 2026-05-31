# Practical Quantum MVP Implementation Plan

**Date:** 2026-05-28  
**Status:** Active Development Plan  
**Scope:** Hardware-ready quantum experiments for FlowGap, GaugeGap, and CurveRank

## Executive Summary

This document translates the comprehensive quantum MVP analysis into actionable implementation steps for the GaugeGap Foundry. The plan prioritizes **GaugeGap** as the strongest quantum-native target, establishes **FlowGap** as a hybrid benchmark, and positions **CurveRank** as an AI-guided spectral search with optional quantum validation.

### Priority Order

1. **GaugeGap** → First hardware paper candidate (4-8 weeks)
2. **FlowGap** → First hybrid benchmark candidate (2-6 weeks)
3. **CurveRank** → First AI+quantum spectral candidate (2-6 weeks)

### Platform Recommendations

| Track | Primary Platform | Secondary Platform | Classical Anchor |
|-------|-----------------|-------------------|------------------|
| **GaugeGap** | Quantinuum H2/Helios | QuEra Aquila (AWS Braket) | QuTiP ED + TeNPy |
| **FlowGap** | IBM Heron + Qiskit Runtime | Quantinuum H2 emulator | SciPy sparse solvers |
| **CurveRank** | QuTiP classical engine | Quantinuum/IonQ trapped-ion | High-precision zero tables |

## Current Repository State

### What We Have

- ✅ Classical exact diagonalization baselines (Z2, U(1), Burgers, Berry-Keating)
- ✅ Qiskit Pauli operator export and validation
- ✅ Local statevector and Aer simulation
- ✅ Hypothesis registry with kill criteria
- ✅ Run ledger and artifact export (CSV/JSONL/SVG)
- ✅ Dynamics analysis with pass/warning/fail verdicts
- ✅ Quantum boundary tracking (`quantum_status.py`)

### What We Need

- ⚠️ Provider adapter architecture (Quantinuum, IBM Runtime, AWS Braket)
- ⚠️ Hardware-ready boundary checks and credential management
- ⚠️ Emulator-to-hardware workflow scaffolding
- ⚠️ Backend calibration metadata capture
- ⚠️ Noise model integration and mitigation controls
- ⚠️ Cross-platform result comparison framework

### Current Quantum Boundary

```text
Level 2: quantum_circuit_simulation (Qiskit Aer, statevector)
Next:   Level 3: hardware_ready_boundary (provider job submission)
```

## GaugeGap: Yang-Mills Mass Gap Track

### Scientific Target

**Finite-lattice mass-gap extraction** for truncated Z2/U(1)/SU(2) gauge models with:
- Ground and first excited state energies (E₀, E₁)
- Mass gap Δ = E₁ - E₀
- Wilson-loop surrogates and electric-flux correlators
- String-breaking dynamics on analogue platforms
- Finite-size scaling analysis

**Not claiming:** Continuum Yang-Mills mass-gap proof

### Platform Strategy

#### Primary: Quantinuum H2/Helios

**Why:** Best overall fit for gauge theory
- All-to-all connectivity (56 qubits H2, 98 qubits Helios)
- Strong 2-qubit fidelities (~1×10⁻³ H2, ~8×10⁻⁴ Helios)
- Official SU(2) lattice gauge theory tutorial exists
- Realistic emulators with noise models
- State-vector emulation to 32 qubits

**MVP Protocol:**
1. Start with existing Z2 plaquette model (gaugegap-0002)
2. Export to Quantinuum-compatible format
3. Run on H2 emulator (noiseless → noisy)
4. Extract gap via VQE/VQD or subspace expansion
5. Submit to H2 hardware with calibration metadata
6. Compare with classical ED baseline

#### Secondary: QuEra Aquila (AWS Braket)

**Why:** Best analogue path for confinement dynamics
- 256-qubit programmable neutral-atom array
- Native AHS (analog Hamiltonian simulation)
- String-breaking experiments already demonstrated
- Local AHS simulator available

**MVP Protocol:**
1. Map Z2 gauge Hamiltonian to Rydberg geometry
2. Design pulse schedule for domain-wall/string observable
3. Validate on Braket AHS local simulator
4. Submit to Aquila hardware
5. Extract string-breaking signatures and correlators

### Implementation Steps

#### Phase 1: Provider Adapter (Week 1-2)

```python
# src/gaugegap/providers/quantinuum_adapter.py
class QuantinuumAdapter:
    """Adapter for Quantinuum H2/Helios emulators and hardware."""
    
    def __init__(self, backend_name="H2-1E", credentials=None):
        self.backend_name = backend_name
        self.credentials = credentials or self._load_credentials()
    
    def submit_circuit(self, circuit, shots=1024, mitigation=None):
        """Submit circuit to emulator or hardware."""
        job = self._submit_job(circuit, shots)
        metadata = self._capture_metadata(job)
        return job, metadata
    
    def get_calibration_data(self):
        """Retrieve current backend calibration."""
        return self._query_backend_properties()

# src/gaugegap/providers/braket_adapter.py
class BraketAHSAdapter:
    """Adapter for AWS Braket Aquila AHS."""
    
    def submit_ahs_program(self, geometry, pulse_schedule, shots=100):
        """Submit AHS program to Aquila."""
        program = self._build_ahs_program(geometry, pulse_schedule)
        job = self._submit_to_aquila(program, shots)
        return job
```

#### Phase 2: Emulator Workflow (Week 2-3)

```python
# scripts/run_gaugegap_quantinuum.py
def run_quantinuum_gap_extraction(
    n_plaquettes=2,
    coupling=1.0,
    field=0.2,
    backend="H2-1E",
    noise_model="realistic",
    shots=1024,
    output_dir="results/quantinuum"
):
    """Run Z2 gap extraction on Quantinuum emulator/hardware."""
    
    # 1. Build classical baseline
    H_dense = build_z2_plaquette_hamiltonian(n_plaquettes, coupling, field)
    E0_ref, E1_ref = exact_gap(H_dense)
    
    # 2. Export to Quantinuum format
    circuit = export_to_quantinuum_circuit(H_dense)
    
    # 3. Run on emulator
    adapter = QuantinuumAdapter(backend=backend)
    job_noiseless = adapter.submit_circuit(circuit, shots=shots, noise=False)
    job_noisy = adapter.submit_circuit(circuit, shots=shots, noise=noise_model)
    
    # 4. Extract gap
    E0_q, E1_q = extract_gap_from_results(job_noisy.result())
    
    # 5. Record metadata
    ledger.record_run(
        hypothesis_id="gaugegap-0002",
        backend=backend,
        job_id=job_noisy.job_id(),
        calibration=adapter.get_calibration_data(),
        results={"E0": E0_q, "E1": E1_q, "gap": E1_q - E0_q}
    )
```

#### Phase 3: Hardware Submission (Week 4-5)

- Validate emulator results against classical baseline
- Check finite-size scaling (n_plaquettes = 1, 2, 3)
- Submit to H2 hardware with explicit boundary statement
- Capture full calibration context (T1, T2, gate fidelities)
- Compare hardware vs emulator vs classical

#### Phase 4: Analogue Companion (Week 6-8)

- Design Rydberg string-breaking protocol
- Run on Braket AHS local simulator
- Submit to Aquila hardware
- Extract domain-wall dynamics and correlators

### Validation Criteria

**Accept if:**
- Gap is non-negative and finite
- Emulator → hardware results agree within error bars
- Classical ED baseline matches at same truncation
- Finite-size trend is monotonic or stable
- Calibration metadata is fully recorded

**Reject if:**
- Gap becomes negative or diverges
- Hardware results differ qualitatively from emulator
- No finite-size scaling analysis
- Missing calibration context

### Expected Outputs

- **Paper-ready dataset:** Z2/U(1) finite-lattice gap extraction on Quantinuum H2
- **Analogue benchmark:** String-breaking dynamics on QuEra Aquila
- **Cross-platform comparison:** Digital (Quantinuum) vs analogue (QuEra) vs classical (ED)
- **Timeline:** 4-8 weeks to first hardware paper

## FlowGap: Navier-Stokes Track

### Scientific Target

**Hybrid quantum-classical PDE benchmarks** for:
- Viscous Burgers equation (1D reduced model)
- Pressure-Poisson subroutine (projection method)
- Kinetic energy decay and divergence control
- Grid convergence and noise sensitivity

**Not claiming:** Navier-Stokes regularity proof or blow-up resolution

### Platform Strategy

#### Primary: IBM Heron + Qiskit Runtime

**Why:** Best official PDE-oriented cloud path
- QUICK-PDE function for Burgers/Poisson (Premium/Flex/On-Prem)
- Documented Burgers examples
- Aer noise models and Runtime mitigation (TREX/ZNE/twirling/DD)
- Heavy-hex lattice up to 156 qubits (Heron r2/r3)

**MVP Protocol:**
1. Solve classical Burgers or pressure-Poisson reference
2. Freeze nonlinear term, isolate linear solve
3. Map to VQLS or HHL-like quantum routine
4. Run on Aer simulator (noiseless → noisy)
5. Run on IBM Runtime with resilience_level=2
6. Compare residuals and conservation laws

#### Secondary: Quantinuum H2 Emulator

**Why:** All-to-all connectivity for small Poisson solves
- Better for tiny VQLS-style linear systems
- Realistic emulator for noise analysis

### Implementation Steps

#### Phase 1: Classical Reference (Week 1)

```python
# scripts/run_flowgap_poisson.py
def run_classical_poisson_reference(nx=4, ny=4, bc="dirichlet"):
    """Solve pressure-Poisson from Chorin projection."""
    
    # 1. Compute intermediate velocity
    u_star = classical_intermediate_velocity(u_n, dt, nu)
    
    # 2. Build Poisson system
    b = divergence(u_star) / dt
    A = poisson_matrix(nx, ny, bc)
    
    # 3. Solve classically
    p_ref = scipy.sparse.linalg.spsolve(A, b)
    
    # 4. Project velocity
    u_np1 = project_velocity(u_star, p_ref, dt)
    
    # 5. Check divergence
    div_after = divergence(u_np1)
    
    return {
        "pressure": p_ref,
        "velocity": u_np1,
        "divergence": np.linalg.norm(div_after),
        "residual": np.linalg.norm(A @ p_ref - b)
    }
```

#### Phase 2: Quantum Subroutine (Week 2-3)

```python
# src/gaugegap/flowgap_qsubroutine.py (extend existing)
def run_vqls_poisson(A, b, backend="aer_simulator", shots=1024):
    """VQLS for pressure-Poisson linear system."""
    
    # 1. Build cost Hamiltonian
    H = A.T @ A
    rhs_state = amplitude_encode(A.T @ b)
    
    # 2. Variational loop
    theta = init_ansatz()
    for step in range(max_iter):
        loss = compute_vqls_loss(theta, H, rhs_state, backend, shots)
        theta = optimizer_step(theta, loss)
    
    # 3. Decode solution
    p_q = decode_state(theta)
    
    return {
        "pressure_quantum": p_q,
        "residual": np.linalg.norm(A @ p_q - b),
        "iterations": step
    }
```

#### Phase 3: IBM Runtime Integration (Week 3-4)

```python
# scripts/run_flowgap_ibm_runtime.py
from qiskit_ibm_runtime import QiskitRuntimeService, EstimatorV2

def run_poisson_on_ibm_runtime(A, b, backend_name=None):
    """Run VQLS Poisson solve on IBM Runtime."""
    
    service = QiskitRuntimeService()
    backend = service.least_busy(operational=True, simulator=False)
    
    # Configure mitigation
    estimator = EstimatorV2(mode=backend)
    estimator.options.resilience_level = 2
    estimator.options.dynamical_decoupling.enable = True
    estimator.options.twirling.enable_gates = True
    
    # Run VQLS
    result = run_vqls_with_estimator(A, b, estimator)
    
    # Capture calibration
    calibration = backend.properties()
    
    return result, calibration
```

#### Phase 4: Validation (Week 4-6)

- Compare quantum residual vs classical residual
- Check divergence reduction after projection
- Grid refinement: 4×4 → 8×8 → 16×16
- Noise sensitivity: noiseless → noisy → hardware
- Shot-count sweep: 128 → 512 → 2048

### Validation Criteria

**Accept if:**
- Quantum residual converges with optimizer steps
- Divergence after projection is reduced
- Grid refinement shows consistent behavior
- Noise/mitigation analysis is complete

**Reject if:**
- Residual diverges with more iterations
- Divergence increases after projection
- Grid refinement changes qualitative behavior
- No noise analysis

### Expected Outputs

- **Hybrid benchmark:** Pressure-Poisson subroutine on IBM Runtime
- **Burgers comparison:** Classical vs quantum on tiny grid
- **Noise analysis:** Aer → Runtime → hardware progression
- **Timeline:** 2-6 weeks to first hybrid paper

## CurveRank: Riemann Hypothesis Track

### Scientific Target

**AI-guided spectral screening** of truncated Hilbert-Pólya candidates:
- Berry-Keating xp operators
- Dirac-Rindler toy models
- Quantum-graph operators
- Spectral mismatch vs known Riemann zeros
- GUE spacing statistics

**Not claiming:** Riemann Hypothesis theorem resolution

### Platform Strategy

#### Primary: QuTiP Classical Engine

**Why:** Core screening must be classical
- Exact diagonalization of truncated operators
- High-precision zero matching
- Spacing statistics (GUE vs Poisson)
- Truncation stability analysis

#### Secondary: Quantinuum/IonQ Trapped-Ion

**Why:** Experimental validation of best candidates
- Digitized Floquet engineering tested against finite zero datasets
- QPE on truncated unitaries
- Quasienergy crossing detection
- Small-scale spectral validation

### Implementation Steps

#### Phase 1: Classical Screening (Week 1-2)

```python
# scripts/run_curverank_ai_screen.py
def run_ai_guided_spectral_screen(
    families=["xp", "dirac_rindler", "quantum_graph"],
    n_basis_range=[10, 20, 30, 40, 50],
    k_zeros=20
):
    """AI-guided screening of candidate operators."""
    
    # 1. Generate candidate family
    operators = []
    for family in families:
        for n in n_basis_range:
            H = generate_candidate_operator(family, n)
            operators.append((family, n, H))
    
    # 2. Classical screening
    ranked = []
    for family, n, H in operators:
        evals = sparse_low_spectrum(H, k=k_zeros)
        target = riemann_zero_targets(k=k_zeros)
        
        score = spectral_score(
            evals=evals,
            target=target,
            spacing_metric="GUE_like",
            truncation_stability=True
        )
        
        ranked.append({
            "family": family,
            "n_basis": n,
            "score": score,
            "operator": H
        })
    
    # 3. Sort by score
    ranked.sort(key=lambda x: x["score"])
    
    return ranked[:10]  # Top 10 candidates
```

#### Phase 2: Quantum Validation (Week 3-4)

```python
# scripts/run_curverank_qpe.py
def run_qpe_on_best_candidate(H_best, backend="quantinuum_h2"):
    """Run QPE on best-ranked operator."""
    
    # 1. Build truncated unitary
    tau = 1.0
    U = expm(-1j * H_best * tau)
    
    # 2. Prepare initial state (adiabatic guess)
    psi0 = prepare_adiabatic_state(H_best)
    
    # 3. Run iterative QPE
    adapter = QuantinuumAdapter(backend=backend)
    phase_data = iterative_qpe(U, psi0, adapter, shots=1024)
    
    # 4. Extract eigenvalues
    evals_q = phases_to_eigenvalues(phase_data, tau)
    
    # 5. Compare with classical
    evals_ref = exact_low_spectrum(H_best, k=10)
    mismatch = spectral_mismatch(evals_q, evals_ref)
    
    return {
        "eigenvalues_quantum": evals_q,
        "eigenvalues_classical": evals_ref,
        "mismatch": mismatch
    }
```

#### Phase 3: Floquet Scan (Week 5-6)

```python
# scripts/run_curverank_floquet.py
def run_floquet_crossing_scan(H_best, param_range, backend="ionq_forte"):
    """Scan for quasienergy crossings (Riemann-zero analogue)."""
    
    crossings = []
    for param in param_range:
        H_param = parameterize_operator(H_best, param)
        U = build_floquet_unitary(H_param)
        
        # Run on trapped-ion hardware
        adapter = IonQAdapter(backend=backend)
        quasienergies = extract_quasienergies(U, adapter)
        
        # Detect crossings
        if detect_crossing(quasienergies):
            crossings.append(param)
    
    return crossings
```

### Validation Criteria

**Accept if:**
- Spectral mismatch decreases or stabilizes with truncation
- Spacing statistics trend toward GUE
- Eigenvalues are numerically stable
- QPE results match classical ED at same truncation

**Reject if:**
- Mismatch increases monotonically
- Spacing diverges toward Poisson
- Eigenvalues become unstable
- QPE results differ qualitatively from ED

### Expected Outputs

- **AI-ranked operator family:** Top 10 candidates with scores
- **Quantum validation:** QPE on best 2-3 candidates
- **Floquet experiment:** Crossing detection on trapped-ion hardware
- **Timeline:** 2-6 weeks to first spectral paper

## Cross-Track Infrastructure

### Provider Adapter Architecture

```python
# src/gaugegap/providers/__init__.py
from abc import ABC, abstractmethod

class QuantumProvider(ABC):
    """Base class for quantum provider adapters."""
    
    @abstractmethod
    def submit_job(self, circuit, shots, **kwargs):
        """Submit job to provider."""
        pass
    
    @abstractmethod
    def get_calibration_data(self):
        """Retrieve backend calibration."""
        pass
    
    @abstractmethod
    def get_result(self, job_id):
        """Retrieve job result."""
        pass

# Concrete implementations
class QuantinuumProvider(QuantumProvider): ...
class IBMRuntimeProvider(QuantumProvider): ...
class BraketProvider(QuantumProvider): ...
class IonQProvider(QuantumProvider): ...
```

### Hardware-Ready Boundary Checks

```python
# src/gaugegap/quantum_boundary.py (extend existing)
def check_hardware_ready(circuit, provider, hypothesis_id):
    """Verify circuit is ready for hardware submission."""
    
    checks = {
        "circuit_valid": validate_circuit(circuit),
        "provider_credentials": check_credentials(provider),
        "hypothesis_registered": check_hypothesis(hypothesis_id),
        "classical_baseline_exists": check_baseline(hypothesis_id),
        "emulator_validated": check_emulator_results(hypothesis_id),
        "calibration_current": check_calibration_age(provider)
    }
    
    if not all(checks.values()):
        raise HardwareNotReadyError(checks)
    
    return True
```

### Emulator-to-Hardware Workflow

```python
# src/gaugegap/workflows/emulator_to_hardware.py
def run_emulator_to_hardware_workflow(
    circuit,
    provider,
    hypothesis_id,
    classical_baseline
):
    """Standard emulator → hardware workflow."""
    
    # 1. Validate classical baseline
    assert classical_baseline is not None
    
    # 2. Run noiseless emulator
    result_noiseless = provider.run_emulator(circuit, noise=False)
    
    # 3. Run noisy emulator
    result_noisy = provider.run_emulator(circuit, noise="realistic")
    
    # 4. Compare with classical
    validate_emulator_results(result_noisy, classical_baseline)
    
    # 5. Check hardware readiness
    check_hardware_ready(circuit, provider, hypothesis_id)
    
    # 6. Submit to hardware
    job = provider.submit_hardware(circuit, shots=1024)
    
    # 7. Capture metadata
    metadata = {
        "job_id": job.job_id(),
        "backend": provider.backend_name,
        "calibration": provider.get_calibration_data(),
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # 8. Record in ledger
    ledger.record_hardware_run(hypothesis_id, job, metadata)
    
    return job, metadata
```

## Implementation Timeline

### Week 1-2: Foundation
- [x] Analyze quantum MVP recommendations
- [ ] Create provider adapter architecture
- [ ] Implement hardware-ready boundary checks
- [ ] Extend quantum_status.py for provider probing

### Week 3-4: GaugeGap Primary
- [ ] Quantinuum H2 emulator integration
- [ ] Z2 plaquette export to Quantinuum format
- [ ] Emulator validation (noiseless → noisy)
- [ ] Gap extraction with VQE/VQD

### Week 5-6: GaugeGap Hardware
- [ ] H2 hardware submission with calibration capture
- [ ] Cross-platform comparison (emulator vs hardware vs ED)
- [ ] Finite-size scaling analysis
- [ ] First hardware paper draft

### Week 7-8: GaugeGap Analogue
- [ ] AWS Braket AHS adapter
- [ ] Rydberg string-breaking protocol
- [ ] Aquila local simulator validation
- [ ] Aquila hardware submission

### Week 3-6 (Parallel): FlowGap
- [ ] IBM Runtime adapter
- [ ] Pressure-Poisson classical reference
- [ ] VQLS quantum subroutine
- [ ] Runtime hardware submission with mitigation
- [ ] Hybrid benchmark paper draft

### Week 3-6 (Parallel): CurveRank
- [ ] AI-guided spectral screening (classical)
- [ ] Top-10 candidate ranking
- [ ] QPE on best candidates (Quantinuum/IonQ)
- [ ] Floquet crossing scan
- [ ] Spectral paper draft

## Risk Mitigation

### Technical Risks

| Risk | Mitigation |
|------|-----------|
| Provider credentials not available | Keep all workflows runnable in emulator/simulator mode |
| Hardware queue times too long | Prioritize emulator validation, hardware is optional |
| Calibration drift between runs | Capture full calibration metadata per job |
| Finite-size effects dominate signal | Require explicit finite-size scaling analysis |
| Noise overwhelms signal | Use mitigation controls (ZNE, DD, twirling, debiasing) |

### Scientific Risks

| Risk | Mitigation |
|------|-----------|
| Overclaiming theorem progress | Enforce claim boundary in all outputs |
| Confusing artefacts with physics | Require classical baseline agreement |
| Overfitting finite truncations | Require truncation stability analysis |
| Missing negative results | Retain all results in ledger, even failures |

## Success Criteria

### GaugeGap MVP Success
- ✅ Finite-lattice gap extracted on Quantinuum H2 hardware
- ✅ Emulator → hardware → classical cross-validation complete
- ✅ Finite-size scaling analysis (n_plaquettes = 1, 2, 3)
- ✅ String-breaking benchmark on QuEra Aquila
- ✅ Paper-ready dataset with full calibration metadata

### FlowGap MVP Success
- ✅ Pressure-Poisson hybrid benchmark on IBM Runtime
- ✅ Classical → Aer → Runtime → hardware progression
- ✅ Residual and divergence analysis complete
- ✅ Grid refinement validation (4×4 → 8×8)
- ✅ Noise sensitivity analysis with mitigation

### CurveRank MVP Success
- ✅ AI-ranked operator family (top 10 candidates)
- ✅ Classical spectral screening complete
- ✅ QPE validation on best 2-3 candidates
- ✅ Floquet crossing scan on trapped-ion hardware
- ✅ Spectral mismatch and GUE statistics reported

## Next Actions

1. **This week:** Implement provider adapter architecture
2. **Next week:** Start GaugeGap Quantinuum emulator integration
3. **In parallel:** Run FlowGap entirely in simulators until robust
4. **Then:** Use CurveRank as AI-heavy classical search, quantum validation optional

## References

- Quantinuum H2/Helios: Official SU(2) lattice gauge theory tutorial
- IBM QUICK-PDE: Burgers equation quantum solver (Premium/Flex/On-Prem)
- QuEra Aquila: String-breaking in programmable quantum simulator
- Trapped-ion Riemann zeros: Floquet engineering experimental observation
- GaugeGap Foundry: Current repository state and verification ladder

## Claim Boundary Reminder

**This plan does NOT claim to solve any Millennium Prize problem.**

It establishes:
- Finite-system benchmarking infrastructure
- Hardware-ready quantum workflows
- Cross-platform validation frameworks
- Hypothesis pruning mechanisms
- Publication-grade datasets

The goal is **meaningful progress today** on verification-first quantum experiments, not speculative theorem claims.
