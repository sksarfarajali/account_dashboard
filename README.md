# Personal Finance Dashboard (Gmail Transaction Alerts)

Reads bank/card transaction-alert emails from Gmail, parses them into
structured transactions, stores them in Postgres, and shows them on a
Streamlit dashboard. Read-only Gmail access; nothing leaves your machine.

## Project structure

```
account_dashboard/
├── app/
│   ├── config/          # settings loader (.env) + configurable filters/category keywords
│   ├── gmail_client/     # OAuth2 flow + Gmail API fetch (gmail.readonly only)
│   ├── parsers/          # one file per bank/sender; each extracts amount/type/date/etc.
│   ├── db/               # SQLAlchemy models, session/engine, create-tables script
│   ├── ingestion/        # fetch -> parse -> dedupe -> insert pipeline (CLI)
│   ├── categorize/       # rule-based keyword categorization
│   └── dashboard/        # Streamlit app: Overview / Transactions / Settings pages
├── scripts/               # one-off scripts (e.g. Gmail auth smoke test)
├── tests/                 # pytest tests (parsers first)
├── requirements.txt
├── .env.example
├── docker-compose.yml     # local Postgres
└── .gitignore
```

## Status

**Step 1 complete:** project scaffold, `requirements.txt`, `.env.example`,
`.gitignore`, `docker-compose.yml`. Dependencies verified installable in a
local virtualenv (Python 3.14).

Remaining build steps (see build order): Gmail OAuth smoke-test script,
DB models, first parser + test, ingestion CLI, dashboard pages, README
setup instructions.

## Security & privacy

- Only the `gmail.readonly` OAuth scope is requested — this app can read
  email but never send, delete, or modify anything in your Gmail account.
- `.env`, `credentials.json`, and `token.json` are git-ignored from the
  first commit and must never be committed.
- No transaction data, email content, or credentials are sent to any
  third-party server — everything is stored in your local Postgres
  container.
- Logs must never contain full email bodies, account numbers, or amounts
  (enforced in later steps).

## Setup

Full setup instructions (Google Cloud OAuth project creation, Postgres,
running the app) will be added at the end of the build, once every piece
is working.
