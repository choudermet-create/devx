import config
from extraction.tables import extract_sheet_table


def extract_vpgs(excel_file: str) -> list[dict]:
    vpgs = extract_sheet_table(excel_file, "VPGs", "VPG Name")
    load_vpgs_into_config(vpgs)
    return vpgs


def load_vpgs_into_config(vpgs: list[dict]) -> None:
    config.vpg_names = [
        vpg["VPG Name"]
        for vpg in vpgs
        if vpg.get("VPG Name")
    ]
