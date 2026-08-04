"""Logo validation, sizing, positioning, and compositing for CPIT Signage."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, UnidentifiedImageError

SUPPORTED_LOGO_FORMATS = {
    "JPEG",
    "PNG",
    "WEBP",
}

LOGO_POSITIONS = {
    "top-left",
    "top-center",
    "top-right",
    "bottom-left",
    "bottom-center",
    "bottom-right",
}

DEFAULT_POSITION = "top-right"
DEFAULT_WIDTH_PERCENT = 18
DEFAULT_MARGIN = 70


class LogoProcessingError(Exception):
    """Raised when a logo cannot be loaded, validated, or composited."""


def load_logo(path: Path) -> Image.Image:
    """
    Load a supported logo and return an RGBA image.

    PNG and WebP transparency is preserved. JPEG files are converted
    to RGBA with a fully opaque alpha channel.
    """
    if not path.is_file():
        raise LogoProcessingError(
            f"Logo file was not found: {path}"
        )

    try:
        with Image.open(path) as source:
            if source.format not in SUPPORTED_LOGO_FORMATS:
                raise LogoProcessingError(
                    "Logo must be a JPEG, PNG, or WebP image."
                )

            source.load()

            if source.width <= 0 or source.height <= 0:
                raise LogoProcessingError(
                    "The logo has invalid dimensions."
                )

            return source.convert("RGBA")

    except UnidentifiedImageError as error:
        raise LogoProcessingError(
            "The selected logo is not a valid image."
        ) from error

    except OSError as error:
        raise LogoProcessingError(
            "The selected logo could not be opened."
        ) from error


def normalize_position(position: str) -> str:
    """Return a supported logo position."""
    normalized = (position or DEFAULT_POSITION).strip().lower()

    if normalized not in LOGO_POSITIONS:
        return DEFAULT_POSITION

    return normalized


def normalize_width_percent(width_percent: int) -> int:
    """
    Validate the requested logo width as a percentage of slide width.

    The supported range is 5 through 40 percent.
    """
    try:
        normalized = int(width_percent)
    except (TypeError, ValueError) as error:
        raise LogoProcessingError(
            "Logo width must be an integer."
        ) from error

    if normalized < 5 or normalized > 40:
        raise LogoProcessingError(
            "Logo width must be between 5 and 40 percent."
        )

    return normalized


def fit_logo(
    logo: Image.Image,
    *,
    slide_width: int,
    slide_height: int,
    width_percent: int = DEFAULT_WIDTH_PERCENT,
    maximum_height_percent: int = 24,
) -> Image.Image:
    """
    Resize a logo while preserving its aspect ratio.

    Width is based on a percentage of slide width. Height is also
    capped to prevent unusually tall logos from dominating the sign.
    """
    if slide_width <= 0 or slide_height <= 0:
        raise LogoProcessingError(
            "Slide dimensions must be positive."
        )

    normalized_width = normalize_width_percent(width_percent)

    if maximum_height_percent < 5 or maximum_height_percent > 50:
        raise LogoProcessingError(
            "Maximum logo height must be between 5 and 50 percent."
        )

    target_width = max(
        1,
        round(slide_width * normalized_width / 100),
    )

    maximum_height = max(
        1,
        round(slide_height * maximum_height_percent / 100),
    )

    source_width, source_height = logo.size

    scale = min(
        target_width / source_width,
        maximum_height / source_height,
    )

    resized_width = max(1, round(source_width * scale))
    resized_height = max(1, round(source_height * scale))

    return logo.resize(
        (resized_width, resized_height),
        Image.Resampling.LANCZOS,
    )


def calculate_logo_position(
    *,
    slide_width: int,
    slide_height: int,
    logo_width: int,
    logo_height: int,
    position: str = DEFAULT_POSITION,
    margin: int = DEFAULT_MARGIN,
) -> tuple[int, int]:
    """Calculate the upper-left paste coordinates for a logo."""
    if margin < 0:
        raise LogoProcessingError(
            "Logo margin cannot be negative."
        )

    normalized_position = normalize_position(position)

    if normalized_position.endswith("left"):
        x_position = margin
    elif normalized_position.endswith("right"):
        x_position = slide_width - logo_width - margin
    else:
        x_position = (slide_width - logo_width) // 2

    if normalized_position.startswith("bottom"):
        y_position = slide_height - logo_height - margin
    else:
        y_position = margin

    return (
        max(0, x_position),
        max(0, y_position),
    )


def apply_logo(
    canvas: Image.Image,
    *,
    logo_path: Path,
    position: str = DEFAULT_POSITION,
    width_percent: int = DEFAULT_WIDTH_PERCENT,
    margin: int = DEFAULT_MARGIN,
) -> Image.Image:
    """
    Composite a logo onto a copy of the supplied canvas.

    The returned image uses RGBA internally so transparent logos are
    blended correctly. Callers may convert the final result to RGB
    before saving as JPEG or PNG.
    """
    if canvas.width <= 0 or canvas.height <= 0:
        raise LogoProcessingError(
            "The sign canvas has invalid dimensions."
        )

    result = canvas.convert("RGBA")
    logo = load_logo(logo_path)

    fitted_logo = fit_logo(
        logo,
        slide_width=result.width,
        slide_height=result.height,
        width_percent=width_percent,
    )

    x_position, y_position = calculate_logo_position(
        slide_width=result.width,
        slide_height=result.height,
        logo_width=fitted_logo.width,
        logo_height=fitted_logo.height,
        position=position,
        margin=margin,
    )

    result.alpha_composite(
        fitted_logo,
        dest=(x_position, y_position),
    )

    return result
