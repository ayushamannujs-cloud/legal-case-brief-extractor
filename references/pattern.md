# Case Brief & Definition Patterns

Annotated examples for the shapes used in `pending_cases.md` and `data.json`.

## Case brief — full template

```markdown
### K.V. Prakash Babu v. State of Karnataka, (2017) 11 SCC 176
**Description:**
Fact: The case involved allegations of mental cruelty under Section 498-A IPC, specifically related to the husband's extra-marital relationship.

Judgement: The Court stated that mental cruelty depends on the milieu and strata of the persons involved and is an individualistic perception. Extra-marital relationship per se does not constitute criminal cruelty under Section 498-A unless other ingredients are met.

Principle 1: Mental cruelty must be such that it is likely to drive the woman to commit suicide.
Principle 2: Coercive harassment can have attributes of cruelty under Section 498-A.
Principle 3: Extra-marital relationship is illegal/immoral but not automatically a criminal offense under 498-A without additional evidence of cruelty.
Principle 4: 'Wilful conduct' contemplates obstinate and deliberate behaviour; mens rea is an essential ingredient.

---
```

Things to notice:

- The title is `Name v. Party, Citation` — comma before the citation, citation in parentheses or brackets exactly as it appears in the source.
- `Fact:` is singular and ends with a colon, on its own paragraph.
- `Judgement:` (British spelling — matches existing data).
- Principles are numbered `Principle 1:`, `Principle 2:` etc. Use a colon. Don't switch to dashes mid-list.
- Blank lines separate Fact / Judgement / Principles for readability inside the JSON description.
- The `---` divider closes the block; the next entry starts with another `###`.

## Case brief — sparse source

When the source text doesn't give you full facts or multiple principles, write what's there and stop. Don't pad.

```markdown
### Ram Das v. State of West Bengal, AIR 1954 SC 711
**Description:**
Fact: Male removed his trouser before lying down in the train; allegation of looking at women with "lustful eyes".

Judgement: The Court considered this a normal act before lying down on the berth; the allegation of lustful eyes was more psychological than factual. Not tenable.

---
```

Single Judgement, no numbered principles — fine.

## Statutory definition — template

```markdown
### Section 86 BNS: Definition of Cruelty
**Description:**
'Cruelty' means:
a) Any wilful conduct which is of such a nature as is likely to drive the woman to commit suicide or to cause grave injury or danger to life, limb or health (whether mental or physical) of the woman; or
b) Harassment of the woman where such harassment is with a view to coercing her or any person related to her to meet any unlawful demand for any property or valuable security or is on account of failure by her or any person related to her to meet such demand.

---
```

- No Fact/Judgement scaffold — just the definition prose.
- Title format: `Section <N> <Code>: <Short label>` or `Sec. <N>: <Short label>` to match existing data conventions.

## Combined / commentary entry

Sometimes the user gives commentary that spans two sections or compares cases. Capture as a single entry with a descriptive title — but only if forcing it into the case-brief shape would be awkward.

```markdown
### Section 85 & 86 BNS: Cruelty
**Description:**
Under The Bharatiya Nyaya Sanhita, the 498A provision has been divided into two. Section 85 concerns the Offence of Cruelty and Section 86 concerns the definition of Cruelty. Whoever, being the husband or the relative of the husband of a woman, subjects such woman to cruelty shall be punished with imprisonment for a term which may extend to three years and shall also be liable to fine.

---
```

## `pending_cases.md` file shape

The file always starts with this header, kept intact across runs:

```markdown
# Pending Terminologies and Case Briefs

Review and edit the following entries. Once you are satisfied, tell me "Sync the cases" to add them to your terminology tracker.

---
```

Each entry is then `### Title` + `**Description:**` + body + `---`. The sync script parses on these markers exactly.

## Anti-patterns (don't do these)

- ❌ Title without citation (`### Arnesh Kumar case`) — always include the citation if known.
- ❌ Bullet points for principles (`- Principle: ...`) — use `Principle N: ...`.
- ❌ Markdown bold/italic inside the description body — the description ends up as a plain string in `data.json`.
- ❌ Inventing principles or facts that weren't in the source.
- ❌ Writing multiple cases under one `###` header — one heading per legal unit.
