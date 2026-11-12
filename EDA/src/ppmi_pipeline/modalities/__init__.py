"""Modality-aware architecture package for PPMI multimodal pipeline."""

from pathlib import Path
from typing import List, Optional

from .base import (
    BaseModalityHandler,
    DatasetSelectionCategory,
    FormatCategory,
    ModalityCategory,
    ModalityFileProfile,
    ObservationGrain,
    SourceClass,
    WorksheetProfile,
)
from .biospecimen import BiospecimenModalityHandler
from .clinical import ClinicalModalityHandler
from .curated import CuratedMultimodalModalityHandler
from .digital_sensor import DigitalSensorModalityHandler
from .genetics import GeneticsMolecularModalityHandler
from .imaging import ImagingModalityHandler


class ModalityRegistry:
    """Registry managing modality detection and handlers across PPMI datasets."""

    def __init__(self) -> None:
        self.handlers: List[BaseModalityHandler] = [
            ClinicalModalityHandler(),
            BiospecimenModalityHandler(),
            GeneticsMolecularModalityHandler(),
            ImagingModalityHandler(),
            DigitalSensorModalityHandler(),
            CuratedMultimodalModalityHandler(),
        ]

    def classify_file_modality(self, file_path: Path) -> ModalityCategory:
        """Classify a given file into its biological / physical modality."""
        name_lower = file_path.name.lower()

        # Check macOS sidecars
        if file_path.name.startswith("._") or "__MACOSX" in file_path.parts:
            return ModalityCategory.SYSTEM_SIDECAR

        ext = file_path.suffix.lower()

        # Check documentation / manuals first
        if ext in {".pdf", ".docx"} and not ("spreadsheet" in name_lower):
            return ModalityCategory.METADATA_DOCUMENTATION

        # Pipeline internal files
        parts = file_path.parts
        if "EDA" in parts or "docs" in parts or "sections" in parts or "ppmi_complete_manual" in parts:
            return ModalityCategory.PIPELINE_INTERNAL

        # Query handlers in priority order (digital sensor / genetics before general clinical)
        for handler in reversed(self.handlers):
            if handler.handles_file(file_path):
                return handler.category

        # Check subject_characteristics folder
        parent_name = file_path.parent.name
        if parent_name == "subject_characteristics":
            if any(k in name_lower for k in ["genetic", "genotypes", "polygenic"]):
                return ModalityCategory.GENETICS_MOLECULAR
            return ModalityCategory.CLINICAL

        return ModalityCategory.UNKNOWN

    def classify_file_format(self, file_path: Path) -> FormatCategory:
        """Classify file format category based on extension and naming conventions."""
        if file_path.name.startswith("._") or "__MACOSX" in file_path.parts:
            return FormatCategory.SYSTEM_METADATA

        ext = file_path.suffix.lower()
        full_ext = "".join(file_path.suffixes).lower()
        name_lower = file_path.name.lower()

        if full_ext == ".nii.gz" or ext in {".nii", ".dcm"}:
            return FormatCategory.BINARY_IMAGING_VOLUME
        elif ext == ".csv":
            if "sensor" in name_lower or "roche" in name_lower:
                return FormatCategory.TIME_SERIES
            return FormatCategory.TABULAR_CSV
        elif ext in {".xlsx", ".xls"}:
            return FormatCategory.TABULAR_EXCEL
        elif ext == ".pdf":
            return FormatCategory.DOCUMENT_PDF
        elif ext in {".docx", ".doc"}:
            return FormatCategory.DOCUMENT_DOCX
        elif ext == ".json":
            return FormatCategory.STRUCTURED_JSON
        elif ext in {".tex", ".txt", ".aux", ".toc", ".out", ".log"}:
            return FormatCategory.TEXT_DOCUMENT
        elif ext == ".py":
            return FormatCategory.CODE_SCRIPT
        return FormatCategory.OTHER

    def get_handler_for_category(self, category: ModalityCategory) -> Optional[BaseModalityHandler]:
        """Obtain the specialized handler instance for a given modality category."""
        for handler in self.handlers:
            if handler.category == category:
                return handler
        return None


__all__ = [
    "BaseModalityHandler",
    "BiospecimenModalityHandler",
    "ClinicalModalityHandler",
    "CuratedMultimodalModalityHandler",
    "DatasetSelectionCategory",
    "DigitalSensorModalityHandler",
    "FormatCategory",
    "GeneticsMolecularModalityHandler",
    "ImagingModalityHandler",
    "ModalityCategory",
    "ModalityFileProfile",
    "ModalityRegistry",
    "ObservationGrain",
    "SourceClass",
    "WorksheetProfile",
]
