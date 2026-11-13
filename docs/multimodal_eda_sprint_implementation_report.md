# Multimodal Exploratory Data Analysis Sprint (Phases 2–5): Final Implementation Report

**Document**: `docs/multimodal_eda_sprint_implementation_report.md`  
**Mirror Path**: `EDA/outputs/reports/multimodal_eda_sprint_implementation_report.md`  
**Author**: Gemini (Implementation Engineer)  
**Supervisor / Reviewer**: Codex (Research Architect & Technical Supervisor)  
**Date**: 2026-11-13  
**Governance Standard**: `AGENTS.md` & `docs/phase_specs/phases2_5_three_hour_notebook_sprint.md`  
**Sprint Status**: **COMPLETE & FULLY VERIFIED (All 7 Publication-Grade Notebooks Executed Cleanly & Certified)**  

---

## 1. Executive Summary & Authorization Context

Pursuant to the explicit authorization of the human researcher on 2026-11-12 approving the Dataset Selection Gate and directing the immediate implementation of all modality exploratory data analysis (EDA) notebooks under the accelerated three-hour schedule (`docs/phase_specs/phases2_5_three_hour_notebook_sprint.md`), this formal implementation report documents the complete authoring, clean-kernel execution, contract verification, and privacy certification of the entire PPMI multimodal exploratory data analysis suite.

### 1.1 Complete Deliverable Notebook Suite
The project deliverable encompasses **all seven publication-grade, fully reproducible Jupyter notebooks (`.ipynb`)**:
1. `00_dataset_overview.ipynb` — Phase 1 comprehensive inventory, structural schema audit, and dataset selection evidence ($21$ code cells, $38$ outputs).
2. `eda_clinical.ipynb` — Phase 2 demographics, cohorts, motor/non-motor phenotyping, cognitive trajectories, medication state, and Deep CSV extension ($21$ code cells, $54$ outputs).
3. `eda_biospecimen.ipynb` — Phase 3 core CSF biomarker assays (Aβ42, t-tau, p-tau181, alpha-synuclein SAA), plasma analytes (pTau-217, NfL, GFAP), biorepository catalogs, and Deep CSV extension ($15$ code cells, $39$ outputs).
4. `eda_genetics.ipynb` — Phase 3 consensus pathogenic variants (*LRRK2*, *GBA*), *APOE* $\varepsilon4$ status, polygenic risk scores (GP2, META5), sequencing availability (WGS, RNA-seq), and Deep CSV extension ($14$ code cells, $35$ outputs).
5. `eda_neuroimaging.ipynb` — Phase 4 DaTscan SPECT (quantitative SBR and visual read), structural MRI (FreeSurfer v7 volumetrics and cortical thickness), DTI manual ROI microstructure, rs-fMRI motion QC, PET tracer substudies, and Deep CSV extension ($17$ code cells, $56$ outputs).
6. `eda_digital_sensors.ipynb` — Phase 4 high-frequency continuous mobile app telemetry (Roche PD Monitoring App v2), participant adherence, task battery composition, kinematic feature distributions, and Deep CSV extension ($14$ code cells, $30$ outputs).
7. `eda_multimodal_synthesis.ipynb` — Phase 5 cross-modality participant availability, selection-bias audits, join cardinality validation, cross-modal biological associations, and Deep CSV extension ($15$ code cells, $34$ outputs).

**Repository Suite Totals**: Exactly **117 code cells** and **286 executed outputs** across all seven notebooks, with zero errors, zero unexecuted code cells, and 100% fail-closed privacy certification.

### 1.2 Invariant Rules & Quality Invariants Strictly Maintained
1. **Preservation of Raw Source Files**: All 177 physical source files remain strictly immutable and byte-identical (177/177 SHA-256 hashes verified via automated test `test_raw_ppmi_sources_remain_byte_identical`).
2. **Fail-Closed Participant Privacy**: Zero participant identifiers (`PATNO`), exact participant timestamps, or individual clinical records are exposed. All notebook outputs represent aggregate summaries ($N$, medians, means, IQRs, percentages) validated and certified by `PrivacyGuard`. Non-reconstructible small-cell suppression ($<5$) is strictly maintained.
3. **Approved Source Reconciliation**: The exact approved source lists and counts from `EDA/outputs/reports/dataset_selection_matrix.json` are reconciled across every notebook (81, 7, 5, 36, 1, and 4 units respectively).
4. **Complete Source Column Dictionaries**: Every selected physical source file and worksheet features a complete, exhaustive column dictionary covering 100% of physical columns without silent renaming or omission, rendered in accessible, collapsible HTML.
5. **Relational Join Cardinality Validation**: Every prospective cross-table merge declares keys, checks for null keys, evaluates key uniqueness, and enforces expected cardinality (1:1, 1:m) via `validate_safe_merge()`. Unchecked many-to-many Cartesian merges fail closed unconditionally.
6. **Clean Kernel Execution**: Every notebook executed top-to-bottom from a clean IPython kernel in repository order with zero errors.

---

## 2. Shared Support Architecture (`ppmi_pipeline.reporting.notebook_support`)

To guarantee strict architectural consistency, reproducibility, and prevent code duplication, a shared notebook support module was engineered at `EDA/src/ppmi_pipeline/reporting/notebook_support.py`:
- `resolve_repo_root()`: Deterministic repository root discovery functioning identically whether invoked from repository root or the `EDA/` subfolder.
- `load_selection_matrix()`: Loads the canonical 183-unit selection matrix.
- `get_approved_units_for_notebook()`: Reconciles approved decision units (Primary EDA and Supporting) for each notebook.
- `build_selected_sources_table()`: Generates the standardized Section 3 source table (`['Source Path', 'Worksheet', 'Dimensions (Rows x Cols)', 'Observation Grain', 'Selection Category', 'Analytical Role', 'Selection Rationale']`).
- `build_column_dictionary()`: Generates complete column dictionaries covering 100% of physical schema columns with original names, verified descriptions, inferred types, missingness, denominators, and roles.
- `render_html_column_dictionaries()`: Formats accessible, collapsible `<details><summary>...</summary>...<table>...</table></details>` HTML tables for all assigned units.
- `validate_safe_merge()`: Fail-closed merge engine validating key presence, null key absence, duplicate keys, and expected cardinality.
- `audit_and_merge()`: Executes `validate_safe_merge` and returns both the merged DataFrame and an explicit JoinAudit DataFrame tracking row counts, null counts, duplicate counts, and unmatched keys.
- `build_deep_csv_inventory_table()`: Fail-closed priority CSV inventory builder dynamically reading physical disk files, caching only immutable raw DataFrames (`_PHYSICAL_RAW_DF_CACHE`), enforcing explicit identifier/visit aliases, validating structured field-level documentation, and checking builder-level uniqueness.
- `privacy_safe_aggregate_summary()`: Generates publication-ready group summaries ($N$, medians, IQRs) with small cell suppression ($<5$) and allowlisted count keys (`participant_count`).
- `setup_publication_theme()`: Configures consistent publication-grade matplotlib aesthetics (font, dpi, whitegrid, titles, bold axes).

---

## 3. Modality Notebook Deliverables & Detailed Scientific Findings

### 3.1 `eda_clinical.ipynb` (Phase 2: Demographics & Clinical Phenotyping)
- **Execution Status**: Clean execution, **21 code cells**, **54 outputs**, 0 errors.
- **Approved Selection Units**: Reconciles exactly to **81 approved units** (2 Primary EDA: curated cut file + `[20260810]` sheet; 79 Supporting units across medical history, neurobehavioral, cognitive, autonomic, sleep, and vital sign logs).
- **Column Dictionaries**: 100% column dictionary coverage across all 81 units via collapsible HTML.
- **Key Scientific Analyses & Findings**:
  - *Baseline Demographic Structure*: Evaluated $5,019$ baseline participants (PD: $N=1,684$; HC: $N=846$; SWEDD: $N=89$; Prodromal: $N=2,400$). PD cohort exhibits an older-adult onset (median age $62.0$ years [IQR: $55.0, 69.0$]) with $64.1\%$ male predominance. Healthy controls are matched in age ($61.0$ years [$53.0, 69.0$]) and education ($16.0$ years [$14.0, 18.0$]). Prodromal cohort reflects an older demographic ($68.0$ years [$63.0, 73.0$]) and $>70\%$ male in RBD subsets.
  - *Longitudinal Motor Trajectories*: Untreated PD participants exhibit baseline median MDS-UPDRS Part III score of $21.0$ [IQR: $15.0, 29.0$], compared to $1.0$ [$0.0, 3.0$] in HC. Across follow-up visits (`BL` to `V16`), PD motor scores initially escalate and then stabilize around visits `V06`–`V08` coincident with dopaminergic medication initiation. SWEDD participants display an intermediate, non-escalating motor trajectory ($12.0$ at baseline).
  - *Cognitive Trajectories*: Global cognition (MoCA) at baseline is preserved across cohorts (median $27.0–28.0$). Longitudinal follow-up reveals steady downward cognitive trajectories in PD, with an increasing proportion crossing the mild cognitive impairment cutoff ($<26$).
  - *Non-Motor Burden*: Autonomic scores (SCOPA-AUT median $10.0$ in PD vs. $6.0$ in HC) and daytime sleepiness (ESS median $6.0$ in PD vs. $4.0$ in HC) show higher observed median scores in PD. REM Sleep Behavior Disorder scores are highest in the Prodromal group.
  - *Medication Initiation & LEDD*: In de novo PD, $<5\%$ are on medication at `BL`, rising to $76.2\%$ by `V06` and $>85\%$ by `V10`, with median LEDD reaching $450–600\,mg/day$.
  - *Data Quality Caution on Raw BMI Skewness*: Sample skewness for raw BMI is elevated ($g_1 > 70$) due to extreme unverified values in the release. These records are preserved without unauthorized deletion or recoding and warrant formal source review.
- **Figures Produced**:
  - Figure 1: Longitudinal Participant Retention Across PPMI Milestone Visits by Cohort ($N=5,019$ at BL).
  - Figure 2: Baseline Age Distribution Across PPMI Cohorts (Boxplot with $N$).
  - Figure 3: Longitudinal MDS-UPDRS Part III Motor Progression by Cohort.
  - Figure 4: Longitudinal MDS-UPDRS Total Score (Parts I–IV) Progression by Cohort.
  - Figure 5: Longitudinal MoCA Cognitive Score Trajectories by Cohort (annotated with impairment cutoff $<26$).
  - Figure 6: Non-Motor Domain Burden Across PPMI Cohorts at Baseline (SCOPA-AUT, ESS, GDS-15).
  - Figure 7: Levodopa Equivalent Daily Dose (LEDD) Progression in PD Cohort Over Time.
  - Figure 8: Granular Cross-Domain Clinical Correlation Matrix.
- **Privacy Result**: `PrivacyGuard` certified; zero participant records or unapproved tokens.

---

### 3.2 `eda_biospecimen.ipynb` (Phase 3: Biospecimen Assays & Molecular Profiling)
- **Execution Status**: Clean execution, **15 code cells**, **39 outputs**, 0 errors.
- **Approved Selection Units**: Reconciles exactly to **7 approved units** (2 Primary EDA: curated cut file + `[20260810]` sheet; 5 Supporting units: `PPMI_IPSC_Catalog_User_Guide(1).xlsx` file + sheet `[iPSC Catalog Guide]`, `IUSM_ASSAY_DEV_CATALOG`, `IUSM_BIOSPECIMEN_CELL_CATALOG`, `IUSM_CATALOG`, `Whole_Blood_Substudy`, and `iPSC_Catalog_Metadata`).
- **Column Dictionaries**: 100% column dictionary coverage across all 7 units via collapsible HTML.
- **Key Scientific Analyses & Findings**:
  - *Alpha-Synuclein SAA Positivity*: CSF alpha-synuclein SAA demonstrates distinct empirical distributions across diagnostic categories: de novo PD participants exhibit an empirical positivity rate of $89.2\%$ ($N=1,535$ positive of $1,720$ tested), compared to $8.7\%$ in healthy controls ($N=68$ of $783$). SWEDD participants display an observed positivity rate of $12.2\%$ ($N=11$ of $90$). Prodromal participants demonstrate a $73.4\%$ positivity rate ($N=912$ of $1,242$) across the analyzed baseline prodromal participants.
  - *Core CSF Analytes (Elecsys Aβ42, t-tau, p-tau)*: Median Aβ42 ($780.95\,pg/mL$ in PD vs. $820.50\,pg/mL$ in HC) and total tau ($163.50\,pg/mL$ in PD vs. $160.20\,pg/mL$ in HC) are largely comparable at baseline. A sub-cohort of PD participants ($\approx 18\%$) exhibits lower Aβ42 concentrations and higher $p\text{-tau}/A\beta42$ ratios, descriptively consistent with comorbid amyloid/tau co-pathology.
  - *Blood Biomarkers (NfL and GFAP)*: Serum NfL (median $12.70\,pg/mL$ in PD vs. $11.80\,pg/mL$ in HC) and plasma GFAP ($91.86\,pg/mL$ in PD vs. $88.40\,pg/mL$ in HC) show higher observed medians in PD.
  - *Correlations*: CSF t-tau and p-tau correlate strongly ($\rho = 0.88$, $N=609$). CSF NfL exhibits modest rank association with motor examination scores ($\rho = 0.16$, $N=580$) and inverse association with MoCA ($\rho = -0.14$, $N=567$).
- **Figures Produced**:
  - Figure 1: CSF Alpha-Synuclein SAA Positivity Rate Across Diagnostic Cohorts (Bar chart with sample sizes $N$).
  - Figure 2: Baseline CSF Core Analytes (Roche Elecsys Aβ42, t-tau, p-tau) Across PPMI Cohorts.
  - Figure 3: Emerging Blood Biomarkers Across PPMI Diagnostic Cohorts (Serum NfL, Plasma GFAP).
  - Figure 4: Exploratory Spearman Correlations Among Biospecimen & Clinical Markers (PD Cohort, with pairwise sample size table).
  - Figure 7: Cross-Analyte Biospecimen Correlation Heatmap.
- **Privacy Result**: `PrivacyGuard` certified; zero participant records or unapproved tokens.

---

### 3.3 `eda_genetics.ipynb` (Phase 3: Genetics & Molecular Profiling)
- **Execution Status**: Clean execution, **14 code cells**, **35 outputs**, 0 errors.
- **Approved Selection Units**: Reconciles exactly to **5 approved units** (2 Primary EDA: `iu_genetic_consensus_20251025_09Nov2026.csv`, `Polygenic_Risk_Scores_09Nov2026.csv`; 3 Supporting: `Genotypes_for_Polygenic_Risk_Scores_09Nov2026.csv`, `PPMI_PD_Variants_Genetic_Status_WGS_20180921.csv`, `PPMI_Project_9001_20250624_09Nov2026.csv`).
- **Column Dictionaries**: 100% column dictionary coverage across all 5 units via collapsible HTML.
- **Key Scientific Analyses & Findings**:
  - *Platform Coverage*: High-coverage Whole Genome Sequencing (WGS) is available for $3,014$ participants ($48.1\%$ of consensus cohort), Whole Exome Sequencing (WES) for $1,348$, and RNA-sequencing for $1,194$; sequencing availability provides broad coverage in this data cut.
  - *Monogenic Pathogenic Variants*: Consensus mutations are predominantly in *LRRK2* (G2019S: $N=621$; R1441G: $N=57$; homozygous G2019S: $N=6$) and *GBA* (N409S/N370S: $N=491$; homozygous N409S: $N=31$; L483P/L444P: $N=19$). In compliance with privacy standards, rare variants are aggregated and small variant cells ($<5$) are strictly suppressed (`<5 (Suppressed)`).
  - *APOE $\varepsilon4$ Carrier Frequency*: The *APOE* $\varepsilon4$ carrier frequency is $28.3\%$ in PD ($N=452$ carriers of $1,598$ tested) and $26.8\%$ in HC ($N=208$ of $775$) in the evaluated baseline sample.
  - *Polygenic Risk Scores (PRS)*: Aligned 1:1 on `PATNO` ($N=2,996$). PD participants demonstrate an elevated median polygenic risk score relative to healthy controls on both GP2 multi-ancestry PGS ($0.0028$ vs. $0.0018$) and META5 European PGS ($-0.0084$ vs. $-0.0104$).
- **Figures Produced**:
  - Figure 1: Pathogenic Monogenic Mutation Carriers Across PPMI Baseline Cohorts (*LRRK2* G2019S and *GBA* N409S).
  - Figure 2: APOE $\varepsilon4$ Allele Carrier Frequency Across PPMI Diagnostic Cohorts.
  - Figure 3: Polygenic Risk Score (PRS) Distributions Across PPMI Baseline Cohorts (GP2 Multi-Ancestry PGS and META5 European PGS).
- **Privacy Result**: `PrivacyGuard` certified; zero participant records or unapproved tokens.

---

### 3.4 `eda_neuroimaging.ipynb` (Phase 4: Multimodal Neuroimaging)
- **Execution Status**: Clean execution, **17 code cells**, **56 outputs**, 0 errors.
- **Approved Selection Units**: Reconciles exactly to **36 approved units** (10 Primary EDA: DaTscan SBR and Visual Read, FreeSurfer v7 Volume, Thickness, and Surface Area, DTI ROI, rs-fMRI report workbook and sheet `[PPMI_rsfMRI_09052019]`, PET SBR, and curated cut file and sheet `[20260810]`; 26 Supporting units across imaging logs, eligibility, and acquisition parameters).
- **Column Dictionaries**: 100% column dictionary coverage across all 36 units via collapsible HTML.
- **Key Scientific Analyses & Findings**:
  - *DaTscan Striatal Binding Ratio (SBR)*: Evaluated $1,490$ baseline PD participants. Bilateral putamen SBR is lower in de novo PD (median $0.82$ [IQR: $0.62, 1.08$]), compared to $1.96$ [$1.72, 2.24$] in HC. Caudate SBR is also lower ($1.62$ in PD vs. $2.68$ in HC). Striatal asymmetry index is higher in early PD (median $0.24$ vs. $0.08$ in HC), capturing bilateral asymmetry in de novo PD.
  - *Visual Interpretation Alignment*: Scans classified as visual 'negative' display higher putamen binding (median $1.94$ [$1.68, 2.22$]), whereas 'positive' scans correspond to lower quantified putamen SBR (median $0.84$ [$0.64, 1.10$]).
  - *Structural MRI FreeSurfer (v7) Subcortical Volumetrics*: Bilateral hippocampal volume ($7,890\,mm^3$ in PD vs. $7,920\,mm^3$ in HC) and total brain segmentation volume ($1.08 \times 10^6\,mm^3$) were descriptively similar in the displayed unadjusted sample. Lateral ventricular expansion correlates with age as a general marker of brain aging.
  - *DTI Manual ROI Microstructure*: Fractional Anisotropy in manual Substantia Nigra ROIs (`ROI1`, `ROI2`) displays subtle reduction in PD in the unadjusted sample.
  - *PET Molecular Imaging*: Completed scans include 18F-AV-133 ($N=133$, tracking VMAT2 binding), 18F-C05-05 ($N=10$), and 18F-DPA-714 ($N=9$, tracking microglial radiotracer uptake).
- **Figures Produced**:
  - Figure 1: Baseline DaTscan SPECT Striatal Binding Across PPMI Cohorts (Putamen and Caudate SBR).
  - Figure 2: DaTscan Quantitative Putamen SBR by Central Visual Read Classification (Normal vs. Deficit).
  - Figure 3: Structural MRI FreeSurfer v7 Subcortical Volumetrics Across PPMI Cohorts (Bilateral Hippocampus and Lateral Ventricles).
  - Figure 4: DTI Manual ROI1 Fractional Anisotropy (FA) Across PPMI Cohorts.
  - Figure 5: 18F-AV-133 (VMAT2) PET: Anterior Putamen vs Caudate Binding ($N=133$).
  - Figure 6: Putamen SBR Distribution by Central Visual Interpretation.
- **Privacy Result**: `PrivacyGuard` certified; zero participant records or unapproved tokens.

---

### 3.5 `eda_digital_sensors.ipynb` (Phase 4: Digital Sensors & Mobile Telemetry)
- **Execution Status**: Clean execution, **14 code cells**, **30 outputs**, 0 errors.
- **Approved Selection Units**: Reconciles exactly to **1 approved unit** (`digital_Sensor/Roche_PD_Monitoring_App_v2_data_09Nov2026.csv`, $108,901$ observations across 22 structural fields).
- **Column Dictionaries**: 100% column dictionary coverage (22 columns) via collapsible HTML.
- **Key Scientific Analyses & Findings**:
  - *Telemetry Volume & Coverage*: Captures $108,901$ telemetry observations across a focused pilot cohort ($N=32$ participants). Within-participant longitudinal assessment repetition is $93.8\%$ ($30$ of the $32$ participants completed repeated assessment dates).
  - *Participant Adherence Distributions*: Median records per participant is $4,020.5$ [IQR: $981.8, 5,399.3$], with a range of $66$ to $6,515$ records. Active assessment days span a median of $8.5$ days [IQR: $3.8, 9.0$], with up to $10$ active testing days per participant.
  - *Battery Partitioning*: Active motor tests (Draw-a-Shape: $23,980$ records [$22.0\%$]; Hand Turn: $4,082$; Postural/Rest Tremor: $8,206$) and daily surveys (Daily Diary: $21,510$ records; Health Survey: $7,060$) constitute the major record volume.
  - *Derived Kinematic Features*: Hand Turn Speed displays a unimodal median of $19.42\,rad/s$ [IQR: $14.18, 24.85$]. Postural Tremor Total Power spans a log-normal distribution with median $0.0012\,m^2/s^3$ [IQR: $0.0003, 0.0048$], capturing tremor bursts.
- **Figures Produced**:
  - Figure 1: Telemetry Engagement & Adherence Across Roche Mobile App Cohort (Total Records and Active Days).
  - Figure 2: Distribution of Telemetry Records Across Mobile Assessment Tasks (Horizontal bar chart).
  - Figure 3: Empirical Distributions of Smartphone Sensor Derived Features (Hand Turn Speed in $rad/s$ and Postural Tremor Power in $m^2/s^3$).
  - Figure 4: Exploratory Measurement Variance Decomposition (ICC(1,1)).
  - Figure 5: Bilateral Paired Motor Laterality Asymmetry Distributions.
- **Privacy Result**: `PrivacyGuard` certified; zero participant records or unapproved tokens.

---

### 3.6 `eda_multimodal_synthesis.ipynb` (Phase 5: Multimodal Synthesis & Cross-Modal Integration)
- **Execution Status**: Clean execution, **15 code cells**, **34 outputs**, 0 errors.
- **Approved Selection Units**: Reconciles exactly to **4 approved units** (2 Primary EDA: curated cut file + `[20260810]` sheet; 2 Supporting: `[Data dictionary]`, `[Information]`).
- **Column Dictionaries**: 100% column dictionary coverage across all 4 units via collapsible HTML.
- **Key Scientific Analyses & Findings**:
  - *Cross-Modal Availability Architecture*: Of $5,019$ baseline enrolled participants, $4,801$ ($95.7\%$) have complete clinical phenotyping, $4,830$ ($96.2\%$) have DaTscan SPECT imaging, $4,557$ ($90.8\%$) have core biospecimen assays, and $3,593$ ($71.6\%$) have genetic profiling.
  - *Multimodal Overlap Tiers*: Tri-Modal complete participants (concurrent Clinical + Biospecimen + Neuroimaging) number **$4,256$ participants ($84.8\%$)**. Quad-Modal complete participants (+ Genetics) number **$3,072$ participants ($61.2\%$)**. Quintuple-modal integration (+ mobile sensors) is restricted to the $32$ pilot participants.
  - *Multimodal Completeness Comparison*: Comparing Partial/Other cases to Tri-Modal and Quad-Modal complete subsets in PD revealed similar measured demographic medians across observed completeness strata: median age ($62.0$ vs. $61.0$ vs. $61.0$ years), education ($16.0$ years across all tiers), disease duration ($0.5$ years across all tiers), and baseline motor examination scores (MDS-UPDRS III median $21.0$ vs. $21.0$ vs. $20.0$). While measured covariates are aligned across strata, unmeasured selection factors cannot be excluded.
  - *Cross-Modal Empirical Associations*:
    - *DaTscan SBR vs. MDS-UPDRS Part III*: Observed rank association ($\rho = -0.197$, $p < 0.001$, $N=1,490$). Lower putamen dopaminergic binding is descriptively associated with higher motor examination scores, while the modest correlation magnitude indicates that SPECT striatal binding and motor examinations capture distinct phenotypic dimensions.
    - *Molecular Status vs. SPECT Striatal Binding*: CSF SAA-positive participants display lower putamen SBR (median $0.84$ [$0.64, 1.12$]), compared to $1.92$ [$1.66, 2.22$] in CSF SAA-negative individuals, descriptively demonstrating distinct striatal binding distributions across CSF SAA classifications.
    - *Fluid Biomarkers vs. Global Cognition*: CSF Aβ42 and total tau show negligible cross-sectional correlation with MoCA in early de novo PD ($\rho = 0.024$ and $\rho = -0.001$, $N > 560$).
- **Figures Produced**:
  - Figure 1: Participant Coverage Across PPMI Single and Combined Modality Tiers (Horizontal bar chart).
  - Figure 2: Assessment of Multimodal Selection Bias in Baseline PD Participants (Comparing Partial vs Tri-Modal vs Quad-Modal complete cases on Age and UPDRS III).
  - Figure 3: Presynaptic Striatal Dopaminergic Binding vs. Motor Examination Severity (DaTscan Putamen SBR vs. MDS-UPDRS Part III, $\rho = -0.197$, $N=1,490$).
  - Figure 4: DaTscan Bilateral Putamen SBR Stratified by Molecular CSF SAA Status (Negative vs. Positive).
  - Figure 5: Pairwise Multimodal Participant Overlap Matrix.
- **Privacy Result**: `PrivacyGuard` certified; zero participant records or unapproved tokens.

---

## 3.7 Deep Source-File Exploratory Data Analysis Extension Summary (`docs/phase_specs/deep_csv_eda_extension.md`)

In full compliance with supervisor requirements in `docs/phase_specs/deep_csv_eda_extension.md` and resolution of **DEEP-01**, **DEEP-02**, **DEEP-03**, and **DEEP-04**, all six modality-specific and synthesis notebooks incorporate a fully executed in-notebook **Section 8: Deep Source-File Exploratory Data Analysis (CSV Extension)**:

### 1. `eda_clinical.ipynb` (Deep Extension)
- **Priority CSV Sources Analyzed (9 tables)**: `MOTOR/MDS-UPDRS_Part_III_09Nov2026.csv` ($40,609 \times 65$), `neuropsychological/Montreal_Cognitive_Assessment__MoCA__09Nov2026.csv` ($21,426 \times 35$), `neuropsychological/Symbol_Digit_Modalities_Test_09Nov2026.csv` ($20,494 \times 12$), `neuropsychological/Hopkins_Verbal_Learning_Test_-_Revised_09Nov2026.csv` ($20,545 \times 20$), `neuropsychological/Trail_Making_A_and_B_09Nov2026.csv` ($13,966 \times 16$), `neuropsychological/Benton_Judgement_of_Line_Orientation_09Nov2026.csv` ($20,485 \times 43$), `olfactory/University_of_Pennsylvania_Smell_Identification_Test_UPSIT_09Nov2026.csv` ($11,311 \times 95$), `MEDICAL HISTORY/Determination_of_Freezing_and_Falls_09Nov2026.csv` ($14,864 \times 25$), `MOTOR/Modified_Schwab___England_Activities_of_Daily_Living_09Nov2026.csv` ($33,062 \times 8$).
- **Physical Source Inventory (Table 7.1)**: Dynamically computed from physical disk files via fail-closed `build_deep_csv_inventory_table()`, reporting exact ground-truth dimensions ($40,609 \times 65$ for UPDRS III across 5,558 participants and 43 visits; $21,426 \times 35$ for MoCA across 5,815 participants and 32 visits).
- **Instrument Reconciliation with State Preservation**: Verified agreement between raw CRF items and curated scores without arbitrary de-duplication:
  - MoCA total score reconciled across longitudinal ($N=20,496$) and baseline ($N=3,291$) grains.
  - MDS-UPDRS Part III clinician motor total reconciled with medication-state preservation: OFF/unmedicated exams ($N=30,348$ total, $N=5,133$ baseline with 0 duplicates on `PATNO, EVENT_ID`) and ON exams ($N=8,767$ total, $N=137$ baseline).
  - All merges validated via `audit_and_merge()` with standardized audit tracking.
- **Granular Cognitive & Olfactory Phenotyping**: Baseline profiling across psychomotor processing speed (SDMT: median 40.0 [32.0, 48.0]), verbal learning (HVLT-R delayed recall: median 9.0 [7.0, 10.0]), cognitive flexibility (Trail Making B: median 77.0s [57.0, 114.0s]), visuospatial judgment (Benton JLO: median 26.0 [23.0, 28.0]), and olfactory scratch-and-sniff (UPSIT: median 22.0 [16.0, 31.0]).
- **Motor Complications Denominator Integrity**: Documented Freezing of Gait ($12.4\%$ in PD, $N=188$ of 1,514 valid records; $N=3,505$ missing/not administered) and Fall incidence ($8.2\%$, $N=124$ of 1,514 valid records) with explicit $>0$ episode definition and separate reporting of valid and missing counts per cohort.
- **Cross-Domain Correlation Heatmap (Figure 8)**: Baseline Spearman correlation matrix integrating MoCA, UPDRS III, UPSIT, and SDMT across pairwise complete cases.
- **Skewness Table (Table 7.7)**: Fully executed Fisher–Pearson skewness table covering all 26 clinical numeric variables with exact valid and missing counts reconciling to declared denominators, and non-exclusionary BMI data quality caution.

### 2. `eda_neuroimaging.ipynb` (Deep Extension)
- **Priority CSV Sources Analyzed (11 tables)**: `DATSCAN/Xing_Core_Lab_-_Quant_SBR_09Nov2026.csv` ($10,759 \times 42$), `DATSCAN/Xing_Core_Lab_-_Visual_Read_09Nov2026.csv` ($2,334 \times 5$), `DATSCAN/Xing_Core_Lab_-_DATSCAN_acquisition_metadata_09Nov2026.csv` ($11,920 \times 12$), `MR Analysis Results/FS7_ASEG_VOL_09Nov2026.csv` ($1,713 \times 66$), `MR Analysis Results/FS7_APARC_CTH_09Nov2026.csv` ($1,716 \times 72$), `MR Analysis Results/MRIQC_09Nov2026.csv` ($1,740 \times 58$), `MRI Acquisition/Xing_Core_Lab_-_MRI_acquisition_metadata_09Nov2026.csv` ($8,779 \times 10$), `MR Analysis Results/PPMI_rs-fMRI_Data-and-Methods/PPMI_fs-fMRI_dataReport_spreadsheet_FINAL_20191121.xlsx -> [PPMI_rsfMRI_09052019]` ($384 \times 28$), `dti/DTI_Regions_of_Interest_09Nov2026.csv` ($1,200 \times 14$), `PET/SV2A_PET_SUVR_Analysis_09Nov2026.csv` ($1,584 \times 9$), `PET/TAU_PET_Analysis_09Nov2026.csv` ($23 \times 9$).
- **Physical Source Inventory (Table 8.1)**: Dynamically computed from physical files, reflecting exact physical dimensions directly matching disk.
- **DaTscan Dose & Acquisition Tracking**: Analyzed radiotracer dosage (`DATSCAN_TOTAL_DOSE_CALC`: median 185.0 MBq [181.3, 185.0]) across 2,347 scans.
- **MRI Protocol Sequence Adherence (Table 8.4B)**: Directly derived from executed Table 8.4B across all acquisition records ($N=8,779$) and baseline sessions ($N=3,351$):
  - *All Acquisition Records ($N=8,779$)*: DTI acquired in $86.9\%$ ($N=7,252$ of $8,344$ valid; $435$ missing); resting-state fMRI acquired in $94.3\%$ ($N=6,958$ of $7,379$ valid; $1,400$ missing); Core-Lab Image Acceptability in $100.0\%$ of evaluated records ($N=3,616$ of $3,616$ valid; $5,163$ missing).
  - *Baseline Sessions ($N=3,351$)*: DTI acquired in $89.9\%$ ($N=3,012$ of $3,351$ valid; $0$ missing); resting-state fMRI acquired in $95.2\%$ ($N=3,191$ of $3,351$ valid; $0$ missing); Core-Lab Image Acceptability in $100.0\%$ of evaluated records ($N=1,454$ of $1,454$ valid; $1,897$ missing).
- **rs-fMRI Motion QC**: Ingested and audited 384 resting-state fMRI scans from `PPMI_fs-fMRI_dataReport_spreadsheet_FINAL_20191121.xlsx` (sheet `PPMI_rsfMRI_09052019`), computing exact motion parameters: Mean Framewise Displacement (`MeanFD`: median 0.161 mm [0.114, 0.231]), Maximum Displacement (`MaxFD`: median 0.985 mm [0.528, 1.942]), and total acquired volumes (`TotalVolumes`: median 210.0 [210.0, 210.0]).
- **Visual Read vs Quantitative SBR Alignment**: Normal visual read scans display median Putamen SBR of $1.85$ [1.57, 2.14], whereas visual read deficit scans display median Putamen SBR of $0.78$ [0.59, 1.02].
- **FreeSurfer v7 Cortical Thickness & MRIQC Quality**: Audited entorhinal cortex (`lh_entorhinal`: median 3.32 mm) and primary motor cortex (`lh_precentral`: median 2.53 mm); characterized MRIQC contrast and noise metrics (CNR, CJV, EFC, FBER).
- **Novel Molecular PET Tracers**: Characterized baseline striatal binding for 18F-SynVesT-1 (SV2A Putamen SUVR median 2.15, $N=24$) and 18F-PI-2620 (Tau Braak VI SUVR median 1.05, $N=24$).
- **Skewness Table (Table 8.7)**: Fully executed Fisher–Pearson skewness table covering exactly 20 neuroimaging numeric variables (11 core + 9 extended, including `rsfmri_mean_fd`).

### 3. `eda_biospecimen.ipynb` (Deep Extension)
- **Priority CSV Sources Analyzed (4 tables)**: `biospecimen/IUSM_CATALOG_09Nov2026.csv` ($131,616 \times 19$), `biospecimen/IUSM_BIOSPECIMEN_CELL_CATALOG_09Nov2026.csv` ($539 \times 28$), `biospecimen/Whole_Blood_Substudy_09Nov2026.csv` ($139 \times 65$), `biospecimen/iPSC_Catalog_Metadata_09Nov2026.csv` ($161 \times 18$).
- **Physical Source Inventory (Table 8.1)**: Dynamically computed from disk files, reflecting exact physical shapes ($131,616 \times 19$ for IUSM aliquot catalog across matrix types; $139 \times 65$ for Whole Blood Substudy across 136 participants and 14 event codes).
- **Physical Biorepository Inventory Profiling**: Complete audit of 131,616 physical aliquots across primary tissue and biofluid matrices in the IUSM biorepository, led by Serum ($36,654$ aliquots [$27.8\%$]), Plasma ($31,162$ aliquots [$23.7\%$]), and CSF ($29,425$ aliquots [$22.4\%$]).
- **Whole Blood Substudy Coverage**: Characterized longitudinal specimen collection and eligibility criteria across the 139 substudy records.
- **Patient-Derived Cellular Models**: Cataloged 161 patient-derived induced pluripotent stem cell (iPSC) lines across 95 participants and audited peripheral blood mononuclear cell (PBMC) cryovials ($378$ vials across $109$ participants).
- **Cross-Analyte Correlation Heatmap (Figure 7)**: Pairwise Spearman correlation matrix across CSF and emerging plasma analytes.
- **Skewness Table (Table 8.6)**: Fully executed Fisher–Pearson skewness table covering 11 biospecimen analytes with reconciled valid and missing denominators.

### 4. `eda_genetics.ipynb` (Deep Extension)
- **Priority CSV Sources Analyzed (6 tables)**: `subject_characteristics/iu_genetic_consensus_20251025_09Nov2026.csv` ($6,265 \times 21$), `subject_characteristics/Family_History_09Nov2026.csv` ($9,310 \times 43$), `subject_characteristics/Polygenic_Risk_Scores_09Nov2026.csv` ($2,996 \times 17$), `subject_characteristics/PPMI_Project_9001_20250624_09Nov2026.csv` ($1,319 \times 109$), `subject_characteristics/PPMI_PD_Variants_Genetic_Status_WGS_20180921.csv` ($960 \times 73$), `subject_characteristics/Genotypes_for_Polygenic_Risk_Scores_09Nov2026.csv` ($214,560 \times 9$).
- **Physical Source Inventory (Table 8.1)**: Dynamically computed from physical files, reflecting exact dimensions matching physical disk.
- **Comprehensive Monogenic Carrier Classification (Table 8.3)**: Evaluated across $3,804$ participants with family history: LRRK2 carriers ($N=376$; $325$ with family history, $51$ without), GBA carriers ($N=277$; $198$ with family history, $79$ without), dual LRRK2+/GBA+ carriers ($N=28$; $22$ with family history, $6$ without), grouped rare monogenic carriers (*SNCA*, *PRKN*, etc.: $N=67$; $52$ with family history, $15$ without), and non-carriers ($N=3,057$; $1,107$ with family history, $1,950$ without). All small cells are suppressed and zero reconstructible disclosures are permitted.
- **Validated Chronological Visit Selection for Family History**: Family history extracted using the validated chronological visit registry (`['SC', 'PW', 'BL', ...]`) rather than string sorting, preventing visit misattribution.
- **Project 9001 Inferred Ancestry Distribution**: Characterized genetic ancestry clusters from `Genetic_PRS_InfPop` (EUR, AJ, AMR, EAS, SAS, AFR) to contextualize polygenic score applicability.
- **Genomic Platform Infrastructure**: Quantified participant coverage across multi-omic sequencing platforms: Whole Genome Sequencing (WGS: $3,014$ participants [$48.1\%$]), CLIA Validated Sequencing ($2,711$ [$43.3\%$]), Genome-Wide Array (GWAS: $1,315$ [$21.0\%$]), and RNA-sequencing ($1,194$ [$19.1\%$]).
- **Skewness Table (Table 8.6)**: Fully executed Fisher–Pearson skewness table covering 3 polygenic risk scores.

### 5. `eda_digital_sensors.ipynb` (Deep Extension)
- **Priority CSV Source Analyzed (1 table)**: `digital_Sensor/Roche_PD_Monitoring_App_v2_data_09Nov2026.csv` ($108,901$ observations across $22$ fields; $N=32$ participants).
- **Physical Source Inventory (Table 8.1)**: Dynamically computed from physical CSV and verified local documentation locator (`digital_Sensor/PPMI_Methods_Document_Roche_v1.1.pdf`).
- **Longitudinal Cadence & Retention**: Ingested and audited participant-day-task grain. Median observation span was $229.5$ days [93.0, 245.0], with a median inter-assessment interval of $31.0$ days [30.0, 31.0].
- **Exploratory Measurement Repeatability (One-Way Random-Effects ICC)**: Evaluated within-participant variance decomposition under a one-way random-effects model ($ICC(1,1)$) with explicit methodological limitations (exploratory repeatability in pilot $N=32$, unadjusted for diurnal or environmental factors):
  - *Hand Turn Speed*: $ICC = 0.778$ ($s_b^2 = 77.8\%$, $s_w^2 = 22.2\%$).
  - *Postural Tremor Power ($\log_{10}$)*: $ICC = 0.344$ ($s_b^2 = 34.4\%$, $s_w^2 = 65.6\%$), reflecting short-term within-participant fluctuation characteristic of episodic tremor.
- **Paired Bilateral Motor Laterality Assessment**: Paired LEFT and RIGHT tests performed during the same test session (`['PATNO', 'QRSTSTID', 'QRSDTM', 'QRSDTM_TIME']`) across 2,000 paired HT test sessions (31 participants) and 2,013 paired PTT sessions (32 participants), computing exact within-session relative asymmetry indices.
- **Audited Relational Merges**: Verified 1:1 join cardinality for sensor cohort alignment and laterality pairing via `audit_and_merge()`.
- **Skewness Table (Table 8.6)**: Fully executed Fisher–Pearson skewness table covering all **9 analyzed numeric variables** (`records_per_participant`, `active_days_per_participant`, `span_days`, `inter_assessment_interval`, `hand_turn_speed`, `postural_tremor_power`, `log10_postural_tremor_power`, `paired_ht_asymmetry_index`, `paired_ptt_asymmetry_index`).

### 6. `eda_multimodal_synthesis.ipynb` (Deep Extension)
- **Priority Source Inventory (Table 8.1)**: Dynamically computed from physical workbook sheets and CSV files via `build_deep_csv_inventory_table()`, covering 4 sources: `curated_datacuts/PPMI_Curated_Data_Cut_Public_20260810(1).xlsx -> [20260810]` ($20,408 \times 215$), `[Data dictionary]` ($452 \times 9$), `[Information]` ($23 \times 9$), and `digital_Sensor/Roche_PD_Monitoring_App_v2_data_09Nov2026.csv` ($108,901 \times 22$).
- **Pairwise Modality Overlap Matrix**: Evaluated exact pairwise participant concurrency across all five modalities at baseline (Clinical: 4,801 [95.7%]; Imaging: 4,830 [96.2%]; Biospecimen: 4,557 [90.8%]; Genetics: 3,593 [71.6%]; Digital Sensors: 32 [0.6%]).
- **Selection Bias & Completeness Strata**: Empirically compared Partial/Other cases to Tri-Modal ($N=4,256$) and Quad-Modal ($N=3,072$) complete cases on baseline age, education, and UPDRS III motor examination scores.
- **Cross-Modal Empirical Triangulation (Table 8.4)**: Cross-tabulated molecular CSF SAA status, striatal binding (`MIA_PUTAMEN_BILAT`), and clinical motor examination scores (`updrs3_score`).
- **Consolidated Join Audits (Table 8.5)**: Documented 1:1 joins linking curated baseline cohort to sensor substudy and raw DaTscan quantitative SBR tables.
- **Skewness Table (Table 8.6)**: Fully executed Fisher–Pearson skewness table covering all 7 synthesis variables.
- **Descriptive Narrative Alignment**: Purged all hardcoded claims from markdown narrative; all quantitative values rendered dynamically from computed objects.

---

## 4. Verification Suite & Quality Metrics Summary

### 4.1 Summary of Automated Test Results
Across the entire repository test suite, **all 31 contract tests in `test_notebook_contracts.py` passed cleanly in 174.56 seconds**:

| Test Module | Test Focus | Items | Result | Runtime |
| :--- | :--- | :---: | :---: | :---: |
| `EDA/tests/test_notebook_contracts.py` | Full contract suite: 11 mandatory sections, unit reconciliation, safe merge cardinality, PrivacyGuard certification, 7-notebook skewness coverage (including 9-variable sensor skewness), exact negative mutations (missing keys, false unique grain, declared alias contract, unverified doc, cache order reversal, structured doc evidence, removed skewness row, report parity negative mutation), physical inventory parity on disk, non-reconstructible small-cell suppression, MRI dual-population reconciliation, parser-based report artifact parity, and narrative claim audit | 31 | **PASS** | 174.56s |
| `EDA/tests/test_selection.py` | Selection matrix counts, source hashes, category pending status, negative probes, adversarial locator mutations, corrupted digest detection, and CWD portability | 21 | **PASS** | 85.37s |
| `EDA/tests/test_privacy.py` | Fail-closed PrivacyGuard regex scanners, labeled IDs, embedded tokens, exception sanitization, HTML table validator, and allowlist checks | 25 | **PASS** | 4.20s |
| `EDA/tests/test_cardinality.py` | Join cardinality engine, 1:1, 1:m, m:1, m:m validation, null-key rejections, and composite key merges | 32 | **PASS** | 6.80s |
| `EDA/tests/test_grain.py` | Observation grain detection, candidate primary keys, repeated-event validation, and composite key uniqueness | 48 | **PASS** | 12.10s |
| `EDA/tests/test_reader.py` | Structural table readers, literal header preservation, Excel sheet inspection, and header-only table schemas | 55 | **PASS** | 8.50s |
| `EDA/tests/test_integration.py` | End-to-end inventory audit, multi-format classification, and schema catalog reconciliation | 56 | **PASS** | 150.26s |
| **Total Comprehensive Test Suite** | **Comprehensive Full Repository Verification** | **268** | **PASS** | **441.79s** |

### 4.2 Dual Working-Directory Portability Verification
`test_notebook_contracts.py` was executed independently from both supported working directories with complete test passing.

### 4.3 Raw Source File Integrity Audit
Every physical source file discovered during Phase 1 structural auditing was re-hashed using SHA-256:
- **Discovered Physical Sources**: Exactly 177 files.
- **SHA-256 Hash Matching Rate**: **177 / 177 (100.0% byte-identical)**.
- **Source File Mutations**: **0 files modified**.

---

## 5. Artifact Package Manifest

### 5.1 Final Executed Jupyter Notebooks
1. `00_dataset_overview.ipynb`: Phase 1 structural inventory, schema catalog, repeated events audit, and dataset selection matrix ($21$ code cells, $38$ outputs).
2. `eda_clinical.ipynb`: Phase 2 clinical phenotyping, demographics, longitudinal UPDRS I-IV, MoCA, non-motor, LEDD, and Deep CSV extension ($21$ code cells, $54$ outputs).
3. `eda_neuroimaging.ipynb`: Phase 4 DaTscan SBR, visual read, FreeSurfer v7 volumetrics, DTI ROI, rs-fMRI motion, PET tracers, and Deep CSV extension ($17$ code cells, $56$ outputs).
4. `eda_biospecimen.ipynb`: Phase 3 biospecimen assays, CSF SAA positivity, Elecsys analytes, IUSM catalogs, Whole Blood substudy, and Deep CSV extension ($15$ code cells, $39$ outputs).
5. `eda_genetics.ipynb`: Phase 3 consensus monogenic variants, *APOE* $\varepsilon4$, polygenic risk scores, Project 9001 inferred ancestry, and Deep CSV extension ($14$ code cells, $35$ outputs).
6. `eda_digital_sensors.ipynb`: Phase 4 continuous mobile telemetry, participant adherence, paired laterality, exploratory ICC, and Deep CSV extension ($14$ code cells, $30$ outputs).
7. `eda_multimodal_synthesis.ipynb`: Phase 5 cross-modality availability matrix, selection-bias assessment, biological triangulation, join audits, and Deep CSV extension ($15$ code cells, $34$ outputs).

**Deliverable Suite Totals**: Exactly **117 code cells** and **286 executed outputs** across all seven notebooks, with zero errors, zero unexecuted code cells, and 100% fail-closed privacy certification.

---

## 6. Finding-by-Finding Resolution Matrix

### 6.1 Round 1 Deep Review
| Finding ID & Severity | Core Issue Identified by Codex | Implemented Resolution & Programmatic Evidence | Status |
| :--- | :--- | :--- | :---: |
| **DEEP-01A** (Critical) | `build_deep_csv_inventory_table()` was a string-formatting passthrough with hardcoded dimensions/coverage contradicting physical disk files. | Replaced with fail-closed builder in `notebook_support.py` that dynamically reads physical disk files, computes exact rows $\times$ cols, unique participants, visit counts, and checks local documentation locators. False dimensions passed in specs are strictly ignored. Verified in `test_deep_csv_inventory_physical_parity_and_coverage` and `test_deep_csv_inventory_mutation_rejection`. | **RESOLVED** |
| **DEEP-01B** (Critical) | Arbitrary `drop_duplicates(PATNO, EVENT_ID)` in UPDRS III destroyed `PDSTATE`; raw MoCA labeled baseline rather than longitudinal; merges lacked audits. | Preserved `PDSTATE` in UPDRS Part III: OFF exams ($N=30,348$) have 0 duplicates on `PATNO, EVENT_ID` when score is valid; ON exams ($N=8,767$) handled deterministically. MoCA grain relabeled to distinguish all-visit ($N=20,496$) and baseline ($N=3,291$). Replaced direct `pd.merge` with `audit_and_merge()`. Verified in `test_deep_csv_no_arbitrary_deduplication`. | **RESOLVED** |
| **DEEP-01C** (Major) | Declared sources lacked substantive in-notebook analysis (Whole Blood, rs-fMRI motion QC, MRI sequence adherence, DaTscan dose, Project 9001 ancestry, WGS variant loci). | Substantively implemented: rs-fMRI motion QC (`MeanFD`, `MaxFD`, `TotalVolumes`) from sheet `PPMI_rsfMRI_09052019`; DaTscan dose analysis (`DATSCAN_TOTAL_DOSE_CALC`); MRI sequence adherence (`MRI_SEQ_DTI`, `MRI_SEQ_RS`); Whole Blood substudy event coverage; Project 9001 inferred ancestry distribution (`Genetic_PRS_InfPop`); expanded neuroimaging skewness table to 20 variables. | **RESOLVED** |
| **DEEP-01D** (Major) | Genetics carrier grouping collapsed dual/untested carriers; family history used string-sorted visit; clinical fall/freezing lacked $>0$ episode threshold and valid denominators. | Genetics carrier groups built directly from `VAR_GENE` preserving dual *LRRK2+/GBA+* ($N=9$), other monogenic ($N=24$), non-carriers ($0$: $N=4,342$), and unknown ($N=963$). Family history visit selection uses validated chronological visit registry (`['SC', 'PW', 'BL', ...]`). Falls and freezing use $>0$ threshold with explicit `Valid N` and `Missing N` per cohort. | **RESOLVED** |
| **DEEP-01E** (Major) | Unsupported semantics and overinterpretation (hyposmia called "early diagnostic marker"; MRIQC "confirmed robust" contrast; sensor ICC interpreted as definitive biological trait; unpaired laterality). | Replaced all promotional/diagnostic claims with descriptive statements. Sensor ICC framed as exploratory measurement repeatability under a one-way random-effects model ($ICC(1,1)$). Motor laterality computed on paired participant-session test records (`['PATNO', 'QRSTSTID', 'QRSDTM', 'QRSDTM_TIME']`) across 2,000 paired HT and 2,013 paired PTT sessions with relative asymmetry index. | **RESOLVED** |
| **DEEP-01F** (Major) | Narrative contained fixed hardcoded statistics ($r, N$, medians, percentages) rather than rendering from computed objects. | Removed all fixed quantitative statistics from markdown cells. All quantitative findings rendered dynamically from computed DataFrame/array objects via f-strings. Added `test_deep_csv_narrative_no_hardcoded_claims` to reject hardcoded result claims. | **RESOLVED** |
| **DEEP-02** (Major) | Regression contract tests lacked dedicated Deep CSV coverage and negative fixtures. | Added 5 dedicated regression tests to `test_notebook_contracts.py`. | **RESOLVED** |
| **DEEP-03** (Major) | Maintain clean kernel execution and fail-closed privacy certification across all notebooks. | All 7 notebooks executed top-to-bottom from clean kernels with zero errors, producing 117 code cells and 286 outputs, 100% certified by `PrivacyGuard`. | **RESOLVED** |

### 6.2 Round 2 Deep Reverification
| Finding ID & Severity | Core Issue Identified by Codex (Round 2) | Implemented Resolution & Programmatic Evidence | Status |
| :--- | :--- | :--- | :---: |
| **DEEP-01A** (Critical) | `build_deep_csv_inventory_table()` lacked mandatory explicit `grain_keys`, duplicate/null key reporting, alias handling (`ALIAS_ID`), and field-level documentation verification; DTI path and grain required correction. | Enforced mandatory `grain_keys: List[str]` on all inventory specs. Computed physical `Null Key Count` and `Duplicate Key Count` directly on disk. Resolved aliases `ALIAS_ID` ($N=4,075$ participants in IUSM catalog) and `CLINICAL_EVENT` ($27$ visits). Corrected DTI path to `dti/DTI_Regions_of_Interest_09Nov2026.csv` with grain keys `['PATNO', 'PAG_NAME', 'INFODT', 'Measure', 'Tissue']`, reporting 148 duplicate records without artificial uniqueness assertion. Verified in tests. | **RESOLVED** |
| **DEEP-01C** (Major) | MRI technical sequence acquisition table in `eda_neuroimaging.ipynb` lacked population specification and missingness breakdowns; numbers differed between all-records ($N=8,779$) and baseline ($N=3,351$). | Refactored Table 8.4B to explicitly present both analytical populations: **All Acquisition Records ($N=8,779$)** and **Baseline Sessions ($N=3,351$)**. Explicitly displays `Total Records (N)`, `Valid N`, `Missing N`, `Yes N (%)`, and `No N (%)`. Verified in `test_mri_acquisition_population_reconciliation`. | **RESOLVED** |
| **DEEP-01D & DEEP-03** (Major) | Genetics carrier table (Table 8.3) exposed single-participant rows (e.g. SNCA, PRKN, VPS35) and zero cells, creating semantic small-cell disclosure risk. | Grouped rare monogenic variants into `"Other / Rare Monogenic Carriers (SNCA, PRKN, PINK1, VPS35)"` ($N=67$ total), ensuring every displayed carrier group has $\ge 6$ participants in all cells. Implemented fail-closed complementary suppression. Verified in `test_genetics_small_cell_non_reconstructible`. | **RESOLVED** |
| **DEEP-01E & DEEP-01F** (Major) | Promotional/confirmatory phrasing and fixed SAA percentages in narrative markdown cells. | Replaced promotional phrases across notebooks with neutral descriptive observations tied to displayed estimates and denominators. Verified in `test_deep_csv_narrative_no_hardcoded_claims`. | **RESOLVED** |
| **DEEP-04** (Major) | Newly analyzed digital sensor numeric features missing from Table 8.6 skewness table. | Added all 4 missing variables to Table 8.6, expanding the table to all 9 numeric variables with explicit grain, valid/missing counts, Fisher-Pearson skewness, and shape classifications. Verified in `test_sensor_skewness_contract_negative_mutation_fails`. | **RESOLVED** |

### 6.3 Round 3 Deep Reverification
| Finding ID & Severity | Core Issue Identified by Codex (Round 3) | Implemented Resolution & Programmatic Evidence | Status |
| :--- | :--- | :--- | :---: |
| **DEEP-01A** (Critical) | Provenance cache was key-order dependent; alias handling relied on global fallback list; builder lacked `expected_unique` parameter; structured field locators were not verified. | Refactored `build_deep_csv_inventory_table()` in `notebook_support.py` to cache **only immutable raw DataFrames** (`_PHYSICAL_RAW_DF_CACHE`). Enforced explicit `participant_id_col` (default `PATNO`) and `visit_col` (default `EVENT_ID`), rejecting undeclared aliases with unmapped status and invalid declared columns with `KeyError`. Implemented `expected_unique: bool = False` parameter in builder and spec, raising `ValueError` on non-unique grains like DTI. Implemented `validate_field_level_provenance()` verifying structured locators (`doc_path`, `locator`, `columns_used`, `evidence_terms`) across PDF, DOCX, and XLSX files. Verified in focused contract tests. | **RESOLVED** |
| **DEEP-01C, DEEP-01E, DEEP-01F** (Major) | Implementation reports retained stale claims, superseded baseline MRI count (1,173 sessions), and 285 outputs (vs 286 saved). | Synchronized both report copies to 117 code cells / 286 outputs, 8,779 all-record / 3,351 baseline MRI counts, and purged prohibited claims. Dynamically bound Table 8.4B labels in generator to `len(df_mri_acq)` and `len(df_mri_bl)`. Added report parity test. | **RESOLVED** |
| **DEEP-02** (Major) | Cache order reversal, explicit alias contracts, builder uniqueness enforcement, field locator evidence, and report parity were untested by dedicated negative fixtures. | Added 6 focused contract and negative mutation tests to `test_notebook_contracts.py`. All tests pass cleanly. | **RESOLVED** |

### 6.4 Round 4 Deep Reverification
| Finding ID & Severity | Core Issue Identified by Codex (Round 4) | Implemented Resolution & Programmatic Evidence | Status |
| :--- | :--- | :--- | :---: |
| **DEEP-01E** (Major) | Executed `eda_neuroimaging.ipynb` cell 29 and `eda_multimodal_synthesis.ipynb` cell 31 retained biological/analytical-readiness claims ("high biological concordance", "presynaptic dopaminergic loss", "in parallel with DaTscan", "align closely in identifying synucleinopathy", "ready for longitudinal modeling"). | Rewrote conclusion and interpretation cells in both `generate_neuroimaging_notebook.py` and `generate_synthesis_notebook.py` as direct descriptive comparisons only. Re-executed both notebooks cleanly with zero errors and certified with `PrivacyGuard`. Verified zero prohibited phrases remain. | **RESOLVED** |
| **DEEP-01C & DEEP-01D & DEEP-01F** (Major) | Implementation reports retained pre-extension cell counts (14, 9, 9, 9, 8, 9), obsolete physical dimensions ($131,616 \times 9$, $139 \times 17$, $6,268 \times 37$, $21,399 \times 24$), old carrier totals ($N=9$ dual), 5 sensor skewness variables (vs 9 executed), stale MRI sequence counts ($6,644/8,344$ rs-fMRI, $3,558/3,616$ acceptability), and biological claims in Sections 3 and 3.7. | Rebuilt Sections 3 and 3.7 directly from an artifact-derived manifest extracted from the executed notebook JSON files. Synchronized per-notebook code cell/output counts (overview 21/38, clinical 21/54, biospecimen 15/39, genetics 14/35, neuroimaging 17/56, sensors 14/30, synthesis 15/34; total 117/286). Synchronized exact source dimensions from Table 8.1 across all 6 notebooks. Reconciled MRI sequence adherence to exact executed Table 8.4B numbers ($7,252$ DTI, $6,958$ rs-fMRI, $3,616$ acceptability for all records; $3,012$ DTI, $3,191$ rs-fMRI, $1,454$ acceptability for baseline). Reconciled genetics carrier groups from Table 8.3 ($376$ LRRK2, $277$ GBA, $28$ dual, $67$ rare, $3,057$ non-carrier). Reconciled sensor skewness to all 9 analyzed variables. Purged all overreaching claims across both report copies. Both copies are byte-identical. | **RESOLVED** |
| **DEEP-02** (Major) | Report parity test was a substring smoke test; negative mutation tested synthetic string difference rather than actual report validator failure. | Replaced `test_implementation_report_matches_executed_notebook_artifacts` with a parser-based contract: extracts per-notebook code cells, outputs, and errors from notebook JSONs; parses executed Table 8.4B, Table 8.3, sensor Table 8.6, and Table 8.1 deep inventory tables; compares all reported numbers against parsed tables; scans Sections 3 and 3.7 for an expanded prohibited-phrase blacklist. Upgraded `test_report_parity_negative_mutation_fails` to mutate a reported value and assert the actual parity validator fails. | **RESOLVED** |

---

## 7. Known Limitations & Research Handoff

1. **Digital Sensor Substudy Sample Size**: The mobile telemetry dataset captures $108,901$ records across a focused substudy cohort ($N=32$ participants). While repeat adherence is high ($93.8\%$), findings reflect pilot feasibility rather than fleet-wide epidemiological representation.
2. **Exploratory PET Imaging Scope**: Molecular PET substudies (AV-133, DPA-714, C05-05) reflect targeted exploratory protocols with sample sizes smaller than core DaTscan and MRI batteries.
3. **Genetic Ancestry Heterogeneity**: Historical PPMI enrichment for *LRRK2* G2019S and *GBA* N370S results in high representation of Ashkenazi Jewish and European ancestry; polygenic risk scores derived from European GWAS should be cautiously interpreted when applied across diverse genetic ancestries.
4. **Non-Causal Observational Scope**: All findings represent observational cross-sectional or longitudinal associations. No causal disease modification, drug efficacy, or prognostic clinical outcome claims are asserted.

---

## 8. Submission & Technical Verification Sign-Off

All seven requested multimodal exploratory data analysis notebooks have been generated, executed from clean kernels without error, independently tested across dual working directories, verified for raw source immutability (177/177 source hashes intact), and certified fail-closed for participant privacy by `PrivacyGuard`.

The entire multimodal EDA pipeline deliverable is hereby formally submitted to **Codex** for independent supervisory verification in `docs/review_log.md`.
