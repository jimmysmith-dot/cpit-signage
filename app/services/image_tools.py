"""Reusable image-processing helpers for CPIT Signage."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, UnidentifiedImageError

SUPPORTED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}


class ImageProcessingError(Exception):
    """Raised when an image cannot be loaded or prepared."""


def load_image(path: Path) -> Image.Image:
    """Load a supported image and convert it to RGB."""
    if not path.is_file():
        raise ImageProcessingError(
            f"Background image was not found: {path}"
        )

    try:
        with Image.open(path) as source:
            if source.format not in SUPPORTED_IMAGE_FORMATS:
                raise ImageProcessingError(
                    "Background image must be JPEG, PNG, or WebP."
                )

            source.load()
            return source.convert("RGB")

    except UnidentifiedImageError as error:
        raise ImageProcessingError(
            "The selected background file is not a valid image."
        ) from error

    except OSError as error:
        raise ImageProcessingError(
            "The selected background image could not be opened."
        ) from error


def crop_to_fill(
    image: Image.Image,
    target_width: int,
    target_height: int,
) -> Image.Image:
    """Resize and center-crop an image to completely fill a target."""
    if target_width <= 0 or target_height <= 0:
        raise ImageProcessingError(
            "Target dimensions must be positive."
        )

    source_width, source_height = image.size

    if source_width <= 0 or source_height <= 0:
        raise ImageProcessingError(
            "The background image has invalid dimensions."
        )

    scale = max(
        target_width / source_width,
        target_height / source_height,
    )

    resized_width = max(1, round(source_width * scale))
    resized_height = max(1, round(source_height * scale))

    resized = image.resize(
        (resized_width, resized_height),
        Image.Resampling.LANCZOS,
    )

    left = max(0, (resized_width - target_width) // 2)
    top = max(0, (resized_height - target_height) // 2)

    return resized.crop(
        (
            left,
            top,
            left + target_width,
            top + target_height,
        )
    )


def apply_dark_overlay(
    image: Image.Image,
    opacity_percent: int,
) -> Image.Image:
    """Apply a black overlay using an opacity from 0 through 100."""
    try:
        opacity = int(opacity_percent)
    except (TypeError, ValueError) as error:
        raise ImageProcessingError(
            "Overlay opacity must be an integer."
        ) from error

    opacity = max(0, min(opacity, 100))

    if opacity == 0:
        return image.copy()

    overlay = Image.new(
        "RGB",
        image.size,
        color=(0, 0, 0),
    )

    return Image.blend(
        image,
        overlay,
        opacity / 100,
    )


def prepare_background(
    *,
    image_path: Path,
    target_width: int,
    target_height: int,
    overlay_opacity: int = 35,
) -> Image.Image:
    """Load, crop, and darken a background image for a sign."""
    image = load_image(image_path)

    fitted = crop_to_fill(
        image,
        target_width,
        target_height,
    )

    return apply_dark_overlay(
        fitted,
        overlay_opacity,
    )
