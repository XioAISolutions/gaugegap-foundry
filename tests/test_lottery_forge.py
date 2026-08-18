import copy
import pytest

from gaugegap.lottery_forge import (
    CLAIM_BOUNDARY, Draw, LotterySpec, analyse, anti_crowd_proxy,
    dmd_temporal_order_test, fibonacci_numbers, generate_synthetic_draws,
    make_proofpack, measured_popularity_penalty, pair_anomalies,
    rolling_backtest, search_candidates, subset_occurrence_test,
    temporal_order_test, validate_draws, verify_proofpack,
)

SPEC=LotterySpec()

def test_fibonacci_numbers_for_649():
    assert fibonacci_numbers(49)==(1,2,3,5,8,13,21,34)

def test_validation_rejects_duplicate_and_range():
    with pytest.raises(ValueError,match="duplicate"):
        validate_draws([Draw((1,1,2,3,4,5)),Draw((1,2,3,4,5,6)),Draw((2,3,4,5,6,7))],SPEC)
    with pytest.raises(ValueError,match="outside"):
        validate_draws([Draw((1,2,3,4,5,50)),Draw((1,2,3,4,5,6)),Draw((2,3,4,5,6,7))],SPEC)

def test_null_tests_are_deterministic():
    draws=generate_synthetic_draws(SPEC,count=80,seed=7)
    a=subset_occurrence_test(draws,fibonacci_numbers(49),SPEC,trials=64,seed=4)
    b=subset_occurrence_test(draws,fibonacci_numbers(49),SPEC,trials=64,seed=4)
    assert a==b and 0<a.empirical_p_value<=1
    t1=temporal_order_test(draws,SPEC,trials=32,seed=9); t2=temporal_order_test(draws,SPEC,trials=32,seed=9)
    assert t1==t2 and 0<t1.empirical_p_value<=1

def test_pair_anomalies_have_corrected_q_values():
    rows=pair_anomalies(generate_synthetic_draws(SPEC,count=90,seed=11),SPEC,top_n=8)
    assert len(rows)==8
    assert all(0<=r["p_value_upper"]<=1 and 0<=r["q_value_bh"]<=1 for r in rows)

def test_walk_forward_backtest_is_bounded():
    result=rolling_backtest(generate_synthetic_draws(SPEC,count=100,seed=12),SPEC,model="frequency",window=30,trials=64,seed=2)
    assert result.evaluated_draws==70 and 0<=result.mean_hits<=SPEC.pick_count
    assert result.chance_mean_hits==pytest.approx(36/49) and 0<result.empirical_p_value<=1

def test_anti_crowd_proxy_prefers_less_conventional_set():
    conventional=(1,5,7,11,13,21); alternative=(32,36,39,43,46,48)
    assert anti_crowd_proxy(alternative,SPEC)[0] > anti_crowd_proxy(conventional,SPEC)[0]

def test_dmd_temporal_null_integration():
    result=dmd_temporal_order_test(generate_synthetic_draws(SPEC,count=70,seed=17),SPEC,trials=8,seed=3,rank=6)
    assert result["rank"]==6 and 0<result["empirical_p_value_lower_error"]<=1
    assert len(result["dominant_modes"])==6

def test_measured_popularity_penalty_is_local():
    popular={(7,14,21,28,35,42):42177}
    exact=measured_popularity_penalty((7,14,21,28,35,42),popular,SPEC)
    near=measured_popularity_penalty((7,14,21,28,35,43),popular,SPEC)
    far=measured_popularity_penalty((2,9,18,27,38,49),popular,SPEC)
    assert exact>near>far

def test_candidate_search_reproducible_and_sorted():
    draws=generate_synthetic_draws(SPEC,count=90,seed=13)
    a=search_candidates(draws,SPEC,top_k=5,samples=500,seed=99); b=search_candidates(draws,SPEC,top_k=5,samples=500,seed=99)
    assert [x.numbers for x in a]==[x.numbers for x in b]
    assert [x.combined_score for x in a]==sorted([x.combined_score for x in a],reverse=True)

def test_analysis_and_proofpack_fail_closed_on_tamper():
    report=analyse(generate_synthetic_draws(SPEC,count=70,seed=14),SPEC,null_trials=24,candidate_samples=250,candidate_top_k=3,seed=5,backtest_windows=(20,),dmd_trials=6)
    assert report["claim_boundary"]==CLAIM_BOUNDARY
    pack=make_proofpack(report); assert verify_proofpack(pack)
    tampered=copy.deepcopy(pack); tampered["draw_count"]+=1
    assert not verify_proofpack(tampered)
