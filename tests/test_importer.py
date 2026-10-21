import json
from pathlib import Path

from coinappraiser.importer import DEFAULT_SOURCE_DIR, import_sources
from coinappraiser.models import Identification
from coinappraiser.catalog import search_catalog


def test_import_sources_builds_reviewed_records_with_source_provenance(tmp_path) -> None:
    output = tmp_path / "catalog.json"

    catalog = import_sources(DEFAULT_SOURCE_DIR, output)

    assert len(catalog.records) == 9
    assert json.loads(output.read_text(encoding="utf-8"))["records"]
    numista_f = next(
        record
        for record in catalog.records
        if record.source == "numista" and record.grade == "F"
    )
    lefranc_fdc = next(
        record
        for record in catalog.records
        if record.source == "lefranc" and record.grade == "FDC"
    )
    assert numista_f.price == 12
    assert numista_f.mintage == 1166038
    assert numista_f.catalog_reference == "Franc 2014 #219/6"
    assert lefranc_fdc.price == 500
    assert lefranc_fdc.price_date == 2017
    assert lefranc_fdc.catalog_reference == "F.219/6"

    identification = Identification(
        country="France",
        denomination="1 franc",
        year=1935,
        mint=None,
        metal=None,
        description="1 franc Morlon",
        confidence=0.95,
    )
    matches = search_catalog(identification, catalog)
    assert [record.source for record in matches[:3]] == [
        "numista",
        "numista",
        "numista",
    ]
    assert len(matches) == 9
    assert [record.grade for record in matches] == [
        "F",
        "VF",
        "XF",
        "B",
        "TB",
        "TTB",
        "SUP",
        "SPL",
        "FDC",
    ]


def test_import_sources_rejects_non_https_source_url(tmp_path) -> None:
    source_dir = tmp_path / "sources"
    source_dir.mkdir()
    (source_dir / "invalid.json").write_text(
        json.dumps(
            {
                "country": "France",
                "denomination": "1 franc",
                "year": 1935,
                "variant": "Morlon",
                "sources": [
                    {
                        "source": "numista",
                        "url": "http://example.test/coin",
                        "catalog_reference": "test",
                        "prices": [{"grade": "F", "price": 1, "currency": "EUR"}],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    try:
        import_sources(source_dir, tmp_path / "output.json")
    except ValueError as exc:
        assert "HTTPS" in str(exc)
    else:
        raise AssertionError("An insecure source URL should be rejected.")
