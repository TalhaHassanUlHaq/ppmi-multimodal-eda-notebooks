# Gemini implementation specification: dataset-selection and prioritization gate

Status: authorized by the human researcher on 2026-11-12 after Phase 1 approval. This specification authorizes the evidence and presentation work needed for file selection. It does **not** authorize detailed clinical, biomarker, genetic, molecular, imaging, or sensor EDA.

## 1. Objective and scientific rationale

Convert the approved Phase 1 structural inventory into a complete, auditable file-selection evidence package for all 177 source files. The purpose is to identify which sources warrant detailed modality-specific EDA, which are needed only for cohorting, joins, scoring, quality control, or interpretation, which are unsuitable for independent detailed EDA, and which require documentation or researcher judgment. Selection must prioritize scientific value without treating missingness, small samples, or filename similarity as automatic exclusion criteria.

The gate has two steps. First, Gemini assembles and validates the evidence matrix without inventing clinical definitions or final decisions. Second, Codex reviews the evidence and records file-level recommendations; Gemini then renders those recommendations for human approval. Detailed Phase 2/3 analysis may begin only after the researcher approves the resulting lists.

## 2. Inputs and required documentation

Use the approved Phase 1 artifacts as the canonical structural inputs:

- `EDA/outputs/reports/phase1_multimodal_inventory.json`
- `EDA/outputs/reports/phase1_schema_catalog.json`
- `EDA/outputs/reports/phase1_grain_catalog.json`
- `EDA/outputs/reports/phase1_repeated_event_keys_report.md`
- `EDA/outputs/reports/phase1_external_references_manifest.json`
- `EDA/outputs/reports/phase1_project_artifacts_manifest.json`
- `00_dataset_overview.ipynb`
- locally present PPMI methods documents, data dictionaries, workbook information/dictionary sheets, and other documentation already inventoried in Phase 1.

Reconcile every selection row to the canonical relative path and SHA-256. For workbooks whose sheets have distinct scientific roles, include both a file-level recommendation and sheet-level evidence/decision fields. Record the exact documentation path, version/date, page, section, sheet, or dictionary field supporting each verified scientific interpretation. If no adequate definition is available, state `Definition not verified`; do not infer meaning from a filename or header alone.

## 3. Evidence fields and validation rules

Create one canonical matrix row per source file, plus linked sheet-level rows where applicable. Preserve exact paths and filenames. At minimum include:

- canonical relative path, filename, modality/folder, format, SHA-256, physical-read status;
- rows, columns, worksheet count, observation grain and whether grain is verified or provisional;
- participant coverage numerator and denominator, visit/event coverage, longitudinal visit count/range, and the scope of each calculation;
- null-key counts, duplicate-key evidence, exact duplicate rows, parser/read warnings, schema/documentation coverage, and relevant quality concerns;
- clinical/scientific relevance, information content, longitudinal usefulness, interpretability, redundancy evidence, and multimodal-integration value, each recorded separately rather than collapsed into an opaque score;
- exact candidate duplicate or superseding source when redundancy is proposed, with hash/schema/content evidence and a clear distinction between byte-identical, schema-overlapping, and scientifically overlapping files;
- proposed category: `Primary EDA`, `Supporting`, `Excluded from detailed EDA`, or `Needs Review`;
- concise file-specific rationale, uncertainty, required follow-up documentation, and proposed target notebook(s).

Use transparent ordinal evidence labels such as `High`, `Moderate`, `Low`, `Unknown`, accompanied by the underlying aggregate evidence. Do not create a weighted total score that silently determines selection. A source with high missingness or low participant count may still be Primary EDA when scientifically important. An exclusion recommendation requires an affirmative reason such as verified administrative content, unreadable/empty structure with no scientific payload, an obsolete/byte-identical duplicate, or content outside the approved EDA questions. No file is permanently deleted or removed from provenance.

All raw sources remain read-only. Do not merge participant-level tables. Do not export participant IDs, values, dates, free text, small identifiable cells, or example records. Apply the approved privacy guard to all generated artifacts and notebook outputs.

## 4. Required calculations and review summaries

Compute privacy-safe aggregate evidence for each file and modality:

- participant and visit coverage using explicit eligible denominators;
- baseline versus longitudinal record coverage, number of distinct scheduled/unscheduled event codes, and follow-up depth where valid;
- structural missingness and variable usability summaries without applying undocumented global sentinels;
- key completeness, duplicate-key multiplicity, and unresolved grain flags;
- documentation coverage: verified definitions, partially documented fields, and unverified definitions;
- pairwise redundancy candidates using hashes, normalized literal schema overlap, row/column dimensions, source version/name evidence, and—only within the authorized local environment—privacy-safe aggregate content comparisons;
- cross-modal join potential based on verified identifiers and event/time fields, without performing joins;
- counts and percentages by proposed category, modality, grain, documentation status, and target notebook.

Every denominator must be named. Flag apparent conflicts between curated cuts and source-domain files rather than assuming one is authoritative. Separate local data presence from externally referenced availability.

## 5. Required notebook presentation

Version `00_dataset_overview.ipynb` for the selection gate without discarding or rewriting the approved Phase 1 audit evidence. Add a clearly labeled **Dataset Selection Gate** section that:

1. explains the seven selection criteria and the four categories;
2. displays an accessible complete 177-file evidence/decision matrix, with sheet-level detail where needed;
3. summarizes proposed categories by modality and target notebook using aggregate tables and only nonredundant figures;
4. lists every `Needs Review` item and the exact question requiring researcher input;
5. presents separate proposed Primary EDA and Supporting lists for Phase 2 clinical domains, Phase 3 biospecimen, and Phase 3 genetics/molecular work;
6. lists every proposed exclusion with a file-specific reason and evidence;
7. states that recommendations are provisional until human approval and records the approved decision/version only after that approval.

The notebook must use explanatory Markdown, compute totals from canonical artifacts, preserve the complete Phase 1 inventory/schema access, execute from a clean kernel, and contain no clinical-result plots or participant-level values. A machine-readable matrix and Markdown review report are supporting artifacts, not substitutes for the notebook.

## 6. Expected outputs

- versioned, executed `00_dataset_overview.ipynb` with the complete selection-gate section;
- `EDA/outputs/reports/dataset_selection_matrix.json` containing all file/sheet evidence and provisional recommendations;
- `EDA/outputs/reports/dataset_selection_matrix.csv` containing privacy-safe flattened evidence for human review;
- `EDA/outputs/reports/dataset_selection_report.md` summarizing criteria, modality recommendations, exclusions, needs-review questions, limitations, and approval status;
- `docs/dataset_selection_decisions.md` as the versioned human/Codex decision record;
- automated tests and a formal Gemini implementation report naming commands, counts, discrepancies, and privacy validation.

Before Codex supplies reviewed recommendations, Gemini may populate `proposed_category` only as `Needs Review — Codex recommendation pending`, while fully populating objective evidence fields. Gemini must not independently finalize clinical selection judgments.

## 7. Automated tests

Test that:

- the matrix contains exactly the canonical 177 paths with no missing or extra sources and matching hashes;
- all source files retain a decision row and all applicable workbook sheets retain linked evidence;
- category values are restricted to the four approved labels or the explicit pre-review pending state;
- no high-missingness, low-coverage, small-sample, `(1)` filename, or filename-only heuristic can automatically force exclusion;
- every proposed exclusion has a nonempty file-specific reason and evidence reference;
- every redundancy claim identifies the comparator and evidence type;
- category totals reconcile globally and by modality, and notebook/report/matrix totals agree;
- all evidence denominators and audit scopes are populated or explicitly unknown;
- raw-file hashes remain unchanged;
- privacy guard rejects identifier-bearing/nested synthetic payloads and accepts the generated aggregate artifacts;
- the notebook executes top to bottom from a clean kernel and its saved outputs contain the complete matrix with no participant-level disclosure.

## 8. Acceptance criteria and approval gate

The selection evidence package is ready for Codex review when all 177 sources reconcile, every row has complete structural evidence or an explicit unknown, documentation provenance is specific, redundancy/exclusion claims are evidenced, all outputs agree, tests pass, and the notebook is cleanly executed and privacy-safe.

Codex then reviews every recommendation, issues corrections, and records one of the four proposed categories with rationale. Gemini implements any corrections and regenerates the package. The human researcher must explicitly approve the final Primary EDA, Supporting, Excluded-from-detailed-EDA, and Needs Review lists. Only that approval authorizes Gemini to implement the detailed Phase 2 and Phase 3 notebooks.

## 9. Limitations and prohibited operations

- No detailed EDA, score computation, cohort modeling, clinical association, biomarker comparison, genetic analysis, or longitudinal trajectory analysis in this gate.
- No participant-level exports or AI-visible records.
- No automatic permanent exclusion, deletion, source modification, or silent deduplication.
- No undocumented variable definitions, score directions, assay units, genetic interpretations, or causal claims.
- No unchecked joins, and no claim that common `PATNO`/`EVENT_ID` columns alone establish scientifically valid integration.
- Do not begin `eda_clinical.ipynb`, `eda_biospecimen.ipynb`, or `eda_genetics.ipynb` until the final selection lists are explicitly approved.
