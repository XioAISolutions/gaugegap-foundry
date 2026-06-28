from gaugegap.unified_orchestrator import UnifiedOrchestrator


def main() -> int:
    result = UnifiedOrchestrator().run("deep-boil-all")
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
