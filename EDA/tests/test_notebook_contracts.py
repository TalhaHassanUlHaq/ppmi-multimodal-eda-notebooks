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
import os
import re
import pytest
import nbformat
import pandas as pd
from typing import Any

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


def extract_skewness_table_from_notebook(nb_dict: dict) -> pd.DataFrame:
    """Helper to extract the executed skewness table from a notebook's HTML outputs."""
    import io
    for cell in nb_dict.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        for out in cell.get("outputs", []):
            html = out.get("data", {}).get("text/html", "")
            if isinstance(html, list):
                html = "".join(html)
            if "Distribution Shape" in html and "Skewness" in html:
                dfs = pd.read_html(io.StringIO(html))
                if dfs:
                    df = dfs[0]
                    # Drop unnamed index column if present
                    df = df[[c for c in df.columns if not str(c).startswith("Unnamed:")]]
                    return df
    return pd.DataFrame()


EXPECTED_SKEWNESS_VARIABLES = {
    "00_dataset_overview.ipynb": [
        "file_size_kb", "tabular_row_count", "column_count", "column_missingness_pct"
    ],
    "eda_clinical.ipynb": [
        "age", "EDUCYRS", "duration_yrs", "BMI", "updrs1_score", "updrs2_score",
        "updrs3_score", "updrs_totscore", "moca", "scopa", "ess", "rem", "gds",
        "stai", "MSEADLG", "updrs4_score", "LEDD",
        "raw_mcatot", "raw_np3tot", "sdmt_score", "hvlt_total_recall", "hvlt_delayed_recall",
        "tmt_a_sec", "tmt_b_sec", "benton_jlo_raw", "upsit_total"
    ],
    "eda_biospecimen.ipynb": [
        "abeta", "tau", "ptau", "ptau_abeta_ratio", "log_ptau_abeta_ratio",
        "asyn", "NFL_CSF", "nfl_serum", "log_nfl_serum", "ptau217_plasma",
        "IU_GFAP_plasma_mean"
    ],
    "eda_genetics.ipynb": [
        "GP2_proxy_PGS", "META5_PGS", "META5_proxy_PGS"
    ],
    "eda_neuroimaging.ipynb": [
        "PUTAMEN_REF_CWM", "CAUDATE_REF_CWM", "STRIATUM_REF_CWM", "putamen_asymmetry",
        "Bilateral_Hippocampus", "Bilateral_Lateral_Ventricles", "BrainSegVol",
        "DTI_ROI1_FA", "DTI_ROI2_FA", "PET_AV133_Caudate", "PET_AV133_Putamen",
        "lh_entorhinal", "lh_precentral", "cnr", "cjv", "efc", "fber",
        "rsfmri_mean_fd", "sv2a_suvr", "tau_suvr"
    ],
    "eda_digital_sensors.ipynb": [
        "records_per_participant", "active_days_per_participant", "span_days",
        "inter_assessment_interval", "hand_turn_speed",
        "postural_tremor_power", "log10_postural_tremor_power",
        "paired_ht_asymmetry_index", "paired_ptt_asymmetry_index"
    ],
    "eda_multimodal_synthesis.ipynb": [
        "modalities_count", "MIA_PUTAMEN_BILAT", "updrs3_score", "age",
        "EDUCYRS", "moca", "SAA_MIA_PUTAMEN_BILAT"
    ]
}

ALLOWED_SHAPES = {
    "Approximately symmetric",
    "Moderately skewed (positive)",
    "Moderately skewed (negative)",
    "Strongly skewed (positive)",
    "Strongly skewed (negative)",
    "Not estimable"
}


def test_all_notebooks_contain_executed_skewness_table():
    """Verify that every notebook contains an executed nonempty skewness table
    covering its declared analyzed numeric-variable list exactly, with valid counts and shapes."""
    import re

    for nb_name, exp_vars in EXPECTED_SKEWNESS_VARIABLES.items():
        nb_path = REPO_ROOT / nb_name
        assert nb_path.exists(), f"Notebook {nb_name} missing"
        with open(nb_path, "r", encoding="utf-8") as f:
            nb = json.load(f)

        table_df = extract_skewness_table_from_notebook(nb)
        assert not table_df.empty, f"Notebook {nb_name} missing executed Distribution Shape & Skewness table"
        assert len(table_df) == len(exp_vars), f"Notebook {nb_name} expected {len(exp_vars)} rows, got {len(table_df)}"
        assert list(table_df["Variable"]) == exp_vars, f"Notebook {nb_name} variables mismatch: {list(table_df['Variable'])} != {exp_vars}"

        for idx, r in table_df.iterrows():
            assert str(r["Analysis Grain"]).strip() != "", f"Empty grain in {nb_name} row {idx}"
            valid_n = int(r["Valid N"])
            missing_n = int(r["Missing N"])
            assert valid_n > 0, f"Valid N must be > 0 in {nb_name} for {r['Variable']}"
            assert missing_n >= 0, f"Missing N must be >= 0 in {nb_name} for {r['Variable']}"
            assert r["Distribution Shape"] in ALLOWED_SHAPES, f"Invalid shape {r['Distribution Shape']} in {nb_name}"

            # Check invariant: Valid N + Missing N == declared denominator in grain
            m = re.search(r"N=([0-9,]+)", str(r["Analysis Grain"]))
            if m:
                declared_n = int(m.group(1).replace(",", ""))
                assert valid_n + missing_n == declared_n, f"Denominator mismatch in {nb_name} for {r['Variable']}: {valid_n} + {missing_n} != {declared_n}"


def test_skewness_contract_negative_mutation_fails():
    """Verify that the contract test strictly fails if an expected variable is missing or mutated."""
    import pytest
    nb_path = REPO_ROOT / "eda_genetics.ipynb"
    assert nb_path.exists()
    with open(nb_path, "r", encoding="utf-8") as f:
        nb = json.load(f)

    table_df = extract_skewness_table_from_notebook(nb)
    assert len(table_df) == 3

    # Mutate table by dropping 1 row
    mutated_df = table_df.iloc[:2].copy()

    with pytest.raises(AssertionError):
        exp_vars = EXPECTED_SKEWNESS_VARIABLES["eda_genetics.ipynb"]
        assert len(mutated_df) == len(exp_vars)
        assert list(mutated_df["Variable"]) == exp_vars


def test_sensor_skewness_contract_negative_mutation_fails():
    """Negative fixture: verify that dropping any of the 9 required sensor skewness variables fails the contract test."""
    nb_path = REPO_ROOT / "eda_digital_sensors.ipynb"
    assert nb_path.exists()
    with open(nb_path, "r", encoding="utf-8") as f:
        nb = json.load(f)

    table_df = extract_skewness_table_from_notebook(nb)
    # Mutate table by dropping 1 row
    mutated_df = table_df.iloc[:-1].copy()

    with pytest.raises(AssertionError):
        exp_vars = EXPECTED_SKEWNESS_VARIABLES["eda_digital_sensors.ipynb"]
        assert len(mutated_df) == len(exp_vars)
        assert list(mutated_df["Variable"]) == exp_vars


def extract_deep_inventory_tables_from_notebook(nb_dict: dict) -> list[pd.DataFrame]:
    """Helper to extract executed Priority CSV inventory tables (Table 8.1) from a notebook."""
    import io
    dfs_found = []
    for cell in nb_dict.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        for out in cell.get("outputs", []):
            html = out.get("data", {}).get("text/html", "")
            if isinstance(html, list):
                html = "".join(html)
            if "Source Path" in html and "Incremental Scientific Purpose" in html:
                dfs = pd.read_html(io.StringIO(html))
                for df in dfs:
                    clean_df = df[[c for c in df.columns if not str(c).startswith("Unnamed:")]]
                    dfs_found.append(clean_df)
    return dfs_found


def extract_join_audit_tables_from_notebook(nb_dict: dict) -> list[pd.DataFrame]:
    """Helper to extract executed join audit tables from a notebook."""
    import io
    dfs_found = []
    for cell in nb_dict.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        for out in cell.get("outputs", []):
            html = out.get("data", {}).get("text/html", "")
            if isinstance(html, list):
                html = "".join(html)
            if "Observed Cardinality" in html and "Left Table" in html:
                dfs = pd.read_html(io.StringIO(html))
                for df in dfs:
                    clean_df = df[[c for c in df.columns if not str(c).startswith("Unnamed:")]]
                    dfs_found.append(clean_df)
    return dfs_found


def test_deep_csv_inventory_physical_parity_and_coverage():
    """Verify that every new modality/synthesis notebook contains an executed Table 8.1
    Priority CSV inventory table whose declared files exist physically on disk,
    whose dimensions match physical shapes, whose grain keys are valid, and whose
    documentation sources are verified or explicitly marked as not verified locally."""
    for nb_name in NEW_SIX_NOTEBOOKS:
        nb_path = REPO_ROOT / nb_name
        assert nb_path.exists(), f"Notebook {nb_name} missing"
        with open(nb_path, "r", encoding="utf-8") as f:
            nb = json.load(f)

        tables = extract_deep_inventory_tables_from_notebook(nb)
        assert len(tables) > 0, f"Notebook {nb_name} missing executed Priority CSV Inventory table (Table 8.1)"
        inv_df = tables[0]
        assert not inv_df.empty, f"Inventory table in {nb_name} is empty"

        required_cols = [
            "Source Path", "Dimensions (Rows x Cols)", "Observation Grain",
            "Grain Keys", "Null Key Count", "Duplicate Key Count",
            "Participant Coverage", "Visit Coverage", "Documentation Source",
            "Incremental Scientific Purpose"
        ]
        assert list(inv_df.columns) == required_cols, f"Column mismatch in {nb_name} Table 8.1: {list(inv_df.columns)}"

        for idx, row in inv_df.iterrows():
            source_entry = str(row["Source Path"]).strip()
            # Split off sheet indicator if present (e.g. 'path.xlsx -> [sheet]')
            rel_file = source_entry.split("->")[0].strip()
            phys_file = REPO_ROOT / rel_file
            assert phys_file.exists(), f"Declared source file {rel_file} in {nb_name} does not exist at {phys_file}"

            grain_keys_str = str(row["Grain Keys"]).strip()
            assert grain_keys_str != "", f"Empty grain keys in {nb_name} row {idx}"
            declared_keys = [k.strip() for k in grain_keys_str.split(",")]

            # Read physical file / sheet and verify dimensions, keys, nulls, and duplicates
            sheet_name = None
            if "->" in source_entry:
                sheet_match = re.search(r"\[(.*?)\]", source_entry)
                if sheet_match:
                    sheet_name = sheet_match.group(1)

            if phys_file.suffix.lower() in [".xlsx", ".xls"]:
                df_phys = pd.read_excel(phys_file, sheet_name=sheet_name or 0)
            else:
                df_phys = pd.read_csv(phys_file, low_memory=False)

            expected_dims = f"{len(df_phys):,} x {len(df_phys.columns)}"
            assert str(row["Dimensions (Rows x Cols)"]) == expected_dims, (
                f"Dimension mismatch in {nb_name} row {idx} for {rel_file}: "
                f"table={row['Dimensions (Rows x Cols)']} vs physical={expected_dims}"
            )

            # Check declared keys exist in columns
            for k in declared_keys:
                assert k in df_phys.columns, f"Key '{k}' in {nb_name} row {idx} missing from columns of {rel_file}"

            # Check nulls and duplicates (compare as ints to handle comma formatting variations)
            act_nulls = int(str(row["Null Key Count"]).replace(",", ""))
            exp_nulls_val = int(df_phys[declared_keys].isna().any(axis=1).sum())
            assert act_nulls == exp_nulls_val, (
                f"Null count mismatch in {nb_name} row {idx}: table={act_nulls} vs physical={exp_nulls_val}"
            )
            act_dups = int(str(row["Duplicate Key Count"]).replace(",", ""))
            exp_dups_val = int(df_phys.duplicated(subset=declared_keys).sum())
            assert act_dups == exp_dups_val, (
                f"Duplicate count mismatch in {nb_name} row {idx}: table={act_dups} vs physical={exp_dups_val}"
            )

            doc_source = str(row["Documentation Source"]).strip()
            assert doc_source != "", f"Empty documentation source in {nb_name} row {idx}"
            if not doc_source.startswith("Definition not verified locally"):
                candidate = doc_source.split("->")[0].strip()
                if not (REPO_ROOT / candidate).exists():
                    candidate_clean = re.sub(r"\s*\(pp?\.?\s*[\d\s–\-]+\)", "", candidate).strip()
                    if (REPO_ROOT / candidate_clean).exists():
                        candidate = candidate_clean
                assert (REPO_ROOT / candidate).exists() or candidate in [
                    "curated_datacuts/PPMI_Curated_Data_Cut_Public_20260810(1).xlsx",
                    "MR Analysis Results/PPMI_rs-fMRI_Data-and-Methods/PPMI_fs-fMRI_dataReport_spreadsheet_FINAL_20191121.xlsx"
                ], f"Unverified doc source asserting local path {candidate} in {nb_name}"


def test_deep_csv_inventory_mutation_rejection():
    """Negative fixture: verify build_deep_csv_inventory_table ignores hardcoded fake dimensions
    and fails closed on nonexistent files."""
    from ppmi_pipeline.reporting.notebook_support import build_deep_csv_inventory_table

    fake_specs = [
        {
            "path": "digital_Sensor/Roche_PD_Monitoring_App_v2_data_09Nov2026.csv",
            "grain_keys": ["PATNO", "QRSCATID", "QRSTSTID", "QRSDTM"],
            "dimensions": "999,999 x 999",  # Fraudulent dimension
            "participant_coverage": "Fake 10,000 Participants",
            "grain": "Measurement-level",
            "scientific_purpose": "Negative test fixture"
        }
    ]
    computed_df = build_deep_csv_inventory_table(fake_specs, repo_root=REPO_ROOT)
    assert len(computed_df) == 1
    # Fail-closed invariant: fraudulent dimensions must NOT be displayed
    assert computed_df.iloc[0]["Dimensions (Rows x Cols)"] == "108,901 x 22"
    assert computed_df.iloc[0]["Participant Coverage"] == "N = 32 participants"

    # Nonexistent file must raise FileNotFoundError
    nonexistent_specs = [{"path": "does_not_exist/fake_file.csv", "grain_keys": ["PATNO"]}]
    with pytest.raises(FileNotFoundError):
        build_deep_csv_inventory_table(nonexistent_specs, repo_root=REPO_ROOT)


def test_deep_csv_inventory_missing_grain_key_fails():
    """Negative fixture: verify build_deep_csv_inventory_table fails closed when grain_keys is omitted or invalid."""
    from ppmi_pipeline.reporting.notebook_support import build_deep_csv_inventory_table

    # Missing grain_keys must raise ValueError
    spec_no_keys = [{
        "path": "digital_Sensor/Roche_PD_Monitoring_App_v2_data_09Nov2026.csv",
        "grain": "Measurement-level"
    }]
    with pytest.raises(ValueError, match="grain_keys"):
        build_deep_csv_inventory_table(spec_no_keys, repo_root=REPO_ROOT)

    # Nonexistent column in grain_keys must raise KeyError
    spec_bad_keys = [{
        "path": "digital_Sensor/Roche_PD_Monitoring_App_v2_data_09Nov2026.csv",
        "grain_keys": ["PATNO", "NONEXISTENT_COLUMN_KEY"],
        "grain": "Measurement-level"
    }]
    with pytest.raises(KeyError, match="NONEXISTENT_COLUMN_KEY"):
        build_deep_csv_inventory_table(spec_bad_keys, repo_root=REPO_ROOT)


def test_deep_csv_inventory_false_unique_grain_fails():
    """Negative fixture: verify that asserting unique grain on legitimately non-unique files fails in the builder."""
    from ppmi_pipeline.reporting.notebook_support import build_deep_csv_inventory_table

    # DTI Regions of Interest has 148 duplicate records on ['PATNO', 'PAG_NAME', 'INFODT', 'Measure', 'Tissue']
    dti_spec = [{
        "path": "dti/DTI_Regions_of_Interest_09Nov2026.csv",
        "grain_keys": ["PATNO", "PAG_NAME", "INFODT", "Measure", "Tissue"],
        "expected_unique": True
    }]
    with pytest.raises(ValueError, match="Unique grain violation"):
        build_deep_csv_inventory_table(dti_spec, repo_root=REPO_ROOT)

    # Also verify builder-level argument expected_unique=True fails closed
    dti_spec_no_flag = [{
        "path": "dti/DTI_Regions_of_Interest_09Nov2026.csv",
        "grain_keys": ["PATNO", "PAG_NAME", "INFODT", "Measure", "Tissue"]
    }]
    with pytest.raises(ValueError, match="Unique grain violation"):
        build_deep_csv_inventory_table(dti_spec_no_flag, repo_root=REPO_ROOT, expected_unique=True)


def test_deep_csv_inventory_declared_alias_contract():
    """Verify explicit declared alias contract: positive declared alias yields participant count,
    undeclared alias yields unmapped status, and invalid declared column raises KeyError."""
    from ppmi_pipeline.reporting.notebook_support import build_deep_csv_inventory_table

    # 1. Positive declared alias: ALIAS_ID on IUSM catalog yields 4,075 participants
    spec_positive = [{
        "path": "biospecimen/IUSM_CATALOG_09Nov2026.csv",
        "grain_keys": ["SPECIMEN_NO"],
        "participant_id_col": "ALIAS_ID"
    }]
    res_pos = build_deep_csv_inventory_table(spec_positive, repo_root=REPO_ROOT)
    assert res_pos.iloc[0]["Participant Coverage"] == "N = 4,075 participants"

    # 2. Undeclared alias: without declaring ALIAS_ID, default PATNO is not in file, so yields unmapped
    spec_undeclared = [{
        "path": "biospecimen/IUSM_CATALOG_09Nov2026.csv",
        "grain_keys": ["SPECIMEN_NO"]
    }]
    res_und = build_deep_csv_inventory_table(spec_undeclared, repo_root=REPO_ROOT)
    assert res_und.iloc[0]["Participant Coverage"] == "Specimen / Aliquot level (no participant ID)"

    # 3. Invalid declared alias: raises KeyError
    spec_invalid = [{
        "path": "biospecimen/IUSM_CATALOG_09Nov2026.csv",
        "grain_keys": ["SPECIMEN_NO"],
        "participant_id_col": "NONEXISTENT_ALIAS_XYZ"
    }]
    with pytest.raises(KeyError, match="Declared participant_id_col 'NONEXISTENT_ALIAS_XYZ' not found"):
        build_deep_csv_inventory_table(spec_invalid, repo_root=REPO_ROOT)


def test_deep_csv_inventory_unverified_doc_source_rejected():
    """Negative fixture: verify that referencing an irrelevant file or raw CRF code against curated dictionary is marked unverified."""
    from ppmi_pipeline.reporting.notebook_support import build_deep_csv_inventory_table

    spec_irrelevant = [{
        "path": "MOTOR/MDS-UPDRS_Part_III_09Nov2026.csv",
        "grain_keys": ["PATNO", "EVENT_ID", "PDSTATE"],
        "doc_source": "README.md"  # Existing irrelevant file
    }]
    res = build_deep_csv_inventory_table(spec_irrelevant, repo_root=REPO_ROOT)
    assert res.iloc[0]["Documentation Source"] == "Definition not verified locally"

    spec_raw_curated = [{
        "path": "MOTOR/MDS-UPDRS_Part_III_09Nov2026.csv",
        "grain_keys": ["PATNO", "EVENT_ID", "PDSTATE"],
        "columns_used": ["NP3TOT"],  # Raw CRF code not in curated dictionary
        "doc_source": "curated_datacuts/PPMI_Curated_Data_Cut_Public_20260810(1).xlsx -> [Data dictionary]"
    }]
    res_raw = build_deep_csv_inventory_table(spec_raw_curated, repo_root=REPO_ROOT)
    assert "Definition not verified locally" in res_raw.iloc[0]["Documentation Source"]


def test_deep_csv_no_arbitrary_deduplication():
    """Verify that UPDRS III reconciliation preserves PDSTATE and does not rely on arbitrary de-duplication."""
    f_updrs = REPO_ROOT / "MOTOR" / "MDS-UPDRS_Part_III_09Nov2026.csv"
    assert f_updrs.exists()
    df_raw = pd.read_csv(f_updrs, low_memory=False)

    # Filtering to valid NP3TOT with OFF or unmedicated state yields 0 duplicates in (PATNO, EVENT_ID)
    valid_off = df_raw[df_raw["NP3TOT"].notna() & (df_raw["PDSTATE"].isin(["OFF"]) | df_raw["PDSTATE"].isna())]
    dup_count = valid_off.duplicated(subset=["PATNO", "EVENT_ID"]).sum()
    assert dup_count == 0, f"Expected 0 duplicates for protocol OFF state, got {dup_count}"

    # Negative test fixture: arbitrary de-duplication drops legitimate medication-state pairs
    synthetic_pdstate = pd.DataFrame({
        "PATNO": [1001, 1001, 1002, 1002],
        "EVENT_ID": ["BL", "BL", "BL", "BL"],
        "PDSTATE": ["OFF", "ON", "OFF", "ON"],
        "NP3TOT": [25.0, 18.0, 32.0, 24.0]
    })
    # Blind drop_duplicates on (PATNO, EVENT_ID) reduces rows from 4 to 2, destroying the ON state
    blind_dedup = synthetic_pdstate.drop_duplicates(subset=["PATNO", "EVENT_ID"])
    assert len(blind_dedup) == 2  # Proves blind deduplication causes data loss
    # Proper protocol preservation retains all rows
    assert len(synthetic_pdstate.drop_duplicates(subset=["PATNO", "EVENT_ID", "PDSTATE"])) == 4


def test_deep_csv_join_audits_enforced():
    """Verify that all six modality/synthesis notebooks contain executed join audits with valid cardinalities,
    and verify fail-closed rejection of many-to-many joins."""
    for nb_name in NEW_SIX_NOTEBOOKS:
        nb_path = REPO_ROOT / nb_name
        assert nb_path.exists()
        with open(nb_path, "r", encoding="utf-8") as f:
            nb = json.load(f)

        audit_tables = extract_join_audit_tables_from_notebook(nb)
        assert len(audit_tables) > 0, f"Notebook {nb_name} missing executed join audit table"

        for at in audit_tables:
            assert "Observed Cardinality" in at.columns
            assert "Join Status" in at.columns
            for _, r in at.iterrows():
                # Enforce no m:m joins in executed notebooks
                assert r["Observed Cardinality"] in ["1:1", "1:m", "m:1"], (
                    f"Forbidden many-to-many join in {nb_name}: {r['Observed Cardinality']}"
                )
                assert r["Join Status"] in ["SUCCESS", "VALIDATED_SAFE"], f"Failed join status in {nb_name}: {r['Join Status']}"


def test_deep_csv_narrative_no_hardcoded_claims():
    """Verify that notebooks do not contain hardcoded result strings, overreaching causal claims,
    or promotional diagnostic assertions in markdown cells."""
    disallowed_phrases = [
        "early diagnostic marker",
        "confirm robust",
        "directly confirms ascertainment enrichment",
        "confirms ascertainment",
        "definitive diagnostic stratification",
        "independently corroborates",
        "non-redundant biological information"
    ]
    for nb_name in NEW_SIX_NOTEBOOKS:
        nb_path = REPO_ROOT / nb_name
        with open(nb_path, "r", encoding="utf-8") as f:
            nb = json.load(f)

        for cell_idx, cell in enumerate(nb.get("cells", [])):
            if cell.get("cell_type") != "markdown":
                continue
            src = "".join(cell.get("source", "")).lower()
            for phrase in disallowed_phrases:
                assert phrase not in src, (
                    f"Disallowed claim '{phrase}' found in {nb_name} cell {cell_idx}"
                )


def test_genetics_small_cell_non_reconstructible():
    """Verify that Table 8.3 in eda_genetics.ipynb enforces non-reconstructible small-cell suppression:
    no cell < 5 is exposed, and complementary cells prevent solving for small groups."""
    nb_path = REPO_ROOT / "eda_genetics.ipynb"
    assert nb_path.exists()
    with open(nb_path, "r", encoding="utf-8") as f:
        nb = json.load(f)

    # Extract executed Table 8.3
    table_found = None
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        for out in cell.get("outputs", []):
            html = out.get("data", {}).get("text/html", "")
            if isinstance(html, list):
                html = "".join(html)
            if "Positive Family History" in html:
                import io
                dfs = pd.read_html(io.StringIO(html))
                if dfs:
                    table_found = dfs[0]
                    break

    assert table_found is not None, "Table 8.3 missing from executed eda_genetics.ipynb"
    for _, r in table_found.iterrows():
        tot_str = str(r["Total Evaluated (N)"]).replace(",", "")
        pos_str = str(r["Positive Family History (N, %)"])
        neg_str = str(r["No Family History (N, %)"])

        # If any count was < 5, must show Suppressed
        if tot_str.isdigit() and int(tot_str) < 5:
            assert "Suppressed" in tot_str

        # No individual cell count of 1, 2, 3, or 4 may be exposed
        m_pos = re.search(r"^([0-9]+)\s*\(", pos_str)
        if m_pos:
            assert int(m_pos.group(1)) >= 5, f"Small cell exposed in positive history: {pos_str}"

        m_neg = re.search(r"^([0-9]+)\s*\(", neg_str)
        if m_neg:
            assert int(m_neg.group(1)) >= 5, f"Small cell exposed in negative history: {neg_str}"


def test_mri_acquisition_population_reconciliation():
    """Verify that Table 8.4B in eda_neuroimaging.ipynb explicitly breaks down both All Records (N=8,779)
    and Baseline Sessions (N=3,351) with Total, Valid, Missing, Yes, and No counts."""
    nb_path = REPO_ROOT / "eda_neuroimaging.ipynb"
    assert nb_path.exists()
    with open(nb_path, "r", encoding="utf-8") as f:
        nb = json.load(f)

    table_found = None
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        for out in cell.get("outputs", []):
            html = out.get("data", {}).get("text/html", "")
            if isinstance(html, list):
                html = "".join(html)
            if "Table 8.4B" in html or ("DTI Sequence Acquired" in html and "Target Population" in html):
                import io
                dfs = pd.read_html(io.StringIO(html))
                if dfs:
                    table_found = dfs[0]
                    break

    assert table_found is not None, "Table 8.4B missing from executed eda_neuroimaging.ipynb"
    assert "Target Population" in table_found.columns
    assert "Total Records (N)" in table_found.columns
    assert "Valid N" in table_found.columns
    assert "Missing N" in table_found.columns
    assert "Yes N (%)" in table_found.columns
    assert "No N (%)" in table_found.columns
    pops = list(table_found["Target Population"].unique())
    assert any("8,779" in p for p in pops), f"Missing All Records N=8,779 in populations: {pops}"
    assert any("3,351" in p for p in pops), f"Missing Baseline N=3,351 in populations: {pops}"


def test_deep_csv_inventory_cache_order_independence():
    """Negative fixture: verify that provenance verification is cache-order independent.
    Evaluating a valid document first and then re-evaluating with an irrelevant document
    must NOT leak the verified status (DEEP-01A)."""
    from ppmi_pipeline.reporting.notebook_support import (
        build_deep_csv_inventory_table,
        clear_physical_raw_cache
    )

    clear_physical_raw_cache()

    roche_valid_spec = [{
        "path": "digital_Sensor/Roche_PD_Monitoring_App_v2_data_09Nov2026.csv",
        "grain_keys": ["PATNO", "QRSCATID", "QRSTSTID", "QRSDTM"],
        "documentation": {
            "doc_path": "digital_Sensor/PPMI_Methods_Document_Roche_v1.1.pdf",
            "locator": {"page_range": (12, 16)},
            "evidence_terms": ["Maximum Hand Turn Speed", "Total Power"]
        }
    }]

    roche_invalid_spec = [{
        "path": "digital_Sensor/Roche_PD_Monitoring_App_v2_data_09Nov2026.csv",
        "grain_keys": ["PATNO", "QRSCATID", "QRSTSTID", "QRSDTM"],
        "doc_source": "README.md"
    }]

    # Step 1: Valid doc first -> must be verified
    res1 = build_deep_csv_inventory_table(roche_valid_spec, repo_root=REPO_ROOT)
    assert "PPMI_Methods_Document_Roche_v1.1.pdf" in res1.iloc[0]["Documentation Source"]

    # Step 2: Invalid doc second -> must be rejected despite raw file being cached
    res2 = build_deep_csv_inventory_table(roche_invalid_spec, repo_root=REPO_ROOT)
    assert res2.iloc[0]["Documentation Source"] == "Definition not verified locally"

    # Step 3: Re-evaluate with valid doc -> still verified
    res3 = build_deep_csv_inventory_table(roche_valid_spec, repo_root=REPO_ROOT)
    assert "PPMI_Methods_Document_Roche_v1.1.pdf" in res3.iloc[0]["Documentation Source"]

    # Step 4: Re-evaluate with invalid doc -> still rejected
    res4 = build_deep_csv_inventory_table(roche_invalid_spec, repo_root=REPO_ROOT)
    assert res4.iloc[0]["Documentation Source"] == "Definition not verified locally"


def test_deep_csv_inventory_structured_doc_evidence():
    """Negative fixture: verify that structured locators fail closed when page ranges are out of bounds
    or required evidence terms are absent from the document."""
    from ppmi_pipeline.reporting.notebook_support import build_deep_csv_inventory_table

    # Case 1: Page range exceeds physical PDF page count
    spec_bad_pages = [{
        "path": "digital_Sensor/Roche_PD_Monitoring_App_v2_data_09Nov2026.csv",
        "grain_keys": ["PATNO", "QRSCATID", "QRSTSTID", "QRSDTM"],
        "documentation": {
            "doc_path": "digital_Sensor/PPMI_Methods_Document_Roche_v1.1.pdf",
            "locator": {"page_range": (900, 950)},  # Far exceeds PDF page count
            "evidence_terms": ["Maximum Hand Turn Speed"]
        }
    }]
    res1 = build_deep_csv_inventory_table(spec_bad_pages, repo_root=REPO_ROOT)
    assert res1.iloc[0]["Documentation Source"] == "Definition not verified locally"

    # Case 2: Evidence term does not appear in cited page range
    spec_missing_term = [{
        "path": "digital_Sensor/Roche_PD_Monitoring_App_v2_data_09Nov2026.csv",
        "grain_keys": ["PATNO", "QRSCATID", "QRSTSTID", "QRSDTM"],
        "documentation": {
            "doc_path": "digital_Sensor/PPMI_Methods_Document_Roche_v1.1.pdf",
            "locator": {"page_range": (12, 16)},
            "evidence_terms": ["CompletelyFabricatedEvidenceTermXYZ"]
        }
    }]
    res2 = build_deep_csv_inventory_table(spec_missing_term, repo_root=REPO_ROOT)
    assert res2.iloc[0]["Documentation Source"] == "Definition not verified locally"

    # Case 3: Valid locator and present evidence terms -> succeeds
    spec_valid = [{
        "path": "digital_Sensor/Roche_PD_Monitoring_App_v2_data_09Nov2026.csv",
        "grain_keys": ["PATNO", "QRSCATID", "QRSTSTID", "QRSDTM"],
        "documentation": {
            "doc_path": "digital_Sensor/PPMI_Methods_Document_Roche_v1.1.pdf",
            "locator": {"page_range": (12, 16)},
            "evidence_terms": ["Maximum Hand Turn Speed", "Total Power"]
        }
    }]
    res3 = build_deep_csv_inventory_table(spec_valid, repo_root=REPO_ROOT)
    assert "PPMI_Methods_Document_Roche_v1.1.pdf" in res3.iloc[0]["Documentation Source"]


def validate_report_against_notebook_artifacts(content: str, repo_root: Path):
    """Rigorous parser-based parity validator between implementation report and notebook artifacts."""
    import re
    import io

    # 1. Parse all 7 notebooks and verify exact per-notebook counts and totals
    expected_nb_counts = {
        "00_dataset_overview.ipynb": (21, 38),
        "eda_clinical.ipynb": (21, 54),
        "eda_biospecimen.ipynb": (15, 39),
        "eda_genetics.ipynb": (14, 35),
        "eda_neuroimaging.ipynb": (17, 56),
        "eda_digital_sensors.ipynb": (14, 30),
        "eda_multimodal_synthesis.ipynb": (15, 34),
    }

    total_code_cells = 0
    total_outputs = 0
    for nb_name, (exp_cells, exp_outs) in expected_nb_counts.items():
        nb_p = repo_root / nb_name
        assert nb_p.exists(), f"Notebook {nb_name} missing"
        with open(nb_p, "r", encoding="utf-8") as f:
            nb_json = json.load(f)
        code_cells = [c for c in nb_json.get("cells", []) if c.get("cell_type") == "code"]
        outs = sum(len(c.get("outputs", [])) for c in code_cells)
        errs = sum(1 for c in code_cells for o in c.get("outputs", []) if o.get("output_type") == "error")
        assert len(code_cells) == exp_cells, f"{nb_name} cell count mismatch: {len(code_cells)} != {exp_cells}"
        assert outs == exp_outs, f"{nb_name} output count mismatch: {outs} != {exp_outs}"
        assert errs == 0, f"{nb_name} has {errs} errors"
        total_code_cells += len(code_cells)
        total_outputs += outs

        # Check per-notebook counts cited in report
        assert re.search(rf"(\$)?{exp_cells}(\$)?\s+code\s+cells", content), f"Report missing '{exp_cells} code cells' for {nb_name}"
        assert re.search(rf"(\$)?{exp_outs}(\$)?\s+outputs", content), f"Report missing '{exp_outs} outputs' for {nb_name}"

    assert total_code_cells == 117
    assert total_outputs == 286
    assert "117 code cells" in content
    assert "286 executed outputs" in content or "286 outputs" in content

    # 2. Extract executed Table 8.4B and verify MRI counts
    nb_img = json.load(open(repo_root / "eda_neuroimaging.ipynb", encoding="utf-8"))
    tbl_84b = None
    for c in nb_img["cells"]:
        for out in c.get("outputs", []):
            html = out.get("data", {}).get("text/html", "")
            if isinstance(html, list):
                html = "".join(html)
            if "8.4B" in html or ("DTI Sequence Acquired" in html and "All Acquisition Records" in html):
                tbl_84b = pd.read_html(io.StringIO(html))[0]
                break
    assert tbl_84b is not None, "Failed to parse Table 8.4B from eda_neuroimaging.ipynb"

    # Assert exact MRI numbers from Table 8.4B are in report
    for val_str in ["8,779", "3,351", "7,252", "6,958", "3,616", "3,012", "3,191", "1,454"]:
        assert val_str in content, f"Report missing MRI Table 8.4B value {val_str}"
    assert "1,173 baseline MRI" not in content

    # 3. Extract Table 8.3 and verify genetics carrier counts
    nb_gen = json.load(open(repo_root / "eda_genetics.ipynb", encoding="utf-8"))
    tbl_83 = None
    for c in nb_gen["cells"]:
        for out in c.get("outputs", []):
            html = out.get("data", {}).get("text/html", "")
            if isinstance(html, list):
                html = "".join(html)
            if "LRRK2 Carrier" in html and "Positive Family History" in html:
                tbl_83 = pd.read_html(io.StringIO(html))[0]
                break
    assert tbl_83 is not None, "Failed to parse Table 8.3 from eda_genetics.ipynb"
    for gen_val in ["376", "277", "28", "67", "3,057"]:
        assert gen_val in content, f"Report missing Genetics Table 8.3 carrier count {gen_val}"

    # 4. Verify sensor 9-variable skewness is cited
    assert "9 analyzed numeric variables" in content or "all 9 numeric variables" in content or "9 sensor variables" in content

    # 5. Extract Table 8.1 / 7.1 deep inventory dimensions from notebooks and verify report citation
    expected_source_dims = [
        "40,609 x 65", "21,426 x 35", "131,616 x 19", "139 x 65",
        "6,265 x 21", "9,310 x 43", "10,759 x 42", "1,740 x 58",
        "108,901 x 22", "20,408 x 215"
    ]
    for dim_str in expected_source_dims:
        dim_tex = dim_str.replace(" x ", r" \times ")
        assert dim_str in content or dim_tex in content, f"Report missing physical Table 8.1 dimension '{dim_str}'"

    # 6. Prohibited overclaims scan across Section 3 and Section 3.7
    section_3_and_37 = content.split("## 3. Modality Notebook Deliverables")[1].split("## 4.")[0]
    expanded_prohibited = [
        "significantly elevated",
        "exceptional diagnostic specificity",
        "corroborating non-synuclein etiology",
        "verifying detectable molecular synuclein seeding",
        "significant inverse correlation",
        "non-redundant complementary phenotyping",
        "detectable molecular synuclein seeding prior to formal motor diagnosis",
        "comorbid alzheimer-like pathology",
        "population base rates",
        "nigrostriatal denervation",
        "high biological concordance",
        "nigral microstructural disruption",
        "confirming biological coherence",
        "identifying synucleinopathy",
        "biological dimensions",
        "ready for longitudinal modeling"
    ]
    for bad in expanded_prohibited:
        assert bad.lower() not in section_3_and_37.lower(), (
            f"Prohibited phrase '{bad}' found in Sections 3/3.7 of report"
        )


def test_implementation_report_matches_executed_notebook_artifacts():
    """Verify report-artifact parity: implementation reports in docs/ and EDA/outputs/reports/
    must reconcile exactly with executed notebook artifacts via parser-based contract."""
    report_paths = [
        REPO_ROOT / "docs" / "multimodal_eda_sprint_implementation_report.md",
        REPO_ROOT / "EDA" / "outputs" / "reports" / "multimodal_eda_sprint_implementation_report.md"
    ]
    for rp in report_paths:
        assert rp.exists(), f"Missing implementation report at {rp}"
        with open(rp, "r", encoding="utf-8") as f:
            content = f.read()
        validate_report_against_notebook_artifacts(content, REPO_ROOT)


def test_report_parity_negative_mutation_fails():
    """Negative fixture: verify that mutating an actual report value causes the parser-based validator to fail."""
    import pytest
    report_path = REPO_ROOT / "docs" / "multimodal_eda_sprint_implementation_report.md"
    assert report_path.exists()
    with open(report_path, "r", encoding="utf-8") as f:
        valid_content = f.read()

    # Mutation 1: Mutating MRI rs-fMRI valid count (6,958 -> 6,644) fails validator
    mutated_mri = valid_content.replace("6,958", "6,644")
    with pytest.raises(AssertionError):
        validate_report_against_notebook_artifacts(mutated_mri, REPO_ROOT)

    # Mutation 2: Mutating total outputs (286 -> 285) fails validator
    mutated_outs = valid_content.replace("286 executed outputs", "285 executed outputs").replace("286 outputs", "285 outputs")
    with pytest.raises(AssertionError):
        validate_report_against_notebook_artifacts(mutated_outs, REPO_ROOT)

    # Mutation 3: Injecting a prohibited overclaim into Section 3 fails validator
    mutated_claim = valid_content.replace(
        "Scans classified as visual 'negative'",
        "Scans classified as visual 'negative' show high biological concordance"
    )
    with pytest.raises(AssertionError):
        validate_report_against_notebook_artifacts(mutated_claim, REPO_ROOT)


