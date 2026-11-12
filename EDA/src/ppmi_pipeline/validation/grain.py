"""Observation grain identification and candidate key analysis.

Determines the level of granularity (Subject, Visit, Repeated-Item, Aliquot/Run, Ambiguous)
for any given PPMI dataset without altering records.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd

from ..modalities.base import ObservationGrain


@dataclass
class GrainAnalysisResult:
    """Detailed results of observation grain evaluation."""
    grain: ObservationGrain
    has_participant_key: bool
    has_visit_key: bool
    participant_col: Optional[str]
    visit_col: Optional[str]
    total_records: int
    distinct_participants: int
    distinct_visits: int
    null_participant_keys: int
    null_visit_keys: int
    is_subject_level_unique: bool
    is_visit_level_unique: bool
    max_multiplicity_per_subject: int
    max_multiplicity_per_visit: int
    is_full_data_validated: bool = True
    candidate_primary_keys: List[List[str]] = field(default_factory=list)
    multiplicity_summary: Dict[str, int] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)


class GrainAnalyzer:
    """Engine analyzing relational observation grain and key invariants."""

    PARTICIPANT_KEY_CANDIDATES = ["PATNO", "ALIAS_ID", "SUBJECT_ID", "SUBJID", "Participant_ID"]
    VISIT_KEY_CANDIDATES = ["EVENT_ID", "VISIT", "VISIT_ID", "CLINICAL_EVENT", "Visit"]

    # Candidate columns that can form composite primary keys with (PATNO, EVENT_ID)
    NATURAL_COMPOSITE_CANDIDATES = [
        ["PAG_NAME", "PDSTATE"],
        ["PAG_NAME", "ORIG_ENTRY"],
        ["ORIG_ENTRY"],
        ["LINE_NO"],
        ["SEQNO1"],
        ["SEQNO"],
        ["PET_LIGAND"],
        ["PET_SCAN_DATE"],
        ["SV2A_REGION"],
        ["TESTNAME"],
        ["TEST_NAME"],
        ["DIAGNOSIS"],
        ["MHCAT"],
        ["AETERM"],
        ["CMTRT"],
        ["RUNDATE"],
        ["SUB_EVENT_ID"],
    ]

    @classmethod
    def find_column(cls, df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
        """Find matching column case-insensitively from a candidate list."""
        col_map = {str(c).strip().upper(): c for c in df.columns}
        for cand in candidates:
            if cand.upper() in col_map:
                return col_map[cand.upper()]
        return None

    @classmethod
    def analyze(
        cls,
        df: pd.DataFrame,
        file_context: str = "",
        is_sample: bool = False,
    ) -> GrainAnalysisResult:
        """Evaluate observation grain for a given dataframe with full candidate key validation."""
        total_rows = len(df)
        if total_rows == 0:
            pat_col = cls.find_column(df, cls.PARTICIPANT_KEY_CANDIDATES)
            vis_col = cls.find_column(df, cls.VISIT_KEY_CANDIDATES)
            grain = ObservationGrain.UNINDEXED_OR_UNKNOWN if pat_col else ObservationGrain.DOCUMENTATION_OR_METADATA
            return GrainAnalysisResult(
                grain=grain,
                has_participant_key=pat_col is not None,
                has_visit_key=vis_col is not None,
                participant_col=pat_col,
                visit_col=vis_col,
                total_records=0,
                distinct_participants=0,
                distinct_visits=0,
                null_participant_keys=0,
                null_visit_keys=0,
                is_subject_level_unique=False,
                is_visit_level_unique=False,
                max_multiplicity_per_subject=0,
                max_multiplicity_per_visit=0,
                is_full_data_validated=not is_sample,
                candidate_primary_keys=[],
                notes=["Zero data records (header line only)"],
            )

        col_map = {str(c).strip().upper(): c for c in df.columns}
        pat_col = cls.find_column(df, cls.PARTICIPANT_KEY_CANDIDATES)
        vis_col = cls.find_column(df, cls.VISIT_KEY_CANDIDATES)

        has_pat = pat_col is not None
        has_vis = vis_col is not None

        if not has_pat:
            return GrainAnalysisResult(
                grain=ObservationGrain.DOCUMENTATION_OR_METADATA,
                has_participant_key=False,
                has_visit_key=has_vis,
                participant_col=None,
                visit_col=vis_col,
                total_records=total_rows,
                distinct_participants=0,
                distinct_visits=0,
                null_participant_keys=0,
                null_visit_keys=0,
                is_subject_level_unique=False,
                is_visit_level_unique=False,
                max_multiplicity_per_subject=0,
                max_multiplicity_per_visit=0,
                is_full_data_validated=not is_sample,
                candidate_primary_keys=[],
                notes=["Table has no participant identifier (Reference / Protocol / Catalog data)"],
            )

        null_pat = int(df[pat_col].isna().sum())
        distinct_pat = int(df[pat_col].nunique(dropna=True))
        is_sub_unique = (distinct_pat == total_rows) and (null_pat == 0)

        # Subject-level multiplicity on valid non-null IDs
        valid_pat_df = df.dropna(subset=[pat_col])
        sub_counts = valid_pat_df[pat_col].value_counts() if len(valid_pat_df) > 0 else pd.Series(dtype=int)
        max_sub_mult = int(sub_counts.max()) if len(sub_counts) > 0 else 0

        # Visit-level analysis
        is_vis_unique = False
        distinct_vis = 0
        null_vis = 0
        max_vis_mult = 0
        dup_vis_pairs = 0

        if has_vis:
            null_vis = int(df[vis_col].isna().sum())
            distinct_vis = int(df[vis_col].nunique(dropna=True))
            valid_vis_df = df.dropna(subset=[pat_col, vis_col])
            if len(valid_vis_df) > 0:
                vis_grouped = valid_vis_df.groupby([pat_col, vis_col], dropna=False).size()
                max_vis_mult = int(vis_grouped.max()) if len(vis_grouped) > 0 else 0
                dup_vis_pairs = int((vis_grouped > 1).sum())
                is_vis_unique = (max_vis_mult == 1) and (null_pat == 0) and (null_vis == 0)

        # Candidate key search with empirical validation
        candidate_keys: List[List[str]] = []

        if is_sub_unique:
            candidate_keys.append([pat_col])
        elif has_vis and is_vis_unique:
            candidate_keys.append([pat_col, vis_col])
        else:
            # Check surrogate REC_ID
            if "REC_ID" in col_map:
                rc = col_map["REC_ID"]
                if df[rc].isna().sum() == 0 and df[rc].nunique() == total_rows:
                    candidate_keys.append([rc])

            # Check ImageID
            if "ImageID" in df.columns:
                if df["ImageID"].isna().sum() == 0 and df["ImageID"].nunique() == total_rows:
                    candidate_keys.append(["ImageID"])

            # Check natural composite keys based on [pat_col, vis_col] + extra columns
            if has_vis:
                for cand in cls.NATURAL_COMPOSITE_CANDIDATES:
                    if all(k.upper() in col_map for k in cand):
                        actual_cols = [pat_col, vis_col] + [col_map[k.upper()] for k in cand]
                        # Check no nulls in candidate key
                        clean_test = df.dropna(subset=actual_cols)
                        if len(clean_test) == total_rows:
                            grp_max = clean_test.groupby(actual_cols, dropna=False).size().max()
                            if grp_max == 1:
                                candidate_keys.append(actual_cols)

        notes: List[str] = []
        if is_sample:
            notes.append("Provisional grain evaluated on sampled rows (not certified for multi-table merges).")

        if null_pat > 0:
            notes.append(f"Contains {null_pat} null participant IDs.")
        if null_vis > 0:
            notes.append(f"Contains {null_vis} null visit IDs.")

        # Determine Observation Grain
        if is_sub_unique:
            grain = ObservationGrain.SUBJECT_LEVEL
            notes.append("Subject-Level: exactly 1 non-null observation per participant.")
        elif has_vis and is_vis_unique:
            grain = ObservationGrain.VISIT_LEVEL
            notes.append("Visit-Level: exactly 1 non-null observation per participant-visit milestone.")
        elif has_vis and not is_vis_unique:
            if len(candidate_keys) > 0:
                grain = ObservationGrain.REPEATED_EVENT_OR_ITEM
                key_str = "; ".join([", ".join(k) for k in candidate_keys[:2]])
                notes.append(f"Repeated Event: multiple records per visit (max {max_vis_mult} records per visit; validated keys: {key_str}).")
            else:
                grain = ObservationGrain.AMBIGUOUS_NEEDS_REVIEW
                notes.append(f"Ambiguous grain: no unique candidate key found ({dup_vis_pairs} duplicate visits, max multiplicity {max_vis_mult}).")
        else:
            # Table without visit key but multiple rows per subject
            if len(candidate_keys) > 0:
                grain = ObservationGrain.REPEATED_EVENT_OR_ITEM
                notes.append(f"Repeated Event: multiple records per subject without visit key (max {max_sub_mult} per subject).")
            else:
                grain = ObservationGrain.AMBIGUOUS_NEEDS_REVIEW
                notes.append(f"Ambiguous grain: no candidate primary key uniquely identifies records (max {max_sub_mult} records per subject).")

        return GrainAnalysisResult(
            grain=grain,
            has_participant_key=True,
            has_visit_key=has_vis,
            participant_col=pat_col,
            visit_col=vis_col,
            total_records=total_rows,
            distinct_participants=distinct_pat,
            distinct_visits=distinct_vis,
            null_participant_keys=null_pat,
            null_visit_keys=null_vis,
            is_subject_level_unique=is_sub_unique,
            is_visit_level_unique=is_vis_unique,
            max_multiplicity_per_subject=max_sub_mult,
            max_multiplicity_per_visit=max_vis_mult,
            is_full_data_validated=not is_sample,
            candidate_primary_keys=candidate_keys,
            multiplicity_summary={
                "max_per_subject": max_sub_mult,
                "max_per_visit": max_vis_mult,
                "duplicate_vis_pairs": dup_vis_pairs,
            },
            notes=notes,
        )
