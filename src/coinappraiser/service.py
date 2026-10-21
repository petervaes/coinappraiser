from coinappraiser.catalog import load_catalog, search_catalog
from coinappraiser.models import AppraisalResult, NumistaValue
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

    analysis = identify_coin(images)
    identification = analysis.identification
    matches = search_catalog(identification, load_catalog())
    exact_identity = (
        identification.country is not None
        and identification.denomination is not None
        and identification.year is not None
    )
    numista_record = next(
        (
            record
            for record in matches
            if exact_identity
            and record.source.casefold() == "numista"
            and record.grade == analysis.condition_assessment.grade
            and record.price is not None
            and record.currency is not None
            and _normalize(record.country) == _normalize(identification.country)
            and _normalize(record.denomination)
            == _normalize(identification.denomination)
            and record.year == identification.year
        ),
        None,
    )
    if numista_record is not None:
        numista_value = NumistaValue(
            grade=analysis.condition_assessment.grade,
            price=numista_record.price,
            currency=numista_record.currency,
            source_url=numista_record.url,
            catalog_reference=numista_record.catalog_reference,
            price_date=numista_record.price_date,
        )
        numista_value_note = (
            "Exact Numista grade match; this is a catalog reference, not a "
            "certified appraisal or guaranteed sale price."
        )
    else:
        numista_value = None
        grade = analysis.condition_assessment.grade
        numista_value_note = (
            f"No exact Numista price is cataloged for grade {grade}."
            if grade is not None
            else "No Numista price selected because the photo-based grade is uncertain."
        )

    return AppraisalResult(
        numista_value=numista_value,
        numista_value_note=numista_value_note,
        condition_assessment=analysis.condition_assessment,
        identification=identification,
        price_references=matches,
        valuation_note=(
            "No matching catalog references were found."
            if not matches
            else "Prices are source references, not a condition-adjusted "
            "appraisal or guaranteed market value."
        ),
    )


def _normalize(value: str | None) -> str:
    return " ".join((value or "").casefold().split())
