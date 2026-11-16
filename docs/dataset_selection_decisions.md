# Dataset Selection & Prioritization Decisions
**Document**: `docs/dataset_selection_decisions.md`  
**Governance Standard**: `AGENTS.md` & `docs/phase_specs/dataset_selection_gate.md`  
**Review Status**: **Codex Review & Human Sign-off Pending**  
**Date**: 2026-11-12  

---

## 1. Decision Summary & Selection Tiers

In accordance with `AGENTS.md` and `docs/phase_specs/dataset_selection_gate.md`, all 177 source files and 6 audited worksheets 
have been evaluated across the seven standardized criteria. In accordance with pre-review governance rules, all recommendations 
remain **provisional** (Awaiting Codex review and researcher sign-off).

| Category | Source Files | Worksheets | Total Decision Units | Percentage (%) |
| :--- | :---: | :---: | :---: | :---: |
| **Primary EDA** | **11** | **2** | **13** | **7.1%** |
| **Supporting** | **132** | **4** | **136** | **74.3%** |
| **Excluded from detailed EDA** | **4** | **0** | **4** | **2.2%** |
| **Needs Review** | **30** | **0** | **30** | **16.4%** |
| **Total Universe** | **177** | **6** | **183** | **100.0%** |

---

## 2. Primary EDA Recommendations

### Phase 2: Cohort Demographics, Clinical & Longitudinal Phenotyping (`eda_clinical.ipynb`)
- Note: Primary clinical instruments are represented in the 23 candidate tables in Section 4 awaiting formal sign-off.

### Phase 3: Biospecimen & Molecular/Genetic Profiling (`eda_biospecimen.ipynb`, `eda_genetics.ipynb`)
- Consensus Monogenic & APOE Genotypes (`subject_characteristics/iu_genetic_consensus_20251025_09Nov2026.csv`)
- Polygenic Risk Scores (`subject_characteristics/Polygenic_Risk_Scores_09Nov2026.csv`)

### Phase 4: Neuroimaging & Digital Sensor Multimodal Analysis (`eda_neuroimaging.ipynb`, `eda_digital_sensors.ipynb`)
- DaTscan Quantitative Striatal Binding Ratios (`DATSCAN/Xing_Core_Lab_-_Quant_SBR_09Nov2026.csv`)
- DaTscan Qualitative Visual Interpretation (`DATSCAN/Xing_Core_Lab_-_Visual_Read_09Nov2026.csv`)
- FreeSurfer v7 Cortical Thickness (`MR Analysis Results/FS7_APARC_CTH_09Nov2026.csv`)
- FreeSurfer v7 Cortical Surface Area (`MR Analysis Results/FS7_APARC_SA_09Nov2026.csv`)
- FreeSurfer v7 Subcortical Volumetrics (`MR Analysis Results/FS7_ASEG_VOL_09Nov2026.csv`)
- DTI Regions of Interest (Substantia Nigra & Cerebral Peduncle) (`dti/DTI_Regions_of_Interest_09Nov2026.csv`)
- AV-133 VMAT2 PET SBR Analysis (`PET/PET_SBR_Analysis_09Nov2026.csv`)
- Roche PD Mobile App Monitoring Telemetry (`digital_Sensor/Roche_PD_Monitoring_App_v2_data_09Nov2026.csv`)

### Phase 5: Multimodal Integration (`eda_multimodal_synthesis.ipynb`)
- Public Curated Longitudinal Multimodal Cut (`curated_datacuts/PPMI_Curated_Data_Cut_Public_20260810(1).xlsx` sheet `[20260810]`)

---

## 3. Provisional Candidate Exclusions & Objective Justifications

1. `MR Analysis Results/FS7_APARC_CTH_09Nov2026(1).csv`: Verified SHA-256 match (byte-identical copy of `MR Analysis Results/FS7_APARC_CTH_09Nov2026.csv`).
2. `subject_characteristics/iu_genetic_consensus_20251025_09Nov2026(1).csv`: Verified SHA-256 match (byte-identical copy of `subject_characteristics/iu_genetic_consensus_20251025_09Nov2026.csv`).
3. `MR Analysis Results/._FS7_APARC_CTH_09Nov2026(1).csv`: AppleDouble metadata sidecar (magic verified: 00 05 16 07; companion hash differs).
4. `subject_characteristics/._iu_genetic_consensus_20251025_09Nov2026(1).csv`: AppleDouble metadata sidecar (magic verified: 00 05 16 07; companion hash differs).

---

## 4. Formal Approval Gate Signatures

- **Codex Supervisory Review Verdict**: [ ] PENDING / [ ] APPROVED  
- **Date**: ____________________  
- **Human Researcher Formal Approval**: [ ] APPROVED  
- **Date**: ____________________  