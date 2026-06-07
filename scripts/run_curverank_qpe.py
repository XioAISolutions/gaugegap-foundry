#!/usr/bin/env python3
"""CurveRank QPE example: spectral validation on trapped-ion hardware.

This script demonstrates quantum phase estimation (QPE) for validating
AI-ranked candidate Hilbert-Pólya operators on trapped-ion platforms.

Workflow:
1. Classical spectral screening of candidate operators
2. Select best candidates based on mismatch to Riemann zeros
3. Build QPE circuit for truncated operator
4. Run on emulator, then hardware
5. Compare estimated eigenvalues with target zeros

This is SPECTRAL SCREENING of toy operators, not a proof route to the
Riemann Hypothesis.

Example usage:
    # Simulator only
    python scripts/run_curverank_qpe.py --family xp --n-basis 10 --backend simulator
    
    # Quantinuum emulator
    python scripts/run_curverank_qpe.py --family xp --n-basis 10 --backend quantinuum --emulator
    
    # IonQ hardware (requires credentials)
    python scripts/run_curverank_qpe.py --family xp --n-basis 10 --backend ionq --device forte-1 --shots 2048
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

import numpy as np
from scipy.linalg import expm

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gaugegap.curverank_operators import generate_candidate_family
from gaugegap.curverank_spectral import (
    riemann_zero_targets,
    spectral_mismatch,
)
from gaugegap.curverank_qpe import (
    build_qpe_circuit,
    choose_evolution_time,
    extract_phase_from_counts,
    measured_phase_to_eigenvalue,
    pad_to_power_of_two,
)
from gaugegap.providers import get_provider
from gaugegap.cost_estimation import estimate_job_cost
from gaugegap.ledger import utc_run_id


def _confirm(prompt: str, assume_yes: bool) -> bool:
    """Ask the user to confirm, auto-proceeding when non-interactive.

    Returns True (proceed) when ``assume_yes`` is set or stdin is not a TTY
    (e.g. CI, pipes, headless desktop runs); otherwise prompts interactively.
    """
    if assume_yes or not sys.stdin.isatty():
        print(f"{prompt} [auto-yes]")
        return True
    return input(prompt).strip().lower() == "y"


def run_curverank_qpe(
    family: str,
    n_basis: int,
    backend_type: str,
    device_name: Optional[str] = None,
    shots: int = 1024,
    n_precision: int = 4,
    use_emulator: bool = False,
    output_dir: Path = Path("results/curverank"),
    assume_yes: bool = False,
) -> Dict[str, Any]:
    """Run CurveRank QPE benchmark.
    
    Args:
        family: Operator family (xp, dirac_rindler, quantum_graph)
        n_basis: Basis size for truncation
        backend_type: Backend type (quantinuum, ionq, simulator)
        device_name: Specific device name (optional)
        shots: Number of shots
        n_precision: QPE precision qubits
        use_emulator: Use emulator instead of hardware
        output_dir: Output directory
    
    Returns:
        Results dictionary
    """
    print(f"\n{'='*60}")
    print("CurveRank QPE Benchmark")
    print(f"{'='*60}\n")
    
    print(f"Operator family: {family}")
    print(f"Basis size: {n_basis}")
    print(f"Backend: {backend_type}")
    if device_name:
        print(f"Device: {device_name}")
    print(f"Shots: {shots}")
    print(f"Precision qubits: {n_precision}")
    print(f"Emulator: {use_emulator}\n")
    
    # Step 1: Generate and screen candidate operators
    print("Step 1: Generating candidate operators...")
    candidates = generate_candidate_family(
        family=family,
        n_basis_range=[n_basis],
    )
    operators = [c["operator"] for c in candidates]
    print(f"  Generated {len(operators)} candidate(s)")

    # Step 2: Classical spectral screening
    print("\nStep 2: Classical spectral screening...")
    k_zeros = max(1, min(10, n_basis // 2))
    target_zeros = riemann_zero_targets(k_zeros)

    scores = []
    for i, H in enumerate(operators):
        eigvals, eigvecs = np.linalg.eigh(H)
        score = spectral_mismatch(eigvals, target_zeros)
        scores.append((score, i, eigvals, eigvecs))
        print(f"  Candidate {i}: mismatch = {score:.6f}")

    # Select best candidate
    scores.sort(key=lambda s: s[0])
    best_score, best_idx, best_evals, best_evecs = scores[0]
    H_best = operators[best_idx]

    # Pick the smallest strictly-positive eigenvalue as the QPE target and grab
    # its eigenvector so the system register is prepared in (close to) an
    # eigenstate -- this is what gives a clean phase read.
    positive = [(e, j) for j, e in enumerate(best_evals) if e > 1e-9]
    if not positive:
        print("  No positive eigenvalue to estimate; aborting.")
        return {}
    target_eig, target_col = min(positive, key=lambda p: p[0])
    target_state = best_evecs[:, target_col]

    print(f"\n  Best candidate: {best_idx} (mismatch = {best_score:.6f})")
    print(f"  Target zeros: {target_zeros[:3]}")
    print(f"  Best eigenvalues: {best_evals[:3]}")
    print(f"  QPE target eigenvalue: {target_eig:.6f}")

    # Step 3: Build QPE circuit
    print("\nStep 3: Building QPE circuit...")

    # Evolution time scaled to the spectral radius so NO eigenvalue aliases onto
    # another phase (in particular the target is not folded to phase zero, which
    # is what tau = 2*pi/|E_1| used to do).
    tau = choose_evolution_time(best_evals)

    # Pad to a power-of-two dimension so the system register is whole qubits.
    H_pad, state_pad = pad_to_power_of_two(H_best, target_state)
    U = expm(-1j * H_pad * tau)

    qc = build_qpe_circuit(U, n_precision=n_precision, initial_statevector=state_pad)
    n_qubits = qc.num_qubits
    depth = qc.depth()

    print(f"  Circuit: {n_qubits} qubits, depth {depth}")
    print(f"  Evolution time: {tau:.4f}")
    
    if n_qubits > 20:
        print(f"\n  Warning: {n_qubits} qubits may exceed hardware limits")
        if not _confirm("  Continue? (y/n): ", assume_yes):
            return {}
    
    # Step 4: Cost estimation
    print("\nStep 4: Estimating cost...")
    if not use_emulator and backend_type != "simulator":
        if backend_type == "quantinuum":
            cost_est = estimate_job_cost(
                provider="quantinuum",
                backend=device_name or "H2-1",
                n_circuits=1,
                shots_per_circuit=shots,
                circuit_depth=depth,
                two_qubit_gates=qc.num_nonlocal_gates()
            )
        elif backend_type == "ionq":
            cost_est = estimate_job_cost(
                provider="ionq",
                backend=device_name or "forte-1",
                n_circuits=1,
                shots_per_circuit=shots,
                n_gates=qc.size(),
                n_qubits=n_qubits
            )
        else:
            cost_est = None
        
        if cost_est:
            print(f"  Estimated cost: ${cost_est.estimated_cost_usd:.2f} USD")
            print(f"  Confidence: {cost_est.confidence}")
            
            if cost_est.estimated_cost_usd > 20.0:
                if not _confirm("\n  Cost exceeds $20. Continue? (y/n): ", assume_yes):
                    print("  Aborted by user.")
                    return {}
    
    # Step 5: Run quantum job
    print("\nStep 5: Running quantum job...")
    try:
        if backend_type == "simulator":
            # Local simulator (transpile so the dense controlled-unitary and
            # state preparation decompose into runnable basis gates).
            from qiskit import transpile
            from qiskit_aer import AerSimulator
            backend = AerSimulator()
            tqc = transpile(qc, backend, basis_gates=["u", "cx"], optimization_level=1)
            job = backend.run(tqc, shots=shots)
            result = job.result()
            counts = result.get_counts()
            job_id = "simulator"
            metadata_dict = {"backend": "simulator", "shots": shots}
            
        elif backend_type == "quantinuum":
            provider = get_provider("quantinuum", backend_name=device_name or "H2-1")
            
            if use_emulator:
                result_data, metadata = provider.submit_emulator(
                    circuit=qc,
                    shots=shots
                )
            else:
                result_data, metadata = provider.submit_hardware(
                    circuit=qc,
                    shots=shots
                )
            
            counts = result_data  # Assuming counts format
            job_id = metadata.job_id
            metadata_dict = {
                "backend": metadata.backend_name,
                "shots": shots,
                "job_id": job_id
            }
            
        elif backend_type == "ionq":
            provider = get_provider("ionq", backend_name=device_name or "forte-1")
            
            result_data, metadata = provider.submit_hardware(
                circuit=qc,
                shots=shots
            )
            
            counts = result_data
            job_id = metadata.job_id
            metadata_dict = {
                "backend": metadata.backend_name,
                "shots": shots,
                "job_id": job_id
            }
        
        else:
            raise ValueError(f"Unknown backend type: {backend_type}")
        
        print(f"  Job completed: {job_id}")
        
    except Exception as e:
        print(f"  Error: {e}")
        import traceback
        traceback.print_exc()
        return {}
    
    # Step 6: Extract and analyze results
    print("\nStep 6: Analyzing results...")
    
    phase, uncertainty = extract_phase_from_counts(counts, n_precision)

    # Invert the (aliasing-free) phase->eigenvalue map. The phase is folded at
    # 0.5 to recover signed eigenvalues; uncertainty is propagated through the
    # same linear scale 2*pi/tau.
    eigenvalue_est = measured_phase_to_eigenvalue(phase, tau)
    eigenvalue_unc = uncertainty * 2 * np.pi / tau if tau != 0 else 0

    print(f"  Measured phase: {phase:.6f} ± {uncertainty:.6f}")
    print(f"  Estimated eigenvalue: {eigenvalue_est:.6f} ± {eigenvalue_unc:.6f}")
    print(f"  Target (first zero): {target_zeros[0]:.6f}")
    print(f"  Classical (target eigenvalue): {target_eig:.6f}")

    # Compute agreement metrics
    error_vs_target = abs(eigenvalue_est - target_zeros[0])
    error_vs_classical = abs(eigenvalue_est - target_eig)
    
    print(f"\n  Error vs target: {error_vs_target:.6f}")
    print(f"  Error vs classical: {error_vs_classical:.6f}")
    
    # Step 7: Save results
    metrics = {
        "family": family,
        "n_basis": n_basis,
        "n_precision": n_precision,
        "n_qubits": n_qubits,
        "circuit_depth": depth,
        "shots": shots,
        "backend_type": backend_type,
        "device_name": device_name,
        "use_emulator": use_emulator,
        "best_candidate_idx": best_idx,
        "classical_mismatch": float(best_score),
        "classical_eigenvalues": [float(e) for e in best_evals],
        "qpe_target_eigenvalue": float(target_eig),
        "evolution_time": float(tau),
        "target_zeros": [float(z) for z in target_zeros],
        "measured_phase": float(phase),
        "phase_uncertainty": float(uncertainty),
        "estimated_eigenvalue": float(eigenvalue_est),
        "eigenvalue_uncertainty": float(eigenvalue_unc),
        "error_vs_target": float(error_vs_target),
        "error_vs_classical": float(error_vs_classical),
        "timestamp": datetime.now().isoformat(),
        **metadata_dict
    }
    
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"curverank-qpe-{family}-{n_basis}-{backend_type}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    
    with open(output_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")

    # Append a provenance record to the JSONL ledger.
    ledger_record = {
        "hypothesis_id": "curverank-0001",
        "result_type": "quantum_qpe",
        "run_id": utc_run_id(),
        "track": "curverank",
        "method": "qpe_spectral_validation",
        "scope": "truncated_operator_screening",
        "metrics": metrics,
    }
    ledger_path = output_dir / "curverank-qpe-ledger.jsonl"
    with ledger_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(ledger_record, sort_keys=True, default=str) + "\n")

    print(f"\n{'='*60}")
    print("QPE benchmark complete")
    print(f"{'='*60}\n")
    
    return metrics


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="CurveRank QPE spectral validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Local simulator
  python scripts/run_curverank_qpe.py --family xp --n-basis 10 --backend simulator
  
  # Quantinuum emulator
  python scripts/run_curverank_qpe.py --family xp --n-basis 10 --backend quantinuum --emulator
  
  # IonQ hardware
  python scripts/run_curverank_qpe.py --family xp --n-basis 10 --backend ionq --device forte-1 --shots 2048
        """
    )
    
    parser.add_argument(
        "--family",
        type=str,
        choices=["xp", "dirac_rindler", "quantum_graph"],
        default="xp",
        help="Operator family (default: xp)"
    )
    parser.add_argument(
        "--n-basis",
        type=int,
        default=10,
        help="Basis size for truncation (default: 10)"
    )
    parser.add_argument(
        "--backend",
        type=str,
        choices=["simulator", "quantinuum", "ionq"],
        default="simulator",
        help="Backend type (default: simulator)"
    )
    parser.add_argument(
        "--device",
        type=str,
        help="Specific device name (e.g., H2-1, forte-1)"
    )
    parser.add_argument(
        "--shots",
        type=int,
        default=1024,
        help="Number of shots (default: 1024)"
    )
    parser.add_argument(
        "--n-precision",
        type=int,
        default=4,
        help="QPE precision qubits (default: 4)"
    )
    parser.add_argument(
        "--emulator",
        action="store_true",
        help="Use emulator instead of hardware"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/curverank"),
        help="Output directory (default: results/curverank)"
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Auto-confirm all prompts (non-interactive runs)"
    )

    args = parser.parse_args()

    # Validate parameters
    if args.n_basis < 4:
        print("Error: n-basis must be at least 4")
        sys.exit(1)

    if args.n_precision > 8:
        print("Warning: n-precision > 8 may be impractical on current hardware")
        if not _confirm("Continue? (y/n): ", args.yes):
            return
    
    # Run benchmark
    try:
        results = run_curverank_qpe(
            family=args.family,
            n_basis=args.n_basis,
            backend_type=args.backend,
            device_name=args.device,
            shots=args.shots,
            n_precision=args.n_precision,
            use_emulator=args.emulator,
            output_dir=args.output_dir,
            assume_yes=args.yes,
        )
        
        if results:
            print("\n✓ QPE benchmark completed successfully")
        else:
            print("\n✗ QPE benchmark failed or was aborted")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

# Made with Bob
