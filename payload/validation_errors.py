import json
from pathlib import Path


def build_validation_errors_file(excel_file: str | Path) -> Path:
    return Path("outputs") / f"{Path(excel_file).stem}_validation_errors.json"


def write_validation_errors(
    section_name: str,
    messages: list[str],
    excel_file: str | Path,
    output_file: str | Path | None = None,
) -> Path:
    output_path = (
        Path(output_file)
        if output_file
        else build_validation_errors_file(excel_file)
    )
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
