import argparse
import json
import sys
from pathlib import Path

from coinappraiser.catalog import CatalogUnavailableError
from coinappraiser.config import load_environment
from coinappraiser.service import MAX_IMAGE_BYTES, appraise_image
from coinappraiser.vision import (
    SUPPORTED_IMAGE_TYPES,
    VisionConfigurationError,
)

CONTENT_TYPES_BY_SUFFIX = {
    ".gif": "image/gif",
    ".jpeg": "image/jpeg",
    ".jpg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}


def main() -> int:
    load_environment()
    parser = argparse.ArgumentParser(
        description="Identify a coin photo and retrieve catalog price references."
    )
    parser.add_argument("image", type=Path, help="Path to a JPEG, PNG, WebP, or GIF")
    args = parser.parse_args()

    content_type = CONTENT_TYPES_BY_SUFFIX.get(args.image.suffix.casefold())
    if content_type not in SUPPORTED_IMAGE_TYPES:
        parser.error("image must be a JPEG, PNG, WebP, or GIF")

    try:
        with args.image.open("rb") as image_file:
            image = image_file.read(MAX_IMAGE_BYTES + 1)
        result = appraise_image(image, content_type)
    except (OSError, ValueError, VisionConfigurationError, CatalogUnavailableError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result.model_dump(mode="json"), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
