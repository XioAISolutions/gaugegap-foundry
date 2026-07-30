"""Python-side verification of browser-exported proofpacks.

``tests/data/browser_proofpack_fixture.json`` was generated with Node.js
running byte-for-byte copies of the browser's ``canonicalJson``/``sha256Hex``
helpers, so these tests prove cross-language hash parity — including the
ECMAScript number-formatting edge cases (``1e-7`` vs Python's ``1e-07``,
scientific-notation switchover at 1e21, decimal rendering of 1e16, etc.).
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from gaugegap.browser_proofpack import (
    canonical_json,
    content_hash,
    js_number_to_string,
    verify_pack,
)

FIXTURE = Path(__file__).parent / "data" / "browser_proofpack_fixture.json"
SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify_browser_proofpack.py"

# Rendered by Node: JSON.stringify over the same values.
JS_NUMBER_TABLE = {
    1e-7: "1e-7",
    1e-6: "0.000001",
    0.00001: "0.00001",
    1e16: "10000000000000000",
    1e21: "1e+21",
    1e22: "1e+22",
    -0.5: "-0.5",
    0.1: "0.1",
    2.667: "2.667",
    -1.5e-15: "-1.5e-15",
    1.2345678901234568e20: "123456789012345680000",
    2.6666666666666665: "2.6666666666666665",
    0.0: "0",
}


def test_js_number_formatting_matches_ecmascript():
    for value, expected in JS_NUMBER_TABLE.items():
        assert js_number_to_string(value) == expected


def test_canonical_json_sorts_keys_and_compacts():
    assert canonical_json({"b": 1, "a": [True, None, "x"]}) == '{"a":[true,null,"x"],"b":1}'


def test_fixture_hash_matches_the_javascript_export():
    pack = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert content_hash(pack) == pack["content_hash"]
    verdict = verify_pack(pack)
    assert verdict["verified"], verdict["problems"]


def test_tampering_is_detected():
    pack = json.loads(FIXTURE.read_text(encoding="utf-8"))
    pack["parameters"]["rho"] = 99.9
    verdict = verify_pack(pack)
    assert not verdict["verified"]
    assert any("mismatch" in problem for problem in verdict["problems"])


def test_unsupported_schema_and_missing_boundary_are_flagged():
    verdict = verify_pack({"schema": "something.else.v9"})
    assert not verdict["verified"]
    assert any("unsupported schema" in problem for problem in verdict["problems"])
    assert any("claim_boundary" in problem for problem in verdict["problems"])


def test_cli_verifies_the_fixture():
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), str(FIXTURE)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["all_verified"] is True
