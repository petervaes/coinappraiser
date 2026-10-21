import base64
import os

from openai import OpenAI
from pydantic import BaseModel

from coinappraiser.models import ConditionAssessment, Identification

SUPPORTED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


class VisionConfigurationError(Exception):
    """Raised when image identification is not configured."""


class CoinAnalysis(BaseModel):
    identification: Identification
    condition_assessment: ConditionAssessment


def identify_coin(images: list[tuple[bytes, str]]) -> CoinAnalysis:
    if not images:
        raise ValueError("At least one coin photo is required.")
    if len(images) > 2:
        raise ValueError("Upload no more than two coin photos.")

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise VisionConfigurationError("Set OPENAI_API_KEY to identify coin photos.")

    content = [
        {
            "type": "input_text",
            "text": (
                "Identify and cautiously assess the coin from the supplied photo or "
                "photos. If two images are provided, they show the obverse and reverse "
                "of the same coin; use both views together. Report only visible or "
                "well-supported identity attributes. Do not estimate or infer a price. "
                "Assess the visible grade using the Numista scale G, VG, F, VF, XF, AU, "
                "UNC. Base the grade on wear of the highest design points and retained "
                "details on both sides; use the worse-preserved side. Describe the "
                "specific visible wear/details that justify the grade. Do not infer "
                "grade from color alone. If image quality or views do not support a "
                "defensible grade, set grade to null and explain why. Confidence is "
                "about the photo-based assessment, not a professional certification."
            ),
        }
    ]
    for image, content_type in images:
        if content_type not in SUPPORTED_IMAGE_TYPES:
            raise ValueError(f"Unsupported image type: {content_type}")
        if not image:
            raise ValueError("The uploaded image is empty.")
        image_data = base64.b64encode(image).decode("ascii")
        content.append(
            {
                "type": "input_image",
                "image_url": f"data:{content_type};base64,{image_data}",
            }
        )

    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        input=[
            {
                "role": "user",
                "content": content,
            }
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "coin_identification",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "identification": {
                            "type": "object",
                            "properties": {
                                "country": {"type": ["string", "null"]},
                                "denomination": {"type": ["string", "null"]},
                                "year": {"type": ["integer", "null"]},
                                "mint": {"type": ["string", "null"]},
                                "metal": {"type": ["string", "null"]},
                                "description": {"type": "string"},
                                "confidence": {"type": "number"},
                            },
                            "required": [
                                "country",
                                "denomination",
                                "year",
                                "mint",
                                "metal",
                                "description",
                                "confidence",
                            ],
                            "additionalProperties": False,
                        },
                        "condition_assessment": {
                            "type": "object",
                            "properties": {
                                "grade": {
                                    "type": ["string", "null"],
                                    "enum": [
                                        "G",
                                        "VG",
                                        "F",
                                        "VF",
                                        "XF",
                                        "AU",
                                        "UNC",
                                        None,
                                    ],
                                },
                                "observed_wear": {"type": "string"},
                                "rationale": {"type": "string"},
                                "confidence": {"type": "number"},
                            },
                            "required": [
                                "grade",
                                "observed_wear",
                                "rationale",
                                "confidence",
                            ],
                            "additionalProperties": False,
                        },
                    },
                    "required": ["identification", "condition_assessment"],
                    "additionalProperties": False,
                },
            }
        },
    )
    return CoinAnalysis.model_validate_json(response.output_text)
