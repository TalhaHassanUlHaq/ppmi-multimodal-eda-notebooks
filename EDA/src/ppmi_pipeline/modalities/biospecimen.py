"""Biospecimen and bioassay modality handler for PPMI."""

from pathlib import Path
from typing import List, Set

from .base import BaseModalityHandler, ModalityCategory


class BiospecimenModalityHandler(BaseModalityHandler):
    """Audits and manages CSF, plasma, serum, and cellular bioassays."""

    BIOSPECIMEN_FOLDERS: Set[str] = {"biospecimen"}

    @property
    def category(self) -> ModalityCategory:
        return ModalityCategory.BIOSPECIMEN

    def handles_folder(self, folder_name: str) -> bool:
        return folder_name.strip().lower() in {f.lower() for f in self.BIOSPECIMEN_FOLDERS}

    def handles_file(self, file_path: Path) -> bool:
        parent_name = file_path.parent.name.lower()
        return "biospecimen" in parent_name or "ipsc" in file_path.name.lower() or "assay" in file_path.name.lower()

    def get_quality_checklist(self) -> List[str]:
        return [
            "Assay lower/upper limits of quantification (LLOQ / ULOQ) left- and right-censoring.",
            "Batch / plate run effects and inter-laboratory variation.",
            "Sample aliquot freeze-thaw count and time to processing integrity.",
            "Validation of assay units consistency across longitudinal data cuts (e.g., pg/mL).",
            "Disambiguation of quantitative continuous values vs qualitative positivity calls (e.g., SAA positive/negative).",
            "Multiplicity check: multiple test runs per participant lumbar puncture.",
        ]

    def propose_eda_methods(self) -> List[str]:
        return [
            "Log-scale distribution and violin plots for CSF biomarkers (Aβ42, t-tau, p-tau, alpha-synuclein).",
            "Biomarker ratios (e.g., t-tau / Aβ42, p-tau / Aβ42) by diagnostic cohort.",
            "Quantile-quantile (Q-Q) plots and outlier identification using robust median absolute deviations.",
            "Survival curves conditioned on baseline biomarker positivity.",
            "Cross-assay concordance analysis across duplicate/replicate assay runs.",
        ]

