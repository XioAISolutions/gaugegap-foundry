from fractions import Fraction

from gaugegap.verified_su2_gap import (
    GaugeInvariantBasis,
    casimir,
    direct_matrix_exact,
    fusion_matrix_exact,
    isolate_eigenvalue,
    sturm_count_less_than,
    tridiagonal_parts,
    verify_gap,
)


def test_gauge_invariant_character_basis():
    basis = GaugeInvariantBasis(max_two_j=3)
    assert basis.dimension == 4
    assert basis.j_values == (
        Fraction(0),
        Fraction(1, 2),
        Fraction(1),
        Fraction(3, 2),
    )
    assert basis.gauss_law_residual == 0
    assert casimir(1) == Fraction(3, 4)
    assert casimir(2) == 2


def test_direct_and_fusion_constructions_match_exactly():
    basis = GaugeInvariantBasis(max_two_j=4)
    direct = direct_matrix_exact(basis, electric=Fraction(3, 2), magnetic=Fraction(2, 5))
    fusion = fusion_matrix_exact(basis, electric=Fraction(3, 2), magnetic=Fraction(2, 5))
    assert direct == fusion


def test_known_two_by_two_case_has_exact_gap_five_quarters():
    result = verify_gap(
        max_two_j=1,
        electric=Fraction(1),
        magnetic=Fraction(1, 2),
        sturm_bits=96,
    )
    assert result.ground.contains(Fraction(-1, 4))
    assert result.first_excited.contains(Fraction(1))
    assert result.gap.contains(Fraction(5, 4))
    assert result.gap.lower > 0
    assert result.strictly_positive
    assert result.construction_residual == 0.0
    assert result.spectrum_residual == 0.0


def test_sturm_counts_ordered_eigenvalues_in_known_case():
    matrix = direct_matrix_exact(GaugeInvariantBasis(1))
    diagonal, off_diagonal = tridiagonal_parts(matrix)
    assert sturm_count_less_than(diagonal, off_diagonal, Fraction(-1)) == 0
    assert sturm_count_less_than(diagonal, off_diagonal, Fraction(0)) == 1
    assert sturm_count_less_than(diagonal, off_diagonal, Fraction(2)) == 2
    ground = isolate_eigenvalue(diagonal, off_diagonal, 0, bits=80)
    excited = isolate_eigenvalue(diagonal, off_diagonal, 1, bits=80)
    assert ground.contains(Fraction(-1, 4))
    assert excited.contains(Fraction(1))


def test_larger_truncations_produce_positive_certified_finite_gaps():
    for max_two_j in (1, 2, 3, 4):
        result = verify_gap(max_two_j=max_two_j, electric=1, magnetic=Fraction(1, 2), sturm_bits=72)
        assert result.strictly_positive
        assert result.gap.width < Fraction(1, 10**12)
        assert "continuum" in result.summary()["claim_boundary"]
