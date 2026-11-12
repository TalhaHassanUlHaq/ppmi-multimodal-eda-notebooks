"""Automated tests for modality classification and modality-specific handlers."""

from pathlib import Path
import pytest

from ppmi_pipeline.modalities import (
    DatasetSelectionCategory,
    FormatCategory,
    ModalityCategory,
    ModalityRegistry,
)


def test_modality_registry_classification():
    """Verify that file paths are accurately mapped to their biological/physical modality."""
    reg = ModalityRegistry()

    # Clinical files
    p_motor = Path("MOTOR/MDS-UPDRS_Part_III_09Nov2026.csv")
    assert reg.classify_file_modality(p_motor) == ModalityCategory.CLINICAL

    p_med = Path("MEDICAL HISTORY/Concomitant_Medication_Log_09Nov2026.csv")
    assert reg.classify_file_modality(p_med) == ModalityCategory.CLINICAL

    # Biospecimen files
    p_bio = Path("biospecimen/IUSM_ASSAY_DEV_CATALOG_09Nov2026.csv")
    assert reg.classify_file_modality(p_bio) == ModalityCategory.BIOSPECIMEN

    # Genetics / Molecular files
    p_gen = Path("subject_characteristics/iu_genetic_consensus_20251025_09Nov2026.csv")
    assert reg.classify_file_modality(p_gen) == ModalityCategory.GENETICS_MOLECULAR

    p_prs = Path("subject_characteristics/Polygenic_Risk_Scores_09Nov2026.csv")
    assert reg.classify_file_modality(p_prs) == ModalityCategory.GENETICS_MOLECULAR

    # Neuroimaging files
    p_dat = Path("DATSCAN/Xing_Core_Lab_-_Quant_SBR_09Nov2026.csv")
    assert reg.classify_file_modality(p_dat) == ModalityCategory.IMAGING

    p_mri = Path("MR Analysis Results/FS7_APARC_CTH_09Nov2026.csv")
    assert reg.classify_file_modality(p_mri) == ModalityCategory.IMAGING

    p_dti = Path("dti/DTI_Regions_of_Interest_09Nov2026.csv")
    assert reg.classify_file_modality(p_dti) == ModalityCategory.IMAGING

    # Digital sensor files
    p_sensor = Path("digital_Sensor/Roche_PD_Monitoring_App_v2_data_09Nov2026.csv")
    assert reg.classify_file_modality(p_sensor) == ModalityCategory.DIGITAL_SENSOR

    # Curated multimodal cut
    p_curated = Path("curated_datacuts/PPMI_Curated_Data_Cut_Public_20260810.xlsx")
    assert reg.classify_file_modality(p_curated) == ModalityCategory.CURATED_MULTIMODAL

    # Documentation
    p_pdf = Path("DATSCAN/PPMI_DaTSCAN_SPECT_Preprocessing_Methods_v1.0.pdf")
    assert reg.classify_file_modality(p_pdf) == ModalityCategory.METADATA_DOCUMENTATION


def test_format_category_classification():
    """Verify that file extensions and characteristics map to proper format categories."""
    reg = ModalityRegistry()

    assert reg.classify_file_format(Path("table.csv")) == FormatCategory.TABULAR_CSV
    assert reg.classify_file_format(Path("sheet.xlsx")) == FormatCategory.TABULAR_EXCEL
    assert reg.classify_file_format(Path("manual.pdf")) == FormatCategory.DOCUMENT_PDF
    assert reg.classify_file_format(Path("guide.docx")) == FormatCategory.DOCUMENT_DOCX
    assert reg.classify_file_format(Path("catalog.json")) == FormatCategory.STRUCTURED_JSON
    assert reg.classify_file_format(Path("brain.nii.gz")) == FormatCategory.BINARY_IMAGING_VOLUME
    assert reg.classify_file_format(Path("roche_sensor_stream.csv")) == FormatCategory.TIME_SERIES


def test_dataset_selection_categories():
    """Verify that all four scientific selection categories are defined."""
    assert DatasetSelectionCategory.PRIMARY_EDA.value == "Primary EDA"
    assert DatasetSelectionCategory.SUPPORTING.value == "Supporting"
    assert DatasetSelectionCategory.EXCLUDED_FROM_DETAILED_EDA.value == "Excluded from detailed EDA"
    assert DatasetSelectionCategory.NEEDS_REVIEW.value == "Needs Review"

