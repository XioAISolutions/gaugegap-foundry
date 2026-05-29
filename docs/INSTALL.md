# Installation and Setup Guide

Complete guide for setting up the GaugeGap Foundry quantum MVP infrastructure.

## Quick Start

```bash
# Clone repository
git clone https://github.com/your-org/gaugegap-foundry.git
cd gaugegap-foundry

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install base dependencies
python -m pip install -e .

# Run classical baselines (no quantum dependencies required)
python scripts/run_gap_sweep.py
python scripts/run_z2_plaquette.py
```

## Installation Options

### Option 1: Minimal (Classical Only)

For classical baselines and exact diagonalization only:

```bash
python -m pip install -e .
```

**Includes:**
- NumPy for numerical computing
- PyYAML for hypothesis files
- Classical solvers (exact diagonalization, PDE solvers)

**Use for:**
- Generating classical reference data
- Finite-system benchmarks without quantum simulation

### Option 2: Quantum Simulation (IBM/Qiskit)

For local quantum simulation with Qiskit:

```bash
python -m pip install -e '.[quantum]'
```

**Includes:**
- Qiskit ≥1.4
- Qiskit Aer ≥0.15 (local simulators)
- Qiskit IBM Runtime ≥0.34 (for hardware access)

**Use for:**
- Pauli operator export and validation
- Local statevector and shot-based simulation
- IBM Runtime hardware access (requires credentials)

### Option 3: Quantinuum Integration

For Quantinuum H2/Helios emulators and hardware:

```bash
python -m pip install -e '.[quantinuum]'
```

**Includes:**
- pytket ≥1.30
- pytket-quantinuum ≥0.37
- pytket-qiskit ≥0.54 (for circuit conversion)

**Use for:**
- GaugeGap experiments on trapped-ion systems
- H2 emulator validation
- H2/Helios hardware submission (requires API key)

### Option 4: AWS Braket (QuEra Aquila)

For neutral-atom analog simulation:

```bash
python -m pip install -e '.[braket]'
```

**Includes:**
- amazon-braket-sdk ≥1.80

**Use for:**
- Local AHS simulator
- QuEra Aquila hardware access (requires AWS credentials)
- String-breaking and gauge dynamics experiments

### Option 5: IonQ Integration

For IonQ trapped-ion systems:

```bash
python -m pip install -e '.[ionq]'
```

**Includes:**
- qiskit-ionq ≥0.5

**Use for:**
- IonQ Forte/Aria hardware access
- QPE experiments for CurveRank
- All-to-all connectivity benchmarks

### Option 6: FlowGap (PDE Solvers)

For Navier-Stokes reduced models:

```bash
python -m pip install -e '.[flow]'
```

**Includes:**
- SciPy ≥1.11 (sparse linear algebra, ODE solvers)

**Use for:**
- Burgers equation benchmarks
- Pressure-Poisson subroutines
- Classical PDE reference solutions

### Option 7: CurveRank (Spectral Analysis)

For Riemann hypothesis spectral screening:

```bash
python -m pip install -e '.[spectral]'
```

**Includes:**
- SciPy ≥1.11 (eigensolvers, special functions)

**Use for:**
- Berry-Keating operator diagonalization
- Spectral mismatch analysis
- GUE spacing statistics

### Option 8: Complete Stack

For all features:

```bash
python -m pip install -e '.[all]'
```

**Includes:** All optional dependencies above

**Use for:**
- Full cross-platform development
- Running all three tracks (GaugeGap, FlowGap, CurveRank)
- Complete testing and validation

### Option 9: Development

For development with testing:

```bash
python -m pip install -e '.[dev]'
```

**Includes:**
- pytest ≥8

**Use for:**
- Running test suite
- Contributing to the project

## Provider Credentials

### IBM Quantum

**Option A: Save account (recommended)**

```python
from qiskit_ibm_runtime import QiskitRuntimeService

QiskitRuntimeService.save_account(
    channel="ibm_quantum",
    token="YOUR_IBM_QUANTUM_TOKEN",
    instance="hub-x/group-y/project-z"
)
```

**Option B: Environment variables**

```bash
export QISKIT_IBM_TOKEN="YOUR_IBM_QUANTUM_TOKEN"
export QISKIT_IBM_INSTANCE="hub-x/group-y/project-z"
```

**Get credentials:**
1. Sign up at https://quantum.ibm.com/
2. Go to Account → API tokens
3. Copy your token and instance

### Quantinuum

**Environment variable:**

```bash
export QUANTINUUM_API_KEY="YOUR_QUANTINUUM_API_KEY"
```

**Get credentials:**
1. Contact Quantinuum for API access
2. H2-1E emulator works without credentials

### AWS Braket (QuEra Aquila)

**Environment variables:**

```bash
export AWS_ACCESS_KEY_ID="YOUR_AWS_ACCESS_KEY"
export AWS_SECRET_ACCESS_KEY="YOUR_AWS_SECRET_KEY"
export AWS_DEFAULT_REGION="us-east-1"
```

**Get credentials:**
1. Sign up for AWS account
2. Enable Amazon Braket service
3. Create IAM user with Braket permissions
4. Generate access keys

**Local simulator works without credentials**

### IonQ

**Environment variable:**

```bash
export IONQ_API_KEY="YOUR_IONQ_API_KEY"
```

**Get credentials:**
1. Sign up at https://cloud.ionq.com/
2. Generate API key from dashboard

## Verification

### Test Classical Baselines

```bash
# Run all classical tests
python -m pytest tests/test_exact_gap.py
python -m pytest tests/test_z2_chain.py
python -m pytest tests/test_z2_plaquette.py

# Generate baseline data
python scripts/run_gap_sweep.py --sizes 4,6 --field-points 3
python scripts/run_z2_plaquette.py
python scripts/run_flowgap_burgers.py --sizes 16,32
python scripts/run_curverank_screen.py --family xp --n-basis 10,20
```

### Test Quantum Simulation

```bash
# Test Qiskit integration
python -m pytest tests/test_qiskit_backend.py
python -m pytest tests/test_pauli_export.py

# Run quantum simulations
python scripts/run_quantum_gap_replica.py
python scripts/run_dynamics.py --backend statevector --n-sites 4
python scripts/run_dynamics.py --backend aer-sampler --n-sites 4 --shots 512
python scripts/run_vqe_gap.py --samples 64
```

### Test Provider Adapters

```bash
# Test provider instantiation (no credentials required)
python -m pytest tests/test_providers.py

# Test hardware readiness checks
python -m pytest tests/test_hardware_ready.py

# Check quantum status
python scripts/quantum_status.py
python scripts/quantum_status.py --probe-ibm  # If IBM credentials configured
```

### Test Example Scripts

```bash
# GaugeGap on Quantinuum (emulator only, no credentials)
python scripts/run_gaugegap_quantinuum.py --backend H2-1E --emulator-only

# With hardware (requires QUANTINUUM_API_KEY)
python scripts/run_gaugegap_quantinuum.py --backend H2-1 --hardware
```

## Troubleshooting

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'qiskit'`

**Solution:**
```bash
python -m pip install -e '.[quantum]'
```

### Credential Errors

**Problem:** `CredentialsError: IBM Quantum credentials required`

**Solution:**
1. Check environment variables: `echo $QISKIT_IBM_TOKEN`
2. Or save account: `QiskitRuntimeService.save_account(...)`
3. Or run in emulator-only mode

### Provider Not Available

**Problem:** `ImportError: pytket-quantinuum is required`

**Solution:**
```bash
python -m pip install -e '.[quantinuum]'
```

### Test Failures

**Problem:** Tests fail with `FileNotFoundError`

**Solution:**
```bash
# Ensure you're in the repository root
cd /path/to/gaugegap-foundry

# Reinstall in editable mode
python -m pip install -e .
```

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/my-feature
```

### 2. Install Development Dependencies

```bash
python -m pip install -e '.[dev,all]'
```

### 3. Run Tests

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_providers.py -v

# Run with coverage
python -m pytest --cov=src/gaugegap
```

### 4. Verify Smoke Tests

```bash
# Run smoke tests from AGENTS.md
python scripts/run_gap_sweep.py --sizes 4,6 --field-points 3 --output-dir /tmp/gaugegap-smoke
python scripts/run_z2_plaquette.py --output-dir /tmp/gaugegap-0002-exact
python scripts/run_flowgap_burgers.py --sizes 16,32 --nu-points 3 --n-steps 20 --output-dir /tmp/flowgap-smoke
python scripts/run_curverank_screen.py --family xp --n-basis 10,20 --k-zeros 10 --output-dir /tmp/curverank-smoke
```

### 5. Commit and Push

```bash
git add .
git commit -m "Add feature: description"
git push origin feature/my-feature
```

## Next Steps

- **For GaugeGap:** See [`docs/quantum-mvp-plan.md`](quantum-mvp-plan.md) for Quantinuum workflow
- **For FlowGap:** See [`hypotheses/flowgap-0001.yaml`](../hypotheses/flowgap-0001.yaml) for Burgers benchmark
- **For CurveRank:** See [`hypotheses/curverank-0001.yaml`](../hypotheses/curverank-0001.yaml) for spectral screening
- **For Hardware:** See [`docs/quantum-boundary.md`](quantum-boundary.md) for readiness checks

## Support

- **Issues:** https://github.com/your-org/gaugegap-foundry/issues
- **Documentation:** [`docs/`](.)
- **Examples:** [`scripts/`](../scripts/)
- **Tests:** [`tests/`](../tests/)