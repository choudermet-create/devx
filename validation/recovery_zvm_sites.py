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
TestReminder = Literal["3 Months", "6 Months", "9 Months", "12 Months"]
JournalSizeUnit = Literal["TiB", "GiB", "%"]
YesNo = Literal["Yes", "No"]
DiskProvisioningOverride = Literal["As-is", "Thin", "Thick"]
VnicIpConfigChange = Literal["No", "Yes, DHCP", "Yes, Static"]


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
    test_reminder: TestReminder | None = Field(
        default=None,
        validation_alias="Test Reminder",
    )
    journal_datastore_name: str | None = Field(
        default=None,
        validation_alias="Journal Datastore Name",
    )
    journal_size_hard_limit_value: Any | None = Field(
        default=None,
        validation_alias="Journal Size Hard Limit Value",
    )
    journal_size_hard_limit_unit: JournalSizeUnit | None = Field(
        default=None,
        validation_alias="Journal Size Hard Limit Unit",
    )
    journal_size_warning_threshold_value: Any | None = Field(
        default=None,
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
    scratch_journal_size_hard_limit_value: Any | None = Field(
        default=None,
        validation_alias="Scratch Journal Size Hard Limit Value",
    )
    scratch_journal_size_hard_limit_unit: JournalSizeUnit | None = Field(
        default=None,
        validation_alias="Scratch Journal Size Hard Limit Unit",
    )
    scratch_journal_size_warning_threshold_value: Any | None = Field(
        default=None,
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
        validation_alias="Failover Live / Move Network Name",
    )
    failover_test_network_name: str | None = Field(
        default=None,
        validation_alias="Failover Test Network Name",
    )
    recovery_folder_name: str | None = Field(
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
    failover_live_move_create_new_mac_address: YesNo | None = Field(
        default=None,
        validation_alias="Failover Live / Move - Create new MAC address",
    )
    failover_live_move_change_vnic_ip_config: VnicIpConfigChange | None = Field(
        default=None,
        validation_alias="Failover Live / Move - Change vNIC IP Config",
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
    failover_test_create_new_mac_address: YesNo | None = Field(
        default=None,
        validation_alias="Failover Test - Create new MAC address",
    )
    failover_test_change_vnic_ip_config: Any | None = Field(
        default=None,
        validation_alias="Failover Test - Change vNIC IP Config",
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

    @field_validator(
        "recovery_datastore_name",
        "journal_datastore_name",
        "scratch_journal_datastore_name",
    )
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

    @field_validator("failover_live_move_network_name", "failover_test_network_name")
    @classmethod
    def validate_recovery_network_name(cls, value):
        if value is None:
            return value

        if value not in config.recovery_network_names:
            raise ValueError(
                f"Recovery Network Name '{value}' is not valid. "
                f"Allowed values: {config.recovery_network_names}"
            )

        return value


def validate_recovery_zvm_site(data: dict) -> RecoveryZVMSite:
    return RecoveryZVMSite(**data)


def validate_recovery_zvm_sites(data: list[dict]) -> list[RecoveryZVMSite]:
    return [validate_recovery_zvm_site(row) for row in data]
