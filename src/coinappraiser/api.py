from fastapi import FastAPI, File, HTTPException, UploadFile

from coinappraiser.catalog import CatalogUnavailableError
from coinappraiser.config import load_environment
from coinappraiser.models import AppraisalResult
from coinappraiser.service import MAX_IMAGE_BYTES, appraise_image
from coinappraiser.vision import (
    SUPPORTED_IMAGE_TYPES,
    VisionConfigurationError,
)

load_environment()

app = FastAPI(
    title="CoinAppraiser API",
    description="Identify a coin photo and retrieve cited catalog price references.",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/appraisals", response_model=AppraisalResult)
def create_appraisal(image: UploadFile = File(...)) -> AppraisalResult:
    if image.content_type not in SUPPORTED_IMAGE_TYPES:
        raise HTTPException(
            status_code=415,
            detail="Upload a JPEG, PNG, WebP, or GIF image.",
        )

    contents = image.file.read(MAX_IMAGE_BYTES + 1)
    if len(contents) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image exceeds the 10 MiB limit.")

    try:
        return appraise_image(contents, image.content_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except VisionConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except CatalogUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
