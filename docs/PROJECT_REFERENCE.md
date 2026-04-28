# Lab Assistant Project Reference

Generated: 2026-04-28

This document captures the current repository shape, runtime topology, deployment setup, and major application flows for future reference. It intentionally lists environment variable names only; local secret values from `.env` files are not copied here.

## Product Summary

Lab Assistant, currently branded in code as ResearchNexus, is an AI-assisted research workspace. Users authenticate with Supabase, create research projects, upload papers, ask grounded questions over indexed paper chunks, maintain notes, and track experiments plus experiment runs.

## Repository Map

```text
.
- README.md
- docker-compose.yml
- backend/
  - Dockerfile
  - requirements.txt
  - requirements-dev.txt
  - pytest.ini
  - alembic.ini
  - alembic/
    - env.py
    - versions/
  - app/
    - main.py
    - core/config.py
    - db.py
    - deps.py
    - api/routes/
    - models/
    - schemas/
    - services/
  - tests/
- frontend/
  - package.json
  - package-lock.json
  - next.config.ts
  - tsconfig.json
  - eslint.config.js
  - src/
    - app/
    - index.css
    - context/
    - lib/
    - views/
    - components/
    - types/
    - proxy.ts
- .github/workflows/backend-tests.yml
- plan.md
```

`plan.md` is currently untracked and contains an earlier Next.js migration plan. It was not modified while creating these docs.

## Runtime Topology

Local backend and database are Docker-centric:

- `docker-compose.yml` starts `backend` and `db`.
- `db` uses `pgvector/pgvector:pg16`, exposes `5432`, stores data in the named `pgdata` volume, and runs a `pg_isready` healthcheck.
- `backend` builds from `backend/Dockerfile`, exposes `8000`, waits for the database healthcheck, mounts `./backend/storage:/app/storage`, then runs `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}`.
- The frontend is not included in Docker Compose. It is run separately with Vite during development or built/deployed from `frontend/`.

Important Compose detail: `env_file: ./backend/${ENV_FILE:-.env}` defaults to `backend/.env`. It does not automatically pick `backend/.env.local` unless `ENV_FILE=.env.local` is set in the shell or root `.env`.

## Deployment And CI

Current deployment artifacts:

- Backend: `backend/Dockerfile` can deploy the FastAPI service on a container platform. There is no platform-specific production manifest in the repo beyond Docker and Compose.
- Database: local Compose uses `pgvector/pgvector:pg16`. A production deployment needs PostgreSQL with the `vector` extension enabled.
- Frontend: Next.js App Router app in `frontend/`. Vercel can auto-detect the Next.js framework. The previous Vite SPA rewrite file has been removed.
- CI: `.github/workflows/backend-tests.yml` runs on backend path changes to `main` and installs `requirements.txt` plus `requirements-dev.txt`, then runs `pytest --tb=short -q`.

Operational caveat: `frontend/next.config.ts` rewrites `/api/:path*` to `API_PROXY_TARGET` with the `/api` prefix stripped. In production, `API_PROXY_TARGET` should point at the deployed FastAPI origin.

## Environment Variables

Root `.env` currently provides Compose substitution values:

- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`

Backend settings are loaded by `backend/app/core/config.py` from `backend/.env`:

- Required by settings: `DATABASE_URL`, `MAX_UPLOAD_MB`
- Supabase auth: `SUPABASE_URL`, `SUPABASE_JWT_SECRET`, `SUPABASE_JWT_ALGORITHM`, `SUPABASE_JWT_PUBLIC_KEY`
- CORS: `CORS_ORIGINS`
- OpenAI: `OPENAI_API_KEY`, `OPENAI_MODEL`
- Worker knobs: `WORKER_POLL_INTERVAL`, `WORKER_MAX_RETRIES`
- Compose database values may also be present in backend env files: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`

Frontend env names:

- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `NEXT_PUBLIC_API_BASE`
- `API_PROXY_TARGET`

## Backend Architecture

The backend is a FastAPI app with sync SQLAlchemy sessions and async OpenAI service calls.

Entry points:

- `backend/app/main.py` creates the FastAPI app titled `ResearchNexus API`.
- CORS origins come from comma-separated `CORS_ORIGINS`; when absent, the API allows all origins.
- Routers are mounted without a global `/api` prefix.
- Health/basic endpoints: `GET /`, `GET /db-ping`.

Database:

- `backend/app/db.py` creates a SQLAlchemy engine from `DATABASE_URL` with `pool_pre_ping=True`.
- Alembic reads `settings.DATABASE_URL` in `backend/alembic/env.py`.
- Migration chain creates users, papers, notes, experiments, chunks with `pgvector`, projects, experiment runs, Supabase UID support, chunk citation metadata, project members, and invites.
- The `chunks.embedding` column uses `Vector(1536)`, matching OpenAI `text-embedding-3-small`.

Auth:

- `backend/app/deps.py` uses FastAPI `HTTPBearer`.
- Supabase JWTs are decoded with either `SUPABASE_JWT_SECRET` for HS256 or JWKS fetched from `${SUPABASE_URL}/auth/v1/.well-known/jwks.json` for asymmetric algorithms.
- Authenticated users are created or updated in the local `users` table on first valid request.
- Project access is checked through ownership or `project_members`.

Main models:

- `User`: local user row keyed by `supabase_uid` and unique email.
- `Project`: owner, name, description, timestamps, members, invites, papers, notes, experiments, chunks.
- `ProjectMember`: project/user membership with `owner` or `member` role.
- `ProjectInvite`: invite code, creator, optional expiration, active flag.
- `Paper`: uploaded paper metadata, extracted text, processing status/error fields, optional project.
- `Chunk`: source-linked text chunk with embedding, page/section/doc metadata, and optional links to paper/note/experiment/run.
- `Note`: project note optionally linked to a paper, experiment, or experiment run.
- `Experiment`: experiment group with goal, protocol, results, status, optional paper.
- `ExperimentRun`: individual run with status, JSON config, JSON metrics, timestamps.

API surface:

- `GET/POST /projects`, `GET/PATCH/DELETE /projects/{project_id}`
- `POST /projects/{project_id}/qa`
- `GET /projects/{project_id}/members`, `DELETE /projects/{project_id}/members/{user_id}`
- `POST/GET /projects/{project_id}/invites`, `DELETE /projects/{project_id}/invites/{invite_id}`
- `POST /projects/join`
- `POST /papers/upload`, `GET /papers`, `GET/PATCH/DELETE /papers/{paper_id}`
- `POST /papers/{paper_id}/index`, `POST /papers/{paper_id}/qa`
- `GET/POST /notes`, `PATCH/DELETE /notes/{note_id}`
- `POST/GET /projects/{project_id}/experiments`
- `GET/PATCH/DELETE /experiments/{experiment_id}`
- `POST/GET /experiments/{experiment_id}/runs`
- `GET/PATCH/DELETE /runs/{run_id}`

AI and RAG flow:

- PDF text extraction uses PyMuPDF in `backend/app/services/pdf_extractor.py`.
- Paper metadata extraction uses OpenAI structured output in `llm_extractor.py`.
- Section detection, token chunking, and embedding calls live in `embedding.py`.
- `rag.py` deletes old paper chunks, chunks extracted text, embeds with `text-embedding-3-small`, stores chunks, retrieves by cosine distance, and asks `OPENAI_MODEL` for grounded answers.
- Current upload flow extracts text, extracts metadata, parses sections, stores the paper, and indexes immediately. The `pdf_path` column and `backend/storage` volume exist, but current upload code does not persist PDF files.

Backend tests:

- `pytest.ini` targets `backend/tests`, enables `pytest-asyncio`, and collects coverage for `app`.
- Tests use in-memory SQLite with FastAPI dependency overrides for DB and auth.
- Current tests cover schema validation and the text truncation helper. They do not exercise PostgreSQL-specific `pgvector` behavior.

## Frontend Architecture

The frontend is a Next.js App Router app:

- React `19.2.0`
- React DOM `19.2.0`
- Next.js `16.x`
- Tailwind CSS `4.1.x`
- Supabase SSR helpers via `@supabase/ssr`
- Supabase JS `2.90.1`
- Lucide React icons
- TypeScript `5.9.x`

Scripts:

- `npm run dev` -> `next dev`
- `npm run build` -> `next build`
- `npm run lint` -> `eslint .`
- `npm run start` -> `next start`

Next API proxy:

- `/api/*` rewrites to `${API_PROXY_TARGET || "http://localhost:8000"}/*` with the `/api` prefix stripped.
- `NEXT_PUBLIC_API_BASE` defaults to `/api`.

Routing:

- `frontend/src/app/layout.tsx` wraps the app in `AuthProvider`.
- `frontend/src/app/(protected)/layout.tsx` wraps protected routes in `AuthGate` and `Layout`.
- `frontend/src/proxy.ts` performs Supabase cookie-aware redirects for protected routes when session cookies are available.
- `frontend/src/components/AuthGate.tsx` keeps a client-side auth guard for browser session state.
- `frontend/src/components/Layout.tsx` provides the authenticated shell and sidebar.

Route map:

- `/login` -> `app/login/page.tsx`
- `/` -> `app/(protected)/page.tsx`
- `/projects/[id]` -> `app/(protected)/projects/[id]/page.tsx`
- `/papers` -> `app/(protected)/papers/page.tsx`
- `/papers/[id]` -> `app/(protected)/papers/[id]/page.tsx`
- `/experiments` -> `app/(protected)/experiments/page.tsx`
- `/experiments/[id]` -> `app/(protected)/experiments/[id]/page.tsx`
- `/settings` -> `app/(protected)/settings/page.tsx`
- `/join/[code]` -> `app/(protected)/join/[code]/page.tsx`

Client data flow:

- `frontend/src/context/AuthContext.tsx` creates the Supabase session/user state, supports Google OAuth, email signup/signin, and signout.
- `frontend/src/lib/supabase.ts` creates a browser Supabase client from `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`.
- `frontend/src/lib/api-service.ts` is the primary typed API client. It reads the current Supabase session, attaches `Authorization: Bearer <token>`, handles JSON and `FormData`, and exposes grouped API helpers.
- `frontend/src/lib/api.ts` is a smaller `authenticatedFetch` helper using the same API base pattern; it appears secondary to `api-service.ts`.

Frontend notes:

- Screen components live under `frontend/src/views/` so `src/pages/` does not trigger the Next Pages Router.
- Every screen remains a client component because the current implementation uses hooks, browser navigation, modals, and browser APIs.
- Browser APIs currently used include `window.location.origin`, `navigator.clipboard`, `confirm`, `alert`, and `new Date(...).toLocale...`.
- Vite starter assets remain (`public/vite.svg`, `src/assets/react.svg`) but do not appear to be used.

## Common Commands

Local full backend/database:

```bash
docker-compose up --build
```

Manual backend:

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Backend tests:

```bash
cd backend
pip install -r requirements.txt -r requirements-dev.txt
pytest
```

Frontend:

```bash
cd frontend
npm install
npm run dev
npm run build
npm run lint
npm run start
```

## Known Gaps And Risks

- Frontend CI is not configured.
- Production API routing relies on `API_PROXY_TARGET` or direct `NEXT_PUBLIC_API_BASE` configuration pointing to a reachable backend.
- Backend Docker uses Python 3.12, while GitHub Actions tests use Python 3.11.
- Local tests use SQLite, so migrations and pgvector behavior require separate PostgreSQL verification.
- Compose's documented `.env.local` fallback in `README.md` does not match the actual `docker-compose.yml` behavior unless `ENV_FILE` is explicitly set.
- CORS must include `http://localhost:5173`, `http://localhost:3000`, and deployed frontend origins when credentials and Supabase bearer auth are used.
- PDF files are not currently stored despite `pdf_path`, `STORAGE_DIR`, and the storage volume existing.
