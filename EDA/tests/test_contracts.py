"""Automated tests for schema contracts and structural enforcement."""

import pandas as pd
import pytest

from ppmi_pipeline.validation.contracts import (
    ContractEnforcer,
    SchemaContract,
)


def test_schema_contract_valid():
    """Verify that a compliant dataframe passes contract validation."""
    df = pd.DataFrame({
        "PATNO": [101, 102],
        "EVENT_ID": ["BL", "V04"],
        "TOTAL_SCORE": [30, 28],
    })

    contract = SchemaContract(
        table_identifier="TEST_SCORE_TABLE",
        required_columns=["PATNO", "EVENT_ID", "TOTAL_SCORE"],
        allowed_visit_codes={"BL", "V04", "V08"},
    )

    res = ContractEnforcer.validate(df, contract)
    assert res.passed is True
    assert len(res.errors) == 0


def test_schema_contract_missing_required_column():
    """Verify that a missing required column is flagged and fails contract."""
    df = pd.DataFrame({
        "PATNO": [101, 102],
        # Missing EVENT_ID
        "TOTAL_SCORE": [30, 28],
    })

    contract = SchemaContract(
        table_identifier="TEST_SCORE_TABLE",
        required_columns=["PATNO", "EVENT_ID", "TOTAL_SCORE"],
    )

    res = ContractEnforcer.validate(df, contract)
    assert res.passed is False
    assert "EVENT_ID" in res.missing_columns


def test_schema_contract_null_participant_id():
    """Verify that null participant IDs are flagged and fail contract."""
    df = pd.DataFrame({
        "PATNO": [101, None],
        "EVENT_ID": ["BL", "V04"],
    })

    contract = SchemaContract(
        table_identifier="TEST_TABLE",
        required_columns=["PATNO", "EVENT_ID"],
        allow_null_participant=False,
    )

    res = ContractEnforcer.validate(df, contract)
    assert res.passed is False
    assert res.null_participant_count == 1


def test_schema_contract_invalid_visit_code():
    """Verify that unexpected visit codes are caught."""
    df = pd.DataFrame({
        "PATNO": [101, 102],
        "EVENT_ID": ["BL", "INVALID_VISIT_99"],
    })

    contract = SchemaContract(
        table_identifier="TEST_TABLE",
        required_columns=["PATNO", "EVENT_ID"],
        allowed_visit_codes={"SC", "BL", "V01", "V04"},
    )

    res = ContractEnforcer.validate(df, contract)
    assert res.passed is False
    assert "INVALID_VISIT_99" in res.invalid_visit_codes

