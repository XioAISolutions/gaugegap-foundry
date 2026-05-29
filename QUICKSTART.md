# One-Day Quickstart: Run Your First Quantum Experiment

**Goal**: Get from zero to first quantum hardware result in one day.

---

## Morning (2 hours): Setup

```bash
# 1. Clone repository (2 minutes)
git clone https://github.com/yourusername/gaugegap-foundry.git
cd gaugegap-foundry

# 2. Install everything (5 minutes)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[all]"

# 3. Verify installation (3 minutes)
python -c "from gaugegap.providers import get_provider; print('✓ Ready')"

# 4. Get quantum credentials (30 minutes)
# Sign up at: https://www.quantinuum.com/products/h-series
# Get your API key and set it:
export QUANTINUUM_API_KEY="your-key-here"

# 5. Test connection (2 minutes)
python -c "
from gaugegap.providers import get_provider
provider = get_provider('quantinuum', backend_name='H2-1')
print('✓ Connected to Quantinuum')
"
```

---

## Afternoon (4 hours): Run Experiments

### Option A: Fastest Path (Emulator Only - Free)

```bash
# Run complete GaugeGap workflow on emulator (30 minutes)
python scripts/run_gaugegap_complete.py \
    --hypothesis-id gaugegap-0002 \
    --sizes 4,6 \
    --field-points 3 \
    --provider quantinuum \
    --backend H2-1 \
    --emulator-only \
    --output-dir results/day1

# Check results
ls -lh results/day1/
cat results/day1/summary.json
```

**You now have**: Quantum simulation results with certified bounds!

### Option B: Real Hardware (Costs ~$25-50)

```bash
# 1. Estimate cost first (1 minute)
python -c "
from gaugegap.cost_estimation import estimate_job_cost
est = estimate_job_cost(
    provider='quantinuum',
    backend='H2-1',
    n_circuits=5,
    shots_per_circuit=1000,
    circuit_depth=50,
    two_qubit_gates=20
)
print(f'Estimated cost: ${est.estimated_cost_usd:.2f}')
"

# 2. Run on real quantum hardware (2-4 hours including queue time)
python scripts/run_gaugegap_complete.py \
    --hypothesis-id gaugegap-0002 \
    --sizes 4,6 \
    --field-points 3 \
    --provider quantinuum \
    --backend H2-1 \
    --hardware \
    --certify \
    --output-dir results/day1-hardware

# 3. Analyze results with certified bounds
python -c "
import json
with open('results/day1-hardware/summary.json') as f:
    data = json.load(f)
print(f\"Mass gap: {data['gap_continuum']} ± {data['gap_uncertainty']}\")
print(f\"Certified bounds: [{data['gap_lower']}, {data['gap_upper']}]\")
"
```

**You now have**: Real quantum hardware results with mathematical certification!

---

## Evening (2 hours): Analyze & Share

```bash
# 1. Generate publication-ready figures (5 minutes)
python scripts/visualize_results.py \
    --input-dir results/day1-hardware \
    --output-dir figures/

# 2. Export formal proof certificate (2 minutes)
python -c "
from gaugegap.rigorous import export_to_lean4
from pathlib import Path
import json

with open('results/day1-hardware/theorem.json') as f:
    theorem = json.load(f)

export_to_lean4(theorem, 'proofs/mass_gap_day1.lean')
print('✓ Lean 4 proof exported')
"

# 3. Create summary report (1 minute)
python scripts/generate_report.py \
    --input-dir results/day1-hardware \
    --output report.md

# 4. Share your results!
cat report.md
```

---

## What You Accomplished Today

✅ **Installed** complete quantum+classical+AI infrastructure  
✅ **Connected** to real quantum hardware (Quantinuum H2)  
✅ **Ran** first quantum experiment (emulator or hardware)  
✅ **Obtained** certified bounds with mathematical rigor  
✅ **Generated** publication-ready figures  
✅ **Exported** formal proof certificate (Lean 4)  
✅ **Created** summary report

---

## Tomorrow: Scale Up

```bash
# Run all three tracks in parallel
python scripts/run_all_tracks.py \
    --gaugegap-sizes 4,6,8 \
    --flowgap-sizes 16,32 \
    --curverank-candidates 100 \
    --provider quantinuum \
    --hardware \
    --output-dir results/day2
```

---

## If Something Goes Wrong

### Installation Issues
```bash
# Try minimal install first
pip install -e .
pip install qiskit qiskit-aer numpy scipy

# Then add quantum providers one by one
pip install pytket-quantinuum  # For Quantinuum
pip install qiskit-ibm-runtime  # For IBM
```

### Credential Issues
```bash
# Verify credentials
python scripts/quantum_status.py

# Test each provider
python -c "from gaugegap.providers import get_provider; get_provider('quantinuum', 'H2-1').check_credentials()"
```

### Out of Memory
```bash
# Use smaller system sizes
python scripts/run_gaugegap_complete.py --sizes 4 --field-points 2
```

### Need Help
```bash
# Check logs
cat logs/gaugegap_complete.log

# Run tests
pytest tests/ -v -k "test_providers"

# Open issue: https://github.com/yourusername/gaugegap-foundry/issues
```

---

## Cost Summary

| Option | Time | Cost | What You Get |
|--------|------|------|--------------|
| **Emulator Only** | 2-3 hours | $0 | Simulation results, certified bounds |
| **Hardware (Small)** | 4-6 hours | $25-50 | Real quantum results, 2-3 system sizes |
| **Hardware (Full)** | 6-8 hours | $100-200 | Complete dataset, publication-ready |

---

## Next Steps

**Week 2**: Run FlowGap and CurveRank tracks  
**Week 3**: Cross-platform validation (IBM, IonQ)  
**Week 4**: Draft first manuscript  
**Month 2**: Submit to journal  
**Month 6**: First publication! 🎉

---

## The Bottom Line

**In one day, you can**:
- Install complete infrastructure
- Connect to quantum hardware
- Run first experiment
- Get certified results
- Generate formal proofs

**Everything is automated. Just run the commands.**

Start now: `git clone https://github.com/yourusername/gaugegap-foundry.git`