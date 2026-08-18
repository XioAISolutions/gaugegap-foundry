"""Official WCLC source adapters for LOTTO MAX and DAILY GRAND.

Monthly since-inception PDFs are merged with current-result pages. Raw payloads
are hashed before parsing. LOTTO MAX callers should filter to the current 1-52
format beginning 2026-04-14 before treating draws as one homogeneous series.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from html.parser import HTMLParser
import io
import re
from urllib.request import Request, urlopen

from gaugegap.lottery_forge import Draw, LotterySpec, validate_draws
from gaugegap.lottery_sources import filter_draw_dates, merge_draw_sources

USER_AGENT = "GaugeGap-Lottery-Forge/1.1 (+https://github.com/XioAISolutions/gaugegap-foundry)"
WCLC_MAX_HISTORY_URL = "https://www.wclc.com/display-on/display-on-downloads/lotto-max-since-inception.htm?channel=print"
WCLC_MAX_RECENT_URL = "https://www.wclc.com/winning-numbers/lotto-max-extra.htm"
WCLC_DAILY_HISTORY_URL = "https://www.wclc.com/display-on/display-on-downloads/daily-grand-since-inception.htm?channel=print"
WCLC_DAILY_RECENT_URL = "https://www.wclc.com/winning-numbers/daily-grand-extra.htm"

_MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
_DATE = rf"(?P<date>(?:{_MONTHS})\s+\d{{1,2}},\s+\d{{4}})"
MAX_HISTORY_RE = re.compile(
    rf"{_DATE}\s+" + r"\s+".join(rf"(?P<n{i}>\d{{1,2}})" for i in range(1, 8))
    + r"\s+(?P<bonus>\d{1,2})\s+\d{7}(?:\s|$)"
)
DAILY_HISTORY_RE = re.compile(
    rf"{_DATE}\s+" + r"\s+".join(rf"(?P<n{i}>\d{{1,2}})" for i in range(1, 6))
    + r"\s+(?P<grand>\d)\s+\d{7}(?:\s|$)"
)
DATE_TOKEN_RE = re.compile(rf"^(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+{_DATE}$")


@dataclass(frozen=True)
class MultiGameDraw:
    draw: Draw
    grand_number: int | None = None


class _TextCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tokens: list[str] = []

    def handle_data(self, data: str) -> None:
        value = " ".join(data.split())
        if value:
            self.tokens.append(value)


def _fetch_bytes(url: str, *, timeout: float = 30.0) -> bytes:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    with urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed WCLC HTTPS URLs
        payload = response.read()
    if not payload:
        raise RuntimeError(f"empty response from {url}")
    return payload


def _date(value: str) -> str:
    value = re.sub(r"^(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+", "", value)
    return datetime.strptime(value, "%B %d, %Y").date().isoformat()


def _pdf_text(payload: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("pypdf is required") from exc
    reader = PdfReader(io.BytesIO(payload))
    return " ".join("\n".join(page.extract_text() or "" for page in reader.pages).split())


def parse_max_history_text(text: str) -> tuple[Draw, ...]:
    by_date: dict[str, Draw] = {}
    normalized = " ".join(text.split())
    for match in MAX_HISTORY_RE.finditer(normalized):
        draw_date = _date(match.group("date"))
        numbers = tuple(int(match.group(f"n{i}")) for i in range(1, 8))
        by_date[draw_date] = Draw.from_numbers(numbers, draw_date=draw_date, bonus=int(match.group("bonus")))
    return tuple(by_date[key] for key in sorted(by_date))


def parse_daily_history_text(text: str) -> tuple[MultiGameDraw, ...]:
    by_date: dict[str, MultiGameDraw] = {}
    normalized = " ".join(text.split())
    for match in DAILY_HISTORY_RE.finditer(normalized):
        draw_date = _date(match.group("date"))
        numbers = tuple(int(match.group(f"n{i}")) for i in range(1, 6))
        by_date[draw_date] = MultiGameDraw(
            Draw.from_numbers(numbers, draw_date=draw_date), int(match.group("grand"))
        )
    return tuple(by_date[key] for key in sorted(by_date))


def parse_max_recent_html(html: str) -> tuple[Draw, ...]:
    parser = _TextCollector(); parser.feed(html)
    tokens = parser.tokens
    by_date: dict[str, Draw] = {}
    for i, token in enumerate(tokens):
        if not DATE_TOKEN_RE.match(token):
            continue
        draw_date = _date(token)
        numbers: list[int] = []
        bonus = None
        for value in tokens[i + 1 : min(i + 35, len(tokens))]:
            if DATE_TOKEN_RE.match(value) or value.upper().startswith("MAXPLUS") or value.upper().startswith("MAXMILLIONS"):
                break
            if len(numbers) < 7 and re.fullmatch(r"\d{1,2}", value):
                numbers.append(int(value)); continue
            match = re.fullmatch(r"Bonus\s+(\d{1,2})", value, flags=re.I)
            if match:
                bonus = int(match.group(1)); break
            if value.lower() == "bonus":
                continue
            if bonus is None and len(numbers) == 7 and re.fullmatch(r"\d{1,2}", value):
                bonus = int(value); break
        if len(numbers) == 7 and bonus is not None:
            by_date[draw_date] = Draw.from_numbers(numbers, draw_date=draw_date, bonus=bonus)
    return tuple(by_date[key] for key in sorted(by_date))


def parse_daily_recent_html(html: str) -> tuple[MultiGameDraw, ...]:
    parser = _TextCollector(); parser.feed(html)
    tokens = parser.tokens
    by_date: dict[str, MultiGameDraw] = {}
    for i, token in enumerate(tokens):
        if not DATE_TOKEN_RE.match(token):
            continue
        draw_date = _date(token)
        main = None
        for j in range(i + 1, min(i + 15, len(tokens))):
            if tokens[j].upper() == "MAIN DRAW":
                main = j; break
        if main is None:
            continue
        numbers: list[int] = []
        grand = None
        j = main + 1
        while j < min(main + 30, len(tokens)):
            value = tokens[j]
            if DATE_TOKEN_RE.match(value):
                break
            if len(numbers) < 5 and re.fullmatch(r"\d{1,2}", value):
                numbers.append(int(value)); j += 1; continue
            match = re.fullmatch(r"Grand\s*Number\s*(\d)", value, flags=re.I)
            if match:
                grand = int(match.group(1)); break
            if value.lower() in {"grand", "grand number"} and j + 1 < len(tokens) and re.fullmatch(r"[1-7]", tokens[j + 1]):
                grand = int(tokens[j + 1]); break
            j += 1
        if len(numbers) == 5 and grand is not None:
            by_date[draw_date] = MultiGameDraw(Draw.from_numbers(numbers, draw_date=draw_date), grand)
    return tuple(by_date[key] for key in sorted(by_date))


def fetch_wclc_max(*, start_date: str = "2026-04-14", end_date: str | None = None, timeout: float = 30.0):
    history_bytes = _fetch_bytes(WCLC_MAX_HISTORY_URL, timeout=timeout)
    recent_bytes = _fetch_bytes(WCLC_MAX_RECENT_URL, timeout=timeout)
    historical = parse_max_history_text(_pdf_text(history_bytes))
    recent = parse_max_recent_html(recent_bytes.decode("utf-8", errors="replace"))
    if len(historical) < 1000 or len(recent) < 2:
        raise RuntimeError(f"suspicious LOTTO MAX parse: historical={len(historical)} recent={len(recent)}")
    selected = filter_draw_dates(merge_draw_sources(historical, recent), start_date=start_date, end_date=end_date)
    spec = LotterySpec(name="lotto-max-7of52", pool_size=52, pick_count=7)
    selected = validate_draws(selected, spec)
    return selected, {
        "kind": "official-wclc-lotto-max",
        "records_selected": len(selected),
        "sources": [
            {"url": WCLC_MAX_HISTORY_URL, "sha256": sha256(history_bytes).hexdigest(), "bytes": len(history_bytes), "records_parsed": len(historical)},
            {"url": WCLC_MAX_RECENT_URL, "sha256": sha256(recent_bytes).hexdigest(), "bytes": len(recent_bytes), "records_parsed": len(recent)},
        ],
    }


def fetch_wclc_daily_grand(*, start_date: str | None = None, end_date: str | None = None, timeout: float = 30.0):
    history_bytes = _fetch_bytes(WCLC_DAILY_HISTORY_URL, timeout=timeout)
    recent_bytes = _fetch_bytes(WCLC_DAILY_RECENT_URL, timeout=timeout)
    historical = parse_daily_history_text(_pdf_text(history_bytes))
    recent = parse_daily_recent_html(recent_bytes.decode("utf-8", errors="replace"))
    if len(historical) < 900 or len(recent) < 2:
        raise RuntimeError(f"suspicious DAILY GRAND parse: historical={len(historical)} recent={len(recent)}")
    by_date = {row.draw.draw_date: row for row in historical}
    by_date.update({row.draw.draw_date: row for row in recent})
    rows = tuple(by_date[key] for key in sorted(by_date))
    if start_date:
        rows = tuple(row for row in rows if row.draw.draw_date and row.draw.draw_date >= start_date)
    if end_date:
        rows = tuple(row for row in rows if row.draw.draw_date and row.draw.draw_date <= end_date)
    spec = LotterySpec(name="daily-grand-5of49", pool_size=49, pick_count=5)
    validate_draws(tuple(row.draw for row in rows), spec)
    return rows, {
        "kind": "official-wclc-daily-grand",
        "records_selected": len(rows),
        "sources": [
            {"url": WCLC_DAILY_HISTORY_URL, "sha256": sha256(history_bytes).hexdigest(), "bytes": len(history_bytes), "records_parsed": len(historical)},
            {"url": WCLC_DAILY_RECENT_URL, "sha256": sha256(recent_bytes).hexdigest(), "bytes": len(recent_bytes), "records_parsed": len(recent)},
        ],
    }
