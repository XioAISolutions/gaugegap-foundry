#!/usr/bin/env python3
"""
Generate publication-quality figures from GaugeGap Foundry results.

This script creates high-resolution PDF figures suitable for academic publication,
including spectral mismatch scaling, operator comparisons, and proof visualizations.
"""

import argparse
import json
from pathlib import Path
import sys

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec

# Set publication-quality defaults
plt.rcParams.update({
    'font.size': 11,
    'font.family': 'serif',
    'font.serif': ['Computer Modern Roman'],
    'text.usetex': False,  # Set to True if LaTeX is available
    'figure.figsize': (8, 6),
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'axes.labelsize': 12,
    'axes.titlesize': 13,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'lines.linewidth': 1.5,
    'lines.markersize': 8,
})


def load_spectral_data(csv_file):
    """Load spectral screening data from CSV."""
    try:
        import pandas as pd
        return pd.read_csv(csv_file)
    except ImportError:
        # Fallback to numpy if pandas not available
        data = np.genfromtxt(csv_file, delimiter=',', names=True, dtype=None, encoding='utf-8')
        return data


def plot_spectral_mismatch_scaling(data, output_file, certified_bound=27.0):
    """
    Plot spectral mismatch M_n vs truncation size n with extrapolation.
    
    Args:
        data: DataFrame or structured array with 'n_basis' and 'mismatch' columns
        output_file: Path to save figure
        certified_bound: Certified lower bound for M_infinity
    """
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Extract data
    if hasattr(data, 'columns'):  # pandas DataFrame
        n_values = data['n_basis'].values
        mismatch_values = data['mismatch'].values
    else:  # numpy structured array
        n_values = data['n_basis']
        mismatch_values = data['mismatch']
    
    # Plot computed values
    ax.plot(n_values, mismatch_values, 'o-', color='#2E86AB', 
            linewidth=2, markersize=10, label='Computed $M_n$', zorder=3)
    
    # Add certified bound
    ax.axhline(certified_bound, color='#A23B72', linestyle='--', 
               linewidth=2, label=f'Certified bound $M_∞ ≥ {certified_bound}$', zorder=2)
    
    # Shade region below bound (impossible region)
    ax.fill_between([n_values[0], n_values[-1]], 0, certified_bound, 
                     alpha=0.1, color='#A23B72', label='Ruled out region')
    
    # Try power-law extrapolation if we have enough points
    if len(n_values) >= 3:
        try:
            # Fit M_n = a + b/n^c
            from scipy.optimize import curve_fit
            
            def power_law(n, a, b, c):
                return a + b / n**c
            
            popt, _ = curve_fit(power_law, n_values, mismatch_values, 
                               p0=[certified_bound, 100, 1], maxfev=10000)
            
            # Extrapolate
            n_extrap = np.linspace(n_values[0], n_values[-1] * 2, 100)
            m_extrap = power_law(n_extrap, *popt)
            
            ax.plot(n_extrap, m_extrap, ':', color='#2E86AB', 
                   linewidth=1.5, alpha=0.7, label=f'Extrapolation: $M_∞ ≈ {popt[0]:.1f}$')
            
            # Mark continuum limit
            ax.axhline(popt[0], color='#2E86AB', linestyle=':', 
                      linewidth=1, alpha=0.5)
        except:
            pass  # Skip extrapolation if fitting fails
    
    ax.set_xlabel('Truncation size $n$', fontsize=13)
    ax.set_ylabel('Spectral mismatch $M_n$', fontsize=13)
    ax.set_title('Berry–Keating Operator: Impossibility Proof', fontsize=14, fontweight='bold')
    ax.legend(loc='best', framealpha=0.95)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_xlim(left=n_values[0] - 1)
    ax.set_ylim(bottom=0)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()


def plot_proof_certificate_visual(cert_file, output_file):
    """
    Create visual representation of proof certificate.
    
    Args:
        cert_file: Path to proof_certificate.json
        output_file: Path to save figure
    """
    with open(cert_file, 'r') as f:
        cert = json.load(f)
    
    fig = plt.figure(figsize=(10, 8))
    gs = GridSpec(3, 2, figure=fig, hspace=0.4, wspace=0.3)
    
    # Title
    fig.suptitle('Computer-Assisted Impossibility Proof Certificate', 
                 fontsize=16, fontweight='bold', y=0.98)
    
    # Theorem statement (top, spanning both columns)
    ax_theorem = fig.add_subplot(gs[0, :])
    ax_theorem.axis('off')
    theorem_text = f"""
    THEOREM: {cert['theorem']['statement']}
    
    The {cert['theorem']['operator']} operator cannot match all Riemann zeros.
    Minimum observed mismatch: {cert['theorem']['min_observed_mismatch']:.2f}
    Certified lower bound: {cert['theorem']['certified_lower_bound']:.1f}
    """
    ax_theorem.text(0.5, 0.5, theorem_text, ha='center', va='center',
                   fontsize=12, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # Proof method (middle left)
    ax_method = fig.add_subplot(gs[1, 0])
    ax_method.axis('off')
    method_text = f"""
    PROOF METHOD
    
    Type: {cert['proof_method']['type'].replace('_', ' ').title()}
    Precision: {cert['proof_method']['precision'].replace('_', ' ')}
    Confidence: {cert['proof_method']['confidence_level'].replace('_', ' ')}
    """
    ax_method.text(0.1, 0.5, method_text, ha='left', va='center',
                  fontsize=10, family='monospace')
    
    # Data summary (middle right)
    ax_data = fig.add_subplot(gs[1, 1])
    ax_data.axis('off')
    data_text = f"""
    DATA SUMMARY
    
    Truncations tested: {cert['theorem']['truncations_tested']}
    Riemann zeros tested: {cert['theorem']['zeros_tested']}
    Run ID: {cert['data']['run_id']}
    Timestamp: {cert['data']['timestamp'][:19]}
    """
    ax_data.text(0.1, 0.5, data_text, ha='left', va='center',
                fontsize=10, family='monospace')
    
    # Claim boundary (bottom left)
    ax_boundary = fig.add_subplot(gs[2, 0])
    ax_boundary.axis('off')
    boundary_text = f"""
    CLAIM BOUNDARY
    
    Scope: {cert['claim_boundary']['scope'].replace('_', ' ').title()}
    
    ✓ Claims: {cert['claim_boundary']['claims'].replace('_', ' ')}
    
    ✗ Does NOT claim:
    """
    for claim in cert['claim_boundary']['does_not_claim']:
        boundary_text += f"\n  • {claim.replace('_', ' ')}"
    
    ax_boundary.text(0.1, 0.5, boundary_text, ha='left', va='center',
                    fontsize=9, family='monospace')
    
    # Reproducibility (bottom right)
    ax_repro = fig.add_subplot(gs[2, 1])
    ax_repro.axis('off')
    repro_text = f"""
    REPRODUCIBILITY
    
    Command:
    {cert['reproducibility']['command']}
    
    Repository:
    {cert['reproducibility']['repository']}
    
    Verified: {'✓ Yes' if cert['reproducibility']['verified'] else '✗ No'}
    """
    ax_repro.text(0.1, 0.5, repro_text, ha='left', va='center',
                 fontsize=9, family='monospace')
    
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()


def plot_operator_comparison(data, output_file):
    """
    Compare multiple operator families if data available.
    
    Args:
        data: DataFrame with 'operator_family' and 'mismatch' columns
        output_file: Path to save figure
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Extract unique operators
    if hasattr(data, 'columns'):  # pandas DataFrame
        if 'operator_family' in data.columns:
            operators = data['operator_family'].unique()
            for op in operators:
                op_data = data[data['operator_family'] == op]
                ax.plot(op_data['n_basis'], op_data['mismatch'], 
                       'o-', label=op, linewidth=2, markersize=8)
        else:
            # Single operator case
            ax.plot(data['n_basis'], data['mismatch'], 
                   'o-', label='Berry-Keating xp', linewidth=2, markersize=8)
    else:
        # numpy structured array - single operator
        ax.plot(data['n_basis'], data['mismatch'], 
               'o-', label='Berry-Keating xp', linewidth=2, markersize=8)
    
    ax.set_xlabel('Truncation size $n$', fontsize=13)
    ax.set_ylabel('Spectral mismatch $M_n$', fontsize=13)
    ax.set_title('Candidate Hilbert–Pólya Operators: Screening Results', 
                fontsize=14, fontweight='bold')
    ax.legend(loc='best', framealpha=0.95)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()


def main():
    parser = argparse.ArgumentParser(
        description='Generate publication-quality figures from GaugeGap Foundry results',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate all figures from sprint results
  python scripts/generate_publication_figures.py \\
      --input results/sprint-now/curverank-0001-spectral-screen.csv \\
      --certificate results/sprint-now/proof_certificate.json \\
      --output figures/

  # Generate only spectral mismatch plot
  python scripts/generate_publication_figures.py \\
      --input results/baselines/curverank-0001-spectral-screen.csv \\
      --output figures/ \\
      --plots mismatch
        """
    )
    
    parser.add_argument('--input', required=True, 
                       help='Input CSV file with spectral data')
    parser.add_argument('--certificate', 
                       help='Proof certificate JSON file (optional)')
    parser.add_argument('--output', default='figures/',
                       help='Output directory for figures (default: figures/)')
    parser.add_argument('--plots', nargs='+', 
                       choices=['mismatch', 'certificate', 'comparison', 'all'],
                       default=['all'],
                       help='Which plots to generate (default: all)')
    parser.add_argument('--certified-bound', type=float, default=27.0,
                       help='Certified lower bound for M_infinity (default: 27.0)')
    
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    print(f"Loading data from {args.input}...")
    try:
        data = load_spectral_data(args.input)
        print(f"✓ Loaded {len(data)} data points")
    except Exception as e:
        print(f"✗ Error loading data: {e}")
        return 1
    
    # Generate requested plots
    plots_to_generate = args.plots if 'all' not in args.plots else ['mismatch', 'certificate', 'comparison']
    
    if 'mismatch' in plots_to_generate:
        print("\nGenerating spectral mismatch scaling plot...")
        try:
            plot_spectral_mismatch_scaling(
                data, 
                output_dir / 'spectral_mismatch_scaling.pdf',
                args.certified_bound
            )
        except Exception as e:
            print(f"✗ Error: {e}")
    
    if 'certificate' in plots_to_generate and args.certificate:
        print("\nGenerating proof certificate visualization...")
        try:
            plot_proof_certificate_visual(
                args.certificate,
                output_dir / 'proof_certificate_visual.pdf'
            )
        except Exception as e:
            print(f"✗ Error: {e}")
    elif 'certificate' in plots_to_generate:
        print("⚠ Skipping certificate plot (no certificate file provided)")
    
    if 'comparison' in plots_to_generate:
        print("\nGenerating operator comparison plot...")
        try:
            plot_operator_comparison(
                data,
                output_dir / 'operator_comparison.pdf'
            )
        except Exception as e:
            print(f"✗ Error: {e}")
    
    print(f"\n✓ All figures saved to {output_dir}/")
    print("\nGenerated files:")
    for pdf_file in sorted(output_dir.glob('*.pdf')):
        print(f"  • {pdf_file}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

# Made with Bob
