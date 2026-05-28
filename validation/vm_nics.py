from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

import config
from validation.recovery_zvm_sites import VnicIpConfigChange, YesNo, normalize_blank
from validation.vpgs import validate_config_value


class VMNIC(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    vpg_name: str | None = Field(
        default=None,
        validation_alias="VPG Name",
    )
    vm_name: str | None = Field(
        default=None,
        validation_alias="VM Name",
    )
    nic_name: str | None = Field(
        default=None,
        validation_alias="NIC Name",
    )
    protected_network_name: str | None = Field(
        default=None,
        validation_alias="Protected Network Name",
    )
    failover_live_move_network_name: str | None = Field(
        default=None,
        validation_alias="Failover Live / Move - Network Name",
    )
    failover_live_move_create_new_mac_address: YesNo | None = Field(
        default=None,
        validation_alias="Failover Live / Move - Create new MAC address",
    )
    failover_live_move_change_vnic_ip_config: VnicIpConfigChange | None = Field(
        default=None,
        validation_alias="Failover Live / Move - Change vNIC IP Config",
    )
    failover_live_move_ip_address: Any | None = Field(
        default=None,
        validation_alias="Failover Live / Move - IP Address",
    )
    failover_live_move_subnet_mask: Any | None = Field(
        default=None,
        validation_alias="Failover Live / Move - Subnet Mask",
    )
    failover_live_move_default_gateway: Any | None = Field(
        default=None,
        validation_alias="Failover Live / Move - Default Gateway",
    )
    failover_live_move_preferred_dns_server: Any | None = Field(
        default=None,
        validation_alias="Failover Live / Move - Preferred DNS Server",
    )
    failover_live_move_alternate_dns_server: Any | None = Field(
        default=None,
        validation_alias="Failover Live / Move - Alternate DNS Server",
    )
    failover_live_move_dns_suffix: Any | None = Field(
        default=None,
        validation_alias="Failover Live / Move - DNS Suffix",
    )
    failover_test_network_name: str | None = Field(
        default=None,
        validation_alias="Failover Test - Network Name",
    )
    failover_test_create_new_mac_address: YesNo | None = Field(
        default=None,
        validation_alias="Failover Test - Create new MAC address",
    )
    failover_test_change_vnic_ip_config: VnicIpConfigChange | None = Field(
        default=None,
        validation_alias="Failover Test - Change vNIC IP Config",
    )
    failover_test_ip_address: Any | None = Field(
        default=None,
        validation_alias="Failover Test - IP Address",
    )
    failover_test_subnet_mask: Any | None = Field(
        default=None,
        validation_alias="Failover Test - Subnet Mask",
    )
    failover_test_default_gateway: Any | None = Field(
        default=None,
        validation_alias="Failover Test - Default Gateway",
    )
    failover_test_preferred_dns_server: Any | None = Field(
        default=None,
        validation_alias="Failover Test - Preferred DNS Server",
    )
    failover_test_alternate_dns_server: Any | None = Field(
        default=None,
        validation_alias="Failover Test - Alternate DNS Server",
    )
    failover_test_dns_suffix: Any | None = Field(
        default=None,
        validation_alias="Failover Test - DNS Suffix",
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

    @field_validator("nic_name")
    @classmethod
    def validate_nic_name(cls, value, info: ValidationInfo):
        if value is None:
            return value

        vm_name = info.data.get("vm_name")
        if vm_name is None:
            raise ValueError(
                f"NIC Name '{value}' cannot be validated because VM Name is not valid."
            )

        allowed_values = config.protected_nic_names_by_vm_name.get(vm_name, [])
        if value not in allowed_values:
            raise ValueError(
                f"NIC Name '{value}' is not valid for VM '{vm_name}'. "
                f"Allowed values: {allowed_values}"
            )

        return value

    @field_validator("protected_network_name")
    @classmethod
    def validate_protected_network_name(cls, value, info: ValidationInfo):
        if value is None:
            return value

        vm_name = info.data.get("vm_name")
        nic_name = info.data.get("nic_name")
        if vm_name is None or nic_name is None:
            raise ValueError(
                f"Protected Network Name '{value}' cannot be validated because "
                "VM Name or NIC Name is not valid."
            )

        allowed_value = config.protected_network_names_by_vm_nic.get((vm_name, nic_name))
        if value != allowed_value:
            raise ValueError(
                f"Protected Network Name '{value}' is not valid for VM '{vm_name}' "
                f"and NIC '{nic_name}'. Allowed values: {[allowed_value] if allowed_value else []}"
            )

        return value

    @field_validator("failover_live_move_network_name", "failover_test_network_name")
    @classmethod
    def validate_recovery_network_name(cls, value):
        return validate_config_value(
            value,
            config.recovery_network_names,
            "Recovery Network Name",
        )


def validate_vm_nic(data: dict) -> VMNIC:
    return VMNIC(**data)


def validate_vm_nics(data: list[dict]) -> list[VMNIC]:
    return [validate_vm_nic(row) for row in data]
