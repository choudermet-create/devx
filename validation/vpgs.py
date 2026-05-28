from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

import config
from validation.recovery_zvm_sites import (
    DiskProvisioningOverride,
    JournalHistoryUnit,
    JournalSizeUnit,
    Priority,
    TargetRPOAlertUnit,
    VPGType,
    YesNo,
    normalize_blank,
)


TestReminder = Literal[
    "None",
    "1 Month",
    "3 Months",
    "6 Months",
    "9 Months",
    "12 Months",
]


class VPG(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    vpg_name: Any | None = Field(
        default=None,
        validation_alias="VPG Name",
    )
    protected_zvm_site_name: str | None = Field(
        default=None,
        validation_alias="Protected ZVM Site Name",
    )
    recovery_zvm_site_name: str | None = Field(
        default=None,
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
    vpg_description: Any | None = Field(
        default=None,
        validation_alias="VPG Description",
    )
    label_1: str | None = Field(
        default=None,
        validation_alias="Label 1",
    )
    label_2: str | None = Field(
        default=None,
        validation_alias="Label 2",
    )
    label_3: str | None = Field(
        default=None,
        validation_alias="Label 3",
    )
    label_4: str | None = Field(
        default=None,
        validation_alias="Label 4",
    )
    label_5: str | None = Field(
        default=None,
        validation_alias="Label 5",
    )
    boot_order_meta_group_name: str | None = Field(
        default=None,
        validation_alias="Boot Order Meta Group Name",
    )
    recovery_host_name: str | None = Field(
        default=None,
        validation_alias="Recovery Host Name",
    )
    recovery_datastore_name: str | None = Field(
        default=None,
        validation_alias="Recovery Datastore Name",
    )
    journal_history_unit: JournalHistoryUnit | None = Field(
        default=None,
        validation_alias="Journal History Unit",
    )
    journal_history_value: int | None = Field(
        default=None,
        validation_alias="Journal History Value",
    )
    target_rpo_alert_value: Any | None = Field(
        default=None,
        validation_alias="Target RPO Alert Value",
    )
    target_rpo_alert_unit: TargetRPOAlertUnit | None = Field(
        default=None,
        validation_alias="Target RPO Alert Unit",
    )
    test_reminder: TestReminder | None = Field(
        default=None,
        validation_alias="Test Reminder",
    )
    journal_datastore_name: str | None = Field(
        default=None,
        validation_alias="Journal Datastore Name",
    )
    journal_size_hard_limit_value: int | None = Field(
        default=None,
        ge=10,
        le=99999,
        validation_alias="Journal Size Hard Limit Value",
    )
    journal_size_hard_limit_unit: JournalSizeUnit | None = Field(
        default=None,
        validation_alias="Journal Size Hard Limit Unit",
    )
    journal_size_warning_threshold_value: int | None = Field(
        default=None,
        ge=10,
        le=99999,
        validation_alias="Journal Size Warning Threshold Value",
    )
    journal_size_warning_threshold_unit: JournalSizeUnit | None = Field(
        default=None,
        validation_alias="Journal Size Warning Threshold Unit",
    )
    scratch_journal_datastore_name: str | None = Field(
        default=None,
        validation_alias="Scratch Journal Datastore Name",
    )
    scratch_journal_size_hard_limit_value: int | None = Field(
        default=None,
        ge=10,
        le=99999,
        validation_alias="Scratch Journal Size Hard Limit Value",
    )
    scratch_journal_size_hard_limit_unit: JournalSizeUnit | None = Field(
        default=None,
        validation_alias="Scratch Journal Size Hard Limit Unit",
    )
    scratch_journal_size_warning_threshold_value: int | None = Field(
        default=None,
        ge=10,
        le=99999,
        validation_alias="Scratch Journal Size Warning Threshold Value",
    )
    scratch_journal_size_warning_threshold_unit: JournalSizeUnit | None = Field(
        default=None,
        validation_alias="Scratch Journal Size Warning Threshold Unit",
    )
    enable_wan_traffic_compression: YesNo | None = Field(
        default=None,
        validation_alias="Enable WAN Traffic Compression",
    )
    disk_provisioning_override: DiskProvisioningOverride | None = Field(
        default=None,
        validation_alias="Disk Provisioning Override",
    )
    failover_live_move_network_name: str | None = Field(
        default=None,
        validation_alias="Failover Live / Move - Network Name",
    )
    failover_test_network_name: str | None = Field(
        default=None,
        validation_alias="Failover Test Network Name",
    )
    recovery_folder_name: Any | None = Field(
        default=None,
        validation_alias="Recovery Folder Name",
    )
    pre_recovery_script_name: Any | None = Field(
        default=None,
        validation_alias="Pre-Recovery Script Name",
    )
    pre_recovery_script_parameters: Any | None = Field(
        default=None,
        validation_alias="Pre-Recovery Script Parameters",
    )
    pre_recovery_script_execution_timeout_seconds: Any | None = Field(
        default=None,
        validation_alias="Pre-Recovery Script Execution Timeout (Seconds)",
    )
    post_recovery_script_name: Any | None = Field(
        default=None,
        validation_alias="Post-Recovery Script Name",
    )
    post_recovery_script_parameters: Any | None = Field(
        default=None,
        validation_alias="Post-Recovery Script Parameters",
    )
    post_recovery_script_execution_timeout_seconds: Any | None = Field(
        default=None,
        validation_alias="Post-Recovery Script Execution Timeout (Seconds)",
    )

    @field_validator("*", mode="before")
    @classmethod
    def convert_blank_values_to_none(cls, value):
        return normalize_blank(value)

    @field_validator("protected_zvm_site_name")
    @classmethod
    def validate_protected_zvm_site_name(cls, value):
        if value is None:
            return value

        if value not in config.protected_site_names:
            raise ValueError(
                f"Protected ZVM Site Name '{value}' is not valid. "
                f"Allowed values: {config.protected_site_names}"
            )

        return value

    @field_validator("recovery_zvm_site_name")
    @classmethod
    def validate_recovery_zvm_site_name(cls, value):
        if value is None:
            return value

        if value not in config.recovery_site_names:
            raise ValueError(
                f"Recovery ZVM Site Name '{value}' is not valid. "
                f"Allowed values: {config.recovery_site_names}"
            )

        return value

    @field_validator("label_1")
    @classmethod
    def validate_label_1(cls, value):
        return validate_config_value(value, config.scopes, "Label 1")

    @field_validator("label_2")
    @classmethod
    def validate_label_2(cls, value):
        return validate_config_value(value, config.waves, "Label 2")

    @field_validator("label_3")
    @classmethod
    def validate_label_3(cls, value):
        return validate_config_value(value, config.application_names, "Label 3")

    @field_validator("label_4")
    @classmethod
    def validate_label_4(cls, value):
        return validate_config_value(value, config.application_environments, "Label 4")

    @field_validator("label_5")
    @classmethod
    def validate_label_5(cls, value):
        return validate_config_value(value, config.data_types, "Label 5")

    @field_validator("boot_order_meta_group_name")
    @classmethod
    def validate_boot_order_meta_group_name(cls, value):
        return validate_config_value(
            value,
            config.boot_order_meta_groups,
            "Boot Order Meta Group Name",
        )

    @field_validator("recovery_host_name")
    @classmethod
    def validate_recovery_host_name(cls, value):
        return validate_config_value(
            value,
            config.recovery_host_names,
            "Recovery Host Name",
        )

    @field_validator(
        "recovery_datastore_name",
        "journal_datastore_name",
        "scratch_journal_datastore_name",
    )
    @classmethod
    def validate_recovery_datastore_name(cls, value):
        return validate_config_value(
            value,
            config.recovery_datastore_names,
            "Recovery Datastore Name",
        )

    @field_validator("failover_live_move_network_name", "failover_test_network_name")
    @classmethod
    def validate_recovery_network_name(cls, value):
        return validate_config_value(
            value,
            config.recovery_network_names,
            "Recovery Network Name",
        )

    @field_validator("journal_history_value")
    @classmethod
    def validate_journal_history_value_range(cls, value, info: ValidationInfo):
        journal_history_unit = info.data.get("journal_history_unit")
        if value is None or journal_history_unit is None:
            return value

        if journal_history_unit == "Days":
            validate_range(
                value,
                1,
                30,
                "Journal History Value",
                "when Journal History Unit is Days",
            )

        if journal_history_unit == "Hours":
            validate_range(
                value,
                1,
                720,
                "Journal History Value",
                "when Journal History Unit is Hours",
            )

        return value


def validate_config_value(value, allowed_values: list, field_name: str):
    if value is None:
        return value

    if value not in allowed_values:
        raise ValueError(
            f"{field_name} '{value}' is not valid. "
            f"Allowed values: {allowed_values}"
        )

    return value


def validate_range(value: int, minimum: int, maximum: int, field_name: str, context: str):
    if minimum <= value <= maximum:
        return

    raise ValueError(
        f"{field_name} '{value}' is not valid {context}. "
        f"Allowed values: {minimum}-{maximum}"
    )


def validate_vpg(data: dict) -> VPG:
    return VPG(**data)


def validate_vpgs(data: list[dict]) -> list[VPG]:
    return [validate_vpg(row) for row in data]
