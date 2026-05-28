from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

import config
from validation.recovery_zvm_sites import JournalSizeUnit, normalize_blank
from validation.vpgs import validate_config_value


class VMReplication(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    vpg_name: str | None = Field(
        default=None,
        validation_alias="VPG Name",
    )
    vm_name: str | None = Field(
        default=None,
        validation_alias="VM Name",
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
    boot_order_group_name: str | None = Field(
        default=None,
        validation_alias="Boot Order Group Name",
    )
    recovery_host_name: str | None = Field(
        default=None,
        validation_alias="Recovery Host Name",
    )
    recovery_datastore_name: str | None = Field(
        default=None,
        validation_alias="Recovery Datastore Name",
    )
    recovery_folder_name: Any | None = Field(
        default=None,
        validation_alias="Recovery Folder Name",
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

    @field_validator("*", mode="before")
    @classmethod
    def convert_blank_values_to_none(cls, value):
        return normalize_blank(value)

    @field_validator("vpg_name")
    @classmethod
    def validate_vpg_name(cls, value):
        return validate_config_value(value, config.vpg_names, "VPG Name")

    @field_validator("vm_name")
    @classmethod
    def validate_vm_name(cls, value):
        return validate_config_value(value, config.protected_vm_names, "VM Name")

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

    @field_validator("boot_order_group_name")
    @classmethod
    def validate_boot_order_group_name(cls, value):
        return validate_config_value(
            value,
            config.boot_order_groups,
            "Boot Order Group Name",
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


def validate_vm_replication_row(data: dict) -> VMReplication:
    return VMReplication(**data)


def validate_vm_replication(data: list[dict]) -> list[VMReplication]:
    return [validate_vm_replication_row(row) for row in data]
