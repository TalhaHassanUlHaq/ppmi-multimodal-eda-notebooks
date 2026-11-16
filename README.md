# PPMI Multimodal Exploratory Data Analysis (EDA) Pipeline

[![Status: Approved](https://img.shields.io/badge/Status-Approved_by_Codex-brightgreen.svg)](docs/review_log.md)
[![Tests: 31 Passing](https://img.shields.io/badge/Tests-31%2F31_Passing-success.svg)](EDA/tests/test_notebook_contracts.py)
[![Privacy: Certified](https://img.shields.io/badge/PrivacyGuard-Certified-blue.svg)](EDA/src/ppmi_pipeline/reporting/privacy.py)
[![Raw Sources: 100% Immutable](https://img.shields.io/badge/Raw_Sources-177%2F177_Verified-blue.svg)](EDA/tests/test_notebook_contracts.py)

Research-grade, modular, and fully reproducible exploratory data analysis pipeline for the **Parkinson's Progression Markers Initiative (PPMI)** multimodal dataset.

---

## 1. Directory Structure

```text
ppmi/
├── README.md                                  # Repository overview and execution guide
├── AGENTS.md                                  # Project mandate and two-agent governance rules
├── pytest.ini                                 # Pytest configuration and root directory anchors
├── .gitignore                                 # Git ignore patterns for build/cache artifacts
│
├── notebooks/                                 # Publication-grade Jupyter Notebook Suite
│   ├── 00_dataset_overview.ipynb              # Phase 1: Full inventory, schema catalog, repeated events
│   ├── eda_clinical.ipynb                     # Phase 2: Demographics, UPDRS I-IV, MoCA, non-motor, LEDD
│   ├── eda_biospecimen.ipynb                  # Phase 3: CSF core analytes (Aβ42, tau), SAA, plasma, IUSM catalogs
│   ├── eda_genetics.ipynb                     # Phase 3: Consensus mutations (LRRK2, GBA), APOE, PRS, sequencing
│   ├── eda_neuroimaging.ipynb                 # Phase 4: DaTscan SPECT (SBR & visual), MRI, DTI ROI, rs-fMRI, PET
│   ├── eda_digital_sensors.ipynb              # Phase 4: Roche mobile app telemetry, adherence, laterality asymmetry
│   └── eda_multimodal_synthesis.ipynb         # Phase 5: Cross-modal overlap matrix, selection bias, triangulation
│
├── EDA/                                       # Core analytical pipeline package & test suite
│   ├── src/ppmi_pipeline/                     # Modular Python pipeline package
│   │   ├── ingestion/                         # Multi-format source file inventory & schema readers
│   │   ├── validation/                        # Relational grain, cardinality & dataset selection engine
│   │   ├── reporting/                         # PrivacyGuard, notebook support layer, audit tables
│   │   └── modalities/                        # Modality-specific domain transformation helpers
│   ├── tests/                                 # Automated test suite (31 contract tests + regression tests)
│   │   ├── test_notebook_contracts.py         # End-to-end notebook contracts, skewness, parity, negative mutations
│   │   ├── test_privacy.py                    # Fail-closed PrivacyGuard regex scanners and allowlist tests
│   │   ├── test_cardinality.py                # Join cardinality validation (1:1, 1:m, m:1, unconditional m:m rejection)
│   │   ├── test_grain.py                      # Observation grain detection and key uniqueness tests
│   │   ├── test_selection.py                  # Dataset selection matrix and 177 source hash tests
│   │   └── test_reader.py                     # Multi-format physical reader parity tests
│   ├── scripts/                               # Deterministic notebook generators and agent bridge
│   │   ├── agent_bridge.py                    # Bidirectional communication bridge between Gemini & Codex
│   │   ├── generate_clinical_notebook.py      # Clean-kernel generator for eda_clinical.ipynb
│   │   ├── generate_biospecimen_notebook.py   # Clean-kernel generator for eda_biospecimen.ipynb
│   │   ├── generate_genetics_notebook.py      # Clean-kernel generator for eda_genetics.ipynb
│   │   ├── generate_neuroimaging_notebook.py  # Clean-kernel generator for eda_neuroimaging.ipynb
│   │   ├── generate_sensors_notebook.py       # Clean-kernel generator for eda_digital_sensors.ipynb
│   │   └── generate_synthesis_notebook.py     # Clean-kernel generator for eda_multimodal_synthesis.ipynb
│   └── outputs/reports/                       # Canonical project manifests, catalogs, and report mirrors
│       ├── multimodal_eda_sprint_implementation_report.md  # Synchronized implementation report mirror
│       ├── dataset_selection_matrix.json      # Approved 183-decision-unit selection matrix
│       ├── phase1_multimodal_inventory.json   # Full inventory of all 177 physical source files
│       └── phase1_schema_catalog.json         # Complete extracted column schemas and grains
│
├── docs/                                      # Project documentation, specifications & review logs
│   ├── multimodal_eda_sprint_implementation_report.md  # Primary formal implementation report
│   ├── review_log.md                          # Independent supervisory review log (Codex verdicts)
│   ├── dataset_selection_decisions.md         # Formal dataset selection gate documentation
│   └── phase_specs/                           # Phase specifications and extension requirements
│
├── manual/                                    # PPMI Dataset Manual and documentation build assets
│   ├── ppmi_manual.pdf                        # Comprehensive compiled PPMI data documentation manual
│   ├── ppmi_manual.tex                        # Master LaTeX document
│   ├── ppmi_dataset_documentation.pdf         # Standalone dataset documentation summary
│   ├── ppmi_dataset_documentation.tex         # Standalone LaTeX source
│   ├── sections/                              # Modality-specific LaTeX chapter sections (00 to 18)
│   └── builder/                               # Manual compilation scripts, metadata, and chapter generators
│
└── [Raw PPMI Source Directories]              # 17 raw data folders (177 files, strictly immutable)
    ├── biospecimen/                           # IUSM aliquot catalogs, cellular models, whole blood substudy
    ├── curated_datacuts/                      # Harmonized multi-visit milestone cuts (public release 20260810)
    ├── DATSCAN/                               # DaTscan SPECT quantitative SBR and central visual reads
    ├── digital_Sensor/                        # Roche Mobile App v2 continuous active tests and surveys
    ├── dti/                                   # Diffusion Tensor Imaging planar region-of-interest extractions
    ├── MEDICAL HISTORY/                       # Baseline medical conditions, adverse events, freezing & falls
    ├── MOTOR/                                 # MDS-UPDRS Parts I-IV, Schwab & England ADL, LEDD
    ├── MR Analysis Results/                   # FreeSurfer v7 (ASEG, APARC), MRIQC, rs-fMRI motion reports
    ├── MRI Acquisition/                       # Technical sequence logs and core-lab image quality flags
    ├── neurobehavioral/                       # Epworth Sleepiness, REM Sleep Behavior Disorder (RBDSQ)
    ├── neuropsychological/                    # MoCA, SDMT, HVLT-R, Trail Making Test A & B, Benton JLO
    ├── non motor/                             # SCOPA-AUT autonomic function questionnaires
    ├── olfactory/                             # UPSIT 40-item smell identification scores
    ├── other cognitive/                       # Supplementary neurocognitive testing forms
    ├── PET/                                   # Molecular PET tracers (AV-133, SV2A, PI-2620, DPA-714)
    ├── sleep disorder/                        # Sleep clinic polysomnography logs and screening
    └── subject_characteristics/               # Demographics, consensus genetics (LRRK2, GBA), APOE, PRS
```

---

## 2. Deliverable Notebook Suite

All seven Jupyter notebooks run top-to-bottom from a clean IPython kernel with **zero errors**, **zero unexecuted code cells**, and **100% PrivacyGuard certification**:

| # | Notebook | Modality & Scope | Code Cells | Outputs | Errors |
| :-: | :--- | :--- | :-: | :-: | :-: |
| 1 | [`00_dataset_overview.ipynb`](notebooks/00_dataset_overview.ipynb) | Complete structural inventory, schema catalog, repeated-event analysis, selection matrix | 21 | 38 | 0 |
| 2 | [`eda_clinical.ipynb`](notebooks/eda_clinical.ipynb) | Demographics, longitudinal UPDRS I–IV, MoCA trajectories, LEDD, deep cognitive tests | 21 | 54 | 0 |
| 3 | [`eda_biospecimen.ipynb`](notebooks/eda_biospecimen.ipynb) | Core CSF analytes (Aβ42, t-tau, p-tau), CSF SAA synuclein seeding, plasma biomarkers | 15 | 39 | 0 |
| 4 | [`eda_genetics.ipynb`](notebooks/eda_genetics.ipynb) | Monogenic variants (*LRRK2*, *GBA*), *APOE* $\varepsilon4$, polygenic risk scores (GP2, META5), WGS | 14 | 35 | 0 |
| 5 | [`eda_neuroimaging.ipynb`](notebooks/eda_neuroimaging.ipynb) | DaTscan SPECT (SBR & visual), FreeSurfer v7 volumetrics, DTI ROI, rs-fMRI motion, PET | 17 | 56 | 0 |
| 6 | [`eda_digital_sensors.ipynb`](notebooks/eda_digital_sensors.ipynb) | Roche mobile app telemetry, participant adherence, task battery, paired laterality asymmetry | 14 | 30 | 0 |
| 7 | [`eda_multimodal_synthesis.ipynb`](notebooks/eda_multimodal_synthesis.ipynb) | Cross-modal participant overlap, selection bias audits, join audits, biological triangulation | 15 | 34 | 0 |
| **Total** | **All 7 Deliverables** | **Full PPMI Multimodal EDA Suite** | **117** | **286** | **0** |

---

## 3. Strict Operating Invariants

1. **Preservation of Raw Files**: All 177 physical source files (`.csv`, `.xlsx`, `.pdf`, `.docx`) across the 17 raw data folders remain strictly immutable and byte-identical (100% verified via automated SHA-256 hash checks).
2. **Fail-Closed PrivacyGuard**: Zero participant identifiers (`PATNO`), scan IDs, or row-level personal health information (PHI) are exposed. All cell sizes $<5$ are strictly suppressed (`<5 (Suppressed)`) with non-reconstructible complementary suppression.
3. **Safe Join Cardinality**: All relational merges declare explicit keys, verify null absence, evaluate key uniqueness, and enforce expected cardinality (1:1, 1:m) via `validate_safe_merge()`. Unchecked many-to-many Cartesian merges fail closed unconditionally.
4. **Artifact-Derived Report Parity**: Both copies of the implementation report (`docs/` and `EDA/outputs/reports/`) are byte-identical (SHA-256 `8843FAC6...`) and derived programmatically from executed notebook JSONs and tables.

---

## 4. Verification & Testing

To run the full notebook contract test suite:

```bash
pytest EDA/tests/test_notebook_contracts.py -v
```

To run the comprehensive test suite across all pipeline modules:

```bash
pytest EDA/tests/ -v
```

---

## 5. Two-Agent Governance

Development operates under an explicit two-agent governance mandate documented in [`AGENTS.md`](AGENTS.md):
- **Codex (Research Architect & Technical Supervisor)**: Independently reviews all code, notebook artifacts, execution logs, and reports. Formal approval recorded in [`docs/review_log.md`](docs/review_log.md).
- **Gemini (Implementation Engineer)**: Responsible for pipeline engineering, reproducible notebook generation, test coverage, and documentation parity.

