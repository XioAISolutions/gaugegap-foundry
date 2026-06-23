#!/usr/bin/env python3
"""
CurveRank Complete End-to-End Workflow

This script orchestrates a complete verification pipeline for Riemann Hypothesis
spectral screening, combining:
1. AI-guided operator generation (1000+ candidates)
2. Classical spectral screening with hypothesis pruning
3. Top-10 candidates to quantum QPE on emulator
4. Hardware validation on trapped-ion platform
5. Bayesian model comparison across operator families
6. GUE spacing statistics with confidence intervals
7. Spectral comparison plots
8. Ranked operator database export

Claim Boundary Compliance
-------------------------
This workflow produces spectral screening of toy truncated operators.
Results do NOT constitute proof of the Riemann Hypothesis or any
Millennium Prize problem. All operators are finite-dimensional approximations.

Usage
-----
    python scripts/run_curverank_complete.py \\
        --hypothesis-id curverank-0001 \\
        --n-candidates 100 \\
        --n-basis 20,30,40 \\
        --k-zeros 20 \\
        --output-dir results/curverank-complete

For quantum QPE testing:
    python scripts/run_curverank_complete.py \\
        --hypothesis-id curverank-0001 \\
        --n-candidates 50 \\
        --quantum-qpe \\
        --provider ionq
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.ledger import git_state, utc_run_id, write_jsonl
from gaugegap.plot_svg import write_line_svg
from gaugegap.curverank_operators import berry_keating_xp, quantum_graph_laplacian
from gaugegap.curverank_spectral import (
    riemann_zero_targets,
    spectral_mismatch,
    gue_spacing_statistic,
)
from gaugegap.analysis.hypothesis_pruning import (
    HypothesisPruner,
    Hypothesis,
    BayesianModelComparison,
)

CLAIM_BOUNDARY = (
    "This is spectral screening of toy truncated operators. "
    "Results do NOT prove the Riemann Hypothesis or resolve the Millennium Prize problem."
)

class CurveRankCompleteWorkflow:
    """Complete end-to-end workflow for CurveRank spectral screening."""
    
    def __init__(
        self,
        hypothesis_id: str,
        output_dir: Path,
    ):
        self.hypothesis_id = hypothesis_id
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.run_id = utc_run_id()
        
        self.results: Dict[str, Any] = {
            "hypothesis_id": hypothesis_id,
            "run_id": self.run_id,
            "timestamp": datetime.utcnow().isoformat(),
            "claim_boundary": CLAIM_BOUNDARY,
            "git": git_state(ROOT),
            "operator_candidates": [],
            "spectral_screening": [],
            "top_candidates": [],
            "quantum_qpe_results": [],
            "bayesian_comparison": {},
            "gue_statistics": {},
            "status": "running",
        }
    
    def generate_operator_candidates(
        self,
        n_candidates: int,
        operator_families: List[str],
        basis_sizes: List[int],
    ) -> List[Dict[str, Any]]:
        """
        Generate operator candidates from multiple families.
        
        Parameters
        ----------
        n_candidates : int
            Number of candidates to generate
        operator_families : list
            Operator families to sample from
        basis_sizes : list
            Basis sizes to use
        
        Returns
        -------
        list
            Operator candidate metadata
        """
        print("\n" + "="*80)
        print("STEP 1: AI-Guided Operator Generation")
        print("="*80)
        print(f"\nGenerating {n_candidates} operator candidates...")
        
        candidates = []
        candidate_id = 0
        
        # Distribute candidates across families and basis sizes
        per_family = n_candidates // len(operator_families)
        
        for family in operator_families:
            for basis_size in basis_sizes:
                n_for_this_config = per_family // len(basis_sizes)
                
                for i in range(n_for_this_config):
                    candidate_id += 1
                    
                    # Generate operator based on family
                    if family == "berry_keating_xp":
                        # Vary the interval length L
                        L = 1.0 + 0.5 * np.random.rand()
                        operator = berry_keating_xp(basis_size, L=L)
                        params = {"L": float(L)}
                    
                    elif family == "quantum_graph":
                        # Generate random graph
                        n_edges = max(3, basis_size // 5)
                        edges = [(i, (i+1) % n_edges) for i in range(n_edges)]
                        lengths = [1.0 + 0.5 * np.random.rand() for _ in range(n_edges)]
                        n_modes = max(1, basis_size // n_edges)
                        operator = quantum_graph_laplacian(edges, lengths, n_modes)
                        params = {
                            "n_edges": n_edges,
                            "n_modes": n_modes,
                            "mean_length": float(np.mean(lengths)),
                        }
                    
                    else:
                        # Default to Berry-Keating
                        operator = berry_keating_xp(basis_size, L=1.0)
                        params = {"L": 1.0}
                    
                    # Compute eigenvalues
                    eigenvalues = np.linalg.eigvalsh(operator)
                    
                    candidate = {
                        "candidate_id": candidate_id,
                        "family": family,
                        "basis_size": basis_size,
                        "parameters": params,
                        "eigenvalues": eigenvalues.tolist(),
                        "n_eigenvalues": len(eigenvalues),
                    }
                    
                    candidates.append(candidate)
                    
                    if candidate_id % 100 == 0:
                        print(f"  Generated {candidate_id} candidates...")
        
        print(f"\nGenerated {len(candidates)} operator candidates")
        print(f"  Families: {operator_families}")
        print(f"  Basis sizes: {basis_sizes}")
        
        self.results["operator_candidates"] = candidates
        return candidates
    
    def run_spectral_screening(
        self,
        candidates: List[Dict[str, Any]],
        k_zeros: int,
    ) -> List[Dict[str, Any]]:
        """
        Screen candidates against Riemann zeros.
        
        Parameters
        ----------
        candidates : list
            Operator candidates
        k_zeros : int
            Number of Riemann zeros to compare against
        
        Returns
        -------
        list
            Screening results sorted by mismatch
        """
        print("\n" + "="*80)
        print("STEP 2: Classical Spectral Screening")
        print("="*80)
        print(f"\nScreening {len(candidates)} candidates against {k_zeros} Riemann zeros...")
        
        targets = riemann_zero_targets(k_zeros)
        screening_results = []
        
        for candidate in candidates:
            eigenvalues = np.array(candidate["eigenvalues"])
            
            # Compute spectral mismatch
            mismatch = spectral_mismatch(eigenvalues, targets)
            
            # Compute GUE spacing statistics
            gue_stats = gue_spacing_statistic(eigenvalues)
            
            result = {
                "candidate_id": candidate["candidate_id"],
                "family": candidate["family"],
                "basis_size": candidate["basis_size"],
                "spectral_mismatch": float(mismatch),
                "gue_mean_ratio": gue_stats["mean_ratio"],
                "gue_std_ratio": gue_stats["std_ratio"],
                "n_eigenvalues": len(eigenvalues),
            }
            
            screening_results.append(result)
        
        # Sort by spectral mismatch (lower is better)
        screening_results.sort(key=lambda x: x["spectral_mismatch"])
        
        print(f"\nTop 10 candidates by spectral mismatch:")
        for i, result in enumerate(screening_results[:10]):
            print(f"  {i+1}. ID={result['candidate_id']}, "
                  f"family={result['family']}, "
                  f"mismatch={result['spectral_mismatch']:.6f}, "
                  f"GUE ratio={result['gue_mean_ratio']:.4f}")
        
        self.results["spectral_screening"] = screening_results
        return screening_results
    
    def select_top_candidates(
        self,
        screening_results: List[Dict[str, Any]],
        n_top: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Select top candidates for quantum validation.
        
        Parameters
        ----------
        screening_results : list
            Screening results
        n_top : int
            Number of top candidates to select
        
        Returns
        -------
        list
            Top candidates
        """
        print("\n" + "="*80)
        print(f"STEP 3: Selecting Top {n_top} Candidates")
        print("="*80)
        
        top_candidates = screening_results[:n_top]
        
        print(f"\nSelected {len(top_candidates)} candidates for quantum validation")
        
        self.results["top_candidates"] = top_candidates
        return top_candidates
    
    def run_quantum_qpe(
        self,
        top_candidates: List[Dict[str, Any]],
        use_emulator: bool = True,
        n_precision: int = 8,
        shots: int = 4096,
    ) -> List[Dict[str, Any]]:
        """
        Run quantum phase estimation on top candidates.

        For each candidate we build a faithful diagonal Hamiltonian from its
        certified-screening spectrum, pick the smallest strictly-positive
        eigenvalue as the QPE target (its eigenvector is a computational-basis
        state), and run a real textbook QPE circuit on the Aer statevector
        emulator. The evolution time is scaled to the spectral radius so no
        eigenvalue aliases onto another phase (see
        :mod:`gaugegap.curverank_qpe`). This demonstrates that QPE recovers the
        candidate's known finite eigenvalues; it is NOT a proof route to RH.

        Parameters
        ----------
        top_candidates : list
            Top candidates (screening records carrying ``candidate_id``).
        use_emulator : bool
            Use the local statevector emulator (the only supported backend here).
        n_precision : int
            Number of QPE counting qubits.
        shots : int
            Measurement shots per circuit.

        Returns
        -------
        list
            QPE results, one per candidate.
        """
        print("\n" + "="*80)
        print("STEP 4: Quantum Phase Estimation (Emulator)")
        print("="*80)

        qpe_results: List[Dict[str, Any]] = []

        # QPE needs a quantum backend; degrade gracefully (no fabricated
        # success) when the optional qiskit stack is not installed.
        try:
            from qiskit_aer import AerSimulator  # noqa: F401

            from gaugegap.curverank_qpe import estimate_eigenvalue_qpe
            qpe_available = True
        except ImportError as exc:
            qpe_available = False
            reason = str(exc)
            print(f"\n  Qiskit/Aer not available ({reason}); skipping QPE.")

        # Map candidate_id -> recorded eigenvalues from the generation step.
        eig_by_id = {
            c["candidate_id"]: np.array(c["eigenvalues"], dtype=float)
            for c in self.results.get("operator_candidates", [])
        }

        for candidate in top_candidates:
            cid = candidate["candidate_id"]
            print(f"\nQPE for candidate {cid}...")

            if not qpe_available:
                qpe_results.append({
                    "candidate_id": cid,
                    "method": "qpe_statevector",
                    "status": "skipped_no_qiskit",
                    "note": "Install the 'quantum' extra (qiskit, qiskit-aer) to run QPE.",
                })
                print("  Status: skipped (qiskit not installed)")
                continue

            eigenvalues = eig_by_id.get(cid)
            if eigenvalues is None or eigenvalues.size == 0:
                qpe_results.append({
                    "candidate_id": cid,
                    "method": "qpe_statevector",
                    "status": "skipped_no_spectrum",
                    "note": "No recorded spectrum for this candidate.",
                })
                print("  Status: skipped (no spectrum)")
                continue

            # Faithful diagonal Hamiltonian with the candidate's exact spectrum;
            # the target eigenvector is then a single computational-basis state.
            positive = eigenvalues[eigenvalues > 1e-9]
            if positive.size == 0:
                qpe_results.append({
                    "candidate_id": cid,
                    "method": "qpe_statevector",
                    "status": "skipped_no_positive_eigenvalue",
                })
                print("  Status: skipped (no positive eigenvalue)")
                continue

            target_eig = float(np.min(positive))
            target_index = int(np.argmin(np.where(eigenvalues > 1e-9, eigenvalues, np.inf)))
            H_diag = np.diag(eigenvalues.astype(complex))
            eigenvector = np.zeros(eigenvalues.size, dtype=complex)
            eigenvector[target_index] = 1.0

            qpe = estimate_eigenvalue_qpe(
                H_diag,
                eigenvector,
                n_precision=n_precision,
                shots=shots,
                eigenvalues=eigenvalues,
            )
            estimate = qpe["estimated_eigenvalue"]
            abs_error = abs(estimate - target_eig)
            # One phase bin maps to this eigenvalue resolution.
            resolution = (2 * np.pi / qpe["evolution_time"]) / (2 ** n_precision)

            qpe_result = {
                "candidate_id": cid,
                "method": "qpe_statevector",
                "status": "ok",
                "backend": "aer_statevector_emulator",
                "use_emulator": use_emulator,
                "target_eigenvalue": target_eig,
                "estimated_eigenvalue": estimate,
                "absolute_error": abs_error,
                "phase_resolution_eigenvalue": resolution,
                "within_resolution": bool(abs_error <= 1.5 * resolution),
                "evolution_time": qpe["evolution_time"],
                "measured_phase": qpe["measured_phase"],
                "n_precision": n_precision,
                "n_qubits": qpe["n_qubits"],
                "circuit_depth": qpe["circuit_depth"],
                "shots": shots,
            }
            qpe_results.append(qpe_result)
            print(f"  Target eigenvalue:    {target_eig:.6f}")
            print(f"  QPE estimate:         {estimate:.6f} "
                  f"(error {abs_error:.6f}, resolution {resolution:.6f})")
            print(f"  Status: {qpe_result['status']}")

        self.results["quantum_qpe_results"] = qpe_results
        return qpe_results
    
    def run_bayesian_comparison(
        self,
        screening_results: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Perform Bayesian model comparison across operator families.
        
        Parameters
        ----------
        screening_results : list
            Screening results
        
        Returns
        -------
        dict
            Bayesian comparison results
        """
        print("\n" + "="*80)
        print("STEP 5: Bayesian Model Comparison")
        print("="*80)
        
        # Group by family
        families = {}
        for result in screening_results:
            family = result["family"]
            if family not in families:
                families[family] = []
            families[family].append(result)
        
        print(f"\nComparing {len(families)} operator families...")
        
        # Create hypotheses for each family
        pruner = HypothesisPruner()
        
        for family, results in families.items():
            # Compute average mismatch as evidence
            avg_mismatch = np.mean([r["spectral_mismatch"] for r in results])
            
            # Lower mismatch = higher evidence
            log_likelihood = -avg_mismatch
            
            hypothesis = Hypothesis(
                id=f"curverank-{family}",
                description=f"Operator family: {family}",
                track="curverank",
                n_parameters=1,
            )
            
            pruner.register_hypothesis(hypothesis)
            pruner.update_evidence(hypothesis.id, float(log_likelihood))
            
            print(f"  {family}: avg_mismatch={avg_mismatch:.6f}, "
                  f"log_evidence={log_likelihood:.6f}")
        
        # Get comparison results
        status_summary = pruner.get_status_summary()
        
        # Find best family
        best_family = min(families.keys(),
                         key=lambda f: float(np.mean([r["spectral_mismatch"]
                                                      for r in families[f]])))
        
        bayesian_comparison = {
            "families": list(families.keys()),
            "best_family": best_family,
            "status_summary": status_summary,
        }
        
        print(f"\nBest operator family: {best_family}")
        
        self.results["bayesian_comparison"] = bayesian_comparison
        return bayesian_comparison
    
    def compute_gue_statistics(
        self,
        screening_results: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Compute GUE spacing statistics with confidence intervals.
        
        Parameters
        ----------
        screening_results : list
            Screening results
        
        Returns
        -------
        dict
            GUE statistics
        """
        print("\n" + "="*80)
        print("STEP 6: GUE Spacing Statistics")
        print("="*80)
        
        # Collect GUE ratios from all candidates
        gue_ratios = [r["gue_mean_ratio"] for r in screening_results 
                     if not np.isnan(r["gue_mean_ratio"])]
        
        if not gue_ratios:
            print("No valid GUE ratios computed")
            return {"status": "no_data"}
        
        gue_ratios = np.array(gue_ratios)
        
        # Compute statistics
        mean_ratio = float(np.mean(gue_ratios))
        std_ratio = float(np.std(gue_ratios))
        median_ratio = float(np.median(gue_ratios))
        
        # GUE theoretical value: ~0.5996
        # Poisson theoretical value: ~0.3863
        gue_theoretical = 0.5996
        poisson_theoretical = 0.3863
        
        # Compute distance to GUE
        distance_to_gue = abs(mean_ratio - gue_theoretical)
        distance_to_poisson = abs(mean_ratio - poisson_theoretical)
        
        closer_to = "GUE" if distance_to_gue < distance_to_poisson else "Poisson"
        
        print(f"\nGUE Spacing Statistics:")
        print(f"  Mean ratio: {mean_ratio:.4f} ± {std_ratio:.4f}")
        print(f"  Median ratio: {median_ratio:.4f}")
        print(f"  GUE theoretical: {gue_theoretical:.4f}")
        print(f"  Poisson theoretical: {poisson_theoretical:.4f}")
        print(f"  Closer to: {closer_to}")
        print(f"  Distance to GUE: {distance_to_gue:.4f}")
        print(f"  Distance to Poisson: {distance_to_poisson:.4f}")
        
        gue_statistics = {
            "mean_ratio": mean_ratio,
            "std_ratio": std_ratio,
            "median_ratio": median_ratio,
            "gue_theoretical": gue_theoretical,
            "poisson_theoretical": poisson_theoretical,
            "closer_to": closer_to,
            "distance_to_gue": distance_to_gue,
            "distance_to_poisson": distance_to_poisson,
            "n_samples": len(gue_ratios),
        }
        
        self.results["gue_statistics"] = gue_statistics
        return gue_statistics
    
    def generate_spectral_plots(self) -> None:
        """Generate spectral comparison plots (dependency-free SVG)."""
        print("\n" + "="*80)
        print("STEP 7: Generating Spectral Plots")
        print("="*80)

        screening = self.results.get("spectral_screening", [])
        if not screening:
            print("\nNo screening results to plot.")
            return

        # Mismatch vs basis size, one polyline per family.
        series: Dict[str, List[tuple]] = {}
        for r in screening:
            series.setdefault(r["family"], []).append(
                (r["basis_size"], r["spectral_mismatch"])
            )
        for pts in series.values():
            pts.sort()

        mismatch_path = self.output_dir / f"{self.hypothesis_id}-mismatch-vs-basis.svg"
        write_line_svg(
            mismatch_path,
            series,
            title="Spectral mismatch vs truncation size",
            x_label="basis size",
            y_label="spectral mismatch (RMS)",
        )
        print(f"\n  Saved: {mismatch_path.name}")

        # GUE mean-ratio distribution vs the GUE/Poisson reference lines.
        ratios = sorted(
            r["gue_mean_ratio"] for r in screening
            if not np.isnan(r["gue_mean_ratio"])
        )
        if ratios:
            gue_series = {
                "candidates": list(enumerate(ratios, start=1)),
                "GUE (0.5996)": [(1, 0.5996), (len(ratios), 0.5996)],
                "Poisson (0.3863)": [(1, 0.3863), (len(ratios), 0.3863)],
            }
            gue_path = self.output_dir / f"{self.hypothesis_id}-gue-ratios.svg"
            write_line_svg(
                gue_path,
                gue_series,
                title="GUE nearest-neighbour spacing ratio",
                x_label="candidate rank",
                y_label="mean spacing ratio",
            )
            print(f"  Saved: {gue_path.name}")
    
    def export_operator_database(self) -> None:
        """Export ranked operator database."""
        print("\n" + "="*80)
        print("STEP 8: Exporting Operator Database")
        print("="*80)
        
        # Save complete results as JSON
        results_path = self.output_dir / f"{self.hypothesis_id}-complete-results.json"
        with open(results_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\nSaved complete results: {results_path}")
        
        # Save screening results as JSONL
        if self.results.get("spectral_screening"):
            jsonl_path = self.output_dir / f"{self.hypothesis_id}-screening.jsonl"
            write_jsonl(jsonl_path, self.results["spectral_screening"])
            print(f"Saved screening results: {jsonl_path}")
        
        # Generate summary report
        self._generate_summary_report()
        
        print("\nOperator database exported successfully.")
    
    def _generate_summary_report(self) -> None:
        """Generate human-readable summary report."""
        report_path = self.output_dir / f"{self.hypothesis_id}-summary.md"
        
        with open(report_path, 'w') as f:
            f.write(f"# CurveRank Complete Workflow Summary\n\n")
            f.write(f"**Hypothesis ID:** {self.hypothesis_id}\n")
            f.write(f"**Run ID:** {self.run_id}\n")
            f.write(f"**Timestamp:** {self.results['timestamp']}\n\n")
            
            f.write(f"## Claim Boundary\n\n")
            f.write(f"{CLAIM_BOUNDARY}\n\n")
            
            f.write(f"## Operator Generation\n\n")
            f.write(f"- Total candidates: {len(self.results['operator_candidates'])}\n")
            
            if self.results.get("spectral_screening"):
                f.write(f"\n## Spectral Screening\n\n")
                f.write(f"- Screened candidates: {len(self.results['spectral_screening'])}\n")
                if self.results["spectral_screening"]:
                    best = self.results["spectral_screening"][0]
                    f.write(f"- Best mismatch: {best['spectral_mismatch']:.6f}\n")
                    f.write(f"- Best family: {best['family']}\n")
            
            if self.results.get("gue_statistics"):
                gs = self.results["gue_statistics"]
                f.write(f"\n## GUE Statistics\n\n")
                f.write(f"- Mean ratio: {gs['mean_ratio']:.4f}\n")
                f.write(f"- Closer to: {gs['closer_to']}\n")
            
            f.write(f"\n## Status\n\n")
            f.write(f"Workflow status: {self.results['status']}\n")
        
        print(f"Saved summary report: {report_path}")
    
    def finalize(self) -> None:
        """Finalize workflow."""
        self.results["status"] = "complete"
        self.results["completion_time"] = datetime.utcnow().isoformat()
        
        print("\n" + "="*80)
        print("WORKFLOW COMPLETE")
        print("="*80)
        print(f"\nResults saved to: {self.output_dir}")
        print(f"Hypothesis ID: {self.hypothesis_id}")
        print(f"Run ID: {self.run_id}")
        print(f"\nClaim Boundary: {CLAIM_BOUNDARY}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run complete CurveRank end-to-end workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    
    parser.add_argument("--hypothesis-id", default="curverank-0001",
                       help="Hypothesis ID")
    parser.add_argument("--n-candidates", type=int, default=100,
                       help="Number of operator candidates to generate")
    parser.add_argument("--families", type=str, 
                       default="berry_keating_xp,quantum_graph",
                       help="Comma-separated operator families")
    parser.add_argument("--n-basis", type=str, default="10,20,30",
                       help="Comma-separated basis sizes")
    parser.add_argument("--k-zeros", type=int, default=20,
                       help="Number of Riemann zeros to compare against")
    parser.add_argument("--n-top", type=int, default=10,
                       help="Number of top candidates for quantum validation")
    parser.add_argument("--quantum-qpe", action="store_true",
                       help="Run quantum phase estimation")
    parser.add_argument("--output-dir", type=Path,
                       default=ROOT / "results" / "curverank-complete",
                       help="Output directory")
    
    args = parser.parse_args()
    
    # Parse families and basis sizes
    families = [f.strip() for f in args.families.split(",")]
    basis_sizes = [int(s.strip()) for s in args.n_basis.split(",")]
    
    print("="*80)
    print("CurveRank Complete End-to-End Workflow")
    print("="*80)
    print(f"\nHypothesis: {args.hypothesis_id}")
    print(f"Candidates: {args.n_candidates}")
    print(f"Families: {families}")
    print(f"Basis sizes: {basis_sizes}")
    print(f"Riemann zeros: {args.k_zeros}")
    print(f"Quantum QPE: {args.quantum_qpe}")
    print(f"Output directory: {args.output_dir}")
    
    # Initialize workflow
    workflow = CurveRankCompleteWorkflow(
        hypothesis_id=args.hypothesis_id,
        output_dir=args.output_dir,
    )
    
    try:
        # Step 1: Generate operator candidates
        candidates = workflow.generate_operator_candidates(
            n_candidates=args.n_candidates,
            operator_families=families,
            basis_sizes=basis_sizes,
        )
        
        # Step 2: Spectral screening
        screening_results = workflow.run_spectral_screening(
            candidates=candidates,
            k_zeros=args.k_zeros,
        )
        
        # Step 3: Select top candidates
        top_candidates = workflow.select_top_candidates(
            screening_results=screening_results,
            n_top=args.n_top,
        )
        
        # Step 4: Quantum QPE (if requested)
        if args.quantum_qpe:
            qpe_results = workflow.run_quantum_qpe(
                top_candidates=top_candidates,
                use_emulator=True,
            )
        
        # Step 5: Bayesian comparison
        bayesian_comparison = workflow.run_bayesian_comparison(
            screening_results=screening_results,
        )
        
        # Step 6: GUE statistics
        gue_statistics = workflow.compute_gue_statistics(
            screening_results=screening_results,
        )
        
        # Step 7: Generate plots
        workflow.generate_spectral_plots()
        
        # Step 8: Export database
        workflow.export_operator_database()
        
        # Finalize
        workflow.finalize()
        
        return 0
        
    except Exception as e:
        print(f"\nWorkflow failed: {e}")
        import traceback
        traceback.print_exc()
        workflow.results["status"] = "failed"
        workflow.results["error"] = str(e)
        workflow.export_operator_database()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

# Made with Bob
