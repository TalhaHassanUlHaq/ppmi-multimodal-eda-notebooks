"""Multimodal dataset inventory and structural auditing engine across all PPMI domains."""

from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import os
import pandas as pd

from ..config.settings import PipelineConfig, get_default_config
from ..modalities import (
    DatasetSelectionCategory,
    FormatCategory,
    ModalityCategory,
    ModalityFileProfile,
    ModalityRegistry,
    ObservationGrain,
    SourceClass,
    WorksheetProfile,
)
from ..reporting.privacy import PrivacyGuard
from ..validation.grain import GrainAnalyzer
from .reader import SafeDataReader


class DatasetInventoryAuditor:
    """Audits multimodal source files strictly within canonical PPMI source domains."""

    def __init__(self, config: Optional[PipelineConfig] = None) -> None:
        self.config = config or get_default_config()
        self.registry = ModalityRegistry()

    def audit_source_universe(self) -> List[ModalityFileProfile]:
        """Audit ONLY the 17 named PPMI source data folders (the canonical source universe)."""
        root = self.config.project_root.resolve()
        profiles: List[ModalityFileProfile] = []

        for folder_name in sorted(self.config.domain_folders):
            folder_path = root / folder_name
            if not folder_path.is_dir():
                continue

            for dirpath, dirnames, filenames in os.walk(folder_path):
                # Skip internal cache directories if any
                if "__pycache__" in dirnames:
                    dirnames.remove("__pycache__")
                if ".pytest_cache" in dirnames:
                    dirnames.remove(".pytest_cache")

                for fname in sorted(filenames):
                    fpath = Path(dirpath) / fname
                    profile = self._audit_source_file(fpath, root, folder_name)
                    profiles.append(profile)

        return profiles

    def audit_project_artifacts(self) -> List[ModalityFileProfile]:
        """Audit project code, generated reports, manual builds, and root docs in a distinct inventory."""
        root = self.config.project_root.resolve()
        profiles: List[ModalityFileProfile] = []

        for entry in sorted(os.listdir(root)):
            entry_path = root / entry
            # Ignore git and vscode
            if entry in {".git", ".vscode", "__pycache__"}:
                continue

            # If entry is in the 17 source domains, skip here (it belongs to source universe)
            if entry in self.config.domain_folders:
                continue

            if entry_path.is_dir():
                for dirpath, dirnames, filenames in os.walk(entry_path):
                    if "__pycache__" in dirnames:
                        dirnames.remove("__pycache__")
                    if ".pytest_cache" in dirnames:
                        dirnames.remove(".pytest_cache")
                    for fname in sorted(filenames):
                        fpath = Path(dirpath) / fname
                        profile = self._audit_non_source_file(fpath, root)
                        profiles.append(profile)
            elif entry_path.is_file():
                profile = self._audit_non_source_file(entry_path, root)
                profiles.append(profile)

        return profiles

    def _audit_source_file(self, file_path: Path, root: Path, domain_folder: str) -> ModalityFileProfile:
        """Audit an authentic source file within the 17 named domains."""
        rel_path = str(file_path.relative_to(root)).replace("\\", "/")
        file_name = file_path.name
        ext = file_path.suffix.lower()
        size_bytes = file_path.stat().st_size
        sha256_hash = SafeDataReader.compute_sha256(file_path)

        is_sidecar = file_name.startswith("._") or "__MACOSX" in file_path.parts
        modality = self.registry.classify_file_modality(file_path)
        format_cat = self.registry.classify_file_format(file_path)

        is_doc = format_cat in {FormatCategory.DOCUMENT_PDF, FormatCategory.DOCUMENT_DOCX, FormatCategory.TEXT_DOCUMENT}
        is_raw = ext in {".csv", ".xlsx"} and ("curated" not in rel_path.lower())
        is_derived = "curated" in rel_path.lower() or "quant_sbr" in file_name.lower() or "aparc" in file_name.lower() or "aseg" in file_name.lower() or "roi" in file_name.lower()

        source_class = (
            SourceClass.MACOS_SIDECAR if is_sidecar else
            SourceClass.STUDY_DOCUMENTATION if is_doc else
            SourceClass.SOURCE_DATA
        )

        profile = ModalityFileProfile(
            file_path=file_path,
            relative_path=rel_path,
            file_name=file_name,
            file_extension=ext,
            file_size_bytes=size_bytes,
            source_class=source_class,
            modality=modality,
            format_category=format_cat,
            is_raw_data=is_raw,
            is_derived_measurement=is_derived,
            is_documentation=is_doc,
            is_macos_sidecar=is_sidecar,
            file_sha256=sha256_hash,
            selection_category=DatasetSelectionCategory.SELECTION_PENDING,
            selection_justification="Selection Pending (Awaiting Supervisor & Selection Gate Approval)",
        )

        if is_sidecar:
            profile.availability_note = "Unreadable macOS metadata resource fork (._ sidecar)"
            profile.observation_grain = ObservationGrain.UNINDEXED_OR_UNKNOWN
            profile.quality_concerns.append("System macOS resource fork sidecar; contains no user data")
            return profile

        # Audit content based on format
        if format_cat in {FormatCategory.TABULAR_CSV, FormatCategory.TIME_SERIES} or ext == ".csv":
            self._audit_csv_file(profile)
        elif format_cat == FormatCategory.TABULAR_EXCEL or ext in {".xlsx", ".xls"}:
            self._audit_excel_file(profile)
        elif format_cat == FormatCategory.DOCUMENT_PDF or ext == ".pdf":
            self._audit_pdf_file(profile)
        elif format_cat == FormatCategory.DOCUMENT_DOCX or ext == ".docx":
            self._audit_docx_file(profile)

        self._annotate_documentation_provenance(profile)
        return profile

    def _audit_non_source_file(self, file_path: Path, root: Path) -> ModalityFileProfile:
        """Audit a project, generated artifact, or manual build file."""
        rel_path = str(file_path.relative_to(root)).replace("\\", "/")
        file_name = file_path.name
        ext = file_path.suffix.lower()
        size_bytes = file_path.stat().st_size

        if "outputs" in rel_path or "reports" in rel_path:
            s_class = SourceClass.GENERATED_ARTIFACT
        else:
            s_class = SourceClass.PROJECT_CODE

        return ModalityFileProfile(
            file_path=file_path,
            relative_path=rel_path,
            file_name=file_name,
            file_extension=ext,
            file_size_bytes=size_bytes,
            source_class=s_class,
            modality=ModalityCategory.PIPELINE_INTERNAL,
            format_category=self.registry.classify_file_format(file_path),
            is_raw_data=False,
            is_derived_measurement=False,
            is_documentation=False,
            availability_note="Internal project code or generated output",
            selection_category=DatasetSelectionCategory.EXCLUDED_FROM_DETAILED_EDA,
            selection_justification="Project codebase or generated artifact; excluded from source dataset universe.",
        )

    def _audit_csv_file(self, profile: ModalityFileProfile) -> None:
        """Audit CSV table schema, literal headers, logical record counts, identifiers, and grain."""
        fpath = profile.file_path
        try:
            # 1. Exact literal headers and duplicate/blank detection
            lit_headers, dups, blank_cnt, parser_aliases = SafeDataReader.read_csv_header(fpath)
            profile.literal_columns = lit_headers
            profile.columns = lit_headers
            profile.column_count = len(lit_headers)
            profile.duplicate_headers = dups
            profile.blank_headers_count = blank_cnt
            profile.parser_aliases = parser_aliases

            if blank_cnt > 0:
                profile.quality_concerns.append(f"Contains {blank_cnt} blank header name(s)")
            if len(dups) > 0:
                profile.quality_concerns.append(f"Contains duplicate column header(s): {dups}")

            # 2. Identifier detection
            cols_upper = {c.strip().upper(): c for c in lit_headers}
            detected_ids: List[str] = []
            if "PATNO" in cols_upper:
                detected_ids.append("PATNO")
                profile.has_participant_id = True
            elif "ALIAS_ID" in cols_upper:
                detected_ids.append("ALIAS_ID")
                profile.has_participant_id = True
            elif "SUBJID" in cols_upper:
                detected_ids.append("SUBJID")
                profile.has_participant_id = True

            if "EVENT_ID" in cols_upper:
                detected_ids.append("EVENT_ID")
                profile.has_visit_id = True
            elif "CLINICAL_EVENT" in cols_upper:
                detected_ids.append("CLINICAL_EVENT")
                profile.has_visit_id = True

            profile.detected_identifiers = detected_ids

            if profile.file_size_bytes == 0:
                profile.row_count = 0
                profile.observation_grain = ObservationGrain.UNINDEXED_OR_UNKNOWN
                profile.quality_concerns.append("Zero-byte empty file")
                return

            # 3. Accurate logical record counting (CSV parser)
            logical_records = SafeDataReader.count_csv_logical_records(fpath)
            profile.row_count = logical_records

            if logical_records == 0:
                profile.quality_concerns.append("Zero data records (header line only)")
                profile.observation_grain = ObservationGrain.DOCUMENTATION_OR_METADATA
                profile.is_full_data_validated = True
                profile.null_rate_percent = None
                profile.column_dictionary = self._generate_column_dictionary(
                    pd.DataFrame(columns=profile.columns),
                    lit_headers,
                    parser_aliases=parser_aliases,
                    is_zero_rows=True,
                )
                return

            # 4. Read for grain and null analysis
            # For files <= 25MB, read full data for 100% certified grain analysis
            is_sample = False
            if profile.file_size_bytes > 25 * 1024 * 1024:
                df = SafeDataReader.read_csv(fpath, nrows=25000)
                is_sample = True
            else:
                df = SafeDataReader.read_csv(fpath)

            profile.is_full_data_validated = not is_sample

            # 5. Grain analysis with full candidate key evaluation
            grain_result = GrainAnalyzer.analyze(df, file_context=profile.relative_path, is_sample=is_sample)
            profile.observation_grain = grain_result.grain
            profile.candidate_primary_keys = [", ".join(k) for k in grain_result.candidate_primary_keys]
            profile.max_key_multiplicity = grain_result.max_multiplicity_per_visit or grain_result.max_multiplicity_per_subject
            profile.distinct_participants = grain_result.distinct_participants
            profile.distinct_visits = grain_result.distinct_visits
            profile.null_participant_keys = grain_result.null_participant_keys
            profile.null_visit_keys = grain_result.null_visit_keys

            # 6. Null rate & duplicate row checks
            null_sum = int(df.isna().sum().sum())
            total_cells = max(len(df) * max(len(df.columns), 1), 1)
            profile.null_rate_percent = round((null_sum / total_cells) * 100.0, 2)

            dup_count = int(df.duplicated().sum())
            profile.duplicate_rows_count = dup_count
            if dup_count > 0:
                profile.quality_concerns.append(f"Contains {dup_count} duplicate row(s)")

            if not profile.has_participant_id:
                profile.quality_concerns.append("No participant identifier (PATNO/ALIAS_ID) found")

            # 7. Position-based column dictionary preserving duplicate column statistics
            profile.column_dictionary = self._generate_column_dictionary(
                df, lit_headers, parser_aliases=parser_aliases, is_zero_rows=False
            )

        except Exception as err:
            sanitized_err = PrivacyGuard.sanitize_exception(err)
            profile.quality_concerns.append(f"Error auditing CSV: {sanitized_err}")
            profile.observation_grain = ObservationGrain.UNINDEXED_OR_UNKNOWN

    def _audit_excel_file(self, profile: ModalityFileProfile) -> None:
        """Audit multi-sheet Excel (.xlsx) workbooks per individual worksheet."""
        try:
            worksheets = SafeDataReader.audit_excel_workbook(profile.file_path)
            profile.worksheets = worksheets
            profile.extra_metadata["sheet_count"] = len(worksheets)
            profile.extra_metadata["sheet_names"] = [ws.sheet_name for ws in worksheets]

            total_rows = sum(ws.row_count for ws in worksheets)
            profile.row_count = total_rows

            # Overall profile columns reflect first primary sheet
            if len(worksheets) > 0:
                first_ws = worksheets[0]
                profile.columns = first_ws.columns
                profile.literal_columns = first_ws.literal_columns
                profile.column_count = first_ws.column_count
                profile.has_participant_id = any(ws.has_participant_id for ws in worksheets)
                profile.has_visit_id = any(ws.has_visit_id for ws in worksheets)
                profile.distinct_participants = max((ws.distinct_participants for ws in worksheets), default=0)
                profile.distinct_visits = max((ws.distinct_visits for ws in worksheets), default=0)
                profile.observation_grain = first_ws.observation_grain
                profile.candidate_primary_keys = first_ws.candidate_primary_keys

            profile.availability_note = f"Physically present Excel workbook ({len(worksheets)} worksheets audited)"
        except Exception as err:
            sanitized_err = PrivacyGuard.sanitize_exception(err)
            profile.quality_concerns.append(f"Error auditing Excel workbook: {sanitized_err}")

    def _audit_pdf_file(self, profile: ModalityFileProfile) -> None:
        """Audit PDF study manual or methods guide."""
        try:
            meta = SafeDataReader.read_pdf_metadata(profile.file_path)
            profile.extra_metadata["page_count"] = meta.get("page_count", 0)
            profile.observation_grain = ObservationGrain.DOCUMENTATION_OR_METADATA
            profile.availability_note = f"Methods/Protocol PDF manual ({meta.get('page_count', 0)} pages)"
        except Exception as err:
            sanitized_err = PrivacyGuard.sanitize_exception(err)
            profile.quality_concerns.append(f"Error reading PDF: {sanitized_err}")

    def _audit_docx_file(self, profile: ModalityFileProfile) -> None:
        """Audit Word (.docx) methods document."""
        try:
            meta = SafeDataReader.read_docx_metadata(profile.file_path)
            profile.extra_metadata["paragraph_count"] = meta.get("paragraph_count", 0)
            profile.extra_metadata["table_count"] = meta.get("table_count", 0)
            profile.observation_grain = ObservationGrain.DOCUMENTATION_OR_METADATA
            profile.availability_note = f"Methods/Protocol DOCX document ({meta.get('paragraph_count', 0)} paragraphs)"
        except Exception as err:
            sanitized_err = PrivacyGuard.sanitize_exception(err)
            profile.quality_concerns.append(f"Error reading DOCX: {sanitized_err}")

    def _generate_column_dictionary(
        self,
        df: pd.DataFrame,
        literal_headers: List[str],
        parser_aliases: Optional[Dict[str, str]] = None,
        is_zero_rows: bool = False,
    ) -> List[Dict[str, Any]]:
        """Extract complete, ordered column dictionary by column position.
        
        Preserves each literal header, its parser alias, and exact per-position missingness
        even when duplicate column names exist in the source file.
        """
        col_dict: List[Dict[str, Any]] = []
        parser_aliases = parser_aliases or {}
        num_cols = len(literal_headers)
        total_rows = len(df)

        for idx in range(num_cols):
            lit_col = literal_headers[idx]
            alias_key = f"idx_{idx}_{lit_col}"
            parser_alias = parser_aliases.get(alias_key, lit_col.strip() or f"Unnamed: {idx}")
            col_upper = lit_col.strip().upper()

            # Assign preliminary role without guessing unverified clinical definitions
            if col_upper in {"PATNO", "ALIAS_ID", "SUBJID"}:
                role = "Participant Identifier (Primary Key)"
                v_type = "identifier"
            elif col_upper in {"EVENT_ID", "VISIT", "CLINICAL_EVENT"}:
                role = "Visit Milestone Identifier (Join Key)"
                v_type = "categorical_visit_code"
            elif col_upper in {"INFODT", "VISIT_DATE", "EXAM_DATE", "SCAN_DATE", "BIRTHDT", "EXAMDT", "ORIG_ENTRY", "LAST_UPDATE"}:
                role = "Temporal / Date Stamp"
                v_type = "date_temporal"
            elif col_upper in {"PAG_NAME", "LINE_NO", "SEQNO", "RECNO"}:
                role = "Instrument Form / Line Tracker"
                v_type = "structural_metadata"
            elif col_upper == "REC_ID":
                role = "Database Record Surrogate Key"
                v_type = "identifier"
            else:
                v_type = "unverified_feature"
                role = "Clinical Feature / Covariate"

            if is_zero_rows or total_rows == 0:
                col_dict.append({
                    "column_index": idx,
                    "original_name": lit_col,
                    "parser_alias": parser_alias,
                    "inferred_type": v_type,
                    "missingness_percentage": None,  # Data-dependent statistic unavailable
                    "missing_numerator": 0,
                    "missing_denominator": 0,
                    "data_status": "Zero data records (header line only); statistics unavailable",
                    "variable_role": role,
                    "description": "Definition not verified",
                    "unit_or_scoring_range": "Not documented/verified",
                    "used_in_eda": "Pending Selection Approval",
                })
                continue

            # Access column strictly by POSITION to isolate duplicate column statistics
            if idx < df.shape[1]:
                series = df.iloc[:, idx]
                null_count = int(series.isna().sum())
                null_pct = round((null_count / total_rows) * 100.0, 2)

                if pd.api.types.is_float_dtype(series) or pd.api.types.is_integer_dtype(series):
                    v_type = "numeric"
                    if role == "Clinical Feature / Covariate":
                        role = "Continuous or Ordinal Measurement"
                elif pd.api.types.is_string_dtype(series) or isinstance(series.dtype, object):
                    if role == "Clinical Feature / Covariate":
                        v_type = "categorical_or_text"

                col_dict.append({
                    "column_index": idx,
                    "original_name": lit_col,
                    "parser_alias": parser_alias,
                    "inferred_type": v_type,
                    "missingness_percentage": null_pct,
                    "missing_numerator": null_count,
                    "missing_denominator": total_rows,
                    "data_status": "Valid data rows indexed",
                    "variable_role": role,
                    "description": "Definition not verified",
                    "unit_or_scoring_range": "Not documented/verified",
                    "used_in_eda": "Pending Selection Approval",
                })
            else:
                col_dict.append({
                    "column_index": idx,
                    "original_name": lit_col,
                    "parser_alias": parser_alias,
                    "inferred_type": v_type,
                    "missingness_percentage": None,
                    "missing_numerator": 0,
                    "missing_denominator": total_rows,
                    "data_status": "Column index exceeds parsed dataframe width",
                    "variable_role": role,
                    "description": "Definition not verified",
                    "unit_or_scoring_range": "Not documented/verified",
                    "used_in_eda": "Pending Selection Approval",
                })

        return col_dict

    def _annotate_documentation_provenance(self, profile: ModalityFileProfile) -> None:
        """Record documentation provenance and verified physical vs external status.
        
        Strict adherence to Codex P1-08:
        - Only cite local documentation files actually present on disk.
        - Mark external locations, frequency, and remote availability as unverified.
        - Do not assert unverified clinical biomarkers or remote infrastructure.
        """
        mod = profile.modality
        fname = profile.file_name.lower()
        rel_lower = profile.relative_path.lower()

        if mod == ModalityCategory.GENETICS_MOLECULAR:
            profile.documentation_provenance = (
                "subject_characteristics/PPMI_Consensus_APOE_SNPs_and_Pathogenic_Variants_Methods_20250515.pdf; "
                "subject_characteristics/PPMI_Risk_SNP_PGS_Methods_20251202.pdf"
            )
            profile.availability_note = (
                "Physically present locally: Tabular genetic variant calls and risk scores. "
                "External references: Definition/availability not verified from local repository files."
            )
        elif mod == ModalityCategory.IMAGING:
            if "datscan" in rel_lower:
                profile.documentation_provenance = "DATSCAN/PPMI_DaTSCAN_SPECT_Preprocessing_Methods_v1.0_20250902.pdf"
            elif "mr analysis" in rel_lower:
                profile.documentation_provenance = "MR Analysis Results/PPMI_rs-fMRI_Data-and-Methods/PPMI_Methods_rs-fMRI_Data_FINAL_2019_12_04.docx"
            elif "dti" in rel_lower:
                profile.documentation_provenance = "dti/PPMI_DTI_ROI_Methods_20160915.pdf"
            else:
                profile.documentation_provenance = "Documentary provenance pending formal documentation link"

            profile.availability_note = (
                "Physically present locally: Derived quantitative imaging tabular files. "
                "External references (raw 3D/4D series): Definition/availability not verified from local repository files."
            )
        elif mod == ModalityCategory.DIGITAL_SENSOR:
            profile.documentation_provenance = "digital_Sensor/PPMI_Methods_Document_Roche_v1.1.pdf"
            profile.availability_note = (
                "Physically present locally: Processed active tests and sensor features. "
                "External references: Definition/availability not verified from local repository files."
            )
        elif mod == ModalityCategory.BIOSPECIMEN:
            profile.documentation_provenance = "biospecimen/PPMI_IPSC_Catalog_User_Guide(1).xlsx"
            profile.availability_note = (
                "Physically present locally: Tabular biofluid assays and cell repository catalog. "
                "External references: Definition/availability not verified from local repository files."
            )
        elif mod == ModalityCategory.CURATED_MULTIMODAL:
            profile.documentation_provenance = "curated_datacuts/PPMI_Curated_Data_Cut_Public_20260810(1).xlsx (sheets: 'Data dictionary', 'Information')"
            profile.availability_note = "Physically present locally: Multi-sheet curated dataset workbook."
        else:
            profile.documentation_provenance = "Documentary provenance pending formal Phase 2 cataloging"
            profile.availability_note = "Physically present locally"
