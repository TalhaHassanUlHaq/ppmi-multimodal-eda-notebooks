"""Curated multimodal cut handler for PPMI."""

from pathlib import Path
from typing import List, Set

from .base import BaseModalityHandler, ModalityCategory


class CuratedMultimodalModalityHandler(BaseModalityHandler):
    """Audits and manages pre-curated cross-modal data cuts combining clinical, imaging, and biofluid metrics."""

    CURATED_FOLDERS: Set[str] = {"curated_datacuts"}

    @property
    def category(self) -> ModalityCategory:
        return ModalityCategory.CURATED_MULTIMODAL

    def handles_folder(self, folder_name: str) -> bool:
        return folder_name.strip().lower() in {f.lower() for f in self.CURATED_FOLDERS}

    def handles_file(self, file_path: Path) -> bool:
        parent_lower = file_path.parent.name.lower()
        name_lower = file_path.name.lower()
        return "curated" in parent_lower or "curated_data_cut" in name_lower

    def get_quality_checklist(self) -> List[str]:
        return [
            "Cross-modality harmonization and synchronization across clinical visit dates.",
            "Integrity of data cut versioning and release milestone traceability (e.g. 20260810 cut).",
            "Multi-sheet structure in workbook (e.g., Data Dictionary, Demographics, UPDRS, Biofluids, DaTscan).",
            "Consistent application of missing value sentinels across curated sheets.",
            "Validation that observation grain matches expected (PATNO, EVENT_ID) composite keys.",
        ]

    def propose_eda_methods(self) -> List[str]:
        return [
            "Cross-modal correlation matrices linking DaTscan, MoCA, UPDRS, and CSF SAA at baseline.",
            "Longitudinal multimodal feature completeness matrix across 10-year follow-up.",
            "PCA / UMAP exploratory projections across combined clinical, imaging, and fluid features.",
            "Benchmarking curated variables against raw individual domain tables for validation.",
        ]

