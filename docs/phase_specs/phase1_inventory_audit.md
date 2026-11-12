# Gemini implementation specification: Phase 1 correction and completion

Status: assigned Phase 1 only, issued by Codex on 2026-11-12 following independent review. Gemini implements and reports; Codex reverifies. No selection gate or detailed EDA work is authorized by this specification.

## 1. Objective and rationale

Produce a reproducible, source-only multimodal inventory and structural audit that can support a scientifically defensible later selection review. Establish what is physically local, what is only referenced externally, what each tabular unit represents, and whether keys can support future integration. Do not claim a modality or biomarker is available merely from folder names.

## 2. Inputs and documentation

Inventory all files in the 17 named folders in `PipelineConfig.domain_folders`, preserving exact relative paths and filenames. Separately inventory study methods and reference documents, project code, generated artifacts, and external references. Read the curated workbook's `20260810`, `Data dictionary`, and `Information` sheets and both sheets of the rs-fMRI workbook for structure. Detect macOS `._` sidecars explicitly. Use local methods PDFs/DOCX and the workbook dictionary as candidate documentation, recording version, source, and field coverage. Do not treat generated local manuals or prose assertions as verified official definitions. List documentation gaps.

## 3. Validation and preprocessing rules

- Open raw sources read-only. Record format, bytes, modification metadata and preferably a content hash in a privacy-safe manifest. Reconcile manifest paths to physical files and state which are failed or unreadable.
- For CSV, parse records with a CSV-aware reader. Count logical records correctly when quoted fields contain newlines or the last record lacks a newline. Record encoding, delimiter, parser failures, and whether row/statistics audits are full-file or sampled.
- Preserve every literal original header in order, including whitespace and duplicate/blank names. Report any pandas aliases separately. Do not silently convert headers or infer clinical definitions from them.
- For each sheet/table, report dimensions, identifiers present, aggregate participant and visit coverage with explicit denominators, null-key counts, duplicate rows, duplicate candidate keys, and unresolved grain. Check candidate key uniqueness on the full data or label it provisional.
- Treat missingness as source- and variable-specific. Record blanks, parser nulls, documented sentinels, and structurally inapplicable values separately. Do not apply the global `-1` or `999` assumptions without documentation.
- Explicitly separate local files from remote references and cite the document supporting each remote claim. Never export participant IDs, record values, dates of birth, or participant-level examples.

## 4. Required structural calculations

Compute totals by source/document/generated class, folder, format, modality, physical availability, audit status, and source version. For each tabular unit, compute exact or clearly scoped row and column counts, aggregate distinct participant and visit counts, multiplicity of candidate keys, null-key counts, and duplicate-row counts. Demonstrate join-cardinality checks on synthetic fixtures, including null keys, one-to-one, one-to-many, many-to-one, and many-to-many cases. Do not merge PPMI data in Phase 1.

## 5. Presentation and required notebook

Gemini must create and execute `00_dataset_overview.ipynb` as the final Phase 1 research deliverable. Its title and introduction explain the inventory question and source universe. Display a complete source manifest and accessible per-table/per-sheet structural schema catalog, followed by objectives, provenance, availability, quality and grain assessments, computed aggregate summaries, interpretation, limitations, and conclusions about **audit readiness only**. Show denominators and scope for each count; label file selection pending. Use explanatory Markdown beside code. A compact inventory report remains a supporting artifact. Figures are optional for Phase 1 and must only visualize aggregate file/format/availability counts if used, with labels, captions and denominators. Do not plot clinical values or start detailed EDA.

## 6. Outputs

Gemini should deliver the executed `00_dataset_overview.ipynb`, a source-only machine-readable file manifest, per-sheet/tabular structural catalog, aggregate Phase 1 report, documentation provenance and availability table, reproducible clean-kernel run instructions and dependency versions, test results, and formal implementation report. The notebook must display its computed tables and any figures directly; external files do not substitute for those outputs. Keep generated outputs out of the next source scan. Clearly mark any provisional categories in old outputs as unapproved or remove them from the Phase 1 review package; defer scientific category assignment to the selection gate.

## 7. Automated tests

Use synthetic fixtures to test scope reconciliation, new generated files not changing source totals, literal/duplicate headers, quoted CSV newlines, no trailing newline, multiple workbook sheets, unreadable sidecars, full versus sampled key claims, null and duplicate join keys, rejection of many-to-many bypass, privacy leakage under arbitrary and nested keys, and raw-file immutability. Execute the notebook from a clean kernel in the documented environment and verify that saved cell outputs contain only approved aggregates/schema metadata, with no participant-level records or unredacted exceptions. Check that manifest and notebook totals agree and conclusions follow computed outputs. Run `pytest` with a workspace-local temporary directory and disabled cache if the environment restricts the system temp/cache paths. Report all commands and results.

## 8. Acceptance criteria

All 177 currently present source-folder files reconcile to the manifest, with no project artifacts counted as source; any count changes are explained. Every tabular source/sheet has schema and dimension status, grain/key evidence or a documented unresolved status. No asserted remote availability or clinical definition lacks provenance. All reports and saved notebook outputs contain only safe aggregates and metadata. Synthetic cardinality and privacy cases pass, and the full test suite passes in a writable temporary location. `00_dataset_overview.ipynb` runs top to bottom from a clean kernel, displays clear computed tables/figures, explains its methods and limitations, and has no hardcoded findings. Gemini supplies before/after evidence for every blocking review finding. Codex reviews the notebook's scientific and visual quality, rechecks the implementation, and then requests user sign-off for Phase 1; selection begins only after that approval.

## 9. Limitations and prohibited operations

No raw modification, participant-level reporting, silent deduplication, global undocumented sentinel conversion, unchecked many-to-many merge, automatic file exclusion, or detailed clinical/biomarker plotting. Do not change cohort definitions or advance phases. Sampling may inform provisional diagnostics but cannot certify complete coverage or key uniqueness.
