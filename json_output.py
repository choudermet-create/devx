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
OUTPUT_FILE = "outputs/vca_check_dump.json"
API_PAYLOAD_OUTPUT_FILE = "outputs/zerto_api_payload.json"


def main() -> None:
    output_path = generate_vca_check_dump(EXCEL_FILE, OUTPUT_FILE)
    print(f"Wrote {output_path}")


def generate_vca_check_dump(
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
    extended_journal = extract_sheet_table(
        excel_file,
        "Extended Journal",
        "VPG Name",
        table_name="Extended_Journal_Copies",
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

    return write_zerto_json_dump(
        excel_file=excel_file,
        zerto_data=zerto_data,
        hypervisor_data=hypervisor_data,
        default_vpg_settings=default_vpg_settings,
        recovery_zvm_sites=recovery_zvm_sites,
        vpgs=vpgs,
        vm_replication=vm_replication,
        vm_storage=vm_storage,
        vm_nics=vm_nics,
        extended_journal=extended_journal,
        validations=validations,
        output_file=output_file,
    )


def write_zerto_json_dump(
    excel_file: str,
    zerto_data: dict,
    hypervisor_data: dict,
    default_vpg_settings: dict,
    recovery_zvm_sites: list[dict],
    vpgs: list[dict],
    vm_replication: list[dict],
    vm_storage: list[dict],
    vm_nics: list[dict],
    extended_journal: list[dict],
    validations: dict,
    output_file: str = OUTPUT_FILE,
) -> Path:
    validation_status = get_validation_status(validations)
    resolved_api_candidate_payloads = build_resolved_api_candidate_payloads(
        default_vpg_settings,
        recovery_zvm_sites,
        vpgs,
        vm_replication,
        vm_storage,
        vm_nics,
        extended_journal,
    )

    payload = {
        "source_file": excel_file,
        "validation_status": validation_status,
        "validations": validations,
        "reference_data": {
            "zvm_sites": zerto_data["summary"]["zvm_sites"],
            "labels": zerto_data["summary"]["labels"],
            "recovery_scripts": zerto_data["summary"]["recovery_scripts"],
            "boot_order_groups": zerto_data["summary"]["boot_order_groups"],
            "hypervisor": hypervisor_data,
        },
        "resolved_api_candidate_payloads": resolved_api_candidate_payloads,
        "api_candidate_payloads": {
            "default_vpg_settings": default_vpg_settings,
            "recovery_zvm_sites": recovery_zvm_sites,
            "vpgs": vpgs,
            "vm_replication": vm_replication,
            "vm_storage": vm_storage,
            "vm_nics": vm_nics,
            "extended_journal": extended_journal,
        },
    }

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(make_json_safe(payload), indent=2),
        encoding="utf-8",
    )
    write_zerto_api_payload(
        resolved_api_candidate_payloads,
        zerto_data["summary"]["boot_order_groups"],
        validation_status,
    )

    return output_path


def write_zerto_api_payload(
    resolved_api_candidate_payloads: dict,
    boot_order_groups: list[dict],
    validation_status: str,
    output_file: str = API_PAYLOAD_OUTPUT_FILE,
) -> Path:
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(
            make_json_safe(
                build_zerto_api_payload(
                    resolved_api_candidate_payloads,
                    boot_order_groups,
                    validation_status,
                ),
            ),
            indent=2,
        ),
        encoding="utf-8",
    )

    return output_path


def build_resolved_api_candidate_payloads(
    default_vpg_settings: dict,
    recovery_zvm_sites: list[dict],
    vpgs: list[dict],
    vm_replication: list[dict],
    vm_storage: list[dict],
    vm_nics: list[dict],
    extended_journal: list[dict],
) -> dict:
    resolved_recovery_zvm_sites = [
        resolve_recovery_zvm_site_defaults(row, default_vpg_settings)
        for row in recovery_zvm_sites
    ]
    recovery_site_defaults = build_recovery_site_defaults(resolved_recovery_zvm_sites)
    resolved_vpgs = [
        resolve_vpg_defaults(row, default_vpg_settings, recovery_site_defaults)
        for row in vpgs
    ]
    vpg_defaults = build_vpg_defaults(resolved_vpgs)

    return {
        "default_vpg_settings": default_vpg_settings,
        "recovery_zvm_sites": resolved_recovery_zvm_sites,
        "vpgs": resolved_vpgs,
        "vm_replication": [
            resolve_vm_replication_defaults(row, vpg_defaults)
            for row in vm_replication
        ],
        "vm_storage": [
            resolve_vm_storage_defaults(row, vpg_defaults)
            for row in vm_storage
        ],
        "vm_nics": [
            resolve_vm_nic_defaults(row, vpg_defaults)
            for row in vm_nics
        ],
        "extended_journal": extended_journal,
    }


def build_zerto_api_payload(
    resolved_api_candidate_payloads: dict,
    boot_order_groups: list[dict],
    validation_status: str,
) -> dict:
    vpgs = resolved_api_candidate_payloads["vpgs"]
    vm_replication = resolved_api_candidate_payloads["vm_replication"]
    vm_storage = resolved_api_candidate_payloads["vm_storage"]
    vm_nics = resolved_api_candidate_payloads["vm_nics"]

    return {
        "validationStatus": validation_status,
        "vpgSettings": [
            build_vpg_payload(
                row,
                rows_for_vpg(vm_replication, row.get("VPG Name")),
                rows_for_vpg(vm_storage, row.get("VPG Name")),
                rows_for_vpg(vm_nics, row.get("VPG Name")),
                boot_order_groups,
            )
            for row in vpgs
        ],
    }


def build_vpg_payload(
    row: dict,
    vm_replication: list[dict],
    vm_storage: list[dict],
    vm_nics: list[dict],
    boot_order_groups: list[dict],
) -> dict:
    return compact_dict({
        "basic": build_basic_api(row),
        "scripting": build_scripting_api(row),
        "bootGroups": build_boot_groups_api(
            boot_order_groups,
            row.get("Boot Order Meta Group Name"),
        ),
        "journal": build_journal_api(row, vm_level=False),
        "scratch": build_scratch_api(row),
        "recovery": build_recovery_api(row),
        "networks": build_networks_api(row),
        "vms": build_vm_payloads(vm_replication, vm_storage, vm_nics),
    })


def build_basic_api(row: dict) -> dict | None:
    return compact_dict({
        "name": row.get("VPG Name"),
        "vpgType": row.get("VPG Type"),
        "rpoInSeconds": duration_to_seconds(
            row.get("Target RPO Alert Value"),
            row.get("Target RPO Alert Unit"),
        ),
        "testIntervalInMinutes": test_reminder_to_minutes(row.get("Test Reminder")),
        "journalHistoryInHours": duration_to_hours(
            row.get("Journal History Value"),
            row.get("Journal History Unit"),
        ),
        "priority": row.get("Priority"),
        "useWanCompression": yes_no_to_bool(row.get("Enable WAN Traffic Compression")),
        "protectedSiteIdentifier": row.get("Effective Protected ZVM Site Name"),
        "recoverySiteIdentifier": row.get("Effective Recovery ZVM Site Name"),
    })


def build_recovery_api(row: dict) -> dict | None:
    return compact_dict({
        "defaultHostIdentifier": row.get("Recovery Host Name"),
        "defaultDatastoreIdentifier": row.get("Recovery Datastore Name"),
        "defaultFolderIdentifier": row.get("Recovery Folder Name"),
    })


def build_journal_api(row: dict, vm_level: bool) -> dict | None:
    if vm_level:
        datastore_field = "Journal Datastore Name"
    else:
        datastore_field = "Journal Datastore Name"

    return compact_dict({
        "limitation": build_journal_limitation(
            row.get("Journal Size Hard Limit Value"),
            row.get("Journal Size Hard Limit Unit"),
            row.get("Journal Size Warning Threshold Value"),
            row.get("Journal Size Warning Threshold Unit"),
        ),
        "datastoreIdentifier": row.get(datastore_field),
    })


def build_scratch_api(row: dict) -> dict | None:
    return compact_dict({
        "limitation": build_journal_limitation(
            row.get("Scratch Journal Size Hard Limit Value"),
            row.get("Scratch Journal Size Hard Limit Unit"),
            row.get("Scratch Journal Size Warning Threshold Value"),
            row.get("Scratch Journal Size Warning Threshold Unit"),
        ),
        "datastoreIdentifier": row.get("Scratch Journal Datastore Name"),
    })


def build_networks_api(row: dict) -> dict | None:
    return compact_dict({
        "failover": build_default_hypervisor_network(
            row.get("Failover Live / Move - Network Name"),
        ),
        "failoverTest": build_default_hypervisor_network(
            row.get("Failover Test Network Name"),
        ),
    })


def build_default_hypervisor_network(network_name) -> dict | None:
    return compact_dict({
        "hypervisor": compact_dict({
            "defaultNetworkIdentifier": network_name,
        }),
    })


def build_scripting_api(row: dict) -> dict | None:
    return compact_dict({
        "preRecovery": build_script_api(row, "Pre-Recovery"),
        "postRecovery": build_script_api(row, "Post-Recovery"),
    })


def build_script_api(row: dict, prefix: str) -> dict | None:
    return compact_dict({
        "command": row.get(f"{prefix} Script Name"),
        "parameters": row.get(f"{prefix} Script Parameters"),
        "timeoutInSeconds": row.get(f"{prefix} Script Execution Timeout (Seconds)"),
    })


def build_boot_groups_api(
    boot_order_groups: list[dict],
    meta_group_name,
) -> dict:
    return compact_dict({
        "bootGroups": compact_list([
            compact_dict({
                "name": group.get("group_name"),
                "bootDelayInSeconds": group.get("boot_delay_secs"),
            })
            for group in boot_order_groups
            if clean_value(group.get("meta_group_name")) == clean_value(meta_group_name)
        ]),
    })


def build_vm_payloads(
    vm_replication: list[dict],
    vm_storage: list[dict],
    vm_nics: list[dict],
) -> list[dict]:
    vm_names = []
    for row in vm_replication + vm_storage + vm_nics:
        vm_name = clean_value(row.get("VM Name"))
        if vm_name and vm_name not in vm_names:
            vm_names.append(vm_name)

    return [
        compact_dict({
            "vmIdentifier": vm_name,
            **(build_vm_replication_payload(
                first_row_for_vm(vm_replication, vm_name),
            ) or {}),
            "volumes": [
                build_vm_storage_payload(row)
                for row in rows_for_vm(vm_storage, vm_name)
            ],
            "nics": [
                build_vm_nic_payload(row)
                for row in rows_for_vm(vm_nics, vm_name)
            ],
        })
        for vm_name in vm_names
    ]


def build_vm_replication_payload(row: dict | None) -> dict | None:
    if not row:
        return None

    return compact_dict({
        "recovery": compact_dict({
            "hostIdentifier": row.get("Recovery Host Name"),
            "datastoreIdentifier": row.get("Recovery Datastore Name"),
            "folderIdentifier": row.get("Recovery Folder Name"),
        }),
        "bootGroupIdentifier": row.get("Boot Order Group Name"),
        "journal": build_journal_api(row, vm_level=True),
        "scratch": build_scratch_api(row),
    })


def build_vm_storage_payload(row: dict) -> dict:
    return compact_dict({
        "volumeIdentifier": row.get("Protected Volume Location"),
        "preseed": compact_dict({
            "path": row.get("Recovery Volume Location"),
        }),
        "rdm": compact_dict({
            "deviceIdentifier": row.get("Recovery Raw Device Name"),
        }),
        "datastore": compact_dict({
            "isThin": disk_provisioning_to_is_thin(
                row.get("Disk Provisioning Override"),
            ),
        }),
        "volumeSyncSettings": row.get("Volume Sync Type"),
    })


def build_vm_nic_payload(row: dict) -> dict:
    return compact_dict({
        "nicIdentifier": row.get("NIC Name"),
        "failover": build_vm_nic_network_api(row, "Failover Live / Move"),
        "failoverTest": build_vm_nic_network_api(row, "Failover Test"),
    })


def build_vm_nic_network_api(row: dict, prefix: str) -> dict | None:
    return compact_dict({
        "hypervisor": compact_dict({
            "networkIdentifier": row.get(f"{prefix} - Network Name"),
            "shouldReplaceMacAddress": yes_no_to_bool(
                row.get(f"{prefix} - Create new MAC address"),
            ),
            "dnsSuffix": row.get(f"{prefix} - DNS Suffix"),
            "ipConfig": build_ip_config(row, prefix),
            "shouldReplaceIpConfiguration": should_replace_ip_configuration(
                row.get(f"{prefix} - Change vNIC IP Config"),
            ),
        }),
    })


def build_ip_config(row: dict, prefix: str) -> dict | None:
    return compact_dict({
        "staticIp": row.get(f"{prefix} - IP Address"),
        "subnetMask": row.get(f"{prefix} - Subnet Mask"),
        "gateway": row.get(f"{prefix} - Default Gateway"),
        "primaryDns": row.get(f"{prefix} - Preferred DNS Server"),
        "secondaryDns": row.get(f"{prefix} - Alternate DNS Server"),
        "isDhcp": is_dhcp(row.get(f"{prefix} - Change vNIC IP Config")),
    })


def build_journal_limitation(
    hard_limit_value,
    hard_limit_unit,
    warning_value,
    warning_unit,
) -> dict | None:
    return compact_dict({
        **limit_to_api_fields(hard_limit_value, hard_limit_unit, "hardLimit"),
        **limit_to_api_fields(warning_value, warning_unit, "warningThreshold"),
    })


def limit_to_api_fields(value, unit, prefix: str) -> dict:
    cleaned_unit = clean_value(unit)
    if cleaned_unit in (None, "Unlimited"):
        return {}

    if cleaned_unit == "%":
        return {f"{prefix}InPercent": value}

    size_mb = size_to_mb(value, cleaned_unit)
    if size_mb is None:
        return {}

    return {f"{prefix}InMB": size_mb}


def size_to_mb(value, unit) -> int | None:
    cleaned_value = clean_value(value)
    if cleaned_value is None:
        return None

    if unit == "GiB":
        return int(float(cleaned_value) * 1024)

    if unit == "TiB":
        return int(float(cleaned_value) * 1024 * 1024)

    return None


def duration_to_seconds(value, unit) -> int | None:
    cleaned_value = clean_value(value)
    cleaned_unit = clean_value(unit)
    if cleaned_value is None or cleaned_unit is None:
        return None

    multipliers = {
        "Seconds": 1,
        "Minutes": 60,
        "Hours": 3600,
        "Days": 86400,
    }
    multiplier = multipliers.get(cleaned_unit)
    if multiplier is None:
        return None

    return int(float(cleaned_value) * multiplier)


def duration_to_hours(value, unit) -> int | None:
    cleaned_value = clean_value(value)
    cleaned_unit = clean_value(unit)
    if cleaned_value is None or cleaned_unit is None:
        return None

    if cleaned_unit == "Hours":
        return int(float(cleaned_value))

    if cleaned_unit == "Days":
        return int(float(cleaned_value) * 24)

    return None


def test_reminder_to_minutes(value) -> int | None:
    cleaned_value = clean_value(value)
    if cleaned_value in (None, "None"):
        return None

    month_map = {
        "1 Month": 1,
        "3 Months": 3,
        "6 Months": 6,
        "9 Months": 9,
        "12 Months": 12,
    }
    months = month_map.get(cleaned_value)
    if months is None:
        return None

    return months * 30 * 24 * 60


def yes_no_to_bool(value) -> bool | None:
    cleaned_value = clean_value(value)
    if cleaned_value == "Yes":
        return True

    if cleaned_value == "No":
        return False

    return None


def disk_provisioning_to_is_thin(value) -> bool | None:
    cleaned_value = clean_value(value)
    if cleaned_value == "Thin":
        return True

    if cleaned_value == "Thick":
        return False

    return None


def should_replace_ip_configuration(value) -> bool | None:
    cleaned_value = clean_value(value)
    if cleaned_value == "No":
        return False

    if cleaned_value in ("Yes, DHCP", "Yes, Static"):
        return True

    return None


def is_dhcp(value) -> bool | None:
    cleaned_value = clean_value(value)
    if cleaned_value == "Yes, DHCP":
        return True

    if cleaned_value == "Yes, Static":
        return False

    return None


def rows_for_vpg(rows: list[dict], vpg_name) -> list[dict]:
    return [
        row
        for row in rows
        if clean_value(row.get("VPG Name")) == clean_value(vpg_name)
    ]


def rows_for_vm(rows: list[dict], vm_name) -> list[dict]:
    return [
        row
        for row in rows
        if clean_value(row.get("VM Name")) == clean_value(vm_name)
    ]


def first_row_for_vm(rows: list[dict], vm_name) -> dict | None:
    matching_rows = rows_for_vm(rows, vm_name)
    if not matching_rows:
        return None

    return matching_rows[0]


def compact_dict(row: dict) -> dict | None:
    compacted = {
        key: value
        for key, value in row.items()
        if clean_value(value) is not None and value != [] and value != {}
    }

    if not compacted:
        return None

    return compacted


def compact_list(rows: list) -> list:
    return [
        row
        for row in rows
        if clean_value(row) is not None and row != [] and row != {}
    ]


def resolve_recovery_zvm_site_defaults(row: dict, default_vpg_settings: dict) -> dict:
    resolved_row = dict(row)
    effective_site_name = first_value(
        row.get("Recovery ZVM Site Name"),
        row.get("Recovery Site Name"),
        default_vpg_settings.get("recovery_site"),
    )

    resolved_row["Effective Recovery ZVM Site Name"] = effective_site_name
    resolve_field(resolved_row, "VPG Type", default_vpg_settings.get("vpg_type"))
    resolve_field(resolved_row, "Priority", default_vpg_settings.get("priority"))
    resolve_field(
        resolved_row,
        "Journal History Value",
        value_unit_value(default_vpg_settings.get("journal_history")),
    )
    resolve_field(
        resolved_row,
        "Journal History Unit",
        value_unit_unit(default_vpg_settings.get("journal_history")),
    )
    resolve_field(
        resolved_row,
        "Target RPO Alert Value",
        value_unit_value(default_vpg_settings.get("target_rpo_alert")),
    )
    resolve_field(
        resolved_row,
        "Target RPO Alert Unit",
        value_unit_unit(default_vpg_settings.get("target_rpo_alert")),
    )
    resolve_field(resolved_row, "Test Reminder", default_vpg_settings.get("test_reminder"))
    resolve_field(
        resolved_row,
        "Journal Size Hard Limit Value",
        value_unit_value(default_vpg_settings.get("journal_size_hard_limit")),
    )
    resolve_field(
        resolved_row,
        "Journal Size Hard Limit Unit",
        value_unit_unit(default_vpg_settings.get("journal_size_hard_limit")),
    )
    resolve_field(
        resolved_row,
        "Journal Size Warning Threshold Value",
        value_unit_value(default_vpg_settings.get("journal_size_warning")),
    )
    resolve_field(
        resolved_row,
        "Journal Size Warning Threshold Unit",
        value_unit_unit(default_vpg_settings.get("journal_size_warning")),
    )
    resolve_field(
        resolved_row,
        "Scratch Journal Size Hard Limit Value",
        value_unit_value(default_vpg_settings.get("scratch_journal_size_hard_limit")),
    )
    resolve_field(
        resolved_row,
        "Scratch Journal Size Hard Limit Unit",
        value_unit_unit(default_vpg_settings.get("scratch_journal_size_hard_limit")),
    )
    resolve_field(
        resolved_row,
        "Scratch Journal Size Warning Threshold Value",
        value_unit_value(default_vpg_settings.get("scratch_journal_size_warning")),
    )
    resolve_field(
        resolved_row,
        "Scratch Journal Size Warning Threshold Unit",
        value_unit_unit(default_vpg_settings.get("scratch_journal_size_warning")),
    )
    resolve_field(
        resolved_row,
        "Enable WAN Traffic Compression",
        default_vpg_settings.get("wan_compression"),
    )
    resolve_field(
        resolved_row,
        "Disk Provisioning Override",
        default_vpg_settings.get("disk_provisioning_override"),
    )
    resolve_field(
        resolved_row,
        "Recovery Folder Name",
        default_vpg_settings.get("recovery_folder_name"),
    )
    resolve_field(
        resolved_row,
        "Pre-Recovery Script Execution Timeout (Seconds)",
        default_vpg_settings.get("pre_recovery_script_execution_timeout_seconds"),
    )
    resolve_field(
        resolved_row,
        "Post-Recovery Script Execution Timeout (Seconds)",
        default_vpg_settings.get("post_recovery_script_execution_timeout_seconds"),
    )
    resolve_field(
        resolved_row,
        "Failover Live / Move - Create new MAC address",
        default_vpg_settings.get("failover_live_move_create_new_mac_address"),
    )
    resolve_field(
        resolved_row,
        "Failover Live / Move - Change vNIC IP Config",
        default_vpg_settings.get("failover_live_move_change_vnic_ip_config"),
    )
    resolve_field(
        resolved_row,
        "Failover Live / Move - Subnet Mask",
        default_vpg_settings.get("failover_live_move_subnet_mask"),
    )
    resolve_field(
        resolved_row,
        "Failover Live / Move - Default Gateway",
        default_vpg_settings.get("failover_live_move_default_gateway"),
    )
    resolve_field(
        resolved_row,
        "Failover Live / Move - Preferred DNS Server",
        default_vpg_settings.get("failover_live_move_preferred_dns_server"),
    )
    resolve_field(
        resolved_row,
        "Failover Live / Move - Alternate DNS Server",
        default_vpg_settings.get("failover_live_move_alternate_dns_server"),
    )
    resolve_field(
        resolved_row,
        "Failover Live / Move - DNS Suffix",
        default_vpg_settings.get("failover_live_move_dns_suffix"),
    )
    resolve_field(
        resolved_row,
        "Failover Test - Create new MAC address",
        default_vpg_settings.get("failover_test_create_new_mac_address"),
    )
    resolve_field(
        resolved_row,
        "Failover Test - Change vNIC IP Config",
        default_vpg_settings.get("failover_test_change_vnic_ip_config"),
    )
    resolve_field(
        resolved_row,
        "Failover Test - Subnet Mask",
        default_vpg_settings.get("failover_test_subnet_mask"),
    )
    resolve_field(
        resolved_row,
        "Failover Test - Default Gateway",
        default_vpg_settings.get("failover_test_default_gateway"),
    )
    resolve_field(
        resolved_row,
        "Failover Test - Preferred DNS Server",
        default_vpg_settings.get("failover_test_preferred_dns_server"),
    )
    resolve_field(
        resolved_row,
        "Failover Test - Alternate DNS Server",
        default_vpg_settings.get("failover_test_alternate_dns_server"),
    )
    resolve_field(
        resolved_row,
        "Failover Test - DNS Suffix",
        default_vpg_settings.get("failover_test_dns_suffix"),
    )

    return resolved_row


def resolve_vpg_defaults(
    row: dict,
    default_vpg_settings: dict,
    recovery_site_defaults: dict,
) -> dict:
    resolved_row = dict(row)
    effective_protected_site = first_value(
        row.get("Protected ZVM Site Name"),
        row.get("Protected Site Name"),
        default_vpg_settings.get("protected_site"),
    )
    effective_recovery_site = first_value(
        row.get("Recovery ZVM Site Name"),
        row.get("Recovery Site Name"),
        default_vpg_settings.get("recovery_site"),
    )
    recovery_defaults = recovery_site_defaults.get(effective_recovery_site, {})

    resolved_row["Effective Protected ZVM Site Name"] = effective_protected_site
    resolved_row["Effective Recovery ZVM Site Name"] = effective_recovery_site
    resolve_field(
        resolved_row,
        "VPG Type",
        recovery_defaults.get("VPG Type"),
        default_vpg_settings.get("vpg_type"),
    )
    resolve_field(
        resolved_row,
        "Priority",
        recovery_defaults.get("Priority"),
        default_vpg_settings.get("priority"),
    )
    resolve_field(resolved_row, "Recovery Host Name", recovery_defaults.get("Recovery Host Name"))
    resolve_field(
        resolved_row,
        "Recovery Datastore Name",
        recovery_defaults.get("Recovery Datastore Name"),
    )
    resolve_field(
        resolved_row,
        "Journal History Value",
        recovery_defaults.get("Journal History Value"),
        value_unit_value(default_vpg_settings.get("journal_history")),
    )
    resolve_field(
        resolved_row,
        "Journal History Unit",
        recovery_defaults.get("Journal History Unit"),
        value_unit_unit(default_vpg_settings.get("journal_history")),
    )
    resolve_field(
        resolved_row,
        "Target RPO Alert Value",
        recovery_defaults.get("Target RPO Alert Value"),
        value_unit_value(default_vpg_settings.get("target_rpo_alert")),
    )
    resolve_field(
        resolved_row,
        "Target RPO Alert Unit",
        recovery_defaults.get("Target RPO Alert Unit"),
        value_unit_unit(default_vpg_settings.get("target_rpo_alert")),
    )
    resolve_field(
        resolved_row,
        "Test Reminder",
        recovery_defaults.get("Test Reminder"),
        default_vpg_settings.get("test_reminder"),
    )
    resolve_field(
        resolved_row,
        "Journal Datastore Name",
        recovery_defaults.get("Journal Datastore Name"),
        recovery_defaults.get("Recovery Datastore Name"),
    )
    resolve_field(
        resolved_row,
        "Journal Size Hard Limit Value",
        recovery_defaults.get("Journal Size Hard Limit Value"),
        value_unit_value(default_vpg_settings.get("journal_size_hard_limit")),
    )
    resolve_field(
        resolved_row,
        "Journal Size Hard Limit Unit",
        recovery_defaults.get("Journal Size Hard Limit Unit"),
        value_unit_unit(default_vpg_settings.get("journal_size_hard_limit")),
    )
    resolve_field(
        resolved_row,
        "Journal Size Warning Threshold Value",
        recovery_defaults.get("Journal Size Warning Threshold Value"),
        value_unit_value(default_vpg_settings.get("journal_size_warning")),
    )
    resolve_field(
        resolved_row,
        "Journal Size Warning Threshold Unit",
        recovery_defaults.get("Journal Size Warning Threshold Unit"),
        value_unit_unit(default_vpg_settings.get("journal_size_warning")),
    )
    resolve_field(
        resolved_row,
        "Scratch Journal Datastore Name",
        recovery_defaults.get("Scratch Journal Datastore Name"),
        recovery_defaults.get("Recovery Datastore Name"),
    )
    resolve_field(
        resolved_row,
        "Scratch Journal Size Hard Limit Value",
        recovery_defaults.get("Scratch Journal Size Hard Limit Value"),
        value_unit_value(default_vpg_settings.get("scratch_journal_size_hard_limit")),
    )
    resolve_field(
        resolved_row,
        "Scratch Journal Size Hard Limit Unit",
        recovery_defaults.get("Scratch Journal Size Hard Limit Unit"),
        value_unit_unit(default_vpg_settings.get("scratch_journal_size_hard_limit")),
    )
    resolve_field(
        resolved_row,
        "Scratch Journal Size Warning Threshold Value",
        recovery_defaults.get("Scratch Journal Size Warning Threshold Value"),
        value_unit_value(default_vpg_settings.get("scratch_journal_size_warning")),
    )
    resolve_field(
        resolved_row,
        "Scratch Journal Size Warning Threshold Unit",
        recovery_defaults.get("Scratch Journal Size Warning Threshold Unit"),
        value_unit_unit(default_vpg_settings.get("scratch_journal_size_warning")),
    )
    resolve_field(
        resolved_row,
        "Enable WAN Traffic Compression",
        recovery_defaults.get("Enable WAN Traffic Compression"),
        default_vpg_settings.get("wan_compression"),
    )
    resolve_field(
        resolved_row,
        "Disk Provisioning Override",
        recovery_defaults.get("Disk Provisioning Override"),
        default_vpg_settings.get("disk_provisioning_override"),
    )
    resolve_field(
        resolved_row,
        "Volume Sync Type",
        default_vpg_settings.get("volume_sync_type"),
    )
    resolve_field(
        resolved_row,
        "Failover Live / Move - Network Name",
        recovery_defaults.get("Failover Live / Move Network Name"),
    )
    resolve_field(
        resolved_row,
        "Failover Test Network Name",
        recovery_defaults.get("Failover Test Network Name"),
    )
    resolve_field(
        resolved_row,
        "Recovery Folder Name",
        recovery_defaults.get("Recovery Folder Name"),
        default_vpg_settings.get("recovery_folder_name"),
    )
    resolve_field(
        resolved_row,
        "Pre-Recovery Script Name",
        recovery_defaults.get("Pre-Recovery Script Name"),
    )
    resolve_field(
        resolved_row,
        "Pre-Recovery Script Execution Timeout (Seconds)",
        recovery_defaults.get("Pre-Recovery Script Execution Timeout (Seconds)"),
        default_vpg_settings.get("pre_recovery_script_execution_timeout_seconds"),
    )
    resolve_field(
        resolved_row,
        "Post-Recovery Script Name",
        recovery_defaults.get("Post-Recovery Script Name"),
    )
    resolve_field(
        resolved_row,
        "Post-Recovery Script Execution Timeout (Seconds)",
        recovery_defaults.get("Post-Recovery Script Execution Timeout (Seconds)"),
        default_vpg_settings.get("post_recovery_script_execution_timeout_seconds"),
    )
    resolve_field(
        resolved_row,
        "Failover Live / Move - Create new MAC address",
        recovery_defaults.get("Failover Live / Move - Create new MAC address"),
        default_vpg_settings.get("failover_live_move_create_new_mac_address"),
    )
    resolve_field(
        resolved_row,
        "Failover Live / Move - Change vNIC IP Config",
        recovery_defaults.get("Failover Live / Move - Change vNIC IP Config"),
        default_vpg_settings.get("failover_live_move_change_vnic_ip_config"),
    )
    resolve_field(
        resolved_row,
        "Failover Live / Move - Subnet Mask",
        recovery_defaults.get("Failover Live / Move - Subnet Mask"),
        default_vpg_settings.get("failover_live_move_subnet_mask"),
    )
    resolve_field(
        resolved_row,
        "Failover Live / Move - Default Gateway",
        recovery_defaults.get("Failover Live / Move - Default Gateway"),
        default_vpg_settings.get("failover_live_move_default_gateway"),
    )
    resolve_field(
        resolved_row,
        "Failover Live / Move - Preferred DNS Server",
        recovery_defaults.get("Failover Live / Move - Preferred DNS Server"),
        default_vpg_settings.get("failover_live_move_preferred_dns_server"),
    )
    resolve_field(
        resolved_row,
        "Failover Live / Move - Alternate DNS Server",
        recovery_defaults.get("Failover Live / Move - Alternate DNS Server"),
        default_vpg_settings.get("failover_live_move_alternate_dns_server"),
    )
    resolve_field(
        resolved_row,
        "Failover Live / Move - DNS Suffix",
        recovery_defaults.get("Failover Live / Move - DNS Suffix"),
        default_vpg_settings.get("failover_live_move_dns_suffix"),
    )
    resolve_field(
        resolved_row,
        "Failover Test - Create new MAC address",
        recovery_defaults.get("Failover Test - Create new MAC address"),
        default_vpg_settings.get("failover_test_create_new_mac_address"),
    )
    resolve_field(
        resolved_row,
        "Failover Test - Change vNIC IP Config",
        recovery_defaults.get("Failover Test - Change vNIC IP Config"),
        default_vpg_settings.get("failover_test_change_vnic_ip_config"),
    )
    resolve_field(
        resolved_row,
        "Failover Test - Subnet Mask",
        recovery_defaults.get("Failover Test - Subnet Mask"),
        default_vpg_settings.get("failover_test_subnet_mask"),
    )
    resolve_field(
        resolved_row,
        "Failover Test - Default Gateway",
        recovery_defaults.get("Failover Test - Default Gateway"),
        default_vpg_settings.get("failover_test_default_gateway"),
    )
    resolve_field(
        resolved_row,
        "Failover Test - Preferred DNS Server",
        recovery_defaults.get("Failover Test - Preferred DNS Server"),
        default_vpg_settings.get("failover_test_preferred_dns_server"),
    )
    resolve_field(
        resolved_row,
        "Failover Test - Alternate DNS Server",
        recovery_defaults.get("Failover Test - Alternate DNS Server"),
        default_vpg_settings.get("failover_test_alternate_dns_server"),
    )
    resolve_field(
        resolved_row,
        "Failover Test - DNS Suffix",
        recovery_defaults.get("Failover Test - DNS Suffix"),
        default_vpg_settings.get("failover_test_dns_suffix"),
    )

    return resolved_row


def resolve_vm_replication_defaults(row: dict, vpg_defaults: dict) -> dict:
    resolved_row = dict(row)
    vpg = vpg_defaults.get(row.get("VPG Name"), {})
    apply_vpg_site_context(resolved_row, vpg)
    resolve_field(resolved_row, "Boot Order Meta Group Name", vpg.get("Boot Order Meta Group Name"))
    resolve_field(resolved_row, "Recovery Host Name", vpg.get("Recovery Host Name"))
    resolve_field(resolved_row, "Recovery Datastore Name", vpg.get("Recovery Datastore Name"))
    resolve_field(resolved_row, "Recovery Folder Name", vpg.get("Recovery Folder Name"))
    resolve_field(resolved_row, "Journal Datastore Name", vpg.get("Journal Datastore Name"))
    copy_vpg_storage_settings(resolved_row, vpg)
    return resolved_row


def resolve_vm_storage_defaults(row: dict, vpg_defaults: dict) -> dict:
    resolved_row = dict(row)
    vpg = vpg_defaults.get(row.get("VPG Name"), {})
    apply_vpg_site_context(resolved_row, vpg)
    resolve_field(resolved_row, "Disk Provisioning Override", vpg.get("Disk Provisioning Override"))
    resolve_field(resolved_row, "Volume Sync Type", vpg.get("Volume Sync Type"))
    return resolved_row


def resolve_vm_nic_defaults(row: dict, vpg_defaults: dict) -> dict:
    resolved_row = dict(row)
    vpg = vpg_defaults.get(row.get("VPG Name"), {})
    apply_vpg_site_context(resolved_row, vpg)
    resolve_field(
        resolved_row,
        "Failover Live / Move - Network Name",
        vpg.get("Failover Live / Move - Network Name"),
    )
    resolve_field(
        resolved_row,
        "Failover Live / Move - Create new MAC address",
        vpg.get("Failover Live / Move - Create new MAC address"),
    )
    resolve_field(
        resolved_row,
        "Failover Live / Move - Change vNIC IP Config",
        vpg.get("Failover Live / Move - Change vNIC IP Config"),
    )
    resolve_field(
        resolved_row,
        "Failover Live / Move - Subnet Mask",
        vpg.get("Failover Live / Move - Subnet Mask"),
    )
    resolve_field(
        resolved_row,
        "Failover Live / Move - Default Gateway",
        vpg.get("Failover Live / Move - Default Gateway"),
    )
    resolve_field(
        resolved_row,
        "Failover Live / Move - Preferred DNS Server",
        vpg.get("Failover Live / Move - Preferred DNS Server"),
    )
    resolve_field(
        resolved_row,
        "Failover Live / Move - Alternate DNS Server",
        vpg.get("Failover Live / Move - Alternate DNS Server"),
    )
    resolve_field(
        resolved_row,
        "Failover Live / Move - DNS Suffix",
        vpg.get("Failover Live / Move - DNS Suffix"),
    )
    resolve_field(
        resolved_row,
        "Failover Test - Network Name",
        vpg.get("Failover Test Network Name"),
    )
    resolve_field(
        resolved_row,
        "Failover Test - Create new MAC address",
        vpg.get("Failover Test - Create new MAC address"),
    )
    resolve_field(
        resolved_row,
        "Failover Test - Change vNIC IP Config",
        vpg.get("Failover Test - Change vNIC IP Config"),
    )
    resolve_field(
        resolved_row,
        "Failover Test - Subnet Mask",
        vpg.get("Failover Test - Subnet Mask"),
    )
    resolve_field(
        resolved_row,
        "Failover Test - Default Gateway",
        vpg.get("Failover Test - Default Gateway"),
    )
    resolve_field(
        resolved_row,
        "Failover Test - Preferred DNS Server",
        vpg.get("Failover Test - Preferred DNS Server"),
    )
    resolve_field(
        resolved_row,
        "Failover Test - Alternate DNS Server",
        vpg.get("Failover Test - Alternate DNS Server"),
    )
    resolve_field(
        resolved_row,
        "Failover Test - DNS Suffix",
        vpg.get("Failover Test - DNS Suffix"),
    )
    return resolved_row


def apply_vpg_site_context(row: dict, vpg: dict) -> None:
    resolve_field(row, "Protected Site Name", vpg.get("Effective Protected ZVM Site Name"))
    resolve_field(row, "Recovery Site Name", vpg.get("Effective Recovery ZVM Site Name"))
    row["Effective Protected ZVM Site Name"] = first_value(
        row.get("Protected Site Name"),
        vpg.get("Effective Protected ZVM Site Name"),
    )
    row["Effective Recovery ZVM Site Name"] = first_value(
        row.get("Recovery Site Name"),
        vpg.get("Effective Recovery ZVM Site Name"),
    )


def copy_vpg_storage_settings(row: dict, vpg: dict) -> None:
    for field_name in (
        "Journal Size Hard Limit Value",
        "Journal Size Hard Limit Unit",
        "Journal Size Warning Threshold Value",
        "Journal Size Warning Threshold Unit",
        "Scratch Journal Datastore Name",
        "Scratch Journal Size Hard Limit Value",
        "Scratch Journal Size Hard Limit Unit",
        "Scratch Journal Size Warning Threshold Value",
        "Scratch Journal Size Warning Threshold Unit",
    ):
        resolve_field(row, field_name, vpg.get(field_name))


def build_recovery_site_defaults(resolved_recovery_zvm_sites: list[dict]) -> dict:
    return {
        row["Effective Recovery ZVM Site Name"]: row
        for row in resolved_recovery_zvm_sites
        if row.get("Effective Recovery ZVM Site Name")
    }


def build_vpg_defaults(resolved_vpgs: list[dict]) -> dict:
    return {
        row["VPG Name"]: row
        for row in resolved_vpgs
        if row.get("VPG Name")
    }


def resolve_field(row: dict, field_name: str, *defaults) -> None:
    row[field_name] = first_value(row.get(field_name), *defaults)


def first_value(*values):
    for value in values:
        if clean_value(value) is not None:
            return clean_value(value)

    return None


def value_unit_value(value_unit: dict | None):
    if not value_unit:
        return None

    return value_unit.get("value")


def value_unit_unit(value_unit: dict | None):
    if not value_unit:
        return None

    return value_unit.get("unit")


def get_validation_status(validations: dict) -> str:
    if all(validation["status"] == "passed" for validation in validations.values()):
        return "passed"

    return "failed"


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
