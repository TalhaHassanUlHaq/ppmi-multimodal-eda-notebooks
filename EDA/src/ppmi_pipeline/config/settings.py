"""Pipeline configuration and runtime settings.

Defines canonical PPMI source domains, non-source artifact paths,
verified missingness sentinels, master identifiers, and strict privacy parameters.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Set


@dataclass(frozen=True)
class PipelineConfig:
    """Immutable runtime configuration for the PPMI EDA pipeline."""

    # Base directory paths
    project_root: Path = field(
        default_factory=lambda: Path(__file__).resolve().parents[4]
    )
    eda_root: Path = field(
        default_factory=lambda: Path(__file__).resolve().parents[3]
    )
    reports_dir: Path = field(
        default_factory=lambda: Path(__file__).resolve().parents[3] / "outputs" / "reports"
    )

    # Canonical 17 PPMI source data folders (the verified source universe)
    domain_folders: List[str] = field(
        default_factory=lambda: [
            "subject_characteristics",
            "biospecimen",
            "DATSCAN",
            "MOTOR",
            "MR Analysis Results",
            "MRI Acquisition",
            "neurobehavioral",
            "neuropsychological",
            "non motor",
            "olfactory",
            "other cognitive",
            "PET",
            "sleep disorder",
            "MEDICAL HISTORY",
            "digital_Sensor",
            "dti",
            "curated_datacuts",
        ]
    )

    # Universal join keys and identifiers
    participant_key: str = "PATNO"
    event_key: str = "EVENT_ID"
    page_key: str = "PAG_NAME"
    line_key: str = "LINE_NO"
    info_date_key: str = "INFODT"

    # Standard parser missing value sentinels.
    # NOTE: Numeric codes like -1 or 999 are NOT applied globally;
    # they must be verified from instrument-specific documentation.
    standard_missing_sentinels: Set[str] = field(
        default_factory=lambda: {
            "",
            " ",
            ".",
            "NA",
            "N/A",
            "NaN",
            "nan",
            "null",
            "None",
            "NONE",
        }
    )

    # Privacy and security constraints
    strict_privacy: bool = True
    banned_log_columns: Set[str] = field(
        default_factory=lambda: {
            "PATNO",
            "ALIAS_ID",
            "SUBJID",
            "CANDID",
            "BIRTHDT",
            "INITIALS",
            "FIRSTNAME",
            "LASTNAME",
        }
    )


def get_default_config() -> PipelineConfig:
    """Obtain default pipeline configuration with verified paths."""
    config = PipelineConfig()
    config.reports_dir.mkdir(parents=True, exist_ok=True)
    return config
