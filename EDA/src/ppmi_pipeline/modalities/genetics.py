"""Genetics and RNA / molecular modality handler for PPMI."""

from pathlib import Path
from typing import List, Set

from .base import BaseModalityHandler, ModalityCategory


class GeneticsMolecularModalityHandler(BaseModalityHandler):
    """Audits and provides specialized EDA logic for genetic variants, polygenic risk, and RNA data."""

    GENETICS_KEYWORDS: Set[str] = {
        "genetic",
        "genotypes",
        "polygenic",
        "consensus",
        "mutation",
        "variant",
        "apoe",
        "lrrk2",
        "gba",
        "snca",
        "rna",
        "wgs",
        "wes",
    }

    @property
    def category(self) -> ModalityCategory:
        return ModalityCategory.GENETICS_MOLECULAR

    def handles_folder(self, folder_name: str) -> bool:
        norm = folder_name.strip().lower()
        return "genetic" in norm or "molecular" in norm or "rna" in norm

    def handles_file(self, file_path: Path) -> bool:
        name_lower = file_path.name.lower()
        parent_lower = file_path.parent.name.lower()

        if self.handles_folder(parent_lower):
            return True

        if parent_lower in {"subject_characteristics", "biospecimen"}:
            for kw in self.GENETICS_KEYWORDS:
                if kw in name_lower:
                    return True
        return False

    def get_quality_checklist(self) -> List[str]:
        return [
            "Verification of physical availability vs remote/external sequencing repository references.",
            "Record exact raw sequencing vs derived summary status (e.g. raw RNA FASTQ/BAM not in local disk; derived PRS and variant consensus present).",
            "Consensus pathogenicity categorization alignment (e.g. ACMG criteria for LRRK2, GBA, SNCA).",
            "Allele frequency and Hardy-Weinberg equilibrium screening within control cohorts.",
            "Polygenic Risk Score (PRS) standardization and distribution normalization.",
            "Resolution of conflicting variant calls across platforms (e.g. CLIA vs WGS vs Sanger).",
        ]

    def propose_eda_methods(self) -> List[str]:
        return [
            "Cross-tabulation of pathogenic carrier status across clinical cohort categories.",
            "APOE allele frequency breakdown (epsilon 2, 3, 4) comparing PD vs Healthy Controls.",
            "PRS distribution profiling and effect-size comparisons against motor onset age.",
            "Gene-environment / gene-phenotype interaction exploratory modeling.",
            "Inventory cross-referencing against external sequencing projects (Project 116 WES, Project 118 WGS, Project 133 RNA-seq).",
        ]

