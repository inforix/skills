# Source Note Template

Use this template for notes in `sources/`. Keep sections that matter for the source; delete empty sections rather than filling them with placeholders.

```markdown
---
type: source
title: "Source Title"
source_kind: "url | pdf | docx | markdown | text | other"
source: "URL or absolute file path"
author: ""
published: ""
ingested: "YYYY-MM-DD"
tags:
  - reading
---

# Source Title

## Gist

One concise paragraph explaining what this source says and why it matters.

## Key Claims

- Claim: ...
  Evidence: ...
  Notes: ...

## Structure

- Section or argument step: ...

## Important Details

- Definitions, numbers, names, dates, examples, mechanisms, or constraints that future notes may need.

## Cases And Source Provenance

| Case | Role in source | Best original source | Local saved copy | Confidence | Notes |
| --- | --- | --- | --- | --- | --- |
| Case name | Evidence/example/counterexample | URL or citation | `raw/cases/source-slug/file.ext` | high/medium/low/unresolved | What was verified, downloaded, or still missing |

- Unresolved case searches:
  - Case: ...
    Searched: queries, cited references, official sites, archives, databases.
    Result: why no reliable source was saved.

## Interpretation

- What follows if this source is right?
- What is strong, weak, missing, surprising, or transferable?
- What should be compared with other sources?

## Connections

- Topics: [[Topic Name]]
- Entities: [[Entity Name]]
- Related sources: [[Other Source Note]]

## Questions

- ...

## Quotes

> Short quote only when the exact wording matters.

## Source Handling

- Raw capture: [[../raw/file-name]]
- Case materials: [[../raw/cases/source-slug]]
- Access notes: paywall, extraction issue, missing figures, unavailable URL, or verification needs.
```

## Naming

Use stable, readable filenames:

```text
sources/YYYY-MM-DD-short-title.md
topics/topic-name.md
entities/entity-name.md
questions/question-slug.md
```

Run this for a slug:

```bash
node read-article/scripts/reader-vault.mjs slug "Source Title"
```
