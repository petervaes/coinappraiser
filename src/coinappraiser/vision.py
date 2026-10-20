import base64
import os

from openai import OpenAI

from coinappraiser.models import Identification

SUPPORTED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


class VisionConfigurationError(Exception):
    """Raised when image identification is not configured."""


def identify_coin(image: bytes, content_type: str) -> Identification:
    if content_type not in SUPPORTED_IMAGE_TYPES:
        raise ValueError(f"Unsupported image type: {content_type}")

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise VisionConfigurationError("Set OPENAI_API_KEY to identify coin photos.")

    image_data = base64.b64encode(image).decode("ascii")
    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            "Identify the coin from this photo. Report only visible "
                            "or well-supported attributes. Do not estimate a price. "
                            "Use null for uncertain country, denomination, year, mint, "
                            "or metal. Give confidence from 0 to 1."
                        ),
                    },
                    {
                        "type": "input_image",
                        "image_url": (
                            f"data:{content_type};base64,{image_data}"
                        ),
                    },
                ],
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
            }
        },
    )
    return Identification.model_validate_json(response.output_text)
