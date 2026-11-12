"""Safe, multi-format, read-only data ingestion reader.

Guarantees strict immutability of raw input files across tabular, spreadsheet,
and document formats. Accurately handles quoted newlines, literal headers,
missing trailing newlines, and multi-sheet Excel workbooks.
"""

from collections import Counter
import csv
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import warnings

import openpyxl
import pandas as pd

try:
    import pypdf
except ImportError:
    pypdf = None

try:
    import docx
except ImportError:
    docx = None

from ..modalities.base import WorksheetProfile


class SafeDataReader:
    """Read-only reader supporting PPMI multi-format datasets."""

    ENCODINGS: List[str] = ["utf-8", "utf-8-sig", "latin-1", "cp1252", "iso-8859-1"]

    @staticmethod
    def compute_sha256(file_path: Union[str, Path]) -> str:
        """Compute SHA-256 checksum of a file without modifying mtime."""
        path = Path(file_path).resolve()
        hasher = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    @staticmethod
    def read_csv(
        file_path: Union[str, Path],
        nrows: Optional[int] = None,
        usecols: Optional[List[str]] = None,
        dtype: Optional[Union[type, Dict[str, Any]]] = None,
        low_memory: bool = False,
    ) -> pd.DataFrame:
        """Safely read a CSV file with automatic encoding fallback.
        
        Guarantees:
        - Opens strictly in read-only mode.
        - Preserves raw string representation when requested.
        - Never modifies the source file.
        """
        path = Path(file_path).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Source CSV file does not exist: {path}")

        for encoding in SafeDataReader.ENCODINGS:
            try:
                with open(path, mode="r", encoding=encoding, errors="strict") as f:
                    df = pd.read_csv(
                        f,
                        nrows=nrows,
                        usecols=usecols,
                        dtype=dtype,
                        low_memory=low_memory,
                    )
                return df
            except (UnicodeDecodeError, UnicodeError):
                continue
            except Exception as err:
                raise IOError(f"Failed to parse CSV file '{path.name}': {err}") from err

        with open(path, mode="r", encoding="utf-8", errors="replace") as f:
            return pd.read_csv(
                f,
                nrows=nrows,
                usecols=usecols,
                dtype=dtype,
                low_memory=low_memory,
            )

    @staticmethod
    def read_csv_header(
        file_path: Union[str, Path]
    ) -> Tuple[List[str], List[str], int, Dict[str, str]]:
        """Extract literal original headers preserving whitespace, order, and duplicates.
        
        Returns:
            literal_headers: exact string headers as written in raw file.
            duplicate_headers: list of headers that appear multiple times.
            blank_headers_count: number of empty or whitespace-only headers.
            parser_aliases: dictionary mapping literal header to pandas parser alias.
        """
        path = Path(file_path).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Source file does not exist: {path}")

        for encoding in SafeDataReader.ENCODINGS:
            try:
                with open(path, mode="r", encoding=encoding, errors="replace", newline="") as f:
                    reader = csv.reader(f)
                    literal_header = next(reader, [])
                    break
            except Exception:
                continue
        else:
            literal_header = []

        # Analyze duplicates and blanks without modifying original strings
        blank_count = sum(1 for h in literal_header if len(h.strip()) == 0)
        counts = Counter(literal_header)
        duplicate_headers = [h for h, count in counts.items() if count > 1 and h.strip() != ""]

        # Compute pandas parser alias mapping
        seen: Dict[str, int] = {}
        parser_aliases: Dict[str, str] = {}
        for idx, h in enumerate(literal_header):
            cleaned = h.strip() if h.strip() else f"Unnamed: {idx}"
            if cleaned in seen:
                seen[cleaned] += 1
                alias = f"{cleaned}.{seen[cleaned]}"
            else:
                seen[cleaned] = 0
                alias = cleaned
            parser_aliases[f"idx_{idx}_{h}"] = alias

        return literal_header, duplicate_headers, blank_count, parser_aliases

    @staticmethod
    def count_csv_logical_records(file_path: Union[str, Path]) -> int:
        """Accurately count logical CSV records using a CSV parser.
        
        Correctly handles:
        - Quoted fields containing embedded newlines.
        - Files lacking a trailing newline on the final record.
        - Excludes header line from data record count.
        """
        path = Path(file_path).resolve()
        record_count = 0
        has_header = False

        for encoding in SafeDataReader.ENCODINGS:
            try:
                with open(path, mode="r", encoding=encoding, errors="replace", newline="") as f:
                    reader = csv.reader(f)
                    # Check for header
                    try:
                        next(reader)
                        has_header = True
                    except StopIteration:
                        return 0

                    for _ in reader:
                        record_count += 1
                return record_count
            except Exception:
                continue

        return record_count

    @staticmethod
    def audit_excel_workbook(file_path: Union[str, Path]) -> List[WorksheetProfile]:
        """Audit every individual sheet in an Excel (.xlsx) workbook.
        
        Extracts exact dimensions, literal headers, identifier presence,
        and missingness for each sheet.
        """
        path = Path(file_path).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Source Excel file does not exist: {path}")

        profiles: List[WorksheetProfile] = []

        try:
            wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
            for sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
                # Read all rows into memory for complete structural evaluation
                # (openpyxl read-only generator)
                rows_gen = ws.iter_rows(values_only=True)
                header_row = next(rows_gen, None)
                if header_row is None:
                    # Empty sheet
                    profiles.append(
                        WorksheetProfile(
                            sheet_name=sheet_name,
                            row_count=0,
                            column_count=0,
                            quality_concerns=["Empty worksheet (0 rows)"],
                        )
                    )
                    continue

                literal_headers = [str(c) if c is not None else "" for c in header_row]
                blank_count = sum(1 for h in literal_headers if h.strip() == "")
                counts = Counter(literal_headers)
                dups = [h for h, c in counts.items() if c > 1 and h.strip() != ""]

                data_rows: List[List[Any]] = []
                for row in rows_gen:
                    # Ignore trailing completely empty rows
                    if any(cell is not None for cell in row):
                        data_rows.append(list(row))

                row_count = len(data_rows)
                col_count = len(literal_headers)

                # Build dataframe for key and null analysis
                df_sheet = pd.DataFrame(data_rows, columns=literal_headers[:col_count]) if data_rows else pd.DataFrame(columns=literal_headers)

                # Identifier check
                cols_upper = {c.strip().upper(): c for c in literal_headers}
                detected_ids: List[str] = []
                has_pat = False
                has_vis = False
                distinct_pat = 0
                distinct_vis = 0
                null_pat = 0
                null_vis = 0

                if "PATNO" in cols_upper:
                    pat_col = cols_upper["PATNO"]
                    detected_ids.append("PATNO")
                    has_pat = True
                    null_pat = int(df_sheet[pat_col].isna().sum())
                    distinct_pat = int(df_sheet[pat_col].nunique(dropna=True))

                if "EVENT_ID" in cols_upper:
                    vis_col = cols_upper["EVENT_ID"]
                    detected_ids.append("EVENT_ID")
                    has_vis = True
                    null_vis = int(df_sheet[vis_col].isna().sum())
                    distinct_vis = int(df_sheet[vis_col].nunique(dropna=True))

                # Check duplicate rows
                dup_rows = int(df_sheet.duplicated().sum()) if len(df_sheet) > 0 else 0

                # Check null rates
                total_cells = max(len(df_sheet) * max(col_count, 1), 1)
                null_sum = int(df_sheet.isna().sum().sum())
                null_pct = round((null_sum / total_cells) * 100.0, 2)

                # Determine sheet grain
                from ..validation.grain import GrainAnalyzer
                grain_res = GrainAnalyzer.analyze(df_sheet, file_context=f"{path.name} [{sheet_name}]")

                concerns: List[str] = []
                if row_count == 0:
                    concerns.append("Worksheet contains header only (0 data records)")
                if blank_count > 0:
                    concerns.append(f"Contains {blank_count} blank/unnamed headers")
                if len(dups) > 0:
                    concerns.append(f"Contains duplicate column names: {dups}")
                if dup_rows > 0:
                    concerns.append(f"Contains {dup_rows} duplicate rows")

                profiles.append(
                    WorksheetProfile(
                        sheet_name=sheet_name,
                        row_count=row_count,
                        column_count=col_count,
                        columns=literal_headers,
                        literal_columns=literal_headers,
                        blank_headers_count=blank_count,
                        duplicate_headers=dups,
                        detected_identifiers=detected_ids,
                        has_participant_id=has_pat,
                        has_visit_id=has_vis,
                        distinct_participants=distinct_pat,
                        distinct_visits=distinct_vis,
                        null_participant_keys=null_pat,
                        null_visit_keys=null_vis,
                        observation_grain=grain_res.grain,
                        candidate_primary_keys=[", ".join(k) for k in grain_res.candidate_primary_keys],
                        is_full_data_validated=True,
                        duplicate_rows_count=dup_rows,
                        null_rate_percent=null_pct,
                        quality_concerns=concerns,
                    )
                )

            wb.close()
        except Exception as err:
            profiles.append(
                WorksheetProfile(
                    sheet_name="ErrorReadingWorkbook",
                    row_count=0,
                    column_count=0,
                    quality_concerns=[f"Failed to parse workbook: {err}"],
                )
            )

        return profiles

    @staticmethod
    def read_pdf_metadata(file_path: Union[str, Path]) -> Dict[str, Any]:
        """Extract page count and document information from PDF files."""
        path = Path(file_path).resolve()
        info: Dict[str, Any] = {"page_count": 0, "title": None, "author": None}
        if pypdf is None:
            info["note"] = "pypdf library not available"
            return info

        try:
            with open(path, "rb") as f:
                reader = pypdf.PdfReader(f)
                info["page_count"] = len(reader.pages)
                meta = reader.metadata
                if meta:
                    info["title"] = meta.get("/Title")
                    info["author"] = meta.get("/Author")
        except Exception as err:
            info["error"] = str(err)
        return info

    @staticmethod
    def read_docx_metadata(file_path: Union[str, Path]) -> Dict[str, Any]:
        """Extract paragraph count, table count, and metadata from DOCX files."""
        path = Path(file_path).resolve()
        info: Dict[str, Any] = {"paragraph_count": 0, "table_count": 0}
        if docx is None:
            info["note"] = "python-docx library not available"
            return info

        try:
            doc = docx.Document(path)
            info["paragraph_count"] = len(doc.paragraphs)
            info["table_count"] = len(doc.tables)
            core_props = doc.core_properties
            if core_props:
                info["title"] = core_props.title
                info["author"] = core_props.author
        except Exception as err:
            info["error"] = str(err)
        return info
