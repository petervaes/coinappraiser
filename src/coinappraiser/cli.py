import argparse
import json
import sys
from pathlib import Path

from coinappraiser.catalog import CatalogUnavailableError
from coinappraiser.config import load_environment
from coinappraiser.service import MAX_IMAGE_BYTES, appraise_images
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
    parser.add_argument(
        "obverse",
        type=Path,
        help="Path to the obverse photo (JPEG, PNG, WebP, or GIF)",
    )
    parser.add_argument(
        "--reverse",
        type=Path,
        help="Optional path to the reverse photo",
    )
    args = parser.parse_args()

    paths = [args.obverse]
    if args.reverse is not None:
        paths.append(args.reverse)

    images: list[tuple[bytes, str]] = []
    for path in paths:
        content_type = CONTENT_TYPES_BY_SUFFIX.get(path.suffix.casefold())
        if content_type not in SUPPORTED_IMAGE_TYPES:
            parser.error(f"{path} must be a JPEG, PNG, WebP, or GIF")

    try:
        total_size = 0
        for path in paths:
            content_type = CONTENT_TYPES_BY_SUFFIX[path.suffix.casefold()]
            with path.open("rb") as image_file:
                image = image_file.read(MAX_IMAGE_BYTES + 1)
            total_size += len(image)
            if total_size > MAX_IMAGE_BYTES:
                raise ValueError("Combined image size exceeds the 10 MiB limit.")
            images.append((image, content_type))
        result = appraise_images(images)
    except (OSError, ValueError, VisionConfigurationError, CatalogUnavailableError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result.model_dump(mode="json"), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
