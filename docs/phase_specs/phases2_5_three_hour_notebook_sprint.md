# Phases 2–5: Three-Hour Multimodal Notebook Sprint

Status: **AUTHORIZED BY THE HUMAN RESEARCHER on 2026-11-12**

Owner: Gemini (implementation). Codex remains supervisor/reviewer and must not edit implementation code.

## 1. Objective and governing decision

Produce the complete publication-quality PPMI multimodal EDA notebook set within the accelerated three-hour window. The researcher has approved the dataset-selection gate and explicitly authorized all modality notebooks. The remaining Round 7 claim-manifest provenance finding is tracked technical debt and must not delay notebook creation.

Required final notebooks:

1. `00_dataset_overview.ipynb` — preserve and reuse the approved Phase 1 inventory and selection evidence.
2. `eda_clinical.ipynb` — demographics, cohorts, motor/non-motor, cognition, sleep, olfaction, medications, and longitudinal clinical phenotyping.
3. `eda_biospecimen.ipynb` — specimen/assay availability and documented biomarker distributions.
4. `eda_genetics.ipynb` — consensus genetics, PRS, and genomic availability.
5. `eda_neuroimaging.ipynb` — DaTscan, structural MRI/FreeSurfer, DTI, rs-fMRI, PET, and imaging QC/coverage.
6. `eda_digital_sensors.ipynb` — Roche mobile telemetry coverage, repeated assessments, and documented active/passive measures.
7. `eda_multimodal_synthesis.ipynb` — cross-modality availability, safe alignment, and descriptive synthesis.

Python modules, CSV reports, HTML fragments, and exported figures are supporting artifacts only. The executed notebooks are the deliverables.

## 2. Approved source scope

Use `EDA/outputs/reports/dataset_selection_matrix.json` as the machine-readable approved source list. Include decision units whose `provisional_recommendation` is `Primary EDA` or `Supporting` and whose target notebook matches the notebook being built. Treat the researcher's approval as approval of those recommendations; do not change file category, cohort definition, or exclusion during this sprint.

Current target counts that the implementation must reconcile:

| Notebook | Primary units | Supporting units | Total units |
| --- | ---: | ---: | ---: |
| `eda_clinical.ipynb` | 2 | 79 | 81 |
| `eda_biospecimen.ipynb` | 2 | 5 | 7 |
| `eda_genetics.ipynb` | 2 | 3 | 5 |
| `eda_neuroimaging.ipynb` | 10 | 26 | 36 |
| `eda_digital_sensors.ipynb` | 1 | 0 | 1 |
| `eda_multimodal_synthesis.ipynb` | 2 | 2 | 4 |

The same physical file and its worksheet decision unit may both appear in the matrix. The notebook must display them without double-counting them as two independent datasets.

## 3. Shared implementation architecture

Gemini must first build or reuse a small shared notebook-support layer for:

- deterministic repository-root and source-path resolution;
- approved source-list loading and reconciliation;
- exact source-schema extraction;
- complete column-dictionary generation;
- privacy-safe aggregate display;
- cohort/event label handling from verified documentation only;
- duplicate-key and join-cardinality checks;
- missingness summaries with explicit denominators;
- consistent plotting style, captions, units, and sample-size annotations;
- notebook contract tests and clean-kernel execution.

Do not hide the scientific analysis in modules. Each notebook must show its research questions, key transformations, analysis calls, computed tables/figures, and interpretation. Modules may remove repetitive ingestion, dictionary, validation, and styling code.

## 4. Mandatory notebook structure

Every modality notebook must contain these sections in this order:

1. Title, scope, scientific introduction, and execution timestamp/data-cut version.
2. Research questions and explicit non-causal scope.
3. **Selected source files table** containing every approved Primary and Supporting unit for that notebook: exact path, worksheet when applicable, dimensions, observation grain, category, analytical role, and selection rationale.
4. **Complete source column dictionaries** for every selected physical data source/worksheet. Use collapsible `<details>` sections for wide or numerous sources, but the complete dictionary must be stored and accessible inside the executed notebook.
5. Cohort, visit, key, unit, and join definitions.
6. Data-quality and representativeness assessment.
7. Modality-specific descriptive analyses and figures.
8. Results-driven interpretation generated from computed aggregates, not hardcoded statistics.
9. Limitations, missing documentation, confounding, selection bias, and follow-up analyses.
10. Conclusions grounded in displayed results.
11. Reproducibility and privacy validation summary.

Every complete column dictionary row must contain:

- exact original column name;
- verified description or `Definition not verified in available local documentation`;
- storage/inferred data type and scientific type;
- documented unit or scoring range, otherwise `Not verified`;
- missing count and missingness percentage;
- the exact denominator used for missingness;
- variable role;
- `Used in current EDA` (`Yes`/`No`);
- documentation source and locator, or explicit unverified status.

Never silently rename source columns or invent definitions. Derived variables must be listed separately with formula, inputs, assumptions, and provenance.

## 5. Modality-specific minimum analyses

### A. Clinical notebook

Primary analytical source: approved curated data-cut worksheet. Supporting files provide interpretation, cohort/diagnosis context, medication state, safety context, or corroboration; they do not each require an independent plot.

Minimum questions and outputs, only when the required fields and definitions are verified:

- cohort and enrollment composition with named denominators;
- baseline age, sex/gender, education, race/ethnicity, and disease-duration summaries where documented;
- visit/event coverage and attrition by cohort, with raw event semantics clearly distinguished from scheduled visits;
- MDS-UPDRS Parts I–IV distributions and longitudinal aggregate trajectories;
- MoCA and other documented cognitive-domain summaries/trajectories;
- non-motor, neurobehavioral, sleep, autonomic, olfactory, and ADL summaries for verified scores;
- medication state and initiation of dopaminergic therapy as descriptive context, not causal adjustment unless specified;
- missingness and assessment availability heatmap by domain and event;
- cohort differences reported descriptively with effect sizes and uncertainty where valid; avoid indiscriminate p-value tables.

Use one participant per baseline summary. Define baseline from an approved event dictionary or verified source rule; if unavailable, label the operational rule explicitly and do not call it official baseline. Aggregate longitudinal plots must display event-specific participant counts. Do not display participant trajectories or identifiers.

### B. Biospecimen notebook

Minimum outputs:

- specimen and assay availability by specimen type, cohort, and event;
- assay missingness, below/above quantification-limit flags, QC status, batch/platform/version coverage where documented;
- distributions for verified biomarker analytes with units and sample sizes;
- repeat-measure availability and within-participant change summaries only when specimen/event alignment is valid;
- documented CSF/plasma/serum associations as exploratory correlations, with pairwise sample sizes and no causal language;
- iPSC/catalog content summarized as availability metadata, not biological assay values.

Do not combine assay versions, matrices, units, or platforms without an explicit harmonization rule. Do not log-transform zero/negative values or censored measurements without a documented policy.

### C. Genetics notebook

Minimum outputs:

- aggregate consensus genetic-status coverage and counts by documented gene/status category;
- PRS availability, missingness, distribution, and documented scale;
- genotype/variant availability summaries for supporting sources;
- cohort-stratified PRS summaries only when cohort and ancestry context are valid;
- explicit discussion of ancestry, population structure, relatedness, platform, and ascertainment limitations.

Never display participant-level variants, genotypes, or rare combinations. Do not run Hardy–Weinberg, ancestry comparisons, penetrance, or gene–phenotype inference without the required verified population definition. Suppress privacy-sensitive small cells under the existing privacy policy.

### D. Neuroimaging notebook

Analyze each imaging modality at its native grain before any integration:

- DaTscan quantitative SBR distributions, regional/asymmetry summaries, visual-read categories, and quantitative/visual concordance;
- FreeSurfer cortical thickness, surface area, and subcortical volume coverage/QC; intracranial-volume normalization only when the exact ICV field and formula are verified;
- DTI ROI FA/diffusivity distributions using manual ROI language; no tractography claims;
- rs-fMRI acquisition/processing coverage and QC/motion summaries; do not fabricate connectivity measures from metadata;
- PET tracer/SBR distributions separated by tracer, protocol, and documented units;
- modality-by-cohort/event coverage and missingness.

Document image-derived-measure provenance, laterality, units, QC filters, scanner/site/protocol heterogeneity, and repeated-scan grain. No many-to-many merge of scan-level tables. Keep exploratory associations separate by modality and annotate sample sizes.

### E. Digital-sensor notebook

Minimum outputs:

- observation grain and verified participant/timestamp coverage;
- assessment dates, participant-days, sessions/assessments per participant, and follow-up span as privacy-safe distributions;
- missingness and availability by documented task/test/sensor measure;
- within-participant repeated-assessment coverage and aggregate temporal patterns;
- distributions and reliability summaries for documented derived measures only;
- device/app/version/time-zone and irregular-sampling limitations.

Do not display raw participant traces, exact timestamps tied to participants, or identifiers. Do not interpret telemetry as clinical progression without validated outcome alignment.

### F. Multimodal synthesis notebook

Minimum outputs:

- modality availability matrix and overlap counts at participant level, exported/displayed only as safe aggregates;
- cohort/event coverage across clinical, biospecimen, genetics, imaging, and sensors;
- attrition and selection-bias comparison between the full clinical cohort and multimodal subsets;
- join-cardinality audit for every cross-modal link;
- a small number of scientifically motivated cross-modal descriptive associations only when temporal alignment, units, grain, and confounders are defensible;
- explicit separation of same-event, nearest-date, and ever-observed availability.

Do not force a complete-case integrated analysis. Do not perform predictive modeling, causal inference, imputation, or participant-level export during this sprint.

## 6. Statistical and visual standards

- Report `n`, missing `n`, denominator, central tendency, spread, and units.
- Every notebook, including `00_dataset_overview.ipynb`, must display a computed skewness table for each numeric variable actually analyzed. Report valid `n`, missing `n`, Fisher–Pearson sample skewness (`bias=False`), direction/magnitude using a documented descriptive rule, and the analysis grain. Identifiers and categorical variables are `Not applicable`. For transformed variables, report skewness before and after transformation.
- Use medians/IQR for skewed measures and mean/SD only where informative; show distribution shape.
- For repeated observations, use participant-level aggregation or repeated-measures-aware descriptive summaries. Do not treat rows as independent participants.
- Exploratory correlations require pairwise `n`; prefer Spearman when scale/distribution supports it. Correct or clearly label multiple testing if many associations are shown.
- Figures require informative title, axes, units, legend, cohort/event definition, and sample size or a linked sample-size table.
- Avoid redundant histograms, generic plots of every numeric column, decorative dashboards, and causal wording.
- Interpret only values computed during notebook execution. No hardcoded findings or manually typed statistics.

## 7. Privacy and prohibited operations

- Never display or save PATNO, subject aliases, exact participant-linked dates/times, row-level genetics, or participant records in notebook outputs.
- Keep participant-level processing local and transient. Send only schemas, code, synthetic fixtures, and approved aggregates to agent review.
- Run PrivacyGuard on every saved output object and the complete executed notebook.
- Preserve every original source file and verify all 177 source hashes at final handoff.
- No unchecked many-to-many joins, silent deduplication, undocumented exclusions, cohort redefinitions, outcome leakage, imputation, causal claims, or model training.

## 8. Required tests and acceptance criteria

Gemini must add automated tests that verify:

1. all seven notebooks exist and are valid notebook JSON;
2. all six new notebooks contain every required section;
3. approved selection counts reconcile to 81, 7, 5, 36, 1, and 4 units respectively;
4. every selected physical source/worksheet has a complete dictionary with exact schema-column coverage and no invented rename;
5. missingness denominators equal the relevant source row count and header-only files are handled;
6. no raw participant identifier or participant-level record appears in saved outputs;
7. every merge declares keys, validates nulls/duplicates, and enforces expected cardinality;
8. displayed summary tables and figures carry sample sizes and units where documented;
9. interpretations contain no hardcoded numeric results disconnected from code outputs;
10. every notebook executes from a clean kernel in repository order with zero errors;
11. PrivacyGuard passes every executed notebook;
12. all 177 source hashes remain unchanged.

A notebook may state that an analysis is not supportable when documentation or variables are absent. It may not fabricate a substitute. A notebook is acceptable only when it executes cleanly, contains the complete selected-source/dictionary evidence, provides at least the minimum valid modality analyses, presents readable results, and passes privacy checks.

## 9. Three-hour execution schedule

### 0:00–0:30 — shared foundation and all skeletons

- Freeze approved selection lists and counts.
- Implement/reuse shared schema, dictionary, safe-display, plotting, and join-validation helpers.
- Create all six new notebook skeletons with every mandatory Markdown section.
- Add notebook contract and dictionary-coverage tests first.

### 0:30–1:20 — clinical, biospecimen, and genetics

- Complete and execute `eda_clinical.ipynb` using the curated data cut as the principal analytical table.
- Complete and execute `eda_biospecimen.ipynb` and `eda_genetics.ipynb` with conservative availability/distribution analyses.
- Do not spend time plotting each Supporting file.

### 1:20–2:05 — neuroimaging and digital sensors

- Complete imaging sections independently by modality.
- Complete sensor coverage/repetition/temporal summaries.
- Run targeted tests and PrivacyGuard immediately after each notebook.

### 2:05–2:35 — multimodal synthesis

- Build coverage/overlap and join-audit outputs first.
- Add only cross-modal associations that pass key, grain, temporal-alignment, and documentation checks.

### 2:35–3:00 — execution and handoff

- Execute all notebooks from clean kernels.
- Run notebook contract tests, PrivacyGuard, hash checks, and full relevant test suite.
- Fix only blocking execution/privacy/dictionary defects.
- Update the implementation report with per-notebook cells, outputs, runtime, tests, limitations, and unresolved items.
- Submit to Codex. Do not wait for perfection on optional plots.

## 10. Handoff format

Gemini's handoff must list, for each notebook:

- path and execution status;
- selected Primary/Supporting unit counts;
- complete-dictionary coverage result;
- research questions answered and analyses intentionally omitted;
- figures/tables produced;
- privacy result;
- test result and runtime;
- unresolved documentation or scientific limitations.

Codex will prioritize blocking review in this order: privacy, source preservation, identifier/cohort/event correctness, join cardinality, dictionary completeness, statistical validity, clean execution, then presentation polish.
