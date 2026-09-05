from __future__ import annotations

import json
import math
import sqlite3
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path('/opt/cpit-signage')
CONFIG_PATH = BASE_DIR / 'config' / 'weather.json'
DATABASE_PATH = BASE_DIR / 'config' / 'signage.db'
MEDIA_DIR = BASE_DIR / 'media'
OUTPUT_FILENAME = 'weather-current.png'
OUTPUT_PATH = MEDIA_DIR / OUTPUT_FILENAME

DEFAULT_CONFIG = {
    'location_name': 'Murfreesboro, TN',
    'property_name': 'Holiday Inn Murfreesboro',
    'latitude': 35.865417,
    'longitude': -86.453505,
    'duration': 15,
    'source_label': 'National Weather Service',
    'user_agent': 'CPIT-Signage/1.0 (CompuPro IT Services)',
}

CANVAS = (1920, 1080)
BG = '#F6F5F0'
CARD = '#FFFFFF'
TEXT = '#202A2F'
MUTED = '#647076'
GREEN = '#6AA342'
GREEN_DARK = '#4B7E2D'
LINE = '#D9DDD7'
BLUE = '#3F7BA8'


@dataclass
class ForecastPeriod:
    name: str
    temperature: int | None
    unit: str
    short_forecast: str
    precipitation: int | None
    wind_speed: str
    wind_direction: str
    is_daytime: bool


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    config = DEFAULT_CONFIG.copy()
    if path.is_file():
        with path.open('r', encoding='utf-8') as handle:
            loaded = json.load(handle)
        if isinstance(loaded, dict):
            config.update(loaded)
    return config


def _http_json(url: str, user_agent: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={
            'User-Agent': user_agent,
            'Accept': 'application/geo+json',
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode('utf-8'))


def fetch_forecast(config: dict[str, Any]) -> list[ForecastPeriod]:
    lat = float(config['latitude'])
    lon = float(config['longitude'])
    user_agent = str(config.get('user_agent') or DEFAULT_CONFIG['user_agent'])

    point_url = f'https://api.weather.gov/points/{lat:.6f},{lon:.6f}'
    point_data = _http_json(point_url, user_agent)
    forecast_url = point_data.get('properties', {}).get('forecast')
    if not forecast_url:
        raise RuntimeError('NWS point response did not provide a forecast URL')

    forecast_data = _http_json(forecast_url, user_agent)
    raw_periods = forecast_data.get('properties', {}).get('periods', [])
    periods: list[ForecastPeriod] = []

    for item in raw_periods:
        precip = item.get('probabilityOfPrecipitation') or {}
        periods.append(
            ForecastPeriod(
                name=str(item.get('name', '')).strip() or 'Forecast',
                temperature=_safe_int(item.get('temperature')),
                unit=str(item.get('temperatureUnit') or 'F'),
                short_forecast=str(item.get('shortForecast') or 'Forecast unavailable').strip(),
                precipitation=_safe_int(precip.get('value')),
                wind_speed=str(item.get('windSpeed') or '').strip(),
                wind_direction=str(item.get('windDirection') or '').strip(),
                is_daytime=bool(item.get('isDaytime')),
            )
        )

    if not periods:
        raise RuntimeError('NWS forecast response contained no forecast periods')
    return periods


def _safe_int(value: Any) -> int | None:
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return None


def _font(size: int, bold: bool = False):
    candidates = [
        Path('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),
        Path('/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf'),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def _rounded(draw: ImageDraw.ImageDraw, box, radius=28, fill=CARD, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def _text_size(draw: ImageDraw.ImageDraw, text: str, font):
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0], box[3] - box[1]


def _fit_text(draw: ImageDraw.ImageDraw, text: str, max_width: int, start_size: int, min_size: int, bold=False):
    for size in range(start_size, min_size - 1, -2):
        font = _font(size, bold=bold)
        if _text_size(draw, text, font)[0] <= max_width:
            return font
    return _font(min_size, bold=bold)


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, max_width: int, max_lines: int = 2) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ''
    for word in words:
        candidate = word if not current else f'{current} {word}'
        if _text_size(draw, candidate, font)[0] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
            if len(lines) >= max_lines - 1:
                break
    if current and len(lines) < max_lines:
        lines.append(current)
    return lines or ['Forecast unavailable']


def _condition_kind(text: str) -> str:
    value = text.lower()
    if 'thunder' in value:
        return 'storm'
    if any(word in value for word in ('snow', 'sleet', 'flurr')):
        return 'snow'
    if any(word in value for word in ('rain', 'shower', 'drizzle')):
        return 'rain'
    if any(word in value for word in ('fog', 'haze', 'mist')):
        return 'fog'
    if any(word in value for word in ('cloud', 'overcast')):
        if any(word in value for word in ('partly', 'mostly sunny', 'mostly clear')):
            return 'partly'
        return 'cloud'
    if any(word in value for word in ('sunny', 'clear')):
        return 'sun'
    return 'partly'


def _draw_weather_icon(draw: ImageDraw.ImageDraw, center: tuple[int, int], size: int, condition: str):
    x, y = center
    kind = _condition_kind(condition)
    sun_r = int(size * 0.19)
    cloud_w = int(size * 0.62)
    cloud_h = int(size * 0.28)

    def sun(cx, cy, r):
        for angle in range(0, 360, 45):
            a = math.radians(angle)
            x1 = cx + int(math.cos(a) * r * 1.35)
            y1 = cy + int(math.sin(a) * r * 1.35)
            x2 = cx + int(math.cos(a) * r * 1.75)
            y2 = cy + int(math.sin(a) * r * 1.75)
            draw.line((x1, y1, x2, y2), fill='#F2B134', width=max(3, size // 55))
        draw.ellipse((cx-r, cy-r, cx+r, cy+r), fill='#F7C650')

    def cloud(cx, cy):
        left = cx - cloud_w // 2
        top = cy - cloud_h // 2
        draw.rounded_rectangle((left, top, left + cloud_w, top + cloud_h), radius=cloud_h // 2, fill='#D7DEE2')
        draw.ellipse((left + int(cloud_w*.12), top - int(cloud_h*.45), left + int(cloud_w*.46), top + int(cloud_h*.75)), fill='#D7DEE2')
        draw.ellipse((left + int(cloud_w*.40), top - int(cloud_h*.72), left + int(cloud_w*.76), top + int(cloud_h*.72)), fill='#C9D3D8')

    if kind == 'sun':
        sun(x, y, int(size * 0.24))
        return
    if kind == 'partly':
        sun(x - int(size*.16), y - int(size*.11), sun_r)
        cloud(x + int(size*.07), y + int(size*.08))
        return
    if kind == 'cloud':
        cloud(x, y)
        return
    if kind in {'rain', 'storm', 'snow'}:
        cloud(x, y - int(size*.09))
        if kind == 'rain' or kind == 'storm':
            for dx in (-int(size*.18), 0, int(size*.18)):
                draw.line((x+dx, y+int(size*.13), x+dx-int(size*.035), y+int(size*.27)), fill=BLUE, width=max(4, size//45))
        if kind == 'storm':
            pts = [(x+int(size*.05), y+int(size*.08)), (x-int(size*.04), y+int(size*.25)), (x+int(size*.03), y+int(size*.25)), (x-int(size*.04), y+int(size*.39))]
            draw.line(pts, fill='#E7A629', width=max(5, size//38), joint='curve')
        if kind == 'snow':
            for dx in (-int(size*.18), 0, int(size*.18)):
                cy = y + int(size*.23)
                r = max(3, size//55)
                draw.line((x+dx-r*2, cy, x+dx+r*2, cy), fill=BLUE, width=2)
                draw.line((x+dx, cy-r*2, x+dx, cy+r*2), fill=BLUE, width=2)
        return
    if kind == 'fog':
        cloud(x, y - int(size*.08))
        for i in range(3):
            yy = y + int(size*(.15 + i*.09))
            draw.line((x-int(size*.28), yy, x+int(size*.28), yy), fill='#AEB9BE', width=max(3, size//60))


def _find_low_for_day(periods: list[ForecastPeriod], day_period_index: int) -> int | None:
    for later in periods[day_period_index + 1:day_period_index + 4]:
        if not later.is_daytime and later.temperature is not None:
            return later.temperature
    return None


def _forecast_cards(periods: list[ForecastPeriod]) -> tuple[ForecastPeriod, list[tuple[ForecastPeriod, int | None]]]:
    lead = periods[0]
    cards: list[tuple[ForecastPeriod, int | None]] = []
    for idx, period in enumerate(periods):
        if period.is_daytime:
            if idx == 0 and lead.is_daytime:
                continue
            cards.append((period, _find_low_for_day(periods, idx)))
        if len(cards) == 3:
            break
    if len(cards) < 3:
        for idx, period in enumerate(periods[1:], start=1):
            if all(period is not existing[0] for existing in cards):
                cards.append((period, _find_low_for_day(periods, idx) if period.is_daytime else None))
            if len(cards) == 3:
                break
    return lead, cards[:3]


def render_weather_slide(periods: list[ForecastPeriod], config: dict[str, Any], output_path: Path = OUTPUT_PATH) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new('RGB', CANVAS, BG)
    draw = ImageDraw.Draw(image)

    # Header
    draw.rectangle((0, 0, 1920, 16), fill=GREEN)
    title_font = _font(58, bold=True)
    property_font = _font(29, bold=True)
    subtitle_font = _font(28)
    draw.text((100, 62), 'LOCAL WEATHER', fill=GREEN_DARK, font=property_font)
    draw.text((100, 108), str(config.get('location_name', 'Local Weather')), fill=TEXT, font=title_font)
    property_name = str(config.get('property_name', '')).strip()
    if property_name:
        pw = _text_size(draw, property_name, property_font)[0]
        draw.text((1820-pw, 86), property_name.upper(), fill=GREEN_DARK, font=property_font)

    lead, cards = _forecast_cards(periods)

    # Main forecast panel
    _rounded(draw, (80, 220, 920, 890), radius=34, fill=CARD, outline=LINE, width=2)
    draw.text((130, 265), 'TODAY', fill=MUTED, font=_font(31, bold=True))
    _draw_weather_icon(draw, (345, 515), 330, lead.short_forecast)

    temp_text = '--°' if lead.temperature is None else f'{lead.temperature}°'
    draw.text((560, 350), temp_text, fill=TEXT, font=_font(150, bold=True))

    cond_font = _fit_text(draw, lead.short_forecast, 300, 44, 30, bold=True)
    for i, line in enumerate(_wrap(draw, lead.short_forecast, cond_font, 300, 2)):
        draw.text((560, 545 + i*52), line, fill=TEXT, font=cond_font)

    precip = '—' if lead.precipitation is None else f'{lead.precipitation}%'
    wind = ' '.join(part for part in (lead.wind_direction, lead.wind_speed) if part) or '—'
    draw.line((130, 700, 870, 700), fill=LINE, width=2)
    small_label = _font(24, bold=True)
    small_value = _font(31, bold=True)
    draw.text((150, 742), 'PRECIPITATION', fill=MUTED, font=small_label)
    draw.text((150, 785), precip, fill=BLUE, font=small_value)
    draw.text((490, 742), 'WIND', fill=MUTED, font=small_label)
    wind_font = _fit_text(draw, wind, 330, 31, 23, bold=True)
    draw.text((490, 785), wind, fill=TEXT, font=wind_font)

    # 3-day cards
    x_positions = [970, 1280, 1590]
    for x, entry in zip(x_positions, cards):
        period, low = entry
        _rounded(draw, (x, 220, x+270, 890), radius=30, fill=CARD, outline=LINE, width=2)
        day_font = _fit_text(draw, period.name.upper(), 220, 27, 20, bold=True)
        tw = _text_size(draw, period.name.upper(), day_font)[0]
        draw.text((x+135-tw/2, 270), period.name.upper(), fill=MUTED, font=day_font)
        _draw_weather_icon(draw, (x+135, 445), 210, period.short_forecast)

        high_text = '--°' if period.temperature is None else f'{period.temperature}°'
        high_font = _font(68, bold=True)
        hw = _text_size(draw, high_text, high_font)[0]
        draw.text((x+135-hw/2, 570), high_text, fill=TEXT, font=high_font)
        if low is not None:
            low_text = f'Low {low}°'
            lw = _text_size(draw, low_text, _font(27, bold=True))[0]
            draw.text((x+135-lw/2, 650), low_text, fill=MUTED, font=_font(27, bold=True))

        cf = _font(24, bold=True)
        lines = _wrap(draw, period.short_forecast, cf, 210, 3)
        yy = 710
        for line in lines:
            w = _text_size(draw, line, cf)[0]
            draw.text((x+135-w/2, yy), line, fill=TEXT, font=cf)
            yy += 34
        if period.precipitation is not None:
            ptxt = f'Rain {period.precipitation}%'
            pf = _font(23, bold=True)
            pw = _text_size(draw, ptxt, pf)[0]
            draw.text((x+135-pw/2, 825), ptxt, fill=BLUE, font=pf)

    # Footer
    now = datetime.now().astimezone()
    footer_left = f"Forecast updated {now.strftime('%-I:%M %p')}"
    footer_right = f"Forecast: {config.get('source_label', 'National Weather Service')}"
    footer_font = _font(24)
    draw.text((100, 970), footer_left, fill=MUTED, font=footer_font)
    rw = _text_size(draw, footer_right, footer_font)[0]
    draw.text((1820-rw, 970), footer_right, fill=MUTED, font=footer_font)
    if now.hour < 12:
        greeting = 'Good morning!'
    elif now.hour < 17:
        greeting = 'Have a great afternoon!'
    else:
        greeting = 'Have a great evening!'
    draw.text((100, 1015), greeting, fill=GREEN_DARK, font=_font(27, bold=True))

    temporary = output_path.with_suffix('.tmp.png')
    image.save(temporary, 'PNG', optimize=True)
    temporary.replace(output_path)
    return output_path


def ensure_playlist_record(config: dict[str, Any], filename: str = OUTPUT_FILENAME) -> None:
    """Ensure one playlist row exists for the weather image.

    Uses schema introspection so this remains compatible with older and newer
    CPIT Signage database revisions, including asset_type-aware builds.
    """
    if not DATABASE_PATH.is_file():
        raise RuntimeError(f'Signage database was not found: {DATABASE_PATH}')

    duration = max(1, min(int(config.get('duration', 15)), 3600))
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row
        columns = {
            row[1]
            for row in connection.execute('PRAGMA table_info(media)').fetchall()
        }
        existing = connection.execute(
            'SELECT id FROM media WHERE filename = ?',
            (filename,),
        ).fetchone()

        if existing:
            connection.execute(
                'UPDATE media SET duration = ? WHERE id = ?',
                (duration, existing['id']),
            )
            return

        next_sort = connection.execute(
            'SELECT COALESCE(MAX(sort_order), 0) + 1 FROM media'
        ).fetchone()[0]

        fields = ['filename', 'media_type', 'duration', 'sort_order', 'enabled']
        values: list[Any] = [filename, 'image', duration, next_sort, 1]
        if 'asset_type' in columns:
            fields.append('asset_type')
            values.append('playlist')

        placeholders = ', '.join('?' for _ in fields)
        sql = f"INSERT INTO media ({', '.join(fields)}) VALUES ({placeholders})"
        connection.execute(sql, values)


def update_weather(config_path: Path = CONFIG_PATH) -> Path:
    config = load_config(config_path)
    periods = fetch_forecast(config)
    output = render_weather_slide(periods, config)
    ensure_playlist_record(config)
    return output


def demo_periods() -> list[ForecastPeriod]:
    return [
        ForecastPeriod('Today', 82, 'F', 'Mostly Sunny', 10, '5 to 10 mph', 'SW', True),
        ForecastPeriod('Tonight', 64, 'F', 'Partly Cloudy', 15, '5 mph', 'S', False),
        ForecastPeriod('Sunday', 80, 'F', 'Chance Showers', 35, '5 to 10 mph', 'S', True),
        ForecastPeriod('Sunday Night', 62, 'F', 'Mostly Cloudy', 25, '5 mph', 'SE', False),
        ForecastPeriod('Monday', 78, 'F', 'Partly Sunny', 20, '5 to 10 mph', 'NW', True),
        ForecastPeriod('Monday Night', 60, 'F', 'Mostly Clear', 10, '5 mph', 'N', False),
        ForecastPeriod('Tuesday', 81, 'F', 'Sunny', 5, '5 mph', 'NE', True),
        ForecastPeriod('Tuesday Night', 61, 'F', 'Clear', 5, '5 mph', 'E', False),
    ]
