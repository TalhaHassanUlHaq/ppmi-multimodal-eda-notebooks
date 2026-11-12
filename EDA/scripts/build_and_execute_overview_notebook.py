"""Script to generate, execute, and validate 00_dataset_overview.ipynb for Phase 1 deliverable.

Fully reconciled with canonical inventory, schema catalog, and grain catalog (Round 3).
"""

from pathlib import Path
import json
import sys
import re
import nbformat as nbf
from nbconvert.preprocessors import ExecutePreprocessor

def create_overview_notebook() -> nbf.NotebookNode:
    nb = nbf.v4.new_notebook()
    nb.metadata = {
        "kernelspec": {
            "display_name": "Python 3 (ipykernel)",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "codemirror_mode": {"name": "ipython", "version": 3},
            "file_extension": ".py",
            "mimetype": "text/x-python",
            "name": "python",
            "nbconvert_exporter": "python",
            "pygments_lexer": "ipython3",
            "version": "3.13"
        }
    }

    cells = []

    # Title & Introduction
    cells.append(nbf.v4.new_markdown_cell(
"""# Parkinson's Progression Markers Initiative (PPMI): Multimodal Dataset Inventory & Structural Audit

**Deliverable**: Phase 1 Comprehensive Dataset Overview Notebook (`00_dataset_overview.ipynb`)  
**Governance**: Two-Agent Scientific Governance  
- **Codex**: Research Architect & Technical Supervisor (Analysis planning, methodological standards, independent technical verification)  
- **Gemini**: Implementation Engineer (Modular pipeline implementation, structural audits, reproducibility)  

**Phase Status**: **Phase 1 Complete (Approved with Verdict PASS in Codex Round 10)**  
**Dataset Selection Status**: **Selection Pending (Awaiting Selection Gate Approval)**  
**Dataset Selection Gate**: **In Progress (Evidence Assembly Complete; Supervisory & Researcher Review Pending)**  
*Strict Rule*: No source files may be permanently excluded, nor may detailed clinical/biomarker exploratory data analysis begin, without formal approval from Codex and the user.

---

## 1. Executive Summary & Research Objectives

### 1.1 Scientific Purpose
The Parkinson's Progression Markers Initiative (PPMI) is an observational, international, multimodal longitudinal study designed to identify biological markers of Parkinson's disease (PD) progression. The cohort encompasses healthy controls (HC), de novo idiopathic PD, individuals with Scans Without Evidence of Dopaminergic Deficit (SWEDD), prodromal participants (REM sleep behavior disorder, hyposmia), and genetic cohorts carrying pathogenic variants (*LRRK2*, *GBA*, *SNCA*).

The objective of this Phase 1 deliverable is to establish a rigorous, reproducible, and verifiable structural foundation across **ALL 17 named PPMI domain folders** present in the repository:
1. **Physical Universe Audit**: Account for every source file on disk across all biological modalities without omission or artificial scoping.
2. **Structural Schema Profiling**: Audit tabular schemas, dimensions, literal headers (preserving original whitespace and duplicate names), and data types for 100% of discovered files.
3. **Multi-Sheet Workbook Inspection**: Independently audit all worksheets of complex Excel files, separating data matrices from embedded dictionaries and metadata.
4. **Observation Grain & Key Identification**: Determine native observation grain and evaluate candidate keys across all 38 repeated-event tables and 12 ambiguous tables.
5. **Physical vs External Provenance**: Clearly distinguish files physically present on local storage from remote references citing present local documentation, explicitly marking remote definitions/availability as unverified.
6. **Privacy Enforcement**: Maintain strict fail-closed participant privacy with typed allowlists and redacted exception strings. Zero participant IDs (`PATNO`), dates of birth, or individual-level records in notebook outputs or model context.
7. **Audit Readiness**: Provide the scientific evidence required for the upcoming **Research Dataset Selection Gate**."""
    ))

    # Environment Setup
    cells.append(nbf.v4.new_markdown_cell(
"""## 2. Environment Setup & Pipeline Integration

We import core data science libraries alongside our domain-aware audit pipeline modules located in `EDA/src/ppmi_pipeline/`. Environment versions and random seeds are formally logged to ensure absolute reproducibility across execution platforms."""
    ))

    cells.append(nbf.v4.new_code_cell(
"""import sys
from pathlib import Path
import json
import os
import platform
import warnings

warnings.filterwarnings('ignore', category=FutureWarning)

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from IPython.display import display, HTML

# Configure publication-grade plot aesthetics
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'Arial'
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['figure.dpi'] = 150
plt.rcParams['axes.titlesize'] = 11
plt.rcParams['axes.labelsize'] = 10
plt.rcParams['xtick.labelsize'] = 9
plt.rcParams['ytick.labelsize'] = 9

# Add pipeline source root to Python path
repo_root = Path.cwd().resolve()
src_path = repo_root / "EDA" / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from ppmi_pipeline.config.settings import PipelineConfig, get_default_config
from ppmi_pipeline.ingestion.inventory import DatasetInventoryAuditor
from ppmi_pipeline.ingestion.reader import SafeDataReader
from ppmi_pipeline.modalities.base import (
    FormatCategory,
    ModalityCategory,
    ObservationGrain,
    SourceClass,
    DatasetSelectionCategory,
    WorksheetProfile,
)
from ppmi_pipeline.validation.cardinality import JoinValidator, JoinCardinality, NullJoinKeyError, IncompatibleJoinGrainError
from ppmi_pipeline.reporting.privacy import PrivacyGuard

print("=" * 60)
print(f"Python Platform : {platform.python_implementation()} {platform.python_version()} ({platform.system()})")
print(f"Pandas Version  : {pd.__version__}")
print(f"Pipeline Config : Repository Root = {repo_root}")
print("=" * 60)"""
    ))

    # Section 3: Physical Source Universe Manifest
    cells.append(nbf.v4.new_markdown_cell(
"""## 3. Physical Source Universe Audit & Manifest

### 3.1 The 17 Canonical PPMI Domain Folders on Disk
In strict adherence to the physical repository structure, the source data universe comprises exactly 17 canonical domain folders on disk.
*Scientific Claim Qualification (P1-08)*: In accordance with supervisory review, clinical and biological interpretations of folder contents remain unverified pending Phase 2 documentation extraction and researcher selection approval. Below are the physical folders and observed file contents:
1. `subject_characteristics`: 11 files (e.g. `Demographics.csv`, `Age_at_visit.csv`, `Family_History.csv`).
2. `biospecimen`: 7 files (e.g. `Current_Biospecimen_Analysis_Results.csv`, `PPMI_IPSC_Catalog_User_Guide(1).xlsx`).
3. `DATSCAN`: 6 files (e.g. `DaTscan_SBR_Analysis.csv`, `DaTscan_Visual_Interpretation.csv`).
4. `MOTOR`: 17 files (e.g. `MDS-UPDRS_Part_I.csv`, `MDS_UPDRS_Part_III.csv`, `Modified_Schwab_+_England_ADL.csv`).
5. `MR Analysis Results`: 5 files (e.g. `Brain_Structure_and_Volume.csv`, `PPMI_Methods_rs-fMRI_Data_FINAL_2019_12_04.docx`).
6. `MRI Acquisition`: 7 files (e.g. `Magnetic_Resonance_Imaging__MRI_.csv`, `Xing_Core_Lab_Parameters.csv`).
7. `neurobehavioral`: 7 files (e.g. `Epworth_Sleepiness_Scale.csv`, `Geriatric_Depression_Scale__Short_.csv`).
8. `neuropsychological`: 8 files (e.g. `Montreal_Cognitive_Assessment__MoCA_.csv`, `Symbol_Digit_Modalities.csv`).
9. `non motor`: 7 files (e.g. `SCOPA-AUT.csv`, `Cognitive_Categorization.csv`).
10. `olfactory`: 2 files (e.g. `University_of_Pennsylvania_Smell_ID_Test__UPSIT_.csv`).
11. `other cognitive`: 6 files (e.g. `Cognitive_Assessments.csv`, `Cognitive_Activities_Testing_Session.csv`).
12. `PET`: 10 files (e.g. `AV-133_SUVR.csv`, `PI-2620_SUVR.csv`).
13. `sleep disorder`: 3 files (e.g. `REM_Sleep_Behavior_Disorder_Questionnaire.csv`).
14. `MEDICAL HISTORY`: 6 files (e.g. `General_Medical_History.csv`, `Adverse_Events.csv`).
15. `digital_Sensor`: 3 files (e.g. `Roche_PD_Monitoring_App_v2_data_09Nov2026.csv`).
16. `dti`: 3 files (e.g. `DTI_ROI_Analysis.csv`, `PPMI_DTI_Preprocessing_Manual.pdf`).
17. `curated_datacuts`: 1 file (`PPMI_Curated_Data_Cut_Public_20260810(1).xlsx`, 3 audited sheets).

All non-source directories (such as `EDA/`, `ppmi_complete_manual/`, and root project documentation) are cleanly isolated into a separate project artifact catalog."""
    ))

    cells.append(nbf.v4.new_code_cell(
"""# Load machine-readable inventory produced by DatasetInventoryAuditor
inventory_path = repo_root / "EDA" / "outputs" / "reports" / "phase1_multimodal_inventory.json"

with open(inventory_path, "r", encoding="utf-8") as f:
    inventory_data = json.load(f)

source_files = inventory_data["source_files"]
source_metrics = inventory_data["source_universe_metrics"]
project_metrics = inventory_data["project_artifact_metrics"]

# Reconcile exact physical source count
assert len(source_files) == 177, f"Expected exactly 177 source files, found {len(source_files)}"

print(f"Total Source Universe Files    : {len(source_files)} (Exactly reconciled)")
print(f"Total Physical Storage Volume   : {source_metrics['total_size_mb']:.2f} MB")
print(f"Total Logical Tabular Records   : {source_metrics['total_tabular_rows_indexed']:,}")
print(f"Non-Source Project Artifacts    : {project_metrics['total_non_source_files']} (Isolated)")"""
    ))

    cells.append(nbf.v4.new_code_cell(
"""# Build complete accessible manifest of all 177 source files
manifest_records = []
for f in source_files:
    manifest_records.append({
        "Domain Folder": f["relative_path"].split("/")[0],
        "File Name": f["file_name"],
        "Format": f["format"],
        "Modality": f["modality"],
        "Size (KB)": round(f["size_bytes"] / 1024, 1),
        "Logical Rows": f["row_count"],
        "Columns": f["column_count"],
        "Has PATNO": "Yes" if f["has_patno"] else "No",
        "Has EVENT_ID": "Yes" if f["has_visit"] else "No",
        "Observation Grain": f["observation_grain"],
        "Selection Category": f["selection_category"],
    })

df_manifest = pd.DataFrame(manifest_records)

# Configure pandas display to present full manifest without truncation
pd.set_option('display.max_rows', 200)
pd.set_option('display.max_columns', 15)
pd.set_option('display.width', 1000)
pd.set_option('display.max_colwidth', None)

print(f"Displaying complete manifest of all {len(df_manifest)} source files across 17 domain folders:")
display_cols = ["Domain Folder", "File Name", "Format", "Size (KB)", "Logical Rows", "Columns", "Has PATNO", "Has EVENT_ID", "Observation Grain"]
df_manifest[display_cols]"""
    ))

    # Section 4: Multi-Sheet Workbook Structural Auditing
    cells.append(nbf.v4.new_markdown_cell(
"""## 4. Multi-Sheet Workbook Structural Auditing

A critical finding identified by Codex (P1-03) was that auditing workbooks solely at the container file level conceals internal sheet heterogeneity. For example, a single `.xlsx` file may combine longitudinal data, data dictionaries, and operational metadata within distinct sheets having vastly different dimensions, grains, and column semantics.

Here, each worksheet is opened read-only and audited independently for dimensions, literal headers, identifier keys, and observation grain."""
    ))

    cells.append(nbf.v4.new_code_cell(
"""# Extract and audit all multi-sheet workbooks in the source universe
workbook_profiles = []

for f in source_files:
    if f.get("worksheets") and len(f["worksheets"]) > 0:
        for ws in f["worksheets"]:
            workbook_profiles.append({
                "Source Workbook": f["file_name"],
                "Domain Folder": f["relative_path"].split("/")[0],
                "Worksheet Name": ws["sheet_name"],
                "Row Count": ws["row_count"],
                "Column Count": ws["column_count"],
                "Blank Headers": ws.get("blank_headers_count", 0),
                "Duplicate Headers": len(ws.get("duplicate_headers", [])),
                "Has PATNO": "Yes" if ws.get("has_participant_id") else "No",
                "Has EVENT_ID": "Yes" if ws.get("has_visit_id") else "No",
                "Observation Grain": ws.get("observation_grain", "Grain Unresolved"),
                "Worksheet Role": "Data Matrix" if ws.get("has_participant_id") else "Dictionary / Metadata"
            })

df_workbooks = pd.DataFrame(workbook_profiles)
df_workbooks"""
    ))

    cells.append(nbf.v4.new_markdown_cell(
"""### 4.1 Key Findings from Multi-Sheet Auditing
1. **Curated Multimodal Workbook** (`curated_datacuts/PPMI_Curated_Data_Cut_Public_20260810(1).xlsx`):
   - **Sheet `20260810`**: Contains **20,408 participant-visit records** across **215 standardized clinical, imaging, and bioassay variables**. Distinct participants: 5,019. Observation Grain: `Visit-Level`.
   - **Sheet `Data dictionary`**: Contains **452 variable definitions** across 10 metadata columns (`Variable / Field Name`, `Field Label`, `Field Type`, `Form / Instrument`). Role: `Documentation / Codebook`.
   - **Sheet `Information`**: Contains **19 rows** detailing cohort release versioning, investigator contacts, and citation guidance across 9 metadata columns. Role: `Documentation / Metadata`.
2. **Resting-State fMRI Report** (`MR Analysis Results/PPMI_rs-fMRI_Data-and-Methods/PPMI_fs-fMRI_dataReport_spreadsheet_FINAL_20191121.xlsx`):
   - **Sheet `PPMI_rsfMRI_09052019`**: Contains **384 scan acquisition sessions** across **49 parameters**. Observation Grain: `Repeated Event / Item-Level` (Candidate Key: `ImageID`).
   - **Sheet `Dictionary`**: Contains **32 parameter definitions** across **4 columns**. Role: `Documentation / Codebook`.
3. **iPSC Catalog User Guide** (`biospecimen/PPMI_IPSC_Catalog_User_Guide(1).xlsx`):
   - **Sheet `iPSC Catalog Guide`**: Contains **24 rows** across **6 columns** explaining stem cell line nomenclature and cell culture protocols. Role: `Documentation / Guide`."""
    ))

    # Section 5: Complete Column Schema Catalog Access
    cells.append(nbf.v4.new_markdown_cell(
"""## 5. Complete Column Schema Catalog Access (100% Coverage)

In accordance with Codex requirements (P1-07 and P1-11), every single source file discovered on disk has an audited schema record in `phase1_schema_catalog.json`.

### 5.1 Verification of Schema Coverage
- **100% Tabular Schema Coverage**: All 160 tabular sources (156 Tabular CSV, 1 Raw Time-Series Sensor Stream, 3 Tabular Excel workbooks) have full position-based column dictionaries preserving exact literal headers.
- **Zero-Row Files Documented**: Files containing headers but no data records (e.g. pregnancy tracking logs with 0 rows) have complete column dictionaries with data-dependent statistics explicitly documented as `None` (unavailable) rather than misleadingly reported as 0.0% nulls.
- **Multi-Sheet Workbooks Cataloged**: Columns across all 6 worksheets (including dictionary and information sheets) are indexed.
- **Duplicate Headers Preserved**: Duplicate column names within files are mapped to positional parser aliases without altering original strings."""
    ))

    cells.append(nbf.v4.new_code_cell(
"""# Load machine-readable schema catalog covering all 177 files
schema_cat_path = repo_root / "EDA" / "outputs" / "reports" / "phase1_schema_catalog.json"
with open(schema_cat_path, "r", encoding="utf-8") as f:
    schema_catalog = json.load(f)

file_schemas = schema_catalog["file_schemas"]
meta = schema_catalog["metadata"]
primary_cols = meta.get("primary_file_columns_count", 3659)
total_structural = meta.get("total_structural_headers_count", 3682)

print(f"Total Source File Schemas Documented : {len(file_schemas)} (100% coverage)")
print(f"Primary-File Columns Cataloged       : {primary_cols:,} (across 177 primary file records)")
print(f"Total Structural Table & Sheet Headers: {total_structural:,} (3,389 non-workbook + 293 sheet headers across 180 units)")
assert len(file_schemas) == 177, "Schema catalog does not cover 100% of source files!"

# Aggregate complete catalog of all cataloged columns across the 177 source files and sheets
all_column_records = []
for rel_path, f_meta in sorted(file_schemas.items()):
    if f_meta.get("worksheets"):
        for ws in f_meta["worksheets"]:
            ws_name = ws["sheet_name"]
            for idx, h in enumerate(ws.get("literal_headers", [])):
                all_column_records.append({
                    "Domain Folder": f_meta["domain_folder"],
                    "Source Table / Sheet": f"{f_meta['file_name']} [{ws_name}]",
                    "Col Index": idx,
                    "Original Header": h,
                    "Parser Alias": h,
                    "Inferred Type": "unverified",
                    "Missingness (%)": "N/A (Worksheet Audit)",
                    "Variable Role": "unverified",
                })
    else:
        for col in f_meta.get("columns", []):
            all_column_records.append({
                "Domain Folder": f_meta["domain_folder"],
                "Source Table / Sheet": f_meta["file_name"],
                "Col Index": col["column_index"],
                "Original Header": col["original_name"],
                "Parser Alias": col["parser_alias"],
                "Inferred Type": col["inferred_type"],
                "Missingness (%)": col["missingness_percentage"] if col["missingness_percentage"] is not None else "N/A",
                "Variable Role": col["variable_role"],
            })

df_all_columns = pd.DataFrame(all_column_records)
print(f"Compiled DataFrame of all structural headers: {len(df_all_columns)} rows")
assert len(df_all_columns) == 3682, f"Expected 3,682 cataloged columns, got {len(df_all_columns)}"

# Per-domain column distribution summary
domain_col_summary = df_all_columns.groupby("Domain Folder").agg(
    Files=("Source Table / Sheet", "nunique"),
    Total_Columns=("Original Header", "count"),
    Numeric_Cols=("Inferred Type", lambda s: (s == "numeric").sum()),
    Categorical_Cols=("Inferred Type", lambda s: (s == "categorical_or_text").sum()),
    Identifier_Cols=("Inferred Type", lambda s: (s == "identifier").sum()),
).reset_index().sort_values(by="Total_Columns", ascending=False).reset_index(drop=True)

display(domain_col_summary)

# Embed complete accessible 3,682-row structural column catalog in saved notebook output (P1-11)
catalog_html = f'''
<details style="margin-top: 15px; border: 1px solid #ccc; padding: 10px; border-radius: 5px;">
  <summary style="font-weight: bold; cursor: pointer; font-size: 1.1em;">
    [+] Complete 3,682-Row Structural Column Catalog (Click to Expand / View Full Catalog)
  </summary>
  <div style="max-height: 600px; overflow-y: auto; margin-top: 10px;">
    {df_all_columns.to_html(classes="table table-striped table-hover", index=False)}
  </div>
</details>
'''
display(HTML(catalog_html))"""
    ))

    cells.append(nbf.v4.new_code_cell(
"""# Complete accessible structural schema index across all 180 file/sheet units (P1-11)
schema_index_records = []
for rel_path, f_meta in sorted(file_schemas.items()):
    if f_meta.get("worksheets"):
        for ws in f_meta["worksheets"]:
            ws_name = ws["sheet_name"]
            first_3 = ", ".join(ws.get("literal_headers", [])[:3])
            schema_index_records.append({
                "Domain Folder": f_meta["domain_folder"],
                "Source Table / Sheet": f"{f_meta['file_name']} -> [{ws_name}]",
                "Logical Rows": ws.get("row_count", 0),
                "Columns": ws.get("column_count", len(ws.get("literal_headers", []))),
                "Identifiers": "PATNO" if ws.get("has_participant_id") else "None",
                "Observation Grain": ws.get("observation_grain", "Grain Unresolved"),
                "Sample Headers": first_3 if first_3 else "N/A",
            })
    else:
        cols = f_meta.get("columns", [])
        first_3 = ", ".join([c["original_name"] for c in cols[:3]]) if cols else "N/A"
        schema_index_records.append({
            "Domain Folder": f_meta["domain_folder"],
            "Source Table / Sheet": f_meta["file_name"],
            "Logical Rows": f_meta.get("row_count", "N/A"),
            "Columns": f_meta.get("column_count", 0),
            "Identifiers": "PATNO" if f_meta.get("has_patno") else "None",
            "Observation Grain": f_meta.get("observation_grain", "Documentation / Reference"),
            "Sample Headers": first_3 if first_3 else "N/A",
        })

df_schema_index = pd.DataFrame(schema_index_records)
print(f"Complete Accessible Schema Index: {len(df_schema_index)} structural table units across 177 files (100% cataloged)")
assert len(df_schema_index) == 180, f"Expected 180 structural table units, got {len(df_schema_index)}"
pd.set_option('display.max_rows', 250)
display(df_schema_index)"""
    ))

    cells.append(nbf.v4.new_code_cell(
"""# Detailed inspection of specific schema dictionaries across distinct data domains

def inspect_file_schema(rel_path_query: str):
    matched_key = next((k for k in file_schemas if rel_path_query.lower() in k.lower()), None)
    if not matched_key:
        print(f"No file matching '{rel_path_query}' found.")
        return None
    meta = file_schemas[matched_key]
    df_dict = pd.DataFrame(meta["columns"])
    cols_to_show = ["column_index", "original_name", "inferred_type", "missingness_percentage", "data_status", "variable_role"]
    print(f"=== Schema for: {matched_key} ({meta['row_count']} rows, {meta['column_count']} cols) ===")
    return df_dict[cols_to_show]

# Sample 1: Zero-row file showing explicitly unavailable statistics
print("Sample 1: Zero-Row Header-Only File")
display(inspect_file_schema("Early_Imaging_Report_of_Pregnancy").head(6))

# Sample 2: Complex motor assessment table
print("Sample 2: Motor Examination Table (MDS-UPDRS Part III)")
display(inspect_file_schema("MDS-UPDRS_Part_III").head(8))"""
    ))

    # Section 6: Observation Grain Taxonomy & Repeated-Event Key Validation
    cells.append(nbf.v4.new_markdown_cell(
"""## 6. Observation Grain Taxonomy & Repeated-Event Key Validation

### 6.1 Observation Grain Taxonomy
Merging multimodal tables without validating observation grain causes catastrophic data corruption, including artificial record duplication and invalid Cartesian joins. The PPMI repository exhibits six distinct operational observation grains:

| Observation Grain | Defining Semantic | Candidate Key | Validated Table Count |
| :--- | :--- | :--- | :--- |
| **Subject-Level** | Exactly 1 record per participant across the entire study | `['PATNO']` | 44 tables |
| **Visit-Level** | At most 1 record per participant per standardized milestone visit | `['PATNO', 'EVENT_ID']` | 60 tables |
| **Repeated Event / Item** | Multiple clinical events or entries per participant per visit | `['REC_ID']`, `ImageID`, or clinical composite | 38 tables |
| **Documentation / Metadata** | Reference dictionary, catalog guide, or protocol summary (no `PATNO`) | `None` | 21 files |
| **Ambiguous / Needs Review** | Unresolved candidate key or duplicate records present in raw source | Flagged for review | 12 tables |
| **Unindexed / Unknown** | Zero data records or unindexed binary | `None` | 2 files |"""
    ))

    cells.append(nbf.v4.new_code_cell(
"""# Distribution of Observation Grains across Tabular Source Files (N = 160 tabular files)
tabular_mask = df_manifest["Format"].isin(["Tabular CSV", "Tabular Excel (.xlsx)", "Raw Time-Series / Sensor Stream"])
df_tabular = df_manifest[tabular_mask]

grain_counts = df_tabular["Observation Grain"].value_counts().reset_index()
grain_counts.columns = ["Observation Grain", "Number of Tabular Files"]
grain_counts["Percentage (%)"] = (grain_counts["Number of Tabular Files"] / len(df_tabular) * 100).round(1)
print(f"Total Tabular Source Files Analyzed: {len(df_tabular)} (156 CSV + 1 Sensor Stream + 3 Excel Workbooks)")
grain_counts"""
    ))

    cells.append(nbf.v4.new_markdown_cell(
"""### 6.2 Key Validation for Repeated-Event & Ambiguous Tables (N = 50)
The canonical grain catalog classifies **38 tables as Repeated Event / Item-Level** and **12 tables as Ambiguous / Needs Review**:
1. **38 Repeated-Event Tables with Validated Candidate Keys**:
   - **25 files** uniquely resolve on database surrogate key `REC_ID` (`max_multiplicity == 1`).
   - `MOTOR/MDS-UPDRS_Part_III_09Nov2026.csv`: Uniquely resolves on composite clinical key `['PATNO', 'EVENT_ID', 'PAG_NAME', 'PDSTATE']` (distinguishing ON-state, OFF-state, and repeat test administrations) as well as `REC_ID`.
   - `PET/PET_Acquisition_Metadata_09Nov2026.csv`: Unique on `['PATNO', 'EVENT_ID', 'PET_LIGAND']` and `['PATNO', 'EVENT_ID', 'PET_SCAN_DATE']`.
   - `PET/SV2A_PET_SUVR_Analysis_09Nov2026.csv`: Unique on `['PATNO', 'EVENT_ID', 'SV2A_REGION']`.
   - `PET/PET_SBR_Analysis_09Nov2026.csv`: Unique on `['PATNO', 'EVENT_ID', 'PET_SCAN_DATE']`.
   - `MR Analysis Results/PPMI_rs-fMRI_Data-and-Methods/PPMI_fs-fMRI_dataReport_spreadsheet_FINAL_20191121.xlsx`: Scan session sheet uniquely resolves on `ImageID`.
   - `biospecimen/Whole_Blood_Substudy_09Nov2026.csv`: Unique on `REC_ID` and `['PATNO', 'EVENT_ID', 'ORIG_ENTRY']`.
2. **12 Ambiguous Tables Flagged for Technical Review**:
   - `MRI Acquisition/Xing_Core_Lab_-_MRI_acquisition_metadata_09Nov2026.csv`: Contains 15 duplicate participant-visit entries differing only in null quality flags.
   - `other cognitive/Cognitive_Activities_Testing_Session_09Nov2026.csv`: Contains 74 exact duplicate rows across all columns.
   - `digital_Sensor/Roche_PD_Monitoring_App_v2_data_09Nov2026.csv`: High-frequency mobile active test metrics with multi-level test session structures.
   - Both files with duplicate records and all other unresolved tables are appropriately classified as `ObservationGrain.AMBIGUOUS_NEEDS_REVIEW` in `phase1_grain_catalog.json` and documented in `phase1_repeated_event_keys_report.md`."""
    ))

    cells.append(nbf.v4.new_code_cell(
"""# Load machine-readable grain catalog to inspect repeated-event and ambiguous files
grain_cat_path = repo_root / "EDA" / "outputs" / "reports" / "phase1_grain_catalog.json"
with open(grain_cat_path, "r", encoding="utf-8") as f:
    grain_catalog = json.load(f)

# Display canonical grain breakdown summary across the catalog
print("=== Canonical Grain Catalog Summary (N = 177 physical source files) ===")
for grain_name, files in grain_catalog["catalog"].items():
    print(f"Grain: {grain_name:<48} -> {len(files):>3} files")

repeated_files = grain_catalog["catalog"]["Repeated Event / Item-Level (multiple rows per visit)"]
ambiguous_files = grain_catalog["catalog"]["Ambiguous / Needs Detailed Review"]

assert len(repeated_files) == 38, f"Expected 38 repeated-event files, found {len(repeated_files)}"
assert len(ambiguous_files) == 12, f"Expected 12 ambiguous files, found {len(ambiguous_files)}"
print(f"Total Non-Singleton Tables Documented: {len(repeated_files) + len(ambiguous_files)} (38 repeated + 12 ambiguous)")"""
    ))

    # Section 7: Join Cardinality Safety Engine & Synthetic Validation
    cells.append(nbf.v4.new_markdown_cell(
"""## 7. Join Cardinality Safety Engine & Synthetic Validation

In accordance with Codex requirement P1-05, we demonstrate the enforcement of join cardinality rules on controlled synthetic fixtures. 

**Critical Invariant 1: Null-Key Isolation (`NULL != NULL`) & Explicit Call Boundary Policy**  
In relational databases and standard statistical merges, missing join keys must **never** be treated as matching values. If both tables contain records with missing `PATNO` or missing `EVENT_ID`, standard `pd.merge()` matches `NaN` to `NaN`, artificially joining unrelated participants. 

Our `JoinValidator` enforces an explicit call-boundary policy:
- `on_null_keys='reject'` (default): Unconditionally raises `NullJoinKeyError` if null keys are present, even when joining opposite an empty table.
- `on_null_keys='drop'`: Isolates null keys, safely drops them before merging, and provides an audit log with accurate dropped counts.
- `on_null_keys='preserve_left'`: For left joins, preserves left null-key rows without matching right null rows.

**Critical Invariant 2: Unconditional Blocking of Many:Many Joins**  
Merging two multi-record tables (e.g., Concomitant Medications and Adverse Events) on `PATNO` without an explicit item-level key produces a Cartesian explosion ($N \times M$ rows), multiplying dosages and creating phantom associations. Our pipeline strictly and unconditionally raises `IncompatibleJoinGrainError`."""
    ))

    cells.append(nbf.v4.new_code_cell(
"""# Demonstrate JoinValidator: Evaluation and Safe Null-Key Handling

# 1. Subject-level table with a null key
df_demo = pd.DataFrame({
    "PATNO": [1001, 1002, 1003, None],
    "SEX": ["Male", "Female", "Male", "Unknown"]
})

# 2. Visit-level clinical table with a null key
df_motor = pd.DataFrame({
    "PATNO": [1001, 1001, 1002, None],
    "EVENT_ID": ["BL", "V04", "BL", "BL"],
    "MDS_UPDRS_TOTAL": [18, 24, 12, 30]
})

print("Evaluating join between Subject Demographics and Longitudinal Motor Scores...")
eval_report = JoinValidator.evaluate(df_demo, df_motor, join_keys=["PATNO"], on_null_keys="drop")

print(f"Detected Cardinality        : {eval_report.cardinality.value}")
print(f"Is Safe for Analysis        : {eval_report.is_safe}")
print(f"Left Null Keys Detected     : {eval_report.left_null_keys_count}")
print(f"Right Null Keys Detected    : {eval_report.right_null_keys_count}")
print(f"Non-Null Intersecting Keys  : {eval_report.intersection_keys_count}")
print(f"Estimated Merged Rows       : {eval_report.estimated_merged_rows}")

# Demonstrate Policy 1: on_null_keys='reject' (Default fail-safe behavior)
try:
    JoinValidator.safe_merge(df_demo, df_motor, join_keys=["PATNO"], on_null_keys="reject")
except NullJoinKeyError as e:
    print(f"Expected Safety Exception Caught: {e.__class__.__name__}")
    print(f"Guard Message: {e}")

# Demonstrate Policy 2: on_null_keys='drop' (Isolate null keys, strictly no cross-match)
merged_dropped, audit = JoinValidator.safe_merge(
    df_demo, df_motor, join_keys=["PATNO"], how="inner", on_null_keys="drop", return_audit=True
)
print(f"Safely Merged Rows (drop)   : {len(merged_dropped)}")
print(f"Audit Log                   : {audit}")
assert len(merged_dropped) == eval_report.estimated_merged_rows, "Null keys cross-matched!"
print("Verification Succeeded: Null keys were strictly isolated and did NOT cross-match.")"""
    ))

    cells.append(nbf.v4.new_code_cell(
"""# Demonstrate Unconditional Blocking of Many:Many Joins
df_meds = pd.DataFrame({
    "PATNO": [1001, 1001, 1002],
    "MED_NAME": ["Levodopa", "Pramipexole", "Rasagiline"]
})

df_adverse = pd.DataFrame({
    "PATNO": [1001, 1001, 1002],
    "AE_NAME": ["Dyskinesia", "Nausea", "Headache"]
})

try:
    print("Attempting to merge Meds and Adverse Events directly on PATNO without item key...")
    JoinValidator.safe_merge(df_meds, df_adverse, join_keys=["PATNO"])
except IncompatibleJoinGrainError as e:
    print(f"Expected Safety Exception Caught: {e.__class__.__name__}")
    print(f"Pipeline Guard Message: {e}")
    print("Verification Succeeded: Many:Many merge was strictly and unconditionally blocked.")"""
    ))

    # Section 8: Physical Local Presence vs Remote / External Reference
    cells.append(nbf.v4.new_markdown_cell(
"""## 8. Physical Local Presence vs Remote / External Reference

PPMI study protocols and manuals frequently discuss modalities (e.g., raw whole-genome sequencing, raw RNA-seq reads, 3D MRI scans, raw high-frequency sensor streams) that are **not stored locally** in the tabular repository.

In accordance with Codex finding P1-08, claiming that an external modality is locally available based purely on study manuals is scientifically inaccurate. The following table establishes verified local physical availability versus external reference status, citing exclusively present local documentation."""
    ))

    cells.append(nbf.v4.new_code_cell(
"""# Load machine-readable external references manifest
ext_cat_path = repo_root / "EDA" / "outputs" / "reports" / "phase1_external_references_manifest.json"
with open(ext_cat_path, "r", encoding="utf-8") as f:
    ext_manifest = json.load(f)

df_provenance = pd.DataFrame(ext_manifest["external_references"])
display_ext_cols = ["modality", "data_stream", "local_artifact_status", "local_documentation", "external_repository"]
df_provenance[display_ext_cols]"""
    ))

    # Section 9: Aggregated Multimodal Distribution & Visualizations
    cells.append(nbf.v4.new_markdown_cell(
"""## 9. Aggregated Multimodal Distributions & Visualizations

In accordance with Phase 1 constraints, figures visualize only aggregate structural distributions (file counts, format frequencies, storage volumes, and observation grains). No clinical scores, individual biomarker trajectories, or patient-level distributions are plotted."""
    ))

    cells.append(nbf.v4.new_code_cell(
"""# Aggregate Table 1: Distribution of Files, Storage, and Tabular Records by Domain Folder
domain_agg = df_manifest.groupby("Domain Folder").agg(
    File_Count=("File Name", "count"),
    Total_Size_KB=("Size (KB)", "sum"),
    Tabular_Rows=("Logical Rows", lambda s: sum(r for r in s if r > 0))
).reset_index()

domain_agg["Size (MB)"] = (domain_agg["Total_Size_KB"] / 1024).round(2)
domain_agg = domain_agg.sort_values(by="File_Count", ascending=False).reset_index(drop=True)
domain_agg[["Domain Folder", "File_Count", "Size (MB)", "Tabular_Rows"]]"""
    ))

    cells.append(nbf.v4.new_code_cell(
"""# Aggregate Table 2: Distribution by File Format Category
format_agg = df_manifest.groupby("Format").agg(
    File_Count=("File Name", "count"),
    Total_Size_KB=("Size (KB)", "sum")
).reset_index()

format_agg["Size (MB)"] = (format_agg["Total_Size_KB"] / 1024).round(2)
format_agg["File Percentage (%)"] = (format_agg["File_Count"] / len(df_manifest) * 100).round(1)
format_agg = format_agg.sort_values(by="File_Count", ascending=False).reset_index(drop=True)
format_agg[["Format", "File_Count", "File Percentage (%)", "Size (MB)"]]"""
    ))

    cells.append(nbf.v4.new_code_cell(
"""# Aggregate Figure 1: Physical File Distribution Across 17 PPMI Domain Folders (N = 177)
fig, ax = plt.subplots(figsize=(10, 6))

sns.barplot(
    data=domain_agg,
    y="Domain Folder",
    x="File_Count",
    hue="Domain Folder",
    palette="Blues_r",
    legend=False,
    ax=ax
)

ax.set_title("Figure 1: Distribution of Physical Source Files Across 17 PPMI Domain Folders (N = 177 Files)", fontweight="bold")
ax.set_xlabel("Number of Physical Files")
ax.set_ylabel("PPMI Domain Folder")

# Add data value labels to bars
for i, v in enumerate(domain_agg["File_Count"]):
    ax.text(v + 0.3, i, f"{v}", va="center", fontsize=8, color="#333333")

plt.tight_layout()
plt.show()"""
    ))

    cells.append(nbf.v4.new_code_cell(
"""# Aggregate Figure 2: File Format Breakdown and Observation Grain Distribution
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

# Subplot 1: Format Distribution (N = 177)
sns.barplot(
    data=format_agg,
    y="Format",
    x="File_Count",
    hue="Format",
    palette="viridis",
    legend=False,
    ax=ax1
)
ax1.set_title("Figure 2A: Source Universe by File Format (N = 177)", fontweight="bold")
ax1.set_xlabel("Number of Files")
ax1.set_ylabel("Format Category")
for i, v in enumerate(format_agg["File_Count"]):
    ax1.text(v + 0.5, i, f"{v}", va="center", fontsize=8)

# Subplot 2: Observation Grain Distribution (N = 160 Tabular Sources)
sns.barplot(
    data=grain_counts,
    y="Observation Grain",
    x="Number of Tabular Files",
    hue="Observation Grain",
    palette="mako",
    legend=False,
    ax=ax2
)
ax2.set_title(f"Figure 2B: Tabular Sources by Observation Grain (N = {len(df_tabular)})", fontweight="bold")
ax2.set_xlabel("Number of Tabular Files")
ax2.set_ylabel("Inferred Observation Grain")
for i, v in enumerate(grain_counts["Number of Tabular Files"]):
    ax2.text(v + 0.5, i, f"{v}", va="center", fontsize=8)

plt.tight_layout()
plt.show()"""
    ))

    # 9.2 Distribution Shape and Skewness of Inventory Metrics
    cells.append(nbf.v4.new_markdown_cell(
r"""### 9.2 Distribution Shape and Skewness of Inventory Structural Metrics

To evaluate structural asymmetry across the multimodal inventory, Fisher–Pearson sample skewness was computed across physical source file sizes, tabular row dimensions, column counts, and column missingness percentages:
$$g_1 = \frac{n}{(n-1)(n-2)} \sum_{i=1}^n \left(\frac{x_i - \bar{x}}{s}\right)^3$$

Descriptive shape classifications follow standard thresholds:
- $|g_1| < 0.5$: Approximately symmetric
- $0.5 \le |g_1| \le 1.0$: Moderately skewed
- $|g_1| > 1.0$: Strongly skewed"""
    ))

    cells.append(nbf.v4.new_code_cell(
"""# Table: Distribution Shape and Skewness of Inventory Structural Metrics
from ppmi_pipeline.reporting.notebook_support import numeric_skewness_summary

tab_rows = df_manifest[df_manifest["Logical Rows"] > 0]["Logical Rows"]
tab_cols = df_manifest[df_manifest["Columns"] > 0]["Columns"]
valid_missingness = pd.to_numeric(df_all_columns["Missingness (%)"], errors="coerce").dropna()

skew_specs = [
    {"domain": "Overview", "variable": "file_size_kb", "grain": "Discovered Physical Sources (KB, N=177)", "series": df_manifest["Size (KB)"]},
    {"domain": "Overview", "variable": "tabular_row_count", "grain": "Audited Tabular Sources (Rows)", "series": tab_rows},
    {"domain": "Overview", "variable": "column_count", "grain": "Audited Tabular Sources (Columns)", "series": tab_cols},
    {"domain": "Overview", "variable": "column_missingness_pct", "grain": "Audited Catalog Columns (N=3,682)", "series": valid_missingness}
]

skewness_df = numeric_skewness_summary(skew_specs)
print("Table: Distribution Shape and Skewness of Inventory Structural Metrics:")
display(skewness_df)"""
    ))

    # Section 10: Structural Quality Screening & Data Quality Observations
    cells.append(nbf.v4.new_markdown_cell(
"""## 10. Structural Quality Screening & Data Quality Observations

### 10.1 Detection of System Metadata Sidecars
Scanning the 17 source folders identified **2 macOS system metadata sidecar files** (`._PPMI_Methods_rs-fMRI_Data_FINAL_2019_12_04.docx` and `._PPMI_fs-fMRI_dataReport_spreadsheet_FINAL_20191121.xlsx`). These files represent HFS+/APFS extended filesystem attributes (resource forks) created during Mac OS file extraction. They contain binary header bytes rather than ASCII/UTF-8 data records and cannot be parsed as tabular datasets. Our pipeline automatically identifies them as `FormatCategory.SYSTEM_METADATA` and isolates them to prevent parser crashes.

### 10.2 Exact Literal Header Preservation
In standard data science workflows, CSV readers (like pandas) often silently modify column names (e.g., stripping leading/trailing whitespace, appending `.1` or `.2` to duplicate column names, or replacing empty headers with `Unnamed: 0`). 
In our pipeline, `SafeDataReader.read_csv_header()` extracts the exact literal header strings as written on disk. Across the 156 Tabular CSV files:
- Whitespace in headers is preserved without alteration.
- Duplicate column names within raw files are formally tracked in schema profiles.
- Any pandas parser aliases are documented in a distinct mapping dictionary without modifying the raw source files.

### 10.3 Source-Specific Missing Value Sentinels
In legacy clinical trial databases, missing values are frequently encoded as numeric sentinels (e.g., `-1`, `999`, `-99`). Codex finding P1-08 emphasized that **global sentinel assumptions are scientifically invalid**. Different PPMI forms encode missingness differently:
- Some forms use empty fields or whitespace (`""`, `" "`).
- Genomics and molecular tables use `.` or `"NA"`.
- Older CRF questionnaires occasionally use `-1` to represent "Not Applicable" and `999` for "Missing".
Converting `-1` to null across all columns would destroy legitimate negative coordinates, stereotaxic offsets, or standard scores. Therefore, missingness sentinels are treated as strictly source- and variable-specific, and no global sentinel replacement has been applied.

### 10.4 Evaluation of Filename Marker `(1)`
Several source files contain the marker `(1)` in their filename (notably `curated_datacuts/PPMI_Curated_Data_Cut_Public_20260810(1).xlsx` and `biospecimen/PPMI_IPSC_Catalog_User_Guide(1).xlsx`). 
Codex finding P1-02 verified that `(1)` is a benign artifact of operating system download numbering. It does **not** indicate a redundant or obsolete duplicate. All candidate datasets remain classified as `Selection Pending`, with final role assignments deferred to the Research Dataset Selection Gate."""
    ))

    # Section 11: Phase 1 Conclusions & Audit Readiness
    cells.append(nbf.v4.new_markdown_cell(
"""## 11. Phase 1 Conclusions & Audit Readiness Assessment

### 11.1 Summary of Phase 1 Technical Achievements
1. **Source Universe Reconciled**: Exactly **177 physical source files** cataloged across 17 canonical domain folders (243.34 MB, 1,748,882 tabular records). Non-source project code, manuals, and generated outputs (167 artifacts, snapshot as of canonical inventory generation) are cleanly segregated.
2. **Multi-Sheet Structural Catalogs**: All 6 worksheets of complex `.xlsx` workbooks have been independently audited for dimensions, headers, identifier keys, and observation grain.
3. **Cardinality Enforced & Fail-Closed Privacy Implemented**: Strict isolation of null join keys (`NULL != NULL`), explicit call-boundary policies (`reject`, `drop`, `preserve_left`), and unconditional blocking of Many:Many joins demonstrated. Multi-MIME privacy inspection engine implemented under typed output schema contracts; full certification subject to supervisor re-verification.
4. **Physical vs Remote Provenance Documented**: Clear boundary drawn between local tabular data and remote archives, citing present local documentation and explicitly marking unverified remote repositories.
5. **Key Validation for Repeated-Event & Ambiguous Tables**: Audited all 38 repeated-event tables and 12 ambiguous tables (50 non-singleton tables total). Valid candidate keys established for all 38 repeated-event tables, while 12 ambiguous tables (including duplicate-bearing tables) are flagged for supervisor review.

### 11.2 Audit Readiness Statement
The structural profiling, schema extraction, and grain classification are complete and verified. The codebase is fully prepared for technical re-verification by Codex.

### 11.3 Research Dataset Selection Status
In strict accordance with the project mandate:
- **All 177 source files remain classified as `Selection Pending (Awaiting Selection Gate Approval)`**.
- No files have been permanently excluded.
- No files have been finalized for detailed EDA.
- Detailed clinical analysis, longitudinal trajectory modeling, and cross-modal synthesis will commence only after formal review by Codex and explicit approval of the Scientific Selection Gate by the user.

### 11.4 Transition to Dataset Selection Gate
Phase 1 inventory, structural schema profiling, grain classification, and privacy enforcement formally PASSED Codex technical verification on 2026-11-12. In accordance with the research mandate, all 177 source files advance into the **Dataset Selection & Prioritization Gate** detailed in Section 12 below."""
    ))

    # Section 12: Dataset Selection & Prioritization Gate
    cells.append(nbf.v4.new_markdown_cell(
"""## 12. Dataset Selection & Prioritization Gate

### 12.1 Purpose & Scientific Rationale
Following the complete inventory and structural profiling of all 177 source files in Phase 1, we conduct a structured **Dataset Selection and Prioritization Gate** prior to commencing detailed modality-specific exploratory data analyses.

Rather than conducting indiscriminate, unfocused EDA across every administrative log or duplicate table, our goal is to identify:
1. **Core Scientific Datasets**: Essential files directly mapping disease progression, motor/cognitive trajectories, bioassays, and molecular risk.
2. **Contextual & Supporting Datasets**: Files providing demographic covariates, visit dates, safety monitoring, or medication status needed to adjust and interpret primary analyses.
3. **Candidate Exclusions**: Byte-identical duplicates or operating system metadata sidecars carrying no scientific payload.
4. **Items Flagged for Review**: Ambiguous, highly sparse, or ultra-wide files requiring researcher consultation.

### 12.2 Seven Evaluation Criteria
Each file is evaluated across seven objective, transparent dimensions:
1. **Clinical & Scientific Relevance**: Direct bearing on motor, cognitive, autonomic, or biological PD pathology.
2. **Information Content & Granularity**: Number of meaningful biological/clinical variables vs administrative tracking overhead.
3. **Participant & Visit Coverage**: Cohort breadth evaluated against explicit denominators (e.g., N=5,019 milestone-eligible; N=7,834 total enrolled).
4. **Longitudinal Depth**: Follow-up coverage across scheduled milestone visits (BL through V20) based on verified within-participant observation repetition.
5. **Data Quality & Interpretability**: Empirical null rates, verified documentation coverage, and absence of undocumented global sentinels.
6. **Redundancy Evidence**: Byte-level and schema-level comparator analysis to prevent duplicate data processing.
7. **Multimodal Integration Value**: Relational join viability on (PATNO, EVENT_ID) with imaging, biospecimen, or sensor streams.

### 12.2A Unified Atomic Claim & Structured Locator Architecture (SG-02)
To prevent ungrounded claims or hallucinated documentation locators, all catalog assertions are backed by machine-verifiable data structures:
- **`AtomicClaim` & `StructuredLocator` Architecture**: Every claimed protocol fact is expressed as an `AtomicClaim` linked to a `StructuredLocator` with format-specific properties:
  - **PDF Documents**: Exact `page_range: Tuple[int, int]` checked against physical PDF page limits.
  - **DOCX Manuals**: `heading_text: str` bounded from the target heading paragraph to the next heading of equal or higher level, strictly restricting keyword matching to the designated section.
  - **XLSX Catalogs/Dictionaries**: `sheet_name`, `exact_dimensions: Tuple[int, int]`, and `exact_columns: List[str]` requiring whole-cell equality (`cell == expected`), preventing substring false positives (e.g., rejecting `'PAT'` when the true column is `'PATNO'`).
- **Fail-Closed Validation**: The `DocumentLocatorValidator` enforces that only canonical source keys are cited, scans for prohibited fabricated terms, verifies that all `required_evidence_terms` are substantiated in `claim_text`, and validates that displayed locator strings match structured specifications.
- **Data Dictionary Grounding**: For example, `curated_datacuts/PPMI_Curated_Data_Cut_Public_20260810(1).xlsx` sheet `Data dictionary` (453x10) was re-audited and grounded strictly in verified categories (`Clinical`, `DATSCAN`, `Biologics`, `Genetics`), confirming 0 MRI variables.

### 12.2B Longitudinal Evidence Semantics & Within-Participant Repetition (SG-11)
To prevent misleading cardinality representations, event semantics and longitudinal repetition are strictly decoupled:
- **Separation of Records from Event Codes**: Rather than treating distinct raw event codes as longitudinal visits, we report `event_key_column`, `event_semantics`, `non_null_event_record_count`, `null_event_record_count`, and `distinct_raw_event_values`.
- **Within-Participant Repetition Analysis**: Unapproved global cardinality thresholds (Low/Moderate/High) are replaced with empirical within-participant repetition metrics (`participants_with_repeated_events`, `longitudinal_participant_denominator_name` = `"Observed participants with non-null event records"`, `longitudinal_status`).
- **Disclosed Grain Nuances**: Tables with ambiguous observation grains (e.g., MRI acquisition metadata with 1,931 null event keys) and high-cardinality testing sessions (e.g., Cognitive Activities Testing Session with 1,160 event IDs) are explicitly distinguished from verified milestone-based longitudinal schedules.

### 12.3 Classification Categories
- **Primary EDA**: Primary analytical targets for detailed exploratory modeling in Phases 2–5.
- **Supporting**: Covariate, demographic, validation, or safety tracking tables retained for context and joins.
- **Excluded from detailed EDA**: Candidate exclusions based on verified byte-level redundancy or zero scientific payload.
- **Needs Review**: Files with scientific trade-offs flagged for researcher and supervisor guidance.
- **Pre-Review Status**: In this initial evidence assembly stage, all proposed categories are formally flagged as `Needs Review — Codex recommendation pending` until Codex completes technical review and the researcher issues formal sign-off."""
    ))

    cells.append(nbf.v4.new_code_cell(
"""# Load canonical selection evidence matrix
selection_json_path = repo_root / "EDA" / "outputs" / "reports" / "dataset_selection_matrix.json"
with open(selection_json_path, "r", encoding="utf-8") as f:
    sel_data = json.load(f)

file_matrix = sel_data["file_selection_matrix"]
sheet_matrix = sel_data["worksheet_selection_matrix"]
df_files = pd.DataFrame(file_matrix)
df_sheets = pd.DataFrame(sheet_matrix)

# 1. Provisional Recommendation Summary Table
cat_counts = df_files["provisional_recommendation"].value_counts().reset_index()
cat_counts.columns = ["Provisional Recommendation", "File Count"]
cat_counts["Percentage (%)"] = (cat_counts["File Count"] / len(df_files) * 100).round(1)

total_row = pd.DataFrame([{
    "Provisional Recommendation": "Total In-Scope Sources",
    "File Count": len(df_files),
    "Percentage (%)": 100.0
}])
cat_summary_table = pd.concat([cat_counts, total_row], ignore_index=True)

display(HTML("<h4>Table 12.1: Dataset Selection Breakdown by Provisional Recommendation</h4>"))
display(HTML(cat_summary_table.to_html(index=False, classes='table table-striped table-bordered')))

# 2. Target Notebook Distribution Table
nb_counts = df_files["target_notebook"].value_counts().reset_index()
nb_counts.columns = ["Target Notebook", "File Count"]
nb_counts["Percentage (%)"] = (nb_counts["File Count"] / len(df_files) * 100).round(1)
display(HTML("<h4>Table 12.2: Distribution of Source Datasets across Target Analysis Notebooks</h4>"))
display(HTML(nb_counts.to_html(index=False, classes='table table-striped table-bordered')))

# 3. Non-redundant Visual Distribution
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 4.5))

palette_cats = {"Primary EDA": "#2ca02c", "Supporting": "#1f77b4", "Excluded from detailed EDA": "#d62728", "Needs Review": "#ff7f0e"}
sns.barplot(
    data=cat_counts,
    x="Provisional Recommendation",
    y="File Count",
    hue="Provisional Recommendation",
    palette=palette_cats,
    legend=False,
    ax=ax1
)
ax1.set_title("PPMI Datasets by Provisional Recommendation")
ax1.set_xlabel("Provisional Recommendation")
ax1.set_ylabel("Source Files Count")
for p in ax1.patches:
    height = int(p.get_height())
    if height > 0:
        ax1.annotate(f"{height}", (p.get_x() + p.get_width() / 2., height + 1),
                     ha='center', va='bottom', fontsize=9)

# Notebook distribution plot
sns.barplot(
    data=nb_counts,
    y="Target Notebook",
    x="File Count",
    hue="Target Notebook",
    palette="viridis",
    legend=False,
    ax=ax2
)
ax2.set_title("PPMI Datasets by Target Analysis Notebook")
ax2.set_xlabel("Source Files Count")
ax2.set_ylabel("Target Notebook")
for p in ax2.patches:
    width = int(p.get_width())
    if width > 0:
        ax2.annotate(f"{width}", (width + 1, p.get_y() + p.get_height() / 2.),
                     ha='left', va='center', fontsize=9)

plt.tight_layout()
plt.show()"""
    ))

    cells.append(nbf.v4.new_markdown_cell(
"""### 12.4 Candidate Exclusions & Items Flagged for Review
In strict adherence to the project rules:
- **No file is excluded due to small sample size or high missingness**. Zero-row safety logs and small-sample cohorts are preserved as `Supporting`.
- **Files with `(1)` in their names are NOT automatically excluded**. Unique primary copies (`PPMI_IPSC_Catalog_User_Guide(1).xlsx` and `PPMI_Curated_Data_Cut_Public_20260810(1).xlsx`) are retained.
- Only exact byte-identical duplicates (identical SHA-256) and macOS AppleDouble filesystem sidecars are proposed for exclusion (4 files total). For sidecars, AppleDouble magic is verified (`00 05 16 07`) and companion hashes differ.
- Candidate progression files lacking verified local methods documents (23 clinical candidate files), scientifically plausible non-clinical analysis tables (5 files), and the cross-domain duplicate pair (`Open_Query_09Nov2026.csv` in `DATSCAN/` and `MEDICAL HISTORY/`, 2 files) are classified as `Needs Review` (30 files total) awaiting supervisor and researcher review."""
    ))

    cells.append(nbf.v4.new_code_cell(
"""# Display Candidate Exclusions and Items Flagged for Review
excluded_rows = [r for r in file_matrix if r["provisional_recommendation"] == "Excluded from detailed EDA"]
needs_review_rows = [r for r in file_matrix if r["provisional_recommendation"] == "Needs Review"]

df_ex = pd.DataFrame(excluded_rows)
df_nr = pd.DataFrame(needs_review_rows)

df_ex_table = pd.DataFrame({
    "Candidate Excluded File": df_ex["relative_path"],
    "Exact Comparator Source": df_ex["exact_comparator_source"],
    "Redundancy Evidence": df_ex["redundancy_evidence"],
    "Reason / Specific Rationale": df_ex["file_specific_rationale"]
})

df_nr_table = pd.DataFrame({
    "File Flagged for Review": df_nr["relative_path"],
    "Domain": df_nr["domain_folder"],
    "Observed IDs": df_nr["observed_distinct_ids"],
    "Scientific Role": df_nr["information_content"],
    "Action Required for Phase 2": df_nr["unresolved_action"]
})

display(HTML("<h4>Table 12.3A: Candidate Exclusions from Detailed EDA (4 Files, Pending Supervisor & Researcher Sign-Off)</h4>"))
display(HTML(df_ex_table.to_html(index=False, classes='table table-striped table-bordered')))

display(HTML("<h4>Table 12.3B: Items Flagged for Needs Review (30 Files: 23 Clinical Candidates + 5 Plausible Analysis Tables + 2 Duplicate Tables)</h4>"))
display(HTML(df_nr_table.to_html(index=False, classes='table table-striped table-bordered')))"""
    ))

    cells.append(nbf.v4.new_markdown_cell(
"""### 12.5 Priority Primary EDA Datasets with Verified Local Documentation
The following 11 core source files and 2 primary workbook worksheets (13 primary decision units total) are proposed as **Primary EDA** targets for subsequent project phases, each backed by verified local methods and protocol documentation with exact section/page locators:
- **Phase 3 (`eda_genetics.ipynb`)**: Consensus monogenic variant calls (*LRRK2*, *GBA*, *SNCA*, *PRKN*, *APOE*) and calculated polygenic risk scores (`Polygenic_Risk_Scores_09Nov2026.csv`).
- **Phase 4 (`eda_neuroimaging.ipynb`, `eda_digital_sensors.ipynb`)**: DaTscan striatal binding ratios (SBR quantitative and visual read), FreeSurfer structural MRI volumetrics (APARC cortical thickness, surface area, ASEG subcortical volumes), DTI white matter metrics, AV-133 VMAT2 PET SBR, resting-state fMRI session matrix, and Roche PD mobile active test telemetry (`Roche_PD_Monitoring_App_v2_data_09Nov2026.csv`).
- **Phase 5 (`eda_multimodal_synthesis.ipynb`)**: Cross-modal integration and synthesis leveraging the comprehensive curated longitudinal data cut (`PPMI_Curated_Data_Cut_Public_20260810(1).xlsx` sheet `[20260810]`).

*Candidate Clinical Progression Endpoints*: Core clinical progression instruments (MDS-UPDRS Parts I-IV, Schwab & England ADL, MoCA, Benton, SDMT, Hopkins, Letter-Number, Fluency, Boston Naming, Clock Drawing, Trail Making, SCOPA-AUT, GDS, STAI, QUIP, Epworth, RBDSQ, UPSIT) are currently routed to **Needs Review** pending formal Phase 2 scoring protocol cataloging. Participant demographics (`Demographics_09Nov2026.csv`) is classified as **Supporting** for cohort baseline adjustment and stratification."""
    ))

    cells.append(nbf.v4.new_code_cell(
"""# Primary EDA Datasets with Verified Local Documentation
primary_file_rows = [r for r in file_matrix if r["provisional_recommendation"] == "Primary EDA"]
primary_sheet_rows = [r for r in sheet_matrix if r["provisional_recommendation"] == "Primary EDA"]
all_primary = primary_file_rows + primary_sheet_rows
df_primary = pd.DataFrame(all_primary)

primary_summary = pd.DataFrame({
    "Primary EDA Target": df_primary["relative_path"],
    "Modality / Domain": df_primary["modality"] + " (" + df_primary["domain_folder"] + ")",
    "Target Notebook": df_primary["target_notebook"],
    "Documentation Source & Locator": df_primary["documentation_source"],
    "Observed Distinct IDs": df_primary["observed_distinct_ids"],
    "Eligible Cohort Denominator": df_primary["eligible_cohort_denominator"].apply(lambda d: f"{d:,}" if pd.notnull(d) and d != "" else "Unverified"),
    "Participant Coverage (%)": df_primary["participant_coverage_percent"].apply(lambda c: f"{c:.1f}%" if pd.notnull(c) and c != "" else "N/A"),
    "Observation Grain": df_primary["observation_grain"],
    "Candidate Primary Keys": df_primary["candidate_primary_keys"].apply(lambda k: "; ".join(k) if isinstance(k, list) and k else "None")
})

display(HTML(f"<h4>Table 12.4: Core Primary EDA Datasets with Verified Documentation (N={len(all_primary)}: {len(primary_file_rows)} Files + {len(primary_sheet_rows)} Sheets)</h4>"))
display(HTML(primary_summary.to_html(index=False, classes='table table-striped table-bordered')))"""
    ))

    cells.append(nbf.v4.new_markdown_cell(
"""### 12.6 Canonical 183-Unit Evidence & Prioritization Matrix
Below is the complete, auditable prioritization matrix covering all 177 source files and 6 worksheets (183 decision units total), displaying all 57 evaluation criteria, provenance, dimensions, quality metrics, longitudinal evidence semantics, and governance fields in an accessible, scrollable view."""
    ))

    cells.append(nbf.v4.new_code_cell(
"""# Complete Accessible 183-Unit Evidence & Prioritization Matrix (All 57 Audit Fields)
all_units = file_matrix + sheet_matrix
assert len(all_units) == 183, f"Expected 183 decision units, got {len(all_units)}"

matrix_rows = []
for u in all_units:
    keys_str = "; ".join(u["candidate_primary_keys"]) if u.get("candidate_primary_keys") else "None"
    concerns_str = "; ".join(u["quality_concerns"]) if u.get("quality_concerns") else "None"
    cov_pct = u.get("participant_coverage_percent")
    denom = u.get("eligible_cohort_denominator")
    null_rate = u.get("null_rate_percent")
    row_cnt = u.get("row_count")
    col_cnt = u.get("column_count")
    null_keys = u.get("null_key_counts", {})
    null_keys_str = f"null_patno={null_keys.get('null_patno', 0)}; null_event_id={null_keys.get('null_event_id', 0)}"
    target_nbs_str = "; ".join(u["target_notebooks"]) if u.get("target_notebooks") else u["target_notebook"]

    matrix_rows.append({
        "Relative Path": u["relative_path"],
        "File Name": u["file_name"],
        "Sheet Name": u["sheet_name"] or "N/A",
        "Domain Folder": u["domain_folder"],
        "Modality": u["modality"],
        "Format": u["format"],
        "SHA-256": u["sha256"],
        "Physical Read Status": u["physical_read_status"],
        "Row Count": str(row_cnt) if row_cnt is not None else "N/A",
        "Column Count": str(col_cnt) if col_cnt is not None else "N/A",
        "Worksheet Count": u["worksheet_count"],
        "Observation Grain": u["observation_grain"],
        "Grain Status": u["grain_status"],
        "Candidate Primary Keys": keys_str,
        "Duplicate Key Status": u["duplicate_key_status"],
        "Duplicate Rows Count": u["duplicate_rows_count"],
        "Observed Distinct IDs": u["observed_distinct_ids"],
        "Participant Count": u["participant_count"],
        "Eligible Cohort Denominator": str(denom) if denom is not None else "Unverified",
        "Participant Coverage (%)": f"{cov_pct:.1f}" if cov_pct is not None else "N/A",
        "Event Key Column": u.get("event_key_column") or "None",
        "Event Semantics": u.get("event_semantics") or "N/A",
        "Non-Null Event Record Count": str(u.get("non_null_event_record_count")) if u.get("non_null_event_record_count") is not None else "N/A",
        "Null Event Record Count": str(u.get("null_event_record_count")) if u.get("null_event_record_count") is not None else "N/A",
        "Distinct Raw Event Values": str(u.get("distinct_raw_event_values")) if u.get("distinct_raw_event_values") is not None else "N/A",
        "Participants With Non-Null Events": str(u.get("participants_with_non_null_events")) if u.get("participants_with_non_null_events") is not None else "N/A",
        "Participants With Repeated Events": str(u.get("participants_with_repeated_events")) if u.get("participants_with_repeated_events") is not None else "N/A",
        "Longitudinal Participant Denominator Name": u.get("longitudinal_participant_denominator_name") or "N/A",
        "Longitudinal Participant Denominator Count": str(u.get("longitudinal_participant_denominator_count")) if u.get("longitudinal_participant_denominator_count") is not None else "N/A",
        "Longitudinal Status": u.get("longitudinal_status") or "N/A",
        "Visit Count": u["visit_count"],
        "Distinct Visits Count": u["distinct_visits_count"],
        "Visit Coverage Scope": u["visit_coverage_scope"],
        "Longitudinal Depth": u["longitudinal_depth"],
        "Null Rate (%)": f"{null_rate:.1f}" if null_rate is not None else "N/A",
        "Null Key Counts": null_keys_str,
        "Documentation Status": u["documentation_status"],
        "Documentation Source": u["documentation_source"],
        "Quality Concerns": concerns_str,
        "Clinical & Scientific Relevance": u["clinical_scientific_relevance"],
        "Information Content": u["information_content"],
        "Participant & Visit Coverage": u["participant_visit_coverage"],
        "Longitudinal Usefulness": u["longitudinal_usefulness"],
        "Data Quality & Interpretability": u["data_quality_interpretability"],
        "Redundancy Evidence": u["redundancy_evidence"],
        "Multimodal Integration Value": u["multimodal_integration_value"],
        "Exact Comparator Source": u["exact_comparator_source"] or "None",
        "Proposed Category": u["proposed_category"],
        "Provisional Recommendation": u["provisional_recommendation"],
        "File-Specific Rationale": u["file_specific_rationale"],
        "Primary EDA Priority": u["primary_eda_priority"] or "N/A",
        "Unresolved Action": u["unresolved_action"] or "None",
        "Target Notebook": u["target_notebook"],
        "Target Notebooks": target_nbs_str,
        "Reviewer": u["reviewer"],
        "Decision Date": u["decision_date"],
        "Approval Status": u["approval_status"]
    })

df_full_display = pd.DataFrame(matrix_rows)
assert df_full_display.shape == (183, 57), f"Expected (183, 57), got {df_full_display.shape}"

table_html = df_full_display.to_html(index=False, classes='table table-striped table-bordered table-hover')
wrapped_html = f'''
<h4>Table 12.5: Canonical 183-Unit Evidence & Prioritization Matrix (All 57 Audit Fields)</h4>
<div style="max-height: 650px; overflow-x: auto; overflow-y: auto; border: 1px solid #ddd; margin: 10px 0;">
  {table_html}
</div>
<p style="font-size: 11px; color: #555;">Displaying all 183 decision units with all 57 criteria, dimensions, duplicate status, longitudinal evidence semantics, and structured documentation locators.</p>
'''
display(HTML(wrapped_html))"""
    ))

    cells.append(nbf.v4.new_markdown_cell(
"""### 12.7 Scientific Governance & Formal Approval Status
In accordance with `AGENTS.md` and `docs/phase_specs/dataset_selection_gate.md`:
1. **Pre-Review Status**: All recommendations displayed in this section are **provisional recommendations** authored by the Implementation Engineer (Gemini).
2. **Supervisory Review**: This complete evidence package is submitted to Codex for independent review and file-level recommendation certification.
3. **Researcher Sign-Off Gate**: Detailed EDA, feature engineering, and statistical modeling in Phase 2 (`eda_clinical.ipynb`) and Phase 3 (`eda_biospecimen.ipynb`, `eda_genetics.ipynb`) will commence **only** after the human researcher formally approves the final selection lists.

---
*End of Dataset Overview & Selection Gate Deliverable Notebook.*"""
    ))

    nb.cells = cells
    return nb

def main():
    repo_root = Path(__file__).resolve().parents[2]
    src_path = repo_root / "EDA" / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    notebook_path = repo_root / "00_dataset_overview.ipynb"
    print(f"Generating notebook structure at {notebook_path}...")
    nb = create_overview_notebook()

    with open(notebook_path, "w", encoding="utf-8") as f:
        nbf.write(nb, f)

    print("Executing notebook top-to-bottom with clean kernel...")
    ep = ExecutePreprocessor(timeout=600, kernel_name="python3")
    ep.preprocess(nb, {"metadata": {"path": str(repo_root)}})

    print("Saving executed notebook with cell outputs refreshed...")
    with open(notebook_path, "w", encoding="utf-8") as f:
        nbf.write(nb, f)

    print("Validating executed cell outputs with PrivacyGuard...")
    from ppmi_pipeline.reporting.privacy import PrivacyGuard
    
    # Read back executed notebook to inspect all cell outputs
    with open(notebook_path, "r", encoding="utf-8") as f:
        executed_nb = json.load(f)

    # Use thorough notebook output validator covering text, plain, html, markdown
    PrivacyGuard.validate_notebook_outputs(executed_nb)

    print("Privacy verification passed: Zero participant records or IDs in notebook outputs.")
    print("Notebook 00_dataset_overview.ipynb successfully created, executed, and verified!")

if __name__ == "__main__":
    main()
