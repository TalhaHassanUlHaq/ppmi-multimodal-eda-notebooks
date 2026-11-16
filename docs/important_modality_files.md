# PPMI Non-Imaging Modalities & Priority Dataset Inventory

This document provides a comprehensive, structured reference for all **non-imaging modalities** in the Parkinson's Progression Markers Initiative (PPMI) dataset. It details the primary and essential supporting files, their physical scale, participant coverage, observation grains, and clinical/biological significance.

> [!NOTE]
> Per project specification, neuroimaging scan modalities (`DATSCAN/`, `dti/`, `MR Analysis Results/`, `MRI Acquisition/`, and `PET/`) are excluded from this catalog.

---

## 1. Modality Summary & Cross-Modal Overview

| Modality Domain | Primary Physical Folder | Primary / Anchor Dataset | Physical Scale | Cohort Coverage ($N$) | Core Scientific Focus |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Harmonized Longitudinal Spine** | `curated_datacuts/` | `PPMI_Curated_Data_Cut_Public_20260810.csv` | 20,408 $\times$ 215 | 5,019 participants | Multimodal milestone harmonization across 10+ years |
| **Clinical Motor Examination** | `MOTOR/` | `MDS-UPDRS_Part_III_09Nov2026.csv` | 31,902 $\times$ 49 | 5,463 participants | Clinician-scored motor signs, ON/OFF states |
| **Neuropsychological & Cognitive** | `neuropsychological/` | `Montreal_Cognitive_Assessment__MoCA__09Nov2026.csv` | 21,426 $\times$ 35 | 5,815 participants | Global cognition, processing speed, visuospatial |
| **Neurobehavioral & Sleep** | `neurobehavioral/`, `sleep disorder/` | `SCOPA-AUT`, `RBDSQ`, `ESS`, `GDS-15` | ~22,600 $\times$ 16–43 | ~5,340 participants | Autonomic dysfunction, dream enactment, mood |
| **Olfactory Sensory Testing** | `olfactory/` | `UPSIT_09Nov2026.csv` | 11,311 $\times$ 95 | 7,199 participants | 40-item smell identification, prodromal deficit |
| **Medical History & Medications** | `MEDICAL HISTORY/` | `LEDD_Concomitant_Medication_Log_09Nov2026.csv` | 10,373 $\times$ 15 | 1,891 participants | Levodopa Equivalent Daily Dose, comorbidities |
| **Genetics & Molecular Risk** | `subject_characteristics/` | `iu_genetic_consensus_20251025_09Nov2026.csv` | 6,265 $\times$ 21 | 6,265 participants | *LRRK2*, *GBA*, *SNCA*, *APOE*, and Polygenic Risk |
| **Biospecimens & Assays** | `biospecimen/` | `Current_Biospecimen_Analysis_Results_09Nov2026.csv` | 40,609 $\times$ 65 | 4,007 participants | CSF synuclein SAA, Aβ42, tau, plasma NfL |
| **Digital Mobile Telemetry** | `digital_Sensor/` | `Roche_PD_Monitoring_App_v2_data_09Nov2026.csv` | 108,901 $\times$ 22 | 32 participants | High-frequency smartphone motor & vocal active tests |

---

## 2. Detailed Modality Catalogs

### 2.1 Harmonized Longitudinal Cohort Spine
* **Physical Directory**: `curated_datacuts/`
* **Scientific Role**: Represents the centralized milestone data cut maintained by the PPMI bioinformatics core. It establishes the baseline reference definitions for participant cohorts (`PD`, `HC`, `SWEDD`, `Prodromal`, `Genetic Cohort`) and synthesizes clinical, biospecimen, and genetic milestones across standardized longitudinal visits (`SC`, `BL`, `V01` through `V20`).

#### Important Files
| File Name | Dimensions | Distinct $N$ | Observation Grain | Selection Tier | Clinical / Biological Purpose |
| :--- | :---: | :---: | :--- | :---: | :--- |
| **`PPMI_Curated_Data_Cut_Public_20260810.csv`** | 20,408 $\times$ 215 | 5,019 | `(PATNO, EVENT_ID)` | Primary EDA | Master longitudinal matrix containing demographics, cohort status, diagnosis age, motor summaries, cognitive metrics, and core biofluid markers. |
| **`PPMI_Curated_Data_Cut_Public_20260810(1).xlsx`** | 3 Sheets | 5,019 | Sheet-dependent | Supporting | Multi-tab workbook containing the primary curated cut (`[20260810]`), variable definitions (`[Data dictionary]`), and release changelogs (`[Information]`). |

---

### 2.2 Clinical Motor Assessments
* **Physical Directory**: `MOTOR/`
* **Scientific Role**: Gold-standard evaluations of motor symptom severity, physical impairment, and activities of daily living according to the Movement Disorder Society Unified Parkinson's Disease Rating Scale (MDS-UPDRS) Parts I through IV.

#### Important Files
| File Name | Dimensions | Distinct $N$ | Observation Grain | Selection Tier | Clinical / Biological Purpose |
| :--- | :---: | :---: | :--- | :---: | :--- |
| **`MDS-UPDRS_Part_III_09Nov2026.csv`** | 31,902 $\times$ 49 | 5,463 | `(PATNO, EVENT_ID, PDSTATE)` | Primary EDA | Objective clinician motor examination covering speech, facial expression, rest tremor, postural tremor, kinetic tremor, rigidity, finger tapping, hand movements, pronation-supination, toe tapping, leg agility, gait, posture, and bradykinesia. Differentiates `ON` vs. `OFF` levodopa states. |
| **`MDS_UPDRS_Part_II__Patient_Questionnaire_09Nov2026.csv`** | 31,883 $\times$ 18 | 5,459 | `(PATNO, EVENT_ID)` | Supporting | Motor Experiences of Daily Living (M-EDL). Patient-reported impact on speech, swallowing, dressing, eating, hygiene, turning in bed, and walking. |
| **`MDS-UPDRS_Part_I_09Nov2026.csv`** | 32,015 $\times$ 13 | 5,463 | `(PATNO, EVENT_ID)` | Supporting | Clinician-administered evaluation of Non-Motor Experiences of Daily Living (cognitive impairment, hallucinations, depressed mood, anxious mood, apathy, dopamine dysregulation syndrome). |
| **`MDS-UPDRS_Part_I_Patient_Questionnaire_09Nov2026.csv`** | 31,895 $\times$ 14 | 5,460 | `(PATNO, EVENT_ID)` | Supporting | Patient-reported Non-Motor Experiences of Daily Living (sleep problems, daytime sleepiness, pain, urinary problems, constipation, lightheadedness, fatigue). |
| **`MDS-UPDRS_Part_IV_09Nov2026.csv`** | 17,994 $\times$ 14 | 3,212 | `(PATNO, EVENT_ID)` | Supporting | Motor Complications: time spent with dyskinesias, dyskinesia-related disability, time in "OFF" state, motor fluctuations, and early morning dystonia. |
| **`Modified_Schwab___England_Activities_of_Daily_Living_09Nov2026.csv`** | 33,062 $\times$ 8 | 5,471 | `(PATNO, EVENT_ID)` | Supporting | Global percentage score (0% to 100%) indicating patient functional autonomy and independence in activities of daily living. |
| **`Neuro_QoL__Lower_Extremity_Function__Mobility__-_Short_Form_09Nov2026.csv`** | 14,826 $\times$ 15 | 4,822 | `(PATNO, EVENT_ID)` | Supporting | Standardized quality of life assessment focused on lower limb mobility, gait stability, and transfers. |
| **`Neuro_QoL__Upper_Extremity_Function_-_Short_Form_09Nov2026.csv`** | 14,823 $\times$ 15 | 4,822 | `(PATNO, EVENT_ID)` | Supporting | Standardized quality of life assessment measuring fine motor control, hand function, and daily upper extremity tasks. |

---

### 2.3 Neuropsychological & Cognitive Function
* **Physical Directories**: `neuropsychological/` & `other cognitive/`
* **Scientific Role**: Deep longitudinal tracking of cognitive domains susceptible to Parkinson's disease neurodegeneration, spanning executive function, visuospatial processing, memory encoding/retrieval, processing speed, and attention.

#### Important Files
| File Name | Dimensions | Distinct $N$ | Observation Grain | Selection Tier | Clinical / Biological Purpose |
| :--- | :---: | :---: | :--- | :---: | :--- |
| **`Montreal_Cognitive_Assessment__MoCA__09Nov2026.csv`** | 21,426 $\times$ 35 | 5,815 | `(PATNO, EVENT_ID)` | Primary EDA | Primary global cognitive screening tool (score 0–30) assessing short-term memory, visuospatial abilities, executive function, phonemic fluency, attention, and orientation. Crucial for identifying Mild Cognitive Impairment (MCI) and dementia onset. |
| **`Symbol_Digit_Modalities_Test_09Nov2026.csv`** | 20,494 $\times$ 12 | 5,323 | `(PATNO, EVENT_ID)` | Supporting | SDMT assesses complex visual scanning, cognitive processing speed, and divided attention. One of the earliest and most sensitive cognitive markers of decline. |
| **`Hopkins_Verbal_Learning_Test_-_Revised_09Nov2026.csv`** | 20,545 $\times$ 20 | 5,328 | `(PATNO, EVENT_ID)` | Supporting | HVLT-R assesses verbal episodic learning and memory across 3 immediate recall trials, delayed recall, and recognition discrimination index. |
| **`Benton_Judgement_of_Line_Orientation_09Nov2026.csv`** | 20,485 $\times$ 43 | 5,325 | `(PATNO, EVENT_ID)` | Supporting | BJLO evaluates parietal lobe integrity and spatial orientation by measuring angular matching of lines. |
| **`Letter_-_Number_Sequencing_09Nov2026.csv`** | 20,492 $\times$ 31 | 5,326 | `(PATNO, EVENT_ID)` | Supporting | Working memory test requiring mental re-ordering of intermixed letters and numbers in ascending and alphabetical order. |
| **`Cognitive_Categorization_09Nov2026.csv`** | 21,344 $\times$ 15 | 5,287 | `(PATNO, EVENT_ID)` | Supporting | Formal clinical diagnosis of cognitive decline stage (`1 = Normal Cognition`, `2 = MCI`, `3 = Dementia`). |
| **`Modified_Semantic_Fluency_09Nov2026.csv`** | 20,548 $\times$ 13 | 5,331 | `(PATNO, EVENT_ID)` | Supporting | Semantic category generation (animals, fruits, vegetables) probing temporal-frontal lexical networks. |
| **`Lexical_Fluency_09Nov2026.csv`** | 14,020 $\times$ 13 | 4,796 | `(PATNO, EVENT_ID)` | Supporting | Phonemic fluency test (F-A-S words in 60 seconds) assessing frontal lobe executive retrieval. |
| **`Clock_Drawing_09Nov2026.csv`** | 14,368 $\times$ 18 | 5,031 | `(PATNO, EVENT_ID)` | Supporting | Visuoconstructive and executive function task evaluating clock face construction and hand placement. |
| **`Trail_Making_A_and_B_09Nov2026.csv`** | 13,966 $\times$ 16 | 4,788 | `(PATNO, EVENT_ID)` | Supporting | TMT Part A measures psychomotor speed; Part B measures cognitive flexibility, visual search, and mental task switching. |

---

### 2.4 Neurobehavioral, Sleep & Autonomic Systems
* **Physical Directories**: `non motor/`, `sleep disorder/`, `neurobehavioral/`
* **Scientific Role**: Systematic tracking of non-motor symptoms that often emerge during the prodromal phase of synucleinopathy and severely impact long-term disease morbidity.

#### Important Files
| File Name | Dimensions | Distinct $N$ | Observation Grain | Selection Tier | Clinical / Biological Purpose |
| :--- | :---: | :---: | :--- | :---: | :--- |
| **`SCOPA-AUT_09Nov2026.csv`** | 22,632 $\times$ 43 | 5,342 | `(PATNO, EVENT_ID)` | Supporting | Scales for Outcomes in Parkinson's Disease - Autonomic. Detailed evaluation of gastrointestinal, urinary, cardiovascular, thermoregulatory, pupillomotor, and sexual dysfunction. |
| **`REM_Sleep_Behavior_Disorder_Screening_Questionnaire_09Nov2026.csv`** | 22,666 $\times$ 29 | 5,343 | `(PATNO, EVENT_ID)` | Supporting | RBDSQ screens for dream-enactment behavior, nocturnal movements, and sleep disruption. REM Sleep Behavior Disorder (RBD) is the strongest clinical prodromal indicator of alpha-synucleinopathy. |
| **`Epworth_Sleepiness_Scale_09Nov2026.csv`** | 22,655 $\times$ 16 | 5,341 | `(PATNO, EVENT_ID)` | Supporting | Standardized 8-scenario evaluation of daytime sleepiness and unintended sleep episodes. |
| **`Geriatric_Depression_Scale__Short_Version__09Nov2026.csv`** | 22,919 $\times$ 22 | 5,468 | `(PATNO, EVENT_ID)` | Supporting | 15-item short-form GDS assessing affective changes, depressive burden, and emotional well-being. |
| **`State-Trait_Anxiety_Inventory_for_Adults_09Nov2026.csv`** | 22,888 $\times$ 47 | 5,463 | `(PATNO, EVENT_ID)` | Supporting | Differentiates acute situational anxiety (State) from baseline personality anxiety predisposition (Trait). |
| **`QUIP-Current-Short_09Nov2026.csv`** | 22,593 $\times$ 21 | 5,334 | `(PATNO, EVENT_ID)` | Supporting | Questionnaire for Impulsive-Compulsive Disorders in Parkinson's Disease (compulsive gambling, hypersexuality, shopping, binge eating, punding). |

---

### 2.5 Olfactory Sensory Biomarker
* **Physical Directory**: `olfactory/`
* **Scientific Role**: Quantification of olfactory loss (hyposmia / anosmia), which represents one of the earliest premotor sensory manifestations of Parkinson's disease.

#### Important Files
| File Name | Dimensions | Distinct $N$ | Observation Grain | Selection Tier | Clinical / Biological Purpose |
| :--- | :---: | :---: | :--- | :---: | :--- |
| **`University_of_Pennsylvania_Smell_Identification_Test_UPSIT_09Nov2026.csv`** | 11,311 $\times$ 95 | 7,199 | `(PATNO, EVENT_ID)` | Supporting | 40-item scratch-and-sniff test across 4 booklets. Provides total score, age/sex-adjusted percentiles, and classification into normosmia, microsmia, or anosmia. Primary clinical enrichment criterion for prodromal cohorts. |
| **`Smell_and_Genetic_Testing_US_09Nov2026.csv`** | 2,719 $\times$ 24 | 2,719 | `(PATNO,)` | Supporting | Home-based olfactory pre-screening and genetic consent records for remote prodromal ascertainment. |

---

### 2.6 Medical History, Systemic Diagnostics & Medications
* **Physical Directory**: `MEDICAL HISTORY/`
* **Scientific Role**: Captures participant clinical background, baseline diagnostic verification, systemic comorbidities, physical examination metrics, and detailed pharmacological regimens.

#### Important Files
| File Name | Dimensions | Distinct $N$ | Observation Grain | Selection Tier | Clinical / Biological Purpose |
| :--- | :---: | :---: | :--- | :---: | :--- |
| **`LEDD_Concomitant_Medication_Log_09Nov2026.csv`** | 10,373 $\times$ 15 | 1,891 | `(PATNO, START_DATE, DRUG_NAME)` | Supporting | Standardized **Levodopa Equivalent Daily Dose (LEDD)** calculations. Crucial covariate for adjusting UPDRS motor scores to account for dopaminergic symptom masking. |
| **`Concomitant_Medication_Log_09Nov2026.csv`** | 68,820 $\times$ 22 | 7,834 | `(PATNO, LOG_ID)` | Supporting | Comprehensive medication history recording drug trade/generic names, indication, daily dose, unit, route, and start/end dates. |
| **`Medical_Conditions_Log_09Nov2026.csv`** | 40,101 $\times$ 14 | 6,636 | `(PATNO, LOG_ID)` | Supporting | Medical history and ongoing comorbidities coded by MedDRA body systems. |
| **`Vital_Signs_09Nov2026.csv`** | 33,495 $\times$ 17 | 7,177 | `(PATNO, EVENT_ID)` | Supporting | Supine and standing blood pressures (orthostatic drop detection), pulse rate, weight, height, and temperature. |
| **`Primary_Research_Diagnosis_09Nov2026.csv`** | 30,813 $\times$ 18 | 5,579 | `(PATNO, EVENT_ID)` | Supporting | Clinician diagnostic certainty and classification across visits (Idiopathic PD, Multiple System Atrophy, Progressive Supranuclear Palsy, Essential Tremor). |
| **`Clinical_Diagnosis_09Nov2026.csv`** | 19,752 $\times$ 11 | 4,611 | `(PATNO, EVENT_ID)` | Supporting | Site-investigator diagnostic logs verifying inclusion/exclusion criteria fulfillment. |
| **`Determination_of_Freezing_and_Falls_09Nov2026.csv`** | 14,864 $\times$ 25 | 4,830 | `(PATNO, EVENT_ID)` | Supporting | Longitudinal tracking of Freezing of Gait (FOG) questionnaire responses and fall frequencies. |
| **`General_Physical_Exam_09Nov2026.csv`** | 79,708 $\times$ 10 | 7,236 | `(PATNO, EVENT_ID, EXAM_ITEM)` | Supporting | Itemized physical examination findings across organ systems. |
| **`Neurological_Exam_09Nov2026.csv`** | 22,643 $\times$ 16 | 7,253 | `(PATNO, EVENT_ID)` | Supporting | Cranial nerves, deep tendon reflexes, and sensory exam logs. |

---

### 2.7 Genetics & Molecular Risk
* **Physical Directory**: `subject_characteristics/`
* **Scientific Role**: High-resolution genotypic characterization of the PPMI cohort, including pathogenic variants in major familial Parkinsonism genes, common risk SNPs, polygenic risk scores, and pedigree history.

#### Important Files
| File Name | Dimensions | Distinct $N$ | Observation Grain | Selection Tier | Clinical / Biological Purpose |
| :--- | :---: | :---: | :--- | :---: | :--- |
| **`iu_genetic_consensus_20251025_09Nov2026.csv`** | 6,265 $\times$ 21 | 6,265 | `(PATNO,)` | Primary EDA | Consensus genetic determinations across all sequencing runs: *LRRK2* mutations (G2019S, R1441G), *GBA* variants (N370S, L444P, E326K), *SNCA* mutations/multiplications, *PRKN*, *PINK1*, and *APOE* ($\varepsilon2/\varepsilon3/\varepsilon4$) diplotypes. |
| **`Polygenic_Risk_Scores_09Nov2026.csv`** | 2,996 $\times$ 17 | 2,996 | `(PATNO,)` | Primary EDA | Validated Parkinson's Polygenic Risk Scores (PRS) including META5 effect sizes, GP2 European PRS, and GP2 multi-ancestry risk estimates. |
| **`Family_History_09Nov2026.csv`** | 9,310 $\times$ 43 | 8,379 | `(PATNO, RELATIVE_TYPE)` | Supporting | Detailed pedigree survey documenting first-, second-, and third-degree biological relatives diagnosed with PD, tremor, or dementia. |
| **`Genotypes_for_Polygenic_Risk_Scores_09Nov2026.csv`** | 214,560 $\times$ 9 | 894 | `(PATNO, SNP_ID)` | Supporting | Measured dosage ($0, 1, 2$) and genotype calls across 240 genome-wide association risk loci used to construct polygenic scores. |
| **`PPMI_Project_9001_20250624_09Nov2026.csv`** | 1,319 $\times$ 109 | 1,319 | `(PATNO,)` | Supporting | Deep targeted resequencing of known Parkinson's loci across enriched genetic cohorts. |
| **`PPMI_PD_Variants_Genetic_Status_WGS_20180921.csv`** | 960 $\times$ 73 | 960 | `(PATNO,)` | Supporting | Whole-Genome Sequencing (WGS) call status for rare pathogenic and likely-pathogenic variants. |

---

### 2.8 Biospecimens & Laboratory Assays
* **Physical Directory**: `biospecimen/`
* **Scientific Role**: Quantification of molecular pathology in cerebrospinal fluid (CSF), blood, and cell models, providing direct biological evidence of protein aggregation and neurodegeneration.

#### Important Files
| File Name | Dimensions | Distinct $N$ | Observation Grain | Selection Tier | Clinical / Biological Purpose |
| :--- | :---: | :---: | :--- | :---: | :--- |
| **`Current_Biospecimen_Analysis_Results_09Nov2026.csv`** | 40,609 $\times$ 65 | 4,007 | `(PATNO, CLINICAL_EVENT, TESTNAME)` | Primary EDA | Core laboratory assays across lumbar puncture CSF and blood biofluids: <br>• **Alpha-Synuclein SAA**: Seed Amplification Assay qualitative reads (positive/negative) and aggregation kinetics.<br>• **Core CSF Analytes**: Roche Elecsys Aβ1-42, Total Tau (t-tau), and Phosphorylated Tau 181 (p-tau181).<br>• **Neurofilament Light (NfL)**: Axonal damage biomarker in CSF and plasma.<br>• **Serum & Plasma Biochemistry**: Urate, lipid subfractions, and systemic biochemistry. |
| **`PPMI_Physical_Biorepository_09Nov2026.csv`** | 131,885 $\times$ 18 | 3,923 | `(PATNO, MATRIX, ALIQUOT_ID)` | Supporting | Physical aliquot inventory stored at the Indiana University Biorepository across 8 biological matrices: RNA ($28,228$), Plasma ($21,985$), Serum ($21,896$), Whole Blood ($19,387$), DNA ($17,691$), CSF ($9,888$), Urine ($9,729$), and PBMC ($2,812$). |
| **`Whole_Blood_WBS_Gene_Expression_RNA_Sequencing_09Nov2026.csv`** | 2,729 $\times$ 12 | 1,466 | `(PATNO, EVENT_ID, SAMPLE_ID)` | Supporting | Sample manifests for PaxGene whole-blood tubes allocated to transcriptome and RNA-sequencing profiling. |
| **`PPMI_IPSC_Catalog_09Nov2026.csv`** | 41 $\times$ 21 | 41 lines | `(LINE_ID,)` | Supporting | Induced Pluripotent Stem Cell (iPSC) lines derived from PPMI participants, annotated by genotype (*LRRK2*, *GBA*, *SNCA*, Idiopathic PD, Healthy Control). |

---

### 2.9 Digital Sensors & High-Frequency Telemetry
* **Physical Directory**: `digital_Sensor/`
* **Scientific Role**: Objective, continuous, and high-frequency digital phenotyping using smartphone active tests and passive telemetry to detect subtle motor fluctuations and early digital progression biomarkers.

#### Important Files
| File Name | Dimensions | Distinct $N$ | Observation Grain | Selection Tier | Clinical / Biological Purpose |
| :--- | :---: | :---: | :--- | :---: | :--- |
| **`Roche_PD_Monitoring_App_v2_data_09Nov2026.csv`** | 108,901 $\times$ 22 | 32 | `(PATNO, TIMESTAMP, TEST_TYPE)` | Primary EDA | High-frequency smartphone telemetry from the Roche PD Mobile Application monitoring substudy. Captures daily active test batteries: <br>• **Sustained Phonation**: Acoustic stability, jitter, shimmer, voice tremor.<br>• **Rest & Postural Tremor**: 3-axis accelerometer and gyroscope power spectrum frequencies.<br>• **Finger Tapping**: Bilateral tapping speed, cadence, and motor fatigue.<br>• **Balance & Turn Tests**: U-turn stability, gait symmetry, and sway velocity.<br>• **Cognitive Active Tests**: Symbol-digit substitution and daily symptom surveys. |

---

## 3. Relational Grain & Safe Cross-Modal Joining

### Universal Primary Keys
To perform valid cross-modal merges without generating false Cartesian products, data analysts must respect the following key relationships:

1. **Participant-Level Datasets (1:1 with Demographics)**:
   * **Key**: `PATNO`
   * **Tables**: `iu_genetic_consensus_20251025_09Nov2026.csv`, `Polygenic_Risk_Scores_09Nov2026.csv`, `Family_History_09Nov2026.csv`
2. **Longitudinal Visit-Level Datasets (1:1 or 1:Many per Visit)**:
   * **Keys**: `(PATNO, EVENT_ID)`
   * **Tables**: `PPMI_Curated_Data_Cut_Public_20260810.csv`, `Montreal_Cognitive_Assessment__MoCA__09Nov2026.csv`, `SCOPA-AUT_09Nov2026.csv`, `RBDSQ_09Nov2026.csv`, `Vital_Signs_09Nov2026.csv`
3. **Multi-State Clinical Assessments**:
   * **Keys**: `(PATNO, EVENT_ID, PDSTATE)`
   * **Table**: `MDS-UPDRS_Part_III_09Nov2026.csv` (requires explicit stratification by `PDSTATE = 'ON'` or `'OFF'`)
4. **Biofluid Analyte Long-Form Results**:
   * **Keys**: `(PATNO, CLINICAL_EVENT, TESTNAME)`
   * **Table**: `Current_Biospecimen_Analysis_Results_09Nov2026.csv` (requires filtering or pivoting by `TESTNAME` prior to visit merges)

> [!IMPORTANT]
> Always validate observation grains and cardinality via `validate_safe_merge()` before joining tables. Unchecked Many:Many (`m:m`) relational merges are strictly prohibited by pipeline contracts.
