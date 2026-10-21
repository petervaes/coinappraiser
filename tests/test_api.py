from fastapi.testclient import TestClient

from coinappraiser.api import app
from coinappraiser.models import AppraisalResult, Identification, PriceReference

client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_appraisal_rejects_unsupported_upload_type() -> None:
    response = client.post(
        "/appraisals",
        files={"image": ("coin.txt", b"not an image", "text/plain")},
    )

    assert response.status_code == 415


def test_appraisal_reports_missing_vision_configuration(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    response = client.post(
        "/appraisals",
        files={"image": ("coin.jpg", b"image data", "image/jpeg")},
    )

    assert response.status_code == 503
    assert "OPENAI_API_KEY" in response.json()["detail"]


def test_appraisal_returns_source_price_references(monkeypatch) -> None:
    monkeypatch.setattr(
        "coinappraiser.api.appraise_images",
        lambda images: AppraisalResult(
            identification=Identification(
                country="France",
                denomination="1 franc",
                year=1900,
                mint=None,
                metal="silver",
                description="French coin",
                confidence=0.9,
            ),
            price_references=[
                PriceReference(
                    id="numista-1",
                    title="French 1 franc",
                    source="numista",
                    url="https://en.numista.com/",
                    country="France",
                    denomination="1 franc",
                    year=1900,
                    grade="VF",
                    price=12,
                    currency="EUR",
                    match_score=10,
                )
            ],
            valuation_note="Prices are source references.",
        ),
    )

    response = client.post(
        "/appraisals",
        files={"image": ("coin.jpg", b"image data", "image/jpeg")},
    )

    assert response.status_code == 200
    assert response.json()["price_references"][0]["url"] == "https://en.numista.com/"
    assert response.json()["price_references"][0]["price"] == 12


def test_appraisal_accepts_obverse_and_reverse_together(monkeypatch) -> None:
    received_images = []

    def fake_appraise(images):
        received_images.extend(images)
        return AppraisalResult(
            identification=Identification(
                country="France",
                denomination="1 franc",
                year=1935,
                mint=None,
                metal=None,
                description="French 1 franc Morlon",
                confidence=0.95,
            ),
            price_references=[],
            valuation_note="No matching catalog references were found.",
        )

    monkeypatch.setattr("coinappraiser.api.appraise_images", fake_appraise)
    response = client.post(
        "/appraisals",
        files=[
            ("obverse", ("front.jpg", b"front", "image/jpeg")),
            ("reverse", ("back.jpg", b"back", "image/jpeg")),
        ],
    )

    assert response.status_code == 200
    assert received_images == [
        (b"front", "image/jpeg"),
        (b"back", "image/jpeg"),
    ]
    assert response.json()["identification"]["year"] == 1935


def test_appraisal_rejects_reverse_without_obverse() -> None:
    response = client.post(
        "/appraisals",
        files={"reverse": ("back.jpg", b"back", "image/jpeg")},
    )

    assert response.status_code == 422


def test_appraisal_rejects_mixed_legacy_and_two_side_fields() -> None:
    response = client.post(
        "/appraisals",
        files=[
            ("image", ("coin.jpg", b"single", "image/jpeg")),
            ("obverse", ("front.jpg", b"front", "image/jpeg")),
        ],
    )

    assert response.status_code == 400


def test_appraisal_rejects_oversized_upload() -> None:
    from coinappraiser.service import MAX_IMAGE_BYTES

    response = client.post(
        "/appraisals",
        files={"image": ("coin.jpg", b"x" * (MAX_IMAGE_BYTES + 1), "image/jpeg")},
    )

    assert response.status_code == 413


def test_appraisal_rejects_combined_oversized_upload() -> None:
    from coinappraiser.service import MAX_IMAGE_BYTES

    half = MAX_IMAGE_BYTES // 2
    response = client.post(
        "/appraisals",
        files=[
            ("obverse", ("front.jpg", b"x" * half, "image/jpeg")),
            ("reverse", ("back.jpg", b"x" * (half + 1), "image/jpeg")),
        ],
    )

    assert response.status_code == 413
