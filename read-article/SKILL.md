---
name: read-article
description: Read, interpret, and file articles, papers, reports, web URLs, Obsidian notes, Markdown, PDF, DOCX, HTML, plain text, or other user-provided reading material into the local Obsidian reader vault. Use when the user asks to read an article, explain a URL/file, summarize a document, extract arguments, build reading notes, compare with prior readings, or maintain a persistent personal reading wiki.
---

# Read Article

## Overview

Use this skill to turn a user-supplied source into durable reading notes in the local Obsidian `reader` vault. Treat the vault as a persistent wiki: raw sources remain stable, while summary, topic, entity, and question pages compound over time.

## Reader Vault

Default vault discovery order:

1. `READER_VAULT_PATH`
2. Obsidian registry entry whose path ends in `/reader`
3. `/Users/wyp/Library/Mobile Documents/iCloud~md~obsidian/Documents/reader`

Use the helper before writing:

```bash
node read-article/scripts/reader-vault.mjs path
node read-article/scripts/reader-vault.mjs init
```

Expected vault structure:

```text
raw/          immutable source captures or copied files
raw/cases/    downloaded source material for cases mentioned by readings
sources/      one note per ingested source
topics/       evolving concept/theme pages
entities/     people, organizations, products, places, projects
questions/    durable answers to user questions worth keeping
assets/       local images or attachments when needed
index.md      content-oriented map of the wiki
log.md        append-only chronological activity log
AGENTS.md     reader-vault operating conventions
```

## Workflow

1. Resolve and preserve the source.
   - For a URL, browse or fetch the current page. Save a Markdown/text capture under `raw/` when useful for reproducibility.
   - For a local file, read it with the appropriate tool. Copy only if the user wants the reader vault to keep a raw copy.
   - For PDFs, DOCX files, images, or pages with important figures, inspect visual content when it affects interpretation.
2. Read for argument, not just summary.
   - Identify thesis, claims, evidence, assumptions, definitions, method, examples, implications, and open questions.
   - Distinguish the source's claims from your interpretation.
   - Preserve important citations, numbers, dates, and direct quotes sparingly.
3. Trace and preserve case sources.
   - Extract every substantive case, example, company, project, incident, dataset, law, paper, or report that the source relies on.
   - Search for the best available original source for each case. Prefer primary sources, official pages, papers, reports, datasets, legal filings, archived pages, or the cited source over secondary summaries.
   - Download or capture found case materials under `raw/cases/<source-slug>/` whenever access allows. Preserve PDFs, HTML/text captures, datasets, images, and citation pages with stable filenames.
   - Record each case in the source note with original URL, local saved path, source type, access date, and confidence. If a case cannot be traced, mark it as unresolved and explain what was searched.
   - Read `references/case-source-handling.md` before doing case tracing.
4. Check the existing wiki before writing.
   - Read `index.md` first if it exists.
   - Search `sources/`, `topics/`, `entities/`, and `questions/` for overlapping concepts, authors, organizations, and claims.
   - Update existing pages when the new source changes or sharpens them; do not create near-duplicate topic pages.
5. Create or update the source note.
   - Use `references/source-note-template.md`.
   - Link to relevant topic/entity/question pages with Obsidian wiki links.
   - Include enough source metadata to re-open the original file or URL.
6. Maintain the wiki layer.
   - Update `index.md` with the new or changed pages.
   - Append one parseable entry to `log.md`.
   - Create topic/entity/question pages only when they help future retrieval or synthesis.
7. Answer the user.
   - Give a concise interpretation in chat.
   - Report the vault pages changed.
   - Surface uncertainties, missing access, paywalls, extraction failures, or places where the source needs human verification.

## Output Standards

Read `references/wiki-method.md` for the persistent-wiki model and `references/source-note-template.md` before writing source notes.
Read `references/case-source-handling.md` whenever the article includes examples or cases.

Every source note should include:

- title and source metadata
- one-paragraph gist
- key claims and supporting evidence
- interpretation and implications
- notable quotes or exact data, only when needed
- case/source provenance, including local downloads where available
- connections to existing wiki pages
- questions or follow-ups

Prefer clear, durable Markdown over long chat-only summaries. If the user asks only for an explanation and not filing, still offer the interpretation, but do not write to the vault unless the request implies durable notes.

## Commands

Create the vault structure:

```bash
node read-article/scripts/reader-vault.mjs init
```

Create a safe filename slug:

```bash
node read-article/scripts/reader-vault.mjs slug "The Article Title"
```

Append a log entry after changes:

```bash
node read-article/scripts/reader-vault.mjs log \
  --type ingest \
  --title "The Article Title" \
  --source "https://example.com/article" \
  --pages "sources/the-article-title.md, topics/example-topic.md"
```

Use `--dry-run` with `init` or `log` to preview without writing.
