#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path('/opt/cpit-signage')
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.weather_service import (  # noqa: E402
    CONFIG_PATH,
    demo_periods,
    load_config,
    render_weather_slide,
    update_weather,
)


def main() -> int:
    parser = argparse.ArgumentParser(description='Update the CPIT Signage weather slide.')
    parser.add_argument('--demo', action='store_true', help='Render sample data without Internet access.')
    parser.add_argument('--output', type=Path, help='Override output path when using --demo.')
    args = parser.parse_args()

    try:
        if args.demo:
            config = load_config(CONFIG_PATH)
            output = args.output or Path('/tmp/cpit-weather-demo.png')
            render_weather_slide(demo_periods(), config, output)
            print(f'Demo weather slide created: {output}')
        else:
            output = update_weather()
            print(f'Weather slide updated: {output}')
        return 0
    except Exception as error:
        print(f'Weather update failed: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
