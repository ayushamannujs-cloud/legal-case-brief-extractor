# Legal Case Brief Extractor

A human-in-the-loop pipeline for extracting structured Indian case briefs and statutory definitions from raw legal text — and syncing them into a JSON knowledge graph.

Built by [@ayushamannujs-cloud](https://github.com/ayushamannujs-cloud).

---

## The problem with building Indian legal datasets

Creating structured legal datasets by hand is slow and error-prone. Automated extraction with LLMs is fast but produces hallucinated citations, inconsistent structure, and entries that need verification anyway. Expensive annotation platforms (Label Studio, Prodigy) are overkill for a law student or small research team working on Indian law.

This pipeline takes a middle path: **LLM extracts, human reviews in plain markdown, deterministic script writes to the database.** No annotation platform. No hallucinations in the final dataset. Every entry is human-verified before it lands in the graph.

---

## How it works

**Stage 1 — Extract (Claude skill)**

Paste raw legal text — a judgment paragraph, a statute section, a textbook digest. The Claude skill (`SKILL.md`) extracts structured entries into `pending_cases.md` in a consistent format:

```markdown
### Arnesh Kumar v. State of Bihar, (2014) 8 SCC 273
**Description:**
Fact: Addressed mechanical arrests under Section 498-A IPC.

Judgement: Mandatory directions issued to police and Magistrates.

Principle 1: Police must not automatically arrest when 498-A is registered.
Principle 2: Arrest requires necessity check under Section 41 CrPC.
Principle 3: Magistrates must record satisfaction before authorising detention.

---
```

**Stage 2 — Review (you)**

Open `pending_cases.md` in any text editor. Fix what the model got wrong — wrong citations, missing principles, imprecise facts. Add or remove entries. This is the human gate.

**Stage 3 — Sync (deterministic script)**

```bash
python3 scripts/sync_cases.py \
    --pending pending_cases.md \
    --data data.json
```

The script:
- Backs up `data.json` to `data.json.bak`
- Parses every `### Title` / `**Description:**` block
- Skips entries already in the database (case-insensitive deduplication)
- Assigns a UUID v4 to each new entry
- Auto-creates connections between case briefs and the statutes they reference (heuristic: detects patterns like "Section 85 BNS", "498-A IPC", "S. 482")
- Reports exactly what was added, skipped, and connected
- Writes `data.json` with 2-space indentation

**Dry run before writing:**
```bash
python3 scripts/sync_cases.py --pending pending_cases.md --data data.json --dry-run
```

---

## Output format

`data.json` is a simple JSON knowledge graph:

```json
{
  "terminologies": [
    {
      "id": "uuid-v4",
      "title": "Arnesh Kumar v. State of Bihar, (2014) 8 SCC 273",
      "description": "Fact: ...\n\nJudgement: ...\n\nPrinciple 1: ...",
      "isImportant": true
    }
  ],
  "connections": [
    { "sourceId": "uuid-of-case", "targetId": "uuid-of-statute" }
  ]
}
```

Nodes are case briefs and statutory definitions. Edges connect cases to the statutes they interpret, restrict, or apply. The graph grows incrementally — run the pipeline as many times as you need.

---

## Use cases

**Legal AI training data**
Each case brief is a structured (facts, judgment, principles) triple extracted from a real Indian judgment — human-verified, consistently formatted. The statute-to-case connections provide relational ground truth for statute identification tasks.

**Legal knowledge graph construction**
The output JSON can feed any graph database or visualization tool. The connection heuristic auto-links cases to parent statutes, reducing manual graph-building work.

**Research dataset annotation**
The `--important` flag marks landmark cases. The `--dry-run` flag previews changes without writing. Together these make the pipeline usable in a team annotation setting.

---

## Case brief schema

Every case entry follows this structure — consistent across the entire dataset:

```
Title: [Case Name] v. [Party], [Citation]

Fact: One or two sentences on the background.

Judgement: The court's holding or key analytical takeaway.

Principle 1: First rule established.
Principle 2: Second rule.
(as many as the case warrants)
```

Statutory and doctrinal entries use plain prose descriptions instead.

---

## Requirements

```bash
pip install -r requirements.txt   # just standard library — no dependencies
```

The sync script uses only Python standard library (`uuid`, `json`, `re`, `pathlib`, `shutil`). No pip install needed for Stage 3.

The Claude skill (Stage 1) requires a Claude client that supports agent skills — Claude Code, Cowork, or compatible Claude API setup.

---

## What this is not

- Not a replacement for expert legal annotation — the human review stage is mandatory, not optional
- Not a full legal knowledge graph platform — it produces a JSON file, not a SPARQL endpoint
- Not jurisdiction-agnostic — the schema and extraction prompts are tuned for Indian law (BNS, IPC, CrPC, IEA, BNSS)

---

## Feedback and collaboration

If you're building Indian legal NLP datasets, working on legal knowledge graphs, or doing legal AI research — feedback and collaboration welcome. Open an issue or reach out.
