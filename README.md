# PPMI Multimodal Exploratory Data Analysis

Publication-oriented, reproducible Jupyter notebooks for exploratory analysis of the Parkinson's Progression Markers Initiative (PPMI) across clinical, biospecimen, genetics, neuroimaging, digital-sensor, and multimodal domains.

## Data access and privacy

PPMI source data are **not included** in this repository. Obtain data through the official PPMI access process and keep participant-level files in an authorized local environment. Do not commit source data, generated participant-level outputs, credentials, or identifiers.

The notebooks report privacy-safe summaries and are intended for descriptive exploration. Associations must not be interpreted as causal or confirmatory evidence.

## Notebooks

Run from a clean kernel in this order:

1. `00_dataset_overview.ipynb` — inventory, structural audit, selection evidence, and schema catalog.
2. `eda_clinical.ipynb` — demographics, clinical assessments, and longitudinal phenotyping.
3. `eda_biospecimen.ipynb` — biospecimen coverage and biomarker distributions.
4. `eda_genetics.ipynb` — genetic and molecular profiling.
5. `eda_neuroimaging.ipynb` — DaTscan, MRI, DTI, rs-fMRI, and related imaging summaries.
6. `eda_digital_sensors.ipynb` — mobile and digital-sensor coverage and repeated measures.
7. `eda_multimodal_synthesis.ipynb` — privacy-safe cross-modal coverage and synthesis.

Each modality notebook includes selected-source rationale, complete source-column dictionaries, data-quality assessment, clinically motivated analyses, figures, interpretation, limitations, and conclusions grounded in computed results.

## Environment

Python 3.11 is recommended.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
$env:PYTHONPATH = "$PWD\EDA\src"
python -m pytest
jupyter lab
```

The analysis expects the authorized PPMI directory structure described in the research plan. Path resolution and modality contracts are implemented under `EDA/src/ppmi_pipeline`. Notebook generators are retained under `EDA/scripts` to make the notebook build process auditable.

## Reproducibility and governance

- Original PPMI files are treated as immutable.
- Observation grain and join cardinality must be validated before merging.
- Many-to-many joins are prohibited unless explicitly justified and audited.
- Missing-value semantics are instrument-specific; undocumented numeric codes are not globally recoded.
- Statistical results and narrative findings are computed at execution time, not hardcoded.
- Automated checks are provided under `EDA/tests`.

See `docs/research_plan.md`, `docs/methodology_decisions.md`, and `docs/phase_specs/` for the scientific and QA specifications.

## Citation

This repository contains analysis code and notebooks only. Cite PPMI and the relevant PPMI data release according to the terms accompanying the authorized data download.
