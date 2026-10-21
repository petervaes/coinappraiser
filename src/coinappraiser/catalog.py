import json
import os
import re
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from pydantic import ValidationError

from coinappraiser.models import Catalog, Identification, PriceReference

MAX_CATALOG_BYTES = 5 * 1024 * 1024
CATALOG_TIMEOUT_SECONDS = 10
REPOSITORY_CATALOG = Path(__file__).resolve().parents[2] / "catalog" / "catalog.json"
DEFAULT_CATALOG = (
    REPOSITORY_CATALOG
    if REPOSITORY_CATALOG.is_file()
    else Path(__file__).with_name("catalog.json")
)


class CatalogUnavailableError(Exception):
    """Raised when the configured catalog cannot be loaded or validated."""


def load_catalog() -> Catalog:
    catalog_url = os.environ.get("COINAPPRAISER_CATALOG_URL")
    try:
        if catalog_url:
            if not catalog_url.startswith("https://"):
                raise CatalogUnavailableError(
                    "COINAPPRAISER_CATALOG_URL must use HTTPS."
                )
            with urlopen(catalog_url, timeout=CATALOG_TIMEOUT_SECONDS) as response:
                raw = response.read(MAX_CATALOG_BYTES + 1)
            if len(raw) > MAX_CATALOG_BYTES:
                raise CatalogUnavailableError("The catalog exceeds the 5 MiB limit.")
        else:
            raw = DEFAULT_CATALOG.read_bytes()
        return Catalog.model_validate(json.loads(raw))
    except (OSError, URLError, json.JSONDecodeError, ValidationError) as exc:
        raise CatalogUnavailableError(f"Could not load the price catalog: {exc}") from exc


def search_catalog(
    identification: Identification,
    catalog: Catalog,
    limit: int = 10,
) -> list[PriceReference]:
    matches: list[PriceReference] = []
    for record in catalog.records:
        score = 0
        for field, weight in (
            ("country", 3),
            ("denomination", 3),
            ("year", 4),
            ("mint", 2),
            ("metal", 1),
        ):
            observed = getattr(identification, field)
            stored = getattr(record, field)
            if observed is None or stored is None:
                continue
            if field == "year":
                if observed == stored:
                    score += weight
            elif _normalize(str(observed)) == _normalize(str(stored)):
                score += weight
            elif field in ("country", "denomination") and (
                _normalize(str(observed)) in _normalize(str(stored))
                or _normalize(str(stored)) in _normalize(str(observed))
            ):
                score += weight
        if score:
            matches.append(PriceReference(**record.model_dump(), match_score=score))
    matches.sort(
        key=lambda item: (
            -item.match_score,
            _source_priority(item.source),
            item.source,
            _grade_priority(item.source, item.grade),
            item.id,
        )
    )
    return matches[:limit]


def _source_priority(source: str) -> int:
    return {"numista": 0, "lefranc": 1}.get(source.casefold(), 2)


def _grade_priority(source: str, grade: str | None) -> int:
    grade_orders = {
        "numista": ("G", "VG", "F", "VF", "XF", "AU", "UNC"),
        "lefranc": ("B", "TB", "TTB", "SUP", "SPL", "FDC"),
    }
    try:
        return grade_orders[source.casefold()].index((grade or "").upper())
    except (KeyError, ValueError):
        return len(grade_orders.get(source.casefold(), ()))


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.casefold()).strip()
