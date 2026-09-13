# TEMP_RABBIT

TEMP_RABBIT is a small AI-assisted idea triage application built for learning and practical use.

## Purpose

The app takes a raw idea, clarifies it, identifies the core question, extracts meaningful branches, and arrives at a decision such as NOW, LATER, or PARK. The goal is to support thinking without automatically generating new projects.

## Architecture

The project follows a clean modular monolith pattern:

- `app/main.py` contains the FastAPI app and route registration.
- `app/core/config.py` loads environment variables.
- `app/db/database.py` contains the SQLAlchemy engine and session factory.
- `app/api/routes/` holds HTTP endpoints.
- `app/services/` will hold AI and domain logic.
- `app/models/` and `app/schemas/` model the database and validated API structures.
- `app/templates/` and `app/static/` support the server-rendered UI.

## Stack

- Python
- FastAPI
- SQLAlchemy
- MySQL
- Jinja2
- Pydantic
- pytest

## Setup

1. Create a virtual environment:
   `python -m venv .venv`
2. Activate it:
   - Windows PowerShell: `.venv\Scripts\Activate.ps1`
   - Windows CMD: `.venv\Scripts\activate.bat`
3. Install dependencies:
   `python -m pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and update the values.

`DATABASE_URL` is required for the application. TEMP_RABBIT's real development/runtime database is MySQL, for example:

`DATABASE_URL=mysql+pymysql://<user>:<password>@localhost:3306/temp_rabbit`

Do not put real credentials in the repository. The application fails with an explicit setup message when `DATABASE_URL` is missing; it does not silently switch to SQLite.

The `cryptography` dependency is declared because PyMySQL may require it for MySQL `caching_sha2_password` or `sha256_password` authentication.

## Run

After configuring a reachable MySQL database and `.env`, start the browser app with:

`uvicorn app.main:app --reload`

Open `http://127.0.0.1:8000/` in a browser.

## Testing

`\.venv\Scripts\python -m pytest -q`

The automated suite explicitly overrides `DATABASE_URL` with isolated in-memory SQLite for browser and persistence tests. Automated AI tests use `FakeAIProvider`; they do not call a live provider.

## Current milestone

Milestone 5 code is complete: the server-rendered browser flow supports new ideas, CONTROL/EXPLORE processing, detail/history pages, notes, reprocessing, and status changes.

## Data safety policy

TEMP_RABBIT V1 does not expose a normal hard-delete workflow for ideas. The product-level removal mechanism is status-based, using values such as `DEAD` or `PARKED`/archived states rather than deleting the idea record itself.

This policy preserves processing history and notes as first-class product data. The database-level cascade delete is kept internally consistent for explicit physical deletion, but it is not part of the normal user workflow and must not be described as preservation-friendly behavior.

## Verification status

- Milestone 5 Code Status: COMPLETE
- Automated Browser Flow: VERIFIED, 35 tests passed
- Live MySQL: PENDING; no local MySQL server, database, or credentials were configured for this verification
- Live AI Provider: PENDING; no live AI API key/provider request was used

The 35 passing tests include browser route coverage, fake-AI submission and failure paths, history/reprocessing, notes, status updates, HTML escaping, and successful transaction state.

## Known warnings

The current pytest run emits a third-party deprecation warning from Starlette/anyio during the test client import path:

`DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated...`

This does not come from TEMP_RABBIT application code. It is a dependency-level warning in the test stack, and it does not require a project code change at this stage. The project continues to function as expected.

The current pytest run emits dependency-level deprecation warnings from Starlette/anyio and Starlette's multipart compatibility import. These warnings do not come from TEMP_RABBIT application code.
