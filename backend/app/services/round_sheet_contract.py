"""Proposed Gate B validation only. No layout, approval or activation defaults."""

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app import models

from .round_evidence import fingerprint


class SheetWriteContract(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    scope: str
    tab_title: str = Field(min_length=1)
    season: int
    layout_version: str = Field(min_length=1)
    round_column: int = Field(ge=7, le=100)
    participant_column: int = Field(ge=7, le=100)
    operation_column: int = Field(ge=7, le=100)
    full_history_evidence: str = Field(min_length=1)
    whole_row_sorting_evidence: str = Field(min_length=1)
    protection_evidence: str = Field(min_length=1)

    @model_validator(mode="after")
    def exact_scope(self):
        workbook, tab, season = self.scope.rsplit(":", 2)
        if not workbook or not tab.isdigit() or season != str(self.season):
            raise ValueError("Exact workbook/tab/fixed season required")
        if len({self.round_column, self.participant_column, self.operation_column}) != 3:
            raise ValueError("Distinct identity columns required")
        return self


class SheetWriteApproval(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    enabled: bool = False
    contract_fingerprint: str
    reference: str = Field(min_length=1)
    actor_profile_id: int = Field(gt=0)
    approved_at: str
    allowed_operations: list[str]

    @model_validator(mode="after")
    def valid_approval(self):
        stamp = datetime.fromisoformat(self.approved_at)
        if (
            not stamp.tzinfo
            or stamp > datetime.now(UTC)
            or not self.allowed_operations
            or not set(self.allowed_operations) <= {"insert", "update"}
        ):
            raise ValueError("Explicit timestamp and allowed operations required")
        return self


def approved_contract(db, scope, operation=None):
    """Invalid/missing approval is absence, never implicit fixture permission."""
    row = db.get(models.AppConfig, "round_sheet_contracts")
    try:
        entry = (row.value if row else {})[scope]
        contract = SheetWriteContract.model_validate(entry["contract"])
        approval = SheetWriteApproval.model_validate(entry["approval"])
        if (
            contract.scope != scope
            or not approval.enabled
            or approval.contract_fingerprint != fingerprint(contract.model_dump())
            or (operation is not None and operation not in approval.allowed_operations)
        ):
            return None
        return contract
    except (KeyError, ValueError, TypeError):
        return None


def column_name(index):
    result = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        result = chr(65 + remainder) + result
    return result
