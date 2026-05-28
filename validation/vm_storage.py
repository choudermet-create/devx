from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

import config
from validation.recovery_zvm_sites import DiskProvisioningOverride, normalize_blank
from validation.vpgs import validate_config_value


VolumeSyncType = Literal[
    "Continuous Sync",
    "Initial Sync Only",
    "No Sync (Empty Disk)",
]


class VMStorage(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    vpg_name: str | None = Field(
        default=None,
        validation_alias="VPG Name",
    )
    vm_name: str | None = Field(
        default=None,
        validation_alias="VM Name",
    )
    protected_volume_location: str | None = Field(
        default=None,
        validation_alias="Protected Volume Location",
    )
    size_gib: Any | None = Field(
        default=None,
        validation_alias="Size (GiB)",
    )
    recovery_volume_location: Any | None = Field(
        default=None,
        validation_alias="Recovery Volume Location",
    )
    recovery_raw_device_name: Any | None = Field(
        default=None,
        validation_alias="Recovery Raw Device Name",
    )
    disk_provisioning_override: DiskProvisioningOverride | None = Field(
        default=None,
        validation_alias="Disk Provisioning Override",
    )
    volume_sync_type: VolumeSyncType | None = Field(
        default=None,
        validation_alias="Volume Sync Type",
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

    @field_validator("protected_volume_location")
    @classmethod
    def validate_protected_volume_location(cls, value, info: ValidationInfo):
        if value is None:
            return value

        vm_name = info.data.get("vm_name")
        if vm_name is None:
            raise ValueError(
                f"Protected Volume Location '{value}' cannot be validated "
                "because VM Name is not valid."
            )

        allowed_values = config.protected_volume_locations_by_vm_name.get(
            vm_name,
            [],
        )

        if value not in allowed_values:
            raise ValueError(
                f"Protected Volume Location '{value}' is not valid for VM "
                f"'{vm_name}'. Allowed values: {allowed_values}"
            )

        return value


def validate_vm_storage_row(data: dict) -> VMStorage:
    return VMStorage(**data)


def validate_vm_storage(data: list[dict]) -> list[VMStorage]:
    return [validate_vm_storage_row(row) for row in data]
