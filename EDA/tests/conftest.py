"""Pytest configuration and test fixtures for the PPMI pipeline."""

import sys
from pathlib import Path
import pytest
import pandas as pd

# Add EDA/src to sys.path
test_dir = Path(__file__).resolve().parent
src_dir = test_dir.parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))


@pytest.fixture
def synthetic_subject_level_df() -> pd.DataFrame:
    """Fixture providing synthetic 1:1 participant-level demographic table."""
    return pd.DataFrame({
        "PATNO": [1001, 1002, 1003, 1004],
        "BIRTHDT": ["1955-03-12", "1960-07-21", "1948-11-04", "1965-01-19"],
        "GENDER": [1, 2, 1, 2],
        "EDUCYRS": [16, 18, 12, 16],
    })


@pytest.fixture
def synthetic_visit_level_df() -> pd.DataFrame:
    """Fixture providing synthetic visit-level clinical table (1 row per PATNO + EVENT_ID)."""
    return pd.DataFrame({
        "PATNO": [1001, 1001, 1002, 1002, 1003],
        "EVENT_ID": ["BL", "V04", "BL", "V04", "BL"],
        "PAG_NAME": ["NUPDR3", "NUPDR3", "NUPDR3", "NUPDR3", "NUPDR3"],
        "NP3TOT": [22, 28, 14, 18, 35],
    })


@pytest.fixture
def synthetic_repeated_event_df() -> pd.DataFrame:
    """Fixture providing synthetic multi-record adverse event or concomitant med table."""
    return pd.DataFrame({
        "PATNO": [1001, 1001, 1001, 1002],
        "EVENT_ID": ["BL", "BL", "V04", "BL"],
        "LINE_NO": [1, 2, 1, 1],
        "CMTRT": ["Levodopa", "Pramipexole", "Levodopa", "Rasagiline"],
        "CMDOS": ["100mg", "0.5mg", "150mg", "1mg"],
    })


@pytest.fixture
def synthetic_unindexed_df() -> pd.DataFrame:
    """Fixture providing synthetic reference/protocol table without PATNO."""
    return pd.DataFrame({
        "TESTNAME": ["ABETA42", "TOTAL_TAU", "PTAU181", "ALPHA_SYN"],
        "UNITS": ["pg/mL", "pg/mL", "pg/mL", "pg/mL"],
        "LLOQ": [200.0, 80.0, 8.0, 10.0],
    })

