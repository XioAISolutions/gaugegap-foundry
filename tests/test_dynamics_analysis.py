from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.dynamics_analysis import analyze_records, write_analysis_outputs


class DynamicsAnalysisTests(unittest.TestCase):
    def test_analysis_verdicts_compare_backend_drift(self) -> None:
        records = [
            _record("local_statevector", "z_expectation", site=0, time=0.0, value=1.0),
            _record("shot_sampler:none", "z_expectation", site=0, time=0.0, value=0.95),
            _record("shot_sampler:depolarizing", "z_expectation", site=0, time=0.0, value=0.75),
            _record("local_statevector", "zz_correlator", bond=0, time=0.0, value=-1.0),
            _record("shot_sampler:none", "zz_correlator", bond=0, time=0.0, value=-0.96),
            _record("shot_sampler:depolarizing", "zz_correlator", bond=0, time=0.0, value=-0.82),
        ]
        rows, summaries, metadata = analyze_records(records, shot_warning=0.08, shot_fail=0.18, noise_warning=0.12, noise_fail=0.28)
        self.assertEqual(metadata["record_count"], 6)
        self.assertEqual(metadata["overall_verdict"], "warning")
        self.assertTrue(any(row["drift_kind"] == "noise_drift" for row in rows))
        self.assertTrue(any(summary["verdict"] == "warning" for summary in summaries))

    def test_analysis_outputs_are_written(self) -> None:
        records = [
            _record("local_statevector", "z_expectation", site=0, time=0.0, value=1.0),
            _record("shot_sampler:none", "z_expectation", site=0, time=0.0, value=0.98),
        ]
        rows, summaries, metadata = analyze_records(records)
        output_dir = Path("/tmp/gaugegap-analysis-test")
        outputs = write_analysis_outputs(output_dir, rows, summaries, metadata)
        for output in outputs.values():
            self.assertTrue(Path(output).exists())


def _record(
    backend: str,
    observable: str,
    time: float,
    value: float,
    site: int | None = None,
    bond: int | None = None,
) -> dict[str, object]:
    return {
        "hypothesis_id": "gaugegap-0001",
        "backend": backend,
        "observable": observable,
        "site": site,
        "bond": bond,
        "time": time,
        "value": value,
    }


if __name__ == "__main__":
    unittest.main()
