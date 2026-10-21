import pytest

from coinappraiser import service
from coinappraiser.catalog import Catalog
from coinappraiser.models import ConditionAssessment, Identification
from coinappraiser.vision import CoinAnalysis


def test_appraise_image_returns_explicit_no_reference_note(monkeypatch) -> None:
    identification = Identification(
        country="France",
        denomination="1 franc",
        year=1900,
        mint=None,
        metal="silver",
        description="French coin",
        confidence=0.9,
    )
    monkeypatch.setattr(
        service,
        "identify_coin",
        lambda images: CoinAnalysis(
            identification=identification,
            condition_assessment=ConditionAssessment(
                grade="VF",
                observed_wear="Visible wear on raised details",
                rationale="Raised detail remains but shows circulation wear",
                confidence=0.8,
            ),
        ),
    )
    monkeypatch.setattr(service, "load_catalog", lambda: Catalog(records=[]))

    result = service.appraise_image(b"image", "image/jpeg")

    assert result.identification == identification
    assert result.condition_assessment.grade == "VF"
    assert result.numista_value is None
    assert result.price_references == []
    assert result.valuation_note == "No matching catalog references were found."


def test_appraise_images_passes_both_coin_sides_to_identification(monkeypatch) -> None:
    identification = Identification(
        country="France",
        denomination="1 franc",
        year=1935,
        mint=None,
        metal=None,
        description="French coin",
        confidence=0.95,
    )
    received_images = []
    monkeypatch.setattr(
        service,
        "identify_coin",
        lambda images: (
            received_images.extend(images),
            CoinAnalysis(
                identification=identification,
                condition_assessment=ConditionAssessment(
                    grade="VF",
                    observed_wear="Some wear",
                    rationale="Details remain visible",
                    confidence=0.7,
                ),
            ),
        )[1],
    )
    monkeypatch.setattr(service, "load_catalog", lambda: Catalog(records=[]))

    service.appraise_images(
        [(b"obverse", "image/jpeg"), (b"reverse", "image/png")]
    )

    assert received_images == [
        (b"obverse", "image/jpeg"),
        (b"reverse", "image/png"),
    ]


def test_appraise_images_returns_exact_condition_numista_value(monkeypatch) -> None:
    identification = Identification(
        country="France",
        denomination="1 franc",
        year=1935,
        mint=None,
        metal="brass",
        description="French 1 franc Morlon",
        confidence=0.95,
    )
    condition = ConditionAssessment(
        grade="VF",
        observed_wear="Moderate wear, central details remain",
        rationale="The high points are worn but the main design is clear",
        confidence=0.8,
    )
    monkeypatch.setattr(
        service,
        "identify_coin",
        lambda images: CoinAnalysis(
            identification=identification,
            condition_assessment=condition,
        ),
    )
    monkeypatch.setattr(service, "load_catalog", lambda: Catalog.model_validate({
        "records": [
            {
                "id": "numista-vf",
                "title": "French 1 franc 1935",
                "source": "numista",
                "url": "https://en.numista.com/707",
                "country": "France",
                "denomination": "1 franc",
                "year": 1935,
                "grade": "VF",
                "price": 15,
                "currency": "EUR",
                "catalog_reference": "Franc 2014 #219/6",
            },
            {
                "id": "numista-xf",
                "title": "French 1 franc 1935",
                "source": "numista",
                "url": "https://en.numista.com/707",
                "country": "France",
                "denomination": "1 franc",
                "year": 1935,
                "grade": "XF",
                "price": 19,
                "currency": "EUR",
            },
            {
                "id": "lefranc-vf",
                "title": "French 1 franc 1935",
                "source": "lefranc",
                "url": "https://www.lefranc.net/monnaie,1-franc-morlon,219.html",
                "country": "France",
                "denomination": "1 franc",
                "year": 1935,
                "grade": "VF",
                "price": 80,
                "currency": "EUR",
            },
        ]
    }))

    result = service.appraise_images([(b"front", "image/jpeg"), (b"back", "image/jpeg")])

    assert result.numista_value is not None
    assert result.numista_value.grade == "VF"
    assert result.numista_value.price == 15
    assert result.numista_value.source_url == "https://en.numista.com/707"
    assert result.condition_assessment.rationale.startswith("The high points")
    assert "Exact Numista grade match" in result.numista_value_note


def test_appraise_images_does_not_infer_nearest_numista_grade(monkeypatch) -> None:
    identification = Identification(
        country="France",
        denomination="1 franc",
        year=1935,
        mint=None,
        metal=None,
        description="French coin",
        confidence=0.9,
    )
    monkeypatch.setattr(
        service,
        "identify_coin",
        lambda images: CoinAnalysis(
            identification=identification,
            condition_assessment=ConditionAssessment(
                grade="AU",
                observed_wear="Only slight wear visible",
                rationale="Details are sharp",
                confidence=0.7,
            ),
        ),
    )
    monkeypatch.setattr(service, "load_catalog", lambda: Catalog.model_validate({
        "records": [
            {
                "id": "numista-xf",
                "title": "French 1 franc 1935",
                "source": "numista",
                "url": "https://en.numista.com/707",
                "country": "France",
                "denomination": "1 franc",
                "year": 1935,
                "grade": "XF",
                "price": 19,
                "currency": "EUR",
            }
        ]
    }))

    result = service.appraise_images([(b"front", "image/jpeg")])

    assert result.numista_value is None
    assert "No exact Numista price" in result.numista_value_note


@pytest.mark.parametrize(
    ("image", "content_type", "message"),
    [
        (b"", "image/jpeg", "empty"),
        (b"x", "image/jpeg", "10 MiB"),
    ],
)
def test_appraise_image_rejects_invalid_size(monkeypatch, image, content_type, message) -> None:
    if message == "10 MiB":
        monkeypatch.setattr(service, "MAX_IMAGE_BYTES", 0)

    with pytest.raises(ValueError, match=message):
        service.appraise_image(image, content_type)
