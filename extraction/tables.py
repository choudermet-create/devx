from datetime import date, datetime, time
from typing import Any

import pandas as pd


def extract_sheet_table(
    excel_file: str,
    sheet_name: str,
    required_header: str,
) -> list[dict]:
    raw_df = pd.read_excel(
        excel_file,
        sheet_name=sheet_name,
        engine="openpyxl",
        header=None,
    )

    header_row_index = find_header_row(raw_df, required_header)

    df = pd.read_excel(
        excel_file,
        sheet_name=sheet_name,
        engine="openpyxl",
        header=header_row_index,
    )

    df = df.dropna(how="all")
    df = df.dropna(axis=1, how="all")

    records = df.to_dict(orient="records")
    return clean_records(records)


def find_header_row(df: pd.DataFrame, required_text: str) -> int:
    for index, row in df.iterrows():
        values = [
            str(value).strip()
            for value in row.tolist()
            if pd.notna(value)
        ]

        if required_text in values:
            return index

    raise ValueError(f"Could not find header row containing '{required_text}'")


def clean_records(records: list[dict]) -> list[dict]:
    cleaned_records = []

    for record in records:
        cleaned_record = {
            str(key).strip(): clean_value(value)
            for key, value in record.items()
            if key is not None and str(key).strip() != "nan"
        }

        if any(value is not None for value in cleaned_record.values()):
            cleaned_records.append(cleaned_record)

    return cleaned_records


def clean_value(value: Any) -> Any:
    if value is None:
        return None

    if isinstance(value, float) and pd.isna(value):
        return None

    if pd.isna(value) if not isinstance(value, (list, dict)) else False:
        return None

    if isinstance(value, str):
        value = value.strip()
        return value or None

    if isinstance(value, (datetime, date, time)):
        return value.isoformat()

    return value
