"""
Hypothesis pruning engine with Bayesian model comparison.

Mathematical Framework
----------------------
For competing hypotheses H₁, H₂, ..., Hₙ given data D, we compute:

1. Bayes Factor: BF₁₂ = P(D|H₁)/P(D|H₂)
   - BF > 10: Strong evidence for H₁
   - BF > 100: Decisive evidence for H₁

2. Model Evidence: P(D|H) = ∫ P(D|θ,H)·P(θ|H) dθ
   - Marginal likelihood integrating over parameters

3. Information Criteria:
   - AIC = 2k - 2ln(L): Akaike Information Criterion
   - BIC = k·ln(n) - 2ln(L): Bayesian Information Criterion
   - DIC = D̄ + pD: Deviance Information Criterion

where k = number of parameters, n = sample size, L = likelihood.

Hypothesis Lifecycle
--------------------
1. Registration: Hypothesis enters with prior probability
2. Testing: Accumulate evidence from experiments
3. Pruning: Eliminate when evidence ratio exceeds threshold
4. Survival: Track lifetime and evidence trajectory

Claim Boundary Compliance
-------------------------
Hypothesis pruning identifies which models are inconsistent with data.
Falsification is rigorous, but survival does NOT constitute proof of
Millennium Prize problems. Surviving hypotheses remain candidates for
further testing.

References
----------
- Kass & Raftery (1995). Bayes Factors. JASA.
- Burnham & Anderson (2002). Model Selection and Multimodel Inference.
- Gelman et al. (2013). Bayesian Data Analysis.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
import json
from scipy.special import logsumexp
from scipy.stats import chi2


@dataclass
class Hypothesis:
    """A testable hypothesis with evidence tracking."""
    
    id: str
    """Unique identifier"""
    
    description: str
    """Human-readable description"""
    
    track: str
    """Track: gaugegap, flowgap, or curverank"""
    
    prediction_function: Optional[Callable] = None
    """Function that predicts observables given parameters"""
    
    n_parameters: int = 0
    """Number of free parameters"""
    
    prior_probability: float = 1.0
    """Prior probability (uniform by default)"""
    
    log_evidence: float = 0.0
    """Accumulated log evidence"""
    
    evidence_history: List[Tuple[datetime, float]] = field(default_factory=list)
    """Timeline of evidence updates"""
    
    status: str = "active"
    """Status: active, falsified, or survived"""
    
    falsification_threshold: float = -10.0
    """Log evidence threshold for falsification (ln(BF) < -10)"""
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional metadata"""
    
    def update_evidence(self, log_likelihood: float, timestamp: Optional[datetime] = None):
        """
        Update hypothesis evidence with new data.
        
        Parameters
        ----------
        log_likelihood : float
            Log likelihood of data under this hypothesis
        timestamp : datetime, optional
            Time of update (default: now)
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        self.log_evidence += log_likelihood
        self.evidence_history.append((timestamp, self.log_evidence))
        
        # Check for falsification
        if self.log_evidence < self.falsification_threshold:
            self.status = "falsified"
    
    def bayes_factor(self, other: "Hypothesis") -> float:
        """
        Compute Bayes factor relative to another hypothesis.
        
        BF = P(D|H₁) / P(D|H₂) = exp(log_evidence₁ - log_evidence₂)
        
        Parameters
        ----------
        other : Hypothesis
            Competing hypothesis
        
        Returns
        -------
        float
            Bayes factor (BF > 1 favors this hypothesis)
        """
        return np.exp(self.log_evidence - other.log_evidence)
    
    def to_dict(self) -> Dict[str, Any]:
        """Export to dictionary."""
        return {
            "id": self.id,
            "description": self.description,
            "track": self.track,
            "n_parameters": self.n_parameters,
            "prior_probability": float(self.prior_probability),
            "log_evidence": float(self.log_evidence),
            "status": self.status,
            "evidence_history": [
                (ts.isoformat(), float(ev)) for ts, ev in self.evidence_history
            ],
            "metadata": self.metadata,
        }


@dataclass
class ModelComparison:
    """Result of Bayesian model comparison."""
    
    hypotheses: List[Hypothesis]
    """Competing hypotheses"""
    
    posterior_probabilities: Dict[str, float]
    """Posterior probability for each hypothesis"""
    
    bayes_factors: Dict[Tuple[str, str], float]
    """Pairwise Bayes factors"""
    
    best_hypothesis: str
    """ID of best-supported hypothesis"""
    
    evidence_ratios: Dict[str, float]
    """Evidence ratio relative to best hypothesis"""
    
    information_criteria: Dict[str, Dict[str, float]]
    """AIC, BIC, DIC for each hypothesis"""
    
    def to_dict(self) -> Dict[str, Any]:
        """Export to dictionary."""
        return {
            "posterior_probabilities": {k: float(v) for k, v in self.posterior_probabilities.items()},
            "best_hypothesis": self.best_hypothesis,
            "evidence_ratios": {k: float(v) for k, v in self.evidence_ratios.items()},
            "information_criteria": {
                h_id: {k: float(v) for k, v in ic.items()}
                for h_id, ic in self.information_criteria.items()
            },
            "bayes_factors": {
                f"{h1}_vs_{h2}": float(bf)
                for (h1, h2), bf in self.bayes_factors.items()
            },
        }


class BayesianModelComparison:
    """
    Bayesian model comparison with evidence computation.
    
    Mathematical Framework
    ----------------------
    Given hypotheses H₁, ..., Hₙ with priors P(Hᵢ) and data D:
    
    Posterior: P(Hᵢ|D) ∝ P(D|Hᵢ)·P(Hᵢ)
    
    Model Evidence: P(D|Hᵢ) = ∫ P(D|θ,Hᵢ)·P(θ|Hᵢ) dθ
    
    For nested models, use Savage-Dickey density ratio.
    For non-nested models, use bridge sampling or thermodynamic integration.
    """
    
    def __init__(self):
        """Initialize Bayesian model comparison."""
        pass
    
    def compare(
        self,
        hypotheses: List[Hypothesis],
        data: np.ndarray,
        compute_ic: bool = True,
    ) -> ModelComparison:
        """
        Compare multiple hypotheses given data.
        
        Parameters
        ----------
        hypotheses : list
            List of competing hypotheses
        data : array
            Observed data
        compute_ic : bool
            Whether to compute information criteria
        
        Returns
        -------
        ModelComparison
            Comparison results
        """
        if len(hypotheses) < 2:
            raise ValueError("Need at least 2 hypotheses for comparison")
        
        # Compute posterior probabilities using Bayes' theorem
        log_evidences = np.array([h.log_evidence for h in hypotheses])
        log_priors = np.array([np.log(h.prior_probability) for h in hypotheses])
        
        log_posteriors = log_evidences + log_priors
        log_posteriors -= logsumexp(log_posteriors)  # Normalize
        
        posterior_probs = {
            h.id: float(np.exp(log_post))
            for h, log_post in zip(hypotheses, log_posteriors)
        }
        
        # Find best hypothesis
        best_idx = np.argmax(log_posteriors)
        best_hypothesis = hypotheses[best_idx]
        
        # Compute pairwise Bayes factors
        bayes_factors = {}
        for i, h1 in enumerate(hypotheses):
            for j, h2 in enumerate(hypotheses):
                if i < j:
                    bf = h1.bayes_factor(h2)
                    bayes_factors[(h1.id, h2.id)] = bf
        
        # Compute evidence ratios relative to best
        evidence_ratios = {
            h.id: float(np.exp(h.log_evidence - best_hypothesis.log_evidence))
            for h in hypotheses
        }
        
        # Compute information criteria if requested
        information_criteria = {}
        if compute_ic:
            for h in hypotheses:
                information_criteria[h.id] = self._compute_information_criteria(
                    h, data
                )
        
        return ModelComparison(
            hypotheses=hypotheses,
            posterior_probabilities=posterior_probs,
            bayes_factors=bayes_factors,
            best_hypothesis=best_hypothesis.id,
            evidence_ratios=evidence_ratios,
            information_criteria=information_criteria,
        )
    
    def _compute_information_criteria(
        self,
        hypothesis: Hypothesis,
        data: np.ndarray,
    ) -> Dict[str, float]:
        """
        Compute AIC, BIC, DIC for a hypothesis.
        
        Parameters
        ----------
        hypothesis : Hypothesis
            Hypothesis to evaluate
        data : array
            Observed data
        
        Returns
        -------
        dict
            Information criteria values
        """
        k = hypothesis.n_parameters
        n = len(data)
        log_likelihood = hypothesis.log_evidence
        
        # AIC: 2k - 2ln(L)
        aic = 2 * k - 2 * log_likelihood
        
        # BIC: k·ln(n) - 2ln(L)
        bic = k * np.log(n) - 2 * log_likelihood
        
        # DIC: D̄ + pD (simplified version)
        # For full DIC, need posterior samples
        dic = -2 * log_likelihood + k
        
        return {
            "AIC": float(aic),
            "BIC": float(bic),
            "DIC": float(dic),
        }


class HypothesisPruner:
    """
    Hypothesis pruning engine with lifecycle tracking.
    
    This class manages a collection of hypotheses, tracks their evidence
    over time, and automatically prunes falsified hypotheses.
    """
    
    def __init__(
        self,
        falsification_threshold: float = -10.0,
        survival_threshold: float = 10.0,
    ):
        """
        Initialize hypothesis pruner.
        
        Parameters
        ----------
        falsification_threshold : float
            Log Bayes factor threshold for falsification (default: -10)
        survival_threshold : float
            Log Bayes factor threshold for strong survival (default: 10)
        """
        self.hypotheses: Dict[str, Hypothesis] = {}
        self.falsification_threshold = falsification_threshold
        self.survival_threshold = survival_threshold
        self.comparison_engine = BayesianModelComparison()
    
    def register_hypothesis(self, hypothesis: Hypothesis):
        """
        Register a new hypothesis for testing.
        
        Parameters
        ----------
        hypothesis : Hypothesis
            Hypothesis to register
        """
        hypothesis.falsification_threshold = self.falsification_threshold
        self.hypotheses[hypothesis.id] = hypothesis
    
    def update_evidence(
        self,
        hypothesis_id: str,
        log_likelihood: float,
        timestamp: Optional[datetime] = None,
    ):
        """
        Update evidence for a hypothesis.
        
        Parameters
        ----------
        hypothesis_id : str
            ID of hypothesis to update
        log_likelihood : float
            Log likelihood of new data
        timestamp : datetime, optional
            Time of update
        """
        if hypothesis_id not in self.hypotheses:
            raise ValueError(f"Unknown hypothesis: {hypothesis_id}")
        
        self.hypotheses[hypothesis_id].update_evidence(log_likelihood, timestamp)
    
    def prune_falsified(self) -> List[str]:
        """
        Identify and mark falsified hypotheses.
        
        Returns
        -------
        list
            IDs of newly falsified hypotheses
        """
        falsified = []
        for h_id, h in self.hypotheses.items():
            if h.status == "active" and h.log_evidence < self.falsification_threshold:
                h.status = "falsified"
                falsified.append(h_id)
        
        return falsified
    
    def identify_survivors(self) -> List[str]:
        """
        Identify strongly supported hypotheses.
        
        Returns
        -------
        list
            IDs of surviving hypotheses
        """
        survivors = []
        active = [h for h in self.hypotheses.values() if h.status == "active"]
        
        if len(active) < 2:
            return []
        
        # Find best hypothesis
        best = max(active, key=lambda h: h.log_evidence)
        
        for h in active:
            if h.id != best.id:
                bf = best.bayes_factor(h)
                if np.log(bf) > self.survival_threshold:
                    # Best hypothesis strongly dominates
                    if best.status == "active":
                        best.status = "survived"
                        survivors.append(best.id)
                    break
        
        return survivors
    
    def compare_active(self, data: np.ndarray) -> Optional[ModelComparison]:
        """
        Compare all active hypotheses.
        
        Parameters
        ----------
        data : array
            Observed data
        
        Returns
        -------
        ModelComparison or None
            Comparison results, or None if fewer than 2 active hypotheses
        """
        active = [h for h in self.hypotheses.values() if h.status == "active"]
        
        if len(active) < 2:
            return None
        
        return self.comparison_engine.compare(active, data)
    
    def get_status_summary(self) -> Dict[str, Any]:
        """
        Get summary of hypothesis statuses.
        
        Returns
        -------
        dict
            Summary statistics
        """
        statuses = [h.status for h in self.hypotheses.values()]
        
        return {
            "total": len(self.hypotheses),
            "active": statuses.count("active"),
            "falsified": statuses.count("falsified"),
            "survived": statuses.count("survived"),
            "hypotheses": {
                h_id: h.to_dict() for h_id, h in self.hypotheses.items()
            },
        }
    
    def export_results(self, filepath: str):
        """
        Export hypothesis tracking results to JSON.
        
        Parameters
        ----------
        filepath : str
            Output file path
        """
        summary = self.get_status_summary()
        
        with open(filepath, "w") as f:
            json.dump(summary, f, indent=2)
    
    def survival_analysis(self) -> Dict[str, Any]:
        """
        Analyze hypothesis survival over time.
        
        Returns
        -------
        dict
            Survival statistics for each hypothesis
        """
        survival_stats = {}
        
        for h_id, h in self.hypotheses.items():
            if len(h.evidence_history) < 2:
                continue
            
            timestamps = [ts for ts, _ in h.evidence_history]
            evidences = [ev for _, ev in h.evidence_history]
            
            # Compute lifetime
            lifetime = (timestamps[-1] - timestamps[0]).total_seconds() / 3600  # hours
            
            # Compute evidence trajectory
            evidence_slope = (evidences[-1] - evidences[0]) / max(len(evidences) - 1, 1)
            
            survival_stats[h_id] = {
                "lifetime_hours": float(lifetime),
                "initial_evidence": float(evidences[0]),
                "final_evidence": float(evidences[-1]),
                "evidence_slope": float(evidence_slope),
                "n_updates": len(evidences),
                "status": h.status,
            }
        
        return survival_stats


def compute_evidence_ratio(
    hypothesis1: Hypothesis,
    hypothesis2: Hypothesis,
) -> float:
    """
    Compute evidence ratio (Bayes factor) between two hypotheses.
    
    Parameters
    ----------
    hypothesis1 : Hypothesis
        First hypothesis
    hypothesis2 : Hypothesis
        Second hypothesis
    
    Returns
    -------
    float
        Evidence ratio (>1 favors hypothesis1)
    """
    return hypothesis1.bayes_factor(hypothesis2)


def information_criteria(
    log_likelihood: float,
    n_parameters: int,
    n_data: int,
) -> Dict[str, float]:
    """
    Compute information criteria for model selection.
    
    Parameters
    ----------
    log_likelihood : float
        Log likelihood of model
    n_parameters : int
        Number of model parameters
    n_data : int
        Number of data points
    
    Returns
    -------
    dict
        AIC, BIC, and DIC values
    """
    aic = 2 * n_parameters - 2 * log_likelihood
    bic = n_parameters * np.log(n_data) - 2 * log_likelihood
    dic = -2 * log_likelihood + n_parameters
    
    return {
        "AIC": float(aic),
        "BIC": float(bic),
        "DIC": float(dic),
    }


def likelihood_ratio_test(
    log_likelihood_full: float,
    log_likelihood_reduced: float,
    df_diff: int,
    alpha: float = 0.05,
) -> Tuple[float, float, bool]:
    """
    Perform likelihood ratio test for nested models.
    
    Mathematical Framework
    ----------------------
    For nested models M₁ ⊂ M₂:
    
    LR = -2(ln(L₁) - ln(L₂)) ~ χ²(df₂ - df₁)
    
    Reject reduced model if LR > χ²_critical.
    
    Parameters
    ----------
    log_likelihood_full : float
        Log likelihood of full model
    log_likelihood_reduced : float
        Log likelihood of reduced model
    df_diff : int
        Difference in degrees of freedom
    alpha : float
        Significance level
    
    Returns
    -------
    lr_statistic : float
        Likelihood ratio test statistic
    p_value : float
        P-value
    reject_reduced : bool
        Whether to reject reduced model
    """
    lr_statistic = -2 * (log_likelihood_reduced - log_likelihood_full)
    p_value = 1 - chi2.cdf(lr_statistic, df_diff)
    reject_reduced = p_value < alpha
    
    return float(lr_statistic), float(p_value), reject_reduced

# Made with Bob
