# Curating Career Paths per MOS

The MOS → Career roadmap uses **curated data** when available; otherwise it falls back to AI.

**Alternative: keyword/skill-based mapping**  
If you build a **MOS skills → career keywords** mapping in another platform (e.g. Python, Excel, O*NET crosswalk), you can import the result as a JSON file. The app will use it before curated paths and AI. See **`mos_career_mapping_schema.md`** for the file format and how to generate the table. To give more users curated (consistent, vetted) career options, you can grow the list in two ways.

---

## Where the data lives

- **File:** `app/data/progression_paths.py`
- **Main list:** `CAREER_PROGRESSION_PATHS` — a Python list of path objects.
- **Indexes** (built automatically from that list):
  - `MOS_TO_PATHS`: `{ "11B": ["combat_to_cybersec"], "25B": ["signal_to_it"], ... }` — which path_ids apply to each MOS.
  - `INDUSTRY_TO_PATHS`: which path_ids apply to each target industry.
  - `PATH_BY_ID`: `{ "combat_to_cybersec": { ... path dict ... }, ... }`.

You **only** edit `CAREER_PROGRESSION_PATHS`. The indexes are rebuilt when the app loads.

---

## Option 1: Map more MOS codes to existing paths (fastest)

If a path already fits additional MOS codes (e.g. same career field), add those codes to `source_mos_codes` for that path.

**Example:** Add Army 19D and 19K to the combat → cybersecurity path (they’re already there). To add 11A (Infantry Officer):

1. Open `progression_paths.py`.
2. Find the path (e.g. `"path_id": "combat_to_cybersec"`).
3. Extend `source_mos_codes`:

```python
"source_mos_codes": ["11B", "11C", "19D", "19K", "0311", "0331", "0341", "11A"],
```

**Result:** Anyone entering 11A will see the same curated “Combat Arms → Cybersecurity Analyst” option.

Use the same idea for other paths: **logistics_to_supply_chain**, **signal_to_it**, **medic_to_healthcare**, **intel_to_data_analytics**. Check branch-specific MOS lists (Army 92 series, Navy ratings, etc.) and add codes that clearly fit the same transition.

---

## Option 2: Add new career paths

To add a **new** transition (e.g. “Avionics → Aerospace / Defense”), add a new object to `CAREER_PROGRESSION_PATHS` with this structure.

### Required path-level fields

| Field | Type | Example |
|-------|------|--------|
| `path_id` | string (unique) | `"avionics_to_aerospace"` |
| `path_name` | string | `"Avionics → Aerospace Technician"` |
| `source_mos_codes` | list[str] | `["15B", "15D", "2A5", "2A6", "AV"]` |
| `source_branches` | list[str] | `["army", "air_force", "navy"]` |
| `source_skill_tags` | list[str] | `["electronics", "maintenance", "troubleshooting"]` |
| `target_industry` | string | `"manufacturing"` or `"defense_contracting"` |
| `target_career_field` | string | `"aerospace"` |
| `target_soc_code` | string | O*NET SOC e.g. `"49-2091.00"` |
| `total_timeline_months` | int | `24` |
| `difficulty_rating` | int 1–5 | `2` |
| `demand_rating` | int 1–5 | `4` |
| `milestones` | list | See below |

### Milestones (required sequence)

Each path has a list of milestones in order. At least:

1. **origin** — Current military role (`phase: "origin"`). Include `skills_from_military`, `veteran_tip`.
2. **preparation** — Certs / training (`phase: "preparation"`). Include `certifications`, optional `skillbridge_programs`, `education`, `skills_required`, `advancement_criteria`.
3. **entry_role** — First civilian job (`phase: "entry_role"`). Include `salary_range_low`, `salary_range_high`, `employers`, `skills_required`.
4. **growth_role** — Mid-level (`phase: "growth_role"`). Same kind of fields.
5. **target_role** (and optionally **stretch_role**) — Goal role.

Copy an existing path (e.g. `combat_to_cybersec` or `signal_to_it`) and change path_id, path_name, source_mos_codes, target_*, and then adjust milestones (titles, descriptions, certs, employers, salaries) to match the new transition.

### Optional path-level fields

- `salary_ceiling`, `path_description`, `military_advantage_summary`
- `common_pitfalls`, `alternative_paths`, `related_communities`

---

## Current paths and MOS coverage (reference)

| path_id | Target | Example MOS codes |
|---------|--------|--------------------|
| combat_to_cybersec | Cybersecurity | 11B, 11C, 19D, 19K, 0311, 0331, 0341 |
| logistics_to_supply_chain | Supply chain / logistics | 92A, 92Y, 92W, 3043, 3051, LS, SK |
| signal_to_it | IT / networks | 25B, 25N, 25S, 25U, 0621, 0631, IT, CTN |
| medic_to_healthcare | Healthcare | 68W, 68C, 8404, HM |
| intel_to_data_analytics | Data / analytics | 35F, 35N, 35M, 0231, 0241, IS, CTI |

Adding more MOS codes to these (Option 1) is the quickest way to “curate a bigger list” per MOS. Adding new paths (Option 2) grows the number of **different** career directions available.

---

## Research tips

- **Army:** MOS list (e.g. 11 series, 25 series, 35 series, 68 series, 92 series).
- **Navy:** Ratings (e.g. IT, CTN, HM, LS, SK).
- **Marines:** MOC (e.g. 0311, 0621, 0231, 3043, 8404).
- **Air Force:** AFSC (e.g. 2A, 3D, 1N).
- **O*NET:** [onetcenter.org](https://www.onetcenter.org/) for SOC codes and role descriptions.
- **Military crosswalks:** DoD / service transition tools that map MOS/AFSC/rating to civilian occupations.

After editing `progression_paths.py`, restart the API so the new indexes (and paths) are loaded.
