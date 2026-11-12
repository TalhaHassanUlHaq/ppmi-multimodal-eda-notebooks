"""Automated tests for Dataset Selection & Prioritization Gate.

Validates all requirements specified in Section 7 of docs/phase_specs/dataset_selection_gate.md
and enforces supervisory invariants from Codex Round 1, Round 2, and Round 3 reviews:
1. Matrix contains exactly canonical 177 source paths with matching SHA-256 hashes.
2. Multi-sheet workbooks retain sheet-level evidence and decision rows (6 sheets, 183 units total).
3. Category values restricted to approved tiers; proposed_category strictly pending approval (SG-08).
4. No automatic exclusion of (1) filenames, small samples, or zero-row safety logs.
5. Every candidate exclusion has a nonempty rationale, specific comparator source, and structured evidence type.
   Verifies byte-identical SHA-256 match for CSV copies and AppleDouble magic 00 05 16 07 for sidecars (SG-04).
6. Expected duplicate groups dynamically derived from canonical inventory hashes match engine output (SG-03).
   Open_Query cross-domain duplicate pair remains in Needs Review (not auto-excluded).
7. Denominators & Coverage policy: all cohort denominators and coverage percentages are strictly unverified / None
   until an exact protocol establishes an eligible population; zero numerator-equals-denominator tautologies (SG-01).
8. Programmatic DocumentLocatorValidator: opens PDFs/DOCX/XLSX, validates physical page bounds, headings, terms,
   and sheet dimensions; negative locator tests reject out-of-bounds locators and missing terms (SG-02, SG-07).
9. Modality-aware routing invariants: zero imaging or biospecimen fallbacks to clinical; neutral modality roles (SG-02).
10. Lossless full-field parity: ALL 47 fields match between JSON and CSV across all 183 rows (SG-06, SG-07).
11. Category totals reconcile globally across JSON, CSV, reports, decisions, and notebook (11, 132, 4, 30) (SG-04).
12. Notebook Table 12.5 contains EXACTLY 183 data rows and ALL 47 required column headers (SG-05).
13. Raw source files on disk remain strictly immutable (full hash check of all 177 sources).
14. PrivacyGuard validates all exported selection artifacts and executed notebook outputs (SG-09).
"""

import csv
import hashlib
import json
import os
from pathlib import Path
import pytest

from ppmi_pipeline.reporting.privacy import PrivacyGuard
from ppmi_pipeline.validation.selection import (
    DENOMINATOR_REGISTRY,
    DOCUMENTATION_CATALOG,
    CANDIDATE_CLINICAL_PROGRESSION_PATHS,
    SCIENTIFICALLY_PLAUSIBLE_ANALYSIS_PATHS,
    OPEN_QUERY_DUPLICATE_PATHS,
    DatasetSelectionAuditor,
    DocumentLocatorValidator,
    SelectionCategory,
    AtomicClaim,
    StructuredLocator,
    LongitudinalTier,
    resolve_repo_root,
    REVIEWED_CLAIM_TEMPLATES,
    CANONICAL_CLAIM_MANIFEST,
    load_canonical_claim_manifest,
    compute_manifest_record_digest,
)


@pytest.fixture(scope="module")
def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


@pytest.fixture(scope="module")
def auditor(repo_root) -> DatasetSelectionAuditor:
    return DatasetSelectionAuditor(repo_root=repo_root)


@pytest.fixture(scope="module")
def selection_data(repo_root, auditor) -> dict:
    matrix_json_path = repo_root / "EDA" / "outputs" / "reports" / "dataset_selection_matrix.json"
    if not matrix_json_path.exists():
        auditor.export_artifacts()
    with open(matrix_json_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def canonical_inventory(repo_root) -> dict:
    inv_path = repo_root / "EDA" / "outputs" / "reports" / "phase1_multimodal_inventory.json"
    assert inv_path.exists(), "Missing canonical inventory"
    with open(inv_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_selection_matrix_source_files_count_and_hashes(canonical_inventory, selection_data):
    """Selection matrix must contain exactly the 177 canonical source files with matching hashes (SG-07)."""
    sources = canonical_inventory["source_files"]
    matrix_files = selection_data["file_selection_matrix"]

    assert len(matrix_files) == 177, f"Expected 177 files in selection matrix, got {len(matrix_files)}"
    assert len(sources) == 177

    inv_hash_map = {s["relative_path"]: s["sha256"] for s in sources}
    matrix_hash_map = {m["relative_path"]: m["sha256"] for m in matrix_files}

    assert set(inv_hash_map.keys()) == set(matrix_hash_map.keys()), "Path discrepancy between inventory and selection"
    for rel_path, inv_hash in inv_hash_map.items():
        assert matrix_hash_map[rel_path] == inv_hash, f"Hash mismatch on {rel_path}"


def test_selection_matrix_retains_sheet_level_rows(selection_data):
    """Multi-sheet workbooks must generate individual sheet-level rows (6 sheets, 183 decision units) (SG-05)."""
    sheet_matrix = selection_data["worksheet_selection_matrix"]
    assert len(sheet_matrix) == 6, f"Expected 6 worksheet rows, got {len(sheet_matrix)}"

    expected_sheets = {
        "curated_datacuts/PPMI_Curated_Data_Cut_Public_20260810(1).xlsx -> [20260810]",
        "curated_datacuts/PPMI_Curated_Data_Cut_Public_20260810(1).xlsx -> [Data dictionary]",
        "curated_datacuts/PPMI_Curated_Data_Cut_Public_20260810(1).xlsx -> [Information]",
        "MR Analysis Results/PPMI_rs-fMRI_Data-and-Methods/PPMI_fs-fMRI_dataReport_spreadsheet_FINAL_20191121.xlsx -> [PPMI_rsfMRI_09052019]",
        "MR Analysis Results/PPMI_rs-fMRI_Data-and-Methods/PPMI_fs-fMRI_dataReport_spreadsheet_FINAL_20191121.xlsx -> [Dictionary]",
        "biospecimen/PPMI_IPSC_Catalog_User_Guide(1).xlsx -> [iPSC Catalog Guide]",
    }
    actual_sheets = {s["relative_path"] for s in sheet_matrix}
    assert actual_sheets == expected_sheets

    # Total decision units = 177 files + 6 worksheets = 183
    all_units = selection_data["file_selection_matrix"] + selection_data["worksheet_selection_matrix"]
    assert len(all_units) == 183


def test_selection_category_values_and_pending_approval(selection_data):
    """All categories must be valid enum members and proposed_category must be strictly pending approval (SG-08)."""
    approved_recs = {c.value for c in SelectionCategory}
    all_units = selection_data["file_selection_matrix"] + selection_data["worksheet_selection_matrix"]

    for row in all_units:
        assert row["provisional_recommendation"] in approved_recs
        assert row["proposed_category"] == SelectionCategory.PRE_REVIEW_PENDING.value
        assert "Awaiting Supervisor Review & Human Sign-off" in row["approval_status"]


def test_no_automatic_exclusion_heuristics(selection_data):
    """Small sample size, high null rate, or (1) naming must NOT trigger automatic exclusion (SG-04)."""
    matrix_files = selection_data["file_selection_matrix"]

    for row in matrix_files:
        fn = row["file_name"]
        rec = row["provisional_recommendation"]
        distinct_pts = row["observed_distinct_ids"]
        null_rate = row["null_rate_percent"]
        row_count = row["row_count"]

        # Legitimate (1) files must NOT be excluded
        if fn in ("PPMI_IPSC_Catalog_User_Guide(1).xlsx", "PPMI_Curated_Data_Cut_Public_20260810(1).xlsx"):
            assert rec != SelectionCategory.EXCLUDED.value, f"Improper exclusion of legitimate file: {fn}"

        # Zero-row table exports must NOT be excluded
        if row_count == 0:
            assert rec != SelectionCategory.EXCLUDED.value, f"Zero-row file improperly excluded: {fn}"

        # Small sample size cohorts must NOT be excluded
        if distinct_pts > 0 and distinct_pts < 50 and rec == SelectionCategory.EXCLUDED.value:
            assert "(1)" in fn or fn.startswith("._"), f"Small-sample file improperly excluded: {fn}"


def test_candidate_exclusions_evidence_types(selection_data):
    """Every exclusion must have structured evidence: byte-identical SHA-256 copy or AppleDouble magic (SG-04)."""
    matrix_files = selection_data["file_selection_matrix"]
    excluded = [r for r in matrix_files if r["provisional_recommendation"] == SelectionCategory.EXCLUDED.value]

    assert len(excluded) == 4, f"Expected exactly 4 candidate exclusions, found {len(excluded)}"

    for row in excluded:
        fn = row["file_name"]
        assert row["exact_comparator_source"] is not None
        assert row["file_specific_rationale"] != ""
        assert row["redundancy_evidence"] != ""

        if fn in ("FS7_APARC_CTH_09Nov2026(1).csv", "iu_genetic_consensus_20251025_09Nov2026(1).csv"):
            assert "Byte-identical copy" in row["redundancy_evidence"]
            assert "SHA-256 match" in row["redundancy_evidence"]
        elif fn.startswith("._"):
            assert "AppleDouble metadata sidecar" in row["redundancy_evidence"]
            assert "00 05 16 07" in row["redundancy_evidence"]
            assert "companion hash differs" in row["redundancy_evidence"]


def test_duplicate_grouping_derived_from_inventory(canonical_inventory, selection_data):
    """Expected duplicate groups dynamically derived from inventory hashes must match engine output (SG-03)."""
    hash_to_paths = {}
    for item in canonical_inventory["source_files"]:
        hash_to_paths.setdefault(item["sha256"], []).append(item["relative_path"])
    expected_groups = {h: paths for h, paths in hash_to_paths.items() if len(paths) > 1}

    engine_groups = selection_data["metadata"]["duplicate_hash_groups"]
    assert engine_groups == expected_groups, "Engine duplicate hash groups do not match derived groups from inventory"

    file_map = {r["relative_path"]: r for r in selection_data["file_selection_matrix"]}
    assert file_map["DATSCAN/Open_Query_09Nov2026.csv"]["provisional_recommendation"] == SelectionCategory.NEEDS_REVIEW.value
    assert file_map["MEDICAL HISTORY/Open_Query_09Nov2026.csv"]["provisional_recommendation"] == SelectionCategory.NEEDS_REVIEW.value


def test_denominators_and_coverage_are_strictly_unverified_no_tautology(selection_data, auditor):
    """All cohort denominators and coverage percentages must be None until verified; zero tautology (SG-01)."""
    all_units = selection_data["file_selection_matrix"] + selection_data["worksheet_selection_matrix"]

    # Invariant 1: Every single row across all 183 units must report None denominator and None coverage
    for row in all_units:
        assert row["eligible_cohort_denominator"] is None, f"Non-null denominator on {row['relative_path']}"
        assert row["participant_coverage_percent"] is None, f"Non-null coverage on {row['relative_path']}"

    # Invariant 2: Synthetic test proving changing distinct participants does NOT invent a denominator
    mock_file = {
        "relative_path": "curated_datacuts/PPMI_Curated_Data_Cut_Public_20260810(1).xlsx",
        "file_name": "PPMI_Curated_Data_Cut_Public_20260810(1).xlsx",
        "modality": "Curated",
        "format": "Excel Workbook",
        "sha256": "mock_hash",
        "row_count": 20408,
        "column_count": 453,
        "has_patno": True,
        "has_visit": True,
        "distinct_participants": 5019,
        "distinct_visits": 21,
    }
    r1, _ = auditor.evaluate_file(mock_file)
    mock_file["distinct_participants"] = 3000
    r2, _ = auditor.evaluate_file(mock_file)
    assert r1.eligible_cohort_denominator is None
    assert r2.eligible_cohort_denominator is None
    assert r1.participant_coverage_percent is None
    assert r2.participant_coverage_percent is None


def test_documentation_catalog_physically_resolves_all_locators_and_terms(repo_root, selection_data):
    """All catalog entries must resolve to disk and pass DocumentLocatorValidator with canonical key checks (SG-02, SG-07)."""
    canonical_sources = set(r["relative_path"] for r in selection_data["file_selection_matrix"])
    for r in selection_data["worksheet_selection_matrix"]:
        canonical_sources.add(r["relative_path"])

    validator = DocumentLocatorValidator(repo_root, canonical_sources=canonical_sources)
    results = validator.validate_catalog(DOCUMENTATION_CATALOG)

    assert len(results) == 30, f"Expected 30 validated catalog entries, got {len(results)}"
    for source_key, (is_valid, msg) in results.items():
        assert is_valid, f"Catalog validation failed for {source_key}: {msg}"


def test_document_locator_validator_fail_closed_mutations(repo_root, selection_data):
    """DocumentLocatorValidator must fail closed on non-canonical keys, unknown types, prohibited claims, missing terms, false bounds, and whole-cell column matching (SG-02, SG-07)."""
    canonical_sources = set(r["relative_path"] for r in selection_data["file_selection_matrix"])
    for r in selection_data["worksheet_selection_matrix"]:
        canonical_sources.add(r["relative_path"])
    validator = DocumentLocatorValidator(repo_root, canonical_sources=canonical_sources)

    sbr_t = REVIEWED_CLAIM_TEMPLATES["sbr_calc"]
    rfmri_t = REVIEWED_CLAIM_TEMPLATES["rfmri_methods"]
    cur_t = REVIEWED_CLAIM_TEMPLATES["curated_data_cut"]

    # 1. Non-canonical source key paired with a real document
    bad_key_entry = {
        "document_path": sbr_t["doc_path"],
        "claims": [
            AtomicClaim(
                claim_id="sbr_calc",
                claim_text=sbr_t["approved_text"],
                structured_locator=StructuredLocator("pdf", sbr_t["doc_path"], page_range=(1, 2)),
                required_evidence_terms=sbr_t["required_evidence_terms"]
            )
        ]
    }
    ok, msg = validator.validate_entry("nonexistent/source_file_999.csv", bad_key_entry)
    assert not ok
    assert "non-canonical" in msg.lower()

    # 2. Missing or empty claims list (fail-closed)
    valid_key = "DATSCAN/Xing_Core_Lab_-_Quant_SBR_09Nov2026.csv"
    no_claims_entry = {
        "document_path": sbr_t["doc_path"],
        "claims": []
    }
    ok, msg = validator.validate_entry(valid_key, no_claims_entry)
    assert not ok
    assert "missing or empty claims" in msg.lower()

    # 3. Unsupported / unknown validation_spec type (fail-closed)
    bad_type_claim = AtomicClaim(
        claim_id="sbr_calc",
        claim_text=sbr_t["approved_text"],
        structured_locator=StructuredLocator("magic_unsupported_type", sbr_t["doc_path"]),
        required_evidence_terms=sbr_t["required_evidence_terms"]
    )
    ok, msg = validator.validate_atomic_claim(bad_type_claim)
    assert not ok
    assert "unsupported validation type" in msg.lower()

    # 4. Prohibited / fabricated assertion in claim_text (e.g. 'cure', 'fabricated', etc.)
    cure_claim = AtomicClaim(
        claim_id="sbr_calc",
        claim_text="Quantitative Specific Binding Ratio calculated by Xing Core Lab guarantees a cure for Parkinson's disease.",
        structured_locator=StructuredLocator("pdf", sbr_t["doc_path"], page_range=(1, 2)),
        required_evidence_terms=sbr_t["required_evidence_terms"]
    )
    ok, msg = validator.validate_atomic_claim(cure_claim)
    assert not ok
    assert "fabricated assertion" in msg.lower()

    # 5. Unauthorized claim text mutation / false prose with valid keywords rejected (SG-02, SG-07)
    mutated_claim = AtomicClaim(
        claim_id="sbr_calc",
        claim_text="Quantitative Specific Binding Ratio calculated by Xing Core Lab for caudate and putamen using MIAKAT and Method standards with extraordinary efficacy.",
        structured_locator=StructuredLocator("pdf", sbr_t["doc_path"], page_range=(1, 2)),
        required_evidence_terms=sbr_t["required_evidence_terms"]
    )
    ok, msg = validator.validate_atomic_claim(mutated_claim)
    assert not ok
    assert "unauthorized text mutation rejected" in msg.lower()

    # 6. Missing / mutated required evidence terms in claim
    missing_term_claim = AtomicClaim(
        claim_id="sbr_calc",
        claim_text=sbr_t["approved_text"],
        structured_locator=StructuredLocator("pdf", sbr_t["doc_path"], page_range=(1, 2)),
        required_evidence_terms=["Method", "Specific Binding Ratio", "NonexistentTerm"]
    )
    ok, msg = validator.validate_atomic_claim(missing_term_claim)
    assert not ok
    assert "differ from supervisor-reviewed template" in msg.lower() or "not assert" in msg.lower()

    # 7. PDF page range template mismatch and physical out of bounds (DaTscan quant has 2 pages)
    bad_pdf_claim = AtomicClaim(
        claim_id="sbr_calc",
        claim_text=sbr_t["approved_text"],
        structured_locator=StructuredLocator("pdf", sbr_t["doc_path"], page_range=(1, 10)),
        required_evidence_terms=sbr_t["required_evidence_terms"]
    )
    ok, msg = validator.validate_atomic_claim(bad_pdf_claim)
    assert not ok
    assert "page_range mismatch" in msg.lower() or "out of bounds" in msg.lower()

    # Physical page bounds check when template itself specifies out-of-bounds page range
    phys_test_manifest = dict(validator.manifest)
    phys_test_manifest["pdf_oob_probe"] = {
        "claim_id": "pdf_oob_probe",
        "template_version": "1.0.0",
        "approved_text": sbr_t["approved_text"],
        "required_evidence_terms": list(sbr_t["required_evidence_terms"]),
        "doc_type": "pdf",
        "doc_path": sbr_t["doc_path"],
        "structured_locator": {
            "doc_type": "pdf",
            "doc_path": sbr_t["doc_path"],
            "page_range": [1, 10],
            "heading_text": None,
            "sheet_name": None,
            "exact_dimensions": None,
            "exact_columns": None,
            "cell_range": None,
            "sheet_title_evidence_terms": None,
        }
    }
    phys_test_manifest["pdf_oob_probe"]["approved_digest"] = compute_manifest_record_digest(phys_test_manifest["pdf_oob_probe"])
    phys_validator = DocumentLocatorValidator(repo_root, manifest=phys_test_manifest)
    phys_oob_claim = AtomicClaim(
        claim_id="pdf_oob_probe",
        claim_text=sbr_t["approved_text"],
        structured_locator=StructuredLocator("pdf", sbr_t["doc_path"], page_range=(1, 10)),
        required_evidence_terms=list(sbr_t["required_evidence_terms"])
    )
    ok_oob, msg_oob = phys_validator.validate_atomic_claim(phys_oob_claim)
    assert not ok_oob
    assert "out of bounds" in msg_oob.lower()

    # 8. DOCX heading check: template mismatch and physical non-heading style rejection
    bad_docx_heading = AtomicClaim(
        claim_id="rfmri_methods",
        claim_text=rfmri_t["approved_text"],
        structured_locator=StructuredLocator(
            "docx",
            rfmri_t["doc_path"],
            heading_text="The current PPMI study comprises five cohorts"
        ),
        required_evidence_terms=rfmri_t["required_evidence_terms"]
    )
    ok, msg = validator.validate_atomic_claim(bad_docx_heading)
    assert not ok
    assert "heading_text mismatch" in msg.lower() or "heading-style paragraph" in msg.lower()

    # Physical DOCX check when template itself specifies body text not in Heading styles
    docx_test_manifest = dict(validator.manifest)
    docx_test_manifest["docx_body_probe"] = {
        "claim_id": "docx_body_probe",
        "template_version": "1.0.0",
        "approved_text": rfmri_t["approved_text"],
        "required_evidence_terms": list(rfmri_t["required_evidence_terms"]),
        "doc_type": "docx",
        "doc_path": rfmri_t["doc_path"],
        "structured_locator": {
            "doc_type": "docx",
            "doc_path": rfmri_t["doc_path"],
            "page_range": None,
            "heading_text": "The current PPMI study comprises five cohorts",
            "sheet_name": None,
            "exact_dimensions": None,
            "exact_columns": None,
            "cell_range": None,
            "sheet_title_evidence_terms": None,
        }
    }
    docx_test_manifest["docx_body_probe"]["approved_digest"] = compute_manifest_record_digest(docx_test_manifest["docx_body_probe"])
    docx_validator = DocumentLocatorValidator(repo_root, manifest=docx_test_manifest)
    docx_body_claim = AtomicClaim(
        claim_id="docx_body_probe",
        claim_text=rfmri_t["approved_text"],
        structured_locator=StructuredLocator("docx", rfmri_t["doc_path"], heading_text="The current PPMI study comprises five cohorts"),
        required_evidence_terms=list(rfmri_t["required_evidence_terms"])
    )
    ok_body, msg_body = docx_validator.validate_atomic_claim(docx_body_claim)
    assert not ok_body
    assert "heading-style paragraph" in msg_body.lower() and "not found" in msg_body.lower()

    # 9. DOCX heading partial/substring match must fail: template mismatch and physical rejection (SG-02, SG-07)
    partial_heading_claim = AtomicClaim(
        claim_id="rfmri_methods",
        claim_text=rfmri_t["approved_text"],
        structured_locator=StructuredLocator(
            "docx",
            rfmri_t["doc_path"],
            heading_text="Meth"  # Substring of 'Method'
        ),
        required_evidence_terms=rfmri_t["required_evidence_terms"]
    )
    ok, msg = validator.validate_atomic_claim(partial_heading_claim)
    assert not ok
    assert "heading_text mismatch" in msg.lower() or "exact heading-style paragraph" in msg.lower()

    # Physical DOCX check when template itself specifies substring 'Meth'
    docx_test_manifest["docx_sub_probe"] = {
        "claim_id": "docx_sub_probe",
        "template_version": "1.0.0",
        "approved_text": rfmri_t["approved_text"],
        "required_evidence_terms": list(rfmri_t["required_evidence_terms"]),
        "doc_type": "docx",
        "doc_path": rfmri_t["doc_path"],
        "structured_locator": {
            "doc_type": "docx",
            "doc_path": rfmri_t["doc_path"],
            "page_range": None,
            "heading_text": "Meth",
            "sheet_name": None,
            "exact_dimensions": None,
            "exact_columns": None,
            "cell_range": None,
            "sheet_title_evidence_terms": None,
        }
    }
    docx_test_manifest["docx_sub_probe"]["approved_digest"] = compute_manifest_record_digest(docx_test_manifest["docx_sub_probe"])
    docx_validator2 = DocumentLocatorValidator(repo_root, manifest=docx_test_manifest)
    docx_sub_claim = AtomicClaim(
        claim_id="docx_sub_probe",
        claim_text=rfmri_t["approved_text"],
        structured_locator=StructuredLocator("docx", rfmri_t["doc_path"], heading_text="Meth"),
        required_evidence_terms=list(rfmri_t["required_evidence_terms"])
    )
    ok_sub, msg_sub = docx_validator2.validate_atomic_claim(docx_sub_claim)
    assert not ok_sub
    assert "exact heading-style paragraph" in msg_sub.lower() and "not found" in msg_sub.lower()

    # 10. XLSX false sheet name, false dimensions, out-of-bounds cell_range, and whole-cell column match
    bad_sheet_claim = AtomicClaim(
        claim_id="curated_data_cut",
        claim_text=cur_t["approved_text"],
        structured_locator=StructuredLocator(
            "xlsx",
            cur_t["doc_path"],
            sheet_name="Nonexistent_Sheet_999",
            exact_dimensions=(453, 10),
            exact_columns=["Category", "Variable", "Description"],
            cell_range="A1:J453"
        ),
        required_evidence_terms=cur_t["required_evidence_terms"]
    )
    ok, msg = validator.validate_atomic_claim(bad_sheet_claim)
    assert not ok
    assert "sheet_name mismatch" in msg.lower() or "not found" in msg.lower()

    bad_dim_claim = AtomicClaim(
        claim_id="curated_data_cut",
        claim_text=cur_t["approved_text"],
        structured_locator=StructuredLocator(
            "xlsx",
            cur_t["doc_path"],
            sheet_name="Data dictionary",
            exact_dimensions=(999, 999),
            exact_columns=["Category", "Variable", "Description"],
            cell_range="A1:J453"
        ),
        required_evidence_terms=cur_t["required_evidence_terms"]
    )
    ok, msg = validator.validate_atomic_claim(bad_dim_claim)
    assert not ok
    assert "exact_dimensions mismatch" in msg.lower() or "!=" in msg.lower()

    bad_range_claim = AtomicClaim(
        claim_id="curated_data_cut",
        claim_text=cur_t["approved_text"],
        structured_locator=StructuredLocator(
            "xlsx",
            cur_t["doc_path"],
            sheet_name="Data dictionary",
            exact_dimensions=(453, 10),
            exact_columns=["Category", "Variable", "Description"],
            cell_range="ZZ999:ZZ1000"
        ),
        required_evidence_terms=cur_t["required_evidence_terms"]
    )
    ok, msg = validator.validate_atomic_claim(bad_range_claim)
    assert not ok
    assert "cell_range mismatch" in msg.lower() or "out of bounds" in msg.lower()

    # 11. Whole-cell exact column matching: 'PAT' must fail against 'PATNO'
    bad_col_claim = AtomicClaim(
        claim_id="curated_data_cut",
        claim_text=cur_t["approved_text"],
        structured_locator=StructuredLocator(
            "xlsx",
            cur_t["doc_path"],
            sheet_name="Data dictionary",
            exact_dimensions=(453, 10),
            exact_columns=["PAT"],
            cell_range="A1:J453"
        ),
        required_evidence_terms=cur_t["required_evidence_terms"]
    )
    ok, msg = validator.validate_atomic_claim(bad_col_claim)
    assert not ok
    assert "exact_columns mismatch" in msg.lower() or "missing" in msg.lower()

    # Physical checks for XLSX when template itself contains out-of-bounds range or non-matching column
    xlsx_test_manifest = dict(validator.manifest)
    xlsx_test_manifest["xlsx_oob_probe"] = {
        "claim_id": "xlsx_oob_probe",
        "template_version": "1.0.0",
        "approved_text": cur_t["approved_text"],
        "required_evidence_terms": list(cur_t["required_evidence_terms"]),
        "doc_type": "xlsx",
        "doc_path": cur_t["doc_path"],
        "structured_locator": {
            "doc_type": "xlsx",
            "doc_path": cur_t["doc_path"],
            "page_range": None,
            "heading_text": None,
            "sheet_name": "Data dictionary",
            "exact_dimensions": [453, 10],
            "exact_columns": ["Category", "Variable", "Description"],
            "cell_range": "ZZ999:ZZ1000",
            "sheet_title_evidence_terms": None,
        }
    }
    xlsx_test_manifest["xlsx_oob_probe"]["approved_digest"] = compute_manifest_record_digest(xlsx_test_manifest["xlsx_oob_probe"])
    xlsx_validator = DocumentLocatorValidator(repo_root, manifest=xlsx_test_manifest)
    phys_range_claim = AtomicClaim(
        claim_id="xlsx_oob_probe",
        claim_text=cur_t["approved_text"],
        structured_locator=StructuredLocator(
            "xlsx",
            cur_t["doc_path"],
            sheet_name="Data dictionary",
            exact_dimensions=(453, 10),
            exact_columns=["Category", "Variable", "Description"],
            cell_range="ZZ999:ZZ1000"
        ),
        required_evidence_terms=list(cur_t["required_evidence_terms"])
    )
    ok_oob_range, msg_oob_range = xlsx_validator.validate_atomic_claim(phys_range_claim)
    assert not ok_oob_range
    assert "out of bounds" in msg_oob_range.lower()

    # 12. Locator string mismatch fails consistency check
    mismatched_locator_entry = {
        "document_path": sbr_t["doc_path"],
        "locator": f"{sbr_t['doc_path']} (pp. 99-100)",
        "claims": [
            AtomicClaim(
                claim_id="sbr_calc",
                claim_text=sbr_t["approved_text"],
                structured_locator=StructuredLocator("pdf", sbr_t["doc_path"], page_range=(1, 2)),
                required_evidence_terms=sbr_t["required_evidence_terms"]
            )
        ]
    }
    ok, msg = validator.validate_entry(valid_key, mismatched_locator_entry)
    assert not ok
    assert "locator string mismatch" in msg.lower()



def test_canonical_template_rejects_omitted_or_mutated_locator_fields(repo_root, selection_data):
    """Negative tests verifying that canonical claim validation rejects omission or mutation of any locator constraint (Round 8 SG-02, SG-07)."""
    validator = DocumentLocatorValidator(repo_root)

    # --- A. PDF page_range mutations ---
    sbr_tmpl = validator.manifest["sbr_calc"]
    # A1. Omitted page_range (None)
    claim_omit_pages = AtomicClaim(
        claim_id="sbr_calc",
        claim_text=sbr_tmpl["approved_text"],
        structured_locator=StructuredLocator("pdf", sbr_tmpl["doc_path"], page_range=None),
        required_evidence_terms=list(sbr_tmpl["required_evidence_terms"])
    )
    ok, msg = validator.validate_atomic_claim(claim_omit_pages)
    assert not ok
    assert "page_range mismatch" in msg

    # A2. Mutated valid in-bounds page_range (1, 1) instead of canonical (1, 2)
    claim_mut_pages1 = AtomicClaim(
        claim_id="sbr_calc",
        claim_text=sbr_tmpl["approved_text"],
        structured_locator=StructuredLocator("pdf", sbr_tmpl["doc_path"], page_range=(1, 1)),
        required_evidence_terms=list(sbr_tmpl["required_evidence_terms"])
    )
    ok, msg = validator.validate_atomic_claim(claim_mut_pages1)
    assert not ok
    assert "page_range mismatch" in msg

    # A3. Mutated valid in-bounds page_range (2, 2) instead of canonical (1, 2)
    claim_mut_pages2 = AtomicClaim(
        claim_id="sbr_calc",
        claim_text=sbr_tmpl["approved_text"],
        structured_locator=StructuredLocator("pdf", sbr_tmpl["doc_path"], page_range=(2, 2)),
        required_evidence_terms=list(sbr_tmpl["required_evidence_terms"])
    )
    ok, msg = validator.validate_atomic_claim(claim_mut_pages2)
    assert not ok
    assert "page_range mismatch" in msg

    # --- B. DOCX heading_text mutations ---
    rfmri_tmpl = validator.manifest["rfmri_methods"]
    # B1. Omitted heading_text (None)
    claim_omit_hd = AtomicClaim(
        claim_id="rfmri_methods",
        claim_text=rfmri_tmpl["approved_text"],
        structured_locator=StructuredLocator("docx", rfmri_tmpl["doc_path"], heading_text=None),
        required_evidence_terms=list(rfmri_tmpl["required_evidence_terms"])
    )
    ok, msg = validator.validate_atomic_claim(claim_omit_hd)
    assert not ok
    assert "heading_text mismatch" in msg

    # B2. Mutated heading_text ("Summary" instead of "Method")
    claim_mut_hd = AtomicClaim(
        claim_id="rfmri_methods",
        claim_text=rfmri_tmpl["approved_text"],
        structured_locator=StructuredLocator("docx", rfmri_tmpl["doc_path"], heading_text="Summary"),
        required_evidence_terms=list(rfmri_tmpl["required_evidence_terms"])
    )
    ok, msg = validator.validate_atomic_claim(claim_mut_hd)
    assert not ok
    assert "heading_text mismatch" in msg

    # --- C. XLSX sheet_name, exact_dimensions, exact_columns, and cell_range mutations ---
    cur_tmpl = validator.manifest["curated_data_cut"]

    # C1. Omitted sheet_name (None)
    claim_omit_sn = AtomicClaim(
        claim_id="curated_data_cut",
        claim_text=cur_tmpl["approved_text"],
        structured_locator=StructuredLocator(
            "xlsx",
            cur_tmpl["doc_path"],
            sheet_name=None,
            exact_dimensions=(453, 10),
            exact_columns=["Category", "Variable", "Description"],
            cell_range="A1:J453"
        ),
        required_evidence_terms=list(cur_tmpl["required_evidence_terms"])
    )
    ok, msg = validator.validate_atomic_claim(claim_omit_sn)
    assert not ok
    assert "sheet_name mismatch" in msg

    # C2. Mutated sheet_name ("WrongSheet")
    claim_mut_sn = AtomicClaim(
        claim_id="curated_data_cut",
        claim_text=cur_tmpl["approved_text"],
        structured_locator=StructuredLocator(
            "xlsx",
            cur_tmpl["doc_path"],
            sheet_name="WrongSheet",
            exact_dimensions=(453, 10),
            exact_columns=["Category", "Variable", "Description"],
            cell_range="A1:J453"
        ),
        required_evidence_terms=list(cur_tmpl["required_evidence_terms"])
    )
    ok, msg = validator.validate_atomic_claim(claim_mut_sn)
    assert not ok
    assert "sheet_name mismatch" in msg

    # C3. Omitted exact_dimensions (None)
    claim_omit_dims = AtomicClaim(
        claim_id="curated_data_cut",
        claim_text=cur_tmpl["approved_text"],
        structured_locator=StructuredLocator(
            "xlsx",
            cur_tmpl["doc_path"],
            sheet_name="Data dictionary",
            exact_dimensions=None,
            exact_columns=["Category", "Variable", "Description"],
            cell_range="A1:J453"
        ),
        required_evidence_terms=list(cur_tmpl["required_evidence_terms"])
    )
    ok, msg = validator.validate_atomic_claim(claim_omit_dims)
    assert not ok
    assert "exact_dimensions mismatch" in msg

    # C4. Mutated exact_dimensions ((453, 11) instead of (453, 10))
    claim_mut_dims = AtomicClaim(
        claim_id="curated_data_cut",
        claim_text=cur_tmpl["approved_text"],
        structured_locator=StructuredLocator(
            "xlsx",
            cur_tmpl["doc_path"],
            sheet_name="Data dictionary",
            exact_dimensions=(453, 11),
            exact_columns=["Category", "Variable", "Description"],
            cell_range="A1:J453"
        ),
        required_evidence_terms=list(cur_tmpl["required_evidence_terms"])
    )
    ok, msg = validator.validate_atomic_claim(claim_mut_dims)
    assert not ok
    assert "exact_dimensions mismatch" in msg

    # C5. Omitted exact_columns (None)
    claim_omit_cols = AtomicClaim(
        claim_id="curated_data_cut",
        claim_text=cur_tmpl["approved_text"],
        structured_locator=StructuredLocator(
            "xlsx",
            cur_tmpl["doc_path"],
            sheet_name="Data dictionary",
            exact_dimensions=(453, 10),
            exact_columns=None,
            cell_range="A1:J453"
        ),
        required_evidence_terms=list(cur_tmpl["required_evidence_terms"])
    )
    ok, msg = validator.validate_atomic_claim(claim_omit_cols)
    assert not ok
    assert "exact_columns mismatch" in msg

    # C6. Mutated exact_columns (subset: ["Category", "Variable"])
    claim_mut_cols = AtomicClaim(
        claim_id="curated_data_cut",
        claim_text=cur_tmpl["approved_text"],
        structured_locator=StructuredLocator(
            "xlsx",
            cur_tmpl["doc_path"],
            sheet_name="Data dictionary",
            exact_dimensions=(453, 10),
            exact_columns=["Category", "Variable"],
            cell_range="A1:J453"
        ),
        required_evidence_terms=list(cur_tmpl["required_evidence_terms"])
    )
    ok, msg = validator.validate_atomic_claim(claim_mut_cols)
    assert not ok
    assert "exact_columns mismatch" in msg

    # C7. Omitted cell_range (None) — EXACT CODEX ROUND 7 PROBE!
    claim_omit_range = AtomicClaim(
        claim_id="curated_data_cut",
        claim_text=cur_tmpl["approved_text"],
        structured_locator=StructuredLocator(
            "xlsx",
            cur_tmpl["doc_path"],
            sheet_name="Data dictionary",
            exact_dimensions=(453, 10),
            exact_columns=["Category", "Variable", "Description"],
            cell_range=None
        ),
        required_evidence_terms=list(cur_tmpl["required_evidence_terms"])
    )
    ok, msg = validator.validate_atomic_claim(claim_omit_range)
    assert not ok
    assert "cell_range mismatch" in msg

    # C8. Mutated valid in-bounds cell_range ("A1:J100" instead of "A1:J453")
    claim_mut_range = AtomicClaim(
        claim_id="curated_data_cut",
        claim_text=cur_tmpl["approved_text"],
        structured_locator=StructuredLocator(
            "xlsx",
            cur_tmpl["doc_path"],
            sheet_name="Data dictionary",
            exact_dimensions=(453, 10),
            exact_columns=["Category", "Variable", "Description"],
            cell_range="A1:J100"
        ),
        required_evidence_terms=list(cur_tmpl["required_evidence_terms"])
    )
    ok, msg = validator.validate_atomic_claim(claim_mut_range)
    assert not ok
    assert "cell_range mismatch" in msg

    # C9. All constraints removed (exact probe tested in Codex Round 7 review)
    claim_all_removed = AtomicClaim(
        claim_id="curated_data_cut",
        claim_text=cur_tmpl["approved_text"],
        structured_locator=StructuredLocator(
            "xlsx",
            cur_tmpl["doc_path"],
            sheet_name="Data dictionary",
            exact_dimensions=None,
            exact_columns=None,
            cell_range=None
        ),
        required_evidence_terms=list(cur_tmpl["required_evidence_terms"])
    )
    ok, msg = validator.validate_atomic_claim(claim_all_removed)
    assert not ok
    assert "mismatch" in msg.lower()


def test_canonical_manifest_digest_integrity_and_duplicate_rejection(repo_root):
    """Canonical manifest loader and validator must enforce digest integrity and duplicate claim ID rejection (Round 8 SG-02, SG-07)."""
    validator = DocumentLocatorValidator(repo_root)

    # 1. Corrupt stored digest (64 zeroes) — EXACT CODEX ROUND 7 PROBE!
    corrupt_manifest = {k: dict(v) for k, v in validator.manifest.items()}
    corrupt_manifest["sbr_calc"] = dict(corrupt_manifest["sbr_calc"])
    corrupt_manifest["sbr_calc"]["approved_digest"] = "0" * 64

    tampered_validator = DocumentLocatorValidator(repo_root, manifest=corrupt_manifest)
    sbr_tmpl = validator.manifest["sbr_calc"]
    canonical_claim = AtomicClaim(
        claim_id="sbr_calc",
        claim_text=sbr_tmpl["approved_text"],
        structured_locator=StructuredLocator(
            "pdf",
            sbr_tmpl["doc_path"],
            page_range=tuple(sbr_tmpl["structured_locator"]["page_range"])
        ),
        required_evidence_terms=list(sbr_tmpl["required_evidence_terms"])
    )
    ok, msg = tampered_validator.validate_atomic_claim(canonical_claim)
    assert not ok
    assert "digest mismatch" in msg.lower()

    # 2. Missing stored digest
    corrupt_manifest2 = {k: dict(v) for k, v in validator.manifest.items()}
    corrupt_manifest2["sbr_calc"] = dict(corrupt_manifest2["sbr_calc"])
    corrupt_manifest2["sbr_calc"]["approved_digest"] = ""

    tampered_validator2 = DocumentLocatorValidator(repo_root, manifest=corrupt_manifest2)
    ok, msg = tampered_validator2.validate_atomic_claim(canonical_claim)
    assert not ok
    assert "digest mismatch" in msg.lower()

    # 3. Tampered manifest record text with original digest preserved
    corrupt_manifest3 = {k: dict(v) for k, v in validator.manifest.items()}
    corrupt_manifest3["sbr_calc"] = dict(corrupt_manifest3["sbr_calc"])
    corrupt_manifest3["sbr_calc"]["approved_text"] = "Unauthorized altered text"

    tampered_validator3 = DocumentLocatorValidator(repo_root, manifest=corrupt_manifest3)
    ok, msg = tampered_validator3.validate_atomic_claim(canonical_claim)
    assert not ok
    assert "digest mismatch" in msg.lower()

    # 4. Duplicate claim_id rejection at manifest load time
    raw_records = list(validator.manifest.values())
    duplicate_records = list(raw_records) + [raw_records[0]]  # duplicate sbr_calc
    with pytest.raises(ValueError, match="Duplicate claim_id"):
        load_canonical_claim_manifest(manifest_source=duplicate_records)

    # 5. Malformed manifest record rejection at manifest load time
    malformed_record = dict(raw_records[0])
    del malformed_record["doc_path"]  # missing required key
    with pytest.raises(ValueError, match="Malformed manifest record"):
        load_canonical_claim_manifest(manifest_source=[malformed_record])


def test_xlsx_cell_range_rejects_terms_only_in_sheet_title_or_outside_range(repo_root):
    """XLSX cell range validation must restrict search strictly to cells inside the approved range and reject terms only in the sheet title or outside the range (Round 8 SG-02, SG-07)."""
    validator = DocumentLocatorValidator(repo_root)

    # 1. Term 'iPSC' is physically in the sheet title 'iPSC Catalog Guide', but NOT inside cells A1:F46
    # A synthetic claim asserting 'iPSC' inside the cell range with NO sheet title evidence MUST fail closed!
    test_manifest = dict(validator.manifest)
    test_manifest["ipsc_synthetic_probe"] = {
        "claim_id": "ipsc_synthetic_probe",
        "template_version": "1.0.0",
        "approved_text": "User guide and variable dictionary for iPSC repository inventory defining Source Table Variable Name and Variable Description.",
        "required_evidence_terms": ["Source Table Variable Name", "Variable Description", "iPSC"],
        "doc_type": "xlsx",
        "doc_path": "biospecimen/PPMI_IPSC_Catalog_User_Guide(1).xlsx",
        "structured_locator": {
            "doc_type": "xlsx",
            "doc_path": "biospecimen/PPMI_IPSC_Catalog_User_Guide(1).xlsx",
            "page_range": None,
            "heading_text": None,
            "sheet_name": "iPSC Catalog Guide",
            "exact_dimensions": [46, 6],
            "exact_columns": ["Source Table Variable Name", "Variable Description"],
            "cell_range": "A1:F46",
            "sheet_title_evidence_terms": None,
        }
    }
    test_manifest["ipsc_synthetic_probe"]["approved_digest"] = compute_manifest_record_digest(test_manifest["ipsc_synthetic_probe"])

    probe_validator = DocumentLocatorValidator(repo_root, manifest=test_manifest)
    probe_claim = AtomicClaim(
        claim_id="ipsc_synthetic_probe",
        claim_text=test_manifest["ipsc_synthetic_probe"]["approved_text"],
        structured_locator=StructuredLocator(
            "xlsx",
            "biospecimen/PPMI_IPSC_Catalog_User_Guide(1).xlsx",
            sheet_name="iPSC Catalog Guide",
            exact_dimensions=(46, 6),
            exact_columns=["Source Table Variable Name", "Variable Description"],
            cell_range="A1:F46",
            sheet_title_evidence_terms=None,
        ),
        required_evidence_terms=["Source Table Variable Name", "Variable Description", "iPSC"]
    )
    ok, msg = probe_validator.validate_atomic_claim(probe_claim)
    assert not ok
    assert "not found inside approved cell range" in msg.lower()
    assert "ipsc" in msg.lower()


def test_dti_roi_scientific_language_and_claims(selection_data):
    """DTI ROI source entry must strictly describe manual substantia nigra / cerebral peduncle ROIs with zero tractography claims (SG-02)."""
    file_map = {r["relative_path"]: r for r in selection_data["file_selection_matrix"]}
    assert "dti/DTI_Regions_of_Interest_09Nov2026.csv" in file_map
    dti_row = file_map["dti/DTI_Regions_of_Interest_09Nov2026.csv"]

    assert dti_row["information_content"] == "DTI Region of Interest (ROI) Fractional Anisotropy & Diffusivity"
    assert "substantia nigra" in dti_row["file_specific_rationale"].lower()
    assert "cerebral peduncle" in dti_row["file_specific_rationale"].lower()

    # Zero occurrences of tractograph in any field for DTI ROI
    for field_name in ("information_content", "file_specific_rationale", "documentation_source"):
        val = dti_row.get(field_name, "")
        assert "tractograph" not in val.lower(), f"Tractography claim found in DTI ROI {field_name}: '{val}'"

    # Also check DTI methods PDF documentation entry
    dti_pdf_row = file_map["dti/PPMI_DTI_ROI_Methods_20160915.pdf"]
    for field_name in ("information_content", "file_specific_rationale"):
        val = dti_pdf_row.get(field_name, "")
        assert "tractograph" not in val.lower(), f"Tractography claim found in DTI methods {field_name}: '{val}'"


def test_visit_and_longitudinal_evidence_semantics(selection_data, auditor):
    """Visit count must strictly equal non-null event records; high-cardinality session fields must not produce high milestone tiers (SG-11)."""
    file_map = {r["relative_path"]: r for r in selection_data["file_selection_matrix"]}
    sheet_map = {r["relative_path"]: r for r in selection_data["worksheet_selection_matrix"]}

    # Invariant 1: Synthetic test fixture where row count differs from non-null event count
    mock_file = {
        "relative_path": "mock_domain/Mock_Table_09Nov2026.csv",
        "file_name": "Mock_Table_09Nov2026.csv",
        "modality": "Clinical",
        "format": "Tabular CSV",
        "sha256": "mock_hash_visit",
        "row_count": 100,
        "column_count": 10,
        "has_patno": True,
        "has_visit": True,
        "null_participant_keys": 0,
        "null_visit_keys": 25,
        "distinct_participants": 50,
        "distinct_visits": 6,
    }
    r, _ = auditor.evaluate_file(mock_file)
    assert r.visit_count == 75, f"Expected visit_count == 75 (100 - 25), got {r.visit_count}"
    assert "75 non-null event records (25 null event keys)" in r.visit_coverage_scope
    assert "75 non-null event records (25 null event keys)" in r.participant_visit_coverage
    assert r.longitudinal_status == "Cross-Sectional (No Within-Participant Longitudinal Follow-up)"

    # Invariant 2: Synthetic test fixture where high-cardinality session field (>50 distinct) produces Session-Level Repeated Observations, NOT High Milestone tier
    mock_session_file = {
        "relative_path": "mock_domain/Mock_Session_09Nov2026.csv",
        "file_name": "Mock_Session_09Nov2026.csv",
        "modality": "Clinical",
        "format": "Tabular CSV",
        "sha256": "mock_hash_session",
        "row_count": 1200,
        "column_count": 10,
        "has_patno": True,
        "has_visit": True,
        "null_participant_keys": 0,
        "null_visit_keys": 0,
        "distinct_participants": 500,
        "distinct_visits": 1160,
    }
    auditor.within_participant_stats[mock_session_file["relative_path"]] = (500, 100)
    r_sess, _ = auditor.evaluate_file(mock_session_file)
    assert r_sess.longitudinal_status == "Session-Level Repeated Observations"
    assert "High (10+ Milestone Visits)" not in r_sess.longitudinal_status
    assert "High (10+ Milestone Visits)" not in r_sess.longitudinal_depth

    # Invariant 3: Synthetic fixture with 10 participants, 10 distinct event codes, and 1 event per participant yields Cross-Sectional (rep=0)
    mock_cross_file = {
        "relative_path": "mock_domain/Mock_Cross_09Nov2026.csv",
        "file_name": "Mock_Cross_09Nov2026.csv",
        "modality": "Clinical",
        "format": "Tabular CSV",
        "sha256": "mock_hash_cross",
        "row_count": 10,
        "column_count": 5,
        "has_patno": True,
        "has_visit": True,
        "null_participant_keys": 0,
        "null_visit_keys": 0,
        "distinct_participants": 10,
        "distinct_visits": 10,
    }
    r_cross, _ = auditor.evaluate_file(mock_cross_file)
    assert r_cross.longitudinal_status == "Cross-Sectional (No Within-Participant Longitudinal Follow-up)"
    assert r_cross.participants_with_repeated_events == 0

    # Invariant 4: Real PPMI table with null event keys (MRI acquisition metadata: 8,779 rows with 1,931 null EVENT_ID)
    mri_acq = file_map["MRI Acquisition/Xing_Core_Lab_-_MRI_acquisition_metadata_09Nov2026.csv"]
    assert mri_acq["row_count"] == 8779
    assert mri_acq["null_key_counts"]["null_event_id"] == 1931
    assert mri_acq["visit_count"] == 6848, f"Expected visit_count == 6848 (8779 - 1931), got {mri_acq['visit_count']}"
    assert "6,848 non-null event records (1,931 null event keys)" in mri_acq["visit_coverage_scope"]
    assert mri_acq["longitudinal_status"] == "Potential Longitudinal Structure — Ambiguous Grain / Event Semantics Unverified"

    # Invariant 5: Real PPMI table with high-cardinality session/date identifier (Cognitive Testing Session)
    cog_sess = file_map["other cognitive/Cognitive_Activities_Testing_Session_09Nov2026.csv"]
    assert cog_sess["row_count"] == 1657
    assert cog_sess["null_key_counts"]["null_event_id"] == 462
    assert cog_sess["visit_count"] == 1195, f"Expected visit_count == 1195 (1657 - 462), got {cog_sess['visit_count']}"
    assert cog_sess["distinct_raw_event_values"] == 1160
    assert cog_sess["longitudinal_status"] == "Session-Level Repeated Observations"
    assert "High (10+ Milestone Visits)" not in cog_sess["longitudinal_status"]

    # Invariant 6: Real PPMI table with verified repeated observations (Dopamine_Imaging)
    dopa = file_map["DATSCAN/Dopamine_Imaging_09Nov2026.csv"]
    assert dopa["participants_with_repeated_events"] == 3903
    assert dopa["longitudinal_status"] == "Verified Repeated Within-Participant Observations Present"
    assert dopa["longitudinal_participant_denominator_name"] == "Observed participants with non-null event records"
    assert dopa["longitudinal_participant_denominator_count"] == dopa["observed_distinct_ids"]

    # Invariant 7: Real PPMI curated cut with verified repeated observations (sheet 20260810)
    cur_sheet = sheet_map["curated_datacuts/PPMI_Curated_Data_Cut_Public_20260810(1).xlsx -> [20260810]"]
    assert cur_sheet["participants_with_repeated_events"] == 3916
    assert cur_sheet["longitudinal_status"] == "Verified Repeated Within-Participant Observations Present"

    # Invariant 8: Decoupled event semantics - zero units assert unverified scheduled milestones (SG-11)
    all_units = selection_data["file_selection_matrix"] + selection_data["worksheet_selection_matrix"]
    for r in all_units:
        assert "Verified Scheduled Milestone Codes" not in r["event_semantics"], f"Unit {r['relative_path']} overstates event semantics: {r['event_semantics']}"

    # Invariant 9: Standard EVENT_ID tables report unverified schedule semantics (SG-11)
    assert dopa["event_semantics"] == "Raw EVENT_ID values — schedule semantics unverified"

    # Invariant 10: Alternative event column CLINICAL_EVENT detected via file_schemas -> columns (SG-11)
    biospec_files = [
        "biospecimen/IUSM_ASSAY_DEV_CATALOG_09Nov2026.csv",
        "biospecimen/IUSM_BIOSPECIMEN_CELL_CATALOG_09Nov2026.csv",
        "biospecimen/IUSM_CATALOG_09Nov2026.csv",
        "biospecimen/iPSC_Catalog_Metadata_09Nov2026.csv",
    ]
    for b_rel in biospec_files:
        b_row = file_map[b_rel]
        assert b_row["event_key_column"] == "CLINICAL_EVENT", f"Expected CLINICAL_EVENT in {b_rel}, got {b_row['event_key_column']}"
        assert b_row["event_semantics"] == "Ambiguous / Unverified Event Semantics"

    # Invariant 11: High-frequency continuous sensor repetition (30 of 32 participants) (SG-11)
    sensor_rel = "digital_Sensor/Roche_PD_Monitoring_App_v2_data_09Nov2026.csv"
    sensor_row = file_map[sensor_rel]
    assert sensor_row["observed_distinct_ids"] == 32
    assert sensor_row["participants_with_non_null_events"] == 32
    assert sensor_row["participants_with_repeated_events"] == 30
    assert "30 with repeated assessment dates" in sensor_row["visit_coverage_scope"]
    assert sensor_row["event_key_column"] == "QRSDTM (Assessment Timestamp)"
    assert sensor_row["event_semantics"] == "Continuous Telemetry / Session Timestamps (Schedule Semantics Unverified)"

    # Invariant 12: Dynamic worksheet repetition recomputed at runtime (SG-11: zero hardcoding)
    assert auditor.within_participant_stats["curated_datacuts/PPMI_Curated_Data_Cut_Public_20260810(1).xlsx -> [20260810]"] == (5019, 3916)
    assert auditor.within_participant_stats["MR Analysis Results/PPMI_rs-fMRI_Data-and-Methods/PPMI_fs-fMRI_dataReport_spreadsheet_FINAL_20191121.xlsx -> [PPMI_rsfMRI_09052019]"] == (194, 121)


def test_modality_aware_routing_invariants(selection_data):
    """Imaging and biospecimen sources must NEVER route to eda_clinical.ipynb or get clinical scale roles (SG-02)."""
    matrix_files = selection_data["file_selection_matrix"]

    for row in matrix_files:
        domain = row["domain_folder"]
        nb = row["target_notebook"]
        rel = row["relative_path"]
        info = row["information_content"]

        # Invariant 1: Imaging files must route to eda_neuroimaging.ipynb (or 00_dataset_overview.ipynb for docs)
        if domain in ("DATSCAN", "dti", "MR Analysis Results", "MRI Technical Information", "PET"):
            assert nb in ("eda_neuroimaging.ipynb", "00_dataset_overview.ipynb"), f"Imaging file {rel} routed to {nb}"

        # Invariant 2: Biospecimen files must route to eda_biospecimen.ipynb (or 00_dataset_overview.ipynb for docs)
        if domain == "biospecimen":
            assert nb in ("eda_biospecimen.ipynb", "00_dataset_overview.ipynb"), f"Biospecimen file {rel} routed to {nb}"
            assert "Clinical Assessment Scale" not in info, f"Biospecimen file {rel} has clinical scale role: {info}"

    # Invariant 3: All 5 scientifically plausible analysis tables must be in Needs Review
    file_map = {r["relative_path"]: r for r in matrix_files}
    for rel_path, spec in SCIENTIFICALLY_PLAUSIBLE_ANALYSIS_PATHS.items():
        assert rel_path in file_map, f"Missing plausible analysis file: {rel_path}"
        r = file_map[rel_path]
        assert r["provisional_recommendation"] == SelectionCategory.NEEDS_REVIEW.value
        assert r["unresolved_action"] == spec["unresolved_action"]
        assert r["target_notebook"] == spec["target_notebook"]


def test_json_csv_lossless_parity_all_57_fields(repo_root, selection_data, auditor):
    """CSV must provide a lossless flat representation of ALL 57 fields for all 183 decision units (SG-06, SG-07, SG-11)."""
    csv_path = repo_root / "EDA" / "outputs" / "reports" / "dataset_selection_matrix.csv"
    assert csv_path.exists(), "Missing dataset_selection_matrix.csv"

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        csv_rows = list(reader)

    assert len(csv_rows) == 183, f"Expected 183 rows in CSV, got {len(csv_rows)}"
    assert len(reader.fieldnames) == 57, f"Expected exactly 57 fields in CSV, got {len(reader.fieldnames)}"

    json_units = selection_data["file_selection_matrix"] + selection_data["worksheet_selection_matrix"]
    assert len(json_units) == 183

    # Build row from engine to verify exact lossless serialization across all 57 fields
    file_rows, sheet_rows = auditor.build_matrix()
    expected_rows = file_rows + sheet_rows
    expected_map = {r.relative_path: r.to_csv_dict() for r in expected_rows}

    for crow in csv_rows:
        rel_path = crow["relative_path"]
        assert rel_path in expected_map, f"CSV path {rel_path} not in expected engine rows"
        erow = expected_map[rel_path]

        for field_name in reader.fieldnames:
            cval = crow[field_name]
            eval_val = str(erow[field_name]) if erow[field_name] is not None else ""
            assert cval == eval_val, f"Field '{field_name}' mismatch for {rel_path}: CSV='{cval}' vs Expected='{eval_val}'"


def test_cross_artifact_counts_reconcile_globally(repo_root, selection_data):
    """Category totals and distributions must reconcile with zero discrepancy across all artifacts (SG-04)."""
    summary = selection_data["summary_by_provisional_recommendation"]

    # Source files: 11 Primary, 132 Supporting, 4 Excluded, 30 Needs Review = 177
    assert summary["Primary EDA"] == 11
    assert summary["Supporting"] == 132
    assert summary["Excluded from detailed EDA"] == 4
    assert summary["Needs Review"] == 30

    # Markdown report reconciliation
    report_path = repo_root / "EDA" / "outputs" / "reports" / "dataset_selection_report.md"
    assert report_path.exists()
    content = report_path.read_text(encoding="utf-8")
    assert "| **Primary EDA** | **11** |" in content
    assert "| **Supporting** | **132** |" in content
    assert "| **Excluded from detailed EDA** | **4** |" in content
    assert "| **Needs Review** | **30** |" in content
    assert "177 source files" in content

    # Decisions document reconciliation
    decisions_path = repo_root / "docs" / "dataset_selection_decisions.md"
    assert decisions_path.exists()
    dec_content = decisions_path.read_text(encoding="utf-8")
    assert "Provisional Candidate Exclusions" in dec_content
    assert "Codex Review & Human Sign-off Pending" in dec_content
    assert "Awaiting Codex review and researcher sign-off" in dec_content
    assert "| **Primary EDA** | **11** |" in dec_content
    assert "| **Supporting** | **132** |" in dec_content
    assert "| **Excluded from detailed EDA** | **4** |" in dec_content
    assert "| **Needs Review** | **30** |" in dec_content


def test_notebook_selection_evidence_completeness(repo_root):
    """Notebook Table 12.5 must contain EXACTLY 183 data rows and ALL 57 required column headers (SG-05, SG-11)."""
    nb_path = repo_root / "00_dataset_overview.ipynb"
    assert nb_path.exists()

    with open(nb_path, "r", encoding="utf-8") as f:
        nb = json.load(f)

    # Locate Table 12.5
    table_found = False
    for cell in nb.get("cells", []):
        for out in cell.get("outputs", []):
            html = "".join(out.get("data", {}).get("text/html", ""))
            if "Table 12.5" in html:
                table_found = True
                import re
                tbody = re.search(r"<tbody>(.*?)</tbody>", html, re.DOTALL)
                assert tbody is not None, "Table 12.5 missing <tbody>"
                data_rows = re.findall(r"<tr>", tbody.group(1))
                assert len(data_rows) == 183, f"Expected exactly 183 data rows in Table 12.5, got {len(data_rows)}"

                # Check all 57 column headers
                required_headers = [
                    "Relative Path", "File Name", "Sheet Name", "Domain Folder", "Modality",
                    "Format", "SHA-256", "Physical Read Status", "Row Count", "Column Count",
                    "Worksheet Count", "Observation Grain", "Grain Status", "Candidate Primary Keys",
                    "Duplicate Key Status", "Duplicate Rows Count", "Observed Distinct IDs",
                    "Participant Count", "Eligible Cohort Denominator", "Participant Coverage (%)",
                    "Event Key Column", "Event Semantics", "Non-Null Event Record Count", "Null Event Record Count",
                    "Distinct Raw Event Values", "Participants With Non-Null Events", "Participants With Repeated Events",
                    "Longitudinal Participant Denominator Name", "Longitudinal Participant Denominator Count", "Longitudinal Status",
                    "Visit Count", "Distinct Visits Count", "Visit Coverage Scope", "Longitudinal Depth",
                    "Null Rate (%)", "Null Key Counts", "Documentation Status", "Documentation Source",
                    "Quality Concerns", "Clinical & Scientific Relevance", "Information Content",
                    "Participant & Visit Coverage", "Longitudinal Usefulness", "Data Quality & Interpretability",
                    "Redundancy Evidence", "Multimodal Integration Value", "Exact Comparator Source",
                    "Proposed Category", "Provisional Recommendation", "File-Specific Rationale",
                    "Primary EDA Priority", "Unresolved Action", "Target Notebook", "Target Notebooks",
                    "Reviewer", "Decision Date", "Approval Status",
                ]
                import html as html_lib
                unescaped_html = html_lib.unescape(html)
                for req_col in required_headers:
                    assert req_col in unescaped_html, f"Missing required column in Table 12.5: {req_col}"
                break
        if table_found:
            break

    assert table_found, "Table 12.5 not found in executed notebook outputs"

    assert table_found, "Table 12.5 not found in executed notebook outputs"


def test_raw_file_hashes_remain_unchanged_all_177_sources(repo_root, canonical_inventory):
    """Raw source files on disk must remain strictly immutable across all 177 files (SG-07)."""
    sources = canonical_inventory["source_files"]
    assert len(sources) == 177

    for item in sources:
        full_path = repo_root / item["relative_path"]
        assert full_path.exists(), f"Source file missing from disk: {item['relative_path']}"
        h = hashlib.sha256(full_path.read_bytes()).hexdigest()
        assert h == item["sha256"], f"Raw source file modified! {item['relative_path']}"


def test_privacy_guard_validates_selection_artifacts_and_notebook(repo_root):
    """All exported selection gate artifacts and executed notebook must pass PrivacyGuard (SG-09)."""
    pg = PrivacyGuard()

    # 1. JSON matrix
    json_path = repo_root / "EDA" / "outputs" / "reports" / "dataset_selection_matrix.json"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    pg.assert_no_participant_records(data, context="dataset_selection_matrix.json")

    # 2. CSV matrix
    csv_path = repo_root / "EDA" / "outputs" / "reports" / "dataset_selection_matrix.csv"
    csv_text = csv_path.read_text(encoding="utf-8")
    pg.assert_no_raw_text_leakage(csv_text, context="dataset_selection_matrix.csv")

    # 3. Markdown report
    report_path = repo_root / "EDA" / "outputs" / "reports" / "dataset_selection_report.md"
    report_text = report_path.read_text(encoding="utf-8")
    pg.assert_no_participant_records(report_text, context="dataset_selection_report.md")

    # 4. Decisions document
    decisions_path = repo_root / "docs" / "dataset_selection_decisions.md"
    decisions_text = decisions_path.read_text(encoding="utf-8")
    pg.assert_no_participant_records(decisions_text, context="dataset_selection_decisions.md")

    # 5. Executed notebook
    nb_path = repo_root / "00_dataset_overview.ipynb"
    with open(nb_path, "r", encoding="utf-8") as f:
        nb_data = json.load(f)
    pg.validate_notebook_outputs(nb_data)


def test_repository_root_discovery_portability(repo_root):
    """Repository root must resolve deterministically from repo root or EDA/ directory (SG-12)."""
    import os
    from ppmi_pipeline.validation.selection import resolve_repo_root

    # 1. Direct call with explicit root
    assert resolve_repo_root(repo_root) == repo_root

    # 2. Call with None from current repo root
    assert resolve_repo_root(None) == repo_root

    # 3. Simulate CWD inside EDA/
    eda_dir = repo_root / "EDA"
    orig_cwd = Path.cwd()
    try:
        os.chdir(eda_dir)
        assert resolve_repo_root(None) == repo_root
    finally:
        os.chdir(orig_cwd)
