import json
from pathlib import Path


VALIDATION_ERRORS_FILE = "outputs/validation_errors.json"


def write_validation_errors(
    section_name: str,
    messages: list[str],
    output_file: str = VALIDATION_ERRORS_FILE,
) -> Path:
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(
            {
                "validation_status": "failed",
                "failed_section": section_name,
                "errors": messages,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    return output_path
