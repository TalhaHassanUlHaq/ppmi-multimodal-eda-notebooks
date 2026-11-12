"""Automated tests for GrainAnalyzer and observation grain classification."""

import pandas as pd
import pytest

from ppmi_pipeline.modalities.base import ObservationGrain
from ppmi_pipeline.validation.grain import GrainAnalyzer


def test_grain_analyzer_subject_level(synthetic_subject_level_df: pd.DataFrame):
    """Verify that a 1:1 participant table is identified as Subject-Level."""
    res = GrainAnalyzer.analyze(synthetic_subject_level_df)
    assert res.grain == ObservationGrain.SUBJECT_LEVEL
    assert res.is_subject_level_unique is True
    assert res.max_multiplicity_per_subject == 1
    assert ["PATNO"] in res.candidate_primary_keys
    assert res.distinct_participants == 4


def test_grain_analyzer_visit_level(synthetic_visit_level_df: pd.DataFrame):
    """Verify that a visit milestone table is identified as Visit-Level."""
    res = GrainAnalyzer.analyze(synthetic_visit_level_df)
    assert res.grain == ObservationGrain.VISIT_LEVEL
    assert res.is_visit_level_unique is True
    assert res.max_multiplicity_per_visit == 1
    assert ["PATNO", "EVENT_ID"] in res.candidate_primary_keys
    assert res.distinct_participants == 3


def test_grain_analyzer_repeated_event(synthetic_repeated_event_df: pd.DataFrame):
    """Verify that multi-record tables (e.g. meds, adverse events) are identified as Repeated Event."""
    res = GrainAnalyzer.analyze(synthetic_repeated_event_df)
    assert res.grain == ObservationGrain.REPEATED_EVENT_OR_ITEM
    assert res.is_visit_level_unique is False
    assert res.max_multiplicity_per_visit == 2
    # Composite key including LINE_NO achieves uniqueness
    assert ["PATNO", "EVENT_ID", "LINE_NO"] in res.candidate_primary_keys


def test_grain_analyzer_unindexed(synthetic_unindexed_df: pd.DataFrame):
    """Verify that protocol/catalog tables without PATNO are marked Documentation/Metadata."""
    res = GrainAnalyzer.analyze(synthetic_unindexed_df)
    assert res.grain == ObservationGrain.DOCUMENTATION_OR_METADATA
    assert res.has_participant_key is False
    assert res.distinct_participants == 0


def test_grain_analyzer_empty_dataframe():
    """Verify safe handling of an empty dataframe."""
    empty_df = pd.DataFrame(columns=["PATNO", "EVENT_ID", "SCORE"])
    res = GrainAnalyzer.analyze(empty_df)
    assert res.total_records == 0
    assert res.grain == ObservationGrain.UNINDEXED_OR_UNKNOWN


def test_grain_analyzer_scan_sessions_key():
    """Verify scan acquisition session key validation (ImageID) (P1-09)."""
    df_scan = pd.DataFrame({
        "PATNO": [1001, 1001, 1002],
        "EVENT_ID": ["BL", "BL", "BL"],
        "ImageID": [7001, 7002, 7003],
        "SCAN_QUALITY": ["Good", "Good", "Pass"],
    })
    res = GrainAnalyzer.analyze(df_scan)
    assert res.grain == ObservationGrain.REPEATED_EVENT_OR_ITEM
    assert ["ImageID"] in res.candidate_primary_keys
    assert res.max_multiplicity_per_visit == 2


def test_grain_analyzer_aliquot_runs_key():
    """Verify aliquot run key validation with TESTNAME (P1-09)."""
    df_aliquot = pd.DataFrame({
        "PATNO": [1001, 1001, 1002],
        "EVENT_ID": ["BL", "BL", "BL"],
        "TESTNAME": ["ABETA", "TAU", "ABETA"],
        "VAL": [800.5, 120.3, 750.2],
    })
    res = GrainAnalyzer.analyze(df_aliquot)
    assert res.grain == ObservationGrain.REPEATED_EVENT_OR_ITEM
    assert ["PATNO", "EVENT_ID", "TESTNAME"] in res.candidate_primary_keys


def test_grain_analyzer_ambiguous_grain_duplicate_rows():
    """Verify that tables with duplicate observations without a unique key are marked Ambiguous (P1-09)."""
    df_dup = pd.DataFrame({
        "PATNO": [1001, 1001, 1002],
        "EVENT_ID": ["BL", "BL", "BL"],
        "SCORE": [10, 10, 20],  # Duplicate observation for participant 1001 at visit BL
    })
    res = GrainAnalyzer.analyze(df_dup)
    assert res.grain == ObservationGrain.AMBIGUOUS_NEEDS_REVIEW
    assert len(res.candidate_primary_keys) == 0
    assert any("Ambiguous grain" in note for note in res.notes)


def test_grain_analyzer_missing_visits():
    """Verify diagnostics when visit IDs contain nulls (P1-09)."""
    df_missing_vis = pd.DataFrame({
        "PATNO": [1001, 1002, 1003],
        "EVENT_ID": ["BL", None, "V04"],
        "VAL": [1, 2, 3],
    })
    res = GrainAnalyzer.analyze(df_missing_vis)
    assert res.null_visit_keys == 1
    assert any("Contains 1 null visit IDs" in note for note in res.notes)
