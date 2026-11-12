"""Schema contracts and structural assertion framework for PPMI datasets."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

import pandas as pd


@dataclass
class SchemaContract:
    """Contract specifying structural invariants for a dataset table."""
    table_identifier: str
    required_columns: List[str]
    participant_col: Optional[str] = "PATNO"
    visit_col: Optional[str] = "EVENT_ID"
    allow_null_participant: bool = False
    max_allowed_null_rate: float = 0.95
    allowed_visit_codes: Optional[Set[str]] = None


@dataclass
class ContractValidationResult:
    """Outcome of contract validation."""
    passed: bool
    missing_columns: List[str] = field(default_factory=list)
    null_participant_count: int = 0
    invalid_visit_codes: List[str] = field(default_factory=list)
    excessive_null_columns: Dict[str, float] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


class ContractEnforcer:
    """Enforces structural contracts on loaded datasets."""

    @classmethod
    def validate(cls, df: pd.DataFrame, contract: SchemaContract) -> ContractValidationResult:
        """Validate dataframe against contract invariants."""
        errors: List[str] = []
        cols_upper = {c.strip().upper(): c for c in df.columns}

        # 1. Required columns check
        missing_cols: List[str] = []
        for req in contract.required_columns:
            if req.upper() not in cols_upper:
                missing_cols.append(req)
        if missing_cols:
            errors.append(f"Missing required columns: {missing_cols}")

        # 2. Participant key non-null check
        null_pat = 0
        if contract.participant_col and contract.participant_col.upper() in cols_upper:
            actual_col = cols_upper[contract.participant_col.upper()]
            null_pat = int(df[actual_col].isna().sum())
            if null_pat > 0 and not contract.allow_null_participant:
                errors.append(f"Found {null_pat} null participant IDs in '{actual_col}'")

        # 3. Visit code validity check
        invalid_visits: List[str] = []
        if contract.visit_col and contract.allowed_visit_codes and contract.visit_col.upper() in cols_upper:
            actual_vis = cols_upper[contract.visit_col.upper()]
            vis_values = df[actual_vis].dropna().unique()
            for v in vis_values:
                val_str = str(v).strip()
                if val_str not in contract.allowed_visit_codes:
                    invalid_visits.append(val_str)
            if invalid_visits:
                errors.append(f"Found unlisted visit codes: {invalid_visits[:5]} (total {len(invalid_visits)})")

        # 4. Excessive null columns check
        excessive_nulls: Dict[str, float] = {}
        total_rows = max(len(df), 1)
        for col in df.columns:
            null_rate = df[col].isna().sum() / total_rows
            if null_rate > contract.max_allowed_null_rate:
                excessive_nulls[col] = float(null_rate)

        passed = len(errors) == 0
        return ContractValidationResult(
            passed=passed,
            missing_columns=missing_cols,
            null_participant_count=null_pat,
            invalid_visit_codes=invalid_visits,
            excessive_null_columns=excessive_nulls,
            errors=errors,
        )

