from fastapi import FastAPI, File, HTTPException, UploadFile

from coinappraiser.catalog import CatalogUnavailableError
from coinappraiser.config import load_environment
from coinappraiser.models import AppraisalResult
from coinappraiser.service import MAX_IMAGE_BYTES, appraise_images
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
def create_appraisal(
    image: UploadFile | None = File(default=None),
    obverse: UploadFile | None = File(default=None),
    reverse: UploadFile | None = File(default=None),
) -> AppraisalResult:
    if image is not None and (obverse is not None or reverse is not None):
        raise HTTPException(
            status_code=400,
            detail="Use either the legacy 'image' field or 'obverse'/'reverse' fields.",
        )
    if image is not None:
        uploaded_images = [image]
    elif obverse is not None:
        uploaded_images = [obverse]
        if reverse is not None:
            uploaded_images.append(reverse)
    else:
        raise HTTPException(
            status_code=422,
            detail="Upload an 'obverse' photo, optionally with a 'reverse' photo.",
        )

    images: list[tuple[bytes, str]] = []
    total_size = 0
    for uploaded in uploaded_images:
        if uploaded.content_type not in SUPPORTED_IMAGE_TYPES:
            raise HTTPException(
                status_code=415,
                detail="Upload JPEG, PNG, WebP, or GIF images.",
            )
        contents = uploaded.file.read(MAX_IMAGE_BYTES + 1)
        total_size += len(contents)
        if total_size > MAX_IMAGE_BYTES:
            raise HTTPException(
                status_code=413,
                detail="Combined image size exceeds the 10 MiB limit.",
            )
        images.append((contents, uploaded.content_type))

    try:
        return appraise_images(images)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except VisionConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except CatalogUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
