from typing import Literal
from pydantic import BaseModel, field_validator, model_validator
import config


class JournalHistoryValueUnit(BaseModel):
    value: int
    unit: Literal["Hours", "Days"]


class TargetRPOAlertValueUnit(BaseModel):
    value: int
    unit: Literal["Seconds", "Minutes", "Hours"]


class JournalSizeValueUnit(BaseModel):
    value: float
    unit: Literal["MiB", "GiB", "TiB"]


class DefaultVPGSettings(BaseModel):
    protected_site: str
    recovery_site: str

    vpg_type: Literal[
        "Remote DR and Continuous Backup",
        "Cyber Recovery",
        "Local Continuous Backup",
        "Data Mobility and Migration",
    ]

    priority: Literal["Low", "Medium", "High"]

    journal_history: JournalHistoryValueUnit
    target_rpo_alert: TargetRPOAlertValueUnit

    test_reminder: str

    journal_size_hard_limit: JournalSizeValueUnit
    journal_size_warning: JournalSizeValueUnit
    scratch_journal_size_hard_limit: JournalSizeValueUnit
    scratch_journal_size_warning: JournalSizeValueUnit

    wan_compression: Literal["Yes", "No"]

    @field_validator("protected_site")
    @classmethod
    def validate_protected_site(cls, value):
        if value not in config.protected_site_names:
            raise ValueError(
                f"Protected site '{value}' is not valid. "
                f"Allowed values: {config.protected_site_names}"
            )
        return value

    @field_validator("recovery_site")
    @classmethod
    def validate_recovery_site(cls, value):
        if value not in config.recovery_site_names:
            raise ValueError(
                f"Recovery site '{value}' is not valid. "
                f"Allowed values: {config.recovery_site_names}"
            )
        return value

    @model_validator(mode="after")
    def validate_journal_sizes(self):
        if self.journal_size_warning.value > self.journal_size_hard_limit.value:
            raise ValueError(
                "Journal Size Warning Threshold cannot be greater than "
                "Journal Size Hard Limit Value"
            )

        if self.scratch_journal_size_warning.value > self.scratch_journal_size_hard_limit.value:
            raise ValueError(
                "Scratch Journal Size Warning Threshold cannot be greater than "
                "Scratch Journal Size Hard Limit Value"
            )

        return self


def validate_default_vpg_settings(data: dict) -> DefaultVPGSettings:
    return DefaultVPGSettings(**data)