import ipaddress
from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, ValidationInfo, field_validator

from validation.recovery_zvm_sites import (
    VnicIpConfigChange,
    YesNo,
    normalize_blank,
    validate_site_scoped_value,
)
from validation.vpgs import validate_config_value
import config
from validation.error_formatting import (
    WorkbookValidationError,
    format_workbook_error,
    validate_model_rows,
)

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
        validation_alias=AliasChoices(
            "Failover Live / Move - Network Name",
            "Failover / Move Network Name",
            "Failover Live / Move Network Name",
        ),
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
    def validate_vm_name(cls, value, info: ValidationInfo):
        if value is None:
            return value

        vpg_name = info.data.get("vpg_name")
        protected_site_name = config.vpg_protected_site_names_by_vpg_name.get(vpg_name)
        if protected_site_name is None:
            raise ValueError(
                f"VM Name '{value}' cannot be validated because VPG "
                f"'{vpg_name}' does not have a Protected ZVM Site Name."
            )

        allowed_values = config.protected_vm_names_by_site.get(
            protected_site_name,
            [],
        )

        if value not in allowed_values:
            raise ValueError(
                f"VM Name '{value}' is not valid for VPG '{vpg_name}' "
                f"with Protected ZVM Site Name '{protected_site_name}'. "
                f"Allowed values: {allowed_values}"
            )

        return value

    @field_validator("nic_name")
    @classmethod
    def validate_nic_name(cls, value, info: ValidationInfo):
        if value is None:
            return value

        vm_name = info.data.get("vm_name")
        vpg_name = info.data.get("vpg_name")
        protected_site_name = config.vpg_protected_site_names_by_vpg_name.get(vpg_name)
        if vm_name is None:
            raise ValueError(
                f"NIC Name '{value}' cannot be validated because VM Name is not valid."
            )

        allowed_values = config.protected_nic_names_by_site_and_vm_name.get(
            (protected_site_name, vm_name),
            [],
        )
        if value not in allowed_values:
            raise ValueError(
                f"NIC Name '{value}' is not valid for VPG '{vpg_name}', "
                f"Protected ZVM Site Name '{protected_site_name}', and VM "
                f"'{vm_name}'. Allowed values: {allowed_values}"
            )

        return value

    @field_validator("protected_network_name")
    @classmethod
    def validate_protected_network_name(cls, value, info: ValidationInfo):
        if value is None:
            return value

        vm_name = info.data.get("vm_name")
        nic_name = info.data.get("nic_name")
        vpg_name = info.data.get("vpg_name")
        protected_site_name = config.vpg_protected_site_names_by_vpg_name.get(vpg_name)
        if vm_name is None or nic_name is None:
            raise ValueError(
                f"Protected Network Name '{value}' cannot be validated because "
                "VM Name or NIC Name is not valid."
            )

        allowed_value = config.protected_network_names_by_site_vm_nic.get(
            (protected_site_name, vm_name, nic_name),
        )
        if value != allowed_value:
            raise ValueError(
                f"Protected Network Name '{value}' is not valid for VPG "
                f"'{vpg_name}', Protected ZVM Site Name '{protected_site_name}', "
                f"VM '{vm_name}', and NIC '{nic_name}'. "
                f"Allowed values: {[allowed_value] if allowed_value else []}"
            )

        return value

    @field_validator("failover_live_move_network_name", "failover_test_network_name")
    @classmethod
    def validate_recovery_network_name(cls, value, info: ValidationInfo):
        if value is None:
            return value

        vpg_name = info.data.get("vpg_name")
        recovery_site_name = config.vpg_recovery_site_names_by_vpg_name.get(vpg_name)

        return validate_site_scoped_value(
            value,
            recovery_site_name,
            config.recovery_network_names_by_site,
            "Recovery Network Name",
        )

    @field_validator(
        "failover_live_move_ip_address",
        "failover_live_move_default_gateway",
        "failover_live_move_preferred_dns_server",
        "failover_live_move_alternate_dns_server",
        "failover_test_ip_address",
        "failover_test_default_gateway",
        "failover_test_preferred_dns_server",
        "failover_test_alternate_dns_server",
    )
    @classmethod
    def validate_ipv4_address(cls, value, info: ValidationInfo):
        if value is None:
            return value

        if not is_valid_ipv4_address(value):
            raise ValueError(
                f"{info.field_name} '{value}' is not valid. "
                "Allowed values: a valid IPv4 address."
            )

        return value

    @field_validator("failover_live_move_subnet_mask", "failover_test_subnet_mask")
    @classmethod
    def validate_ipv4_subnet_mask(cls, value, info: ValidationInfo):
        if value is None:
            return value

        if not is_valid_ipv4_subnet_mask(value):
            raise ValueError(
                f"{info.field_name} '{value}' is not valid. "
                "Allowed values: a valid IPv4 subnet mask."
            )

        return value


def validate_vm_nic(data: dict) -> VMNIC:
    return VMNIC(**data)


def validate_vm_nics(data: list[dict]) -> list[VMNIC]:
    validated_rows = validate_model_rows(VMNIC, data)
    validate_unique_vm_nic_rows(data)
    return validated_rows


def is_valid_ipv4_address(value) -> bool:
    try:
        return isinstance(ipaddress.ip_address(str(value)), ipaddress.IPv4Address)
    except ValueError:
        return False


def is_valid_ipv4_subnet_mask(value) -> bool:
    text = str(value)
    if "." not in text:
        return False

    try:
        ipaddress.IPv4Network(f"0.0.0.0/{text}", strict=False)
    except ValueError:
        return False

    return True


def validate_unique_vm_nic_rows(data: list[dict]) -> None:
    seen_rows = {}
    messages = []

    for row in data:
        key = (
            row.get("VPG Name"),
            row.get("VM Name"),
            row.get("NIC Name"),
        )

        if any(value is None for value in key):
            continue

        if key in seen_rows:
            for duplicate_row in (seen_rows[key], row):
                messages.append(format_workbook_error(
                    duplicate_row,
                    "NIC Name",
                    row.get("NIC Name"),
                    "The combination of VPG Name, VM Name, and NIC Name must be unique.",
                ))
            continue

        seen_rows[key] = row

    if messages:
        raise WorkbookValidationError(messages)
