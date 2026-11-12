"""Automated tests for privacy guardrails and adversarial data leakage prevention (P1-06)."""

import pytest

from ppmi_pipeline.reporting.privacy import (
    PrivacyGuard,
    PrivacyViolationError,
)


def test_privacy_guard_allows_safe_aggregates():
    """Verify that pure aggregate metadata and summary stats pass privacy check."""
    valid_aggregate_report = {
        "domain": "MOTOR",
        "total_records": 1500,
        "row_count": 20408,
        "distinct_participants": 5019,
        "distinct_visits": 19,
        "null_participant_keys": 0,
        "columns": ["PATNO", "EVENT_ID", "NP3TOT"],
        "has_patno": True,
        "file_size_bytes": 35651234,
    }

    # Should pass without raising
    scrubbed = PrivacyGuard.scrub_report_dict(valid_aggregate_report)
    assert scrubbed["distinct_participants"] == 5019
    assert scrubbed["row_count"] == 20408


def test_privacy_guard_blocks_single_generic_identifier():
    """Verify that a single participant identifier under a generic key is blocked (P1-06 probe)."""
    probe_single_id = {
        "domain": "CLINICAL",
        "participant": 10874,
    }
    with pytest.raises(PrivacyViolationError):
        PrivacyGuard.assert_no_participant_records(probe_single_id)


def test_privacy_guard_blocks_single_string_identifier():
    """Verify that a single string participant identifier under generic key is blocked (P1-06 probe)."""
    probe_single_str = {
        "result": {
            "id": "P1001",
        }
    }
    with pytest.raises(PrivacyViolationError):
        PrivacyGuard.assert_no_participant_records(probe_single_str)


def test_privacy_guard_blocks_generic_row_shaped_record():
    """Verify that a row-shaped record with generic keys (id + score) is blocked (P1-06 probe)."""
    generic_row = {
        "test_sample": {
            "id": 10874,
            "score": 32.5,
        }
    }
    with pytest.raises(PrivacyViolationError):
        PrivacyGuard.assert_no_participant_records(generic_row)


def test_privacy_guard_blocks_single_item_in_list():
    """Verify that even a single participant ID in a list is blocked (P1-06)."""
    list_with_one_id = {
        "cohort": [10874],
    }
    with pytest.raises(PrivacyViolationError):
        PrivacyGuard.assert_no_participant_records(list_with_one_id)


def test_privacy_guard_blocks_ids_under_generic_key():
    """Verify that participant ID lists under generic keys like 'participants' are blocked (P1-06)."""
    leaky_report = {
        "domain": "MOTOR",
        "participants": [10874, 10875, 10876],
    }
    with pytest.raises(PrivacyViolationError):
        PrivacyGuard.assert_no_participant_records(leaky_report)


def test_privacy_guard_blocks_nested_row_level_record():
    """Verify that individual participant row records are blocked (P1-06)."""
    row_record_report = {
        "example_row": {
            "PATNO": 10874,
            "EVENT_ID": "BL",
            "NP3TOT": 32,
        }
    }
    with pytest.raises(PrivacyViolationError):
        PrivacyGuard.assert_no_participant_records(row_record_report)


def test_privacy_guard_sanitizes_exception_strings():
    """Verify that exception sanitizer redacts participant ID patterns from error traces (P1-06)."""
    err = ValueError("Failed to parse record for PATNO 10874 at line 52")
    sanitized = PrivacyGuard.sanitize_exception(err)
    assert "10874" not in sanitized
    assert "[REDACTED_ID]" in sanitized


def test_privacy_guard_notebook_output_validation():
    """Verify that notebook validator detects HTML and stream text leakage (P1-06)."""
    clean_notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "source": "# Summary Report\nAggregate summary of PPMI cohort."
            },
            {
                "cell_type": "code",
                "outputs": [
                    {
                        "name": "stdout",
                        "text": "Total records indexed: 20,408\nDistinct participants: 5,019\n"
                    },
                    {
                        "data": {
                            "text/plain": "DataFrame summary: 177 files",
                            "text/html": "<table><tr><td>177 files</td></tr></table>"
                        }
                    }
                ]
            }
        ]
    }
    # Clean notebook passes
    PrivacyGuard.validate_notebook_outputs(clean_notebook)

    # Leaky notebook with HTML row dict is caught
    leaky_notebook = {
        "cells": [
            {
                "cell_type": "code",
                "outputs": [
                    {
                        "data": {
                            "text/html": "<div>Row: {'PATNO': 10874, 'NP3TOT': 32}</div>"
                        }
                    }
                ]
            }
        ]
    }
    with pytest.raises(PrivacyViolationError):
        PrivacyGuard.validate_notebook_outputs(leaky_notebook)


def test_privacy_guard_blocks_adversarial_count_key_bypass():
    """Verify that collection under count field {'row_count': [12345]} is blocked (P1-06 Round 3)."""
    probe_list_under_count = {"row_count": [12345]}
    with pytest.raises(PrivacyViolationError) as exc_info:
        PrivacyGuard.assert_no_participant_records(probe_list_under_count)
    # Ensure synthetic ID is redacted in exception message
    assert "12345" not in str(exc_info.value)
    assert "[REDACTED" in str(exc_info.value) or "collection type" in str(exc_info.value).lower()


def test_privacy_guard_blocks_unauthorized_total_prefix():
    """Verify that arbitrary unapproved key {'total_note': 12345} is blocked (P1-06 Round 3)."""
    probe_total_prefix = {"total_note": 12345}
    with pytest.raises(PrivacyViolationError) as exc_info:
        PrivacyGuard.assert_no_participant_records(probe_total_prefix)
    assert "12345" not in str(exc_info.value)
    assert "[REDACTED_ID]" in str(exc_info.value)


def test_privacy_guard_blocks_plain_text_patno_in_notebook():
    """Verify that plain text 'PATNO: 12345' is caught by notebook validator (P1-06 Round 3)."""
    leaky_plain_text_nb = {
        "cells": [
            {
                "cell_type": "code",
                "outputs": [
                    {
                        "name": "stdout",
                        "text": "Selected record: PATNO: 12345 status confirmed"
                    }
                ]
            }
        ]
    }
    with pytest.raises(PrivacyViolationError) as exc_info:
        PrivacyGuard.validate_notebook_outputs(leaky_plain_text_nb)
    assert "12345" not in str(exc_info.value)


def test_privacy_guard_blocks_html_row_with_id_and_visit():
    """Verify that HTML table row with ID and visit code is caught (P1-06 Round 3)."""
    leaky_html_nb = {
        "cells": [
            {
                "cell_type": "code",
                "outputs": [
                    {
                        "data": {
                            "text/html": "<table><tr><td>12345</td><td>BL</td><td>24.0</td></tr></table>"
                        }
                    }
                ]
            }
        ]
    }
    with pytest.raises(PrivacyViolationError) as exc_info:
        PrivacyGuard.validate_notebook_outputs(leaky_html_nb)
    assert "12345" not in str(exc_info.value)


def test_privacy_guard_blocks_generic_participant_text():
    """Verify that generic text 'Participant 12345 was seen' is blocked (P1-06 Round 4)."""
    leaky_nb = {
        "cells": [
            {
                "cell_type": "code",
                "outputs": [
                    {
                        "name": "stdout",
                        "text": "Participant 12345 was seen during clinical evaluation."
                    }
                ]
            }
        ]
    }
    with pytest.raises(PrivacyViolationError) as exc_info:
        PrivacyGuard.validate_notebook_outputs(leaky_nb)
    assert "12345" not in str(exc_info.value)


def test_privacy_guard_blocks_html_row_id_and_score_without_visit():
    """Verify that HTML table row with ID and score but no visit code is blocked (P1-06 Round 4)."""
    leaky_nb = {
        "cells": [
            {
                "cell_type": "code",
                "outputs": [
                    {
                        "data": {
                            "text/html": "<table><tr><td>12345</td><td>18.5</td></tr></table>"
                        }
                    }
                ]
            }
        ]
    }
    with pytest.raises(PrivacyViolationError) as exc_info:
        PrivacyGuard.validate_notebook_outputs(leaky_nb)
    assert "12345" not in str(exc_info.value)


def test_privacy_guard_blocks_application_json_with_patno_and_score():
    """Verify that application/json MIME payload with PATNO and score is blocked (P1-06 Round 4)."""
    leaky_nb = {
        "cells": [
            {
                "cell_type": "code",
                "outputs": [
                    {
                        "data": {
                            "application/json": {"PATNO": 12345, "score": 25.0}
                        }
                    }
                ]
            }
        ]
    }
    with pytest.raises(PrivacyViolationError) as exc_info:
        PrivacyGuard.validate_notebook_outputs(leaky_nb)
    assert "12345" not in str(exc_info.value)


def test_privacy_guard_blocks_svg_text_with_patno():
    """Verify that SVG text containing PATNO: 12345 is blocked (P1-06 Round 4)."""
    leaky_nb = {
        "cells": [
            {
                "cell_type": "code",
                "outputs": [
                    {
                        "data": {
                            "image/svg+xml": "<svg><text>PATNO: 12345</text></svg>"
                        }
                    }
                ]
            }
        ]
    }
    with pytest.raises(PrivacyViolationError) as exc_info:
        PrivacyGuard.validate_notebook_outputs(leaky_nb)
    assert "12345" not in str(exc_info.value)


def test_privacy_guard_blocks_record_text_probe():
    """Verify that 'Record 12345 scored 20' is blocked (P1-06 Round 5)."""
    leaky_nb = {
        "cells": [
            {
                "cell_type": "code",
                "outputs": [
                    {
                        "name": "stdout",
                        "text": "Record 12345 scored 20 during assessment."
                    }
                ]
            }
        ]
    }
    with pytest.raises(PrivacyViolationError) as exc_info:
        PrivacyGuard.validate_notebook_outputs(leaky_nb)
    assert "12345" not in str(exc_info.value)


def test_privacy_guard_blocks_svg_record_text_probe():
    """Verify that SVG '<text>Record 12345 score 20</text>' is blocked (P1-06 Round 5)."""
    leaky_nb = {
        "cells": [
            {
                "cell_type": "code",
                "outputs": [
                    {
                        "data": {
                            "image/svg+xml": "<svg><text>Record 12345 score 20</text></svg>"
                        }
                    }
                ]
            }
        ]
    }
    with pytest.raises(PrivacyViolationError) as exc_info:
        PrivacyGuard.validate_notebook_outputs(leaky_nb)
    assert "12345" not in str(exc_info.value)


def test_privacy_guard_blocks_html_id_with_selection_pending():
    """Verify that HTML table row with ID and 'Selection Pending' is blocked (P1-06 Round 5)."""
    leaky_nb = {
        "cells": [
            {
                "cell_type": "code",
                "outputs": [
                    {
                        "data": {
                            "text/html": "<table><tr><td>12345</td><td>Selection Pending</td></tr></table>"
                        }
                    }
                ]
            }
        ]
    }
    with pytest.raises(PrivacyViolationError) as exc_info:
        PrivacyGuard.validate_notebook_outputs(leaky_nb)
    assert "12345" not in str(exc_info.value)


def test_privacy_guard_blocks_case_text_probe():
    """Verify that plain text 'Case 12345 scored 20' is blocked (P1-06 Round 6)."""
    leaky_nb = {
        "cells": [
            {
                "cell_type": "code",
                "outputs": [
                    {
                        "name": "stdout",
                        "text": "Case 12345 scored 20 on examination."
                    }
                ]
            }
        ]
    }
    with pytest.raises(PrivacyViolationError) as exc_info:
        PrivacyGuard.validate_notebook_outputs(leaky_nb)
    assert "12345" not in str(exc_info.value)
    assert "[REDACTED_ID]" in str(exc_info.value)


def test_privacy_guard_blocks_svg_case_probe():
    """Verify that SVG '<text>Case 12345 score 20</text>' is blocked (P1-06 Round 6)."""
    leaky_nb = {
        "cells": [
            {
                "cell_type": "code",
                "outputs": [
                    {
                        "data": {
                            "image/svg+xml": "<svg><text>Case 12345 score 20</text></svg>"
                        }
                    }
                ]
            }
        ]
    }
    with pytest.raises(PrivacyViolationError) as exc_info:
        PrivacyGuard.validate_notebook_outputs(leaky_nb)
    assert "12345" not in str(exc_info.value)
    assert "[REDACTED_ID]" in str(exc_info.value)


def test_privacy_guard_blocks_html_domain_collision():
    """Verify that HTML '12345 / MOTOR / 20' is blocked despite domain keyword (P1-06 Round 6)."""
    leaky_nb = {
        "cells": [
            {
                "cell_type": "code",
                "outputs": [
                    {
                        "data": {
                            "text/html": "<table><tr><td>12345</td><td>MOTOR</td><td>20</td></tr></table>"
                        }
                    }
                ]
            }
        ]
    }
    with pytest.raises(PrivacyViolationError) as exc_info:
        PrivacyGuard.validate_notebook_outputs(leaky_nb)
    assert "12345" not in str(exc_info.value)
    assert "[REDACTED" in str(exc_info.value)


def test_privacy_guard_blocks_html_schema_keyword_collision():
    """Verify that HTML '12345 / unverified' is blocked despite schema keyword (P1-06 Round 6)."""
    leaky_nb = {
        "cells": [
            {
                "cell_type": "code",
                "outputs": [
                    {
                        "data": {
                            "text/html": "<table><tr><td>12345</td><td>unverified</td></tr></table>"
                        }
                    }
                ]
            }
        ]
    }
    with pytest.raises(PrivacyViolationError) as exc_info:
        PrivacyGuard.validate_notebook_outputs(leaky_nb)
    assert "12345" not in str(exc_info.value)
    assert "[REDACTED" in str(exc_info.value)


def test_privacy_guard_blocks_html_manifest_column_collision():
    """Verify that placing ID in File Name column of manifest table is blocked (P1-06 Round 6)."""
    leaky_nb = {
        "cells": [
            {
                "cell_type": "code",
                "outputs": [
                    {
                        "data": {
                            "text/html": (
                                "<table><thead><tr><th>Domain Folder</th><th>File Name</th><th>Format</th></tr></thead>"
                                "<tbody><tr><td>MOTOR</td><td>12345</td><td>CSV</td></tr></tbody></table>"
                            )
                        }
                    }
                ]
            }
        ]
    }
    with pytest.raises(PrivacyViolationError) as exc_info:
        PrivacyGuard.validate_notebook_outputs(leaky_nb)
    assert "12345" not in str(exc_info.value)
    assert "[REDACTED_ID]" in str(exc_info.value)


def test_privacy_guard_blocks_html_fake_schema_table():
    """Verify that arbitrary unapproved table with ID and domain is blocked (P1-06 Round 6)."""
    leaky_nb = {
        "cells": [
            {
                "cell_type": "code",
                "outputs": [
                    {
                        "data": {
                            "text/html": (
                                "<table><thead><tr><th>Domain</th><th>Participant</th><th>Score</th></tr></thead>"
                                "<tbody><tr><td>MOTOR</td><td>12345</td><td>25.0</td></tr></tbody></table>"
                            )
                        }
                    }
                ]
            }
        ]
    }
    with pytest.raises(PrivacyViolationError) as exc_info:
        PrivacyGuard.validate_notebook_outputs(leaky_nb)
    assert "12345" not in str(exc_info.value)
    assert "[REDACTED" in str(exc_info.value)


@pytest.mark.parametrize("stream_msg", [
    "Exported PATNO_12345.csv",
    "Exported patno_12345.csv",
    "Exported PATNO_P12345.csv",
    "Exported patno-p12345.csv",
    "Exported patno#12345.csv",
    "Exported patno:12345.csv",
    "Exported patno=12345.csv",
    "Exported SUBJID_98765.csv",
    "Exported participant_54321.csv",
])
def test_privacy_guard_blocks_stream_text_patno_filename_probes(stream_msg: str):
    """Verify stream text with labeled identifier in filename is blocked (P1-06 Round 7)."""
    leaky_nb = {
        "cells": [
            {
                "cell_type": "code",
                "outputs": [
                    {
                        "name": "stdout",
                        "text": stream_msg,
                    }
                ]
            }
        ]
    }
    with pytest.raises(PrivacyViolationError) as exc_info:
        PrivacyGuard.validate_notebook_outputs(leaky_nb)
    # Check that raw numeric sequence is not leaked in exception string
    assert "12345" not in str(exc_info.value)
    assert "98765" not in str(exc_info.value)
    assert "54321" not in str(exc_info.value)
    assert "[REDACTED" in str(exc_info.value)


@pytest.mark.parametrize("svg_text", [
    "<svg><text>PATNO_12345</text></svg>",
    "<svg><text>patno_12345</text></svg>",
    "<svg><text>PATNO_P12345</text></svg>",
    "<svg><text>patno-p12345</text></svg>",
    "<svg><text>subjid_98765</text></svg>",
    "<svg><text>case_2025</text></svg>",
])
def test_privacy_guard_blocks_svg_patno_probes(svg_text: str):
    """Verify SVG text with labeled identifier is blocked (P1-06 Round 7)."""
    leaky_nb = {
        "cells": [
            {
                "cell_type": "code",
                "outputs": [
                    {
                        "data": {
                            "image/svg+xml": svg_text,
                        }
                    }
                ]
            }
        ]
    }
    with pytest.raises(PrivacyViolationError) as exc_info:
        PrivacyGuard.validate_notebook_outputs(leaky_nb)
    assert "12345" not in str(exc_info.value)
    assert "98765" not in str(exc_info.value)
    assert "2025" not in str(exc_info.value)
    assert "[REDACTED" in str(exc_info.value)


@pytest.mark.parametrize("json_payload", [
    '{"file_name": "PATNO_12345.csv"}',
    '{"file_name": "patno_12345.csv"}',
    '{"file_name": "PATNO_P12345.csv"}',
    '{"file_name": "patno-p12345.csv"}',
    '{"subject_id": "P-12345"}',
    '{"case_id": "case_2025"}',
])
def test_privacy_guard_blocks_json_patno_filename_probes(json_payload: str):
    """Verify structured JSON with labeled identifier is blocked (P1-06 Round 7)."""
    leaky_nb = {
        "cells": [
            {
                "cell_type": "code",
                "outputs": [
                    {
                        "data": {
                            "application/json": json_payload,
                        }
                    }
                ]
            }
        ]
    }
    with pytest.raises(PrivacyViolationError) as exc_info:
        PrivacyGuard.validate_notebook_outputs(leaky_nb)
    assert "12345" not in str(exc_info.value)
    assert "2025" not in str(exc_info.value)
    assert "[REDACTED" in str(exc_info.value)


@pytest.mark.parametrize("file_name_val", [
    "PATNO_12345.csv",
    "patno_12345.csv",
    "PATNO_P12345.csv",
    "patno-p12345.csv",
    "subjid_98765.csv",
    "case_2025.csv",
])
def test_privacy_guard_blocks_html_manifest_patno_filename_probes(file_name_val: str):
    """Verify approved manifest table containing labeled ID in File Name is blocked (P1-06 Round 7)."""
    table_html = (
        "<table><thead><tr><th>Domain Folder</th><th>File Name</th><th>Format</th></tr></thead>"
        f"<tbody><tr><td>MOTOR</td><td>{file_name_val}</td><td>Tabular CSV</td></tr></tbody></table>"
    )
    leaky_nb = {
        "cells": [
            {
                "cell_type": "code",
                "outputs": [
                    {
                        "data": {
                            "text/html": table_html,
                        }
                    }
                ]
            }
        ]
    }
    with pytest.raises(PrivacyViolationError) as exc_info:
        PrivacyGuard.validate_notebook_outputs(leaky_nb)
    assert "12345" not in str(exc_info.value)
    assert "98765" not in str(exc_info.value)
    assert "2025" not in str(exc_info.value)
    assert "[REDACTED" in str(exc_info.value)


@pytest.mark.parametrize("case_probe", [
    "Case 2025 scored 20",
    "case 2025 scored 20",
    "Case P2025 scored 20",
    "case_2025 scored 20",
    "case-2025 scored 20",
    "case:2025 scored 20",
    "2025 scored 20 on examination",
])
def test_privacy_guard_blocks_case_year_and_probe_variants(case_probe: str):
    """Verify Case 2025 probes and bare year-like participant values are blocked (P1-06 Round 7)."""
    leaky_nb = {
        "cells": [
            {
                "cell_type": "code",
                "outputs": [
                    {
                        "name": "stdout",
                        "text": case_probe,
                    }
                ]
            }
        ]
    }
    with pytest.raises(PrivacyViolationError) as exc_info:
        PrivacyGuard.validate_notebook_outputs(leaky_nb)
    assert "2025" not in str(exc_info.value)
    assert "[REDACTED" in str(exc_info.value)


def test_privacy_guard_allows_typed_date_fields_and_safe_years():
    """Verify that typed date fields and full ISO/calendar dates remain approved."""
    safe_report = {
        "audit_year": 2026,
        "release_date": "2026-11-12",
        "baseline_year": 2010,
        "cohort_year": 2020,
        "row_count": 20408,
    }
    scrubbed = PrivacyGuard.scrub_report_dict(safe_report)
    assert scrubbed["audit_year"] == 2026
    assert scrubbed["baseline_year"] == 2010

    safe_nb = {
        "cells": [
            {
                "cell_type": "code",
                "outputs": [
                    {
                        "name": "stdout",
                        "text": "Audit completed on 2026-11-12T04:45:21Z. Total rows: 20408. Year: 2026.",
                    }
                ]
            }
        ]
    }
    # Should pass without raising
    PrivacyGuard.validate_notebook_outputs(safe_nb)


@pytest.mark.parametrize("probe", [
    "Exported PID_12345.csv",
    "Exported pid_12345.csv",
    "Exported ID_12345.csv",
    "Exported id_12345.csv",
    "Exported 1234567.csv",
    "Exported 12345.csv",
    "Exported P1234567.csv",
    "Exported p-1234567.csv",
    "Exported p_1234567.csv",
])
def test_privacy_guard_blocks_round8_stream_text_probes(probe: str):
    """Verify stream text with generic PID/ID or seven-digit token is blocked (P1-06 Round 8)."""
    leaky_nb = {
        "cells": [
            {
                "cell_type": "code",
                "outputs": [
                    {
                        "name": "stdout",
                        "text": probe,
                    }
                ]
            }
        ]
    }
    with pytest.raises(PrivacyViolationError) as exc_info:
        PrivacyGuard.validate_notebook_outputs(leaky_nb)
    assert "12345" not in str(exc_info.value)
    assert "1234567" not in str(exc_info.value)
    assert "[REDACTED" in str(exc_info.value)


@pytest.mark.parametrize("svg_text", [
    "<svg><text>PID_12345</text></svg>",
    "<svg><text>pid_12345</text></svg>",
    "<svg><text>ID_12345</text></svg>",
    "<svg><text>id_12345</text></svg>",
    "<svg><text>1234567</text></svg>",
    "<svg><text>P1234567</text></svg>",
])
def test_privacy_guard_blocks_round8_svg_probes(svg_text: str):
    """Verify SVG text with generic PID/ID or seven-digit token is blocked (P1-06 Round 8)."""
    leaky_nb = {
        "cells": [
            {
                "cell_type": "code",
                "outputs": [
                    {
                        "data": {
                            "image/svg+xml": svg_text,
                        }
                    }
                ]
            }
        ]
    }
    with pytest.raises(PrivacyViolationError) as exc_info:
        PrivacyGuard.validate_notebook_outputs(leaky_nb)
    assert "12345" not in str(exc_info.value)
    assert "1234567" not in str(exc_info.value)
    assert "[REDACTED" in str(exc_info.value)


@pytest.mark.parametrize("json_payload", [
    '{"id": "ID_12345.csv"}',
    '{"file_name": "PID_12345.csv"}',
    '{"file_name": "pid_12345.csv"}',
    '{"outer": {"nested": {"file_name": "1234567.csv"}}}',
    '{"patient": {"record_id": "P1234567.csv"}}',
    '{"study": {"id": "p-1234567"}}',
])
def test_privacy_guard_blocks_round8_nested_json_probes(json_payload: str):
    """Verify nested JSON with generic PID/ID or seven-digit token is blocked (P1-06 Round 8)."""
    leaky_nb = {
        "cells": [
            {
                "cell_type": "code",
                "outputs": [
                    {
                        "data": {
                            "application/json": json_payload,
                        }
                    }
                ]
            }
        ]
    }
    with pytest.raises(PrivacyViolationError) as exc_info:
        PrivacyGuard.validate_notebook_outputs(leaky_nb)
    assert "12345" not in str(exc_info.value)
    assert "1234567" not in str(exc_info.value)
    assert "[REDACTED" in str(exc_info.value)


@pytest.mark.parametrize("file_name_val", [
    "PID_12345.csv",
    "pid_12345.csv",
    "ID_12345.csv",
    "id_12345.csv",
    "1234567.csv",
    "P1234567.csv",
    "p-1234567.csv",
])
def test_privacy_guard_blocks_round8_html_manifest_probes(file_name_val: str):
    """Verify HTML manifest table with generic PID/ID or seven-digit token is blocked (P1-06 Round 8)."""
    table_html = (
        "<table><thead><tr><th>Domain Folder</th><th>File Name</th><th>Format</th></tr></thead>"
        f"<tbody><tr><td>MOTOR</td><td>{file_name_val}</td><td>Tabular CSV</td></tr></tbody></table>"
    )
    leaky_nb = {
        "cells": [
            {
                "cell_type": "code",
                "outputs": [
                    {
                        "data": {
                            "text/html": table_html,
                        }
                    }
                ]
            }
        ]
    }
    with pytest.raises(PrivacyViolationError) as exc_info:
        PrivacyGuard.validate_notebook_outputs(leaky_nb)
    assert "12345" not in str(exc_info.value)
    assert "1234567" not in str(exc_info.value)
    assert "[REDACTED" in str(exc_info.value)


def test_privacy_guard_allows_round8_safe_inventory_filenames():
    """Verify that known safe inventory filenames and approved metadata pass without false positive."""
    safe_filenames = [
        "Dopamine_Imaging_09Nov2026.csv",
        "PPMI_Project_9001_20250624_09Nov2026.csv",
        "NX_PI-2620_Tau_Imaging_Substudy_Imaging_09Nov2026.csv",
        "Tau_Substudy_MK-6240_PET_Imaging_09Nov2026.csv",
        "PPMI_Methods_rs-fMRI_Data_FINAL_2019_12_04.docx",
    ]
    rows_html = "".join([
        f"<tr><td>DATSCAN</td><td>{fn}</td><td>Tabular CSV</td><td>123.4</td><td>1500.0</td></tr>"
        for fn in safe_filenames
    ])
    manifest_html = (
        "<table><thead><tr><th>Domain Folder</th><th>File Name</th><th>Format</th>"
        "<th>Size (KB)</th><th>Logical Rows</th></tr></thead>"
        f"<tbody>{rows_html}</tbody></table>"
    )
    safe_nb = {
        "cells": [
            {
                "cell_type": "code",
                "outputs": [
                    {
                        "data": {
                            "text/html": manifest_html,
                        }
                    },
                    {
                        "name": "stdout",
                        "text": (
                            "Loaded 177 physical source files. Total records: 1748882. "
                            "Genomic coordinate: chr4:950422:A:C_C_TMEM175_rs34884217. "
                            "Hash: 8f3b2c1a4e5d6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a."
                        )
                    }
                ]
            }
        ]
    }
    # Must pass without raising
    PrivacyGuard.validate_notebook_outputs(safe_nb)


ROUND9_CONCATENATED_PROBES = [
    # Six exact matrix failure probes from Codex Round 9 review:
    "RID1234",
    "RID1234567",
    "RIDP12345",
    "SUBJ1234",
    "SUBJ1234567",
    "SUBJP12345",
    # 5-digit standard variants:
    "RID12345",
    "SUBJ12345",
    # Lowercase variants:
    "rid1234",
    "rid12345",
    "rid1234567",
    "ridp12345",
    "subj1234",
    "subj12345",
    "subj1234567",
    "subjp12345",
    # Unlisted alphabetic prefixes (verifying context-independent architecture, not label enumeration):
    "UNLISTED1234",
    "XYZ12345",
    "xyz12345",
    "XYZP12345",
    "FOO1234567",
    "ANYPREFIX12345",
]


@pytest.mark.parametrize("probe", ROUND9_CONCATENATED_PROBES)
def test_privacy_guard_blocks_round9_concatenated_alias_stream_text(probe: str):
    """Verify stream text with concatenated research/subject alias is blocked (P1-06 Round 9)."""
    leaky_nb = {
        "cells": [
            {
                "cell_type": "code",
                "outputs": [
                    {
                        "name": "stdout",
                        "text": f"Exported {probe}.csv to local directory.",
                    }
                ]
            }
        ]
    }
    with pytest.raises(PrivacyViolationError) as exc_info:
        PrivacyGuard.validate_notebook_outputs(leaky_nb)
    assert "1234" not in str(exc_info.value)
    assert "[REDACTED" in str(exc_info.value)


@pytest.mark.parametrize("probe", ROUND9_CONCATENATED_PROBES)
def test_privacy_guard_blocks_round9_concatenated_alias_svg(probe: str):
    """Verify SVG text with concatenated research/subject alias is blocked (P1-06 Round 9)."""
    leaky_nb = {
        "cells": [
            {
                "cell_type": "code",
                "outputs": [
                    {
                        "data": {
                            "image/svg+xml": f"<svg><text>{probe}</text></svg>",
                        }
                    }
                ]
            }
        ]
    }
    with pytest.raises(PrivacyViolationError) as exc_info:
        PrivacyGuard.validate_notebook_outputs(leaky_nb)
    assert "1234" not in str(exc_info.value)
    assert "[REDACTED" in str(exc_info.value)


@pytest.mark.parametrize("probe", [
    "RID1234",
    "SUBJ1234567",
    "RIDP12345",
    "SUBJP12345",
    "rid12345",
    "UNLISTED1234",
    "XYZ12345",
])
def test_privacy_guard_blocks_round9_concatenated_alias_markdown(probe: str):
    """Verify Markdown cells with concatenated research/subject alias are blocked (P1-06 Round 9)."""
    leaky_nb = {
        "cells": [
            {
                "cell_type": "markdown",
                "source": f"### Participant Assessment\nRecord for participant {probe} processed.",
            }
        ]
    }
    with pytest.raises(PrivacyViolationError) as exc_info:
        PrivacyGuard.validate_notebook_outputs(leaky_nb)
    assert "1234" not in str(exc_info.value)
    assert "[REDACTED" in str(exc_info.value)


@pytest.mark.parametrize("probe", [
    "RID1234",
    "SUBJ12345",
    "RIDP12345",
    "SUBJP12345",
    "UNLISTED1234",
    "FOO1234567",
])
def test_privacy_guard_blocks_round9_concatenated_alias_xml(probe: str):
    """Verify XML MIME data with concatenated research/subject alias is blocked (P1-06 Round 9)."""
    leaky_nb = {
        "cells": [
            {
                "cell_type": "code",
                "outputs": [
                    {
                        "data": {
                            "application/xml": f"<subject><alias>{probe}</alias></subject>",
                        }
                    }
                ]
            }
        ]
    }
    with pytest.raises(PrivacyViolationError) as exc_info:
        PrivacyGuard.validate_notebook_outputs(leaky_nb)
    assert "1234" not in str(exc_info.value)
    assert "[REDACTED" in str(exc_info.value)


@pytest.mark.parametrize("probe", [
    "RID1234",
    "RID1234567",
    "RIDP12345",
    "SUBJ1234",
    "SUBJ1234567",
    "SUBJP12345",
    "rid12345",
    "UNLISTED1234",
    "XYZ12345",
    "XYZP12345",
])
def test_privacy_guard_blocks_round9_concatenated_alias_nested_json(probe: str):
    """Verify nested JSON with concatenated research/subject alias is blocked (P1-06 Round 9)."""
    import json
    payload = json.dumps({"outer": {"nested": {"file_name": f"{probe}.csv"}}})
    leaky_nb = {
        "cells": [
            {
                "cell_type": "code",
                "outputs": [
                    {
                        "data": {
                            "application/json": payload,
                        }
                    }
                ]
            }
        ]
    }
    with pytest.raises(PrivacyViolationError) as exc_info:
        PrivacyGuard.validate_notebook_outputs(leaky_nb)
    assert "1234" not in str(exc_info.value)
    assert "[REDACTED" in str(exc_info.value)


@pytest.mark.parametrize("probe", [
    "RID1234",
    "SUBJ12345",
    "RIDP12345",
    "UNLISTED1234",
])
def test_privacy_guard_blocks_round9_concatenated_alias_nested_list(probe: str):
    """Verify nested list structures with concatenated alias are blocked (P1-06 Round 9)."""
    leaky_report = {
        "dataset_summary": {
            "participant_list": [["clean_entry", probe]],
        }
    }
    with pytest.raises(PrivacyViolationError) as exc_info:
        PrivacyGuard.assert_no_participant_records(leaky_report)
    assert "1234" not in str(exc_info.value)
    assert "[REDACTED" in str(exc_info.value)


@pytest.mark.parametrize("probe", [
    "RID1234.csv",
    "RID1234567.csv",
    "RIDP12345.csv",
    "SUBJ1234.csv",
    "SUBJ1234567.csv",
    "SUBJP12345.csv",
    "rid12345.csv",
    "subj12345.csv",
    "UNLISTED1234.csv",
    "XYZ12345.csv",
    "XYZP12345.csv",
])
def test_privacy_guard_blocks_round9_concatenated_alias_html_manifest(probe: str):
    """Verify approved manifest table with concatenated alias is blocked (P1-06 Round 9)."""
    table_html = (
        "<table><thead><tr><th>Domain Folder</th><th>File Name</th><th>Format</th></tr></thead>"
        f"<tbody><tr><td>MOTOR</td><td>{probe}</td><td>Tabular CSV</td></tr></tbody></table>"
    )
    leaky_nb = {
        "cells": [
            {
                "cell_type": "code",
                "outputs": [
                    {
                        "data": {
                            "text/html": table_html,
                        }
                    }
                ]
            }
        ]
    }
    with pytest.raises(PrivacyViolationError) as exc_info:
        PrivacyGuard.validate_notebook_outputs(leaky_nb)
    assert "1234" not in str(exc_info.value)
    assert "[REDACTED" in str(exc_info.value)


def test_privacy_guard_allows_round9_safe_assay_genomic_semester():
    """Verify that safe assay, genomic, tracer, kernel, semester, and dimension patterns pass."""
    safe_nb = {
        "cells": [
            {
                "cell_type": "code",
                "outputs": [
                    {
                        "name": "stdout",
                        "text": (
                            "Repository path: F:\\Lums courses\\FALL2026\\SPROJ\\ppmi\n"
                            "Kernel process: ipykernel_17828\\temp.py\n"
                            "Tracer: NX_PI-2620, MK-6240, MNI1008, Project_9001\n"
                            "Assay header: C2N_AB4240\n"
                            "Genomic SNP: chr2:134782397:C:T_C_ACMSD/TMEM163_rs6430538\n"
                            "Genomic coordinate: chr16:31110472:G:A_A_ZNF646/KAT8/BCKDK_rs14235\n"
                            "Dimensions: 20408 x 215\n"
                            "Total records: 1748882"
                        )
                    }
                ]
            }
        ]
    }
    # Must pass without raising
    PrivacyGuard.validate_notebook_outputs(safe_nb)

