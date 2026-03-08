# MOS → Career Mapping File (Algorithm / External Table)

Use this when you build a **keyword/skill-based mapping** (e.g. MOS skills → career role keywords) in another platform and want to import the results into the Career Roadmap.

---

## File location (priority order)

1. **Env override:** `MOS_CAREER_MAPPING_PATH` (if set and file exists)
2. **Career Mapping folder:** `Career Mapping/mos_career_mapping.json` (repo root) — use this folder for your updated mapping files
3. **MOS Mapping folder:** `Career Roadmap/MOS Mapping/mos_career_mapping.json`
4. **MOS Mapping pipeline output:** `Career Roadmap/MOS Mapping/output/mos_career_mapping.json` (after running `main.py`)
5. **App data:** `app/data/mos_career_mapping.json`
- If no file is found or it’s empty, the app falls back to curated paths and then AI.

---

## Format

Single JSON object: keys are **MOS codes** (uppercase), values are **arrays of career options**.

```json
{
  "11B": [
    {
      "industry": "Technology",
      "entry_role": "SOC Analyst I",
      "career_field": "Cybersecurity",
      "demand_level": "High",
      "salary_range": "$55,000 - $78,000",
      "path_id": "combat_to_cybersec",
      "match_keywords": ["security", "risk assessment", "operations"],
      "match_score": 0.92
    }
  ],
  "25B": [
    {
      "industry": "Technology",
      "entry_role": "Network Administrator",
      "career_field": "Information Technology",
      "demand_level": "High",
      "salary_range": "$60,000 - $85,000",
      "path_id": "signal_to_it",
      "match_keywords": ["networking", "systems", "troubleshooting"],
      "match_score": 0.88
    }
  ]
}
```

### Required per option

| Field | Type | Description |
|-------|------|-------------|
| `industry` | string | Civilian industry (e.g. "Technology", "Healthcare") |
| `entry_role` | string | Entry-level job title |
| `career_field` | string | Broader career field (e.g. "Cybersecurity", "Supply Chain") |

### Optional per option

| Field | Type | Description |
|-------|------|-------------|
| `demand_level` | string | "High", "Medium", or "Low" |
| `salary_range` | string | e.g. "$50,000 - $65,000" |
| `path_id` | string | If this maps to a curated path, use its `path_id` so the full roadmap can use that path |
| `match_keywords` | string[] | Keywords that linked MOS to this career (for transparency/debugging) |
| `match_score` | number | 0–1 score from your algorithm (for sorting/filtering) |

---

## How the app uses it

1. **MOS options** (`GET /api/v1/roadmap/mos/{code}/options`):
   - If `mos_career_mapping.json` exists and contains the MOS, those options are returned first (optionally filtered by `industry` query param).
   - If the mapping has no entry for the MOS, the app uses curated paths, then AI fallback.

2. **Roadmap generation** (when user picks an option):
   - If the chosen option includes a `path_id` that exists in the curated paths, the full roadmap uses that path’s milestones.
   - If there is no matching `path_id`, the app can still generate a roadmap (e.g. via AI) using `industry` and `entry_role`.

---

## Building the mapping in another platform

1. **Sources for MOS skills / job scope**
   - O*NET Military Crosswalk (MOS → civilian occupations)
   - Service MOS manuals or official job descriptions
   - Your own skill tags or descriptions per MOS

2. **Sources for career role keywords**
   - O*NET job descriptions and skills
   - Job postings or labor data (BLS, job boards)
   - Curated list of industries and entry roles

3. **Algorithm ideas**
   - Extract keywords from MOS description/skills (TF-IDF, simple tokenization, or NLP).
   - Extract keywords from career roles/industries.
   - Match via keyword overlap, cosine similarity, or embedding similarity.
   - Output one row per (MOS, career_option) with optional `match_score` and `match_keywords`.

4. **Export**
   - Produce a JSON object: `{ "MOS_CODE": [ { "industry", "entry_role", "career_field", ... }, ... ], ... }`.
   - Save as `app/data/mos_career_mapping.json` (or configure the path in the app and copy the file there).

---

## Example: minimal CSV to convert to JSON

If you build the table in a spreadsheet or CSV:

| mos_code | industry   | entry_role           | career_field      | demand_level | salary_range        | path_id           |
|----------|------------|----------------------|-------------------|--------------|---------------------|-------------------|
| 11B      | Technology | SOC Analyst I        | Cybersecurity     | High         | $55,000 - $78,000   | combat_to_cybersec |
| 25B      | Technology | Network Administrator| Information Technology | High    | $60,000 - $85,000   | signal_to_it      |

Convert to the JSON format above (group rows by `mos_code` into arrays of options).
