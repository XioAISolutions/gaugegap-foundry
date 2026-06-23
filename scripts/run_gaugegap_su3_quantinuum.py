#!/usr/bin/env python3
"""
Run SU(3) Pure Gauge Theory on Quantinuum Hardware (gaugegap-0005)

This script demonstrates SU(3) gauge theory execution on Quantinuum H2/Helios,
representing the closest finite-system analog to Yang-Mills in this series.

Example usage:
    # Emulator only
    python scripts/run_gaugegap_su3_quantinuum.py --backend H2-1E --emulator-only
    
    # Full workflow with hardware
    export QUANTINUUM_API_KEY="your-api-key"
    python scripts/run_gaugegap_su3_quantinuum.py --backend H2-1 --hardware
"""

import argparse
from pathlib import Path
import sys
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gaugegap.gaugegap_su3_pure import (
    SU3PureGaugeConfig,
    SU3PureGaugeLattice,
)
from gaugegap.providers import get_provider
from gaugegap.workflows import run_emulator_to_hardware


def main():
    parser = argparse.ArgumentParser(
        description="Run SU(3) pure gauge theory on Quantinuum"
    )
    parser.add_argument(
        "--backend",
        default="H2-1E",
        choices=["H2-1E", "H2-1", "Helios"],
        help="Quantinuum backend name"
    )
    parser.add_argument(
        "--lattice-size",
        type=str,
        default="2x2",
        help="Lattice size (e.g., '2x2')"
    )
    parser.add_argument(
        "--coupling",
        type=float,
        default=1.0,
        help="Gauge coupling strength g"
    )
    parser.add_argument(
        "--truncation",
        type=float,
        default=0.5,
        help="Truncation parameter"
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
    
    # Parse lattice size
    parts = args.lattice_size.lower().split('x')
    if len(parts) != 2:
        parser.error(f"Invalid lattice size format: {args.lattice_size}")
    nx, ny = int(parts[0]), int(parts[1])
    
    print("=" * 70)
    print("SU(3) Pure Gauge Theory on Quantinuum (gaugegap-0005)")
    print("=" * 70)
    print(f"Backend: {args.backend}")
    print(f"Lattice: {nx}×{ny}")
    print(f"Coupling: g = {args.coupling}")
    print(f"Truncation: {args.truncation}")
    print(f"Shots: {args.shots}")
    print()
    print("NOTE: This is finite-lattice SU(3), NOT continuum Yang-Mills.")
    print("=" * 70)
    print()
    
    # Step 1: Compute classical baseline
    print("Step 1: Computing classical baseline...")
    
    # For SU(3), electric and magnetic couplings are related
    g_electric = args.coupling ** 2 / 2.0
    g_magnetic = 1.0 / (args.coupling ** 2)
    
    config = SU3PureGaugeConfig(
        nx=nx,
        ny=ny,
        g_electric=g_electric,
        g_magnetic=g_magnetic,
        truncation=args.truncation
    )
    
    lattice = SU3PureGaugeLattice(config)
    gap_result = lattice.compute_gap()
    
    if gap_result.get("gap") is None:
        print(f"  ERROR: {gap_result.get('error', 'Unknown error')}")
        print()
        print("Classical baseline failed. Cannot proceed to quantum hardware.")
        return 1
    
    E0 = gap_result["E0"]
    E1 = gap_result["E1"]
    gap = gap_result["gap"]
    
    classical_result = {
        "energy_0": float(E0),
        "energy_1": float(E1),
        "gap": float(gap),
        "nx": nx,
        "ny": ny,
        "coupling": args.coupling,
        "truncation": args.truncation,
        "hilbert_dim": gap_result.get("hilbert_dim"),
        "n_links": gap_result.get("n_links"),
        "n_plaquettes": gap_result.get("n_plaquettes")
    }
    
    print(f"  E0 = {E0:.6f}")
    print(f"  E1 = {E1:.6f}")
    print(f"  Gap = {gap:.6f}")
    print(f"  Hilbert dim = {gap_result.get('hilbert_dim')}")
    print()
    
    # Step 2: Check if quantum circuit compilation is available
    print("Step 2: Checking quantum circuit compilation...")
    try:
        from gaugegap.quantum.su3_circuit import (
            SU3CircuitConfig,
            SU3CircuitCompiler,
            SU3QuantumSimulator
        )
        
        # Create circuit configuration
        n_qubits = 2 * lattice.n_links  # 2 qubits per link
        circuit_config = SU3CircuitConfig(
            n_qubits=n_qubits,
            trotter_steps=1,
            ansatz_depth=2
        )
        
        # Create simulator
        lattice_config_dict = {
            'nx': nx,
            'ny': ny,
            'g_electric': g_electric,
            'g_magnetic': g_magnetic
        }
        
        simulator = SU3QuantumSimulator(lattice_config_dict, circuit_config)
        
        print(f"  Circuit qubits: {n_qubits}")
        print(f"  Trotter steps: {circuit_config.trotter_steps}")
        print(f"  Ansatz depth: {circuit_config.ansatz_depth}")
        print()
        
        # Prepare Hamiltonian terms
        electric_terms, magnetic_terms = simulator.prepare_hamiltonian_terms()
        print(f"  Electric terms: {len(electric_terms)}")
        print(f"  Magnetic terms: {len(magnetic_terms)}")
        print()
        
        circuit_available = True
        
    except ImportError as e:
        print(f"  Warning: Quantum circuit compilation not available: {e}")
        print("  Install qiskit: pip install 'qiskit>=1.4'")
        print()
        circuit_available = False
    
    # Step 3: Save results
    print("Step 3: Saving results...")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = args.output_dir / f"gaugegap-0005-su3-{nx}x{ny}-g{args.coupling:.2f}.json"
    
    result_data = {
        "hypothesis_id": "gaugegap-0005",
        "track": "GaugeGap",
        "model": "su3_qcd_like_2plus1d",
        "backend": args.backend,
        "classical_result": classical_result,
        "circuit_available": circuit_available,
        "hardware_submitted": False,
        "status": "classical_baseline_complete"
    }
    
    with open(output_file, 'w') as f:
        json.dump(result_data, f, indent=2)
    
    print(f"  Saved: {output_file}")
    print()
    
    # Step 4: Hardware submission (if requested and available)
    if args.hardware and not args.emulator_only:
        print("Step 4: Hardware submission...")
        
        if not circuit_available:
            print("  ERROR: Cannot submit to hardware without circuit compilation")
            print("  Install qiskit and retry")
            return 1
        
        print("  NOTE: Full hardware submission requires:")
        print("    1. Qiskit circuit compilation")
        print("    2. Provider credentials")
        print("    3. Hardware readiness verification")
        print()
        print("  This is a placeholder for future hardware integration.")
        # prototype scaffold; known limitation (hardware path is not implemented here)
        print("  Use existing provider adapters for actual submission.")
        print()
    
    print("=" * 70)
    print("SU(3) execution complete!")
    print()
    print("Next steps:")
    print("  1. Review classical baseline results")
    print("  2. Install qiskit for circuit compilation")
    print("  3. Use provider adapters for hardware submission")
    print("  4. Compare results across platforms")
    print("=" * 70)
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob