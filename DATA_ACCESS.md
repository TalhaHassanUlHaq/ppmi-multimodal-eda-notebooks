# Data access

This codebase does not redistribute PPMI data. Researchers must obtain authorized access through the official PPMI data portal and comply with the applicable data-use agreement.

Keep downloaded participant-level data outside Git. The repository ignore rules block common tabular, imaging, document, and generated-output formats as a defense in depth, but they do not replace a manual review before every commit.

Before publishing changes:

1. Inspect `git status` and `git diff --cached --stat`.
2. Confirm that only code, notebooks, tests, and non-sensitive documentation are staged.
3. Scan notebook outputs for participant identifiers or row-level records.
4. Never bypass the ignore rules to add PPMI source files.
