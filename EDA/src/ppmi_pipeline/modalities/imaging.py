"""Neuroimaging modality handler for PPMI (SPECT, MRI, DTI, PET)."""

from pathlib import Path
from typing import List, Set

from .base import BaseModalityHandler, ModalityCategory


class ImagingModalityHandler(BaseModalityHandler):
    """Audits and provides specialized EDA logic for neuroimaging modalities."""

    IMAGING_FOLDERS: Set[str] = {
        "DATSCAN",
        "dti",
        "MR Analysis Results",
        "MRI Acquisition",
        "PET",
    }

    @property
    def category(self) -> ModalityCategory:
        return ModalityCategory.IMAGING

    def handles_folder(self, folder_name: str) -> bool:
        normalized = folder_name.strip()
        return normalized in self.IMAGING_FOLDERS or normalized.upper() in {f.upper() for f in self.IMAGING_FOLDERS}

    def handles_file(self, file_path: Path) -> bool:
        parent_name = file_path.parent.name
        if self.handles_folder(parent_name):
            return True
        grandparent_name = file_path.parent.parent.name
        if self.handles_folder(grandparent_name):
            return True
        return False

    def get_quality_checklist(self) -> List[str]:
        return [
            "Physical file presence verification: distinguishing derived volumetric/SBR tables from remote 3D NIfTI/DICOM volumes.",
            "DaTscan striatal binding ratio (SBR) quantification consistency across core laboratories (e.g., Xing Core Lab).",
            "Left/right putamen and caudate asymmetry index calculation and plausibility checks.",
            "MRI FreeSurfer v7 segmentation quality assurance, Euler number checks, and intracranial volume (ICV) normalization.",
            "DTI gradient direction count, b-value verification, and susceptibility artifact documentation.",
            "PET radiotracer specificity and dose/uptake timing harmonization.",
            "Imaging acquisition date to clinical visit milestone latency (days between scan and clinical exam).",
        ]

    def propose_eda_methods(self) -> List[str]:
        return [
            "Striatal Binding Ratio (SBR) longitudinal slope analysis by hemisphere (ipsilateral vs contralateral to dominant motor deficit).",
            "FreeSurfer cortical thickness regional shrinkage and hippocampal volume trajectory profiling.",
            "DTI fractional anisotropy (FA) and mean diffusivity (MD) comparisons in substantia nigra and corpus callosum.",
            "Cross-correlation heatmaps linking DaTscan putamen deficit with UPDRS motor scores.",
            "Cataloging scan acquisition protocols and scanner field strengths (1.5T vs 3.0T).",
        ]

