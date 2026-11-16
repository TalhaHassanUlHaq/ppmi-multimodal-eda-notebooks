# Modality inventory review

Status: Reconciled Canonical Phase 1 Inventory (Round 3 Reconciliation, 2026-11-12).  
Authoritative Sources:
- Canonical Inventory Manifest: [`EDA/outputs/reports/phase1_multimodal_inventory.json`](../EDA/outputs/reports/phase1_multimodal_inventory.json)
- Schema Catalog: [`EDA/outputs/reports/phase1_schema_catalog.json`](../EDA/outputs/reports/phase1_schema_catalog.json)
- Grain Catalog: [`EDA/outputs/reports/phase1_grain_catalog.json`](../EDA/outputs/reports/phase1_grain_catalog.json)
- Project Artifacts Manifest: [`EDA/outputs/reports/phase1_project_artifacts_manifest.json`](../EDA/outputs/reports/phase1_project_artifacts_manifest.json)
- External References Manifest: [`EDA/outputs/reports/phase1_external_references_manifest.json`](../EDA/outputs/reports/phase1_external_references_manifest.json)
- Repeated-Event & Ambiguous Keys Report: [`EDA/outputs/reports/phase1_repeated_event_keys_report.md`](../EDA/outputs/reports/phase1_repeated_event_keys_report.md)

---

## 1. Scope Reconciliation & Authoritative Counts

| Inventory Scope | File Count | Storage (MB) | Tabular Rows | Status / Notes |
| :--- | ---: | ---: | ---: | :--- |
| **PPMI Source Universe (17 named domain folders)** | **177** | **243.34** | **1,748,882** | 100% reconciled to disk; exactly 177 physical source files |
| **Non-Source Project Artifacts** | **167** | **9.47** | N/A | Pipeline code, tests, reports, and generated catalogs isolated (snapshot as of canonical inventory generation) |
| **Externally Referenced Data Streams** | **7** | N/A | N/A | Remote archives (WGS, RNA-seq, 3D/4D series, raw sensor telemetry) cited with local documentation |

### Dataset Selection Status
- **Selection Pending**: **177 / 177 files (100%)**
- *Governance Invariant*: All automated selection categories from earlier rounds have been retired. Zero files are permanently excluded or approved for detailed EDA until the human researcher and Codex sign off at the Research Dataset Selection Gate. Filename markers such as `(1)` are recognized as download numbering artifacts and do not imply redundancy.

---

## 2. Multi-Sheet Workbook Structural Auditing

Every readable worksheet has been audited independently for dimensions, literal schemas, identifiers, and observation grain:
- `curated_datacuts/PPMI_Curated_Data_Cut_Public_20260810(1).xlsx`:
  - Sheet `20260810`: 20,408 rows × 215 columns (Visit-Level; distinct PATNOs: 5,019)
  - Sheet `Data dictionary`: 452 rows × 10 columns (Documentation / Codebook)
  - Sheet `Information`: 19 rows × 9 columns (Documentation / Metadata)
- `MR Analysis Results/PPMI_rs-fMRI_Data-and-Methods/PPMI_fs-fMRI_dataReport_spreadsheet_FINAL_20191121.xlsx`:
  - Sheet `PPMI_rsfMRI_09052019`: 384 rows × 49 columns (Repeated Event / Scan Session; candidate key: `ImageID`)
  - Sheet `Dictionary`: 32 rows × 4 columns (Documentation / Codebook)
- `biospecimen/PPMI_IPSC_Catalog_User_Guide(1).xlsx`:
  - Sheet `iPSC Catalog Guide`: 24 rows × 6 columns (Documentation / Guide)

---

## 3. Observation Grain & Key Validation Breakdown

| Observation Grain | Table Count | Candidate Key Status | Typical Domain Examples |
| :--- | ---: | :--- | :--- |
| **Subject-Level** | 44 | Unique on `PATNO` | Demographics, Family History, Genetic Consensus, Polygenic Risk Scores |
| **Visit-Level** | 60 | Unique on `(PATNO, EVENT_ID)` | Curated cut `20260810`, MoCA, Vital Signs, DaTscan SBR |
| **Repeated Event / Item-Level** | 38 | Unique on candidate key (`REC_ID`, `ImageID`, or clinical composite) | MDS-UPDRS Part III, Concomitant Meds, Adverse Events, PET ligand tables |
| **Documentation / Reference** | 21 | No participant key (Metadata) | Protocol manuals, data dictionaries, user guides |
| **Ambiguous / Needs Detailed Review** | 12 | Unresolved candidate key / duplicate records | Xing Core Lab MRI QC, Cognitive Activities Session, Roche App, IUSM Catalogs |
| **Unindexed / Unknown Grain** | 2 | Zero-byte or unparsed binary | Corrupted / empty files |
| **Total Physical Source Files** | **177** | **100% Accounted** | Reconciled across all 17 source domains |

## Physical local source folders

| Folder | Files | Domain role to verify |
| --- | ---: | --- |
| `MEDICAL HISTORY` | 64 | Diagnosis, conditions, medication, adverse events, safety and substudies |
| `PET` | 19 | Tracer-specific imaging and derived measurements |
| `DATSCAN` | 14 | SPECT measures, reads, acquisition, and methods |
| `other cognitive` | 14 | Cognitive tasks and questionnaires |
| `MOTOR` | 13 | MDS-UPDRS and gait/motor instruments |
| `MR Analysis Results` | 11 | Derived structural MRI, QC, rs-fMRI report and methods |
| `neuropsychological` | 10 | Cognitive test instruments |
| `subject_characteristics` | 10 | Family/genetic tables and methods; confirm cohort sources elsewhere |
| `biospecimen` | 6 | Assay and catalog records, iPSC guide |
| `dti` | 3 | ROI table and methods |
| `neurobehavioral` | 3 | Mood and behavior instruments |
| `MRI Acquisition` | 2 | Acquisition and MRI metadata |
| `digital_Sensor` | 2 | Roche app table and methods |
| `olfactory` | 2 | Smell testing |
| `sleep disorder` | 2 | Sleep questionnaires |
| `curated_datacuts` | 1 | Three-sheet workbook: `20260810`, `Data dictionary`, `Information` |
| `non motor` | 1 | SCOPA-AUT |

## Availability and documentation checks

The local audit confirms physical files at these paths. It does **not** verify every biological measurement asserted by informal descriptions, nor the location or accessibility of remotely referenced WGS/RNA files, raw image volumes, or continuous sensor streams. Each remote item is formally cataloged in `phase1_external_references_manifest.json` with its documentary source, explicitly marked `"Definition/availability not verified from local repository files"` when remote repositories are not locally provable.

All six readable multi-sheet workbook worksheets are independently audited for dimensions, literal schemas, identifiers, and observation grain. All 177 physical source files possess full ordered schemas cataloged in `phase1_schema_catalog.json` (3,659 columns), and all nonempty tabular sources are verified by full-file observation grain analysis in `phase1_grain_catalog.json`. All candidate files remain classified as `Selection Pending` awaiting the Research Dataset Selection Gate.
