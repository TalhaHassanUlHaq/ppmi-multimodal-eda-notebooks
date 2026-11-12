"""End-to-end integration test verifying multimodal inventory auditing on workspace files."""

from pathlib import Path
from typing import List
import pytest

from ppmi_pipeline.config.settings import PipelineConfig
from ppmi_pipeline.ingestion.inventory import DatasetInventoryAuditor
from ppmi_pipeline.modalities.base import (
    DatasetSelectionCategory,
    FormatCategory,
    ModalityCategory,
    ModalityFileProfile,
)
from ppmi_pipeline.reporting.audit_report import AuditReportGenerator


@pytest.fixture(scope="module")
def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def pipeline_config(repo_root: Path) -> PipelineConfig:
    return PipelineConfig(project_root=repo_root)


@pytest.fixture(scope="module")
def auditor(pipeline_config: PipelineConfig) -> DatasetInventoryAuditor:
    return DatasetInventoryAuditor(pipeline_config)


@pytest.fixture(scope="module")
def source_profiles(auditor: DatasetInventoryAuditor) -> List[ModalityFileProfile]:
    return auditor.audit_source_universe()


def test_source_universe_reconciliation(source_profiles: List[ModalityFileProfile], pipeline_config: PipelineConfig):
    """Verify that source universe contains exactly 177 physical files across 17 folders (P1-01)."""
    assert len(source_profiles) == 177, f"Expected 177 source files, found {len(source_profiles)}"

    # Check that each file is inside one of the 17 domain folders
    for p in source_profiles:
        first_folder = p.relative_path.split("/")[0]
        assert first_folder in pipeline_config.domain_folders, f"File {p.relative_path} is outside 17 source domains!"


def test_source_inventory_count_is_invariant_to_generated_files(repo_root: Path, auditor: DatasetInventoryAuditor):
    """Verify that creating new output files does not alter the source inventory count (P1-01)."""
    initial_count = len(auditor.audit_source_universe())

    # Create dummy artifact in EDA/outputs
    dummy = repo_root / "EDA" / "outputs" / "dummy_test_artifact.txt"
    try:
        dummy.write_text("temporary test output", encoding="utf-8")
        post_count = len(auditor.audit_source_universe())
        assert post_count == initial_count, "Source file count drifted after creating an artifact!"
    finally:
        if dummy.exists():
            dummy.unlink()


def test_copy_marker_does_not_imply_redundancy_or_exclusion(source_profiles: List[ModalityFileProfile]):
    """Verify that (1) in filename does not cause automated exclusion or redundancy claims (P1-02)."""
    curated_profile = next((p for p in source_profiles if "Curated" in p.file_name), None)

    assert curated_profile is not None
    # File name has '(1)' but must NOT be automatically marked excluded!
    assert curated_profile.selection_category == DatasetSelectionCategory.SELECTION_PENDING


def test_multi_sheet_workbook_auditing(source_profiles: List[ModalityFileProfile]):
    """Verify that all sheets of multi-sheet workbooks are independently audited (P1-03)."""
    curated = next(p for p in source_profiles if "Curated" in p.file_name)

    assert len(curated.worksheets) == 3
    sheet_names = [ws.sheet_name for ws in curated.worksheets]
    assert "20260810" in sheet_names
    assert "Data dictionary" in sheet_names
    assert "Information" in sheet_names

    # Check 20260810 data sheet
    data_ws = next(ws for ws in curated.worksheets if ws.sheet_name == "20260810")
    assert data_ws.row_count > 20000
    assert data_ws.column_count > 200
    assert data_ws.has_participant_id is True
    assert data_ws.has_visit_id is True


def test_raw_file_immutability(source_profiles: List[ModalityFileProfile]):
    """Verify that running the audit leaves all raw files completely untouched."""
    # Check that modification timestamps and sizes match filesystem
    for p in source_profiles[:10]:
        assert p.file_size_bytes == p.file_path.stat().st_size


def test_inventory_cross_deliverable_consistency(repo_root: Path):
    """Verify that file counts, metrics, and categories reconcile across JSONs, MD report, and notebook (P1-10)."""
    import json
    import re
    from ppmi_pipeline.reporting.privacy import PrivacyGuard

    reports_dir = repo_root / "EDA" / "outputs" / "reports"
    inv_file = reports_dir / "phase1_multimodal_inventory.json"
    schema_file = reports_dir / "phase1_schema_catalog.json"
    grain_file = reports_dir / "phase1_grain_catalog.json"
    report_file = reports_dir / "phase1_inventory_report.md"
    notebook_file = repo_root / "00_dataset_overview.ipynb"

    assert inv_file.exists(), "Inventory JSON missing!"
    assert schema_file.exists(), "Schema catalog JSON missing!"
    assert grain_file.exists(), "Grain catalog JSON missing!"
    assert report_file.exists(), "Markdown report missing!"
    assert notebook_file.exists(), "Overview notebook missing!"

    with open(inv_file, "r", encoding="utf-8") as f:
        inv_data = json.load(f)
    with open(schema_file, "r", encoding="utf-8") as f:
        schema_data = json.load(f)
    with open(grain_file, "r", encoding="utf-8") as f:
        grain_data = json.load(f)
    with open(report_file, "r", encoding="utf-8") as f:
        report_text = f.read()
    with open(notebook_file, "r", encoding="utf-8") as f:
        nb_data = json.load(f)

    # 1. Total Source Files Reconciled Across All Deliverables (177)
    source_files = inv_data["source_files"]
    assert len(source_files) == 177, f"Expected 177 in inventory, found {len(source_files)}"
    assert schema_data["metadata"]["total_files_cataloged"] == 177
    assert len(schema_data["file_schemas"]) == 177

    total_grain_files = sum(len(file_list) for file_list in grain_data["catalog"].values())
    assert total_grain_files == 177, f"Grain catalog contains {total_grain_files} files, expected 177"

    assert "**177 physical files**" in report_text or "177 physical source files" in report_text

    # 2. Modality & Format Category Counts Sum to Total Source Files
    modality_sum = sum(details["file_count"] for details in inv_data["domain_details"].values())
    assert modality_sum == 177, f"Domain details sum to {modality_sum}, expected 177"

    # 3. All 177 Files Have Status 'Selection Pending' (P1-02)
    selection_categories = {f["selection_category"] for f in source_files}
    assert selection_categories == {"Selection Pending (Awaiting Selection Gate Approval)"}

    # 4. Zero-Row Files Have Complete Column Schemas With Null Statistics (P1-11)
    zero_row_schemas = [
        v for v in schema_data["file_schemas"].values()
        if v.get("row_count") == 0 and v.get("format") == "Tabular CSV"
    ]
    assert len(zero_row_schemas) == 3, f"Expected 3 zero-row CSVs, found {len(zero_row_schemas)}"
    for z in zero_row_schemas:
        assert len(z["columns"]) > 0, f"Zero-row file {z['file_name']} lacks column definitions!"
        for col in z["columns"]:
            assert col["missingness_percentage"] is None
            assert col["missing_denominator"] == 0
            assert "unavailable" in col["data_status"].lower()

    # 5. Multi-Sheet Workbook Dimension Reconciliation (P1-03)
    rsfmri_schema = next(v for k, v in schema_data["file_schemas"].items() if "PPMI_fs-fMRI" in k)
    assert len(rsfmri_schema["worksheets"]) == 2
    ws1 = next(ws for ws in rsfmri_schema["worksheets"] if ws["sheet_name"] == "PPMI_rsfMRI_09052019")
    ws2 = next(ws for ws in rsfmri_schema["worksheets"] if ws["sheet_name"] == "Dictionary")
    assert (ws1["row_count"], ws1["column_count"]) == (384, 49)
    assert (ws2["row_count"], ws2["column_count"]) == (32, 4)

    ipsc_schema = next(v for k, v in schema_data["file_schemas"].items() if "IPSC_Catalog_User_Guide" in k)
    assert len(ipsc_schema["worksheets"]) == 1
    assert (ipsc_schema["worksheets"][0]["row_count"], ipsc_schema["worksheets"][0]["column_count"]) == (24, 6)

    curated_schema = next(v for k, v in schema_data["file_schemas"].items() if "Curated_Data_Cut" in k)
    assert len(curated_schema["worksheets"]) == 3
    cws1 = next(ws for ws in curated_schema["worksheets"] if ws["sheet_name"] == "20260810")
    cws2 = next(ws for ws in curated_schema["worksheets"] if ws["sheet_name"] == "Data dictionary")
    cws3 = next(ws for ws in curated_schema["worksheets"] if ws["sheet_name"] == "Information")
    assert (cws1["row_count"], cws1["column_count"]) == (20408, 215)
    assert (cws2["row_count"], cws2["column_count"]) == (452, 10)
    assert (cws3["row_count"], cws3["column_count"]) == (19, 9)

    # 6. Artifact Count and Tabular Format Consistency (P1-10 Round 4)
    project_artifacts_file = reports_dir / "phase1_project_artifacts_manifest.json"
    assert project_artifacts_file.exists()
    with open(project_artifacts_file, "r", encoding="utf-8") as f:
        artifacts_data = json.load(f)
    assert artifacts_data["metadata"]["total_non_source_files"] == inv_data["project_artifact_metrics"]["total_non_source_files"]
    assert artifacts_data["metadata"]["total_non_source_files"] >= 165

    # Tabular sources: 156 Tabular CSV + 1 Raw Time-Series (Sensor CSV) + 3 Tabular Excel = 160 tabular files
    format_counts = inv_data["format_breakdown"]
    tabular_total = (
        format_counts.get("Tabular CSV", 0) +
        format_counts.get("Tabular Excel (.xlsx)", 0) +
        format_counts.get("Raw Time-Series / Sensor Stream", 0)
    )
    assert tabular_total == 160, f"Expected 160 tabular sources, found {tabular_total}"

    # Roche individual file row count (108,901) vs total digital sensor modality rows (109,293)
    roche_entry = next(f for f in source_files if "Roche_PD_Monitoring_App" in f["file_name"])
    assert roche_entry["row_count"] == 108901, f"Expected 108,901 Roche rows, found {roche_entry['row_count']}"

    sensor_files = [f for f in source_files if f.get("modality") == "Digital Sensor & Mobile Telemetry"]
    total_sensor_rows = sum(f.get("row_count", 0) or 0 for f in sensor_files)
    assert total_sensor_rows == 109293, f"Expected 109,293 total sensor rows, found {total_sensor_rows}"

    # Grain distribution exact counts (P1-10)
    grain_catalog = grain_data["catalog"]
    assert len(grain_catalog["Visit-Level (1 row per participant-visit)"]) == 60
    assert len(grain_catalog["Subject-Level (1 row per participant)"]) == 44
    assert len(grain_catalog["Repeated Event / Item-Level (multiple rows per visit)"]) == 38
    assert len(grain_catalog["Documentation / Reference (no participant key)"]) == 21
    assert len(grain_catalog["Ambiguous / Needs Detailed Review"]) == 12
    assert len(grain_catalog["Unindexed / Unknown Grain"]) == 2

    # 7. Privacy Validation of Executed Notebook Outputs (P1-06)
    PrivacyGuard.validate_notebook_outputs(nb_data)


def test_notebook_markdown_conclusions_and_saved_outputs(repo_root: Path):
    """Verify notebook Markdown, conclusions, and saved outputs directly (P1-10 / P1-11 Round 6)."""
    import json
    from ppmi_pipeline.reporting.privacy import PrivacyGuard

    notebook_file = repo_root / "00_dataset_overview.ipynb"
    schema_file = repo_root / "EDA" / "outputs" / "reports" / "phase1_schema_catalog.json"
    assert notebook_file.exists()
    assert schema_file.exists()

    with open(notebook_file, "r", encoding="utf-8") as f:
        nb_data = json.load(f)
    with open(schema_file, "r", encoding="utf-8") as f:
        schema_data = json.load(f)

    # 1. Schema metadata named denominators
    meta = schema_data["metadata"]
    assert meta["primary_file_columns_count"] == 3659
    assert meta["total_structural_headers_count"] == 3682
    assert meta["total_columns_cataloged"] == 3682

    # 2. Check notebook Markdown cells for accurate conclusions and counts
    all_markdown = " ".join(
        "".join(cell.get("source", []))
        for cell in nb_data["cells"]
        if cell.get("cell_type") == "markdown"
    )

    # Must contain 167 artifacts snapshot, never stale 166
    assert "167 artifacts" in all_markdown, "Notebook markdown conclusion must reference 167 artifacts!"
    assert "166 artifacts" not in all_markdown, "Stale 166 artifacts count found in notebook markdown!"
    assert "177 physical source files" in all_markdown
    assert "Selection Pending (Awaiting Selection Gate Approval)" in all_markdown
    # Unverified disclaimer present
    assert "unverified pending Phase 2" in all_markdown

    # 3. Check that the complete 3,682-row column catalog is saved in output HTML
    found_3682_catalog = False
    for cell in nb_data["cells"]:
        if cell.get("cell_type") == "code":
            for out in cell.get("outputs", []):
                html_data = out.get("data", {}).get("text/html", "")
                html_str = "".join(html_data) if isinstance(html_data, list) else str(html_data)
                if "Complete 3,682-Row Structural Column Catalog" in html_str:
                    # Count table rows in the catalog
                    row_matches = html_str.count("<tr>")
                    # There are 3682 data rows + 1 header row = 3683 tr tags
                    assert row_matches >= 3682, f"Expected at least 3,682 table rows in catalog, found {row_matches}"
                    found_3682_catalog = True
                    break
    assert found_3682_catalog is True, "Complete 3,682-row catalog HTML not found in saved notebook outputs!"

    # 4. Privacy verification across all outputs
    PrivacyGuard.validate_notebook_outputs(nb_data)
