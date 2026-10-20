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
        "coinappraiser.api.appraise_image",
        lambda image, content_type: AppraisalResult(
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


def test_appraisal_rejects_oversized_upload() -> None:
    from coinappraiser.service import MAX_IMAGE_BYTES

    response = client.post(
        "/appraisals",
        files={"image": ("coin.jpg", b"x" * (MAX_IMAGE_BYTES + 1), "image/jpeg")},
    )

    assert response.status_code == 413
