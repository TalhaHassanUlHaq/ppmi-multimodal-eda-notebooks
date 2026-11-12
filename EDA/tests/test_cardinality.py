"""Automated tests for JoinValidator and join cardinality enforcement (P1-05)."""

import pandas as pd
import pytest

from ppmi_pipeline.validation.cardinality import (
    IncompatibleJoinGrainError,
    JoinCardinality,
    JoinValidator,
    NullJoinKeyError,
)


def test_join_validator_one_to_one(synthetic_subject_level_df: pd.DataFrame):
    """Verify 1:1 join evaluation between two participant-level tables."""
    second_subject_df = pd.DataFrame({
        "PATNO": [1001, 1002, 1003],
        "GENE": ["LRRK2", "GBA", "SNCA"],
    })

    report = JoinValidator.evaluate(
        left_df=synthetic_subject_level_df,
        right_df=second_subject_df,
        join_keys=["PATNO"],
    )

    assert report.cardinality == JoinCardinality.ONE_TO_ONE
    assert report.is_safe is True
    assert report.left_keys_unique is True
    assert report.right_keys_unique is True
    assert report.intersection_keys_count == 3

    # Safe merge succeeds
    merged = JoinValidator.safe_merge(
        left_df=synthetic_subject_level_df,
        right_df=second_subject_df,
        join_keys=["PATNO"],
        how="inner",
    )
    assert len(merged) == 3


def test_join_validator_one_to_many(
    synthetic_subject_level_df: pd.DataFrame, synthetic_visit_level_df: pd.DataFrame
):
    """Verify 1:Many join evaluation (Subject-Level to Visit-Level)."""
    report = JoinValidator.evaluate(
        left_df=synthetic_subject_level_df,
        right_df=synthetic_visit_level_df,
        join_keys=["PATNO"],
    )

    assert report.cardinality == JoinCardinality.ONE_TO_MANY
    assert report.is_safe is True
    assert report.left_keys_unique is True
    assert report.right_keys_unique is False

    merged = JoinValidator.safe_merge(
        left_df=synthetic_subject_level_df,
        right_df=synthetic_visit_level_df,
        join_keys=["PATNO"],
        how="inner",
    )
    assert len(merged) == 5


def test_join_validator_prevents_null_key_cross_matching():
    """Verify that null join keys NEVER cross-match and estimator matches actual (P1-05)."""
    # Two tables that both contain a row with a null join key
    left = pd.DataFrame({
        "PATNO": [1001, None],
        "LEFT_VAL": ["L1", "L2"],
    })
    right = pd.DataFrame({
        "PATNO": [1001, None],
        "RIGHT_VAL": ["R1", "R2"],
    })

    report = JoinValidator.evaluate(
        left_df=left,
        right_df=right,
        join_keys=["PATNO"],
        how="inner",
    )

    assert report.left_null_keys_count == 1
    assert report.right_null_keys_count == 1
    # Only non-null key 1001 intersects
    assert report.intersection_keys_count == 1
    assert report.estimated_merged_rows == 1

    # In safe_merge with default on_null_keys="reject", it must raise NullJoinKeyError!
    with pytest.raises(NullJoinKeyError):
        JoinValidator.safe_merge(
            left_df=left,
            right_df=right,
            join_keys=["PATNO"],
            how="inner",
            on_null_keys="reject",
        )

    # In safe_merge with on_null_keys="drop", exactly 1 row merged; NULL does NOT match NULL!
    merged, audit = JoinValidator.safe_merge(
        left_df=left,
        right_df=right,
        join_keys=["PATNO"],
        how="inner",
        on_null_keys="drop",
        return_audit=True,
    )
    assert len(merged) == 1
    assert merged["PATNO"].iloc[0] == 1001
    assert audit["left_dropped_null_rows"] == 1
    assert audit["right_dropped_null_rows"] == 1
    assert report.estimated_merged_rows == len(merged)


def test_join_validator_left_join_null_key_disposition():
    """Verify left join handling with explicit on_null_keys policy (P1-05 reverification)."""
    left = pd.DataFrame({
        "PATNO": [1001, None],
        "LEFT_VAL": ["L1", "L2"],
    })
    right = pd.DataFrame({
        "PATNO": [1001, 1002],
        "RIGHT_VAL": ["R1", "R2"],
    })

    # 1. on_null_keys='reject' raises
    with pytest.raises(NullJoinKeyError):
        JoinValidator.safe_merge(left, right, join_keys=["PATNO"], how="left", on_null_keys="reject")

    # 2. on_null_keys='drop' drops the null row and returns audit
    merged_drop, audit_drop = JoinValidator.safe_merge(
        left, right, join_keys=["PATNO"], how="left", on_null_keys="drop", return_audit=True
    )
    assert len(merged_drop) == 1
    assert audit_drop["left_dropped_null_rows"] == 1

    # 3. on_null_keys='preserve_left' preserves the left null row without cross-matching
    merged_pres, audit_pres = JoinValidator.safe_merge(
        left, right, join_keys=["PATNO"], how="left", on_null_keys="preserve_left", return_audit=True
    )
    assert len(merged_pres) == 2
    assert audit_pres["left_dropped_null_rows"] == 0
    assert pd.isna(merged_pres.loc[merged_pres["LEFT_VAL"] == "L2", "RIGHT_VAL"].iloc[0])


def test_join_validator_empty_table_diagnostics():
    """Verify safe diagnostics when tables are empty."""
    empty_left = pd.DataFrame(columns=["PATNO", "VAL"])
    non_empty_right = pd.DataFrame({"PATNO": [1001, 1002], "INFO": ["A", "B"]})

    report = JoinValidator.evaluate(empty_left, non_empty_right, join_keys=["PATNO"], how="inner")
    assert report.left_rows == 0
    assert report.estimated_merged_rows == 0
    assert report.is_safe is True
    assert "At least one table has 0 rows" in report.warnings


def test_join_validator_blocks_many_to_many_unconditionally():
    """Verify that Many:Many joins are strictly blocked without bypass parameters (P1-05)."""
    meds_df = pd.DataFrame({
        "PATNO": [1001, 1001, 1002],
        "MED": ["MedA", "MedB", "MedC"],
    })
    ae_df = pd.DataFrame({
        "PATNO": [1001, 1001, 1002],
        "AE": ["Headache", "Nausea", "Tremor"],
    })

    report = JoinValidator.evaluate(
        left_df=meds_df,
        right_df=ae_df,
        join_keys=["PATNO"],
    )

    assert report.cardinality == JoinCardinality.MANY_TO_MANY
    assert report.is_safe is False
    assert any("Join BLOCKED" in w for w in report.warnings)

    with pytest.raises(IncompatibleJoinGrainError):
        JoinValidator.safe_merge(
            left_df=meds_df,
            right_df=ae_df,
            join_keys=["PATNO"],
        )


def test_join_validator_missing_keys_raises_key_error():
    """Verify KeyError when join keys do not exist in one of the tables."""
    df1 = pd.DataFrame({"PATNO": [1, 2]})
    df2 = pd.DataFrame({"SUBJECT_ID": [1, 2]})

    with pytest.raises(KeyError):
        JoinValidator.evaluate(df1, df2, join_keys=["PATNO"])


def test_join_validator_empty_table_with_null_keys():
    """Verify that null keys opposite an empty table are strictly detected and handled (P1-05 Round 3)."""
    # Two-row left table with one null key
    left_with_null = pd.DataFrame({
        "PATNO": [1001, None],
        "VAL": ["A", "B"],
    })
    empty_right = pd.DataFrame(columns=["PATNO", "INFO"])

    # 1. evaluate() detects the left null key despite empty right table
    report = JoinValidator.evaluate(
        left_with_null, empty_right, join_keys=["PATNO"], how="left", on_null_keys="reject"
    )
    assert report.left_null_keys_count == 1
    assert report.right_null_keys_count == 0
    assert report.is_safe is False
    assert report.estimated_merged_rows == 1  # Valid non-null row

    # 2. safe_merge with default 'reject' policy must raise NullJoinKeyError!
    with pytest.raises(NullJoinKeyError):
        JoinValidator.safe_merge(
            left_with_null, empty_right, join_keys=["PATNO"], how="left", on_null_keys="reject"
        )

    # 3. safe_merge with 'drop' policy drops the null row and accurately reports audit
    merged_drop, audit_drop = JoinValidator.safe_merge(
        left_with_null, empty_right, join_keys=["PATNO"], how="left", on_null_keys="drop", return_audit=True
    )
    assert len(merged_drop) == 1
    assert audit_drop["left_dropped_null_rows"] == 1
    assert audit_drop["right_dropped_null_rows"] == 0
    assert audit_drop["merged_output_rows"] == 1
    assert report.estimated_merged_rows == len(merged_drop)

    # 4. safe_merge with 'preserve_left' preserves the null row
    report_pres = JoinValidator.evaluate(
        left_with_null, empty_right, join_keys=["PATNO"], how="left", on_null_keys="preserve_left"
    )
    assert report_pres.estimated_merged_rows == 2
    merged_pres, audit_pres = JoinValidator.safe_merge(
        left_with_null, empty_right, join_keys=["PATNO"], how="left", on_null_keys="preserve_left", return_audit=True
    )
    assert len(merged_pres) == 2
    assert audit_pres["left_dropped_null_rows"] == 0
    assert report_pres.estimated_merged_rows == len(merged_pres)


def test_join_validator_empty_left_with_right_null():
    """Verify that null keys on the right opposite an empty left table are detected."""
    empty_left = pd.DataFrame(columns=["PATNO", "VAL"])
    right_with_null = pd.DataFrame({"PATNO": [1001, None], "INFO": ["A", "B"]})

    # evaluate detects right null
    report = JoinValidator.evaluate(empty_left, right_with_null, join_keys=["PATNO"], on_null_keys="reject")
    assert report.right_null_keys_count == 1
    assert report.is_safe is False

    with pytest.raises(NullJoinKeyError):
        JoinValidator.safe_merge(empty_left, right_with_null, join_keys=["PATNO"], on_null_keys="reject")


def test_join_validator_invalid_policy_raises():
    """Verify that unrecognized on_null_keys policy raises ValueError immediately."""
    df1 = pd.DataFrame({"PATNO": [1001, 1002]})
    df2 = pd.DataFrame({"PATNO": [1001, 1002]})

    with pytest.raises(ValueError, match="Invalid on_null_keys policy"):
        JoinValidator.safe_merge(df1, df2, join_keys=["PATNO"], on_null_keys="ignore_and_cross_match")

    with pytest.raises(ValueError, match="only valid for left joins"):
        JoinValidator.safe_merge(df1, df2, join_keys=["PATNO"], how="inner", on_null_keys="preserve_left")


def test_join_validator_estimated_vs_actual_rows_agreement():
    """Verify that estimator matches actual merged row count across all join types."""
    left = pd.DataFrame({"PATNO": [1001, 1002, 1003], "L": ["A", "B", "C"]})
    right = pd.DataFrame({"PATNO": [1002, 1003, 1004], "R": ["X", "Y", "Z"]})

    for join_type in ["inner", "left", "right", "outer"]:
        rep = JoinValidator.evaluate(left, right, join_keys=["PATNO"], how=join_type)
        merged = JoinValidator.safe_merge(left, right, join_keys=["PATNO"], how=join_type)
        assert rep.estimated_merged_rows == len(merged), f"Mismatch for {join_type} join!"
