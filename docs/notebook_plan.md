# Final Jupyter notebook organization and review contract

Status: notebook architecture specified from the user's mandatory deliverable requirement on 2026-11-12. Only Phase 1 implementation is currently assigned. Exact later analyses and source lists remain conditional on the Phase 1 and selection approvals.

## Notebook sequence

| Order / notebook | Phase | Scientific scope and primary outputs |
| --- | --- | --- |
| `00_dataset_overview.ipynb` | 1, then versioned at the selection gate | Reproducible physical source inventory; file and sheet coverage; formats and sizes; aggregate structural quality, grain/key status, documentation provenance, local versus external availability, and audit limitations. Phase 1 version labels all file selection as pending. At the later selection gate, a new version can display the proposed decision matrix for human review and then record the approved decisions without rewriting the original audit evidence. |
| `eda_clinical.ipynb` | 2 | Approved cohort and enrollment denominators; demographics, diagnosis and medical history; medications and treatment state; MDS-UPDRS and other motor measures; non-motor, autonomic, mood, cognition and neuropsychology, sleep, olfaction, daily living; visit coverage and valid longitudinal descriptions. Organize sections by research question so this breadth does not become a plot catalog. |
| `eda_biospecimen.ipynb` | 3 | Specimen/aliquot/assay-run coverage, documented CSF and blood measures, SAA and iPSC catalog status where verified, assay QC, limits and batches, and substudy-specific denominators. |
| `eda_genetics.ipynb` | 3 | Verified consensus variants, APOE, PRS, and sequencing or transcriptomic availability; documented ancestry, genotyping QC, data versions, and the distinction between derived results and raw molecular data. |
| `eda_neuroimaging.ipynb` | 4 | Separate question-led sections for DaTscan SBR/visual reads, structural MRI/FreeSurfer, DTI, rs-fMRI, and PET tracers actually present and approved; scan/region/tracer grain, acquisition context and QC. |
| `eda_digital_sensors.ipynb` | 4 | Roche app active-test and sensor-derived feature availability, run/window coverage, quality and sampling; within-participant summaries before participant comparisons. Document whether high-frequency streams are truly present. |
| `eda_multimodal_synthesis.ipynb` | 5 | Curated cut provenance and validated cross-modal overlap; approved feature harmonization, join cardinality, temporal alignment, cohort attrition and appropriately qualified associations. |

The curated workbook may support several notebooks, but its sheet role and grain must be stated each time. A modality that has no verified usable local data receives an explicit availability/limitation section rather than an invented analysis. Splitting a very large approved modality notebook requires human and Codex agreement on the revised deliverable map.

## Required narrative in every notebook

Begin with title, brief scientific introduction and source table. For modality notebooks, place the complete source column dictionary immediately after that table, as specified in [EDA/RESEARCH_PLAN.md](../EDA/RESEARCH_PLAN.md). Then present objectives and research questions, eligible population and denominators, data description and provenance, quality assessment, analysis methods, computed descriptive results, selected figures/tables, interpretation, limitations, and conclusions. `00_dataset_overview.ipynb` uses a complete source manifest and accessible structural schema catalog in place of a modality-specific clinical dictionary; it must not pretend that unapproved files are selected for detailed EDA.

Gemini must write explanatory Markdown next to executable cells: why each question matters, why each filter/aggregation is used, what each output shows, and what cannot be inferred. Reusable Python modules may handle ingestion, validation, scoring and plotting helpers, but the notebook must display the key parameters, sample/record flow, calculations called, and results needed to audit the scientific argument. Code, CSV reports, and exported figures support the notebooks and do not replace them.

Display summary tables and figures in saved notebook outputs, with descriptive titles, axis and column labels, documented units, captions or nearby explanatory text, cohort and visit definitions, and participant and observation sample sizes or denominators. Show missingness, quality exclusions and uncertainty when relevant. Avoid duplicate or uninformative plots. Compute numbers from local sources on execution; do not hardcode results, create placeholder findings, or infer a clinical interpretation from a header alone. Distinguish descriptive observations, associations, and causal claims.

## Reproducibility and privacy gate

Gemini documents a clean environment setup, package versions or lock file, input paths and versions, parsing rules, execution command/order, and random seeds when used. Every notebook must execute top to bottom from a clean kernel in the documented environment, with all output cells refreshed. No participant-level rows, identifiers, dates, restricted free text, or unredacted error traces may be saved in the notebook or exported review artifacts. Aggregate outputs must pass privacy checks, including small-cell handling where disclosure risk exists.

Codex reviews executed notebooks for statistical correctness, denominator and grain integrity, duplicate and missingness handling, score/unit provenance, visual clarity, caption completeness, narrative consistency, reproducibility, and output privacy. Gemini corrects findings and reruns the notebook; Codex reverifies. **A phase is incomplete until its required notebook is scientifically sound, visually clear, documented, privacy-safe, and successfully validated**, in addition to its code and report gates. The human researcher retains final phase approval.
