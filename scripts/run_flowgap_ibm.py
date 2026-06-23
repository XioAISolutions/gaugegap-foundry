#!/usr/bin/env python3
"""FlowGap IBM Runtime example: pressure-Poisson subroutine benchmark.

This script demonstrates the FlowGap hybrid quantum-classical workflow for
incompressible flow using IBM Qiskit Runtime. It implements a toy pressure-Poisson
solve within a projection method for a 2D cavity flow.

Workflow:
1. Classical intermediate velocity (u*) from momentum equation
2. Quantum pressure solve: ∇²p = ∇·u* / dt
3. Velocity projection: u^(n+1) = u* - dt∇p

This is a FINITE-SYSTEM BENCHMARK for reduced PDE subroutines, not a resolution
of 3D Navier-Stokes regularity.

Example usage:
    # Simulator only
    python scripts/run_flowgap_ibm.py --backend aer --nx 4 --ny 4 --shots 1024
    
    # With hardware (requires IBM credentials)
    python scripts/run_flowgap_ibm.py --backend ibm_brisbane --nx 4 --ny 4 --shots 2048 --use-runtime
    
    # With noise mitigation
    python scripts/run_flowgap_ibm.py --backend aer --noise depolarizing --resilience-level 2 --shots 1024
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gaugegap.providers import get_provider
from gaugegap.hardware_ready import verify_hardware_ready
from gaugegap.workflows.emulator_to_hardware import run_emulator_to_hardware
from gaugegap.cost_estimation import estimate_job_cost
from gaugegap.ledger import record_result


def build_poisson_matrix(nx: int, ny: int, dx: float = 1.0) -> np.ndarray:
    """Build 2D Poisson matrix with Dirichlet boundary conditions.
    
    Args:
        nx: Grid points in x
        ny: Grid points in y
        dx: Grid spacing
    
    Returns:
        Sparse Poisson matrix (nx*ny, nx*ny)
    """
    n = nx * ny
    A = np.zeros((n, n))
    
    for i in range(nx):
        for j in range(ny):
            idx = i * ny + j
            
            # Diagonal term
            A[idx, idx] = -4.0 / (dx * dx)
            
            # Off-diagonal terms (interior points only)
            if i > 0:  # left neighbor
                A[idx, idx - ny] = 1.0 / (dx * dx)
            if i < nx - 1:  # right neighbor
                A[idx, idx + ny] = 1.0 / (dx * dx)
            if j > 0:  # bottom neighbor
                A[idx, idx - 1] = 1.0 / (dx * dx)
            if j < ny - 1:  # top neighbor
                A[idx, idx + 1] = 1.0 / (dx * dx)
    
    return A


def classical_intermediate_velocity(
    u: np.ndarray,
    v: np.ndarray,
    dt: float,
    nu: float,
    nx: int,
    ny: int,
    dx: float = 1.0
) -> tuple[np.ndarray, np.ndarray]:
    """Compute intermediate velocity from momentum equation (simplified).
    
    This is a toy implementation for demonstration. Real CFD would use
    proper discretization schemes.
    
    Args:
        u: x-velocity field (nx, ny)
        v: y-velocity field (nx, ny)
        dt: Time step
        nu: Kinematic viscosity
        nx: Grid points in x
        ny: Grid points in y
        dx: Grid spacing
    
    Returns:
        (u_star, v_star): Intermediate velocity fields
    """
    # Simplified: just add viscous diffusion (prototype scaffold; known limitation)
    u_star = u.copy()
    v_star = v.copy()
    
    # Interior points only (toy Laplacian)
    for i in range(1, nx - 1):
        for j in range(1, ny - 1):
            laplacian_u = (
                u[i+1, j] + u[i-1, j] + u[i, j+1] + u[i, j-1] - 4*u[i, j]
            ) / (dx * dx)
            laplacian_v = (
                v[i+1, j] + v[i-1, j] + v[i, j+1] + v[i, j-1] - 4*v[i, j]
            ) / (dx * dx)
            
            u_star[i, j] = u[i, j] + dt * nu * laplacian_u
            v_star[i, j] = v[i, j] + dt * nu * laplacian_v
    
    return u_star, v_star


def compute_divergence(
    u: np.ndarray,
    v: np.ndarray,
    dx: float = 1.0
) -> np.ndarray:
    """Compute divergence of velocity field.
    
    Args:
        u: x-velocity (nx, ny)
        v: y-velocity (nx, ny)
        dx: Grid spacing
    
    Returns:
        Divergence field (nx, ny)
    """
    nx, ny = u.shape
    div = np.zeros((nx, ny))
    
    for i in range(1, nx - 1):
        for j in range(1, ny - 1):
            du_dx = (u[i+1, j] - u[i-1, j]) / (2 * dx)
            dv_dy = (v[i, j+1] - v[i, j-1]) / (2 * dx)
            div[i, j] = du_dx + dv_dy
    
    return div


def build_vqls_circuit(
    A: np.ndarray,
    b: np.ndarray,
    n_layers: int = 2
) -> QuantumCircuit:
    """Build variational quantum linear solver circuit.
    
    This is a toy VQLS ansatz for demonstration. Real implementation would
    use more sophisticated ansätze and optimization.
    
    Args:
        A: System matrix
        b: RHS vector
        n_layers: Ansatz depth
    
    Returns:
        Parameterized quantum circuit
    """
    n = len(b)
    n_qubits = int(np.ceil(np.log2(n)))
    
    qc = QuantumCircuit(n_qubits)
    
    # Initial state preparation (simplified; prototype scaffold, known limitation)
    for i in range(n_qubits):
        qc.h(i)
    
    # Variational layers
    for layer in range(n_layers):
        # Rotation layer
        for i in range(n_qubits):
            qc.ry(0.1 * (layer + 1), i)  # Placeholder parameters (prototype scaffold; known limitation)
            qc.rz(0.1 * (layer + 1), i)
        
        # Entangling layer
        for i in range(n_qubits - 1):
            qc.cx(i, i + 1)
        if n_qubits > 1:
            qc.cx(n_qubits - 1, 0)
    
    # Measurement
    qc.measure_all()
    
    return qc


def run_flowgap_benchmark(
    nx: int,
    ny: int,
    backend_name: str,
    shots: int,
    use_runtime: bool = False,
    noise_model: Optional[str] = None,
    resilience_level: int = 0,
    output_dir: Path = Path("results/flowgap")
) -> Dict[str, Any]:
    """Run FlowGap pressure-Poisson benchmark.
    
    Args:
        nx: Grid points in x
        ny: Grid points in y
        backend_name: IBM backend name
        shots: Number of shots
        use_runtime: Use Qiskit Runtime
        noise_model: Noise model (depolarizing, thermal, None)
        resilience_level: Runtime resilience level (0-2)
        output_dir: Output directory
    
    Returns:
        Results dictionary
    """
    print(f"\n{'='*60}")
    print("FlowGap IBM Runtime Benchmark")
    print(f"{'='*60}\n")
    
    # Problem setup
    dt = 0.01
    nu = 0.01
    dx = 1.0 / max(nx, ny)
    
    print(f"Grid: {nx}×{ny}")
    print(f"Time step: {dt}")
    print(f"Viscosity: {nu}")
    print(f"Backend: {backend_name}")
    print(f"Shots: {shots}")
    print(f"Runtime: {use_runtime}")
    print(f"Noise: {noise_model or 'None'}")
    print(f"Resilience: {resilience_level}\n")
    
    # Initialize velocity field (lid-driven cavity)
    u = np.zeros((nx, ny))
    v = np.zeros((nx, ny))
    u[:, -1] = 1.0  # Top lid moving
    
    # Step 1: Classical intermediate velocity
    print("Step 1: Computing intermediate velocity (classical)...")
    u_star, v_star = classical_intermediate_velocity(u, v, dt, nu, nx, ny, dx)
    
    # Step 2: Build pressure Poisson problem
    print("Step 2: Building pressure Poisson system...")
    A = build_poisson_matrix(nx, ny, dx)
    div = compute_divergence(u_star, v_star, dx)
    b = (div / dt).flatten()
    
    # Classical reference solution
    print("Step 3: Computing classical reference solution...")
    try:
        p_ref = np.linalg.solve(A, b).reshape(nx, ny)
        residual_ref = np.linalg.norm(A @ p_ref.flatten() - b)
        print(f"  Classical residual: {residual_ref:.6e}")
    except np.linalg.LinAlgError:
        print("  Warning: Classical solve failed (singular matrix)")
        p_ref = np.zeros((nx, ny))
        residual_ref = np.inf
    
    # Step 4: Build quantum circuit
    print("Step 4: Building quantum circuit...")
    n_points = nx * ny
    if n_points > 16:
        print(f"  Warning: {n_points} points requires {int(np.ceil(np.log2(n_points)))} qubits")
        print("  This is a toy demonstration; real VQLS would need optimization")
    
    qc = build_vqls_circuit(A, b, n_layers=2)
    print(f"  Circuit: {qc.num_qubits} qubits, depth {qc.depth()}")
    
    # Step 5: Cost estimation
    print("\nStep 5: Estimating cost...")
    if not backend_name.startswith("aer"):
        cost_est = estimate_job_cost(
            provider="ibm",
            backend=backend_name,
            n_circuits=1,
            shots_per_circuit=shots,
            use_runtime=use_runtime
        )
        print(f"  Estimated cost: ${cost_est.estimated_cost_usd:.2f} USD")
        print(f"  Confidence: {cost_est.confidence}")
        
        if cost_est.estimated_cost_usd > 10.0:
            response = input("\n  Cost exceeds $10. Continue? (y/n): ")
            if response.lower() != 'y':
                print("  Aborted by user.")
                return {}
    
    # Step 6: Run quantum job
    print("\nStep 6: Running quantum job...")
    try:
        provider = get_provider("ibm", backend_name=backend_name)
        
        if backend_name.startswith("aer"):
            # Simulator
            result_data, metadata = provider.submit_emulator(
                circuit=qc,
                shots=shots,
                noise_model=noise_model
            )
        else:
            # Hardware
            if not use_runtime:
                print("  Warning: Hardware access without Runtime may have limited features")
            
            result_data, metadata = provider.submit_hardware(
                circuit=qc,
                shots=shots
            )
        
        print(f"  Job completed: {metadata.job_id}")
        
    except Exception as e:
        print(f"  Error: {e}")
        return {}
    
    # Step 7: Extract and analyze results
    print("\nStep 7: Analyzing results...")
    
    # For this toy example, we would need to:
    # 1. Decode measurement outcomes to pressure field
    # 2. Compute residual and divergence
    # 3. Compare with classical solution
    
    # Placeholder metrics (prototype scaffold; known limitation)
    metrics = {
        "nx": nx,
        "ny": ny,
        "n_qubits": qc.num_qubits,
        "circuit_depth": qc.depth(),
        "shots": shots,
        "backend": backend_name,
        "use_runtime": use_runtime,
        "noise_model": noise_model,
        "resilience_level": resilience_level,
        "classical_residual": float(residual_ref),
        "job_id": metadata.job_id,
        "timestamp": datetime.now().isoformat()
    }
    
    # Step 8: Save results
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"flowgap-ibm-{nx}x{ny}-{backend_name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    
    with open(output_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")
    
    # Record in ledger
    record_result(
        hypothesis_id="flowgap-0001",
        result_type="quantum_benchmark",
        metrics=metrics,
        metadata={
            "track": "flowgap",
            "method": "ibm_runtime_vqls",
            "scope": "pressure_poisson_subroutine"
        }
    )
    
    print(f"\n{'='*60}")
    print("Benchmark complete")
    print(f"{'='*60}\n")
    
    return metrics


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="FlowGap IBM Runtime pressure-Poisson benchmark",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Aer simulator
  python scripts/run_flowgap_ibm.py --backend aer --nx 4 --ny 4 --shots 1024
  
  # With depolarizing noise
  python scripts/run_flowgap_ibm.py --backend aer --noise depolarizing --shots 1024
  
  # IBM hardware (requires credentials)
  python scripts/run_flowgap_ibm.py --backend ibm_brisbane --nx 4 --ny 4 --shots 2048 --use-runtime --resilience-level 2
        """
    )
    
    parser.add_argument(
        "--nx",
        type=int,
        default=4,
        help="Grid points in x (default: 4)"
    )
    parser.add_argument(
        "--ny",
        type=int,
        default=4,
        help="Grid points in y (default: 4)"
    )
    parser.add_argument(
        "--backend",
        type=str,
        default="aer",
        help="IBM backend name (default: aer)"
    )
    parser.add_argument(
        "--shots",
        type=int,
        default=1024,
        help="Number of shots (default: 1024)"
    )
    parser.add_argument(
        "--use-runtime",
        action="store_true",
        help="Use Qiskit Runtime (required for hardware)"
    )
    parser.add_argument(
        "--noise",
        type=str,
        choices=["depolarizing", "thermal", None],
        default=None,
        help="Noise model for Aer simulator"
    )
    parser.add_argument(
        "--resilience-level",
        type=int,
        choices=[0, 1, 2],
        default=0,
        help="Runtime resilience level (0=none, 1=light, 2=heavy)"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/flowgap"),
        help="Output directory (default: results/flowgap)"
    )
    
    args = parser.parse_args()
    
    # Validate grid size
    n_points = args.nx * args.ny
    n_qubits = int(np.ceil(np.log2(n_points)))
    
    if n_qubits > 10:
        print(f"Warning: {args.nx}×{args.ny} grid requires {n_qubits} qubits")
        print("This may be too large for current hardware. Consider smaller grid.")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return
    
    # Run benchmark
    try:
        results = run_flowgap_benchmark(
            nx=args.nx,
            ny=args.ny,
            backend_name=args.backend,
            shots=args.shots,
            use_runtime=args.use_runtime,
            noise_model=args.noise,
            resilience_level=args.resilience_level,
            output_dir=args.output_dir
        )
        
        if results:
            print("\n✓ Benchmark completed successfully")
        else:
            print("\n✗ Benchmark failed or was aborted")
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
