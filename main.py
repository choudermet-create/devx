from pydantic import ValidationError

from ingestion.reader import load_excel_workbook, validate_required_sheets
from extraction.zerto_data import extract_zerto_data
from extraction.hypervisor import extract_hypervisor_data
from extraction.vpg_settings import extract_default_vpg_settings
from extraction.recovery_zvm_sites import extract_recovery_zvm_sites
from validation.default_vpg_settings import validate_default_vpg_settings
from validation.recovery_zvm_sites import validate_recovery_zvm_sites
from generate_zerto_json import generate_zerto_json


def main():
    excel_file = "files/basic2.xlsx"

    workbook = load_excel_workbook(excel_file)
    validate_required_sheets(workbook)

    print("Workbook loaded successfully")

    zerto_data = extract_zerto_data(excel_file)
    hypervisor_data = extract_hypervisor_data(excel_file)
    vpg_settings = extract_default_vpg_settings(excel_file)
    recovery_zvm_sites = extract_recovery_zvm_sites(excel_file)

    print_zerto_summary(zerto_data["summary"])
    print_hypervisor_summary(hypervisor_data)

    try:
        validated_vpg_settings = validate_default_vpg_settings(vpg_settings)
        print("\nDefault VPG Settings validation passed")
        print("--------------------------------------")
        print(validated_vpg_settings)

    except ValidationError as error:
        print("\nDefault VPG Settings validation failed")
        print("--------------------------------------")
        print(error)

    try:
        validated_recovery_zvm_sites = validate_recovery_zvm_sites(recovery_zvm_sites)
        print("\nRecovery ZVM Sites validation passed")
        print("------------------------------------")
        for site in validated_recovery_zvm_sites:
            print(site)

    except ValidationError as error:
        print("\nRecovery ZVM Sites validation failed")
        print("------------------------------------")
        print(error)

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


if __name__ == "__main__":
    main()
