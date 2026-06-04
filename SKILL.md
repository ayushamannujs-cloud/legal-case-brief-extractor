---
name: case-brief-extractor
description: Extracts structured legal terminology and case briefs from unstructured legal text and syncs them into the Terminology Tracker knowledge graph at `/Users/ayushaman/Terminology tracker/`. Use this skill whenever the user pastes raw legal text, statute commentary, case digests, or judgment summaries and wants them captured as terminologies or case briefs — even if they don't explicitly mention the tracker. Also trigger when the user says "extract these cases", "add these to my tracker", "sync the cases", "draft pending cases", references `pending_cases.md`, asks to update `server/data.json`, or mentions sections of the BNS / IPC / case law that should be saved. Handles the full Markdown-Mediated Synchronization workflow: extraction → write `pending_cases.md` for user review → on the "Sync the cases" directive, parse the reviewed Markdown, assign UUIDs, append to `server/data.json`, and auto-create graph connections between cases and their parent statutes.
---

# Case Brief Extractor

A workflow skill for the **Terminology Tracker** legal knowledge graph at `/Users/ayushaman/Terminology tracker/`. The project stores legal terminologies and case briefs in `server/data.json` and visualizes them as a graph. This skill is the disciplined pipeline for getting raw legal text into that database without breaking the patterns that already exist there.

## Why this skill exists

The user works with messy legal source material (textbook prose, judgment paragraphs, lecture notes) and wants it captured into a structured database. Doing this by hand is slow and error-prone; doing it without a review step risks polluting the database with hallucinated or misformatted entries. The skill enforces a two-stage workflow:

1. **Extract → `pending_cases.md`** so the user can eyeball and fix things in any text editor.
2. **Sync → `server/data.json`** only after the user explicitly approves.

Never skip the review stage. Never write straight to `data.json` on first pass, even if the user seems impatient — the whole point is to keep humans in the loop.

## When to use this skill

Trigger on inputs like:

- "Here's some text on Section X of the BNS, extract the cases."
- "Draft pending cases for these paragraphs."
- "Add *Arnesh Kumar v. State of Bihar* to my tracker."
- "Update `pending_cases.md` with these."
- "Sync the cases" / "Sync pending cases" / "Push these to the database" — this is the second-stage trigger that means "the markdown file is ready, write it to data.json now."

If the user just asks a legal question without wanting anything saved, don't trigger.

## Project layout (what lives where)

```
/Users/ayushaman/Terminology tracker/
├── pending_cases.md         # Staging area — Claude writes here, user edits here
├── server/
│   ├── data.json            # The actual database
│   └── index.js             # Express server (reference for schema)
└── client/                  # Frontend (graph UI)
```

The mount path under bash is `/sessions/compassionate-relaxed-ptolemy/mnt/Terminology tracker/` — use absolute paths and translate accordingly when running scripts.

## Data schema (the contract)

`server/data.json` is a single object:

```json
{
  "terminologies": [
    { "id": "<uuid-v4>", "title": "...", "description": "...", "isImportant": false }
  ],
  "connections": [
    { "sourceId": "<uuid>", "targetId": "<uuid>" }
  ]
}
```

Rules that come from `server/index.js` and existing entries:

- `id` is a UUID v4. Generate one per new entry — never reuse an existing one.
- `title` and `description` are required strings.
- `isImportant` is optional (boolean). Set `true` for landmark cases and central definitions; leave `false`/omit for ancillary entries. Match the convention in existing rows when in doubt.
- Connections are undirected in spirit — the server treats `(A,B)` and `(B,A)` as the same edge — but you should still write each one only once.

## Case brief pattern (use this exact shape)

Existing entries in `data.json` follow a consistent shape. Stick to it so the graph view stays uniform.

**Title format:** `[Case Name] v. [Opposing Party], [Citation]`

Examples from existing data:
- `K.V. Prakash Babu v. State of Karnataka, (2017) 11 SCC 176`
- `Reema Aggarwal v. Anupam, (2004) 3 SCC 199`
- `Ram Das v. state of West Bengal [AIR 1954 SC 711],`

Use whichever citation format the source provides — SCC, AIR, neutral citation. Don't invent citations you don't have.

**Description structure (for case briefs):**

```
Fact: <one or two sentences on the facts/background>

Judgement: <the court's holding or analytical takeaway>

Principle 1: <first rule established>
Principle 2: <second rule>
...
```

Notes:
- Use singular `Fact:` (matches existing data — some entries say "Facts:" but new ones should follow the dominant pattern).
- `Principle N:` is the labelling style. Don't switch to bullets or "Holding:" — the rest of the dataset uses this.
- For purely definitional terminologies (statutes, doctrines), skip Fact/Judgement/Principle and just write a clean prose description.

## The workflow

### Stage 1 — Extract to `pending_cases.md`

When the user supplies raw text:

1. Read the existing `pending_cases.md` if it exists. If it has unsynced entries the user wants to keep, append; otherwise overwrite with a fresh header.
2. Identify each distinct unit in the source text:
   - **Statutory definitions** → one entry per section/sub-definition.
   - **Case laws** → one entry per case.
3. For each unit, write a section in this exact format:

```markdown
### <Title in the canonical form above>
**Description:**
<Either the definition prose, or the Fact/Judgement/Principle block.>

---
```

4. Keep the leading explainer block at the top so the user knows what to do:

```markdown
# Pending Terminologies and Case Briefs

Review and edit the following entries. Once you are satisfied, tell me "Sync the cases" to add them to your terminology tracker.

---
```

5. After writing, briefly summarise to the user what you extracted (count + titles) and remind them: *"Edit `pending_cases.md` as needed, then tell me 'Sync the cases' when ready."*

**Do not** invent facts, principles, or citations that aren't in the source text. If the source is thin, write a thin entry — the user can flesh it out during review. If a case is mentioned only by name without facts, either skip it or write a stub and flag it explicitly in your summary.

### Stage 2 — Sync to `data.json`

Trigger: the user says **"Sync the cases"** (or any close paraphrase — "sync pending", "push them in", "add them to the db").

Use the bundled script — it's the deterministic, reusable way to do this:

```bash
python3 "/sessions/compassionate-relaxed-ptolemy/mnt/skill_folder/case-brief-extractor/scripts/sync_cases.py" \
  --pending "/sessions/compassionate-relaxed-ptolemy/mnt/Terminology tracker/pending_cases.md" \
  --data "/sessions/compassionate-relaxed-ptolemy/mnt/Terminology tracker/server/data.json"
```

The script:
1. Backs up `data.json` to `data.json.bak` (so you can roll back).
2. Parses `### Title` / `**Description:**` blocks out of the markdown.
3. Skips entries whose title already exists in `data.json` (case-insensitive match) to avoid duplicates if the user re-syncs.
4. Assigns a fresh UUID v4 to each new entry.
5. Appends to `terminologies`.
6. Auto-creates connections — see "Graph connectivity" below.
7. Writes the file back with 2-space indentation (matches existing style).
8. Prints a summary: how many added, how many skipped as duplicates, how many connections created.

After the script runs, report the summary to the user. Offer to clear `pending_cases.md` (reset it to just the header) so the staging area is empty for the next batch — but only do it if they confirm, in case they want to keep the file as a record.

### Graph connectivity (auto-connections)

When syncing, the script looks for statute/case parentage and creates `connections` rows. The heuristic:

- For each newly added **case brief** entry, scan its description for statute references — patterns like `Section 85 BNS`, `498-A IPC`, `S. 75`, `section 63`, `Sec. 77`. For each statute reference, if a terminology with a matching title exists in `data.json`, create a connection.
- Also scan for cross-references to other case names already in the database (rough match on `<Name> v. <Other>`).
- Don't create duplicate edges. The server treats edges as undirected, so check both `(A,B)` and `(B,A)`.

This heuristic isn't perfect — when in doubt, the script logs the proposed connections and you can call attention to any that look wrong. The user can delete edges later in the UI.

## Working notes

**On consistency.** The existing `data.json` has some inconsistencies (trailing commas in titles, "Fact" vs "Facts", varied citation brackets). Don't try to fix old rows as part of this workflow — that's a separate cleanup task. Just make sure *new* rows follow the cleanest version of the pattern.

**On `isImportant`.** Looking at existing data: landmark cases (`Ram Das`, `Mrs. Rupan Deol Bajaj`, `Sakshi`) are flagged `true`; routine definitions are `false` or omitted. Use judgment — if the case is one of the famous handful that everyone cites in this area, mark it important.

**On large inputs.** If the user dumps a chapter's worth of text, don't try to extract everything into one massive `pending_cases.md`. Ask whether they want to scope to a particular section/topic first. Better to do focused batches with clear review.

**On the user's directive language.** "Sync the cases" is the canonical second-stage trigger but the user paraphrases. Treat any clear "the markdown looks good, push it" intent as the trigger. If unsure, ask once before running the script — it edits the canonical database.

## References

- `references/schema.md` — full schema notes with example rows from the existing database.
- `references/pattern.md` — annotated examples of well-formed case briefs and definitions.
- `scripts/sync_cases.py` — the parser + writer for Stage 2.
