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
    Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    Path("/usr/share/fonts/truetype/freefont/FreeSans.ttf"),
]

BOLD_FONT_CANDIDATES = [
    Path(
        "/usr/share/fonts/truetype/liberation2/"
        "LiberationSans-Bold.ttf"
    ),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    Path("/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"),
]

ITALIC_FONT_CANDIDATES = [
    Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Italic.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf"),
    Path("/usr/share/fonts/truetype/freefont/FreeSansOblique.ttf"),
]

BOLD_ITALIC_FONT_CANDIDATES = [
    Path("/usr/share/fonts/truetype/liberation2/LiberationSans-BoldItalic.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf"),
    Path("/usr/share/fonts/truetype/freefont/FreeSansBoldOblique.ttf"),
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


def _load_font(
    size: int,
    *,
    bold: bool = False,
    italic: bool = False,
) -> ImageFont.FreeTypeFont:
    if bold and italic:
        candidates = BOLD_ITALIC_FONT_CANDIDATES
    elif bold:
        candidates = BOLD_FONT_CANDIDATES
    elif italic:
        candidates = ITALIC_FONT_CANDIDATES
    else:
        candidates = FONT_CANDIDATES
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
    show_divider: bool = True,
    background_image_path: Path | None = None,
    overlay_opacity: int = DEFAULT_OVERLAY_OPACITY,
    logo_path: Path | None = None,
    logo_position: str = "top-right",
    logo_width_percent: int = 18,
    logo_margin: int = 70,
    title_x: float = 50.0,
    title_y: float = 38.0,
    body_x: float = 50.0,
    body_y: float = 58.0,
    footer_x: float = 50.0,
    footer_y: float = 90.0,
    title_font_size: int = 104,
    title_bold: bool = True,
    title_italic: bool = False,
    title_underline: bool = False,
    body_font_size: int = 60,
    body_bold: bool = False,
    body_italic: bool = False,
    body_underline: bool = False,
    footer_font_size: int = 38,
    footer_bold: bool = False,
    footer_italic: bool = False,
    footer_underline: bool = False,
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

    def validated_font_size(value, label):
        try:
            size = int(value)
        except (TypeError, ValueError) as error:
            raise SlideGenerationError(
                f"{label} font size must be an integer."
            ) from error
        if size < 16 or size > 160:
            raise SlideGenerationError(
                f"{label} font size must be between 16 and 160 pixels."
            )
        return size

    title_font_size = validated_font_size(title_font_size, "Title")
    body_font_size = validated_font_size(body_font_size, "Message")
    footer_font_size = validated_font_size(footer_font_size, "Footer")

    title_font = _load_font(
        title_font_size, bold=title_bold, italic=title_italic
    )
    body_font = _load_font(
        body_font_size, bold=body_bold, italic=body_italic
    )
    footer_font = _load_font(
        footer_font_size, bold=footer_bold, italic=footer_italic
    )

    # Studio preview text boxes are 84% of the 1920px canvas.
    # Use the identical width here so Chromium and Pillow wrap at the
    # same boundary regardless of the draggable X anchor.
    text_box_width = int(round(SLIDE_WIDTH * 0.84))

    def available_width(_x_percent):
        return text_box_width

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
        available_width(title_x),
    ) if title else []

    body_lines = _wrap_text_to_width(
        draw,
        body,
        body_font,
        available_width(body_x),
    ) if body else []

    def draw_positioned_block(
        lines, *, font, x_percent, y_percent, line_height_ratio, underline=False
    ):
        if not lines:
            return None

        sizes = [_measure_text(draw, line, font) for line in lines]
        line_height = max(1, int(round(font.size * line_height_ratio)))
        block_height = line_height * len(lines)
        anchor_x = int(SLIDE_WIDTH * (float(x_percent) / 100.0))
        start_y = int(round(
            SLIDE_HEIGHT * (float(y_percent) / 100.0) - block_height / 2
        ))
        current_y = start_y
        min_x, max_x = SLIDE_WIDTH, 0

        for index, line in enumerate(lines):
            width = sizes[index][0]
            if normalized_alignment == "left":
                x_position = anchor_x
            elif normalized_alignment == "right":
                x_position = anchor_x - width
            else:
                x_position = anchor_x - width // 2

            # Do not clamp X/Y. Chromium clips the 84% text box at the
            # preview edge, so Pillow must allow the same off-canvas layout.
            draw.text((x_position, current_y), line, font=font, fill=text_color)
            if underline and line:
                underline_y = current_y + font.size + max(2, font.size // 18)
                thickness = max(2, font.size // 22)
                draw.rectangle(
                    (x_position, underline_y, x_position + width, underline_y + thickness),
                    fill=text_color,
                )
            min_x = min(min_x, x_position)
            max_x = max(max_x, x_position + width)
            current_y += line_height

        return min_x, start_y, max_x, start_y + block_height

    title_box = draw_positioned_block(
        title_lines, font=title_font, x_percent=title_x,
        y_percent=title_y, line_height_ratio=1.08, underline=title_underline,
    )
    body_box = draw_positioned_block(
        body_lines, font=body_font, x_percent=body_x,
        y_percent=body_y, line_height_ratio=1.35, underline=body_underline,
    )

    if show_divider and title_box and body_box:
        divider_width = 420
        divider_center_x = int(SLIDE_WIDTH * (float(title_x) / 100.0))
        divider_left = max(30, min(
            SLIDE_WIDTH - divider_width - 30,
            divider_center_x - divider_width // 2,
        ))
        divider_y = min(SLIDE_HEIGHT - 40, title_box[3] + 28)
        draw.rounded_rectangle(
            (divider_left, divider_y, divider_left + divider_width, divider_y + 10),
            radius=5, fill=accent_color,
        )

    if footer:
        footer_lines = _wrap_text_to_width(
            draw, footer, footer_font, available_width(footer_x)
        )
        draw_positioned_block(
            footer_lines, font=footer_font, x_percent=footer_x,
            y_percent=footer_y, line_height_ratio=1.30, underline=footer_underline,
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
