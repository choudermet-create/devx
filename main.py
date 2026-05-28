from pydantic import ValidationError

from ingestion.reader import load_excel_workbook, validate_required_sheets
from extraction.zerto_data import extract_zerto_data
from extraction.hypervisor import extract_hypervisor_data
from extraction.vpg_settings import extract_default_vpg_settings
from extraction.recovery_zvm_sites import extract_recovery_zvm_sites
from extraction.tables import extract_sheet_table
from extraction.vpgs import extract_vpgs
from validation.default_vpg_settings import validate_default_vpg_settings
from validation.recovery_zvm_sites import validate_recovery_zvm_sites
from validation.vpgs import validate_vpgs
from validation.vm_replication import validate_vm_replication
from validation.vm_storage import validate_vm_storage
from validation.vm_nics import validate_vm_nics
from validation.error_formatting import format_validation_errors
from generate_zerto_json import generate_zerto_json


def main():
    excel_file = "files/basic2.xlsx"

    workbook = load_excel_workbook(excel_file)
    validate_required_sheets(workbook)

    print("\nWorkbook loaded successfully")

    zerto_data = extract_zerto_data(excel_file)
    hypervisor_data = extract_hypervisor_data(excel_file)
    vpg_settings = extract_default_vpg_settings(excel_file)
    recovery_zvm_sites = extract_recovery_zvm_sites(excel_file)
    vpgs = extract_vpgs(excel_file)
    vm_replication = extract_sheet_table(excel_file, "VM Replication", "VPG Name")
    vm_storage = extract_sheet_table(excel_file, "VM Storage", "VPG Name")
    vm_nics = extract_sheet_table(excel_file, "VM NICs", "VPG Name")

    print_zerto_summary(zerto_data["summary"])
    print_hypervisor_summary(hypervisor_data)

    try:
        validated_vpg_settings = validate_default_vpg_settings(vpg_settings)
        print("\nDefault VPG Settings validation passed")
        print("--------------------------------------")
        print_default_vpg_settings_validation(validated_vpg_settings)

    except ValidationError as error:
        print("\nDefault VPG Settings validation failed")
        print("--------------------------------------")
        for message in format_validation_errors(error):
            print(f"- {message}")

    try:
        validated_recovery_zvm_sites = validate_recovery_zvm_sites(recovery_zvm_sites)
        print("\nRecovery ZVM Sites validation passed")
        print("------------------------------------")
        print_recovery_zvm_sites_validation(validated_recovery_zvm_sites)

    except ValidationError as error:
        print("\nRecovery ZVM Sites validation failed")
        print("------------------------------------")
        for message in format_validation_errors(error):
            print(f"- {message}")

    try:
        validated_vpgs = validate_vpgs(vpgs)
        print("\nVPGs validation passed")
        print("----------------------")
        print_vpgs_validation(validated_vpgs)

    except ValidationError as error:
        print("\nVPGs validation failed")
        print("----------------------")
        for message in format_validation_errors(error):
            print(f"- {message}")

    try:
        validated_vm_replication = validate_vm_replication(vm_replication)
        print("\nVM Replication validation passed")
        print("--------------------------------")
        print_vm_replication_validation(validated_vm_replication)

    except ValidationError as error:
        print("\nVM Replication validation failed")
        print("--------------------------------")
        for message in format_validation_errors(error):
            print(f"- {message}")

    try:
        validated_vm_storage = validate_vm_storage(vm_storage)
        print("\nVM Storage validation passed")
        print("----------------------------")
        print_vm_storage_validation(validated_vm_storage)

    except ValidationError as error:
        print("\nVM Storage validation failed")
        print("----------------------------")
        for message in format_validation_errors(error):
            print(f"- {message}")

    try:
        validated_vm_nics = validate_vm_nics(vm_nics)
        print("\nVM NICs validation passed")
        print("-------------------------")
        print_vm_nics_validation(validated_vm_nics)

    except ValidationError as error:
        print("\nVM NICs validation failed")
        print("-------------------------")
        for message in format_validation_errors(error):
            print(f"- {message}")

    output_path = generate_zerto_json(excel_file)
    print(f"\nJSON output written to {output_path}")


def print_zerto_summary(summary: dict) -> None:
    print("\nZerto Data Summary")
    print("------------------")

    print("\nZVM Sites")
    for site in summary["zvm_sites"]:
        print(f"- Site Name: {site['site_name']}")
        print(f"  Protected: {site['protected']}")
        print(f"  Recovery: {site['recovery']}")

    print("\nLabels")
    print(f"- Scopes: {summary['labels']['scopes']}")
    print(f"- Waves: {summary['labels']['waves']}")
    print(f"- Application Names: {summary['labels']['application_names']}")
    print(f"- Application Environments: {summary['labels']['application_environments']}")
    print(f"- Data Types: {summary['labels']['data_types']}")

    print("\nRecovery Scripts")
    for script in summary["recovery_scripts"]:
        print(f"- {script}")

    print("\nBoot Order Groups")
    for group in summary["boot_order_groups"]:
        print(f"- Meta Group: {group['meta_group_name']}")
        print(f"  Group ID: {group['group_id']}")
        print(f"  Group Name: {group['group_name']}")
        print(f"  Boot Delay: {group['boot_delay_secs']} seconds")


def print_hypervisor_summary(hypervisor_data: dict) -> None:
    print("\nHypervisor Data Summary")
    print("-----------------------")

    print("\nProtected VMs")
    for vm in hypervisor_data["protected_vms"]:
        print(f"- Site: {vm.get('Protected ZVM Site Name')}")
        print(f"  VM Name: {vm.get('VM Name')}")
        print(f"  CPU Count: {vm.get('CPU Count')}")
        print(f"  Memory: {vm.get('Memory (GiB)')} GiB")

    print("\nProtected VM Volumes")
    for volume in hypervisor_data["protected_vm_volumes"]:
        print(f"- VM: {volume.get('Protected ZVM Site Name')} | {volume.get('VM Name')}")
        print(f"  Volume: {volume.get('Volume Location')}")
        print(f"  Size: {volume.get('Provisioned Size (GiB)')} GiB")

    print("\nProtected VM NICs")
    for nic in hypervisor_data["protected_vm_nics"]:
        print(f"- VM: {nic.get('Protected ZVM Site Name')} | {nic.get('VM Name')}")
        print(f"  NIC: {nic.get('NIC Name')}")
        print(f"  Network: {nic.get('Network')}")

    print("\nRecovery Hosts")
    for host in hypervisor_data["recovery_hosts"]:
        print(f"- Site: {host.get('Recovery ZVM Site Name')}")
        print(f"  Host: {host.get('Host Name')}")

    print("\nRecovery Datastores")
    for datastore in hypervisor_data["recovery_datastores"]:
        print(f"- Site: {datastore.get('Recovery ZVM Site Name')}")
        print(f"  Datastore: {datastore.get('Datastore Name')}")
        print(f"  Size: {datastore.get('Size (GiB)')} GiB")

    print("\nRecovery Folders")
    for folder in hypervisor_data["recovery_folders"]:
        print(f"- Site: {folder.get('Recovery ZVM Site Name')}")
        print(f"  Folder: {folder.get('Folder Name')}")

    print("\nRecovery Networks")
    for network in hypervisor_data["recovery_networks"]:
        print(f"- Site: {network.get('Recovery ZVM Site Name')}")
        print(f"  Network: {network.get('Network Name')}")


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
    main()
