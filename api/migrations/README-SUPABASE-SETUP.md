# Supabase setup — FOB project only

Use the **single Supabase project labeled FOB** for all app and ERG data. Run the full schema once, then point the API at the same database if you use it for the ERG directory.

---

## 1. Use the FOB project

1. Go to [https://supabase.com](https://supabase.com) and sign in.
2. Open the project labeled **FOB** (the same project whose URL you use in `REACT_APP_SUPABASE_URL` in the frontend).
3. All tables (profiles, saved data, corporate_ergs) live in this one project.

---

## 2. Run the full schema (if not already done)

The frontend repo has one combined migration for the FOB project:

- **File:** `skillbridge-explorer/supabase/migrations/001_fob_full_schema.sql`
- In the FOB project: **SQL Editor** → **New query** → paste the full file contents → **Run**.

This creates `profiles`, `saved_roadmaps`, `networking_roadmaps`, `saved_programs`, `benefits_progress`, `corporate_ergs`, `erg_submissions`, RLS, and triggers. If you already ran the older split migrations (`001_fob_schema.sql` and `001_corporate_ergs.sql`) on this project, you can skip this or run only the parts you're missing.

---

## 3. (Optional) Point the SkillBridge API at the FOB database

To have the API read/write ERG data in the same FOB database:

1. In the FOB project: **Project settings** (gear) → **Database**.
2. Copy the **Connection string** (URI), e.g. `postgresql://postgres.[ref]:[YOUR-PASSWORD]@aws-0-[region].pooler.supabase.com:6543/postgres`.
3. For the API, use the **async** driver: change `postgresql://` to `postgresql+asyncpg://`.
4. In `skillbridge-api/.env` set:
   - `DATABASE_URL=postgresql+asyncpg://postgres.[YOUR_FOB_REF]:[YOUR-PASSWORD]@[host]:6543/postgres`
5. Restart the API and run the ERG seed when ready:
   - From repo root: `cd skillbridge-api; py -m scripts.run_erg_scrape --seed`. If already in `skillbridge-api`: `py -m scripts.run_erg_scrape --seed`

---

## Quick reference

| Step              | Where (FOB project)       |
|-------------------|----------------------------|
| Open SQL Editor   | Left sidebar → SQL Editor  |
| Run full schema   | Paste `001_fob_full_schema.sql` → Run |
| Check tables      | Left sidebar → Table Editor |
| Get connection URI| Project settings → Database |
