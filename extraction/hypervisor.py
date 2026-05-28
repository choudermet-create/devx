import pandas as pd
import config
from extraction.tables import clean_records


def extract_hypervisor_data(excel_file: str) -> dict:
    raw_df = pd.read_excel(
        excel_file,
        sheet_name="Hypervisor Data",
        engine="openpyxl",
        header=None,
    )

    header_row_index = find_header_row(raw_df, "Protected ZVM Site Name")

    tables = {
        "protected_vms": extract_table(raw_df, header_row_index, 0, 5),
        "protected_vm_volumes": extract_table(raw_df, header_row_index, 7, 13),
        "protected_vm_nics": extract_table(raw_df, header_row_index, 15, 21),
        "recovery_hosts": extract_table(raw_df, header_row_index, 23, 28),
        "recovery_datastores": extract_table(raw_df, header_row_index, 30, 34),
        "recovery_folders": extract_table(raw_df, header_row_index, 36, 39),
        "recovery_networks": extract_table(raw_df, header_row_index, 41, 44),
    }

    load_hypervisor_data_into_config(tables)

    return tables


def find_header_row(df: pd.DataFrame, required_text: str) -> int:
    for index, row in df.iterrows():
        values = [str(value).strip() for value in row.tolist() if pd.notna(value)]

        if required_text in values:
            return index

    raise ValueError(f"Could not find header row containing '{required_text}'")


def extract_table(
    raw_df: pd.DataFrame,
    header_row_index: int,
    start_col: int,
    end_col: int,
) -> list[dict]:
    table_df = raw_df.iloc[header_row_index:, start_col:end_col + 1].copy()

    table_df.columns = table_df.iloc[0]
    table_df = table_df.iloc[1:]

    table_df = table_df.dropna(how="all")
    table_df = table_df.where(pd.notnull(table_df), None)

    return clean_records(table_df.to_dict(orient="records"))


def load_hypervisor_data_into_config(tables: dict) -> None:
    config.protected_vms = tables["protected_vms"]
    config.protected_vm_volumes = tables["protected_vm_volumes"]
    config.protected_vm_nics = tables["protected_vm_nics"]

    config.recovery_hosts = tables["recovery_hosts"]
    config.recovery_datastores = tables["recovery_datastores"]
    config.recovery_folders = tables["recovery_folders"]
    config.recovery_networks = tables["recovery_networks"]

    config.protected_vm_names = [
        vm["VM Name"]
        for vm in config.protected_vms
        if vm.get("VM Name")
    ]

    config.protected_volume_locations_by_vm_name = {}
    for volume in config.protected_vm_volumes:
        vm_name = volume.get("VM Name")
        volume_location = volume.get("Volume Location")

        if vm_name and volume_location:
            config.protected_volume_locations_by_vm_name.setdefault(
                vm_name,
                [],
            ).append(volume_location)

    config.protected_nic_names_by_vm_name = {}
    config.protected_network_names_by_vm_nic = {}
    for nic in config.protected_vm_nics:
        vm_name = nic.get("VM Name")
        nic_name = nic.get("NIC Name")
        network_name = nic.get("Network")

        if vm_name and nic_name:
            config.protected_nic_names_by_vm_name.setdefault(
                vm_name,
                [],
            ).append(nic_name)

        if vm_name and nic_name and network_name:
            config.protected_network_names_by_vm_nic[(vm_name, nic_name)] = network_name

    config.recovery_host_names = [
        host["Host Name"]
        for host in config.recovery_hosts
        if host.get("Host Name")
    ]

    config.recovery_datastore_names = [
        datastore["Datastore Name"]
        for datastore in config.recovery_datastores
        if datastore.get("Datastore Name")
    ]

    config.recovery_folder_names = [
        folder["Folder Name"]
        for folder in config.recovery_folders
        if folder.get("Folder Name")
    ]

    config.recovery_network_names = [
        network["Network Name"]
        for network in config.recovery_networks
        if network.get("Network Name")
    ]
