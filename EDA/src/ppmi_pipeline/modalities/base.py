"""Base interfaces, data structures, and enumerations for multimodal PPMI EDA."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


class ModalityCategory(str, Enum):
    """Categorization of PPMI data streams by physical / biological modality."""
    CLINICAL = "Clinical & Neuropsychological"
    BIOSPECIMEN = "Biospecimen & Bioassays"
    GENETICS_MOLECULAR = "Genetics & RNA / Molecular"
    IMAGING = "Neuroimaging (SPECT, MRI, DTI, PET)"
    DIGITAL_SENSOR = "Digital Sensor & Mobile Telemetry"
    CURATED_MULTIMODAL = "Curated Multimodal Cut"
    METADATA_DOCUMENTATION = "Protocol Documentation & Manuals"
    PIPELINE_INTERNAL = "Pipeline Internal Artifacts"
    SYSTEM_SIDECAR = "System Metadata Sidecar (._)"
    UNKNOWN = "Unknown / Unclassified"


class SourceClass(str, Enum):
    """Classification of files within the project repository."""
    SOURCE_DATA = "Source Data (PPMI Named Domain)"
    STUDY_DOCUMENTATION = "Study Protocol / Methods Document"
    PROJECT_CODE = "Project Code & Pipeline Scripts"
    GENERATED_ARTIFACT = "Generated Audit Artifact / Output"
    EXTERNAL_REFERENCE = "External Reference (Not Locally Archived)"
    MACOS_SIDECAR = "macOS Metadata Sidecar (._)"


class FormatCategory(str, Enum):
    """File format classification."""
    TABULAR_CSV = "Tabular CSV"
    TABULAR_EXCEL = "Tabular Excel (.xlsx)"
    DOCUMENT_PDF = "Document PDF"
    DOCUMENT_DOCX = "Document Word (.docx)"
    STRUCTURED_JSON = "Structured JSON"
    TEXT_DOCUMENT = "Text / LaTeX Document"
    BINARY_IMAGING_VOLUME = "Binary Neuroimaging Volume (NIfTI/DICOM)"
    TIME_SERIES = "Raw Time-Series / Sensor Stream"
    CODE_SCRIPT = "Pipeline Python / Script"
    SYSTEM_METADATA = "System Metadata Sidecar"
    OTHER = "Other Format"


class ObservationGrain(str, Enum):
    """Observation grain of records within a dataset."""
    SUBJECT_LEVEL = "Subject-Level (1 row per participant)"
    VISIT_LEVEL = "Visit-Level (1 row per participant-visit)"
    REPEATED_EVENT_OR_ITEM = "Repeated Event / Item-Level (multiple rows per visit)"
    ALIQUOT_OR_ASSAY_RUN = "Aliquot / Assay-Run Level"
    SENSOR_TEST_RUN = "Sensor Active Test / Session Level"
    DOCUMENTATION_OR_METADATA = "Documentation / Reference (no participant key)"
    AMBIGUOUS_NEEDS_REVIEW = "Ambiguous / Needs Detailed Review"
    UNINDEXED_OR_UNKNOWN = "Unindexed / Unknown Grain"


class DatasetSelectionCategory(str, Enum):
    """Scientific prioritization tier for detailed exploratory data analysis.
    
    NOTE: In Phase 1, all dataset classifications remain strictly provisional
    (Selection Pending) awaiting the formal researcher selection gate.
    """
    SELECTION_PENDING = "Selection Pending (Awaiting Selection Gate Approval)"
    PRIMARY_EDA = "Primary EDA"
    SUPPORTING = "Supporting"
    EXCLUDED_FROM_DETAILED_EDA = "Excluded from detailed EDA"
    NEEDS_REVIEW = "Needs Review"


@dataclass
class WorksheetProfile:
    """Detailed structural profile for an individual sheet within a workbook."""
    sheet_name: str
    row_count: int
    column_count: int
    columns: List[str] = field(default_factory=list)
    literal_columns: List[str] = field(default_factory=list)
    blank_headers_count: int = 0
    duplicate_headers: List[str] = field(default_factory=list)
    detected_identifiers: List[str] = field(default_factory=list)
    has_participant_id: bool = False
    has_visit_id: bool = False
    distinct_participants: int = 0
    distinct_visits: int = 0
    null_participant_keys: int = 0
    null_visit_keys: int = 0
    observation_grain: ObservationGrain = ObservationGrain.UNINDEXED_OR_UNKNOWN
    candidate_primary_keys: List[str] = field(default_factory=list)
    is_full_data_validated: bool = True
    duplicate_rows_count: int = 0
    null_rate_percent: float = 0.0
    quality_concerns: List[str] = field(default_factory=list)


@dataclass
class ModalityFileProfile:
    """Detailed structural and modality profile for an individual dataset file."""
    file_path: Path
    relative_path: str
    file_name: str
    file_extension: str
    file_size_bytes: int
    source_class: SourceClass
    modality: ModalityCategory
    format_category: FormatCategory
    is_raw_data: bool
    is_derived_measurement: bool
    is_documentation: bool
    is_macos_sidecar: bool = False
    file_sha256: Optional[str] = None

    # Scientific selection tier (strictly provisional in Phase 1)
    selection_category: DatasetSelectionCategory = DatasetSelectionCategory.SELECTION_PENDING
    selection_justification: str = "Awaiting formal researcher selection gate approval"
    selection_scores: Dict[str, Any] = field(default_factory=dict)

    # Schema & Content profile (where applicable)
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    columns: List[str] = field(default_factory=list)
    literal_columns: List[str] = field(default_factory=list)
    blank_headers_count: int = 0
    duplicate_headers: List[str] = field(default_factory=list)
    parser_aliases: Dict[str, str] = field(default_factory=dict)
    column_dictionary: List[Dict[str, Any]] = field(default_factory=list)
    detected_identifiers: List[str] = field(default_factory=list)
    has_participant_id: bool = False
    has_visit_id: bool = False
    distinct_participants: int = 0
    distinct_visits: int = 0
    null_participant_keys: int = 0
    null_visit_keys: int = 0
    observation_grain: ObservationGrain = ObservationGrain.UNINDEXED_OR_UNKNOWN
    candidate_primary_keys: List[str] = field(default_factory=list)
    max_key_multiplicity: int = 0
    is_full_data_validated: bool = True
    duplicate_rows_count: int = 0
    null_rate_percent: float = 0.0

    # For multi-sheet workbooks
    worksheets: List[WorksheetProfile] = field(default_factory=list)

    # Physical presence vs external reference note
    availability_note: str = "Physically present locally"
    documentation_provenance: str = "Not documented / verified"
    quality_concerns: List[str] = field(default_factory=list)
    extra_metadata: Dict[str, Any] = field(default_factory=dict)


class BaseModalityHandler(ABC):
    """Abstract base class defining modality-specific audit and EDA capabilities."""

    @property
    @abstractmethod
    def category(self) -> ModalityCategory:
        """The modality category handled by this module."""
        pass

    @abstractmethod
    def handles_folder(self, folder_name: str) -> bool:
        """Determines if a given folder falls within this modality's domain."""
        pass

    @abstractmethod
    def handles_file(self, file_path: Path) -> bool:
        """Determines if a specific file falls within this modality's domain."""
        pass

    @abstractmethod
    def get_quality_checklist(self) -> List[str]:
        """Returns the domain-specific data quality checks for this modality."""
        pass

    @abstractmethod
    def propose_eda_methods(self) -> List[str]:
        """Proposes tailored exploratory data analysis methods for this modality."""
        pass
