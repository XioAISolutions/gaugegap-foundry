"""Verification-first lottery diagnostics and anti-crowd heuristics.

Nothing here changes the probability of a valid combination in a fair draw.
Historical structure must survive null controls and strict future holdouts before
it can be treated as predictive evidence. Crowd scores address sharing risk only.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from itertools import combinations
import heapq, json, math, random
from typing import Iterable, Mapping, Sequence

import numpy as np

CLAIM_BOUNDARY = (
    "Finite historical diagnostics only. No reported pattern, score, rank, temporal mode, "
    "or anti-crowd heuristic changes the draw probability of a valid combination in a fair "
    "lottery. Predictive claims require pre-registered out-of-sample performance above a "
    "chance null; anti-crowd scores are behavioural proxies, not measured ticket popularity."
)

@dataclass(frozen=True)
class LotterySpec:
    name: str = "lotto-6of49"; pool_size: int = 49; pick_count: int = 6
    def validate(self) -> None:
        if self.pool_size < 2 or not 1 <= self.pick_count < self.pool_size:
            raise ValueError("invalid lottery specification")

@dataclass(frozen=True)
class Draw:
    numbers: tuple[int, ...]; draw_date: str | None = None
    @classmethod
    def from_numbers(cls, numbers: Iterable[int], draw_date=None) -> "Draw":
        return cls(tuple(sorted(map(int, numbers))), None if draw_date is None else str(draw_date))

@dataclass(frozen=True)
class NullResult:
    statistic: float; null_mean: float; null_std: float; empirical_p_value: float
    trials: int; alternative: str; seed: int
    def summary(self) -> dict[str, object]: return self.__dict__.copy()

@dataclass(frozen=True)
class BacktestResult:
    model: str; window: int; evaluated_draws: int; total_hits: int; mean_hits: float
    chance_mean_hits: float; empirical_p_value: float; trials: int; seed: int
    def summary(self) -> dict[str, object]: return self.__dict__.copy()

@dataclass(frozen=True)
class CandidateScore:
    numbers: tuple[int, ...]; anti_crowd_score: float; neutrality_score: float
    measured_popularity_penalty: float; combined_score: float; features: Mapping[str, float]
    def summary(self) -> dict[str, object]:
        d=self.__dict__.copy(); d["numbers"]=list(self.numbers); d["features"]=dict(self.features); return d

def validate_draws(draws: Sequence[Draw], spec: LotterySpec) -> tuple[Draw, ...]:
    spec.validate()
    if len(draws) < 3: raise ValueError("at least three draws are required")
    out=[]
    for i, draw in enumerate(draws):
        nums=tuple(sorted(draw.numbers))
        if len(nums) != spec.pick_count: raise ValueError(f"draw {i} has wrong number count")
        if len(set(nums)) != len(nums): raise ValueError(f"draw {i} contains duplicate numbers")
        if nums[0] < 1 or nums[-1] > spec.pool_size: raise ValueError(f"draw {i} outside valid range")
        out.append(Draw(nums, draw.draw_date))
    return tuple(out)

def draws_digest(draws: Sequence[Draw], spec: LotterySpec) -> str:
    body={"game":spec.__dict__,"draws":[{"date":d.draw_date,"numbers":list(d.numbers)} for d in draws]}
    return sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def encode_draws(draws: Sequence[Draw], spec: LotterySpec) -> np.ndarray:
    draws=validate_draws(draws,spec); x=np.zeros((len(draws),spec.pool_size),float)
    for i,d in enumerate(draws): x[i,np.asarray(d.numbers)-1]=1.0
    return x

def fibonacci_numbers(limit: int) -> tuple[int, ...]:
    if limit < 1: return ()
    a=[1,2]
    while a[-1]+a[-2] <= limit: a.append(a[-1]+a[-2])
    return tuple(v for v in a if v <= limit)

def number_frequency_records(draws: Sequence[Draw], spec: LotterySpec) -> list[dict[str,float|int]]:
    counts=encode_draws(draws,spec).sum(0); p=spec.pick_count/spec.pool_size; exp=len(draws)*p
    sd=math.sqrt(len(draws)*p*(1-p)) or 1.0
    return [{"number":i+1,"count":int(c),"expected":float(exp),"z_score":float((c-exp)/sd)} for i,c in enumerate(counts)]

def _random_draw(rng: random.Random, spec: LotterySpec) -> tuple[int,...]:
    return tuple(sorted(rng.sample(range(1,spec.pool_size+1),spec.pick_count)))

def subset_occurrence_test(draws, subset, spec, *, trials=5000, seed=0) -> NullResult:
    draws=validate_draws(draws,spec); subset=frozenset(map(int,subset))
    if not subset or any(n<1 or n>spec.pool_size for n in subset): raise ValueError("invalid subset")
    obs=sum(len(subset.intersection(d.numbers)) for d in draws); rng=random.Random(seed); null=[]
    for _ in range(trials): null.append(sum(len(subset.intersection(_random_draw(rng,spec))) for _d in draws))
    arr=np.asarray(null,float); mean=float(arr.mean()); dist=abs(obs-mean)
    extreme=int(np.count_nonzero(np.abs(arr-mean)>=dist-1e-12))
    return NullResult(float(obs),mean,float(arr.std(ddof=1)) if trials>1 else 0.0,(extreme+1)/(trials+1),trials,"two-sided",seed)

def _binom_upper(n:int,p:float,k0:int)->float:
    return min(1.0,sum(math.comb(n,k)*p**k*(1-p)**(n-k) for k in range(max(0,k0),n+1)))

def _bh(ps: Sequence[float])->list[float]:
    m=len(ps); order=sorted(range(m),key=lambda i:ps[i]); q=[1.0]*m; running=1.0
    for r0 in range(m-1,-1,-1):
        i=order[r0]; running=min(running,ps[i]*m/(r0+1),1.0); q[i]=running
    return q

def pair_anomalies(draws, spec, *, top_n=20)->list[dict[str,object]]:
    draws=validate_draws(draws,spec); pairs=list(combinations(range(1,spec.pool_size+1),2)); counts={p:0 for p in pairs}
    for d in draws:
        for p in combinations(d.numbers,2): counts[p]+=1
    prob=spec.pick_count*(spec.pick_count-1)/(spec.pool_size*(spec.pool_size-1))
    ps=[_binom_upper(len(draws),prob,counts[p]) for p in pairs]; qs=_bh(ps)
    rows=[{"pair":list(p),"count":counts[p],"expected":len(draws)*prob,"p_value_upper":ps[i],"q_value_bh":qs[i]} for i,p in enumerate(pairs)]
    rows.sort(key=lambda r:(r["q_value_bh"],r["p_value_upper"],-r["count"],r["pair"])); return rows[:max(1,top_n)]

def _lag1(x:np.ndarray)->float:
    vals=[]
    for j in range(x.shape[1]):
        a,b=x[:-1,j],x[1:,j]
        vals.append(0.0 if np.std(a)==0 or np.std(b)==0 else abs(float(np.corrcoef(a,b)[0,1])))
    return max(vals,default=0.0)

def temporal_order_test(draws,spec,*,trials=2000,seed=0)->NullResult:
    x=encode_draws(draws,spec); obs=_lag1(x); rng=np.random.default_rng(seed)
    null=np.asarray([_lag1(x[rng.permutation(len(x))]) for _ in range(trials)],float)
    p=(int(np.count_nonzero(null>=obs-1e-12))+1)/(trials+1)
    return NullResult(obs,float(null.mean()),float(null.std(ddof=1)) if trials>1 else 0.0,p,trials,"greater",seed)

def dmd_temporal_order_test(draws,spec,*,trials=128,seed=0,rank=12)->dict[str,object]:
    from gaugegap.koopman import dominant_modes, exact_dmd
    x=encode_draws(draws,spec); rank=max(1,min(rank,len(x)-1,x.shape[1])); obs=exact_dmd(x,dt=1.0,rank=rank)
    rng=np.random.default_rng(seed); null=[]
    for _ in range(trials): null.append(exact_dmd(x[rng.permutation(len(x))],dt=1.0,rank=rank).reconstruction_error)
    arr=np.asarray(null,float); p=(int(np.count_nonzero(arr<=obs.reconstruction_error+1e-12))+1)/(trials+1)
    return {"rank":rank,"observed_reconstruction_error":float(obs.reconstruction_error),"observed_spectral_radius":float(obs.spectral_radius),
            "dominant_modes":dominant_modes(obs,count=min(8,rank)),"null_mean_reconstruction_error":float(arr.mean()),
            "null_std_reconstruction_error":float(arr.std(ddof=1)) if trials>1 else 0.0,"empirical_p_value_lower_error":p,"trials":trials,"seed":seed,
            "claim_boundary":"Finite sampled DMD diagnostic only; lower error than shuffled order is exploratory structure, not prospective prediction."}

def _predict(history,spec,model)->tuple[int,...]:
    x=encode_draws(history,spec); counts=x.sum(0)
    if model=="frequency": score=counts
    elif model=="cold-frequency": score=-counts
    else:
        gaps=np.zeros(spec.pool_size)
        for j in range(spec.pool_size):
            hit=np.flatnonzero(x[:,j]); gaps[j]=len(history) if not hit.size else len(history)-1-int(hit[-1])
        if model=="recency": score=gaps
        elif model=="hybrid": score=(counts-counts.mean())/max(float(counts.std()),1e-12)+.25*(gaps-gaps.mean())/max(float(gaps.std()),1e-12)
        else: raise ValueError(f"unknown model: {model}")
    order=sorted(range(spec.pool_size),key=lambda j:(-float(score[j]),j+1)); return tuple(sorted(j+1 for j in order[:spec.pick_count]))

def rolling_backtest(draws,spec,*,model,window=52,trials=5000,seed=0)->BacktestResult:
    draws=validate_draws(draws,spec)
    if window<3 or window>=len(draws): raise ValueError("invalid window")
    hits=[]
    for i in range(window,len(draws)): hits.append(len(set(_predict(draws[i-window:i],spec,model)).intersection(draws[i].numbers)))
    obs=sum(hits); actual=[set(d.numbers) for d in draws[window:]]; rng=random.Random(seed); null=[]
    for _ in range(trials): null.append(sum(len(set(_random_draw(rng,spec)).intersection(a)) for a in actual))
    p=(sum(v>=obs for v in null)+1)/(trials+1); chance=spec.pick_count**2/spec.pool_size
    return BacktestResult(model,window,len(hits),obs,float(np.mean(hits)),chance,p,trials,seed)

def _progressions(nums)->int:
    s=set(nums); return sum(1 for a,b in combinations(sorted(nums),2) if 2*b-a in s and 2*b-a>b)

def combination_features(numbers,spec)->dict[str,float]:
    v=tuple(sorted(map(int,numbers)))
    if len(v)!=spec.pick_count or len(set(v))!=len(v) or v[0]<1 or v[-1]>spec.pool_size: raise ValueError("invalid combination")
    fib=set(fibonacci_numbers(spec.pool_size)); chosen=set(v)
    return {"birthday_count":float(sum(x<=31 for x in v)),"fibonacci_count":float(sum(x in fib for x in v)),"lucky_count":float(sum(x in {7,11,13} for x in v)),
            "round_count":float(sum(x%5==0 for x in v)),"consecutive_pairs":float(sum(x+1 in chosen for x in v)),"three_term_progressions":float(_progressions(v)),
            "same_last_digit_pairs":float(sum(a%10==b%10 for a,b in combinations(v,2))),"all_above_31":float(all(x>31 for x in v)),
            "sum":float(sum(v)),"odd_count":float(sum(x%2 for x in v)),"range":float(v[-1]-v[0])}

def anti_crowd_proxy(numbers,spec)->tuple[float,dict[str,float]]:
    f=combination_features(numbers,spec)
    penalty=.90*f["birthday_count"]+.75*f["fibonacci_count"]+.70*f["lucky_count"]+.30*f["round_count"]+.65*f["three_term_progressions"]+.30*f["same_last_digit_pairs"]+.50*f["all_above_31"]-.20*f["consecutive_pairs"]
    return -float(penalty),f

def historical_neutrality_score(numbers,records)->float:
    z={int(r["number"]):float(r["z_score"]) for r in records}; return -float(np.mean([abs(z[int(n)]) for n in numbers]))

def measured_popularity_penalty(numbers,popular,spec)->float:
    if not popular:return 0.0
    s=set(numbers); return max(math.log1p(max(0,int(plays)))*(len(s.intersection(combo))/spec.pick_count)**4 for combo,plays in popular.items())

def score_candidate(numbers,spec,records,*,neutrality_weight=.35,popular_combinations=None,popularity_weight=.35)->CandidateScore:
    combo=tuple(sorted(map(int,numbers))); anti,f=anti_crowd_proxy(combo,spec); neutral=historical_neutrality_score(combo,records); measured=measured_popularity_penalty(combo,popular_combinations,spec)
    return CandidateScore(combo,anti,neutral,measured,anti+neutrality_weight*neutral-popularity_weight*measured,f)

def search_candidates(draws,spec,*,top_k=10,samples=200000,seed=0,exhaustive=False,neutrality_weight=.35,popular_combinations=None,popularity_weight=.35)->list[CandidateScore]:
    draws=validate_draws(draws,spec); records=number_frequency_records(draws,spec); heap=[]
    if exhaustive: iterator=combinations(range(1,spec.pool_size+1),spec.pick_count)
    else:
        rng=random.Random(seed); seen=set(); target=min(samples,math.comb(spec.pool_size,spec.pick_count))
        def sampled():
            while len(seen)<target:
                c=_random_draw(rng,spec)
                if c not in seen: seen.add(c); yield c
        iterator=sampled()
    for combo in iterator:
        score=score_candidate(combo,spec,records,neutrality_weight=neutrality_weight,popular_combinations=popular_combinations,popularity_weight=popularity_weight)
        entry=(score.combined_score,tuple(-n for n in score.numbers),score)
        if len(heap)<top_k: heapq.heappush(heap,entry)
        elif entry[:2]>heap[0][:2]: heapq.heapreplace(heap,entry)
    return [x[2] for x in sorted(heap,key=lambda e:(e[0],e[1]),reverse=True)]

def generate_synthetic_draws(spec,*,count=220,seed=649)->tuple[Draw,...]:
    rng=random.Random(seed); return tuple(Draw(_random_draw(rng,spec)) for _ in range(count))

def analyse(draws,spec,*,null_trials=2000,candidate_samples=100000,candidate_top_k=10,seed=649,backtest_windows=(26,52,104),dmd_trials=None,popular_combinations=None)->dict[str,object]:
    draws=validate_draws(draws,spec); freqs=number_frequency_records(draws,spec); fib=fibonacci_numbers(spec.pool_size)
    fib_test=subset_occurrence_test(draws,fib,spec,trials=null_trials,seed=seed); temporal=temporal_order_test(draws,spec,trials=null_trials,seed=seed+1)
    dmd=dmd_temporal_order_test(draws,spec,trials=min(128,null_trials) if dmd_trials is None else dmd_trials,seed=seed+3,rank=12); pairs=pair_anomalies(draws,spec)
    back=[]
    for w in backtest_windows:
        if w<len(draws):
            for mi,m in enumerate(("frequency","cold-frequency","recency","hybrid")): back.append(rolling_backtest(draws,spec,model=m,window=w,trials=null_trials,seed=seed+10000+w*10+mi).summary())
    candidates=search_candidates(draws,spec,top_k=candidate_top_k,samples=candidate_samples,seed=seed+2,popular_combinations=popular_combinations)
    gate=any(x["empirical_p_value"]<.01 and x["mean_hits"]>x["chance_mean_hits"] for x in back)
    return {"schema":"gaugegap.lottery_forge.analysis.v1","game":spec.__dict__,"draw_count":len(draws),"draws_sha256":draws_digest(draws,spec),"claim_boundary":CLAIM_BOUNDARY,
            "frequency_records":freqs,"fibonacci":{"numbers":list(fib),"null_test":fib_test.summary(),"interpretation":"exploratory unless pre-registered"},
            "pair_anomalies":pairs,"pairs_surviving_bh_0_05":[x for x in pairs if x["q_value_bh"]<.05],"temporal_order":temporal.summary(),"dmd_temporal_order":dmd,
            "rolling_backtests":back,"predictive_evidence_gate":{"threshold":"empirical p < 0.01 and mean hits > chance on strict holdout","passed":bool(gate)},
            "candidate_search":{"objective":"anti-crowd behavioural proxy plus finite-history neutrality; NOT draw probability","measured_popular_combinations_count":len(popular_combinations or {}),"sample_count":candidate_samples,"top":[c.summary() for c in candidates]}}

def make_proofpack(analysis: Mapping[str,object])->dict[str,object]:
    body=dict(analysis); body["proofpack_schema"]="gaugegap.lottery_forge.proofpack.v1"; body["claim_boundary"]=CLAIM_BOUNDARY; body.pop("result_hash",None)
    body["result_hash"]=sha256(json.dumps(body,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest(); return body

def verify_proofpack(payload: Mapping[str,object])->bool:
    if payload.get("proofpack_schema")!="gaugegap.lottery_forge.proofpack.v1" or payload.get("claim_boundary")!=CLAIM_BOUNDARY:return False
    expected=payload.get("result_hash"); body=dict(payload); body.pop("result_hash",None)
    try: actual=sha256(json.dumps(body,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
    except (TypeError,ValueError): return False
    return isinstance(expected,str) and expected==actual
