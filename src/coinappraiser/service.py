from coinappraiser.catalog import load_catalog, search_catalog
from coinappraiser.models import AppraisalResult
from coinappraiser.vision import identify_coin

MAX_IMAGE_BYTES = 10 * 1024 * 1024


def appraise_image(image: bytes, content_type: str) -> AppraisalResult:
    return appraise_images([(image, content_type)])


def appraise_images(images: list[tuple[bytes, str]]) -> AppraisalResult:
    if not images:
        raise ValueError("At least one coin photo is required.")
    if len(images) > 2:
        raise ValueError("Upload no more than two coin photos.")
    if any(not image for image, _ in images):
        raise ValueError("The uploaded image is empty.")
    if sum(len(image) for image, _ in images) > MAX_IMAGE_BYTES:
        raise ValueError("The uploaded image exceeds the 10 MiB limit.")

    identification = identify_coin(images)
    matches = search_catalog(identification, load_catalog())
    return AppraisalResult(
        identification=identification,
        price_references=matches,
        valuation_note=(
            "No matching catalog references were found."
            if not matches
            else "Prices are source references, not a condition-adjusted "
            "appraisal or guaranteed market value."
        ),
    )
