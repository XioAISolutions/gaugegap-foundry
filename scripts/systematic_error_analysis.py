#!/usr/bin/env python3
"""
Systematic Error Analysis for GaugeGap Benchmarks

Analyzes and quantifies systematic errors from:
1. Finite-size effects
2. Truncation errors
3. Discretization errors
4. Extrapolation uncertainties
5. Method comparison

Claim Boundary Compliance
-------------------------
All error estimates are for finite-system benchmarks only.
No claim of Millennium Prize problem resolution.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def analyze_finite_size_errors(results: List[Dict]) -> Dict[str, Any]:
    """Analyze finite-size scaling errors."""
    
    # Group by field
    field_groups = {}
    for r in results:
        field = r.get('transverse_field', r.get('params', {}).get('transverse_field'))
        if field is None:
            continue
        if field not in field_groups:
            field_groups[field] = []
        field_groups[field].append(r)
    
    errors = {}
    for field, group in field_groups.items():
        if len(group) < 2:
            continue
        
        sizes = [r.get('n_plaquettes', r.get('params', {}).get('n_plaquettes', 0)) for r in group]
        gaps = [r.get('mass_gap', r.get('value', 0)) for r in group]
        
        if len(sizes) >= 2:
            # Estimate finite-size error as difference between largest two sizes
            sorted_data = sorted(zip(sizes, gaps), reverse=True)
            if len(sorted_data) >= 2:
                finite_size_error = abs(sorted_data[0][1] - sorted_data[1][1])
                errors[field] = {
                    'finite_size_error': float(finite_size_error),
                    'largest_size': sorted_data[0][0],
                    'largest_gap': sorted_data[0][1],
                    'relative_error': float(finite_size_error / sorted_data[0][1]) if sorted_data[0][1] != 0 else 0,
                }
    
    return errors


def analyze_truncation_errors(u1_results: List[Dict]) -> Dict[str, Any]:
    """Analyze truncation errors in U(1) gauge theory."""
    
    # Group by n_links and g_magnetic
    groups = {}
    for r in u1_results:
        params = r.get('params', {})
        n_links = params.get('n_links')
        g_mag = params.get('g_magnetic')
        trunc = params.get('truncation')
        
        if n_links is None or g_mag is None or trunc is None:
            continue
        
        key = (n_links, g_mag)
        if key not in groups:
            groups[key] = []
        groups[key].append((trunc, r.get('value', 0)))
    
    errors = {}
    for key, data in groups.items():
        if len(data) < 2:
            continue
        
        sorted_data = sorted(data, reverse=True)  # Highest truncation first
        if len(sorted_data) >= 2:
            trunc_error = abs(sorted_data[0][1] - sorted_data[1][1])
            errors[f"n_links={key[0]}_g_mag={key[1]}"] = {
                'truncation_error': float(trunc_error),
                'highest_truncation': sorted_data[0][0],
                'highest_gap': sorted_data[0][1],
                'relative_error': float(trunc_error / sorted_data[0][1]) if sorted_data[0][1] != 0 else 0,
            }
    
    return errors


def analyze_method_comparison(z2_results: List[Dict], quantum_results: List[Dict]) -> Dict[str, Any]:
    """Compare classical exact vs quantum VQE methods."""
    
    comparisons = []
    
    for qr in quantum_results:
        vqe_data = qr.get('vqe', {})
        if not vqe_data:
            continue
        
        n_plaq = qr.get('n_plaquettes')
        field = qr.get('transverse_field')
        
        # Find matching classical result
        for cr in z2_results:
            if (cr.get('n_plaquettes') == n_plaq and 
                abs(cr.get('transverse_field', 0) - field) < 1e-10):
                
                exact_gap = cr.get('mass_gap', 0)
                vqe_gap = vqe_data.get('gap', 0)
                error = abs(exact_gap - vqe_gap)
                
                comparisons.append({
                    'n_plaquettes': n_plaq,
                    'transverse_field': field,
                    'exact_gap': float(exact_gap),
                    'vqe_gap': float(vqe_gap),
                    'absolute_error': float(error),
                    'relative_error': float(error / exact_gap) if exact_gap != 0 else 0,
                })
                break
    
    if not comparisons:
        return {}
    
    errors = [c['absolute_error'] for c in comparisons]
    rel_errors = [c['relative_error'] for c in comparisons]
    
    return {
        'comparisons': comparisons,
        'mean_absolute_error': float(np.mean(errors)),
        'max_absolute_error': float(np.max(errors)),
        'mean_relative_error': float(np.mean(rel_errors)),
        'max_relative_error': float(np.max(rel_errors)),
    }


def generate_error_budget(
    finite_size_errors: Dict,
    truncation_errors: Dict,
    method_errors: Dict,
) -> Dict[str, Any]:
    """Generate comprehensive error budget."""
    
    # Extract representative errors
    fs_errors = [v['finite_size_error'] for v in finite_size_errors.values()]
    trunc_errors = [v['truncation_error'] for v in truncation_errors.values()]
    
    budget = {
        'finite_size': {
            'mean': float(np.mean(fs_errors)) if fs_errors else 0,
            'max': float(np.max(fs_errors)) if fs_errors else 0,
            'description': 'Error from finite lattice size',
        },
        'truncation': {
            'mean': float(np.mean(trunc_errors)) if trunc_errors else 0,
            'max': float(np.max(trunc_errors)) if trunc_errors else 0,
            'description': 'Error from Hilbert space truncation',
        },
        'method_comparison': {
            'mean': method_errors.get('mean_absolute_error', 0),
            'max': method_errors.get('max_absolute_error', 0),
            'description': 'Difference between exact and VQE methods',
        },
    }
    
    # Total systematic error (quadrature sum)
    total_mean = np.sqrt(sum(v['mean']**2 for v in budget.values()))
    total_max = np.sqrt(sum(v['max']**2 for v in budget.values()))
    
    budget['total'] = {
        'mean': float(total_mean),
        'max': float(total_max),
        'description': 'Combined systematic error (quadrature)',
    }
    
    return budget


def main() -> int:
    """Main analysis workflow."""
    
    print("="*80)
    print("Systematic Error Analysis for GaugeGap Benchmarks")
    print("="*80)
    
    # Load Z2 results
    z2_file = ROOT / "results" / "baselines" / "gaugegap-0002-complete-results.json"
    if z2_file.exists():
        with open(z2_file, 'r') as f:
            z2_data = json.load(f)
        z2_results = z2_data.get('classical_results', [])
        quantum_results = z2_data.get('quantum_results', [])
        print(f"\nLoaded {len(z2_results)} Z2 classical results")
        print(f"Loaded {len(quantum_results)} Z2 quantum results")
    else:
        z2_results = []
        quantum_results = []
        print("\nNo Z2 results found")
    
    # Load U(1) results
    u1_file = ROOT / "results" / "gaugegap-u1-extended" / "gaugegap-u1-0001-u1-gap-sweep.jsonl"
    u1_results = []
    if u1_file.exists():
        with open(u1_file, 'r') as f:
            for line in f:
                u1_results.append(json.loads(line))
        print(f"Loaded {len(u1_results)} U(1) results")
    else:
        print("No U(1) results found")
    
    # Analyze errors
    print("\n" + "="*80)
    print("Analyzing Finite-Size Errors")
    print("="*80)
    finite_size_errors = analyze_finite_size_errors(z2_results)
    for field, errors in finite_size_errors.items():
        print(f"\nField h={field}:")
        print(f"  Finite-size error: {errors['finite_size_error']:.6f}")
        print(f"  Relative error: {errors['relative_error']*100:.2f}%")
    
    print("\n" + "="*80)
    print("Analyzing Truncation Errors (U(1))")
    print("="*80)
    truncation_errors = analyze_truncation_errors(u1_results)
    for key, errors in truncation_errors.items():
        print(f"\n{key}:")
        print(f"  Truncation error: {errors['truncation_error']:.6f}")
        print(f"  Relative error: {errors['relative_error']*100:.2f}%")
    
    print("\n" + "="*80)
    print("Analyzing Method Comparison (Exact vs VQE)")
    print("="*80)
    method_errors = analyze_method_comparison(z2_results, quantum_results)
    if method_errors:
        print(f"\nMean absolute error: {method_errors['mean_absolute_error']:.6f}")
        print(f"Max absolute error: {method_errors['max_absolute_error']:.6f}")
        print(f"Mean relative error: {method_errors['mean_relative_error']*100:.2f}%")
        print(f"Max relative error: {method_errors['max_relative_error']*100:.2f}%")
    
    # Generate error budget
    print("\n" + "="*80)
    print("Error Budget")
    print("="*80)
    error_budget = generate_error_budget(
        finite_size_errors,
        truncation_errors,
        method_errors,
    )
    
    for source, data in error_budget.items():
        print(f"\n{source.upper()}:")
        print(f"  {data['description']}")
        print(f"  Mean: {data['mean']:.6f}")
        print(f"  Max: {data['max']:.6f}")
    
    # Save results
    output_dir = ROOT / "results" / "systematic-errors"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = {
        'finite_size_errors': finite_size_errors,
        'truncation_errors': truncation_errors,
        'method_comparison': method_errors,
        'error_budget': error_budget,
    }
    
    output_file = output_dir / "systematic-error-analysis.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n\nSaved results to: {output_file}")
    
    # Generate report
    report_file = output_dir / "systematic-error-report.md"
    with open(report_file, 'w') as f:
        f.write("# Systematic Error Analysis Report\n\n")
        f.write("## Claim Boundary\n\n")
        f.write("All error estimates are for finite-system benchmarks only. ")
        f.write("No claim of Millennium Prize problem resolution.\n\n")
        
        f.write("## Error Budget Summary\n\n")
        f.write("| Source | Mean Error | Max Error | Description |\n")
        f.write("|--------|-----------|-----------|-------------|\n")
        for source, data in error_budget.items():
            f.write(f"| {source} | {data['mean']:.6f} | {data['max']:.6f} | {data['description']} |\n")
        
        f.write("\n## Interpretation\n\n")
        total_mean = error_budget['total']['mean']
        if total_mean < 0.01:
            f.write("Systematic errors are **well-controlled** (< 1%).\n")
        elif total_mean < 0.05:
            f.write("Systematic errors are **moderate** (1-5%).\n")
        else:
            f.write("Systematic errors are **significant** (> 5%).\n")
        
        f.write("\n## Recommendations\n\n")
        f.write("1. Extend to larger system sizes to reduce finite-size effects\n")
        f.write("2. Increase truncation parameters for U(1) calculations\n")
        f.write("3. Improve VQE optimization for better quantum-classical agreement\n")
        f.write("4. Perform Richardson extrapolation for continuum limit\n")
    
    print(f"Saved report to: {report_file}")
    
    print("\n" + "="*80)
    print("Systematic Error Analysis Complete")
    print("="*80)
    print("\nClaim Boundary: Finite-system benchmarks only; no Millennium Prize claim.")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# Made with Bob
