"""Generate image-based signage slides with Pillow."""

from __future__ import annotations

import re
from pathlib import Path
from uuid import uuid4

from PIL import Image, ImageColor, ImageDraw, ImageFont

from app.services.image_tools import (
    ImageProcessingError,
    prepare_background,
)
from app.services.logo_tools import (
    LogoProcessingError,
    apply_logo,
)

SLIDE_WIDTH = 1920
SLIDE_HEIGHT = 1080

DEFAULT_BACKGROUND = "#153A5B"
DEFAULT_TEXT_COLOR = "#FFFFFF"
DEFAULT_ACCENT_COLOR = "#75B9E6"
DEFAULT_OVERLAY_OPACITY = 35

FONT_CANDIDATES = [
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"),
    Path("/usr/share/fonts/truetype/freefont/FreeSans.ttf"),
]

BOLD_FONT_CANDIDATES = [
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    Path(
        "/usr/share/fonts/truetype/liberation2/"
        "LiberationSans-Bold.ttf"
    ),
    Path("/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"),
]


class SlideGenerationError(Exception):
    """Raised when a signage slide cannot be generated."""


def _find_font(candidates: list[Path]) -> Path:
    for candidate in candidates:
        if candidate.is_file():
            return candidate

    raise SlideGenerationError(
        "No supported TrueType font was found on the player."
    )


def _load_font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = BOLD_FONT_CANDIDATES if bold else FONT_CANDIDATES
    font_path = _find_font(candidates)

    try:
        return ImageFont.truetype(str(font_path), size=size)
    except OSError as error:
        raise SlideGenerationError(
            f"Unable to load font: {font_path}"
        ) from error


def _validate_color(value: str, fallback: str) -> str:
    candidate = (value or fallback).strip()

    try:
        ImageColor.getrgb(candidate)
    except ValueError:
        return fallback

    return candidate


def _safe_filename(title: str) -> str:
    base = re.sub(r"[^A-Za-z0-9_-]+", "-", title.strip())
    base = base.strip("-_").lower()

    if not base:
        base = "created-sign"

    return f"{base[:60]}-{uuid4().hex[:8]}.png"


def _measure_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
) -> tuple[int, int]:
    if not text:
        return 0, 0

    left, top, right, bottom = draw.textbbox(
        (0, 0),
        text,
        font=font,
    )

    return right - left, bottom - top


def _wrap_text_to_width(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    maximum_width: int,
) -> list[str]:
    """Wrap text based on rendered pixel width."""
    paragraphs = text.replace("\r\n", "\n").split("\n")
    wrapped_lines: list[str] = []

    for paragraph in paragraphs:
        paragraph = paragraph.strip()

        if not paragraph:
            wrapped_lines.append("")
            continue

        words = paragraph.split()
        current_line = ""

        for word in words:
            proposed = (
                f"{current_line} {word}"
                if current_line
                else word
            )

            width, _ = _measure_text(
                draw,
                proposed,
                font,
            )

            if width <= maximum_width:
                current_line = proposed
                continue

            if current_line:
                wrapped_lines.append(current_line)

            # Handle an unusually long single word.
            word_width, _ = _measure_text(draw, word, font)

            if word_width <= maximum_width:
                current_line = word
                continue

            character_line = ""

            for character in word:
                proposed_characters = character_line + character

                character_width, _ = _measure_text(
                    draw,
                    proposed_characters,
                    font,
                )

                if character_width <= maximum_width:
                    character_line = proposed_characters
                else:
                    if character_line:
                        wrapped_lines.append(character_line)

                    character_line = character

            current_line = character_line

        if current_line:
            wrapped_lines.append(current_line)

    return wrapped_lines


def _draw_centered_lines(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    *,
    font: ImageFont.FreeTypeFont,
    fill: str,
    center_x: int,
    start_y: int,
    line_spacing: int,
    alignment: str,
    left_margin: int,
    right_margin: int,
) -> int:
    """Draw lines and return the Y position below the last line."""
    current_y = start_y

    for line in lines:
        width, height = _measure_text(draw, line, font)

        if alignment == "left":
            x_position = left_margin
        elif alignment == "right":
            x_position = right_margin - width
        else:
            x_position = center_x - (width // 2)

        draw.text(
            (x_position, current_y),
            line,
            font=font,
            fill=fill,
        )

        current_y += max(height, font.size) + line_spacing

    return current_y



def _create_canvas(
    *,
    background_color: str,
    background_image_path: Path | None,
    overlay_opacity: int,
) -> Image.Image:
    """Create the solid-color or image-based 1920x1080 canvas."""
    if background_image_path is None:
        return Image.new(
            "RGB",
            (SLIDE_WIDTH, SLIDE_HEIGHT),
            color=background_color,
        )

    try:
        return prepare_background(
            image_path=background_image_path,
            target_width=SLIDE_WIDTH,
            target_height=SLIDE_HEIGHT,
            overlay_opacity=overlay_opacity,
        )

    except ImageProcessingError as error:
        raise SlideGenerationError(str(error)) from error

def create_sign_slide(
    *,
    output_directory: Path,
    title: str,
    body: str,
    footer: str = "",
    background_color: str = DEFAULT_BACKGROUND,
    text_color: str = DEFAULT_TEXT_COLOR,
    accent_color: str = DEFAULT_ACCENT_COLOR,
    alignment: str = "center",
    background_image_path: Path | None = None,
    overlay_opacity: int = DEFAULT_OVERLAY_OPACITY,
    logo_path: Path | None = None,
    logo_position: str = "top-right",
    logo_width_percent: int = 18,
    logo_margin: int = 70,
) -> Path:
    """
    Generate a 1920x1080 PNG sign and return its path.

    The background may be a solid color or a source image. Background
    images are center-cropped to fill the slide and can be darkened
    with an adjustable overlay. An optional logo may be composited
    before text is drawn. The output is ready for the normal media
    playlist.
    """
    title = title.strip()
    body = body.strip()
    footer = footer.strip()

    if not title and not body:
        raise SlideGenerationError(
            "A title or body message is required."
        )

    normalized_alignment = alignment.strip().lower()

    if normalized_alignment not in {"left", "center", "right"}:
        normalized_alignment = "center"

    try:
        normalized_overlay = int(overlay_opacity)
    except (TypeError, ValueError) as error:
        raise SlideGenerationError(
            "Overlay opacity must be an integer."
        ) from error

    if normalized_overlay < 0 or normalized_overlay > 100:
        raise SlideGenerationError(
            "Overlay opacity must be between 0 and 100."
        )

    background_color = _validate_color(
        background_color,
        DEFAULT_BACKGROUND,
    )

    text_color = _validate_color(
        text_color,
        DEFAULT_TEXT_COLOR,
    )

    accent_color = _validate_color(
        accent_color,
        DEFAULT_ACCENT_COLOR,
    )

    output_directory.mkdir(parents=True, exist_ok=True)

    filename = _safe_filename(title or "created-sign")
    output_path = output_directory / filename

    image = _create_canvas(
        background_color=background_color,
        background_image_path=background_image_path,
        overlay_opacity=normalized_overlay,
    )

    if logo_path is not None:
        try:
            image = apply_logo(
                image,
                logo_path=logo_path,
                position=logo_position,
                width_percent=logo_width_percent,
                margin=logo_margin,
            )
        except LogoProcessingError as error:
            raise SlideGenerationError(str(error)) from error

    draw = ImageDraw.Draw(image)

    title_font = _load_font(104, bold=True)
    body_font = _load_font(60)
    footer_font = _load_font(38)

    left_margin = 170
    right_margin = SLIDE_WIDTH - 170
    content_width = right_margin - left_margin
    center_x = SLIDE_WIDTH // 2

    # Accent bar across the top.
    draw.rectangle(
        (
            0,
            0,
            SLIDE_WIDTH,
            26,
        ),
        fill=accent_color,
    )

    title_lines = _wrap_text_to_width(
        draw,
        title,
        title_font,
        content_width,
    ) if title else []

    body_lines = _wrap_text_to_width(
        draw,
        body,
        body_font,
        content_width,
    ) if body else []

    title_line_height = title_font.size + 22
    body_line_height = body_font.size + 22

    title_block_height = len(title_lines) * title_line_height
    body_block_height = len(body_lines) * body_line_height

    block_spacing = 55 if title_lines and body_lines else 0

    available_top = 130
    available_bottom = 890 if footer else 970
    available_height = available_bottom - available_top

    total_height = (
        title_block_height
        + block_spacing
        + body_block_height
    )

    start_y = available_top + max(
        0,
        (available_height - total_height) // 2,
    )

    if title_lines:
        start_y = _draw_centered_lines(
            draw,
            title_lines,
            font=title_font,
            fill=text_color,
            center_x=center_x,
            start_y=start_y,
            line_spacing=22,
            alignment=normalized_alignment,
            left_margin=left_margin,
            right_margin=right_margin,
        )

    if title_lines and body_lines:
        start_y += block_spacing

        # Decorative divider beneath the title.
        divider_width = 420
        divider_left = center_x - (divider_width // 2)

        draw.rounded_rectangle(
            (
                divider_left,
                start_y - 30,
                divider_left + divider_width,
                start_y - 20,
            ),
            radius=5,
            fill=accent_color,
        )

    if body_lines:
        _draw_centered_lines(
            draw,
            body_lines,
            font=body_font,
            fill=text_color,
            center_x=center_x,
            start_y=start_y,
            line_spacing=22,
            alignment=normalized_alignment,
            left_margin=left_margin,
            right_margin=right_margin,
        )

    if footer:
        footer_lines = _wrap_text_to_width(
            draw,
            footer,
            footer_font,
            content_width,
        )

        footer_y = SLIDE_HEIGHT - 120

        for line in reversed(footer_lines):
            _, line_height = _measure_text(
                draw,
                line,
                footer_font,
            )

            footer_y -= max(line_height, footer_font.size) + 8

        _draw_centered_lines(
            draw,
            footer_lines,
            font=footer_font,
            fill=text_color,
            center_x=center_x,
            start_y=footer_y,
            line_spacing=8,
            alignment=normalized_alignment,
            left_margin=left_margin,
            right_margin=right_margin,
        )

    try:
        image.convert("RGB").save(
            output_path,
            format="PNG",
            optimize=True,
        )
    except OSError as error:
        raise SlideGenerationError(
            "The generated slide could not be saved."
        ) from error

    return output_path
