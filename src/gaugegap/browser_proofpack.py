"""Verify browser-exported proofpacks.

The Foundry Experience (and the BrainSNN arcade) export content-hashed JSON
evidence files from the browser (schema ``gaugegap.browser_attractor_proofpack.v1``).
The hash is SHA-256 over a canonical serialization produced in JavaScript:
sorted object keys, no whitespace, ``JSON.stringify`` number/string semantics.

This module recomputes that hash in Python so a downloaded pack can be
verified offline. The only subtle part is number formatting: Python's
``repr``/``json.dumps`` diverge from ECMAScript for exponents (``1e-07`` vs
``1e-7``) and switch to scientific notation at different magnitudes, so
``js_number_to_string`` implements the ECMAScript ``Number::toString``
formatting rules over Python's shortest-round-trip digits.
"""
from __future__ import annotations

import hashlib
import json
import math
from typing import Any

SUPPORTED_SCHEMAS = frozenset({"gaugegap.browser_attractor_proofpack.v1"})


def js_number_to_string(value: float) -> str:
    """Format a float exactly as ECMAScript ``String(value)`` would."""
    if math.isnan(value) or math.isinf(value):
        raise ValueError("non-finite numbers cannot appear in JSON proofpacks")
    if value == 0:
        return "0"  # JSON.stringify(-0) is "0"
    sign = "-" if value < 0 else ""
    mantissa = repr(abs(value))
    if "e" in mantissa or "E" in mantissa:
        base, _, exp_text = mantissa.lower().partition("e")
        exponent = int(exp_text)
    else:
        base, exponent = mantissa, 0
    int_part, _, frac_part = base.partition(".")
    raw_digits = (int_part + frac_part).lstrip("0")
    # Decimal position n: value = 0.<digits> * 10**n (ECMAScript 6.1.6.1.20 terms).
    n = len(int_part.lstrip("0")) + exponent if int_part.lstrip("0") else exponent - (
        len(frac_part) - len(frac_part.lstrip("0"))
    )
    digits = raw_digits.rstrip("0")
    k = len(digits)
    if k <= n <= 21:
        text = digits + "0" * (n - k)
    elif 0 < n <= 21:
        text = digits[:n] + "." + digits[n:]
    elif -6 < n <= 0:
        text = "0." + "0" * (-n) + digits
    else:
        exponent_part = n - 1
        head = digits[0] + ("." + digits[1:] if k > 1 else "")
        text = f"{head}e{'+' if exponent_part >= 0 else '-'}{abs(exponent_part)}"
    return sign + text


def canonical_json(value: Any) -> str:
    """Mirror the browser's canonicalJson: sorted keys, compact, JS numbers."""
    if value is None or value is True or value is False:
        return json.dumps(value)
    if isinstance(value, bool):  # pragma: no cover - covered by the branch above
        return json.dumps(value)
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return js_number_to_string(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(canonical_json(item) for item in value) + "]"
    if isinstance(value, dict):
        items = (
            json.dumps(str(key), ensure_ascii=False) + ":" + canonical_json(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        )
        return "{" + ",".join(items) + "}"
    raise TypeError(f"unsupported type in proofpack: {type(value)!r}")


def content_hash(pack: dict) -> str:
    """SHA-256 over the canonical pack with ``content_hash`` removed."""
    body = {key: value for key, value in pack.items() if key != "content_hash"}
    return hashlib.sha256(canonical_json(body).encode("utf-8")).hexdigest()


def verify_pack(pack: dict) -> dict:
    """Verify a browser proofpack; returns a structured verdict."""
    problems: list[str] = []
    schema = pack.get("schema")
    if schema not in SUPPORTED_SCHEMAS:
        problems.append(f"unsupported schema: {schema!r}")
    if not pack.get("claim_boundary"):
        problems.append("missing claim_boundary")
    recorded = pack.get("content_hash")
    recomputed = content_hash(pack)
    if not recorded:
        problems.append("missing content_hash")
    elif recorded == "unavailable-no-webcrypto":
        problems.append("pack was exported without WebCrypto; hash cannot be verified")
    elif recorded != recomputed:
        problems.append("content_hash mismatch: pack was modified after export")
    return {
        "schema": schema,
        "verified": not problems,
        "recorded_hash": recorded,
        "recomputed_hash": recomputed,
        "problems": problems,
    }
