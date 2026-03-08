# Set Up Supabase for the ERG Directory

Use the **single Supabase project labeled FOB**. The ERG tables live in the same project as your app data.

---

## Step 1: Open the FOB project

1. Go to [supabase.com](https://supabase.com) and sign in.
2. Open the project labeled **FOB** (the same project whose URL is in `REACT_APP_SUPABASE_URL` in `skillbridge-explorer/.env.local`).

---

## Step 2: Run the full schema (if not already done)

1. In the **left sidebar**, click **SQL Editor** → **New query**.
2. Open **`skillbridge-explorer/supabase/migrations/001_fob_full_schema.sql`** and copy **all** of its contents.
3. Paste into the query box and click **Run** (or Ctrl+Enter).
4. You should see **Success. No rows returned.** This creates all app tables plus **corporate_ergs** and **erg_submissions**.
6. If Supabase shows a warning about “destructive operation”, that’s normal (the script creates tables). Click **Run this query**.
7. You should see **Success. No rows returned.**

To confirm:

- Go to **Table Editor** in the sidebar.
- You should see **corporate_ergs** and **erg_submissions**. They will be empty until you load seed data.

---

## Step 3: Get the database connection string (for the API)

The **SkillBridge API** (FastAPI) needs a Postgres connection string to read/write ERG data in the same FOB database.

1. In the FOB project, click **Project settings** (gear) → **Database**.
3. Scroll to **Connection string**.
4. Choose the **URI** tab.
5. Copy the connection string. It will look like:
   - `postgresql://postgres.[project-ref]:[YOUR-PASSWORD]@aws-0-[region].pooler.supabase.com:6543/postgres`
6. Replace `[YOUR-PASSWORD]` with your **database password** (the one you set when creating the project).  
   If you forgot it, use **Reset database password** on the same Database settings page.
7. For the Python API we need the **async** driver. Change the start of the URL:
   - From: `postgresql://`
   - To: `postgresql+asyncpg://`  
   Example:
   - `postgresql+asyncpg://postgres.[YOUR_FOB_PROJECT_REF]:YOUR_PASSWORD@aws-0-us-east-1.pooler.supabase.com:6543/postgres`

---

## Step 4: Set DATABASE_URL in the API

1. In the `skillbridge-api` folder, create a `.env` file if you don’t have one (e.g. copy from `.env.example`).
2. Set or update **DATABASE_URL** to the Supabase connection string you built in Step 3:

   ```env
   DATABASE_URL=postgresql+asyncpg://postgres.[ref]:[YOUR-PASSWORD]@[host]:6543/postgres
   ```

3. Save the file.  
   **Important:** Don’t commit `.env` to git (it should be in `.gitignore`).

---

## Step 5: Load ERG seed data

With the API pointing at Supabase, load the 25 known ERGs (Amazon, Microsoft, JPMorgan, etc.):

1. Open a terminal.
2. Go to the API folder and activate the venv:

   **PowerShell (Windows):**

   ```powershell
   cd c:\Users\james\OneDrive\FOB\skillbridge-api
   .\venv\Scripts\Activate.ps1
   ```

3. Run the seed script:

   ```powershell
   python -m scripts.run_erg_scrape --seed
   ```

4. You should see something like: `Seed complete: inserted=25, updated=0`

---

## Step 6: Restart the API and test

1. Start (or restart) the API, e.g.:

   ```powershell
   uvicorn app.main:app --reload --port 8001
   ```

2. In the browser, open the app and go to **ERG Directory**. You should see the seeded companies.
3. Or call the API directly:
   - `http://localhost:8001/api/v1/ergs` — list ERGs
   - `http://localhost:8001/api/v1/ergs/stats` — stats

---

## Quick checklist

| Step | What you did |
|------|----------------------|
| 1 | Opened Supabase project |
| 2 | Ran `001_fob_full_schema.sql` in FOB project SQL Editor |
| 3 | Copied DB connection string and changed to `postgresql+asyncpg://...` |
| 4 | Set `DATABASE_URL` in `skillbridge-api/.env` |
| 5 | Ran `python -m scripts.run_erg_scrape --seed` |
| 6 | Restarted API and opened ERG Directory |

---

## Troubleshooting

- **503 on `/api/v1/ergs`**  
  The API can’t reach the database. Check that `DATABASE_URL` in `skillbridge-api/.env` is correct and uses `postgresql+asyncpg://`. Restart the API after changing `.env`.

- **“relation corporate_ergs does not exist”**  
  The migration wasn’t run or failed. Run `001_fob_full_schema.sql` in the FOB project SQL Editor and check for errors.

- **Seed script fails**  
  Confirm `DATABASE_URL` is set and the password in the URL is correct. Test the URL with a tool like psql or the Supabase SQL Editor (connected to the same project).

- **Frontend still shows no ERGs**  
  Ensure `REACT_APP_API_BASE` in the frontend points at your API (e.g. `http://localhost:8001`). The ERG Directory page reads from the API, which reads from Supabase.
