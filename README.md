# Personal Finance Dashboard (Gmail Transaction Alerts)

Reads bank/card transaction-alert emails from Gmail, parses them into
structured transactions, stores them in Postgres, and shows them on a
Streamlit dashboard.

## What data is stored, and where

- Everything (transactions, raw email snippets, your Gmail OAuth token) is
  stored **only** in your local Postgres database and local token file.
  Nothing is sent to any third-party server — this app only talks to the
  Gmail API (Google's own servers, over HTTPS) and your local database.
- The app only ever requests the `gmail.readonly` scope: it can read email,
  but can never send, delete, label, or modify anything in your Gmail
  account.
- `.env`, `credentials.json`, and `token.json` are git-ignored from the
  first commit — never commit them.

## Project structure

```
account_dashboard/
├── app/
│   ├── config/          # settings.py (.env loader), filters.py (sender/subject/category rules)
│   ├── gmail_client/     # OAuth2 flow (auth.py) + Gmail API fetch (fetch.py)
│   ├── parsers/          # one file per bank (hdfc.py, icici.py, axis.py) + generic.py fallback
│   ├── db/               # SQLAlchemy models, session/engine, create-tables script
│   ├── ingestion/        # fetch -> parse -> dedupe -> insert pipeline (CLI)
│   ├── categorize/       # rule-based keyword categorization
│   └── dashboard/        # Streamlit app: Home (Overview), pages/Transactions, pages/Settings
├── scripts/gmail_auth_test.py   # one-time OAuth smoke test
├── tests/                        # pytest — parsers + ingestion
├── requirements.txt
├── .env.example
├── docker-compose.yml     # optional: local Postgres via Docker
└── .gitignore
```

## 1. Prerequisites

- Python 3.11+ (tested with 3.14)
- PostgreSQL, either:
  - a native local install (what these instructions assume), or
  - Docker + `docker compose up -d` using the provided `docker-compose.yml`
- A Google account (the one whose transaction emails you want to read)

## 2. Google Cloud OAuth setup (one-time, do this yourself)

Google requires you to create your own OAuth client — this app cannot
create one on your behalf.

1. Go to **console.cloud.google.com** and sign in with the Google account
   you want the dashboard to read email from.
2. Click the project dropdown (top left, next to "Google Cloud") →
   **New Project**. Name it e.g. `finance-dashboard` → **Create**. Wait for
   it to finish, then select it in the project dropdown.
3. In the left sidebar (or top search bar), go to **APIs & Services** →
   **Library**. Search for **Gmail API** → click it → **Enable**.
4. Go to **APIs & Services** → **OAuth consent screen**.
   - User type: **External** (unless you have a Google Workspace org) →
     **Create**.
   - Fill in: App name (`Finance Dashboard`), User support email (yours),
     Developer contact email (yours) → **Save and Continue** through the
     remaining steps (Scopes, Test users — you can skip adding scopes here,
     the app requests them at login time).
   - On the **Test users** step, click **Add users** and add your own
     Gmail address. (While the app is in "Testing" status, only test users
     you list here can log in — that's fine, it's just you.)
   - Finish and go back to the dashboard.
5. Go to **APIs & Services** → **Credentials** → **Create Credentials** →
   **OAuth client ID**.
   - Application type: **Desktop app**.
   - Name: `Finance Dashboard Desktop`.
   - Click **Create**.
6. A dialog shows your client ID/secret — click **Download JSON**.
7. Rename the downloaded file to `credentials.json` and place it in the
   project root: `account_dashboard/credentials.json`. (It's already in
   `.gitignore` — never commit it.)

## 3. Postgres setup

You have two options — pick one.

**Option A — native Postgres already installed/running:**

```bash
psql -U postgres -c "CREATE ROLE finance_user LOGIN PASSWORD 'your_password_here';"
psql -U postgres -c "CREATE DATABASE finance_dashboard OWNER finance_user;"
```

**Option B — Docker:**

```bash
docker compose up -d
```

This starts Postgres with the user/db from your `.env` (see below) — no
manual `CREATE ROLE`/`CREATE DATABASE` needed.

## 4. Configure `.env`

```bash
cp .env.example .env
```

Edit `.env`:
- Set `POSTGRES_PASSWORD` / `DATABASE_URL` to match whatever you used in
  step 3.
- Leave the Gmail settings as-is unless you placed `credentials.json`
  somewhere other than the project root.

## 5. Install dependencies

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

## 6. Run it

```bash
# 1. Confirm Gmail OAuth works (opens a browser window to log in the first time)
python scripts/gmail_auth_test.py

# 2. Create the database tables
python -m app.db.init_db

# 3. Run the tests
pytest tests/ -v

# 4. Pull in your transaction emails
python -m app.ingestion.pipeline --max 200

# 5. Launch the dashboard
streamlit run app/dashboard/Home.py
```

Then open the URL Streamlit prints (usually `http://localhost:8501`). The
**Sync now** button in the sidebar re-runs step 4 from inside the UI.

## 7. Deploying to Streamlit Community Cloud (optional)

Running locally (steps 1–6) is the simplest and most private option — skip
this section unless you specifically want a hosted, browser-accessible
version.

**Why this needs different code than local:** the local OAuth flow works by
opening a browser *on the same machine* that's running the script, and
caches the token to a local file. Neither works on a hosted server — the
browser is on your laptop, the server is somewhere else, and a hosted app's
disk resets on every restart. So the hosted path uses a different (still
`gmail.readonly`-only) OAuth flow: you click **Connect Gmail** in the
sidebar, it redirects to Google, Google redirects back to the app's own
URL with an authorization code, and the resulting refresh token is stored
in Postgres instead of a local file. This is already built — you just need
to provision the pieces below.

1. **Cloud Postgres.** Streamlit Cloud can't reach a database on your own
   machine. Create a free Postgres instance yourself — e.g. at
   **neon.tech** or **supabase.com** (sign up, create a project, copy the
   connection string). You'll need it in step 4.
2. **A second, "Web application" OAuth client.** The `credentials.json`
   from step 2 is a *Desktop app* client and only works for the local flow.
   In the same Google Cloud project:
   - **APIs & Services** → **Credentials** → **Create Credentials** →
     **OAuth client ID** → Application type: **Web application**.
   - Name it e.g. `Finance Dashboard Web`. Leave **Authorized redirect
     URIs** empty for now — you'll add it in step 5 once you know the
     app's URL. Click **Create**.
   - Note the **Client ID** and **Client secret** shown — you'll need both.
3. **Push this repo to GitHub** if you haven't already (`git push`).
4. **Deploy on Streamlit Cloud.**
   - Go to **share.streamlit.io**, sign in with GitHub.
   - **New app** → pick this repo/branch → main file path:
     `app/dashboard/Home.py` → **Deploy**.
   - It will fail to fully load until secrets are set (next step) — that's
     expected.
5. **Add secrets.** In the app's **Settings** → **Secrets**, paste (see
   `.streamlit/secrets.toml.example` for the template):
   ```toml
   DATABASE_URL = "postgresql+psycopg2://user:password@host:5432/dbname?sslmode=require"
   GMAIL_CLIENT_ID = "...apps.googleusercontent.com"
   GMAIL_CLIENT_SECRET = "..."
   REDIRECT_URI = "https://your-app-name.streamlit.app"
   ```
   Use the DB connection string from step 1, and the Web client ID/secret
   from step 2. `REDIRECT_URI` is the URL Streamlit Cloud assigned your app
   (visible in the app's address bar / settings once deployed).
6. **Register the redirect URI with Google.** Go back to the Web OAuth
   client from step 2 → **Authorized redirect URIs** → add the exact same
   `REDIRECT_URI` value → **Save**.
7. **Create the tables once.** From your local machine, with `DATABASE_URL`
   in `.env` pointed at the *cloud* Postgres instead of your local one, run
   `python -m app.db.init_db`.
8. Reload the deployed app. Click **Connect Gmail** in the sidebar, approve
   read-only access, and you'll land back on the dashboard connected. Use
   **Sync now** to pull transactions.

## Adding a new bank

The filter list and parsers are designed to grow over time without
touching existing code:

1. Add the bank's alert-email sender address to `SENDER_FILTERS` in
   `app/config/filters.py`.
2. Copy `app/parsers/hdfc.py` to `app/parsers/<bank>.py` and adjust the
   regex to match that bank's email format.
3. Register the new parser in `app/parsers/registry.py`'s `PARSERS` list
   (order matters — more specific parsers should come before generic).
4. Add a test in `tests/test_parsers.py` using a real (sanitized) sample
   email string from that bank.

The in-app **Settings** page shows the currently active filters and
category keywords for reference.

## Security notes

- Logs and the dashboard never print full raw email bodies to shared
  output — only parsed, structured fields.
- The OAuth token (`token.json`) is cached locally after first login; it
  is not encrypted at rest by default. If you want it encrypted, the
  simplest approach is OS-level disk encryption (BitLocker/FileVault) —
  application-level encryption wasn't judged worth the added complexity
  for a single-user local tool, but ask if you'd like it added.
