import logging
from pprint import pformat
from pathlib import Path
import traceback

from pydantic import ValidationError

from ingestion.reader import load_excel_workbook, validate_required_sheets
from extraction.zerto_data import extract_zerto_data
from extraction.hypervisor import extract_hypervisor_data
from extraction.vpg_settings import extract_default_vpg_settings
from extraction.recovery_zvm_sites import extract_recovery_zvm_sites
from extraction.tables import extract_sheet_table
from extraction.vpgs import extract_vpgs
from validation.default_vpg_settings import validate_default_vpg_settings
from validation.zerto_data import validate_zerto_data
from validation.hypervisor import validate_hypervisor_data
from validation.recovery_zvm_sites import validate_recovery_zvm_sites
from validation.vpgs import validate_vpgs
from validation.vm_replication import validate_vm_replication
from validation.vm_storage import validate_vm_storage
from validation.vm_nics import validate_vm_nics
from validation.error_formatting import WorkbookValidationError, format_validation_errors
from payload.json_output import (
    API_PAYLOAD_OUTPUT_FILE,
    make_json_safe,
    write_zerto_json_dump,
)
from payload.manifest_output import MANIFEST_OUTPUT_FILE


LOG_FILE = Path("outputs/vca_check.log")
RAW_LOG_STREAM = None


def raw_log(label: str, value=None) -> None:
    if RAW_LOG_STREAM is None:
        return

    RAW_LOG_STREAM.write(f"\n--- {label} ---\n")
    if value is not None:
        RAW_LOG_STREAM.write(pformat(value, width=120))
        RAW_LOG_STREAM.write("\n")
    RAW_LOG_STREAM.flush()


def main():
    setup_logging()

    excel_file = "files/manifest ready VCA Data - 0.109.xlsx"
    raw_log("run_started", {"source_file": excel_file})
    logging.info("Starting VCA workbook validation run")
    logging.info("Source workbook: %s", excel_file)

    logging.info("Loading workbook")
    workbook = load_excel_workbook(excel_file)
    validate_required_sheets(workbook)
    raw_log("workbook", {"sheets": workbook.sheetnames})

    print("\nWorkbook loaded successfully")
    logging.info("Workbook loaded successfully")

    logging.info("Extracting workbook data")
    zerto_data = extract_zerto_data(excel_file)
    raw_log("extracted.zerto_data", {
        "columns": zerto_data.get("columns"),
        "summary": zerto_data.get("summary"),
        "records": zerto_data.get("records"),
    })
    hypervisor_data = extract_hypervisor_data(excel_file)
    raw_log("extracted.hypervisor_data", hypervisor_data)
    vpg_settings = extract_default_vpg_settings(excel_file, print_output=False)
    raw_log("extracted.default_vpg_settings", vpg_settings)
    recovery_zvm_sites = extract_recovery_zvm_sites(excel_file)
    raw_log("extracted.recovery_zvm_sites", recovery_zvm_sites)
    vpgs = extract_vpgs(excel_file)
    raw_log("extracted.vpgs", vpgs)
    vm_replication = extract_sheet_table(
        excel_file,
        "VM Replication",
        "VPG Name",
        table_name="VM_Replication",
    )
    raw_log("extracted.vm_replication", vm_replication)
    vm_storage = extract_sheet_table(
        excel_file,
        "VM Storage", "VPG Name", table_name="VM_Storage",
    )
    raw_log("extracted.vm_storage", vm_storage)
    vm_nics = extract_sheet_table(
        excel_file,
        "VM NICs",
        "VPG Name",
        table_name="VM_NICs",
    )
    raw_log("extracted.vm_nics", vm_nics)
    extended_journal = extract_sheet_table(
        excel_file,
        "Extended Journal",
        "VPG Name",
        table_name="Extended_Journal_Copies",
    )
    raw_log("extracted.extended_journal", extended_journal)
    log_extraction_summary(
        zerto_data,
        hypervisor_data,
        recovery_zvm_sites,
        vpgs,
        vm_replication,
        vm_storage,
        vm_nics,
    )
    validations = {}

    try:
        result = validate_zerto_data(zerto_data)
        validations["zerto_data"] = validation_passed(result)
        raw_log("validation.zerto_data", validations["zerto_data"])
        print("\nZerto Data validation passed")
        print("----------------------------")
        log_validation_passed("Zerto Data")

    except WorkbookValidationError as error:
        print("\nZerto Data validation failed")
        print("----------------------------")
        print_validation_messages(error.messages)
        log_validation_failed("Zerto Data", error.messages)
        validations["zerto_data"] = validation_failed(error.messages)
        raw_log("validation.zerto_data", validations["zerto_data"])
        stop_after_validation_failure("Zerto Data")
        return

    try:
        result = validate_hypervisor_data(hypervisor_data)
        validations["hypervisor_data"] = validation_passed(result)
        raw_log("validation.hypervisor_data", validations["hypervisor_data"])
        print("\nHypervisor Data validation passed")
        print("---------------------------------")
        log_validation_passed("Hypervisor Data")

    except WorkbookValidationError as error:
        print("\nHypervisor Data validation failed")
        print("---------------------------------")
        print_validation_messages(error.messages)
        log_validation_failed("Hypervisor Data", error.messages)
        validations["hypervisor_data"] = validation_failed(error.messages)
        raw_log("validation.hypervisor_data", validations["hypervisor_data"])
        stop_after_validation_failure("Hypervisor Data")
        return

    except ValidationError as error:
        messages = format_validation_errors(error)
        print("\nHypervisor Data validation failed")
        print("---------------------------------")
        print_validation_messages(messages)
        log_validation_failed("Hypervisor Data", messages)
        validations["hypervisor_data"] = validation_failed(
            messages,
            error.errors(include_url=False),
        )
        raw_log("validation.hypervisor_data", validations["hypervisor_data"])
        stop_after_validation_failure("Hypervisor Data")
        return

    except ValueError as error:
        print("\nHypervisor Data validation failed")
        print("---------------------------------")
        print(f"- {error}")
        log_validation_failed("Hypervisor Data", [str(error)])
        validations["hypervisor_data"] = validation_failed([str(error)])
        raw_log("validation.hypervisor_data", validations["hypervisor_data"])
        stop_after_validation_failure("Hypervisor Data")
        return

    try:
        result = validate_default_vpg_settings(vpg_settings)
        validations["default_vpg_settings"] = validation_passed(result)
        raw_log(
            "validation.default_vpg_settings",
            validations["default_vpg_settings"],
        )
        print("\nDefault VPG Settings validation passed")
        print("--------------------------------------")
        log_validation_passed("Default VPG Settings")

    except ValidationError as error:
        messages = format_validation_errors(error)
        print("\nDefault VPG Settings validation failed")
        print("--------------------------------------")
        print_validation_messages(messages)
        log_validation_failed("Default VPG Settings", messages)
        validations["default_vpg_settings"] = validation_failed(
            messages,
            error.errors(include_url=False),
        )
        raw_log(
            "validation.default_vpg_settings",
            validations["default_vpg_settings"],
        )
        stop_after_validation_failure("Default VPG Settings")
        return

    try:
        result = validate_recovery_zvm_sites(recovery_zvm_sites, vpg_settings)
        validations["recovery_zvm_sites"] = validation_passed(result)
        raw_log(
            "validation.recovery_zvm_sites",
            validations["recovery_zvm_sites"],
        )
        print("\nRecovery ZVM Sites validation passed")
        print("------------------------------------")
        log_validation_passed("Recovery ZVM Sites")

    except WorkbookValidationError as error:
        print("\nRecovery ZVM Sites validation failed")
        print("------------------------------------")
        print_validation_messages(error.messages)
        log_validation_failed("Recovery ZVM Sites", error.messages)
        validations["recovery_zvm_sites"] = validation_failed(error.messages)
        raw_log(
            "validation.recovery_zvm_sites",
            validations["recovery_zvm_sites"],
        )
        stop_after_validation_failure("Recovery ZVM Sites")
        return

    except ValidationError as error:
        messages = format_validation_errors(error)
        print("\nRecovery ZVM Sites validation failed")
        print("------------------------------------")
        print_validation_messages(messages)
        log_validation_failed("Recovery ZVM Sites", messages)
        validations["recovery_zvm_sites"] = validation_failed(
            messages,
            error.errors(include_url=False),
        )
        raw_log(
            "validation.recovery_zvm_sites",
            validations["recovery_zvm_sites"],
        )
        stop_after_validation_failure("Recovery ZVM Sites")
        return

    try:
        result = validate_vpgs(vpgs, vpg_settings, recovery_zvm_sites)
        validations["vpgs"] = validation_passed(result)
        raw_log("validation.vpgs", validations["vpgs"])
        print("\nVPGs validation passed")
        print("----------------------")
        log_validation_passed("VPGs")

    except WorkbookValidationError as error:
        print("\nVPGs validation failed")
        print("----------------------")
        print_validation_messages(error.messages)
        log_validation_failed("VPGs", error.messages)
        validations["vpgs"] = validation_failed(error.messages)
        raw_log("validation.vpgs", validations["vpgs"])
        stop_after_validation_failure("VPGs")
        return

    except ValidationError as error:
        messages = format_validation_errors(error)
        print("\nVPGs validation failed")
        print("----------------------")
        print_validation_messages(messages)
        log_validation_failed("VPGs", messages)
        validations["vpgs"] = validation_failed(
            messages,
            error.errors(include_url=False),
        )
        raw_log("validation.vpgs", validations["vpgs"])
        stop_after_validation_failure("VPGs")
        return

    try:
        result = validate_vm_replication(vm_replication)
        validations["vm_replication"] = validation_passed(result)
        raw_log("validation.vm_replication", validations["vm_replication"])
        print("\nVM Replication validation passed")
        print("--------------------------------")
        log_validation_passed("VM Replication")

    except WorkbookValidationError as error:
        print("\nVM Replication validation failed")
        print("--------------------------------")
        print_validation_messages(error.messages)
        log_validation_failed("VM Replication", error.messages)
        validations["vm_replication"] = validation_failed(error.messages)
        raw_log("validation.vm_replication", validations["vm_replication"])
        stop_after_validation_failure("VM Replication")
        return

    except ValidationError as error:
        messages = format_validation_errors(error)
        print("\nVM Replication validation failed")
        print("--------------------------------")
        print_validation_messages(messages)
        log_validation_failed("VM Replication", messages)
        validations["vm_replication"] = validation_failed(
            messages,
            error.errors(include_url=False),
        )
        raw_log("validation.vm_replication", validations["vm_replication"])
        stop_after_validation_failure("VM Replication")
        return

    try:
        result = validate_vm_storage(vm_storage)
        validations["vm_storage"] = validation_passed(result)
        raw_log("validation.vm_storage", validations["vm_storage"])
        print("\nVM Storage validation passed")
        print("----------------------------")
        log_validation_passed("VM Storage")

    except WorkbookValidationError as error:
        print("\nVM Storage validation failed")
        print("----------------------------")
        print_validation_messages(error.messages)
        log_validation_failed("VM Storage", error.messages)
        validations["vm_storage"] = validation_failed(error.messages)
        raw_log("validation.vm_storage", validations["vm_storage"])
        stop_after_validation_failure("VM Storage")
        return

    except ValidationError as error:
        messages = format_validation_errors(error)
        print("\nVM Storage validation failed")
        print("----------------------------")
        print_validation_messages(messages)
        log_validation_failed("VM Storage", messages)
        validations["vm_storage"] = validation_failed(
            messages,
            error.errors(include_url=False),
        )
        raw_log("validation.vm_storage", validations["vm_storage"])
        stop_after_validation_failure("VM Storage")
        return

    try:
        result = validate_vm_nics(
            vm_nics,
            vpg_settings,
            recovery_zvm_sites,
            vpgs,
        )
        validations["vm_nics"] = validation_passed(result)
        raw_log("validation.vm_nics", validations["vm_nics"])
        print("\nVM NICs validation passed")
        print("-------------------------")
        log_validation_passed("VM NICs")

    except WorkbookValidationError as error:
        print("\nVM NICs validation failed")
        print("-------------------------")
        print_validation_messages(error.messages)
        log_validation_failed("VM NICs", error.messages)
        validations["vm_nics"] = validation_failed(error.messages)
        raw_log("validation.vm_nics", validations["vm_nics"])
        stop_after_validation_failure("VM NICs")
        return

    except ValidationError as error:
        messages = format_validation_errors(error)
        print("\nVM NICs validation failed")
        print("-------------------------")
        print_validation_messages(messages)
        log_validation_failed("VM NICs", messages)
        validations["vm_nics"] = validation_failed(
            messages,
            error.errors(include_url=False),
        )
        raw_log("validation.vm_nics", validations["vm_nics"])
        stop_after_validation_failure("VM NICs")
        return

    logging.info("Generating JSON output")
    output_path = write_zerto_json_dump(
        excel_file=excel_file,
        zerto_data=zerto_data,
        hypervisor_data=hypervisor_data,
        default_vpg_settings=vpg_settings,
        recovery_zvm_sites=recovery_zvm_sites,
        vpgs=vpgs,
        vm_replication=vm_replication,
        vm_storage=vm_storage,
        vm_nics=vm_nics,
        extended_journal=extended_journal,
        validations=validations,
    )
    raw_log("outputs", {
        "diagnostic_output_file": str(output_path),
        "api_payload_output_file": API_PAYLOAD_OUTPUT_FILE,
        "log_file": str(LOG_FILE),
    })
    print(f"\nJSON output written to {output_path}")
    print(f"Zerto API payload written to {API_PAYLOAD_OUTPUT_FILE}")
    print(f"VCA Run manifest written to {MANIFEST_OUTPUT_FILE}")
    logging.info("JSON output written to %s", output_path)
    logging.info("Zerto API payload written to %s", API_PAYLOAD_OUTPUT_FILE)
    logging.info("VCA Run manifest written to %s", MANIFEST_OUTPUT_FILE)
    logging.info("Run complete")
    print(f"Detailed log written to {LOG_FILE}")


def print_zerto_summary(summary: dict) -> None:
    print("\nZerto Data Summary")
    print("------------------")

    print_topic_heading("ZVM Sites")
    for index, site in enumerate(summary["zvm_sites"]):
        if index > 0:
            print()
        print(f"- Site Name: {site['site_name']}")
        print(f"  Protected: {site['protected']}")
        print(f"  Recovery: {site['recovery']}")

    print_topic_heading("Labels")
    print_named_list("Scopes", summary["labels"]["scopes"])
    print_named_list("Waves", summary["labels"]["waves"])
    print_named_list("Application Names", summary["labels"]["application_names"])
    print_named_list(
        "Application Environments",
        summary["labels"]["application_environments"],
    )
    print_named_list("Data Types", summary["labels"]["data_types"])

    print_topic_heading("Recovery Scripts")
    for script in summary["recovery_scripts"]:
        print(f"- {script}")

    print_topic_heading("Boot Order Groups")
    for index, group in enumerate(summary["boot_order_groups"]):
        if index > 0:
            print()
        print(f"- Meta Group: {group['meta_group_name']}")
        print(f"  Group ID: {group['group_id']}")
        print(f"  Group Name: {group['group_name']}")
        print(f"  Boot Delay: {group['boot_delay_secs']} seconds")


def print_hypervisor_summary(hypervisor_data: dict) -> None:
    print("\nHypervisor Data Summary")
    print("-----------------------")

    print_topic_heading("Protected VMs")
    for index, vm in enumerate(hypervisor_data["protected_vms"]):
        if index > 0:
            print()
        print(f"- Site: {vm.get('Protected ZVM Site Name')}")
        print(f"  VM Name: {vm.get('VM Name')}")
        print(f"  CPU Count: {vm.get('CPU Count')}")
        print(f"  Memory: {vm.get('Memory (GiB)')} GiB")

    print_topic_heading("Protected VM Volumes")
    for index, volume in enumerate(hypervisor_data["protected_vm_volumes"]):
        if index > 0:
            print()
        print(f"- VM: {volume.get('Protected ZVM Site Name')} | {volume.get('VM Name')}")
        print(f"  Volume: {volume.get('Volume Location')}")
        print(f"  Size: {volume.get('Provisioned Size (GiB)')} GiB")

    print_topic_heading("Protected VM NICs")
    for index, nic in enumerate(hypervisor_data["protected_vm_nics"]):
        if index > 0:
            print()
        print(f"- VM: {nic.get('Protected ZVM Site Name')} | {nic.get('VM Name')}")
        print(f"  NIC: {nic.get('NIC Name')}")
        print(f"  Network: {nic.get('Network Name')}")

    print_topic_heading("Recovery Hosts")
    for index, host in enumerate(hypervisor_data["recovery_hosts"]):
        if index > 0:
            print()
        print(f"- Site: {host.get('Recovery ZVM Site Name')}")
        print(f"  Host: {host.get('Host Name')}")

    print_topic_heading("Recovery Datastores")
    for index, datastore in enumerate(hypervisor_data["recovery_datastores"]):
        if index > 0:
            print()
        print(f"- Site: {datastore.get('Recovery ZVM Site Name')}")
        print(f"  Datastore: {datastore.get('Datastore Name')}")
        print(f"  Size: {datastore.get('Size (GiB)')} GiB")

    print_topic_heading("Recovery Folders")
    for index, folder in enumerate(hypervisor_data["recovery_folders"]):
        if index > 0:
            print()
        print(f"- Site: {folder.get('Recovery ZVM Site Name')}")
        print(f"  Folder: {folder.get('Folder Name')}")

    print_topic_heading("Recovery Networks")
    for index, network in enumerate(hypervisor_data["recovery_networks"]):
        if index > 0:
            print()
        print(f"- Site: {network.get('Recovery ZVM Site Name')}")
        print(f"  Network: {network.get('Network Name')}")


def print_topic_heading(title: str) -> None:
    print(f"\n{title}\n")


def setup_logging() -> None:
    global RAW_LOG_STREAM

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    RAW_LOG_STREAM = LOG_FILE.open("w", encoding="utf-8")
    logging.disable(logging.CRITICAL)


def log_extraction_summary(
    zerto_data: dict,
    hypervisor_data: dict,
    recovery_zvm_sites: list,
    vpgs: list,
    vm_replication: list,
    vm_storage: list,
    vm_nics: list,
) -> None:
    logging.info("Extraction complete")
    logging.info(
        "Zerto Data: %s sites, %s recovery scripts, %s boot order groups",
        len(zerto_data["summary"]["zvm_sites"]),
        len(zerto_data["summary"]["recovery_scripts"]),
        len(zerto_data["summary"]["boot_order_groups"]),
    )
    logging.info(
        "Hypervisor Data: %s protected VMs, %s volumes, %s NICs, "
        "%s recovery hosts, %s datastores, %s folders, %s networks",
        len(hypervisor_data["protected_vms"]),
        len(hypervisor_data["protected_vm_volumes"]),
        len(hypervisor_data["protected_vm_nics"]),
        len(hypervisor_data["recovery_hosts"]),
        len(hypervisor_data["recovery_datastores"]),
        len(hypervisor_data["recovery_folders"]),
        len(hypervisor_data["recovery_networks"]),
    )
    logging.info("Recovery ZVM Sites rows: %s", len(recovery_zvm_sites))
    logging.info("VPG rows: %s", len(vpgs))
    logging.info("VM Replication rows: %s", len(vm_replication))
    logging.info("VM Storage rows: %s", len(vm_storage))
    logging.info("VM NIC rows: %s", len(vm_nics))


def log_validation_passed(section_name: str) -> None:
    logging.info("%s validation passed", section_name)


def log_validation_failed(section_name: str, messages: list[str]) -> None:
    logging.warning("%s validation failed with %s error(s)", section_name, len(messages))

    for message in messages:
        logging.warning("%s validation error:\n%s", section_name, message)


def print_named_list(label: str, values: list) -> None:
    print(f"- {label}:")

    if not values:
        print("  Not set")
        print()
        return

    for value in values:
        print(f"  - {value}")

    print()


def print_validation_messages(messages: list[str]) -> None:
    for index, message in enumerate(messages):
        if index > 0:
            print()
        print(f"- {message}")


def stop_after_validation_failure(section_name: str) -> None:
    message = (
        f"Stopping validation because {section_name} failed. "
        "Fix this section and run VCA Check again."
    )
    print(f"\n{message}")
    raw_log("run_stopped", {
        "failed_section": section_name,
        "reason": "Validation failed; later sheets were not validated.",
    })
    print(f"Detailed log written to {LOG_FILE}")


def validation_passed(result) -> dict:
    return {
        "status": "passed",
        "records": make_json_safe(result),
    }


def validation_failed(messages: list[str], errors: list | None = None) -> dict:
    return {
        "status": "failed",
        "messages": messages,
        "errors": errors or [],
    }


def print_hypervisor_validation(data: dict) -> None:
    print_key_values({
        "Protected VMs": len(data["protected_vms"]),
        "Protected VM Volumes": len(data["protected_vm_volumes"]),
        "Protected VM NICs": len(data["protected_vm_nics"]),
        "Recovery Hosts": len(data["recovery_hosts"]),
        "Recovery Datastores": len(data["recovery_datastores"]),
        "Recovery Folders": len(data["recovery_folders"]),
        "Recovery Networks": len(data["recovery_networks"]),
    })


def print_default_vpg_settings_validation(settings) -> None:
    rows = {
        "Protected Site": settings.protected_site,
        "Recovery Site": settings.recovery_site,
        "VPG Type": settings.vpg_type,
        "Priority": settings.priority,
        "Journal History": format_value_unit(settings.journal_history),
        "Target RPO Alert": format_value_unit(settings.target_rpo_alert),
        "Test Reminder": settings.test_reminder,
        "Journal Size Hard Limit": format_value_unit(settings.journal_size_hard_limit),
        "Journal Size Warning": format_value_unit(settings.journal_size_warning),
        "Scratch Journal Size Hard Limit": format_value_unit(
            settings.scratch_journal_size_hard_limit,
        ),
        "Scratch Journal Size Warning": format_value_unit(
            settings.scratch_journal_size_warning,
        ),
        "WAN Compression": settings.wan_compression,
    }

    print_key_values(rows)


def print_recovery_zvm_sites_validation(sites: list) -> None:
    for index, site in enumerate(sites, start=1):
        print(f"\nRecovery ZVM Site #{index}")
        print_key_values({
            "Recovery ZVM Site Name": site.recovery_zvm_site_name,
            "VPG Type": site.vpg_type,
            "Priority": site.priority,
            "Recovery Host Name": site.recovery_host_name,
            "Recovery Datastore Name": site.recovery_datastore_name,
            "Journal History": format_optional_value_unit(
                site.journal_history_value,
                site.journal_history_unit,
            ),
            "Target RPO Alert": format_optional_value_unit(
                site.target_rpo_alert_value,
                site.target_rpo_alert_unit,
            ),
            "Test Reminder": site.test_reminder,
            "Journal Datastore Name": site.journal_datastore_name,
            "Journal Size Hard Limit": format_optional_value_unit(
                site.journal_size_hard_limit_value,
                site.journal_size_hard_limit_unit,
            ),
            "Journal Size Warning Threshold": format_optional_value_unit(
                site.journal_size_warning_threshold_value,
                site.journal_size_warning_threshold_unit,
            ),
            "Scratch Journal Datastore Name": site.scratch_journal_datastore_name,
            "Scratch Journal Size Hard Limit": format_optional_value_unit(
                site.scratch_journal_size_hard_limit_value,
                site.scratch_journal_size_hard_limit_unit,
            ),
            "Scratch Journal Size Warning Threshold": format_optional_value_unit(
                site.scratch_journal_size_warning_threshold_value,
                site.scratch_journal_size_warning_threshold_unit,
            ),
            "Enable WAN Traffic Compression": site.enable_wan_traffic_compression,
            "Disk Provisioning Override": site.disk_provisioning_override,
            "Failover Live / Move Network Name": site.failover_live_move_network_name,
            "Failover Test Network Name": site.failover_test_network_name,
            "Recovery Folder Name": site.recovery_folder_name,
            "Pre-Recovery Script Name": site.pre_recovery_script_name,
            "Pre-Recovery Script Parameters": site.pre_recovery_script_parameters,
            "Pre-Recovery Script Execution Timeout (Seconds)": (
                site.pre_recovery_script_execution_timeout_seconds
            ),
            "Post-Recovery Script Name": site.post_recovery_script_name,
            "Post-Recovery Script Parameters": site.post_recovery_script_parameters,
            "Post-Recovery Script Execution Timeout (Seconds)": (
                site.post_recovery_script_execution_timeout_seconds
            ),
            "Failover Live / Move - Create new MAC address": (
                site.failover_live_move_create_new_mac_address
            ),
            "Failover Live / Move - Change vNIC IP Config": (
                site.failover_live_move_change_vnic_ip_config
            ),
            "Failover Live / Move - Subnet Mask": site.failover_live_move_subnet_mask,
            "Failover Live / Move - Default Gateway": (
                site.failover_live_move_default_gateway
            ),
            "Failover Live / Move - Preferred DNS Server": (
                site.failover_live_move_preferred_dns_server
            ),
            "Failover Live / Move - Alternate DNS Server": (
                site.failover_live_move_alternate_dns_server
            ),
            "Failover Live / Move - DNS Suffix": site.failover_live_move_dns_suffix,
            "Failover Test - Create new MAC address": (
                site.failover_test_create_new_mac_address
            ),
            "Failover Test - Change vNIC IP Config": (
                site.failover_test_change_vnic_ip_config
            ),
            "Failover Test - Subnet Mask": site.failover_test_subnet_mask,
            "Failover Test - Default Gateway": site.failover_test_default_gateway,
            "Failover Test - Preferred DNS Server": (
                site.failover_test_preferred_dns_server
            ),
            "Failover Test - Alternate DNS Server": (
                site.failover_test_alternate_dns_server
            ),
            "Failover Test - DNS Suffix": site.failover_test_dns_suffix,
        })


def print_vpgs_validation(vpgs: list) -> None:
    for index, vpg in enumerate(vpgs, start=1):
        print(f"\nVPG #{index}")
        print_key_values({
            "VPG Name": vpg.vpg_name,
            "Protected ZVM Site Name": vpg.protected_zvm_site_name,
            "Recovery ZVM Site Name": vpg.recovery_zvm_site_name,
            "VPG Type": vpg.vpg_type,
            "Priority": vpg.priority,
            "VPG Description": vpg.vpg_description,
            "Label 1": vpg.label_1,
            "Label 2": vpg.label_2,
            "Label 3": vpg.label_3,
            "Label 4": vpg.label_4,
            "Label 5": vpg.label_5,
            "Boot Order Meta Group Name": vpg.boot_order_meta_group_name,
            "Recovery Host Name": vpg.recovery_host_name,
            "Recovery Datastore Name": vpg.recovery_datastore_name,
            "Journal History": format_optional_value_unit(
                vpg.journal_history_value,
                vpg.journal_history_unit,
            ),
            "Target RPO Alert": format_optional_value_unit(
                vpg.target_rpo_alert_value,
                vpg.target_rpo_alert_unit,
            ),
            "Test Reminder": vpg.test_reminder,
            "Journal Datastore Name": vpg.journal_datastore_name,
            "Journal Size Hard Limit": format_optional_value_unit(
                vpg.journal_size_hard_limit_value,
                vpg.journal_size_hard_limit_unit,
            ),
            "Journal Size Warning Threshold": format_optional_value_unit(
                vpg.journal_size_warning_threshold_value,
                vpg.journal_size_warning_threshold_unit,
            ),
            "Scratch Journal Datastore Name": vpg.scratch_journal_datastore_name,
            "Scratch Journal Size Hard Limit": format_optional_value_unit(
                vpg.scratch_journal_size_hard_limit_value,
                vpg.scratch_journal_size_hard_limit_unit,
            ),
            "Scratch Journal Size Warning Threshold": format_optional_value_unit(
                vpg.scratch_journal_size_warning_threshold_value,
                vpg.scratch_journal_size_warning_threshold_unit,
            ),
            "Enable WAN Traffic Compression": vpg.enable_wan_traffic_compression,
            "Disk Provisioning Override": vpg.disk_provisioning_override,
            "Failover Live / Move - Network Name": (
                vpg.failover_live_move_network_name
            ),
            "Failover Test Network Name": vpg.failover_test_network_name,
            "Recovery Folder Name": vpg.recovery_folder_name,
            "Pre-Recovery Script Name": vpg.pre_recovery_script_name,
            "Pre-Recovery Script Parameters": vpg.pre_recovery_script_parameters,
            "Pre-Recovery Script Execution Timeout (Seconds)": (
                vpg.pre_recovery_script_execution_timeout_seconds
            ),
            "Post-Recovery Script Name": vpg.post_recovery_script_name,
            "Post-Recovery Script Parameters": vpg.post_recovery_script_parameters,
            "Post-Recovery Script Execution Timeout (Seconds)": (
                vpg.post_recovery_script_execution_timeout_seconds
            ),
        })


def print_vm_replication_validation(rows: list) -> None:
    for index, row in enumerate(rows, start=1):
        print(f"\nVM Replication Row #{index}")
        print_key_values({
            "VPG Name": row.vpg_name,
            "VM Name": row.vm_name,
            "Label 1": row.label_1,
            "Label 2": row.label_2,
            "Label 3": row.label_3,
            "Label 4": row.label_4,
            "Label 5": row.label_5,
            "Boot Order Group Name": row.boot_order_group_name,
            "Recovery Host Name": row.recovery_host_name,
            "Recovery Datastore Name": row.recovery_datastore_name,
            "Recovery Folder Name": row.recovery_folder_name,
            "Journal Datastore Name": row.journal_datastore_name,
            "Journal Size Hard Limit": format_optional_value_unit(
                row.journal_size_hard_limit_value,
                row.journal_size_hard_limit_unit,
            ),
            "Journal Size Warning Threshold": format_optional_value_unit(
                row.journal_size_warning_threshold_value,
                row.journal_size_warning_threshold_unit,
            ),
            "Scratch Journal Datastore Name": row.scratch_journal_datastore_name,
            "Scratch Journal Size Hard Limit": format_optional_value_unit(
                row.scratch_journal_size_hard_limit_value,
                row.scratch_journal_size_hard_limit_unit,
            ),
            "Scratch Journal Size Warning Threshold": format_optional_value_unit(
                row.scratch_journal_size_warning_threshold_value,
                row.scratch_journal_size_warning_threshold_unit,
            ),
        })


def print_vm_storage_validation(rows: list) -> None:
    for index, row in enumerate(rows, start=1):
        print(f"\nVM Storage Row #{index}")
        print_key_values({
            "VPG Name": row.vpg_name,
            "VM Name": row.vm_name,
            "Protected Volume Location": row.protected_volume_location,
            "Size (GiB)": row.size_gib,
            "Recovery Volume Location": row.recovery_volume_location,
            "Recovery Raw Device Name": row.recovery_raw_device_name,
            "Disk Provisioning Override": row.disk_provisioning_override,
            "Volume Sync Type": row.volume_sync_type,
        })


def print_vm_nics_validation(rows: list) -> None:
    for index, row in enumerate(rows, start=1):
        print(f"\nVM NICs Row #{index}")
        print_key_values({
            "VPG Name": row.vpg_name,
            "VM Name": row.vm_name,
            "NIC Name": row.nic_name,
            "Protected Network Name": row.protected_network_name,
            "Failover Live / Move - Network Name": (
                row.failover_live_move_network_name
            ),
            "Failover Live / Move - Create new MAC address": (
                row.failover_live_move_create_new_mac_address
            ),
            "Failover Live / Move - Change vNIC IP Config": (
                row.failover_live_move_change_vnic_ip_config
            ),
            "Failover Live / Move - IP Address": row.failover_live_move_ip_address,
            "Failover Live / Move - Subnet Mask": row.failover_live_move_subnet_mask,
            "Failover Live / Move - Default Gateway": (
                row.failover_live_move_default_gateway
            ),
            "Failover Live / Move - Preferred DNS Server": (
                row.failover_live_move_preferred_dns_server
            ),
            "Failover Live / Move - Alternate DNS Server": (
                row.failover_live_move_alternate_dns_server
            ),
            "Failover Live / Move - DNS Suffix": row.failover_live_move_dns_suffix,
            "Failover Test - Network Name": row.failover_test_network_name,
            "Failover Test - Create new MAC address": (
                row.failover_test_create_new_mac_address
            ),
            "Failover Test - Change vNIC IP Config": (
                row.failover_test_change_vnic_ip_config
            ),
            "Failover Test - IP Address": row.failover_test_ip_address,
            "Failover Test - Subnet Mask": row.failover_test_subnet_mask,
            "Failover Test - Default Gateway": row.failover_test_default_gateway,
            "Failover Test - Preferred DNS Server": (
                row.failover_test_preferred_dns_server
            ),
            "Failover Test - Alternate DNS Server": (
                row.failover_test_alternate_dns_server
            ),
            "Failover Test - DNS Suffix": row.failover_test_dns_suffix,
        })


def print_key_values(rows: dict) -> None:
    for label, value in rows.items():
        print(f"- {label}: {format_display_value(value)}")


def format_value_unit(value_unit) -> str:
    return f"{value_unit.value:g} {value_unit.unit}"


def format_optional_value_unit(value, unit) -> str | None:
    if value is None and unit is None:
        return None

    if value is None:
        return unit

    if unit is None:
        return str(value)

    return f"{value:g} {unit}"


def format_display_value(value) -> str:
    if value is None:
        return "Not set"

    return str(value)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        raw_log("unhandled_exception", traceback.format_exc())
        raise
