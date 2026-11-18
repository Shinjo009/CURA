# Medical content files

Each `*.json` file is a list of passages. Outside development, Cura serves an entry only
if `review_status` is `reviewed` or `published`, it names a `reviewer` and a
`reviewed_on` date, and it is in date. Entries expire at most 12 months after review.

```json
[
  {
    "name": "ICMR",
    "title": "Vitamin D deficiency",
    "url": "https://...",
    "source_type": "guideline",
    "tier": 1,
    "topics": ["vitamin_d"],
    "keywords": ["vitamin d", "25-oh"],
    "excerpt": "Cura's own summary, or the exact source text",
    "content_kind": "cura_summary",
    "publication_date": "2025-03-01",
    "licence_status": "link_only",
    "region": "IN",
    "review_status": "published",
    "reviewer": "Dr A. Name",
    "reviewed_on": "2026-10-01",
    "expires_on": "2027-09-30"
  }
]
```

`content_kind` must be `quoted_passage` only for exact source text whose licence allows
quoting. Everything else is `cura_summary`, and Cura never presents it as the source's words.

## Markdown guides

A guide written as markdown goes in `markdown/` with a sidecar `<name>.meta.json` that holds the
review details and the topics and keywords for each numbered section. Sections listed in
`skip_sections` (for example the system instructions) are not served. Reviewer and review date are
only used to decide whether a passage may be served; they are never added to answers.
`cura_bio_ai_knowledge_base.md` is the Bio-AI guide. It is only retrieved for Bio-AI questions.
