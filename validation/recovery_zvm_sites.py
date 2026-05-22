from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

import config


VPGType = Literal[
    "Remote DR and Continuous Backup",
    "Cyber Recovery",
    "Local Continuous Backup",
    "Data Mobility and Migration",
]

Priority = Literal["Low", "Medium", "High"]
JournalHistoryUnit = Literal["Days", "Hours"]
TargetRPOAlertUnit = Literal["Seconds", "Minutes", "Hours"]


def normalize_blank(value: Any) -> Any:
    if value is None:
        return None

    if isinstance(value, float) and value != value:
        return None

    if isinstance(value, str) and value.strip() == "":
        return None

    return value


class RecoveryZVMSite(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    recovery_zvm_site_name: str = Field(
        validation_alias="Recovery ZVM Site Name",
    )
    vpg_type: VPGType | None = Field(
        default=None,
        validation_alias="VPG Type",
    )
    priority: Priority | None = Field(
        default=None,
        validation_alias="Priority",
    )
    recovery_host_name: str | None = Field(
        default=None,
        validation_alias="Recovery Host Name",
    )
    recovery_datastore_name: str | None = Field(
        default=None,
        validation_alias="Recovery Datastore Name",
    )
    journal_history_value: int | None = Field(
        default=None,
        validation_alias="Journal History Value",
    )
    journal_history_unit: JournalHistoryUnit | None = Field(
        default=None,
        validation_alias="Journal History Unit",
    )
    target_rpo_alert_value: int | None = Field(
        default=None,
        validation_alias="Target RPO Alert Value",
    )
    target_rpo_alert_unit: TargetRPOAlertUnit | None = Field(
        default=None,
        validation_alias="Target RPO Alert Unit",
    )
    journal_datastore_name: str | None = Field(
        default=None,
        validation_alias="Journal Datastore Name",
    )

    @field_validator("*", mode="before")
    @classmethod
    def convert_blank_values_to_none(cls, value):
        return normalize_blank(value)

    @field_validator("recovery_zvm_site_name")
    @classmethod
    def validate_recovery_zvm_site_name(cls, value):
        if value not in config.recovery_site_names:
            raise ValueError(
                f"Recovery ZVM Site Name '{value}' is not valid. "
                f"Allowed values: {config.recovery_site_names}"
            )

        return value

    @field_validator("recovery_host_name")
    @classmethod
    def validate_recovery_host_name(cls, value):
        if value is None:
            return value

        if value not in config.recovery_host_names:
            raise ValueError(
                f"Recovery Host Name '{value}' is not valid. "
                f"Allowed values: {config.recovery_host_names}"
            )

        return value

    @field_validator("recovery_datastore_name", "journal_datastore_name")
    @classmethod
    def validate_recovery_datastore_name(cls, value):
        if value is None:
            return value

        if value not in config.recovery_datastore_names:
            raise ValueError(
                f"Recovery Datastore Name '{value}' is not valid. "
                f"Allowed values: {config.recovery_datastore_names}"
            )

        return value


def validate_recovery_zvm_site(data: dict) -> RecoveryZVMSite:
    return RecoveryZVMSite(**data)


def validate_recovery_zvm_sites(data: list[dict]) -> list[RecoveryZVMSite]:
    return [validate_recovery_zvm_site(row) for row in data]
