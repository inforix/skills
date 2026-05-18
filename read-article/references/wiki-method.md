# Persistent Reader Wiki Method

Use this reference when turning a file or URL into durable notes in the Obsidian `reader` vault.

## Core Model

The reader vault has three layers:

- `raw/`: source captures and source-adjacent files. Treat as source-of-truth material and avoid editing it after capture.
- wiki pages: LLM-maintained Markdown notes in `sources/`, `topics/`, `entities/`, and `questions/`.
- conventions: `AGENTS.md`, `index.md`, and `log.md` describe how the wiki is organized and what has changed.

The goal is compounding knowledge. Do not only summarize the current article. Integrate it with what is already in the vault by updating relevant pages, adding cross-links, and recording contradictions or refinements.

## Ingest Principles

- Read one source deeply before broadening.
- Extract claims, evidence, definitions, assumptions, methods, implications, and unresolved questions.
- Separate source claims from your analysis.
- Preserve exact quotes only when wording matters.
- Create fewer, stronger pages. Update existing topic/entity pages before adding new ones.
- Link aggressively but meaningfully with Obsidian wiki links, for example `[[AI agents]]`.
- Keep source notes stable enough that later answers can cite them.

## Page Types

### Source Notes

One note per article, paper, report, webpage, book chapter, or uploaded file. Use `references/source-note-template.md`.

### Topic Pages

Use for recurring concepts, themes, theories, methods, or debates. Topic pages should synthesize across sources and include links back to source notes.

### Entity Pages

Use for people, organizations, projects, products, standards, laws, and places that recur across sources.

### Question Pages

Use when a user asks a question whose answer should persist, especially comparisons, decisions, literature syntheses, or open research directions.

## Index And Log

`index.md` is content-oriented. Keep it useful for navigation:

- list pages by category
- include one-line summaries
- add or update entries after every ingest

`log.md` is chronological and append-only. Use headings that are easy to grep:

```markdown
## [YYYY-MM-DD] ingest | Article Title
```

Log entries should include source, pages changed, and one sentence describing what changed.

## Contradictions And Stale Claims

When a new source conflicts with an older page:

1. Do not silently overwrite the older claim.
2. Add a short note explaining the conflict.
3. Link both source notes.
4. If one source is newer or stronger, say why.
5. Add a follow-up question if the conflict cannot be resolved.

## User-Facing Answer

After updating the vault, answer in chat with:

- the core interpretation
- the most important caveats
- the pages created or updated
- any source access or extraction limitations
