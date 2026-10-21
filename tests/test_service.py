import pytest

from coinappraiser import service
from coinappraiser.catalog import Catalog
from coinappraiser.models import Identification


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
    monkeypatch.setattr(service, "identify_coin", lambda images: identification)
    monkeypatch.setattr(service, "load_catalog", lambda: Catalog(records=[]))

    result = service.appraise_image(b"image", "image/jpeg")

    assert result.identification == identification
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
        lambda images: (received_images.extend(images), identification)[1],
    )
    monkeypatch.setattr(service, "load_catalog", lambda: Catalog(records=[]))

    service.appraise_images(
        [(b"obverse", "image/jpeg"), (b"reverse", "image/png")]
    )

    assert received_images == [
        (b"obverse", "image/jpeg"),
        (b"reverse", "image/png"),
    ]


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
