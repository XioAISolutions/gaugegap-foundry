from gaugegap.hypothesis_registry import get_hypothesis, load_registry
from gaugegap.unified_orchestrator import STAGES, UnifiedOrchestrator
from gaugegap.unified_registry import build_registry


def test_unified_registry_covers_configured_tracks():
    registry = build_registry()
    assert "integrity" in registry
    assert any(spec.units for spec in registry.values())
    unit_ids = [unit.id for spec in registry.values() for unit in spec.units]
    assert len(unit_ids) == len(set(unit_ids))


def test_unified_orchestrator_dry_run_is_reproducible():
    orchestrator = UnifiedOrchestrator()
    first = orchestrator.run("deep-boil-registry-check", dry_run=True)
    second = orchestrator.run("deep-boil-registry-check", dry_run=True)
    assert first.success
    assert first.stages == STAGES
    assert first.digest == second.digest
    assert first.runs[0].id == "deep-boil-registry-check"


def test_hypothesis_registry_resolves_registered_record():
    registry = load_registry()
    assert get_hypothesis("deep-boil-0001", registry).track == "Integration"
