import json
from pathlib import Path

from pydantic import ValidationError

from extraction.hypervisor import extract_hypervisor_data
from extraction.recovery_zvm_sites import extract_recovery_zvm_sites
from extraction.tables import clean_value, extract_sheet_table
from extraction.vpg_settings import extract_default_vpg_settings
from extraction.vpgs import extract_vpgs
from extraction.zerto_data import extract_zerto_data
from ingestion.reader import load_excel_workbook, validate_required_sheets
from validation.default_vpg_settings import validate_default_vpg_settings
from validation.error_formatting import WorkbookValidationError, format_validation_errors
from validation.hypervisor import validate_hypervisor_data
from validation.zerto_data import validate_zerto_data
from validation.recovery_zvm_sites import validate_recovery_zvm_sites
from validation.vpgs import validate_vpgs
from validation.vm_replication import validate_vm_replication
from validation.vm_storage import validate_vm_storage
from validation.vm_nics import validate_vm_nics


EXCEL_FILE = "files/VCA Data - 0.106.xlsx"
OUTPUT_FILE = "outputs/zerto_payload.json"


def main() -> None:
    output_path = generate_zerto_json(EXCEL_FILE, OUTPUT_FILE)
    print(f"Wrote {output_path}")


def generate_zerto_json(
    excel_file: str = EXCEL_FILE,
    output_file: str = OUTPUT_FILE,
) -> Path:
    workbook = load_excel_workbook(excel_file)
    validate_required_sheets(workbook)

    zerto_data = extract_zerto_data(excel_file)
    hypervisor_data = extract_hypervisor_data(excel_file)
    default_vpg_settings = extract_default_vpg_settings(excel_file, print_output=False)
    recovery_zvm_sites = extract_recovery_zvm_sites(excel_file)
    vpgs = extract_vpgs(excel_file)
    vm_replication = extract_sheet_table(
        excel_file,
        "VM Replication",
        "VPG Name",
        table_name="VM_Replication",
    )
    vm_storage = extract_sheet_table(
        excel_file,
        "VM Storage",
        "VPG Name",
        table_name="VM_Storage",
    )
    vm_nics = extract_sheet_table(
        excel_file,
        "VM NICs",
        "VPG Name",
        table_name="VM_NICs",
    )

    validations = {
        "zerto_data": validate_section(
            lambda: validate_zerto_data(zerto_data),
        ),
        "hypervisor_data": validate_section(
            lambda: validate_hypervisor_data(hypervisor_data),
        ),
        "default_vpg_settings": validate_section(
            lambda: validate_default_vpg_settings(default_vpg_settings),
        ),
        "recovery_zvm_sites": validate_section(
            lambda: validate_recovery_zvm_sites(recovery_zvm_sites),
        ),
        "vpgs": validate_section(
            lambda: validate_vpgs(vpgs),
        ),
        "vm_replication": validate_section(
            lambda: validate_vm_replication(vm_replication),
        ),
        "vm_storage": validate_section(
            lambda: validate_vm_storage(vm_storage),
        ),
        "vm_nics": validate_section(
            lambda: validate_vm_nics(vm_nics),
        ),
    }

    payload = {
        "source_file": excel_file,
        "ready_for_zerto_api": all(
            validation["status"] == "passed"
            for validation in validations.values()
        ),
        "validations": validations,
        "reference_data": {
            "zvm_sites": zerto_data["summary"]["zvm_sites"],
            "labels": zerto_data["summary"]["labels"],
            "recovery_scripts": zerto_data["summary"]["recovery_scripts"],
            "boot_order_groups": zerto_data["summary"]["boot_order_groups"],
            "hypervisor": hypervisor_data,
        },
        "api_candidate_payloads": {
            "default_vpg_settings": default_vpg_settings,
            "recovery_zvm_sites": recovery_zvm_sites,
            "vpgs": vpgs,
            "vm_replication": vm_replication,
            "vm_storage": vm_storage,
            "vm_nics": vm_nics,
            "extended_journal": extract_sheet_table(
                excel_file,
                "Extended Journal",
                "VPG Name",
                table_name="Extended_Journal_Copies",
            ),
        },
    }

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(make_json_safe(payload), indent=2),
        encoding="utf-8",
    )

    return output_path


def validate_section(validate):
    try:
        result = validate()
    except WorkbookValidationError as error:
        return {
            "status": "failed",
            "messages": error.messages,
            "errors": [],
        }
    except ValidationError as error:
        return {
            "status": "failed",
            "messages": format_validation_errors(error),
            "errors": error.errors(include_url=False),
        }
    except ValueError as error:
        return {
            "status": "failed",
            "messages": [str(error)],
            "errors": [],
        }

    return {
        "status": "passed",
        "records": make_json_safe(result),
    }


def make_json_safe(value):
    if isinstance(value, list):
        return [make_json_safe(item) for item in value]

    if isinstance(value, tuple):
        return [make_json_safe(item) for item in value]

    if isinstance(value, dict):
        return {
            str(key): make_json_safe(item)
            for key, item in value.items()
            if not str(key).startswith("__")
        }

    if hasattr(value, "model_dump"):
        return make_json_safe(value.model_dump())

    cleaned_value = clean_value(value)

    if isinstance(cleaned_value, (str, int, float, bool)) or cleaned_value is None:
        return cleaned_value

    return str(cleaned_value)


if __name__ == "__main__":
    main()
