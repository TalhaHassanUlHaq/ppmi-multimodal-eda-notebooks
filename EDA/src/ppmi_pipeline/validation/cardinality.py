"""Join cardinality validation engine and safe relational merge operations.

Enforces strict relational invariants:
- Unconditional prohibition of unchecked Many:Many joins.
- Explicit call-boundary handling of null join keys (reject, drop, or preserve_left).
- Guaranteed prevention of null-key cross-matching (NULL != NULL).
- Rigorous estimation and audit reporting for merged and dropped rows.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import pandas as pd


class JoinCardinality(str, Enum):
    """Categorization of join relationship between two tables."""
    ONE_TO_ONE = "1:1 (One-to-One)"
    ONE_TO_MANY = "1:Many (One-to-Many)"
    MANY_TO_ONE = "Many:1 (Many-to-One)"
    MANY_TO_MANY = "Many:Many (Cartesian Explosion Risk)"
    UNKNOWN = "Unknown / Undefined"


class IncompatibleJoinGrainError(ValueError):
    """Raised when an attempted join violates observation grain or cardinality rules."""
    pass


class NullJoinKeyError(ValueError):
    """Raised when null join keys are present and on_null_keys='reject'."""
    pass


@dataclass
class JoinValidationReport:
    """Detailed structural diagnostic report for a prospective merge."""
    join_keys: List[str]
    cardinality: JoinCardinality
    is_safe: bool
    left_rows: int
    right_rows: int
    left_null_keys_count: int
    right_null_keys_count: int
    left_keys_unique: bool
    right_keys_unique: bool
    left_distinct_keys: int
    right_distinct_keys: int
    intersection_keys_count: int
    left_only_keys_count: int
    right_only_keys_count: int
    estimated_merged_rows: int
    row_inflation_ratio: float
    warnings: List[str] = field(default_factory=list)


class JoinValidator:
    """Validates grain compatibility and safely executes joins."""

    @classmethod
    def evaluate(
        cls,
        left_df: pd.DataFrame,
        right_df: pd.DataFrame,
        join_keys: List[str],
        how: str = "inner",
        on_null_keys: str = "reject",
        left_name: str = "LeftTable",
        right_name: str = "RightTable",
    ) -> JoinValidationReport:
        """Evaluate observation grain, key overlap, and cardinality prior to merging."""
        # 0. Validate on_null_keys policy
        ALLOWED_NULL_POLICIES = {"reject", "drop", "preserve_left"}
        if on_null_keys not in ALLOWED_NULL_POLICIES:
            raise ValueError(
                f"Invalid on_null_keys policy '{on_null_keys}'. Must be one of: {sorted(ALLOWED_NULL_POLICIES)}."
            )
        if on_null_keys == "preserve_left" and how != "left":
            raise ValueError(
                f"Policy on_null_keys='preserve_left' is only valid for left joins, but how='{how}' was requested."
            )

        # 1. Validate join keys exist in both tables
        for k in join_keys:
            if k not in left_df.columns:
                raise KeyError(f"Join key '{k}' missing from {left_name}")
            if k not in right_df.columns:
                raise KeyError(f"Join key '{k}' missing from {right_name}")

        left_rows = len(left_df)
        right_rows = len(right_df)

        # 2. Check for null join keys in both tables UNCONDITIONALLY before empty-table returns
        left_null_mask = left_df[join_keys].isna().any(axis=1) if left_rows > 0 else pd.Series([], dtype=bool)
        right_null_mask = right_df[join_keys].isna().any(axis=1) if right_rows > 0 else pd.Series([], dtype=bool)

        left_null_count = int(left_null_mask.sum())
        right_null_count = int(right_null_mask.sum())

        warnings: List[str] = []
        if left_null_count > 0:
            warnings.append(f"{left_name} has {left_null_count} rows with null join key(s); null keys must not match.")
        if right_null_count > 0:
            warnings.append(f"{right_name} has {right_null_count} rows with null join key(s); null keys must not match.")

        # Filter out rows with null join keys for strict relational evaluation
        left_valid = left_df[~left_null_mask] if left_rows > 0 else left_df
        right_valid = right_df[~right_null_mask] if right_rows > 0 else right_df

        # If either table has 0 valid non-null rows
        if len(left_valid) == 0 or len(right_valid) == 0:
            if left_rows == 0 or right_rows == 0:
                warnings.append("At least one table has 0 rows")

            if how == "inner":
                est_rows = 0
            elif how == "left":
                est_rows = left_rows if on_null_keys == "preserve_left" else len(left_valid)
            elif how == "right":
                est_rows = len(right_valid)
            elif how == "outer":
                est_rows = (left_rows if on_null_keys == "preserve_left" else len(left_valid)) + len(right_valid)
            else:
                est_rows = 0

            is_safe = True
            if left_null_count > 0 or right_null_count > 0:
                if on_null_keys == "reject":
                    is_safe = False

            return JoinValidationReport(
                join_keys=join_keys,
                cardinality=JoinCardinality.ONE_TO_ONE,
                is_safe=is_safe,
                left_rows=left_rows,
                right_rows=right_rows,
                left_null_keys_count=left_null_count,
                right_null_keys_count=right_null_count,
                left_keys_unique=True,
                right_keys_unique=True,
                left_distinct_keys=0,
                right_distinct_keys=0,
                intersection_keys_count=0,
                left_only_keys_count=len(left_valid),
                right_only_keys_count=len(right_valid),
                estimated_merged_rows=est_rows,
                row_inflation_ratio=0.0,
                warnings=warnings,
            )

        # 3. Key uniqueness checks on non-null rows
        left_counts = left_valid.groupby(join_keys, dropna=False).size()
        right_counts = right_valid.groupby(join_keys, dropna=False).size()

        left_keys_unique = bool((left_counts.max() == 1))
        right_keys_unique = bool((right_counts.max() == 1))

        # 4. Determine Cardinality
        if left_keys_unique and right_keys_unique:
            cardinality = JoinCardinality.ONE_TO_ONE
        elif left_keys_unique and not right_keys_unique:
            cardinality = JoinCardinality.ONE_TO_MANY
        elif not left_keys_unique and right_keys_unique:
            cardinality = JoinCardinality.MANY_TO_ONE
        else:
            cardinality = JoinCardinality.MANY_TO_MANY

        # 5. Key set overlap analysis (non-null keys only)
        left_key_set = set(left_counts.index)
        right_key_set = set(right_counts.index)

        common_keys = left_key_set.intersection(right_key_set)
        left_only = left_key_set.difference(right_key_set)
        right_only = right_key_set.difference(left_key_set)

        # 6. Estimate exact row count based on join type and null key policy
        shared_left_counts = left_counts.loc[list(common_keys)] if common_keys else pd.Series(dtype=int)
        shared_right_counts = right_counts.loc[list(common_keys)] if common_keys else pd.Series(dtype=int)
        inner_matches = int((shared_left_counts * shared_right_counts).sum()) if len(common_keys) > 0 else 0

        if how == "inner":
            est_rows = inner_matches
        elif how == "left":
            left_unmatched = int(left_counts.loc[list(left_only)].sum()) if left_only else 0
            preserved_nulls = left_null_count if on_null_keys == "preserve_left" else 0
            est_rows = inner_matches + left_unmatched + preserved_nulls
        elif how == "right":
            right_unmatched = int(right_counts.loc[list(right_only)].sum()) if right_only else 0
            est_rows = inner_matches + right_unmatched
        elif how == "outer":
            left_unmatched = int(left_counts.loc[list(left_only)].sum()) if left_only else 0
            right_unmatched = int(right_counts.loc[list(right_only)].sum()) if right_only else 0
            preserved_nulls = left_null_count if on_null_keys == "preserve_left" else 0
            est_rows = inner_matches + left_unmatched + right_unmatched + preserved_nulls
        else:
            est_rows = inner_matches

        baseline_rows = max(len(left_valid), 1)
        row_inflation = est_rows / baseline_rows

        is_safe = True
        if cardinality == JoinCardinality.MANY_TO_MANY:
            is_safe = False
            warnings.append(
                f"MANY:MANY relationship detected on keys {join_keys}. "
                f"Left max multiplicity: {left_counts.max()}; Right max multiplicity: {right_counts.max()}. "
                "Join BLOCKED. Many-to-many joins require prior validated aggregation or key refinement."
            )

        if left_null_count > 0 or right_null_count > 0:
            warnings.append(
                f"Null join keys present (Left: {left_null_count}, Right: {right_null_count}). "
                "Explicit null-key disposition policy required at call boundary."
            )
            if on_null_keys == "reject":
                is_safe = False

        return JoinValidationReport(
            join_keys=join_keys,
            cardinality=cardinality,
            is_safe=is_safe,
            left_rows=left_rows,
            right_rows=right_rows,
            left_null_keys_count=left_null_count,
            right_null_keys_count=right_null_count,
            left_keys_unique=left_keys_unique,
            right_keys_unique=right_keys_unique,
            left_distinct_keys=len(left_key_set),
            right_distinct_keys=len(right_key_set),
            intersection_keys_count=len(common_keys),
            left_only_keys_count=len(left_only),
            right_only_keys_count=len(right_only),
            estimated_merged_rows=est_rows,
            row_inflation_ratio=row_inflation,
            warnings=warnings,
        )

    @classmethod
    def safe_merge(
        cls,
        left_df: pd.DataFrame,
        right_df: pd.DataFrame,
        join_keys: List[str],
        how: str = "inner",
        on_null_keys: str = "reject",
        return_audit: bool = False,
        left_name: str = "LeftTable",
        right_name: str = "RightTable",
        **merge_kwargs: Any,
    ) -> Union[pd.DataFrame, Tuple[pd.DataFrame, Dict[str, Any]]]:
        """Execute a merge operation ONLY after validating observation grain and cardinality.
        
        Parameters:
            left_df: Left input dataframe.
            right_df: Right input dataframe.
            join_keys: List of column names to join on.
            how: Join method ('inner', 'left', 'right', 'outer'). Default: 'inner'.
            on_null_keys: Policy for handling null join keys:
                - 'reject' (default): Raise NullJoinKeyError if any null join keys are present.
                - 'drop': Drop rows with null join keys before merging; audits dropped rows.
                - 'preserve_left': For left joins, preserve left rows with null keys without matching.
            return_audit: If True, returns a tuple of (merged_df, audit_dict).
        
        Strict Invariants:
        - Blocks Many-to-Many joins unconditionally.
        - Guaranteed prevention of null-key cross-matching (NULL != NULL).
        - Explicit call-boundary audit of null-key disposition.
        """
        # 1. Validate on_null_keys policy string immediately
        ALLOWED_NULL_POLICIES = {"reject", "drop", "preserve_left"}
        if on_null_keys not in ALLOWED_NULL_POLICIES:
            raise ValueError(
                f"Invalid on_null_keys policy '{on_null_keys}'. Must be one of: {sorted(ALLOWED_NULL_POLICIES)}."
            )
        if on_null_keys == "preserve_left" and how != "left":
            raise ValueError(
                f"Policy on_null_keys='preserve_left' is only valid for left joins, but how='{how}' was requested."
            )

        # 2. Count null keys on both inputs UNCONDITIONALLY
        for k in join_keys:
            if k not in left_df.columns:
                raise KeyError(f"Join key '{k}' missing from {left_name}")
            if k not in right_df.columns:
                raise KeyError(f"Join key '{k}' missing from {right_name}")

        left_null_mask = left_df[join_keys].isna().any(axis=1) if len(left_df) > 0 else pd.Series([], dtype=bool)
        right_null_mask = right_df[join_keys].isna().any(axis=1) if len(right_df) > 0 else pd.Series([], dtype=bool)

        left_null_count = int(left_null_mask.sum())
        right_null_count = int(right_null_mask.sum())

        # If on_null_keys is 'reject', any null key raises NullJoinKeyError unconditionally!
        if left_null_count > 0 or right_null_count > 0:
            if on_null_keys == "reject":
                raise NullJoinKeyError(
                    f"Null join keys detected in merge inputs (Left nulls: {left_null_count}, "
                    f"Right nulls: {right_null_count}). By default (on_null_keys='reject'), "
                    "joins with null keys are rejected to prevent silent data loss or cross-matching. "
                    "Specify on_null_keys='drop' or on_null_keys='preserve_left' with an audit policy."
                )

        # 3. Evaluate cardinality and safety
        report = cls.evaluate(
            left_df=left_df,
            right_df=right_df,
            join_keys=join_keys,
            how=how,
            on_null_keys=on_null_keys,
            left_name=left_name,
            right_name=right_name,
        )

        if report.cardinality == JoinCardinality.MANY_TO_MANY:
            raise IncompatibleJoinGrainError(
                f"Unsafe merge between '{left_name}' and '{right_name}' on {join_keys}. "
                f"Cardinality is {report.cardinality.value}. "
                f"Warnings: {'; '.join(report.warnings)}"
            )

        left_clean = left_df[~left_null_mask] if len(left_df) > 0 else left_df
        right_clean = right_df[~right_null_mask] if len(right_df) > 0 else right_df

        if how == "left" and on_null_keys == "preserve_left":
            merged_non_null = pd.merge(left_clean, right_clean, on=join_keys, how="left", **merge_kwargs)
            left_null_rows = left_df[left_null_mask].copy()
            # Add missing columns from right_df as NA
            for col in right_df.columns:
                if col not in left_null_rows.columns:
                    left_null_rows[col] = pd.NA
            merged = pd.concat([merged_non_null, left_null_rows], ignore_index=True)
            left_dropped = 0
            right_dropped = right_null_count
        else:
            merged = pd.merge(left_clean, right_clean, on=join_keys, how=how, **merge_kwargs)
            left_dropped = left_null_count
            right_dropped = right_null_count

        audit = {
            "join_keys": join_keys,
            "how": how,
            "on_null_keys_policy": on_null_keys,
            "left_input_rows": len(left_df),
            "right_input_rows": len(right_df),
            "left_dropped_null_rows": left_dropped,
            "right_dropped_null_rows": right_dropped,
            "merged_output_rows": len(merged),
            "cardinality": report.cardinality.value,
        }

        if return_audit:
            return merged, audit
        return merged
