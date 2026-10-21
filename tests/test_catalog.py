from coinappraiser.catalog import search_catalog
from coinappraiser.models import Catalog, CatalogRecord, Identification


def test_search_returns_matching_records_in_score_order() -> None:
    catalog = Catalog(
        records=[
            CatalogRecord(
                id="partial",
                title="French coin",
                source="numista",
                url="https://en.numista.com/",
                country="France",
                year=1900,
                price=10,
                currency="EUR",
            ),
            CatalogRecord(
                id="exact",
                title="French 1 franc",
                source="lefranc",
                url="https://example.test/coin",
                country="France",
                denomination="1 franc",
                year=1900,
                mint="Paris",
                metal="silver",
                grade="VF",
                price=12,
                currency="EUR",
            ),
        ]
    )
    identification = Identification(
        country="France",
        denomination="1 franc",
        year=1900,
        mint="Paris",
        metal="silver",
        description="French silver coin",
        confidence=0.9,
    )

    results = search_catalog(identification, catalog)

    assert [record.id for record in results] == ["exact", "partial"]
    assert results[0].match_score > results[1].match_score
    assert results[0].price == 12
    assert results[0].source == "lefranc"


def test_search_does_not_return_records_without_matching_fields() -> None:
    catalog = Catalog(
        records=[
            CatalogRecord(
                id="unrelated",
                title="Unrelated coin",
                source="numista",
                url="https://en.numista.com/",
                country="Japan",
                year=2000,
            )
        ]
    )
    identification = Identification(
        country="France",
        denomination=None,
        year=1900,
        mint=None,
        metal=None,
        description="French coin",
        confidence=0.8,
    )

    assert search_catalog(identification, catalog) == []


def test_search_uses_partial_country_and_denomination_matches() -> None:
    catalog = Catalog(
        records=[
            CatalogRecord(
                id="record",
                title="French coin",
                source="lefranc",
                url="https://example.test/coin",
                country="French Republic",
                denomination="1 franc",
            )
        ]
    )
    identification = Identification(
        country="French",
        denomination="franc",
        year=None,
        mint=None,
        metal=None,
        description="French franc",
        confidence=0.7,
    )

    assert search_catalog(identification, catalog)[0].id == "record"


def test_search_prefers_numista_when_match_scores_are_equal() -> None:
    catalog = Catalog(
        records=[
            CatalogRecord(
                id="lefranc",
                title="French 1 franc",
                source="lefranc",
                url="https://example.test/lefranc",
                country="France",
                denomination="1 franc",
                year=1935,
                grade="TTB",
                price=45,
                currency="EUR",
            ),
            CatalogRecord(
                id="numista",
                title="French 1 franc",
                source="numista",
                url="https://example.test/numista",
                country="France",
                denomination="1 franc",
                year=1935,
                grade="VF",
                price=15,
                currency="EUR",
            ),
        ]
    )
    identification = Identification(
        country="France",
        denomination="1 franc",
        year=1935,
        mint=None,
        metal=None,
        description="French coin",
        confidence=0.9,
    )

    results = search_catalog(identification, catalog)

    assert [record.source for record in results] == ["numista", "lefranc"]
