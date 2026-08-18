"""Exact, fail-closed verification of finite Hadamard witnesses.

A Hadamard matrix of order ``n`` is an ``n x n`` matrix over ``{+1, -1}`` whose
rows are pairwise orthogonal, i.e. ``H @ H.T == n * I`` exactly.  That identity
is a finite statement over the integers, so this module never touches floating
point: rows are stored as arbitrary-precision bitmasks and every inner product
is computed as ``n - 2 * popcount(row_i ^ row_j)``.

Hadamard Forge separates three things the literature usually bundles together:

* **construction** -- classical constructors (Sylvester, Paley I/II, Kronecker)
  that this module can emit itself;
* **ingestion** -- an external witness supplied as a file, trusted for nothing;
* **verification** -- exact integer gates that a witness must discharge before
  any label is attached to it.

A witness that fails any gate produces no certificate.  A witness this module
cannot construct is reported as ``awaiting_witness`` rather than as an open
problem: the registry describes *this constructor set*, not the literature.

CLAIM BOUNDARY:
Verifying a witness of order ``n`` establishes the exact existence of one
``n x n`` Hadamard matrix and nothing else.  It does not address the Hadamard
conjecture, does not establish inequivalence or minimality, and reports no
statement about orders for which no witness was supplied.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Mapping, Sequence


CLAIM_BOUNDARY = (
    "Exact integer verification of a single finite Hadamard witness: H @ H.T == n * I "
    "over the integers. This certifies the existence of one matrix of that order. It is "
    "not a proof of the Hadamard conjecture, says nothing about equivalence classes, and "
    "makes no claim about orders for which no witness was verified."
)

RELEASE_LABELS = ("REPRODUCED", "REDISCOVERED", "DISCOVERED")

WITNESS_SCHEMA = "gaugegap.hadamard_witness.v1"
VERIFICATION_SCHEMA = "gaugegap.hadamard_verification.v1"
PROOFPACK_SCHEMA = "gaugegap.hadamard_proofpack.v1"


class HadamardForgeError(RuntimeError):
    """Raised when a witness cannot be ingested as an exact +-1 matrix."""


# ---------------------------------------------------------------------------
# Witness representation
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class HadamardWitness:
    """An ``order x order`` sign matrix stored as one bitmask per row.

    Bit ``j`` of ``rows[i]`` is set exactly when ``H[i][j] == -1``; a clear bit
    is ``+1``.  The packing is the compressed representation *and* the exact
    representation -- decoding is total and lossless, so verification never
    depends on how the witness was transported.
    """

    order: int
    rows: tuple[int, ...]
    name: str
    provenance: str

    def __post_init__(self) -> None:
        if not isinstance(self.order, int) or isinstance(self.order, bool) or self.order < 1:
            raise HadamardForgeError("order must be a positive integer")
        if len(self.rows) != self.order:
            raise HadamardForgeError(
                f"witness declares order {self.order} but carries {len(self.rows)} rows"
            )
        limit = 1 << self.order
        for index, row in enumerate(self.rows):
            if not isinstance(row, int) or isinstance(row, bool):
                raise HadamardForgeError("row masks must be integers")
            if row < 0 or row >= limit:
                raise HadamardForgeError(
                    f"row {index} carries bits outside the declared order {self.order}"
                )

    # -- construction -------------------------------------------------------

    @classmethod
    def from_signs(
        cls,
        signs: Sequence[Sequence[int]],
        *,
        name: str,
        provenance: str,
    ) -> "HadamardWitness":
        """Ingest an explicit ``{+1, -1}`` matrix, failing closed on anything else."""

        rows_in = list(signs)
        order = len(rows_in)
        if order < 1:
            raise HadamardForgeError("witness has no rows")
        masks: list[int] = []
        for index, row in enumerate(rows_in):
            entries = list(row)
            if len(entries) != order:
                raise HadamardForgeError(
                    f"row {index} has {len(entries)} entries; expected {order} (matrix must be square)"
                )
            mask = 0
            for column, entry in enumerate(entries):
                if isinstance(entry, bool) or not isinstance(entry, int) or entry not in (1, -1):
                    raise HadamardForgeError(
                        f"entry ({index},{column}) is {entry!r}; only the exact integers +1 and -1 are admissible"
                    )
                if entry == -1:
                    mask |= 1 << column
            masks.append(mask)
        return cls(order, tuple(masks), name, provenance)

    @classmethod
    def from_packed_hex(
        cls,
        order: int,
        rows_hex: Sequence[str],
        *,
        name: str,
        provenance: str,
    ) -> "HadamardWitness":
        """Decode the packed representation emitted by :meth:`packed_hex`."""

        width = (order + 3) // 4
        masks: list[int] = []
        for index, token in enumerate(rows_hex):
            if not isinstance(token, str) or len(token) != width:
                raise HadamardForgeError(
                    f"packed row {index} must be {width} hex characters for order {order}"
                )
            try:
                masks.append(int(token, 16))
            except ValueError as exc:
                raise HadamardForgeError(f"packed row {index} is not hexadecimal") from exc
        return cls(order, tuple(masks), name, provenance)

    # -- access -------------------------------------------------------------

    def signs(self) -> tuple[tuple[int, ...], ...]:
        """Materialise the matrix as exact ``+1``/``-1`` integers."""

        return tuple(
            tuple(-1 if (row >> column) & 1 else 1 for column in range(self.order))
            for row in self.rows
        )

    def row_inner_product(self, i: int, j: int) -> int:
        """Exact integer ``<row_i, row_j>`` via popcount; no arithmetic on floats."""

        agreements_flipped = (self.rows[i] ^ self.rows[j]).bit_count()
        return self.order - 2 * agreements_flipped

    def column_masks(self) -> tuple[int, ...]:
        """Return the transpose in the same packed form."""

        columns = [0] * self.order
        for i, row in enumerate(self.rows):
            mask = row
            while mask:
                low = mask & -mask
                columns[low.bit_length() - 1] |= 1 << i
                mask ^= low
        return tuple(columns)

    def transpose(self) -> "HadamardWitness":
        return HadamardWitness(
            self.order,
            self.column_masks(),
            f"{self.name}-transpose",
            self.provenance,
        )

    def packed_hex(self) -> tuple[str, ...]:
        width = (self.order + 3) // 4
        return tuple(format(row, f"0{width}x") for row in self.rows)

    # -- identity -----------------------------------------------------------

    def to_dict(self, *, include_rows: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema": WITNESS_SCHEMA,
            "order": self.order,
            "name": self.name,
            "provenance": self.provenance,
            "rows_sha256": self.rows_digest(),
        }
        if include_rows:
            payload["rows_hex"] = list(self.packed_hex())
        return payload

    def rows_digest(self) -> str:
        """Hash of the packed rows alone (independent of name and provenance)."""

        canonical = json.dumps(
            {"order": self.order, "rows_hex": list(self.packed_hex())},
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def digest(self) -> str:
        canonical = json.dumps(
            self.to_dict(include_rows=True), sort_keys=True, separators=(",", ":")
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Verification gates
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class VerificationGate:
    name: str
    passed: bool
    detail: str

    def to_dict(self) -> dict[str, object]:
        return {"name": self.name, "passed": self.passed, "detail": self.detail}


@dataclass(frozen=True)
class HadamardVerification:
    witness_digest: str
    order: int
    passed: bool
    gram_diagonal: int | None
    gram_offdiagonal_max_abs: int | None
    gates: tuple[VerificationGate, ...]
    claim_boundary: str = CLAIM_BOUNDARY

    def failed_gates(self) -> tuple[str, ...]:
        return tuple(gate.name for gate in self.gates if not gate.passed)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": VERIFICATION_SCHEMA,
            "witness_digest": self.witness_digest,
            "order": self.order,
            "passed": self.passed,
            "gram_diagonal": self.gram_diagonal,
            "gram_offdiagonal_max_abs": self.gram_offdiagonal_max_abs,
            "gates": [gate.to_dict() for gate in self.gates],
            "claim_boundary": self.claim_boundary,
        }


def _gram_extremes(witness: HadamardWitness) -> tuple[set[int], int]:
    """Return the distinct diagonal values and ``max |off-diagonal|`` of ``H @ H.T``."""

    diagonal: set[int] = set()
    worst = 0
    for i in range(witness.order):
        diagonal.add(witness.row_inner_product(i, i))
        for j in range(i + 1, witness.order):
            value = abs(witness.row_inner_product(i, j))
            if value > worst:
                worst = value
    return diagonal, worst


def verify_hadamard(
    witness: HadamardWitness,
    *,
    expected_order: int | None = None,
    expected_rows_digest: str | None = None,
    check_columns: bool = True,
) -> HadamardVerification:
    """Discharge every exact gate required before a witness may be certified."""

    gates: list[VerificationGate] = []
    order = witness.order

    admissible = order in (1, 2) or order % 4 == 0
    gates.append(
        VerificationGate(
            "admissible_order",
            admissible,
            f"order {order} satisfies the necessary condition n in {{1, 2}} or 4 | n."
            if admissible
            else f"order {order} violates the necessary condition n in {{1, 2}} or 4 | n.",
        )
    )

    if expected_order is not None:
        gates.append(
            VerificationGate(
                "expected_order",
                order == expected_order,
                f"declared order {order} == requested order {expected_order}"
                if order == expected_order
                else f"declared order {order} != requested order {expected_order}",
            )
        )

    # The packed representation cannot express an entry outside {+1, -1}; this
    # gate records that the decoded shape is square and in range, which is what
    # the ingestion boundary enforces.
    shape_ok = len(witness.rows) == order and all(row < (1 << order) for row in witness.rows)
    gates.append(
        VerificationGate(
            "square_pm1_alphabet",
            shape_ok,
            f"{order} rows of {order} entries, every entry exactly +1 or -1."
            if shape_ok
            else "decoded witness is not a square +-1 matrix.",
        )
    )

    diagonal, worst_offdiagonal = _gram_extremes(witness)
    diagonal_ok = diagonal == {order}
    gates.append(
        VerificationGate(
            "gram_diagonal_equals_order",
            diagonal_ok,
            f"every diagonal entry of H @ H.T equals {order}."
            if diagonal_ok
            else f"diagonal entries of H @ H.T are {sorted(diagonal)}; expected {{{order}}}.",
        )
    )

    orthogonal = worst_offdiagonal == 0
    gates.append(
        VerificationGate(
            "row_orthogonality",
            orthogonal,
            "all off-diagonal entries of H @ H.T are exactly 0."
            if orthogonal
            else f"largest |off-diagonal| entry of H @ H.T is {worst_offdiagonal}; expected 0.",
        )
    )

    if check_columns:
        column_diagonal, column_worst = _gram_extremes(witness.transpose())
        columns_ok = column_diagonal == {order} and column_worst == 0
        gates.append(
            VerificationGate(
                "column_orthogonality",
                columns_ok,
                "H.T @ H == n * I holds exactly (independent recomputation on the transpose)."
                if columns_ok
                else f"H.T @ H is not n * I: diagonal {sorted(column_diagonal)}, "
                f"max |off-diagonal| {column_worst}.",
            )
        )

    if expected_rows_digest is not None:
        matches = witness.rows_digest() == expected_rows_digest
        gates.append(
            VerificationGate(
                "expected_rows_digest",
                matches,
                "packed rows match the expected SHA-256."
                if matches
                else "packed rows do not match the expected SHA-256.",
            )
        )

    passed = all(gate.passed for gate in gates)
    return HadamardVerification(
        witness_digest=witness.digest(),
        order=order,
        passed=passed,
        gram_diagonal=next(iter(diagonal)) if len(diagonal) == 1 else None,
        gram_offdiagonal_max_abs=worst_offdiagonal,
        gates=tuple(gates),
    )


# ---------------------------------------------------------------------------
# Classical constructors
# ---------------------------------------------------------------------------


def _is_prime(value: int) -> bool:
    if value < 2:
        return False
    if value % 2 == 0:
        return value == 2
    factor = 3
    while factor * factor <= value:
        if value % factor == 0:
            return False
        factor += 2
    return True


def _quadratic_residue_character(q: int) -> list[int]:
    """Legendre symbol table ``chi(0..q-1)`` for an odd prime ``q``."""

    chi = [-1] * q
    chi[0] = 0
    for x in range(1, q):
        chi[(x * x) % q] = 1
    return chi


def sylvester_witness(exponent: int) -> HadamardWitness:
    """Sylvester construction of order ``2 ** exponent``.

    ``H[i][j] == -1`` exactly when ``popcount(i & j)`` is odd, so the packed
    rows are produced directly without materialising the matrix.
    """

    if exponent < 0:
        raise HadamardForgeError("Sylvester exponent must be non-negative")
    order = 1 << exponent
    rows = []
    for i in range(order):
        mask = 0
        for j in range(order):
            if (i & j).bit_count() & 1:
                mask |= 1 << j
        rows.append(mask)
    return HadamardWitness(
        order,
        tuple(rows),
        name=f"sylvester-{order}",
        provenance=f"constructor:sylvester(2^{exponent})",
    )


def paley_type_i_witness(q: int) -> HadamardWitness:
    """Paley type I construction of order ``q + 1`` for a prime ``q = 3 (mod 4)``."""

    if not _is_prime(q) or q % 4 != 3:
        raise HadamardForgeError(
            f"Paley type I requires a prime q = 3 (mod 4); got q={q}"
        )
    chi = _quadratic_residue_character(q)
    order = q + 1
    # Border row/column plus the Jacobsthal block, then add the identity.
    signs: list[list[int]] = []
    for i in range(order):
        row: list[int] = []
        for j in range(order):
            if i == j:
                row.append(1)
            elif i == 0:
                row.append(1)
            elif j == 0:
                row.append(-1)
            else:
                row.append(chi[(i - j) % q])
        signs.append(row)
    return HadamardWitness.from_signs(
        signs,
        name=f"paley-i-{order}",
        provenance=f"constructor:paley_type_i(q={q})",
    )


def paley_type_ii_witness(q: int) -> HadamardWitness:
    """Paley type II construction of order ``2 * (q + 1)`` for a prime ``q = 1 (mod 4)``.

    Uses the symmetric conference matrix ``S`` of order ``q + 1`` and the block
    substitution ``H = S (x) [[1,1],[1,-1]] + I (x) [[1,-1],[-1,-1]]``.
    """

    if not _is_prime(q) or q % 4 != 1:
        raise HadamardForgeError(
            f"Paley type II requires a prime q = 1 (mod 4); got q={q}"
        )
    chi = _quadratic_residue_character(q)
    side = q + 1
    conference: list[list[int]] = []
    for i in range(side):
        row: list[int] = []
        for j in range(side):
            if i == j:
                row.append(0)
            elif i == 0:
                row.append(1)
            elif j == 0:
                row.append(1)
            else:
                row.append(chi[(i - j) % q])
        conference.append(row)

    block_s = ((1, 1), (1, -1))
    block_i = ((1, -1), (-1, -1))
    order = 2 * side
    signs = [[0] * order for _ in range(order)]
    for i in range(side):
        for j in range(side):
            scale = conference[i][j]
            for a in range(2):
                for b in range(2):
                    value = scale * block_s[a][b]
                    if i == j:
                        value += block_i[a][b]
                    signs[2 * i + a][2 * j + b] = value
    return HadamardWitness.from_signs(
        signs,
        name=f"paley-ii-{order}",
        provenance=f"constructor:paley_type_ii(q={q})",
    )


def kronecker_witness(left: HadamardWitness, right: HadamardWitness) -> HadamardWitness:
    """Kronecker product; order ``left.order * right.order``."""

    left_signs = left.signs()
    right_signs = right.signs()
    order = left.order * right.order
    signs = [[0] * order for _ in range(order)]
    for i in range(left.order):
        for j in range(left.order):
            scale = left_signs[i][j]
            for a in range(right.order):
                base_row = signs[i * right.order + a]
                source = right_signs[a]
                for b in range(right.order):
                    base_row[j * right.order + b] = scale * source[b]
    return HadamardWitness.from_signs(
        signs,
        name=f"kronecker-{order}",
        provenance=f"constructor:kronecker({left.name},{right.name})",
    )


def construct_witness(order: int) -> HadamardWitness:
    """Build a witness of ``order`` from this module's constructor set.

    Raises :class:`HadamardForgeError` when no constructor in the set applies.
    The failure is a statement about *this constructor set*, not about the
    literature: an order this module cannot build may still be constructible.
    """

    if order < 1:
        raise HadamardForgeError("order must be a positive integer")
    if order in (1, 2):
        return sylvester_witness(order - 1)
    if order % 4 != 0:
        raise HadamardForgeError(
            f"order {order} violates the necessary condition n in {{1, 2}} or 4 | n"
        )
    if order & (order - 1) == 0:
        return sylvester_witness(order.bit_length() - 1)
    if _is_prime(order - 1) and (order - 1) % 4 == 3:
        return paley_type_i_witness(order - 1)
    if order % 2 == 0:
        half = order // 2
        if _is_prime(half - 1) and (half - 1) % 4 == 1:
            return paley_type_ii_witness(half - 1)
    # Kronecker fallback: H_2 (x) H_{order/2} whenever the half order is itself
    # constructible.  Recursion terminates because the order strictly decreases.
    if order % 2 == 0 and (order // 2) % 4 == 0:
        try:
            half_witness = construct_witness(order // 2)
        except HadamardForgeError:
            half_witness = None
        if half_witness is not None:
            return kronecker_witness(sylvester_witness(1), half_witness)
    for factor in range(4, order // 2 + 1, 4):
        if order % factor:
            continue
        cofactor = order // factor
        if cofactor % 4 and cofactor not in (1, 2):
            continue
        try:
            left = construct_witness(factor)
            right = construct_witness(cofactor)
        except HadamardForgeError:
            continue
        return kronecker_witness(left, right)
    raise HadamardForgeError(
        f"no constructor in this module's set produces order {order}; "
        "supply an external witness file to verify one"
    )


def constructible_orders(limit: int) -> tuple[int, ...]:
    """Orders up to ``limit`` that :func:`construct_witness` can emit itself."""

    found = [1, 2]
    for order in range(4, limit + 1, 4):
        if _constructor_available(order):
            found.append(order)
    return tuple(found)


def orders_awaiting_witness(limit: int) -> tuple[int, ...]:
    """Admissible orders up to ``limit`` this constructor set does not cover.

    These are *not* claimed to be open in the literature; they are the orders
    for which Hadamard Forge needs an externally supplied witness before it can
    certify anything.
    """

    return tuple(
        order for order in range(4, limit + 1, 4) if not _constructor_available(order)
    )


def _constructor_available(order: int) -> bool:
    """Cheap structural test mirroring :func:`construct_witness` coverage."""

    if order in (1, 2):
        return True
    if order % 4 != 0:
        return False
    if order & (order - 1) == 0:
        return True
    if _is_prime(order - 1) and (order - 1) % 4 == 3:
        return True
    half = order // 2
    if _is_prime(half - 1) and (half - 1) % 4 == 1:
        return True
    if half % 4 == 0 and _constructor_available(half):
        return True
    for factor in range(4, order // 2 + 1, 4):
        if order % factor:
            continue
        cofactor = order // factor
        if cofactor not in (1, 2) and cofactor % 4:
            continue
        if _constructor_available(factor) and _constructor_available(cofactor):
            return True
    return False


# ---------------------------------------------------------------------------
# External witness ingestion
# ---------------------------------------------------------------------------


def load_witness(path: Path | str, *, name: str | None = None) -> HadamardWitness:
    """Load an external witness, trusting nothing about its contents.

    Three transport forms are accepted, all decoded exactly:

    * JSON ``{"order": n, "rows_hex": [...]}`` (the form this module emits);
    * JSON ``{"signs": [[1, -1, ...], ...]}``;
    * plain text, one row per line of ``+``/``-`` (or ``1``/``0``) characters.
    """

    source = Path(path)
    try:
        text = source.read_text(encoding="utf-8")
    except OSError as exc:
        raise HadamardForgeError(f"cannot read witness file {source}: {exc}") from exc

    provenance = f"external-witness:{source.name}"
    label = name or source.stem

    stripped = text.lstrip()
    if stripped.startswith("{"):
        try:
            payload = json.loads(text)
        except ValueError as exc:
            raise HadamardForgeError(f"witness file {source} is not valid JSON: {exc}") from exc
        if not isinstance(payload, dict):
            raise HadamardForgeError(f"witness file {source} must contain a JSON object")
        if "rows_hex" in payload:
            order = payload.get("order")
            if not isinstance(order, int) or isinstance(order, bool):
                raise HadamardForgeError("packed witness must declare an integer order")
            rows_hex = payload.get("rows_hex")
            if not isinstance(rows_hex, list):
                raise HadamardForgeError("packed witness must carry a rows_hex list")
            return HadamardWitness.from_packed_hex(
                order, rows_hex, name=str(payload.get("name", label)), provenance=provenance
            )
        if "signs" in payload:
            signs = payload["signs"]
            if not isinstance(signs, list):
                raise HadamardForgeError("witness 'signs' must be a list of rows")
            return HadamardWitness.from_signs(
                signs, name=str(payload.get("name", label)), provenance=provenance
            )
        raise HadamardForgeError(
            f"witness file {source} has neither 'rows_hex' nor 'signs'"
        )

    return HadamardWitness.from_signs(
        _parse_sign_text(text, source=source), name=label, provenance=provenance
    )


def _parse_sign_text(text: str, *, source: Path) -> list[list[int]]:
    rows: list[list[int]] = []
    for number, line in enumerate(text.splitlines(), start=1):
        candidate = "".join(line.split())
        if not candidate or candidate.startswith("#"):
            continue
        row: list[int] = []
        for character in candidate:
            if character in "+1":
                row.append(1)
            elif character in "-0":
                row.append(-1)
            else:
                raise HadamardForgeError(
                    f"{source}:{number}: character {character!r} is not a sign token"
                )
        rows.append(row)
    if not rows:
        raise HadamardForgeError(f"witness file {source} contains no rows")
    return rows


def write_witness(witness: HadamardWitness, path: Path | str) -> Path:
    """Write the packed witness so an independent checker can re-verify it."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(canonical_json(witness.to_dict(include_rows=True)), encoding="utf-8")
    return target


# ---------------------------------------------------------------------------
# Proofpack
# ---------------------------------------------------------------------------


def build_hadamard_proofpack(
    witness: HadamardWitness,
    verification: HadamardVerification,
    *,
    release_label: str = "REPRODUCED",
    problem_id: str,
    embed_rows_max_order: int = 64,
    search_record: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Assemble the content-hashed proofpack for a verified witness.

    Rows are embedded inline for small orders and referenced by SHA-256 for
    large ones; the digest of the packed rows is always present, so the
    companion witness file is verifiable against the proofpack either way.

    ``search_record`` is attached when the witness came from a search rather
    than a closed-form constructor, so the certificate carries what was examined
    alongside what was verified.
    """

    if release_label not in RELEASE_LABELS:
        raise ValueError(f"release_label must be one of {RELEASE_LABELS}")
    payload: dict[str, object] = {
        "schema": PROOFPACK_SCHEMA,
        "problem_id": problem_id,
        "release_label": release_label,
        "order": witness.order,
        "witness": witness.to_dict(include_rows=witness.order <= embed_rows_max_order),
        "witness_digest": witness.digest(),
        "rows_sha256": witness.rows_digest(),
        "verification": verification.to_dict(),
        "arithmetic": "exact_integer_popcount",
        "claim_boundary": CLAIM_BOUNDARY,
    }
    if search_record is not None:
        payload["search"] = dict(search_record)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    payload["proofpack_digest"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return payload


def canonical_json(payload: Mapping[str, object]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def gram_summary(witness: HadamardWitness, *, sample: int = 6) -> list[list[int]]:
    """Top-left ``sample x sample`` block of ``H @ H.T`` for human inspection."""

    span = min(sample, witness.order)
    return [
        [witness.row_inner_product(i, j) for j in range(span)]
        for i in range(span)
    ]
