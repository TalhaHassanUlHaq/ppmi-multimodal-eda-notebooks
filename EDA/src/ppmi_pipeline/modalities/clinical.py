"""Clinical and neuropsychological modality handler for PPMI."""

from pathlib import Path
from typing import List, Set

from .base import BaseModalityHandler, ModalityCategory


class ClinicalModalityHandler(BaseModalityHandler):
    """Audits and provides specialized EDA logic for clinical, motor, and cognitive domains."""

    CLINICAL_FOLDERS: Set[str] = {
        "MOTOR",
        "MEDICAL HISTORY",
        "neurobehavioral",
        "neuropsychological",
        "non motor",
        "olfactory",
        "other cognitive",
        "sleep disorder",
    }

    @property
    def category(self) -> ModalityCategory:
        return ModalityCategory.CLINICAL

    def handles_folder(self, folder_name: str) -> bool:
        normalized = folder_name.strip()
        return normalized in self.CLINICAL_FOLDERS or normalized.upper() in {f.upper() for f in self.CLINICAL_FOLDERS}

    def handles_file(self, file_path: Path) -> bool:
        parent_name = file_path.parent.name
        if self.handles_folder(parent_name):
            return True
        # Specific clinical files residing in subject_characteristics
        if parent_name == "subject_characteristics" and "Demographics" in file_path.name:
            return True
        return False

    def get_quality_checklist(self) -> List[str]:
        return [
            "Validation of visit milestone adherence (SC, BL, V01–V20).",
            "Verification of subscale item completeness (e.g. MDS-UPDRS Part III motor scores).",
            "Screening for out-of-range rating scores (e.g., UPDRS items 0–4, MoCA items 0–30).",
            "Identification of off-state vs on-state dopaminergic assessment flags (PD_MED_USE).",
            "Inspection of longitudinal clinical attrition and dropout rates.",
            "Verification of observation grain (visit-level vs repeated adverse event / med log entries).",
        ]

    def propose_eda_methods(self) -> List[str]:
        return [
            "Longitudinal score trajectory modeling (mean trajectories with 95% CI by cohort).",
            "Missingness heatmaps across scheduled protocol visits.",
            "Distribution skewness and floor/ceiling effect analysis across rating instruments.",
            "Survival / Kaplan-Meier analysis for clinical conversion endpoints (e.g. time to motor onset).",
            "Correlation matrices across motor and non-motor functional indices.",
        ]

