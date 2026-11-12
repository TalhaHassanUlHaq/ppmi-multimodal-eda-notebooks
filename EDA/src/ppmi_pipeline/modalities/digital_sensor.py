"""Digital sensor and mobile telemetry modality handler for PPMI."""

from pathlib import Path
from typing import List, Set

from .base import BaseModalityHandler, ModalityCategory


class DigitalSensorModalityHandler(BaseModalityHandler):
    """Audits and manages high-frequency digital sensors, wearables, and smartphone monitoring."""

    DIGITAL_SENSOR_FOLDERS: Set[str] = {
        "digital_Sensor",
        "digital_sensor",
    }

    @property
    def category(self) -> ModalityCategory:
        return ModalityCategory.DIGITAL_SENSOR

    def handles_folder(self, folder_name: str) -> bool:
        normalized = folder_name.strip().lower()
        return any(sf.lower() in normalized for sf in self.DIGITAL_SENSOR_FOLDERS)

    def handles_file(self, file_path: Path) -> bool:
        parent_lower = file_path.parent.name.lower()
        name_lower = file_path.name.lower()

        if self.handles_folder(parent_lower):
            return True
        # Gait accelerometer / Opal / Axivity sub-studies residing in MOTOR
        if "gait_data" in name_lower or "axivity" in name_lower or "opals" in name_lower:
            return True
        return False

    def get_quality_checklist(self) -> List[str]:
        return [
            "Participant compliance and longitudinal attrition in daily/weekly app active tests.",
            "Test battery completeness (e.g., finger tapping, tremor hold, balance, voice test).",
            "Passive monitoring wearing time per day and diurnal cadence integrity.",
            "Device hardware and operating system heterogeneity (iOS vs Android versions).",
            "High-frequency time-series sampling frequency jitter and missing packet drops.",
            "Observation grain resolution: test-run level vs session level vs daily summary.",
        ]

    def propose_eda_methods(self) -> List[str]:
        return [
            "Adherence decay analysis (testing frequency over 12-month monitoring periods).",
            "Diurnal motor fluctuation profiling from passive smartwatch/phone accelerometer metrics.",
            "Correlation analysis between digital smartphone motor scores and in-clinic MDS-UPDRS Part III.",
            "Feature variance breakdown: within-subject day-to-day variability vs between-subject phenotypic variance.",
            "Sensitivity analysis for digital surrogate markers detecting prodromal and early PD progression.",
        ]

