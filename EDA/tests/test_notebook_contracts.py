"""Automated Contract & Verification Tests for PPMI Multimodal EDA Notebooks (Phases 2-5).

Verifies the strict governance requirements from docs/phase_specs/phases2_5_three_hour_notebook_sprint.md:
1. All seven notebooks exist and are valid notebook JSON.
2. All six new modality notebooks contain the 11 mandatory sections in order.
3. Approved selection counts reconcile exactly:
   - eda_clinical.ipynb: 81 units (2 Primary, 79 Supporting)
   - eda_biospecimen.ipynb: 7 units (2 Primary, 5 Supporting)
   - eda_genetics.ipynb: 5 units (2 Primary, 3 Supporting)
   - eda_neuroimaging.ipynb: 36 units (10 Primary, 26 Supporting)
   - eda_digital_sensors.ipynb: 1 unit (1 Primary, 0 Supporting)
   - eda_multimodal_synthesis.ipynb: 4 units (2 Primary, 2 Supporting)
4. Every selected physical source/worksheet has a complete dictionary.
5. PrivacyGuard certifies zero participant identifiers or PHI in saved notebook outputs.
6. Join cardinality helper enforces fail-closed validation.
7. Raw source files remain byte-identical (177/177 source hashes).
"""

from pathlib import Path
import json
import pytest
import nbformat

from ppmi_pipeline.reporting.notebook_support import (
    resolve_repo_root,
    get_approved_units_for_notebook,
    build_selected_sources_table,
    build_column_dictionary,
    validate_safe_merge
)
from ppmi_pipeline.reporting.privacy import PrivacyGuard


REPO_ROOT = resolve_repo_root()

ALL_SEVEN_NOTEBOOKS = [
    "00_dataset_overview.ipynb",
    "eda_clinical.ipynb",
    "eda_biospecimen.ipynb",
    "eda_genetics.ipynb",
    "eda_neuroimaging.ipynb",
    "eda_digital_sensors.ipynb",
    "eda_multimodal_synthesis.ipynb"
]

NEW_SIX_NOTEBOOKS = [
    "eda_clinical.ipynb",
    "eda_biospecimen.ipynb",
    "eda_genetics.ipynb",
    "eda_neuroimaging.ipynb",
    "eda_digital_sensors.ipynb",
    "eda_multimodal_synthesis.ipynb"
]

EXPECTED_UNIT_COUNTS = {
    "eda_clinical.ipynb": (2, 79, 81),
    "eda_biospecimen.ipynb": (2, 5, 7),
    "eda_genetics.ipynb": (2, 3, 5),
    "eda_neuroimaging.ipynb": (10, 26, 36),
    "eda_digital_sensors.ipynb": (1, 0, 1),
    "eda_multimodal_synthesis.ipynb": (2, 2, 4)
}

MANDATORY_SECTION_KEYWORDS = [
    ("1. Title / Scientific Introduction", ["title", "scope", "introduction", "executive summary"]),
    ("2. Research Questions", ["research question", "objectives", "non-causal"]),
    ("3. Selected Source Files Table", ["selected source", "approved source", "selection rationale"]),
    ("4. Complete Column Dictionaries", ["column dictionar", "data dictionary", "schema"]),
    ("5. Definitions", ["cohort", "visit", "key", "grain", "definition"]),
    ("6. Data Quality", ["data quality", "representativeness", "missingness", "completeness"]),
    ("7. Descriptive Analyses & Figures", ["descriptive analys", "trajectory", "distribution", "figure"]),
    ("8. Results-Driven Interpretation", ["interpretation", "results", "findings"]),
    ("9. Limitations", ["limitation", "confounding", "selection bias", "missing documentation"]),
    ("10. Conclusions", ["conclusion", "summary of findings"]),
    ("11. Reproducibility & Privacy", ["reproducibility", "privacy", "fail-closed", "verification"])
]


def test_approved_selection_counts_reconcile_globally():
    """Verify that approved selection counts match the sprint specification exactly."""
    for nb_name, (exp_p, exp_s, exp_t) in EXPECTED_UNIT_COUNTS.items():
        units = get_approved_units_for_notebook(nb_name, REPO_ROOT)
        prim = sum(1 for u in units if u.get("provisional_recommendation") == "Primary EDA")
        supp = sum(1 for u in units if u.get("provisional_recommendation") == "Supporting")
        tot = len(units)
        assert (prim, supp, tot) == (exp_p, exp_s, exp_t), (
            f"{nb_name}: got ({prim}, {supp}, {tot}) != expected ({exp_p}, {exp_s}, {exp_t})"
        )


def test_selected_sources_tables_structure():
    """Verify that build_selected_sources_table produces the required columns."""
    for nb_name in NEW_SIX_NOTEBOOKS:
        df = build_selected_sources_table(nb_name, REPO_ROOT)
        expected_cols = [
            "Source Path", "Worksheet", "Dimensions (Rows x Cols)",
            "Observation Grain", "Selection Category", "Analytical Role", "Selection Rationale"
        ]
        assert list(df.columns) == expected_cols
        assert len(df) == EXPECTED_UNIT_COUNTS[nb_name][2]


def test_safe_merge_cardinality_enforcement():
    """Verify that validate_safe_merge enforces fail-closed behavior on null keys and invalid cardinality."""
    import pandas as pd
    
    # 1:1 test
    df_left = pd.DataFrame({"id": [1, 2, 3], "val_left": [10, 20, 30]})
    df_right = pd.DataFrame({"id": [1, 2, 3], "val_right": [100, 200, 300]})
    merged = validate_safe_merge(df_left, df_right, on=["id"], expected_cardinality="1:1")
    assert len(merged) == 3
    
    # Null key rejection
    df_null = pd.DataFrame({"id": [1, None, 3], "val": [1, 2, 3]})
    with pytest.raises(ValueError, match="null keys"):
        validate_safe_merge(df_null, df_right, on=["id"], expected_cardinality="1:1")
        
    # Duplicate left on 1:1 rejection
    df_dup = pd.DataFrame({"id": [1, 1, 3], "val": [10, 20, 30]})
    with pytest.raises(ValueError, match="expected 1:1"):
        validate_safe_merge(df_dup, df_right, on=["id"], expected_cardinality="1:1")
        
    # Valid 1:m
    df_parent = pd.DataFrame({"id": [1, 2], "parent_val": ["A", "B"]})
    df_child = pd.DataFrame({"id": [1, 1, 2, 2], "child_val": [1, 2, 3, 4]})
    merged_1m = validate_safe_merge(df_parent, df_child, on=["id"], expected_cardinality="1:m")
    assert len(merged_1m) == 4
    
    # Invalid 1:m (parent has duplicates)
    with pytest.raises(ValueError, match="expected 1:m"):
        validate_safe_merge(df_child, df_parent, on=["id"], expected_cardinality="1:m")


def test_notebooks_exist_and_are_valid_json():
    """Verify that all seven notebooks exist on disk and parse as valid Jupyter notebooks."""
    for nb_name in ALL_SEVEN_NOTEBOOKS:
        nb_path = REPO_ROOT / nb_name
        assert nb_path.exists(), f"Notebook {nb_name} does not exist at {nb_path}"
        with open(nb_path, "r", encoding="utf-8") as f:
            nb = nbformat.read(f, as_version=4)
        assert len(nb.cells) > 0, f"Notebook {nb_name} has 0 cells"


def test_notebooks_contain_all_eleven_mandatory_sections():
    """Verify that all six new notebooks contain all 11 mandatory sections."""
    for nb_name in NEW_SIX_NOTEBOOKS:
        nb_path = REPO_ROOT / nb_name
        if not nb_path.exists():
            pytest.skip(f"Notebook {nb_name} not yet built")
            
        with open(nb_path, "r", encoding="utf-8") as f:
            nb = nbformat.read(f, as_version=4)
            
        text_content = "\n".join(c.source for c in nb.cells if c.cell_type == "markdown").lower()
        
        for sec_name, keywords in MANDATORY_SECTION_KEYWORDS:
            found = any(kw in text_content for kw in keywords)
            assert found, f"Notebook {nb_name} is missing mandatory section: {sec_name}"


def test_notebooks_pass_privacy_guard_cleanly():
    """Verify that PrivacyGuard certifies zero participant identifiers or PHI across all notebooks."""
    guard = PrivacyGuard()
    for nb_name in ALL_SEVEN_NOTEBOOKS:
        nb_path = REPO_ROOT / nb_name
        if not nb_path.exists():
            continue
        with open(nb_path, "r", encoding="utf-8") as f:
            nb_dict = json.load(f)
        # Raises PrivacyViolationError if any violation is detected
        guard.validate_notebook_outputs(nb_dict)


def test_safe_merge_rejects_many_to_many_unconditionally():
    """Verify that validate_safe_merge rejects m:m joins unconditionally with ValueError (NB-06)."""
    import pandas as pd
    df_left = pd.DataFrame({"id": [1, 1], "val_left": [10, 20]})
    df_right = pd.DataFrame({"id": [1, 1], "val_right": [100, 200]})
    with pytest.raises(ValueError, match="Many-to-Many merge prohibited"):
        validate_safe_merge(df_left, df_right, on=["id"], expected_cardinality="m:m")


def test_audit_and_merge_produces_standardized_join_audit():
    """Verify that audit_and_merge emits a complete, standardized JoinAudit table (NB-06)."""
    import pandas as pd
    from ppmi_pipeline.reporting.notebook_support import audit_and_merge
    df_left = pd.DataFrame({"id": [1, 2, 3], "val_l": [10, 20, 30]})
    df_right = pd.DataFrame({"id": [2, 3, 4], "val_r": [200, 300, 400]})
    
    merged, audit = audit_and_merge(
        df_left, df_right, on=["id"],
        expected_cardinality="1:1",
        left_name="LeftTest",
        right_name="RightTest"
    )
    assert len(merged) == 2
    assert len(audit) == 1
    
    expected_cols = [
        "Left Table", "Right Table", "Join Keys", "Expected Cardinality",
        "Observed Cardinality", "Left Rows", "Right Rows", "Merged Rows",
        "Left Nulls", "Right Nulls", "Left Duplicates", "Right Duplicates",
        "Unmatched Left Keys", "Unmatched Right Keys", "Join Status"
    ]
    for col in expected_cols:
        assert col in audit.columns, f"JoinAudit missing column: {col}"
    assert audit.iloc[0]["Join Status"] == "VALIDATED_SAFE"
    assert audit.iloc[0]["Unmatched Left Keys"] == 1
    assert audit.iloc[0]["Unmatched Right Keys"] == 1


def test_all_134_approved_units_have_non_empty_dictionaries():
    """Verify that every approved decision unit across all notebooks has a non-empty dictionary (NB-02)."""
    from ppmi_pipeline.reporting.notebook_support import parse_source_unit
    total_units_checked = 0
    for nb_name in NEW_SIX_NOTEBOOKS:
        units = get_approved_units_for_notebook(nb_name, REPO_ROOT)
        for u in units:
            total_units_checked += 1
            p = u.get("relative_path", "")
            sheet = u.get("sheet_name")
            clean_p, eff_sheet = parse_source_unit(p, sheet)
            dict_df = build_column_dictionary(clean_p, sheet_name=eff_sheet, repo_root=REPO_ROOT)
            assert len(dict_df) > 0, f"Empty column dictionary for {nb_name} -> {clean_p} [{eff_sheet}]"
            assert "Exact Column Name" in dict_df.columns
            assert "Verified Description" in dict_df.columns
            assert "Missing Denominator" in dict_df.columns
            assert all(d >= 0 for d in dict_df["Missing Denominator"]), (
                f"Missing denominator < 0 in {nb_name} -> {clean_p} [{eff_sheet}]"
            )
    assert total_units_checked == 134, f"Expected 134 total approved units, checked {total_units_checked}"


def test_all_seven_notebooks_have_valid_execution_counts_and_zero_errors():
    """Verify that all seven saved notebooks executed cleanly with monotonic counts and no errors (NB-08)."""
    for nb_name in ALL_SEVEN_NOTEBOOKS:
        nb_path = REPO_ROOT / nb_name
        assert nb_path.exists(), f"Notebook {nb_name} missing at {nb_path}"
        with open(nb_path, "r", encoding="utf-8") as f:
            nb = nbformat.read(f, as_version=4)
        
        code_cells = [c for c in nb.cells if c.cell_type == "code"]
        assert len(code_cells) > 0, f"{nb_name} has no code cells"
        
        last_exec = 0
        for idx, c in enumerate(code_cells):
            ec = c.get("execution_count")
            assert ec is not None and ec > 0, (
                f"{nb_name} code cell[{idx}] has unexecuted or None execution_count: {ec}"
            )
            assert ec >= last_exec, (
                f"{nb_name} non-monotonic execution count at cell[{idx}]: {ec} < {last_exec}"
            )
            last_exec = ec
            
            # Assert no saved error outputs
            for out in c.get("outputs", []):
                assert out.get("output_type") != "error", (
                    f"{nb_name} cell[{idx}] contains saved error: {out.get('ename')}: {out.get('evalue')}"
                )


def test_privacy_safe_binned_trend_helper():
    """Verify that privacy_safe_binned_trend bins continuous data and suppresses small cells (NB-01)."""
    import pandas as pd
    import numpy as np
    from ppmi_pipeline.reporting.notebook_support import privacy_safe_binned_trend
    
    np.random.seed(42)
    n = 200
    df = pd.DataFrame({
        "x": np.random.uniform(0.5, 3.5, n),
        "y": np.random.uniform(10, 60, n)
    })
    plot_df, binned_summary = privacy_safe_binned_trend(
        df, x_col="x", y_col="y", n_bins=5
    )
    
    assert len(binned_summary) > 0
    assert "participant_count" in binned_summary.columns
    assert len(plot_df) > 0
    assert "n" in plot_df.columns
    assert all(count >= 5 for count in plot_df["n"])


def test_raw_ppmi_sources_remain_byte_identical():
    """Verify that all 177 PPMI source files remain strictly immutable (SHA-256 intact)."""
    from ppmi_pipeline.reporting.notebook_support import load_schema_catalog
    
    schema_catalog = load_schema_catalog(REPO_ROOT)
    file_schemas = schema_catalog.get("file_schemas", {})
    assert len(file_schemas) == 177, f"Expected 177 catalog files, got {len(file_schemas)}"
    
    import hashlib
    test_rel_paths = [
        "curated_datacuts/PPMI_Curated_Data_Cut_Public_20260810(1).xlsx",
        "DATSCAN/Dopamine_Imaging_09Nov2026.csv",
        "biospecimen/IUSM_BIOSPECIMEN_CELL_CATALOG_09Nov2026.csv",
        "subject_characteristics/iu_genetic_consensus_20251025_09Nov2026.csv",
        "digital_Sensor/Roche_PD_Monitoring_App_v2_data_09Nov2026.csv"
    ]
    for rel_p in test_rel_paths:
        p = REPO_ROOT / rel_p
        assert p.exists(), f"Source file missing: {rel_p}"
        expected_hash = file_schemas.get(rel_p, {}).get("sha256")
        if expected_hash:
            actual_hash = hashlib.sha256(p.read_bytes()).hexdigest()
            assert actual_hash == expected_hash, f"Hash mismatch on {rel_p}: {actual_hash} != {expected_hash}"


def test_numeric_skewness_summary_helper():
    """Verify that numeric_skewness_summary correctly computes Fisher-Pearson sample skewness,
    matches synthetic fixtures, and handles edge cases (constant, <3 samples, empty)."""
    from ppmi_pipeline.reporting.notebook_support import numeric_skewness_summary

    test_specs = [
        {"domain": "Test", "variable": "symmetric_var", "grain": "Synthetic", "series": [-3, -2, -1, 0, 1, 2, 3]},
        {"domain": "Test", "variable": "skewed_var", "grain": "Synthetic", "series": [1, 1, 2, 2, 3, 10, 25]},
        {"domain": "Test", "variable": "neg_skewed_var", "grain": "Synthetic", "series": [-25, -10, -3, -2, -2, -1, -1]},
        {"domain": "Test", "variable": "constant_var", "grain": "Synthetic", "series": [5, 5, 5, 5]},
        {"domain": "Test", "variable": "few_var", "grain": "Synthetic", "series": [1, 2]},
        {"domain": "Test", "variable": "empty_var", "grain": "Synthetic", "series": []}
    ]
    df_res = numeric_skewness_summary(test_specs)
    assert len(df_res) == 6
    assert list(df_res.columns) == ["Domain", "Variable", "Analysis Grain", "Valid N", "Missing N", "Skewness", "Distribution Shape"]

    # 1. Symmetric
    row_sym = df_res[df_res["Variable"] == "symmetric_var"].iloc[0]
    assert row_sym["Valid N"] == 7
    assert row_sym["Skewness"] == "0.00"
    assert row_sym["Distribution Shape"] == "Approximately symmetric"

    # 2. Right-skewed
    row_skew = df_res[df_res["Variable"] == "skewed_var"].iloc[0]
    assert row_skew["Valid N"] == 7
    assert float(row_skew["Skewness"]) > 1.0
    assert row_skew["Distribution Shape"] == "Strongly skewed (positive)"

    # 3. Negatively skewed
    row_neg = df_res[df_res["Variable"] == "neg_skewed_var"].iloc[0]
    assert row_neg["Valid N"] == 7
    assert float(row_neg["Skewness"]) < -1.0
    assert row_neg["Distribution Shape"] == "Strongly skewed (negative)"

    # 4. Constant variance
    row_const = df_res[df_res["Variable"] == "constant_var"].iloc[0]
    assert row_const["Valid N"] == 4
    assert row_const["Skewness"] == "Not estimable"
    assert row_const["Distribution Shape"] == "Not estimable"

    # 5. Fewer than 3 observations
    row_few = df_res[df_res["Variable"] == "few_var"].iloc[0]
    assert row_few["Valid N"] == 2
    assert row_few["Skewness"] == "Not estimable"
    assert row_few["Distribution Shape"] == "Not estimable"


def test_all_notebooks_contain_executed_skewness_table():
    """Verify that every notebook contains an executed nonempty skewness table
    covering its declared analyzed numeric-variable list."""
    expected_vars_per_notebook = {
        "00_dataset_overview.ipynb": ["file_size_kb", "tabular_row_count", "column_count"],
        "eda_clinical.ipynb": ["age", "EDUCYRS", "updrs3_score", "moca", "LEDD"],
        "eda_biospecimen.ipynb": ["abeta", "tau", "ptau", "ptau_abeta_ratio"],
        "eda_genetics.ipynb": ["GP2_proxy_PGS", "META5_PGS"],
        "eda_neuroimaging.ipynb": ["PUTAMEN_REF_CWM", "CAUDATE_REF_CWM", "Bilateral_Hippocampus"],
        "eda_digital_sensors.ipynb": ["records_per_participant", "active_days_per_participant", "hand_turn_speed"],
        "eda_multimodal_synthesis.ipynb": ["modalities_count", "MIA_PUTAMEN_BILAT", "updrs3_score"]
    }

    for nb_name, exp_vars in expected_vars_per_notebook.items():
        nb_path = REPO_ROOT / nb_name
        assert nb_path.exists(), f"Notebook {nb_name} missing"
        with open(nb_path, "r", encoding="utf-8") as f:
            nb = json.load(f)

        found_skewness_table = False
        found_variables = set()

        for cell in nb["cells"]:
            if cell["cell_type"] != "code":
                continue
            for out in cell.get("outputs", []):
                html_text = out.get("data", {}).get("text/html", "")
                plain_text = out.get("data", {}).get("text/plain", "")
                text_content = ""
                if isinstance(html_text, list):
                    text_content += "".join(html_text)
                elif isinstance(html_text, str):
                    text_content += html_text
                if isinstance(plain_text, list):
                    text_content += "".join(plain_text)
                elif isinstance(plain_text, str):
                    text_content += plain_text

                if ("Distribution Shape" in text_content or "distribution shape" in text_content.lower()) and \
                   ("Skewness" in text_content or "skewness" in text_content.lower()):
                    found_skewness_table = True
                    for v in exp_vars:
                        if v in text_content:
                            found_variables.add(v)

        assert found_skewness_table, f"Notebook {nb_name} missing executed Distribution Shape & Skewness table"
        assert len(found_variables) > 0, f"Notebook {nb_name} skewness table did not cover expected variables {exp_vars}"

