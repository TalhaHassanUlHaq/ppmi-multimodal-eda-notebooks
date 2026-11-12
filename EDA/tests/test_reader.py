"""Automated tests for SafeDataReader, logical record counting, and file immutability."""

from pathlib import Path
import os
import pytest
import pandas as pd

from ppmi_pipeline.config.settings import PipelineConfig
from ppmi_pipeline.ingestion.inventory import DatasetInventoryAuditor
from ppmi_pipeline.ingestion.reader import SafeDataReader


def test_safe_read_csv_preserves_content_and_immutability(tmp_path: Path):
    """Verify that SafeDataReader loads data correctly and does not modify the source file."""
    test_csv = tmp_path / "test_data.csv"
    original_content = "PATNO,EVENT_ID,SCORE\n101,BL,25.5\n102,BL,18.0\n"
    test_csv.write_text(original_content, encoding="utf-8")

    initial_mtime = test_csv.stat().st_mtime_ns

    df = SafeDataReader.read_csv(test_csv)
    assert len(df) == 2
    assert list(df.columns) == ["PATNO", "EVENT_ID", "SCORE"]
    assert df["SCORE"].iloc[0] == 25.5

    # Assert source file was not modified
    assert test_csv.stat().st_mtime_ns == initial_mtime
    assert test_csv.read_text(encoding="utf-8") == original_content


def test_count_csv_logical_records_with_quoted_newlines(tmp_path: Path):
    """Verify that logical record counting accurately handles embedded newlines in quoted fields (P1-04)."""
    test_csv = tmp_path / "multiline_quoted.csv"
    # 2 logical data records, but 5 raw newline characters
    content = 'PATNO,NOTE\n101,"Line 1\nLine 2\nLine 3"\n102,"Single line"\n'
    test_csv.write_text(content, encoding="utf-8")

    count = SafeDataReader.count_csv_logical_records(test_csv)
    assert count == 2, f"Expected 2 logical records, got {count}"


def test_count_csv_logical_records_no_trailing_newline(tmp_path: Path):
    """Verify that logical record counting does not miss the final record when trailing newline is absent (P1-04)."""
    test_csv = tmp_path / "no_trailing_newline.csv"
    # 3 data records, no trailing newline after the last row
    content = "PATNO,EVENT_ID,VAL\n1,BL,10\n2,BL,20\n3,BL,30"
    test_csv.write_text(content, encoding="utf-8")

    count = SafeDataReader.count_csv_logical_records(test_csv)
    assert count == 3, f"Expected 3 logical records, got {count}"


def test_read_csv_header_preserves_literal_whitespace_and_duplicates(tmp_path: Path):
    """Verify literal original headers preservation, duplicate detection, and blank tracking (P1-07)."""
    test_csv = tmp_path / "duplicate_headers.csv"
    # Header contains leading/trailing whitespace, a duplicate name 'SCORE', and a blank header
    content = "PATNO , SCORE ,SCORE, \n101,10,20,A\n"
    test_csv.write_text(content, encoding="utf-8")

    lit_headers, dups, blank_cnt, aliases = SafeDataReader.read_csv_header(test_csv)
    # Literal headers preserve original strings exactly
    assert lit_headers == ["PATNO ", " SCORE ", "SCORE", " "]
    assert blank_cnt == 1
    assert "SCORE" in aliases["idx_2_SCORE"]


def test_position_based_column_dictionary_duplicate_headers(tmp_path: Path):
    """Verify that duplicate headers with differing missing counts [0, 1] are accurately recorded (P1-07)."""
    test_csv = tmp_path / "duplicate_cols_missing.csv"
    # Two identical column names 'SCORE', first has value 10, second is empty (null)
    content = "PATNO,SCORE,SCORE\n101,10,\n"
    test_csv.write_text(content, encoding="utf-8")

    lit_headers, _, _, aliases = SafeDataReader.read_csv_header(test_csv)
    df = SafeDataReader.read_csv(test_csv)

    auditor = DatasetInventoryAuditor()
    col_dict = auditor._generate_column_dictionary(df, lit_headers, parser_aliases=aliases)

    assert len(col_dict) == 3
    # Check column 1 (first SCORE): 0 missing
    assert col_dict[1]["original_name"] == "SCORE"
    assert col_dict[1]["missing_numerator"] == 0
    assert col_dict[1]["missingness_percentage"] == 0.0

    # Check column 2 (second SCORE): 1 missing
    assert col_dict[2]["original_name"] == "SCORE"
    assert col_dict[2]["missing_numerator"] == 1
    assert col_dict[2]["missingness_percentage"] == 100.0


def test_zero_row_header_only_file_schema_documentation(tmp_path: Path):
    """Verify that zero-row header-only CSVs retain full column dictionaries with unavailable stats (P1-07)."""
    test_csv = tmp_path / "zero_rows_header_only.csv"
    content = "PATNO,EVENT_ID,PREG_RESULT,TEST_DATE\n"
    test_csv.write_text(content, encoding="utf-8")

    config = PipelineConfig(project_root=tmp_path)
    auditor = DatasetInventoryAuditor(config)
    profile = auditor._audit_source_file(test_csv, tmp_path, "TEST_DOMAIN")

    assert profile.row_count == 0
    assert profile.column_count == 4
    assert len(profile.column_dictionary) == 4

    for entry in profile.column_dictionary:
        assert entry["missingness_percentage"] is None
        assert entry["missing_denominator"] == 0
        assert "Zero data records" in entry["data_status"]

    assert profile.column_dictionary[0]["original_name"] == "PATNO"
    assert profile.column_dictionary[0]["inferred_type"] == "identifier"


def test_compute_sha256(tmp_path: Path):
    """Verify that SHA-256 calculation produces reproducible checksums."""
    test_file = tmp_path / "sample.txt"
    test_file.write_text("PPMI Verification Data", encoding="utf-8")

    hash1 = SafeDataReader.compute_sha256(test_file)
    hash2 = SafeDataReader.compute_sha256(test_file)
    assert hash1 == hash2
    assert len(hash1) == 64


def test_safe_read_csv_encoding_fallback(tmp_path: Path):
    """Verify that files with latin-1 characters are safely loaded without errors."""
    test_csv = tmp_path / "latin1_data.csv"
    test_csv.write_bytes(b"PATNO,NOTE\n101,Caf\xe9 study\n")

    df = SafeDataReader.read_csv(test_csv)
    assert len(df) == 1
    assert "Caf" in df["NOTE"].iloc[0]


def test_safe_read_csv_nonexistent_file_raises():
    """Verify that attempting to read a missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        SafeDataReader.read_csv(Path("nonexistent_table_9999.csv"))
