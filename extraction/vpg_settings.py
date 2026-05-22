import pandas as pd


def extract_default_vpg_settings(excel_file: str, print_output: bool = True) -> dict:
    df = pd.read_excel(
        excel_file,
        sheet_name="Default VPG Settings",
        engine="openpyxl",
        header=None,
    )

    data = {}

    # Default Sites
    for i, row in df.iterrows():
        if row[0] == "Protected Site":
            data["protected_site"] = row[1]

        if row[0] == "Recovery Site":
            data["recovery_site"] = row[1]

    # Default VPG Settings block
    for i, row in df.iterrows():
        key = row[0]
        value = row[1]
        unit = row[2] if len(row) > 2 else None

        if key == "VPG Type":
            data["vpg_type"] = value

        elif key == "Priority":
            data["priority"] = value

        elif key == "Journal History":
            data["journal_history"] = {
                "value": value,
                "unit": unit,
            }

        elif key == "Target RPO Alert":
            data["target_rpo_alert"] = {
                "value": value,
                "unit": unit,
            }

        elif key == "Test Reminder":
            data["test_reminder"] = value

        elif key == "Journal Size Hard Limit Value":
            data["journal_size_hard_limit"] = {
                "value": value,
                "unit": unit,
            }

        elif key == "Journal Size Warning Threshold":
            data["journal_size_warning"] = {
                "value": value,
                "unit": unit,
            }

        elif key == "Scratch Journal Size Hard Limit Value":
            data["scratch_journal_size_hard_limit"] = {
                "value": value,
                "unit": unit,
            }

        elif key == "Scratch Journal Size Warning Threshold":
            data["scratch_journal_size_warning"] = {
                "value": value,
                "unit": unit,
            }

        elif key == "Enable WAN Traffic Compression?":
            data["wan_compression"] = value

    if print_output:
        print("\nDefault VPG Settings (Structured)")
        print("---------------------------------")
        for k, v in data.items():
            print(f"{k}: {v}")

    return data
