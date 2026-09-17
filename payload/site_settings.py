import json
from pathlib import Path

from payload.json_output import make_json_safe


SITE_SETTINGS_FILE = "outputs/site_settings.json"


def write_site_settings_json(
    site_settings: dict[str, list[dict]],
    output_file: str = SITE_SETTINGS_FILE,
) -> Path:
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(make_json_safe(site_settings), indent=2),
        encoding="utf-8",
    )

    return output_path
