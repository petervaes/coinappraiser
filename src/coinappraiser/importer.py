import argparse
import json
import re
import sys
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from coinappraiser.models import Catalog, CatalogRecord

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE_DIR = PROJECT_ROOT / "catalog" / "sources"
DEFAULT_OUTPUT = PROJECT_ROOT / "catalog" / "catalog.json"
ALLOWED_SOURCES = {"numista", "lefranc"}


class SourcePrice(BaseModel):
    model_config = ConfigDict(extra="forbid")

    grade: str
    price: float = Field(ge=0)
    currency: str


class SourceEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str
    url: str
    catalog_reference: str
    prices: list[SourcePrice]
    mintage: int | None = Field(default=None, ge=0)
    price_date: int | None = Field(default=None, ge=1)


class SourceBundle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    country: str
    denomination: str
    year: int
    mint: str | None = None
    metal: str | None = None
    variant: str
    sources: list[SourceEntry]


def import_sources(source_dir: Path, output_path: Path) -> Catalog:
    records: list[CatalogRecord] = []
    record_ids: set[str] = set()

    source_files = sorted(source_dir.glob("*.json"))
    if not source_files:
        raise ValueError(f"No source JSON files found in {source_dir}")

    for source_file in source_files:
        bundle = SourceBundle.model_validate_json(source_file.read_text(encoding="utf-8"))
        for entry in bundle.sources:
            source = entry.source.casefold()
            if source not in ALLOWED_SOURCES:
                raise ValueError(
                    f"Unsupported source {entry.source!r} in {source_file.name}"
                )
            if not entry.url.startswith("https://"):
                raise ValueError(
                    f"Source URL must use HTTPS in {source_file.name}: {entry.url}"
                )
            if not entry.prices:
                raise ValueError(f"No prices supplied for {source} in {source_file.name}")

            for price in entry.prices:
                record_id = _record_id(
                    source,
                    bundle.country,
                    bundle.denomination,
                    bundle.year,
                    price.grade,
                )
                if record_id in record_ids:
                    raise ValueError(f"Duplicate catalog record id: {record_id}")
                record_ids.add(record_id)
                records.append(
                    CatalogRecord(
                        id=record_id,
                        title=(
                            f"{bundle.country} {bundle.denomination} "
                            f"{bundle.year} {bundle.variant}"
                        ),
                        source=source,
                        url=entry.url,
                        country=bundle.country,
                        denomination=bundle.denomination,
                        year=bundle.year,
                        mint=bundle.mint,
                        metal=bundle.metal,
                        grade=price.grade,
                        price=price.price,
                        currency=price.currency,
                        catalog_reference=entry.catalog_reference,
                        mintage=entry.mintage,
                        price_date=entry.price_date,
                    )
                )

    catalog = Catalog(records=records)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(catalog.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return catalog


def _record_id(
    source: str,
    country: str,
    denomination: str,
    year: int,
    grade: str,
) -> str:
    slug = "-".join((country, denomination, str(year), grade)).casefold()
    slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
    return f"{source}-{slug}"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build the price-reference catalog from reviewed source records."
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=DEFAULT_SOURCE_DIR,
        help=f"Folder containing reviewed source JSON files (default: {DEFAULT_SOURCE_DIR})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Catalog output path (default: {DEFAULT_OUTPUT})",
    )
    args = parser.parse_args()

    try:
        catalog = import_sources(args.source_dir, args.output)
    except (OSError, ValidationError, ValueError, json.JSONDecodeError) as exc:
        print(f"Catalog import failed: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote {len(catalog.records)} source price records to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
