from coinappraiser.catalog import load_catalog, search_catalog
from coinappraiser.models import AppraisalResult
from coinappraiser.vision import identify_coin

MAX_IMAGE_BYTES = 10 * 1024 * 1024


def appraise_image(image: bytes, content_type: str) -> AppraisalResult:
    if not image:
        raise ValueError("The uploaded image is empty.")
    if len(image) > MAX_IMAGE_BYTES:
        raise ValueError("The uploaded image exceeds the 10 MiB limit.")

    identification = identify_coin(image, content_type)
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
