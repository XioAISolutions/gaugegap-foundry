"""Authoritative source adapters for Lottery Forge.

WCLC's since-inception print/PDF is the monthly historical snapshot. The current
winning-numbers page supplements it so monthly publication lag does not silently
omit the newest draws. Raw payloads are hashed before parsing and merging.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from hashlib import sha256
from html.parser import HTMLParser
import io
import re
from typing import Iterable
from urllib.request import Request, urlopen

from gaugegap.lottery_forge import Draw, LotterySpec, validate_draws

WCLC_SINCE_INCEPTION_URL = (
    "https://www.wclc.com/display-on/display-on-downloads/"
    "lotto-649-since-inception.htm?channel=print"
)
WCLC_RECENT_URL = "https://www.wclc.com/winning-numbers/lotto-649-extra.htm"
USER_AGENT = "GaugeGap-Lottery-Forge/1.0 (+https://github.com/XioAISolutions/gaugegap-foundry)"

_MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
_DATE_PREFIX = rf"(?P<date>(?:{_MONTHS})\s+\d{{1,2}},\s+\d{{4}})"
PDF_DRAW_RE = re.compile(
    rf"{_DATE_PREFIX}\s+"
    r"(?P<n1>\d{1,2})\s+(?P<n2>\d{1,2})\s+(?P<n3>\d{1,2})\s+"
    r"(?P<n4>\d{1,2})\s+(?P<n5>\d{1,2})\s+(?P<n6>\d{1,2})\s+"
    r"(?P<bonus>\d{1,2})(?:\s|$)"
)
HTML_DATE_RE = re.compile(
    rf"^(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+{_DATE_PREFIX}$"
)


@dataclass(frozen=True)
class SourcePayload:
    name: str
    url: str
    sha256: str
    bytes: int
    records_parsed: int

    def summary(self) -> dict[str, object]:
        return {
            "name": self.name,
            "url": self.url,
            "sha256": self.sha256,
            "bytes": self.bytes,
            "records_parsed": self.records_parsed,
        }


def _fetch_bytes(url: str, *, timeout: float = 30.0) -> bytes:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    with urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed HTTPS authority
        payload = response.read()
    if not payload:
        raise RuntimeError(f"empty response from {url}")
    return payload


def _iso_date(value: str) -> str:
    value = re.sub(
        r"^(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+",
        "",
        value,
    )
    return datetime.strptime(value, "%B %d, %Y").date().isoformat()


def parse_wclc_since_inception_text(text: str) -> tuple[Draw, ...]:
    """Parse normalized text extracted from WCLC's since-inception PDF."""
    by_date: dict[str, Draw] = {}
    normalized = " ".join(text.split())
    for match in PDF_DRAW_RE.finditer(normalized):
        draw_date = _iso_date(match.group("date"))
        numbers = tuple(int(match.group(f"n{i}")) for i in range(1, 7))
        bonus = int(match.group("bonus"))
        by_date[draw_date] = Draw.from_numbers(numbers, draw_date=draw_date, bonus=bonus)
    return tuple(by_date[key] for key in sorted(by_date))


def extract_wclc_pdf_draws(payload: bytes) -> tuple[Draw, ...]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("pypdf is required to parse the WCLC historical snapshot") from exc
    reader = PdfReader(io.BytesIO(payload))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    draws = parse_wclc_since_inception_text(text)
    if len(draws) < 100:
        raise RuntimeError(f"WCLC historical parse returned suspiciously few draws: {len(draws)}")
    return draws


class _TextCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tokens: list[str] = []

    def handle_data(self, data: str) -> None:
        value = " ".join(data.split())
        if value:
            self.tokens.append(value)


def parse_wclc_recent_html(html: str) -> tuple[Draw, ...]:
    """Parse recent Classic Draw records from WCLC's current results page."""
    parser = _TextCollector()
    parser.feed(html)
    tokens = parser.tokens
    by_date: dict[str, Draw] = {}
    i = 0
    while i < len(tokens):
        if not HTML_DATE_RE.match(tokens[i]):
            i += 1
            continue
        draw_date = _iso_date(tokens[i])
        classic = None
        for j in range(i + 1, min(i + 12, len(tokens))):
            if tokens[j].upper() == "CLASSIC DRAW":
                classic = j
                break
        if classic is None:
            i += 1
            continue
        numbers: list[int] = []
        bonus: int | None = None
        j = classic + 1
        while j < min(classic + 30, len(tokens)):
            token = tokens[j]
            if HTML_DATE_RE.match(token) or token.upper() == "GOLD BALL DRAW":
                break
            if re.fullmatch(r"\d{1,2}", token) and len(numbers) < 6:
                numbers.append(int(token))
            else:
                match = re.fullmatch(r"Bonus\s+(\d{1,2})", token, flags=re.IGNORECASE)
                if match:
                    bonus = int(match.group(1))
                    break
                if token.lower() == "bonus" and j + 1 < len(tokens) and re.fullmatch(r"\d{1,2}", tokens[j + 1]):
                    bonus = int(tokens[j + 1])
                    break
            j += 1
        if len(numbers) == 6 and bonus is not None:
            by_date[draw_date] = Draw.from_numbers(numbers, draw_date=draw_date, bonus=bonus)
        i = max(i + 1, j)
    return tuple(by_date[key] for key in sorted(by_date))


def merge_draw_sources(*sources: Iterable[Draw]) -> tuple[Draw, ...]:
    """Merge by ISO date; later sources override earlier ones."""
    by_date: dict[str, Draw] = {}
    undated: list[Draw] = []
    for source in sources:
        for draw in source:
            if draw.draw_date is None:
                undated.append(draw)
            else:
                by_date[draw.draw_date] = draw
    return tuple(by_date[key] for key in sorted(by_date)) + tuple(undated)


def filter_draw_dates(draws: Iterable[Draw], *, start_date: str | None, end_date: str | None) -> tuple[Draw, ...]:
    start = date.fromisoformat(start_date) if start_date else None
    end = date.fromisoformat(end_date) if end_date else None
    if start and end and start > end:
        raise ValueError("start_date must be <= end_date")
    out = []
    for draw in draws:
        if draw.draw_date is None:
            continue
        current = date.fromisoformat(draw.draw_date)
        if start and current < start:
            continue
        if end and current > end:
            continue
        out.append(draw)
    return tuple(out)


def fetch_wclc_649(
    *,
    start_date: str | None = None,
    end_date: str | None = None,
    timeout: float = 30.0,
    spec: LotterySpec | None = None,
) -> tuple[tuple[Draw, ...], dict[str, object]]:
    """Fetch, hash, merge, validate, and date-filter official WCLC Classic draws."""
    spec = spec or LotterySpec()
    historical_bytes = _fetch_bytes(WCLC_SINCE_INCEPTION_URL, timeout=timeout)
    recent_bytes = _fetch_bytes(WCLC_RECENT_URL, timeout=timeout)
    historical = extract_wclc_pdf_draws(historical_bytes)
    recent = parse_wclc_recent_html(recent_bytes.decode("utf-8", errors="replace"))
    if len(recent) < 2:
        raise RuntimeError(f"WCLC recent-page parse returned suspiciously few draws: {len(recent)}")
    merged = merge_draw_sources(historical, recent)
    selected = filter_draw_dates(merged, start_date=start_date, end_date=end_date)
    selected = validate_draws(selected, spec)
    if not selected:
        raise RuntimeError("no WCLC draws matched the requested date interval")
    meta = {
        "kind": "official-wclc-merged",
        "requested_start_date": start_date,
        "requested_end_date": end_date,
        "resolved_start_date": selected[0].draw_date,
        "resolved_end_date": selected[-1].draw_date,
        "records_selected": len(selected),
        "sources": [
            SourcePayload(
                "wclc-lotto-649-since-inception",
                WCLC_SINCE_INCEPTION_URL,
                sha256(historical_bytes).hexdigest(),
                len(historical_bytes),
                len(historical),
            ).summary(),
            SourcePayload(
                "wclc-lotto-649-current-results",
                WCLC_RECENT_URL,
                sha256(recent_bytes).hexdigest(),
                len(recent_bytes),
                len(recent),
            ).summary(),
        ],
    }
    return selected, meta
