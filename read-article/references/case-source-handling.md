# Case Source Handling

Use this reference whenever a reading source contains cases, examples, company stories, projects, events, datasets, legal or policy examples, research findings, benchmarks, or named incidents.

## Goal

Do not let cases remain as unsupported anecdotes. Trace them to the best available source and save what can be saved into the reader vault so later notes can inspect the evidence without rediscovering it.

## Extraction

While reading, make a case list with:

- exact name used in the source
- normalized name if different
- why the case matters to the author's argument
- any cited URL, footnote, paper title, organization, date, jurisdiction, dataset, or figure number
- claim that depends on the case

## Source Priority

Prefer sources in this order:

1. The source's cited URL, paper, report, dataset, filing, law, or official document.
2. Primary publisher or owner: official organization page, company blog, government page, standards body, court/agency filing, original dataset, conference paper, arXiv/DOI page.
3. Stable archival or bibliographic pages: Internet Archive, DOI resolver, publisher abstract, library catalog.
4. Reputable secondary source only when primary material is unavailable.

Avoid treating summaries, SEO pages, scraped copies, forum posts, or uncited reposts as original sources unless no better source can be found. If using a secondary source, label it clearly.

## Search Procedure

For each non-trivial case:

1. Start from citations and links in the original source.
2. Search exact phrases, names, titles, dates, and identifiers.
3. Search official domains when organizations are named.
4. Search scholarly or legal identifiers when available: DOI, arXiv id, case number, report number, dataset id.
5. If the current web is needed, browse and cite sources in the final answer when discussing web-derived facts.
6. Stop after a reasonable good-faith search, but record unresolved cases rather than silently dropping them.

## Save Downloads

Save case materials under:

```text
raw/cases/<source-slug>/
```

Use stable filenames:

```text
case-name--official-report.pdf
case-name--publisher-page.md
case-name--dataset.csv
case-name--archive-page.html
```

Download durable files when allowed:

```bash
curl -L --fail --show-error --output "<vault>/raw/cases/<source-slug>/<file-name>" "<url>"
```

For pages that are not clean downloads, save a Markdown or text capture with:

- title
- URL
- fetched/access date
- short excerpt or summary
- key metadata
- reason it supports the case

Do not bypass paywalls, login gates, robots restrictions, or access controls. Record the limitation instead.

## Record In The Source Note

Add or update `## Cases And Source Provenance` with one row per case:

- `Case`: normalized case name
- `Role in source`: evidence, analogy, counterexample, benchmark, historical example, etc.
- `Best original source`: URL or citation
- `Local saved copy`: path under `raw/cases/<source-slug>/`
- `Confidence`: high, medium, low, or unresolved
- `Notes`: what was verified, what remains uncertain, and why this source is credible

If a case cannot be sourced, include it under `Unresolved case searches` with searched queries and reason.
