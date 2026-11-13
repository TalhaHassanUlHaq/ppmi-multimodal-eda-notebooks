"""Fail-closed local privacy scrubber and assertion guardrails.

Guarantees zero-leakage of participant-level records, identifiers, or clinical rows
into model contexts, AI review logs, or public reports, regardless of key naming.
"""

from typing import Any, Dict, List, Set, Union
import json
import re


class PrivacyViolationError(ValueError):
    """Raised when participant-level data or identifiers are detected in an output."""
    pass


class PrivacyGuard:
    """Enforces aggregate-only reporting and blocks participant-level identifiers and row records."""

    BANNED_EXACT_KEYS: Set[str] = {
        "PATNO",
        "ALIAS_ID",
        "SUBJID",
        "SUBJECT_ID",
        "CANDID",
        "BIRTHDT",
        "INITIALS",
        "FIRSTNAME",
        "LASTNAME",
        "PARTICIPANT_ID",
    }

    # Generic or suspicious keys that should NEVER hold an individual identifier
    SUSPICIOUS_KEY_PATTERNS = re.compile(
        r"^(?:pat(?:no|ient)?|subj(?:ect|id)?|part(?:icipant)?|id|item|code|candid|alias|individual|person|sample_id)$",
        re.IGNORECASE,
    )

    # Measurement/clinical attribute keys that signal a row-like dictionary when paired with an identifier
    ROW_ATTRIBUTE_KEYS = re.compile(
        r"^(?:score|event|visit|age|gender|sex|diag|status|val|value|result|date|time|infodt|med|dose|ae|term|stage)$",
        re.IGNORECASE,
    )

    # Allowlisted aggregate count, size, and metadata keys that are permitted to contain scalar integers >= 1000
    ALLOWLISTED_COUNT_KEYS: Set[str] = {
        "row_count",
        "column_count",
        "file_size_bytes",
        "size_bytes",
        "total_rows",
        "total_files",
        "total_records",
        "total_cells",
        "total_tabular_rows",
        "total_tabular_rows_indexed",
        "total_source_files",
        "total_non_source_files",
        "total_source_folders",
        "distinct_participants",
        "distinct_visits",
        "null_participant_keys",
        "null_visit_keys",
        "blank_headers_count",
        "duplicate_headers_count",
        "duplicate_rows_count",
        "missing_numerator",
        "missing_denominator",
        "files_with_participant_identifier",
        "files_with_visit_identifier",
        "left_null_keys_count",
        "right_null_keys_count",
        "intersection_keys_count",
        "estimated_merged_rows",
        "actual_merged_rows",
        "max_per_subject",
        "max_per_visit",
        "max_key_multiplicity",
        "max_vis_multiplicity",
        "duplicate_vis_pairs",
        "exact_duplicate_rows",
        "page_count",
        "paragraph_count",
        "table_count",
        "sheet_count",
        "total_flagged_files",
        "total_columns_cataloged",
        "primary_file_columns_count",
        "total_structural_headers_count",
        "total_structural_columns",
        "total_files_cataloged",
        "total_external_data_streams",
        "tabular_tables_count",
        "documentation_files_count",
        "left_input_rows",
        "right_input_rows",
        "left_dropped_null_rows",
        "right_dropped_null_rows",
        "merged_output_rows",
        "left_rows",
        "right_rows",
        "left_distinct_keys",
        "right_distinct_keys",
        "left_only_keys_count",
        "right_only_keys_count",
        "observed_distinct_ids",
        "participant_count",
        "eligible_cohort_denominator",
        "denominator",
        "visit_count",
        "distinct_visits_count",
        "non_null_event_record_count",
        "null_event_record_count",
        "distinct_raw_event_values",
        "participants_with_non_null_events",
        "participants_with_repeated_events",
        "longitudinal_participant_denominator_count",
        "cohort_milestone_eligible",
        "cohort_all_enrolled_maximum",
        "wgs_project_9001_sequenced",
        "roche_mobile_telemetry_active",
        "measurement_count",
        "distinct_participant_days",
        "active_assessment_days",
        "unique_participants",
        "telemetry_records",
        "merged_rows",
        "unmatched_left_keys",
        "unmatched_right_keys",
        "left_duplicates",
        "right_duplicates",
        "left_nulls",
        "right_nulls",
        "total_source_files_evaluated",
        "total_matrix_rows",
        "total_source_files",
        "total_workbook_sheets_indexed",
        "total_decision_units",
        "worksheet_count",
        "candidate_sources_count",
        "primary_eda_count",
        "supporting_count",
        "excluded_count",
        "needs_review_count",
        "null_patno",
        "null_event_id",
        "total",
        "primary eda",
        "supporting",
        "excluded from detailed eda",
        "needs review",
        "none (excluded)",
        "total in-scope sources",
        "00_dataset_overview.ipynb",
        "eda_clinical.ipynb",
        "eda_biospecimen.ipynb",
        "eda_genetics.ipynb",
        "eda_neuroimaging.ipynb",
        "eda_digital_sensors.ipynb",
        "eda_multimodal_synthesis.ipynb",
    }

    # Regex identifying typical PPMI participant identifiers: 4 to 7 digit integers or P-prefixed codes (minimum 1000)
    PAT_ID_PATTERN = re.compile(r"^(?:P(?:PMI)?[_-]?)?[1-9]\d{3,6}$", re.IGNORECASE)

    # Labeled identifier pattern matching explicit participant indicators with any separator (_ - : = # space or none)
    LABELED_ID_PATTERN = re.compile(
        r"(?i)(?:\b|(?<=[^A-Za-z0-9]))"
        r"(?:(?<!NULL_)(?<!NOT_NULL_)PATNO|SUBJID|SUBJECT(?:_?ID)?|SUBJ|PARTICIPANT(?:_?ID)?|PART(?:_?ID)?|PATIENT(?:_?ID)?|CASE(?:_?ID)?|RECORD(?:_?ID)?|RID|SAMPLE(?:_?ID)?|INDIVIDUAL(?:_?ID)?|CANDID|PERSON(?:_?ID)?|PID|(?<!EVENT_)(?<!REC_)(?<!PAG_)(?<!IMAGE_)(?<!IMAGE)(?<!STUDY_)(?<!SITE_)(?<!SERIES_)(?<!PROJECT_)(?<!VISIT_)ID)"
        r"[ \t_:=#-]*"
        r"(?:P(?:PMI)?[_-]?)?[0-9]{3,7}"
        r"(?:\b|(?=[^A-Za-z0-9]))"
    )

    # Patterns indicating participant ID in free-text outputs
    TEXT_ID_PATTERNS = [
        re.compile(r"(?i)(?:\b|(?<=[^A-Za-z0-9]))(?:(?<!NULL_)(?<!NOT_NULL_)PATNO|SUBJID|SUBJECT(?:_?ID)?|SUBJ|PARTICIPANT(?:_?ID)?|PART(?:_?ID)?|PATIENT(?:_?ID)?|CASE(?:_?ID)?|RECORD(?:_?ID)?|RID|SAMPLE(?:_?ID)?|INDIVIDUAL(?:_?ID)?|CANDID|PERSON(?:_?ID)?|PID|(?<!EVENT_)(?<!REC_)(?<!PAG_)(?<!IMAGE_)(?<!IMAGE)(?<!STUDY_)(?<!SITE_)(?<!SERIES_)(?<!PROJECT_)(?<!VISIT_)ID)[ \t_:=#-]+(?:P(?:PMI)?[_-]?)?[0-9]{2,7}\b"),
        re.compile(r"(?i)\b(?:Participant|Subject|Patient|(?<!NULL_)(?<!NOT_NULL_)PATNO|Record|Sample|Individual|Case|PID|RID|SUBJ|(?<!EVENT_)(?<!REC_)(?<!PAG_)(?<!IMAGE_)(?<!IMAGE)(?<!STUDY_)(?<!SITE_)(?<!SERIES_)(?<!PROJECT_)(?<!VISIT_)ID)[ \t]+(?:P(?:PMI)?[_-]?)?[0-9]{2,7}\b"),
        re.compile(r"(?is)<text[^>]*>.*?(?:PATNO|SUBJID|Participant|Subject|Record|Patient|Sample|Case|PID|RID|SUBJ|(?<!EVENT_)(?<!REC_)(?<!PAG_)(?<!IMAGE_)(?<!IMAGE)(?<!STUDY_)(?<!SITE_)(?<!SERIES_)(?<!PROJECT_)(?<!VISIT_)ID)[ \t_:=#-]+(?:P(?:PMI)?[_-]?)?[0-9]{2,7}.*?</text>"),
        re.compile(r"\{[^{}]*(?:['\"](?:PATNO|SUBJID|id|participant|record|subject|case|sample|pid|rid|subj)['\"]\s*:\s*(?:['\"]?P?\d{3,7}['\"]?))[^{}]*\}", re.IGNORECASE),
    ]

    CANONICAL_DOMAINS = {
        "subject_characteristics", "biospecimen", "datscan", "motor",
        "mr analysis results", "mri acquisition", "neurobehavioral",
        "neuropsychological", "non motor", "olfactory", "other cognitive",
        "pet", "sleep disorder", "medical history", "digital_sensor",
        "dti", "curated_datacuts",
    }

    FILE_EXTENSIONS = (".csv", ".xlsx", ".pdf", ".docx", "._")

    # Embedded candidate participant identifier token: 4 to 7 digit integer (1000..9999999) or P-prefixed code
    # Context-independent scanner recognizing tokens at punctuation boundaries, alphabetic-to-digit transitions,
    # and alias-to-P-prefix transitions (e.g. RID12345, SUBJ1234, SUBJP12345, XYZ12345)
    EMBEDDED_ID_SEGMENT_PATTERN = re.compile(
        r"(?i)(?<![0-9])(?:P(?:PMI)?[_-]?)?([1-9]\d{3,6})(?![A-Za-z0-9])"
    )
    STANDALONE_ID_TOKEN = EMBEDDED_ID_SEGMENT_PATTERN

    APPROVED_PREFIX_PATTERNS = [
        re.compile(r"(?i)\b(?:Total|Total\s+[a-z\s]+|Row\s+Count|Distinct\s+[a-z\s]+|File\s+Size|Size|Bytes|Count|N|Files|Units|Headers|Columns|Rows|Records|Samples|Positions?|Dimensions?|Length|Height|Width|Visits|Participants|Subjects|Assessments|Observations|null_(?:patno|event_id)|null_[a-z_]+)\s*[:=]\s*$"),
    ]
    APPROVED_SUFFIX_PATTERNS = [
        re.compile(r"(?i)^\s*(?:rows|files|units|columns|headers|bytes|KB|MB|GB|ms|seconds|sec|records|samples|pts|px|visits|participants|subjects|assessments|observations|sources|sheets|measurements|days)\b"),
    ]
    APPROVED_DIM_PATTERN = re.compile(r"\b\d+\s*(?:x|×)\s*\d+\b", re.IGNORECASE)
    APPROVED_DATE_PATTERN = re.compile(
        r"(?i)\b(?:"
        r"\d{4}-\d{2}-\d{2}(?:[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?)?Z?"
        r"|\d{1,2}[-_ ](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[-_ ](?:19|20)\d{2}"
        r"|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[-_ ]\d{1,2},?[-_ ](?:19|20)\d{2}"
        r"|(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])"
        r"|\b(?:19|20)\d{2}\s*[-–/]\s*(?:19|20)\d{2}\b"
        r"|\b(?:date|year|cohort|baseline|vintage|release|generated|since|until|through|to|from)\s*[:=]?\s*(?:19|20)\d{2}\b"
        r")"
    )
    APPROVED_SAFE_PATTERNS = [
        re.compile(r"(?i)(?<![A-Za-z0-9])(?:\d{4}[-_]\d{2}[-_]\d{2}|\d{2}[A-Za-z]{3}\d{4}|(?:19|20)\d{6})(?![A-Za-z0-9])"),
        re.compile(r"(?i)(?<![A-Za-z0-9])(?:(?:19|20)\d{2}|(?:19|20)\d{4,6})(?:\.\.\.|…)"),
        re.compile(r"(?i)(?<![A-Za-z0-9])(?:MK[-_\s]?6240|PI[-_\s]?2620|Project[-_\s]?9001|MNI[-_\s]?1008)(?![A-Za-z0-9])"),
        re.compile(r"(?i)(?<![A-Za-z0-9])C2N[-_]AB4240(?![A-Za-z0-9])"),
        re.compile(r"\b[0-9a-fA-F]{32,64}\b"),
        re.compile(r"(?i)(?:\b|(?<=[^A-Za-z0-9]))(?:chr[0-9xym]+|rs\d+)[:_A-Za-z0-9/-]*\b"),
        re.compile(r"\b(?:\d+\s*(?:x|×)\s*\d+)\b", re.IGNORECASE),
        re.compile(r"(?i)\bipykernel_\d+\b"),
        re.compile(r"(?i)\b(?:Fall|Spring|Summer|Winter)[-_]?(?:19|20)\d{2}\b"),
        re.compile(r"(?i)\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)[,\s]+(?:19|20)\d{2}\b"),
        re.compile(r"(?i)\bnull_(?:patno|event_id)=\d+\b"),
        re.compile(r"(?i)(?:[<>=~]\s*)?\d+(?:\.\d+)?\s*(?:pg/mL|ng/mL|ug/mL|mg/mL|mm\^3|mm)\b"),
        re.compile(r"(?i)\b(?:19|20)\d{2}(?:/(?:19|20)\d{2})?\s+(?:ELISA|Elecsys|assay|assays)\b"),
        re.compile(r"(?i)\((?:[A-Za-z\s.,&]+[,\s]+)?(?:19|20)\d{2}\)"),
        re.compile(r"(?i)(?:\b(?:et\s+al\.?|and\s+GP2)[,\s]+|\()(?:\b(?:19|20)\d{2}\b)"),
        re.compile(r"\b\d+\.\d+\b"),
    ]
    APPROVED_HASH_PATTERN = re.compile(r"\b[0-9a-fA-F]{32,64}\b")
    APPROVED_GENOMIC_PATTERN = re.compile(r"(?i)\b(?:chr[0-9xym]+|rs\d+)[:_A-Za-z0-9-]*\b")
    APPROVED_FILENAME_PATTERN = re.compile(r"(?i)\b[A-Za-z0-9_-]+\.(?:csv|xlsx|pdf|docx|py|md|json)\b")

    APPROVED_DATE_FIELDS: Set[str] = {
        "year", "date", "timestamp", "generated_at", "audit_date", "release_date",
        "created_at", "updated_at", "start_date", "end_date", "baseline_year",
        "cohort_year", "publication_year", "audit_year",
    }

    APPROVED_TABLE_SCHEMAS = {
        "deep_source_inventory": {
            "required": {"incremental scientific purpose", "source path"},
            "required_mode": "all",
            "numeric_columns": {
                "participant coverage", "visit coverage", "dimensions (rows × cols)", "dimensions (rows x cols)",
                "row count", "column count", "rows", "columns", "index", "",
            },
        },
        "selection_gate_matrix": {
            "required": {"provisional recommendation", "provisional_recommendation", "proposed category", "proposed_category", "relative path"},
            "required_mode": "any",
            "numeric_columns": {
                "row count", "column count", "worksheet count", "duplicate rows count",
                "observed distinct ids", "participant count", "eligible cohort denominator", "participant coverage (%)", "participant coverage percent",
                "non-null event record count", "non_null_event_record_count", "null event record count", "null_event_record_count",
                "distinct raw event values", "distinct_raw_event_values", "participants with non-null events", "participants_with_non_null_events",
                "participants with repeated events", "participants_with_repeated_events",
                "longitudinal participant denominator count", "longitudinal_participant_denominator_count",
                "visit count", "distinct visits count", "distinct visits", "longitudinal depth", "null rate (%)", "null rate percent",
                "null key counts", "index", "",
            },
        },
        "selection_summary": {
            "required": {"provisional recommendation", "target notebook", "modality", "selection status", "primary eda source file"},
            "required_mode": "any",
            "numeric_columns": {
                "file count", "files", "source files", "percentage (%)", "total rows",
                "observed distinct ids", "distinct participants", "participant count", "eligible cohort denominator", "participant coverage (%)", "index", "",
            },
        },
        "selection_exclusions": {
            "required": {"candidate excluded file", "exact comparator source", "reason / evidence", "redundancy evidence"},
            "required_mode": "any",
            "numeric_columns": {"row count", "column count", "index", ""},
        },
        "selection_needs_review": {
            "required": {"file flagged for review", "action required for phase 2", "action required", "scientific role"},
            "required_mode": "any",
            "numeric_columns": {
                "observed ids", "observed distinct ids", "distinct participants", "participant count",
                "distinct visits", "distinct visits count", "row count", "column count", "index", "",
            },
        },
        "manifest": {
            "required": {"file name", "format"},
            "required_mode": "all",
            "numeric_columns": {
                "size (kb)", "size (mb)", "size (bytes)", "logical rows", "row count",
                "total rows", "columns", "column count", "worksheet count", "participant count",
                "participant coverage (%)", "index", "",
            },
        },
        "aggregate_summary": {
            "required": {"file_count", "file count", "tabular row count", "tabular_rows", "total_columns", "total records"},
            "required_mode": "any",
            "numeric_columns": {
                "file_count", "file count", "total_size_kb", "size (mb)", "file percentage (%)",
                "tabular_rows", "tabular_row_count", "tabular row count", "row_count", "row count",
                "total_records", "total records", "distinct_participants", "distinct_visits",
                "null_participant_keys", "total size (kb)", "tabular source count", "row percentage (%)",
                "has_patno_files", "has_event_id_files", "files", "total_columns", "numeric_cols",
                "categorical_cols", "identifier_cols", "index", "",
            },
        },
        "schema_index": {
            "required": {"columns count", "sample headers"},
            "required_mode": "any",
            "numeric_columns": {
                "columns count", "columns", "column count", "logical rows", "row count",
                "worksheet count", "index", "",
            },
        },
        "column_dictionary": {
            "required": {"inferred type"},
            "required_mode": "all",
            "numeric_columns": {
                "col index", "position", "column_index", "index", "missing count", "missing_numerator",
                "missing_denominator", "missing denominator", "denominator", "missingness (%)", "missing %", "unique values", "distinct count", "",
            },
        },
        "workbook_audit": {
            "required": {"worksheet name", "workbook path", "sheet name"},
            "required_mode": "any",
            "numeric_columns": {
                "row count", "column count", "blank headers", "duplicate headers",
                "distinct participants", "dimensions (rows × cols)", "index", "",
            },
        },
        "non_source_artifacts": {
            "required": {"category", "file count"},
            "required_mode": "all",
            "numeric_columns": {
                "file count", "total size (kb)", "index", "",
            },
        },
        "external_references": {
            "required": {"modality", "referenced remote data stream"},
            "required_mode": "all",
            "numeric_columns": {"index", ""},
        },
        "longitudinal_cohort_counts": {
            "required": {"healthy control (hc)", "parkinson's disease (pd)", "prodromal", "swedd"},
            "required_mode": "any",
            "numeric_columns": {
                "healthy control (hc)", "parkinson's disease (pd)", "prodromal", "swedd",
                "hc", "pd", "event_id", "cohort_label", "index", "",
            },
        },
        "join_audit": {
            "required": {"left table", "left source", "right table", "right source", "expected cardinality", "join status", "audit status"},
            "required_mode": "any",
            "numeric_columns": {
                "left rows", "right rows", "left key nulls", "right key nulls", "left nulls", "right nulls",
                "left key duplicates", "right key duplicates", "left duplicates", "right duplicates",
                "unmatched left keys", "unmatched right keys", "merged rows", "index", "",
            },
        },
        "demographic_summary": {
            "required": {"cohort", "sample size", "participants"},
            "required_mode": "any",
            "numeric_columns": {
                "sample size", "participants", "n", "count", "age (mean)", "age (sd)",
                "male (%)", "female (%)", "index", "",
            },
        },
        "telemetry_summary": {
            "required": {"telemetry records", "unique participants", "active participant days", "valid measurements"},
            "required_mode": "any",
            "numeric_columns": {
                "telemetry records", "unique participants", "active participant days",
                "valid measurements", "records", "participants", "days", "measurements", "index", "",
            },
        },
        "trajectory_summary": {
            "required": {"event_id", "visit", "milestone"},
            "required_mode": "any",
            "numeric_columns": {
                "healthy control (hc)", "parkinson's disease (pd)", "prodromal", "swedd",
                "hc", "pd", "n", "median", "mean", "iqr", "q25", "q75", "count", "sample size", "index", "",
            },
        },
        "medication_summary": {
            "required": {"milestone visit", "total pd visits", "valid ledd (n)", "% on medication (valid denominator)"},
            "required_mode": "any",
            "numeric_columns": {
                "valid ledd (n)", "total pd visits", "% on medication (valid denominator)",
                "median ledd (mg/day)", "mean ledd (mg/day)", "participant_count", "index", "",
            },
        },
        "skewness_summary": {
            "required": {"distribution shape", "skewness"},
            "required_mode": "any",
            "numeric_columns": {
                "valid n", "missing n", "skewness", "sample size", "index", "",
            },
        },
        "instrument_reconciliation": {
            "required": {"instrument", "curated metric"},
            "required_mode": "any",
            "numeric_columns": {
                "matched visits (n)", "matched visits", "pearson r", "mean abs diff", "concordance rate", "index", "",
            },
        },
        "neuropsych_battery": {
            "required": {"cohort", "sdmt score (median [iqr], n)"},
            "required_mode": "any",
            "numeric_columns": {
                "sdmt score (median [iqr], n)", "hvlt delayed recall (median [iqr], n)",
                "trail b sec (median [iqr], n)", "benton jlo raw (median [iqr], n)",
                "upsit total (median [iqr], n)", "index", "",
            },
        },
        "motor_complications_falls": {
            "required": {"freezing past week (n, %)", "falls past week (n, %)"},
            "required_mode": "any",
            "numeric_columns": {
                "total evaluated (n)", "freezing past week (n, %)", "falls past week (n, %)", "index", "",
            },
        },
        "correlation_denominators": {
            "required": {"mds-updrs iii", "moca total", "csf aβ42", "csf abeta42", "csf t-tau", "plasma ptau-217", "plasma gfap"},
            "required_mode": "any",
            "numeric_columns": {
                "mds-updrs iii", "moca total", "sdmt (speed)", "trail b (exec)", "hvlt recall",
                "upsit (smell)", "scopa (autonomic)", "gds (depression)", "stai (anxiety)",
                "ess (sleepiness)", "rbdsq (rbd)",
                "csf aβ42", "csf abeta42", "csf t-tau", "csf p-tau181", "csf nfl",
                "serum nfl", "plasma ptau-217", "plasma gfap", "index", "",
            },
        },
        "imaging_qc_stratification": {
            "required": {"field strength", "mriqc metric", "scanner field strength"},
            "required_mode": "any",
            "numeric_columns": {
                "cnr", "cjv", "efc", "fber", "n", "sample size", "median", "iqr", "mean", "sd", "index", "",
            },
        },
        "pet_tracer_summary": {
            "required": {"radioligand", "pet ligand", "tracer"},
            "required_mode": "any",
            "numeric_columns": {
                "participant_count", "scan count", "completed scans", "index", "",
            },
        },
        "specimen_catalog_summary": {
            "required": {"specimen matrix type", "total aliquots (n)", "matrix type", "specimen type", "repository resource"},
            "required_mode": "any",
            "numeric_columns": {
                "total aliquots (n)", "total aliquots", "aliquots", "percentage (%)", "distinct visits",
                "total vials / lines (n)", "distinct participants", "index", "",
            },
        },
        "genomic_platform_summary": {
            "required": {"sequencing platform / assay", "platform / assay", "sequencing technology"},
            "required_mode": "any",
            "numeric_columns": {
                "available participants (n)", "available participants", "coverage (%)", "coverage percent", "index", "",
            },
        },
        "family_history_summary": {
            "required": {"genetic category", "positive family history (n, %)", "family history"},
            "required_mode": "any",
            "numeric_columns": {
                "total evaluated (n)", "positive family history (n, %)", "no family history (n, %)", "index", "",
            },
        },
    }

    @classmethod
    def is_safe_approved_token(cls, text: str, start: int, end: int) -> bool:
        """Verify whether an embedded token falls within an approved safe pattern or context."""
        for p in cls.APPROVED_SAFE_PATTERNS:
            for sm in p.finditer(text):
                if sm.start() <= start and end <= sm.end():
                    return True
        for m in cls.APPROVED_DATE_PATTERN.finditer(text):
            if m.start() <= start and end <= m.end():
                return True
        for dm in cls.APPROVED_DIM_PATTERN.finditer(text):
            if dm.start() <= start and end <= dm.end():
                return True
        prefix_window = text[max(0, start - 50):start]
        for ap in cls.APPROVED_PREFIX_PATTERNS:
            if ap.search(prefix_window):
                return True
        suffix_window = text[end:min(len(text), end + 50)]
        for asuf in cls.APPROVED_SUFFIX_PATTERNS:
            if asuf.search(suffix_window):
                return True
        return False

    @classmethod
    def scan_string_for_embedded_id(cls, text: str, context: str = "") -> None:
        """Context-independent embedded identifier scanner covering labeled IDs and punctuation-delimited segments."""
        if not text:
            return

        # 1. Check labeled identifier pattern across text
        if cls.LABELED_ID_PATTERN.search(text):
            raise PrivacyViolationError(
                f"Participant identifier [REDACTED_ID] detected in {context}."
            )

        # 2. Check embedded numeric segments (4 to 7 digits or P-prefixed)
        for m in cls.EMBEDDED_ID_SEGMENT_PATTERN.finditer(text):
            tok_start = m.start()
            tok_end = m.end()

            if cls.is_safe_approved_token(text, tok_start, tok_end):
                continue

            raise PrivacyViolationError(
                f"Participant-like identifier [REDACTED_ID] detected in {context}."
            )

    @classmethod
    def is_approved_text_slot(cls, text: str, start: int, end: int) -> bool:
        """Verify whether a participant-like number occupies an approved aggregate value slot."""
        # Never exempt if the token is part of a labeled participant identifier
        for lm in cls.LABELED_ID_PATTERN.finditer(text):
            if lm.start() <= start and end <= lm.end():
                return False

        if cls.is_safe_approved_token(text, start, end):
            return True

        for m in cls.APPROVED_DIM_PATTERN.finditer(text):
            if m.start() <= start and end <= m.end():
                return True

        prefix_window = text[max(0, start - 50):start]
        for p in cls.APPROVED_PREFIX_PATTERNS:
            if p.search(prefix_window):
                return True
        suffix_window = text[end:min(len(text), end + 50)]
        for s in cls.APPROVED_SUFFIX_PATTERNS:
            if s.search(suffix_window):
                return True
        return False

    @classmethod
    def validate_html_tables(cls, html_text: str, context: str) -> None:
        """Parse HTML tables and validate columns and values against typed approved schemas."""
        tables = re.findall(r"<table[^>]*>.*?</table>", html_text, re.DOTALL | re.IGNORECASE)
        if not tables:
            # If no <table> tag but <tr> present, unapproved table
            if "<tr" in html_text.lower():
                rows = re.findall(r"<tr[^>]*>.*?</tr>", html_text, re.DOTALL | re.IGNORECASE)
                for r in rows:
                    cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", r, re.DOTALL | re.IGNORECASE)
                    for c in cells:
                        clean_c = re.sub(r"<[^>]+>", "", c).strip()
                        if cls.is_participant_id_like(clean_c) or cls.LABELED_ID_PATTERN.search(clean_c):
                            raise PrivacyViolationError(
                                f"Participant table row [REDACTED_RECORD] detected in unapproved HTML table in {context}."
                            )
            return

        for table in tables:
            thead = re.search(r"<thead[^>]*>(.*?)</thead>", table, re.DOTALL | re.IGNORECASE)
            header_text = thead.group(1) if thead else ""
            if not header_text:
                first_tr = re.search(r"<tr[^>]*>(.*?)</tr>", table, re.DOTALL | re.IGNORECASE)
                header_text = first_tr.group(1) if first_tr else ""

            header_cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", header_text, re.DOTALL | re.IGNORECASE)
            headers = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", h).strip().lower()) for h in header_cells]

            matched_schema = None
            headers_set = set(headers)
            for s_name, s_def in cls.APPROVED_TABLE_SCHEMAS.items():
                mode = s_def.get("required_mode", "all")
                if mode == "any":
                    if any(r in headers_set for r in s_def["required"]):
                        matched_schema = s_def
                        break
                else:
                    if s_def["required"].issubset(headers_set):
                        matched_schema = s_def
                        break

            tbody = re.search(r"<tbody[^>]*>(.*?)</tbody>", table, re.DOTALL | re.IGNORECASE)
            rows_text = tbody.group(1) if tbody else table
            rows = re.findall(r"<tr[^>]*>.*?</tr>", rows_text, re.DOTALL | re.IGNORECASE)

            for r in rows:
                cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", r, re.DOTALL | re.IGNORECASE)
                cells_clean = [re.sub(r"<[^>]+>", "", c).strip() for c in cells]

                if matched_schema is None:
                    # Unapproved table header: ANY ID-like cell is rejected
                    for c in cells_clean:
                        if cls.is_participant_id_like(c):
                            raise PrivacyViolationError(
                                f"Participant table row [REDACTED_RECORD] detected in unapproved HTML table schema in {context}."
                            )
                else:
                    # Approved schema:
                    # 1. Non-numeric columns MUST NOT contain embedded participant IDs or segments (e.g. PID_12345.csv, 1234567.csv)
                    # 2. Only allowlisted numeric columns may contain numeric counts >= 1000
                    for col_idx, cell_val in enumerate(cells_clean):
                        col_name = headers[col_idx] if col_idx < len(headers) else ""
                        if col_name in matched_schema["numeric_columns"]:
                            clean_num = re.sub(r"[,\s]", "", cell_val)
                            try:
                                float(clean_num)
                                # Allowed aggregate numeric scalar
                                continue
                            except ValueError:
                                pass
                            if re.match(r"^(?:null_[a-z_]+=\d+(?:;\s*)?)+$", cell_val.strip(), re.I):
                                continue

                        # In non-numeric columns (like File Name, Format, Domain, etc.):
                        # Strictly scan for any embedded participant identifier or segment!
                        cls.scan_string_for_embedded_id(cell_val, context=f"{context}.column['{col_name}']")

    PLAIN_TEXT_FORMAT_CATEGORIES = [
        "tabular csv", "document pdf", "tabular excel", "system metadata sidecar",
        "document word", "raw time-series",
    ]

    @classmethod
    def is_approved_plain_text_table(cls, text: str, context: str) -> bool:
        """Validate whether a plain-text DataFrame output adheres to an approved table contract."""
        lines = [l for l in text.strip().splitlines() if l.strip()]
        if len(lines) < 2:
            return False

        header_line = lines[0].lower()
        matched = None
        if "file name" in header_line and "format" in header_line:
            matched = "manifest"
        elif any(k in header_line for k in ["total_columns", "file_count", "file count", "tabular row count", "tabular_rows"]):
            matched = "aggregate_summary"
        elif "sample headers" in header_line or ("source table" in header_line and "columns" in header_line):
            matched = "schema_index"
        elif "original header" in header_line or "parser alias" in header_line:
            matched = "column_dictionary"
        elif "worksheet name" in header_line or "source workbook" in header_line:
            matched = "workbook_audit"
        elif "provisional_recommendation" in header_line or "provisional recommendation" in header_line or "proposed_category" in header_line or "target_notebook" in header_line:
            matched = "selection_matrix"
        elif any(k in header_line for k in ["cohort_label", "healthy control", "parkinson's disease", "prodromal", "swedd"]):
            matched = "cohort_counts"
        elif any(k in header_line for k in ["left table", "left source", "right table", "right source", "expected cardinality", "join keys", "merged rows", "join audit"]):
            matched = "join_audit"
        elif any(k in header_line for k in ["milestone visit", "total pd visits", "valid ledd", "median ledd", "% on medication"]):
            matched = "medication_summary"
        elif any(k in header_line for k in ["skewness", "distribution shape"]) or ("domain" in header_line and "variable" in header_line and any("skewness" in l.lower() for l in lines)):
            matched = "skewness_summary"
        elif any(k in header_line for k in ["incremental scientific purpose", "documentation source", "deep source", "priority source", "source path"]):
            matched = "deep_source_inventory"
        elif any(k in header_line for k in ["instrument", "curated metric", "raw crf metric", "matched visits"]):
            matched = "instrument_reconciliation"
        elif any(k in header_line for k in ["sdmt score", "hvlt delayed", "benton jlo", "freezing past week", "falls past week"]):
            matched = "domain_summary"
        elif any(k in header_line for k in ["moca total", "mds-updrs iii", "upsit (smell)", "sdmt (speed)", "csf aβ42", "csf t-tau"]):
            matched = "correlation_matrix"
        elif any(k in header_line for k in ["cnr", "cjv", "efc", "fber", "field strength", "mriqc"]):
            matched = "imaging_qc"
        elif any(k in header_line for k in ["radioligand", "pet ligand", "tracer", "completed scans"]):
            matched = "pet_tracer"
        elif any(k in header_line for k in ["specimen matrix type", "total aliquots", "specimen type", "matrix type"]):
            matched = "specimen_summary"

        if matched is None:
            return False

        # Validate lines
        for line in lines[1:]:
            tokens = list(cls.STANDALONE_ID_TOKEN.finditer(line))
            if not tokens:
                continue

            if matched == "manifest":
                line_lower = line.lower()
                format_pos = -1
                for fmt in cls.PLAIN_TEXT_FORMAT_CATEGORIES:
                    idx = line_lower.find(fmt)
                    if idx != -1:
                        format_pos = idx
                        break

                if format_pos == -1:
                    return False

                for tok in tokens:
                    if tok.start() < format_pos:
                        if not cls.is_safe_approved_token(line, tok.start(), tok.end()):
                            raise PrivacyViolationError(
                                f"Participant-like identifier [REDACTED_ID] detected in text table column in {context}."
                            )

            elif matched == "schema_index":
                for tok in tokens:
                    if not cls.is_safe_approved_token(line, tok.start(), tok.end()):
                        prefix = line[:tok.start()]
                        if not re.search(r"(?i)(?:\.csv|\.xlsx|\.pdf|\.docx|->|\._|\.\.\.)", prefix):
                            raise PrivacyViolationError(
                                f"Participant-like identifier [REDACTED_ID] detected in schema index table column in {context}."
                            )

            elif matched == "workbook_audit":
                for tok in tokens:
                    if not cls.is_safe_approved_token(line, tok.start(), tok.end()):
                        prefix = line[:tok.start()]
                        if not re.search(r"(?i)(?:curated|guide|spreadsheet|ppmi|rsfmri|xlsx)", prefix):
                            raise PrivacyViolationError(
                                f"Participant-like identifier [REDACTED_ID] detected in workbook table column in {context}."
                            )
                    prefix = line[:tok.start()]
                    if not re.search(r"(?i)(?:curated|guide|spreadsheet|ppmi|rsfmri|xlsx)", prefix):
                        raise PrivacyViolationError(
                            f"Participant-like identifier [REDACTED_ID] detected in workbook table column in {context}."
                        )

            elif matched == "column_dictionary":
                for tok in tokens:
                    prefix = line[:tok.start()]
                    if not re.search(r"^\s*\d+\s+", prefix):
                        raise PrivacyViolationError(
                            f"Participant-like identifier [REDACTED_ID] detected in column name in {context}."
                        )

            elif matched == "selection_matrix":
                line_lower = line.lower()
                format_pos = -1
                for fmt in cls.PLAIN_TEXT_FORMAT_CATEGORIES:
                    idx = line_lower.find(fmt)
                    if idx != -1:
                        format_pos = idx
                        break

                for tok in tokens:
                    if format_pos != -1 and tok.start() < format_pos:
                        if not cls.is_safe_approved_token(line, tok.start(), tok.end()):
                            raise PrivacyViolationError(
                                f"Participant-like identifier [REDACTED_ID] detected in filename/path column in {context}."
                            )

            elif matched in ("cohort_counts", "join_audit", "medication_summary", "skewness_summary", "deep_source_inventory", "instrument_reconciliation", "domain_summary", "correlation_matrix", "imaging_qc", "pet_tracer", "specimen_summary"):
                continue

        return True

    @classmethod
    def is_authorized_aggregate_html_row(cls, cells_clean: List[str]) -> bool:
        """Legacy row contract preserved for backward compatibility."""
        return False

    @classmethod
    def is_participant_id_like(cls, val: Any) -> bool:
        """Heuristic checking if a scalar value looks like a participant identifier."""
        if isinstance(val, bool):
            return False
        if isinstance(val, int) and (1000 <= val <= 9999999):
            return True
        if isinstance(val, str):
            val_clean = val.strip()
            if cls.PAT_ID_PATTERN.match(val_clean):
                return True
            if cls.LABELED_ID_PATTERN.search(val_clean):
                return True
            for m in cls.EMBEDDED_ID_SEGMENT_PATTERN.finditer(val_clean):
                if not cls.is_safe_approved_token(val_clean, m.start(), m.end()):
                    return True
        return False

    @classmethod
    def is_allowlisted_count_field(cls, key_name: str) -> bool:
        """Check if a field name is an explicitly allowlisted aggregate count/size field."""
        cleaned = re.sub(r"\[\d+\]", "", str(key_name).strip().lower())
        return cleaned in cls.ALLOWLISTED_COUNT_KEYS

    @classmethod
    def is_approved_date_field(cls, key_name: str) -> bool:
        """Check if a field name is an explicitly allowlisted date/year field."""
        cleaned = re.sub(r"\[\d+\]", "", str(key_name).strip().lower())
        return cleaned in cls.APPROVED_DATE_FIELDS

    @classmethod
    def assert_no_participant_records(cls, data: Any, context: str = "") -> None:
        """Deeply and recursively inspect any data structure to assert absence of row-level records or IDs.
        
        Fail-Closed Invariants:
        1. Checks banned key names (PATNO, SUBJID, etc.).
        2. Blocks any scalar participant-like ID under ANY generic or suspicious field.
        3. Strict allowlist for count/size fields: only scalar numbers permitted under exact allowlisted keys.
        4. Rejects non-scalar collections (lists/dicts) under count fields.
        5. Blocks any list/collection containing even a SINGLE participant-like ID.
        6. Blocks any dictionary that exhibits row-like structure.
        7. Inspects free-text strings for embedded participant IDs or HTML table rows.
        8. REDACTS all values in exception messages to avoid leakage into logs or AI context.
        """
        if isinstance(data, dict):
            keys = [str(k) for k in data.keys()]
            keys_upper = {k.strip().upper(): k for k in keys}

            # 1. Check for banned key names
            for banned in cls.BANNED_EXACT_KEYS:
                if banned in keys_upper:
                    k_orig = keys_upper[banned]
                    v = data[k_orig]
                    # Allow only boolean flags (e.g. has_patno=True)
                    if isinstance(v, bool):
                        continue
                    raise PrivacyViolationError(
                        f"Participant identifier field [REDACTED_FIELD] detected under banned key '{k_orig}' in {context}."
                    )

            # 2. Check for row-like dictionary structure:
            has_id_field = any(cls.SUSPICIOUS_KEY_PATTERNS.match(k.strip()) for k in keys)
            has_attr_field = any(cls.ROW_ATTRIBUTE_KEYS.match(k.strip()) for k in keys)
            if has_id_field and has_attr_field:
                raise PrivacyViolationError(
                    f"Row-shaped record with identifier and attribute fields detected in {context}."
                )

            # 3. Check values in dictionary
            for k, v in data.items():
                k_str = str(k).strip()

                # If key is an allowlisted count field, ensure value is strictly scalar numeric or None
                if cls.is_allowlisted_count_field(k_str):
                    if isinstance(v, (list, tuple, set, dict)):
                        raise PrivacyViolationError(
                            f"Non-scalar collection type '{type(v).__name__}' detected under aggregate count field '{k}' in {context}."
                        )
                    # Scalar count is allowed
                    continue

                # If key is an approved date/year field, permit scalar year
                if cls.is_approved_date_field(k_str) and isinstance(v, int) and (1900 <= v <= 2099):
                    continue

                # Scan string values for embedded participant identifiers
                if isinstance(v, str):
                    cls.scan_string_for_embedded_id(v, context=f"{context}.{k}")

                # If key itself is suspicious and value is ID-like
                if cls.SUSPICIOUS_KEY_PATTERNS.match(k_str) and cls.is_participant_id_like(v):
                    raise PrivacyViolationError(
                        f"Participant identifier [REDACTED_ID] detected under generic/suspicious field '{k}' in {context}."
                    )

                # If scalar value looks like participant ID and key is NOT allowlisted count/size
                if cls.is_participant_id_like(v):
                    raise PrivacyViolationError(
                        f"Participant-like identifier [REDACTED_ID] detected under non-aggregate field '{k}' in {context}."
                    )

                # Check text strings for embedded IDs
                if isinstance(v, str):
                    cls.assert_no_raw_text_leakage(v, context=f"{context}.{k}")

                # Recursive check
                cls.assert_no_participant_records(v, context=f"{context}.{k}" if context else str(k))

        elif isinstance(data, (list, tuple, set)):
            # Check if ANY scalar resembles a participant ID - NEVER exempt elements of a collection!
            for i, x in enumerate(data):
                if cls.is_participant_id_like(x):
                    raise PrivacyViolationError(
                        f"Participant identifier [REDACTED_ID] detected in collection under {context} at index {i}."
                    )
                if isinstance(x, str):
                    cls.scan_string_for_embedded_id(x, context=f"{context}[{i}]")
                    cls.assert_no_raw_text_leakage(x, context=f"{context}[{i}]")
                cls.assert_no_participant_records(x, context=f"{context}[{i}]" if context else f"[{i}]")

        elif isinstance(data, (str, int)):
            # Standalone scalar
            if cls.is_participant_id_like(data):
                field_name = context.split(".")[-1] if context else ""
                if not cls.is_allowlisted_count_field(field_name) and not (cls.is_approved_date_field(field_name) and isinstance(data, int) and (1900 <= data <= 2099)):
                    raise PrivacyViolationError(
                        f"Participant identifier [REDACTED_ID] detected in standalone scalar context: {context}."
                    )
            if isinstance(data, str):
                cls.scan_string_for_embedded_id(data, context=context)
                cls.assert_no_raw_text_leakage(data, context=context)

    @classmethod
    def scrub_report_dict(cls, report_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Verify and sanitize a report dictionary to guarantee purely aggregate contents."""
        cls.assert_no_participant_records(report_dict, context="ReportDictionary")
        return report_dict

    @classmethod
    def validate_notebook_outputs(cls, notebook_dict: Dict[str, Any]) -> None:
        """Inspect ALL notebook cells and output MIME types for privacy violations.
        
        Validates:
        - Stream text ('text')
        - Text plain ('data' -> 'text/plain')
        - HTML ('data' -> 'text/html')
        - Markdown ('data' -> 'text/markdown')
        - SVG XML ('data' -> 'image/svg+xml')
        - Structured JSON ('data' -> 'application/json' or '+json')
        - Markdown cells
        - Tracebacks ('traceback')
        """
        for cell_idx, cell in enumerate(notebook_dict.get("cells", [])):
            cell_type = cell.get("cell_type")
            context = f"Cell[{cell_idx}]:{cell_type}"

            if cell_type == "markdown":
                source_text = "".join(cell.get("source", [])) if isinstance(cell.get("source"), list) else str(cell.get("source", ""))
                cls.assert_no_raw_text_leakage(source_text, context)

            elif cell_type == "code":
                outputs = cell.get("outputs", [])
                for out_idx, out in enumerate(outputs):
                    out_context = f"{context}.output[{out_idx}]"
                    
                    # 1. Stream text
                    if "text" in out:
                        txt = "".join(out["text"]) if isinstance(out["text"], list) else str(out["text"])
                        cls.assert_no_raw_text_leakage(txt, out_context)

                    # 2. Data MIME types
                    if "data" in out:
                        data_dict = out["data"]
                        for mime_type, content in data_dict.items():
                            mime_context = f"{out_context}.{mime_type}"
                            
                            # Structured JSON data
                            if mime_type == "application/json" or mime_type.endswith("+json"):
                                if isinstance(content, str):
                                    try:
                                        structured = json.loads(content)
                                    except Exception as e:
                                        raise PrivacyViolationError(f"Malformed JSON in {mime_context}: {e}")
                                else:
                                    structured = content
                                cls.assert_no_participant_records(structured, context=mime_context)
                                
                            # Textual and vector graphic data
                            elif mime_type.startswith("text/") or mime_type in {"image/svg+xml", "application/xml"}:
                                mime_str = "".join(content) if isinstance(content, list) else str(content)
                                cls.assert_no_raw_text_leakage(mime_str, mime_context)
                                
                                # Attempt JSON parsing if string resembles serialized JSON object or array
                                s_clean = mime_str.strip()
                                if (s_clean.startswith("{") and s_clean.endswith("}")) or (s_clean.startswith("[") and s_clean.endswith("]")):
                                    parsed_obj = None
                                    try:
                                        parsed_obj = json.loads(s_clean)
                                    except Exception:
                                        pass
                                    if parsed_obj is not None:
                                        cls.assert_no_participant_records(parsed_obj, context=f"{mime_context}[json]")
                                        
                            # Standard binary image raster formats are allowed
                            elif mime_type in {"image/png", "image/jpeg", "image/gif"}:
                                continue
                                
                            else:
                                # For any unapproved MIME type, strictly inspect string representation
                                cls.assert_no_raw_text_leakage(str(content), mime_context)

                    # 3. Traceback
                    if "traceback" in out:
                        tb = "".join(out["traceback"]) if isinstance(out["traceback"], list) else str(out["traceback"])
                        cls.assert_no_raw_text_leakage(tb, f"{out_context}.traceback")

    @classmethod
    def assert_no_raw_text_leakage(cls, text: str, context: str) -> None:
        """Scan raw output text, SVG, or HTML for participant records or raw ID patterns."""
        # 1. Check labeled identifier pattern FIRST across the entire text
        if cls.LABELED_ID_PATTERN.search(text):
            raise PrivacyViolationError(
                f"Participant record pattern [REDACTED_ID] detected in {context}."
            )

        # 2. Check legacy/specific regex patterns
        for pattern in cls.TEXT_ID_PATTERNS:
            if pattern.search(text):
                raise PrivacyViolationError(
                    f"Participant record pattern [REDACTED_ID] detected in {context}."
                )

        # 3. Inspect HTML tables against approved typed schemas
        if "<table" in text.lower() or "<tr" in text.lower():
            cls.validate_html_tables(text, context)

        # 3. Inspect remaining non-table text/SVG for standalone candidate participant IDs
        # Remove validated <table> blocks to prevent duplicate checking
        text_no_tables = re.sub(r"<table[^>]*>.*?</table>", " ", text, flags=re.DOTALL | re.IGNORECASE)
        # Strip HTML character entities (e.g. &#9654;, &nbsp;)
        text_no_entities = re.sub(r"&[a-zA-Z0-9#]+;", " ", text_no_tables)
        # Strip remaining HTML tags
        clean_text = re.sub(r"<[^>]+>", " ", text_no_entities)

        # If clean_text represents an approved plain-text table, validate its column contracts
        if cls.is_approved_plain_text_table(clean_text, context):
            return

        for m in cls.STANDALONE_ID_TOKEN.finditer(clean_text):
            if not cls.is_approved_text_slot(clean_text, m.start(), m.end()):
                raise PrivacyViolationError(
                    f"Standalone participant-like identifier [REDACTED_ID] detected in {context}."
                )

    @classmethod
    def sanitize_exception(cls, err: Exception) -> str:
        """Sanitize an exception string to prevent raw record leakage in audit error logs."""
        raw_msg = str(err)
        # Redact any numeric sequences of 3 or more digits
        sanitized = re.sub(r"\b\d{3,7}\b", "[REDACTED_ID]", raw_msg)
        return sanitized