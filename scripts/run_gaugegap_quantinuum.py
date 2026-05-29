#!/usr/bin/env python3
"""Run GaugeGap Z2 plaquette experiment on Quantinuum H2/Helios.

This script demonstrates the complete emulator-to-hardware workflow:
1. Compute classical baseline
2. Run noiseless emulator
3. Run noisy emulator with realistic noise
4. Validate emulator vs classical
5. Submit to hardware (if --hardware flag is set)

Example usage:
    # Emulator only (no credentials required)
    python scripts/run_gaugegap_quantinuum.py --backend H2-1E --emulator-only
    
    # Full workflow with hardware submission
    export QUANTINUUM_API_KEY="your-api-key"
    python scripts/run_gaugegap_quantinuum.py --backend H2-1 --hardware
"""

import argparse
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gaugegap.models.z2_plaquette import (
    open_plaquette_chain_layout,
    validate_parameters,
    hamiltonian_dense
)
from gaugegap.solvers.exact_gap import exact_gap
from gaugegap.quantum.pauli_export import z2_plaquette_sparse_pauli
from gaugegap.providers import get_provider
from gaugegap.workflows import run_emulator_to_hardware


def main():
    parser = argparse.ArgumentParser(
        description="Run GaugeGap Z2 plaquette on Quantinuum"
    )
    parser.add_argument(
        "--backend",
        default="H2-1E",
        choices=["H2-1E", "H2-1", "Helios"],
        help="Quantinuum backend name"
    )
    parser.add_argument(
        "--n-plaquettes",
        type=int,
        default=2,
        help="Number of plaquettes in chain"
    )
    parser.add_argument(
        "--coupling",
        type=float,
        default=1.0,
        help="Plaquette coupling strength J"
    )
    parser.add_argument(
        "--field",
        type=float,
        default=0.2,
        help="Transverse field strength h"
    )
    parser.add_argument(
        "--shots",
        type=int,
        default=1024,
        help="Number of measurement shots"
    )
    parser.add_argument(
        "--hardware",
        action="store_true",
        help="Submit to hardware (requires QUANTINUUM_API_KEY)"
    )
    parser.add_argument(
        "--emulator-only",
        action="store_true",
        help="Run emulator only, skip hardware"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/quantinuum"),
        help="Output directory for results"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.hardware and args.emulator_only:
        parser.error("Cannot specify both --hardware and --emulator-only")
    
    if args.backend == "H2-1E" and args.hardware:
        parser.error("H2-1E is an emulator, cannot use --hardware flag")
    
    print(f"GaugeGap Z2 Plaquette on Quantinuum {args.backend}")
    print(f"Parameters: n_plaquettes={args.n_plaquettes}, J={args.coupling}, h={args.field}")
    print()
    
    # Step 1: Compute classical baseline
    print("Step 1: Computing classical baseline...")
    layout = open_plaquette_chain_layout(args.n_plaquettes)
    J, h = validate_parameters(args.coupling, args.field)
    
    H_dense = hamiltonian_dense(args.n_plaquettes, J, h)
    gap_result = exact_gap(H_dense)
    
    E0 = gap_result.ground_energy
    E1 = gap_result.first_excited_energy
    gap = gap_result.gap
    
    classical_result = {
        "energy_0": float(E0),
        "energy_1": float(E1),
        "gap": float(gap),
        "n_plaquettes": args.n_plaquettes,
        "coupling": args.coupling,
        "field": args.field
    }
    
    print(f"  E0 = {E0:.6f}")
    print(f"  E1 = {E1:.6f}")
    print(f"  Gap = {gap:.6f}")
    print()
    
    # Step 2: Convert to Quantinuum circuit
    print("Step 2: Converting to Quantinuum circuit...")
    try:
        from gaugegap.providers.quantinuum_adapter import QuantinuumProvider
        
        # Build Qiskit SparsePauliOp first
        pauli_op = z2_plaquette_sparse_pauli(args.n_plaquettes, J, h)
        
        # Create simple VQE-style ansatz circuit
        try:
            from qiskit import QuantumCircuit
            
            n_qubits = layout.n_links
            qc = QuantumCircuit(n_qubits)
            
            # Hardware-efficient ansatz
            for i in range(n_qubits):
                qc.ry(0.1, i)
            for i in range(n_qubits - 1):
                qc.cx(i, i + 1)
            
            qc.measure_all()
            
            # Convert to pytket
            circuit = QuantinuumProvider.convert_from_qiskit(qc)
            
            print(f"  Circuit: {circuit.n_qubits} qubits, depth {circuit.depth()}")
            print()
            
        except ImportError as e:
            print(f"  Error: {e}")
            print("  Install qiskit: pip install 'qiskit>=1.4'")
            return 1
        
    except ImportError as e:
        print(f"  Error: {e}")
        print("  Install pytket-quantinuum: pip install pytket-quantinuum pytket-qiskit")
        return 1
    
    # Step 3: Create provider and run workflow
    print("Step 3: Creating Quantinuum provider...")
    try:
        provider = get_provider("quantinuum", args.backend)
        
        if not args.emulator_only and not provider.check_credentials():
            print("  Warning: No Quantinuum credentials found")
            print("  Set QUANTINUUM_API_KEY environment variable for hardware access")
            print("  Continuing with emulator only...")
            args.hardware = False
        
        print(f"  Provider: {provider.__class__.__name__}")
        print(f"  Backend: {args.backend}")
        print()
        
    except Exception as e:
        print(f"  Error creating provider: {e}")
        return 1
    
    # Step 4: Run emulator-to-hardware workflow
    print("Step 4: Running emulator-to-hardware workflow...")
    print(f"  Hardware submission: {'enabled' if args.hardware else 'disabled'}")
    print()
    
    try:
        result = run_emulator_to_hardware(
            provider=provider,
            hypothesis_id="gaugegap-0002",
            circuit=circuit,
            classical_result=classical_result,
            shots=args.shots,
            noise_model="realistic",
            hardware=args.hardware and not args.emulator_only,
            output_dir=args.output_dir
        )
        
        print()
        print("Workflow complete!")
        print(f"  Status: {result.workflow_status}")
        print(f"  Emulator validated: {result.emulator_validated}")
        
        if result.hardware_result and result.hardware_job_metadata:
            print(f"  Hardware job ID: {result.hardware_job_metadata.get('job_id', 'N/A')}")
        
        if result.error_message:
            print(f"  Error: {result.error_message}")
        
        print()
        print(f"Results saved to: {args.output_dir}")
        
        return 0 if result.workflow_status in ["complete", "emulator_only"] else 1
        
    except Exception as e:
        print(f"  Workflow error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
