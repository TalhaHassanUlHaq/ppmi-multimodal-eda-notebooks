# Deep CSV EDA Extension for Existing Modality Notebooks

**Status:** Human-requested extension to the approved notebook sprint  
**Implementation owner:** Gemini  
**Supervisor/reviewer:** Codex  
**Deliverable form:** New executed sections inside the existing modality notebooks; no replacement script or standalone report is an acceptable substitute.

## 1. Objective and scope

Extend the current notebooks with deeper, clinically motivated analysis of locally available CSV files that contain useful scientific information. This is **not** authorization to plot every column or analyze every administrative table. Gemini must verify each file's columns, documentation, observation grain, participant/visit coverage, and join cardinality before using it.

The extension must preserve current cohort definitions and approved privacy rules. Any proposed cohort redefinition, consequential exclusion, undocumented recoding, or permanent file reclassification requires renewed human approval.

## 2. Notebook integration standard

Each modality notebook must gain a clearly labeled **Deep Source-File EDA** section before its final interpretation/limitations/conclusions. The section must contain:

1. scientific questions tied to the selected CSVs;
2. a compact table of the CSV paths, dimensions, grain, participant/visit coverage, documentation source, and why each file adds information beyond the curated cut;
3. a source-specific quality audit: exact keys, null keys, duplicates, repeated events, missingness, out-of-range or implausible values, and category/code verification;
4. clinically meaningful descriptive analyses and a limited number of non-repetitive figures;
5. visible sample sizes and denominators for every table and figure;
6. aggregate interpretation that distinguishes observation from inference;
7. source-specific limitations and confounding;
8. an updated skewness table containing **every newly analyzed numeric variable**, at its actual analytical grain, with correct valid/missing denominators;
9. a join-audit table for every cross-file combination.

No participant-level rows, individual scatterplots, exact cells below five, or participant identifiers may be displayed. All displayed figures must be generated from privacy-safe aggregates.

## 3. Priority CSVs and required analyses

### 3.1 `eda_clinical.ipynb`

#### Priority source families

- `MOTOR/MDS-UPDRS_Part_I_09Nov2026.csv`
- `MOTOR/MDS_UPDRS_Part_II__Patient_Questionnaire_09Nov2026.csv`
- `MOTOR/MDS-UPDRS_Part_III_09Nov2026.csv`
- `MOTOR/MDS-UPDRS_Part_IV__Motor_Complications_09Nov2026.csv`
- `MOTOR/Modified_Schwab___England_Activities_of_Daily_Living_09Nov2026.csv`
- `MEDICAL HISTORY/PD_Diagnosis_History_09Nov2026.csv`
- `MEDICAL HISTORY/Clinical_Diagnosis_09Nov2026.csv`
- `MEDICAL HISTORY/Initiation_of_Dopaminergic_Therapy_09Nov2026.csv`
- `MEDICAL HISTORY/LEDD_Concomitant_Medication_Log_09Nov2026.csv`
- `MEDICAL HISTORY/Determination_of_Freezing_and_Falls_09Nov2026.csv`
- `neuropsychological/Montreal_Cognitive_Assessment__MoCA__09Nov2026.csv`
- `neuropsychological/Hopkins_Verbal_Learning_Test_-_Revised_09Nov2026.csv`
- `neuropsychological/Symbol_Digit_Modalities_Test_09Nov2026.csv`
- `neuropsychological/Trail_Making_A_and_B_09Nov2026.csv`
- `neuropsychological/Benton_Judgement_of_Line_Orientation_09Nov2026.csv`
- `neurobehavioral/Geriatric_Depression_Scale__Short_Version__09Nov2026.csv`
- `neurobehavioral/State-Trait_Anxiety_Inventory_for_Adults_09Nov2026.csv`
- `non motor/SCOPA-AUT_09Nov2026.csv`
- `sleep disorder/Epworth_Sleepiness_Scale_09Nov2026.csv`
- `sleep disorder/REM_Sleep_Behavior_Disorder_Screening_Questionnaire_09Nov2026.csv`
- `olfactory/University_of_Pennsylvania_Smell_Identification_Test_UPSIT_09Nov2026.csv`

#### Required depth

- Reconcile raw instrument totals with curated scores where both exist; report agreement, unmatched records, and discrepancies without silently replacing either source.
- Describe baseline distributions, missingness, floor/ceiling effects, and cohort differences for verified total/domain scores.
- Show longitudinal median/IQR trajectories with visit-specific `n`; distinguish repeated-participant trajectories from changing cross-sectional samples.
- Analyze motor/non-motor/cognitive domain correlation using Spearman coefficients with pairwise `n` and explicit exploratory/multiplicity language.
- Describe dopaminergic-therapy initiation and LEDD patterns using verified medication denominators; do not treat missing LEDD as zero.
- Describe falls/freezing and ADL burden using verified codes, with small-cell suppression.
- Do not compute composite scores from items unless the official scoring rule is locally documented and cited.

### 3.2 `eda_biospecimen.ipynb`

#### Priority source families

- `biospecimen/IUSM_BIOSPECIMEN_CELL_CATALOG_09Nov2026.csv`
- `biospecimen/IUSM_CATALOG_09Nov2026.csv`
- `biospecimen/IUSM_ASSAY_DEV_CATALOG_09Nov2026.csv`
- `biospecimen/Whole_Blood_Substudy_09Nov2026.csv`
- `biospecimen/iPSC_Catalog_Metadata_09Nov2026.csv`
- curated-cut biomarker fields already used in the notebook, where the CSV catalogs do not contain assay results.

#### Required depth

- Separate specimen availability/catalog analysis from measured biomarker-value analysis.
- Summarize verified specimen types, collection visits, assay/platform/batch fields, storage or processing metadata, and participant coverage only when documented.
- Report availability by cohort and milestone visit, repeated collections per participant, and missingness by specimen/analyte.
- For measured analytes, add distribution diagnostics, raw/log skewness where appropriate, cohort summaries, pairwise Spearman matrices with pairwise `n`, and sensitivity to documented assay/batch metadata when possible.
- Do not interpret catalog presence as an assay result, and do not combine units or platforms without verified harmonization.

### 3.3 `eda_genetics.ipynb`

#### Priority source families

- `subject_characteristics/iu_genetic_consensus_20251025_09Nov2026.csv`
- `subject_characteristics/Polygenic_Risk_Scores_09Nov2026.csv`
- `subject_characteristics/Genotypes_for_Polygenic_Risk_Scores_09Nov2026.csv`
- `subject_characteristics/PPMI_Project_9001_20250624_09Nov2026.csv`
- `subject_characteristics/PPMI_PD_Variants_Genetic_Status_WGS_20180921.csv`
- `subject_characteristics/Family_History_09Nov2026.csv` when its codes are documented.

#### Required depth

- Describe sequencing/genotyping availability, missingness, and overlap by cohort without treating availability as a biological finding.
- Summarize verified pathogenic/likely pathogenic carrier categories by gene and cohort with cell suppression.
- Analyze PRS distributions, skewness, cohort overlap, and missingness; standardize only if the method and reference population are stated.
- Examine descriptive relationships among consensus carrier status, PRS, family history, and clinical cohort using privacy-safe aggregates.
- Explicitly discuss ancestry portability, enrichment design, relatedness, and ascertainment; do not make deterministic or individual-risk claims.

### 3.4 `eda_neuroimaging.ipynb`

#### Priority source families

- `DATSCAN/Xing_Core_Lab_-_Quant_SBR_09Nov2026.csv`
- `DATSCAN/Xing_Core_Lab_-_Visual_Read_09Nov2026.csv`
- `DATSCAN/Xing_Core_Lab_-_DATSCAN_acquisition_metadata_09Nov2026.csv`
- `MR Analysis Results/FS7_ASEG_VOL_09Nov2026.csv`
- `MR Analysis Results/FS7_APARC_CTH_09Nov2026.csv`
- `MR Analysis Results/FS7_APARC_SA_09Nov2026.csv`
- `MR Analysis Results/MRIQC_09Nov2026.csv`
- `MRI Acquisition/Magnetic_Resonance_Imaging__MRI__09Nov2026.csv`
- `MRI Acquisition/Xing_Core_Lab_-_MRI_acquisition_metadata_09Nov2026.csv`
- `dti/DTI_Regions_of_Interest_09Nov2026.csv`
- `PET/PET_SBR_Analysis_09Nov2026.csv`
- `PET/SV2A_PET_SUVR_Analysis_09Nov2026.csv`
- `PET/TAU_PET_Analysis_09Nov2026.csv`
- locally present rs-fMRI session/QC worksheet already selected for the notebook.

#### Required depth

- Audit scan/session grain, repeat scans, laterality, visit alignment, and participant-to-scan cardinality separately for every modality.
- DaTscan: SBR distributions, side/asymmetry measures, visual-read agreement, acquisition/QC stratification, and longitudinal change only where repeat visits are verified.
- MRI: predeclared clinically relevant regions rather than indiscriminate atlas plotting; report thickness/area/volume separately, and account descriptively for age, sex, ICV, scanner/site, and QC when verified fields exist.
- DTI: verified ROI FA/MD metrics, QC/coverage, cohort distributions, and confounding by protocol/site; do not call ROI measurements tractography.
- rs-fMRI: session coverage, verified motion/QC metrics, acquisition parameters, and exclusions; do not infer connectivity when connectivity matrices are not locally present.
- PET: tracer-specific coverage and distributions; never pool tracers or units; use privacy-safe grouped/binned summaries for cross-measure relationships.
- Every displayed imaging metric must have units, scan `n`, participant `n`, and QC inclusion denominator.

### 3.5 `eda_digital_sensors.ipynb`

#### Priority source

- `digital_Sensor/Roche_PD_Monitoring_App_v2_data_09Nov2026.csv`

#### Required depth

- Audit participant-day-task grain, duplicate records, timestamps, task codes, verified feature meanings/units, and missingness by task.
- Describe records per participant, active days, first-to-last observation span, inter-assessment intervals, and retention across study day.
- Partition within-participant and between-participant variability for verified continuous features using aggregate variance summaries.
- Analyze raw and log-transformed distributions where justified; add both to the skewness table.
- Examine verified laterality/task differences only when documentation supports them.
- Treat the 32-participant study as a feasibility/measurement substudy; do not generalize population prevalence or clinical efficacy.

### 3.6 `eda_multimodal_synthesis.ipynb`

#### Required depth

- Use only validated one-row-per-participant baseline aggregates or explicitly audited repeated-measure summaries.
- Add an aggregate pairwise modality-overlap matrix with counts and percentages.
- Add a missingness/availability profile by cohort and visit without displaying participant rows.
- Expand cross-modal associations only for prespecified clinically meaningful pairs: motor–DaTscan, cognition–biomarkers, SAA–DaTscan, PRS/carrier status–phenotype, and selected imaging–clinical pairs where denominators are adequate.
- Report effect size, valid `n`, missing `n`, and uncertainty where appropriate; apply false-discovery-rate control if multiple inferential p-values are presented, or label the whole analysis descriptive and omit significance claims.
- Compare complete versus incomplete multimodal subsets on measured covariates descriptively; never claim representativeness or absence of selection bias.

## 4. Prohibited low-value expansion

Do not add independent deep EDA for consent logs, pregnancy tests, open-query tables, routine administrative tracking, or the many substudy adverse-event forms unless the human researcher supplies a specific safety question. Do not create one plot per numeric column, automated pairplots, unfiltered correlation walls, or hundreds of atlas-region plots.

## 5. Required automated tests

Gemini must add focused tests that verify:

1. every deep-analysis CSV is explicitly declared and physically present;
2. exact used columns exist and have a verified definition or are visibly labeled unverified;
3. observation grain and key uniqueness are checked before analysis;
4. every merge has a saved join-audit record and no `m:m` path;
5. every displayed table/figure contains valid `n` and denominator information;
6. cells below five and participant-level records cannot reach notebook outputs;
7. the skewness table contains every newly analyzed numeric variable exactly once with correct denominators;
8. saved notebooks execute from clean kernels with zero error cells;
9. source files remain unchanged.

## 6. Acceptance criteria

The extension is acceptable only when:

- analysis depth materially exceeds the current curated-cut overview while remaining clinically focused;
- source-specific results are reproducible and documentation-backed;
- raw and curated results are reconciled rather than silently mixed;
- plots are limited, readable, labeled with units and sample sizes, and interpreted conservatively;
- no restricted records or identifiers are displayed;
- all focused notebook tests pass; and
- Codex independently reviews the executed notebooks and records a final `PASS` or `CHANGES REQUIRED` decision.

## 7. Implementation order for speed

1. Finish the current narrow skewness denominator/test correction.
2. Extend `eda_clinical.ipynb` first because it has the richest useful CSV set.
3. Extend neuroimaging, biospecimen, genetics, and sensors in parallel only if implementation resources permit.
4. Update synthesis after the modality notebooks stabilize.
5. Regenerate only affected notebooks and run focused notebook tests; do not rerun Phase 1 or selection infrastructure unless a source-integrity failure appears.
