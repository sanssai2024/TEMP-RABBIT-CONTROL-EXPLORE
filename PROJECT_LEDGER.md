# Project Ledger

## Current milestone

Milestone 5: First usable server-rendered TEMP_RABBIT flow

## Completed work

- Repository inspected and confirmed empty.
- Proposed V1 architecture and work packages defined.
- FastAPI foundation created with configuration, SQLAlchemy setup, and health endpoints.
- Initial smoke tests added for app boot and health route.
- Idea domain model created with SQLAlchemy enums for status and decision.
- Pydantic schemas added for validated idea creation and updates.
- Minimal repository/service boundary added to support idea creation logic.
- Persistence milestone implemented with `ideas`, `idea_processings`, and `idea_notes` models.
- Alembic configuration and migration scaffold added for reproducible schema management.
- AI processing milestone completed with CONTROL/EXPLORE prompt modules, a provider-isolated AI service, structured Pydantic output validation, and processing persistence.
- Tests added for valid, invalid, and failure-path AI processing behavior.
- Server-rendered Milestone 5 flow added for homepage, new idea submission, idea list/detail pages, notes, reprocessing, status updates, and processing history.
- Real OpenAI-compatible provider adapter added behind the AI service abstraction; browser tests inject fake providers.
- Successful processing history creation and current decision update now commit as one database transaction.
- Milestone 5 browser-flow tests added for page loading, submissions, failure preservation, retries, history, notes, status, escaping, and transaction state.

## Architecture

- Monolithic FastAPI app with modular package layout.
- Central configuration via pydantic-settings and environment variables.
- SQLAlchemy models now include relational history tracking for ideas, processings, and notes.
- Domain validation remains separated from persistence logic and is enforced at the model and service boundary.
- Flexible AI output remains stored in `idea_processings.structured_result_json` rather than normalized tables.
- AI provider logic is isolated behind a service boundary and mockable for testability.

## Important decisions

- V1 remains a single-user modular monolith rather than a multi-service system.
- AI provider logic is isolated behind a clean service layer so provider-specific logic is not spread across the app.
- Flexible AI output is intentionally stored in a processing-specific JSON blob to preserve historical runs.
- The normal product workflow does not hard-delete ideas; status-based states such as `DEAD`, `PARKED`, or archived equivalents are used instead.
- Database-level cascade delete remains as a low-level cleanup behavior for explicit physical deletion, but it is not part of normal V1 product behavior and should not be described as a preservation strategy.
- MySQL is the required TEMP_RABBIT development/runtime database and is configured through `DATABASE_URL`; missing configuration fails explicitly.
- Tests explicitly override the database with isolated SQLite; SQLite is not a runtime fallback.
- Structured output is final-validated with Pydantic even when the provider returns JSON-like data.

## Database changes

- Added the `ideas` table concept with status and decision enums.
- Added the `idea_processings` table and JSON payload field for historical AI results.
- Added the `idea_notes` table for user-authored records.
- Added Alembic initial migration files for schema reproduction.
- MySQL configuration is required through `DATABASE_URL` and environment variables; credentials are not hardcoded.
- `cryptography` is declared because PyMySQL may require it for MySQL `caching_sha2_password` or `sha256_password` authentication.

## Tests completed

- Health and root app identity smoke tests.
- Valid and invalid idea creation tests.
- Application of enum values and service creation logic.
- Persistence tests for multiple processing runs and notes.
- AI validation tests for valid/invalid output and failure handling.
- Milestone 5 browser-flow tests: 11 focused tests.
- Complete suite: 35 passed.

## Warning status

The pytest warning is a third-party deprecation warning from the Starlette/anyio test client stack:

`DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated...`

This is not caused by TEMP_RABBIT application code. No clean project-side fix is necessary at this stage beyond documenting the dependency warning.

Automated Milestone 5 browser flow is verified with 35 passing tests using isolated SQLite and fake AI providers. Live MySQL verification is pending because no local MySQL server, database, or credentials were configured. Live AI verification is pending because no live API key/provider request was used.

## Current blockers

- Local MySQL server credentials and database are not configured yet for live DB verification.
- Live AI API credentials are not configured yet; automated tests use mocked providers only.
- The browser flow is implemented and tested; live database and live AI verification remain pending.

## Milestone 5 status

- Code Status: COMPLETE
- Automated Browser Flow: VERIFIED
- Live MySQL: PENDING
- Live AI Provider: PENDING

No later milestone work was added.

## Visual reference refinement — 2026-09-13

- Resumed from the existing frontend rather than rebuilding it. The interrupted session had saved homepage connection/reflection markup and mascot gradient definitions; the matching stylesheet had not been written.
- Completed the reference-inspired styling in app/static/style.css: serif display headings, compact shared header and introduction, wider paired cards, softer blue CONTROL lighting, near-black ember EXPLORE surfaces, and restrained borders/shadows.
- Styled the QUESTIONS sphere and connecting lines, including a visible bridge between stacked mobile cards. Finished passive intention labels and reflection panels already present in the homepage template.
- Refined the existing rabbit placeholders with silver shading for CONTROL and a darker, sharper silhouette and warm rim light for EXPLORE. Slots support replacement artwork; production illustrated mascots remain pending.
- Preserved existing routes, form names, backend logic, database schema, persistence, configuration, tests, focus states, and reduced-motion handling.
- Complete existing suite rerun: 35 passed, 24 dependency deprecation warnings. Used the existing virtual environment with a process-only DEBUG=false override; no environment configuration files were modified.
- Reviewed headless Chrome screenshots with isolated SQLite sample data and FakeAIProvider: overview at 1440, 820, 390, and 320 pixels; new idea mobile, detail desktop/mobile, and idea list desktop captured. No horizontal document overflow was measured. Confirmed EXPLORE form preselection and displayed saved status.
- Updated screenshots are in .frontend-review/. Updated comparison notes are in .frontend-review/README.md. No live MySQL or live AI verification was performed in this visual-only pass.
- Git was not available and no .git directory was present in this checkout; current files were used as the source of truth.
