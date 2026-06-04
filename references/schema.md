# Terminology Tracker Schema

The database is a single JSON file at `server/data.json` with two top-level arrays.

## `terminologies`

Each row is an object with:

| field         | type    | required | notes                                                                 |
|---------------|---------|----------|-----------------------------------------------------------------------|
| `id`          | string  | yes      | UUID v4, unique across the array.                                     |
| `title`       | string  | yes      | Display label. For cases use `Name v. Opposing Party, Citation`.       |
| `description` | string  | yes      | Free-form prose. Multi-line is fine — store actual newlines, not `\n`. |
| `isImportant` | boolean | no       | `true` for landmark / frequently-cited entries; absent or `false` otherwise. |

Example (definition):

```json
{
  "id": "64845d86-eef8-4c74-8d63-7659aa82e5fa",
  "title": "Section 129: Criminal Force",
  "description": "Whoever assaults or uses criminal force to any person otherwise than on grave\nand sudden provocation given by that person, shall be punished with imprisonment of either\ndescription for a term which may extend to three months, or with fine which may extend to\none thousand rupees, or with both"
}
```

Example (case, landmark):

```json
{
  "id": "27d988a3-441f-48fe-a6ec-c2f5a115ce88",
  "title": "Mrs. Rupan Deol Bajaj & Anr v. Kanwar Pal Singh Gill & Anr [AIR 1996 SC 309],",
  "description": "Fact: a superior rank police officer slapped the back of the complainant, an IAS Officer, in a party in a public place.\n\nJudgement:\nPrinciple 1- \"the ultimate test for ascertaining whether the modesty has been outraged is, in the action of the offender such as could be perceived as one which is capable of shocking the sense of decency of a woman\",\nPrinciple 2- whether there are any sexual overtones or not, if it affronts to the normal sense of feminine decency, then liable\n",
  "isImportant": true
}
```

## `connections`

Each row is an object with two UUID strings — both must refer to existing `terminologies.id` values.

| field      | type   | required | notes                                                  |
|------------|--------|----------|--------------------------------------------------------|
| `sourceId` | string | yes      | UUID of one endpoint.                                  |
| `targetId` | string | yes      | UUID of the other endpoint.                            |

The server treats `(A,B)` and `(B,A)` as the same edge — only one row per unordered pair.

Example:

```json
{ "sourceId": "64845d86-eef8-4c74-8d63-7659aa82e5fa", "targetId": "27d988a3-441f-48fe-a6ec-c2f5a115ce88" }
```

## File formatting

`data.json` is pretty-printed with 2-space indentation. Preserve that when writing — the sync script uses `indent=2`.

## Server reference

The Express server at `server/index.js` is the source of truth for validation rules:
- `POST /api/terminologies` requires `title` and `description`.
- `POST /api/connections` rejects edges to non-existent IDs and rejects duplicate edges (bi-directional check).
- `DELETE /api/terminologies/:id` cascades to remove any connections touching that ID.

The sync script mirrors these rules so direct file writes stay consistent with what the API would have produced.
