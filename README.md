# ResearchNexus

ResearchNexus is an AI-powered research management platform for organizing projects, papers, experiments, and team collaboration. It features a RAG pipeline that lets you ask natural-language questions about your uploaded papers and get grounded answers with citations.

I built this because I often found my experiments and runs getting disorganized and hard to track. I think this could be a useful tool for anyone working in a research environment.

## Features

- **Project Management** — Create projects, invite team members via shareable links, and manage roles (owner/member).
- **Paper Repository** — Upload PDFs with automatic text extraction, metadata parsing, and section identification via LLM.
- **AI-Powered Q&A** — Ask questions about individual papers or across an entire project. Answers are grounded in your documents with citations.
- **Experiment Tracking** — Log experiments with goals, protocols, and results. Track individual runs with JSON config (hyperparameters, seeds) and metrics (accuracy, loss, F1).
- **Notes** — Attach notes to projects, papers, experiments, or specific runs.
- **Team Collaboration** — Invite members to projects with invite codes, manage membership, and share research context.
- **Authentication** — Email/password and Google OAuth via Supabase.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 19, TypeScript, Vite, Tailwind CSS 4 |
| Backend | FastAPI, SQLAlchemy, Alembic |
| Database | PostgreSQL 16 with pgvector |
| Auth | Supabase (JWT, Google OAuth with PKCE) |
| AI | OpenAI gpt-4o-mini (answers + extraction), text-embedding-3-small (embeddings) |
| PDF Processing | PyMuPDF |
| Deployment | Vercel (frontend), Docker (backend + database) |

## RAG Pipeline

When a PDF is uploaded, the following pipeline runs:

1. **Text Extraction** — PyMuPDF extracts all text with page offsets.
2. **LLM Metadata Extraction** — OpenAI extracts title, abstract, and document section boundaries (Abstract, Methods, Results, etc.) from the text.
3. **Chunking** — Text is split into ~400-token chunks respecting section boundaries, with 50-token overlap between chunks.
4. **Embedding** — Each chunk is embedded with `text-embedding-3-small` (1536 dimensions) and stored in PostgreSQL via pgvector.

When you ask a question:

1. The question is embedded into a vector.
2. Cosine similarity search finds the most relevant chunks.
3. Those chunks are passed as context to gpt-4o-mini with a system prompt that enforces grounded answers with quotes.
4. The answer and cited sources are returned.

Q&A works at the paper level (`/papers/{id}/qa`) or across an entire project (`/projects/{id}/qa`).

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- A [Supabase](https://supabase.com) project (for authentication)
- An [OpenAI API key](https://platform.openai.com)

### 1. Clone the Repository

```bash
git clone <repository-url>
cd lab-assistant
```

### 2. Backend Setup

#### With Docker (recommended)

Create your backend environment file:

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` and fill in your credentials:

```env
DATABASE_URL=postgresql+psycopg2://ai_lab_username:ai_lab_password_1@db:5432/ai_lab

SUPABASE_URL=https://your-project.supabase.co
SUPABASE_JWT_SECRET=your_supabase_jwt_secret
SUPABASE_JWT_ALGORITHM=ES256

OPENAI_API_KEY=sk-...

CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

Start the database and backend:

```bash
docker-compose up --build
```

The API will be at `http://localhost:8000` and interactive docs at `http://localhost:8000/docs`.

#### Manual Setup

Start just the database with Docker:

```bash
docker-compose up -d db
```

Then set up the backend manually:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and change the `DATABASE_URL` host from `db` to `localhost`:

```env
DATABASE_URL=postgresql+psycopg2://ai_lab_username:ai_lab_password_1@localhost:5432/ai_lab
```

Run migrations and start the server:

```bash
alembic upgrade head
uvicorn app.main:app --reload
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

Create `frontend/.env.local`:

```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
VITE_API_BASE=http://localhost:8000
```

Start the dev server:

```bash
npm run dev
```

The app will be at `http://localhost:5173`.

### 4. Supabase Configuration

In your Supabase project dashboard:

1. Enable **Email/Password** auth under Authentication > Providers.
2. Enable **Google OAuth** under Authentication > Providers > Google, and add your Google client ID and secret.
3. Add your app URL (`http://localhost:5173`) to the allowed redirect URLs under Authentication > URL Configuration.

## API Endpoints

### Projects

| Method | Endpoint | Description |
|---|---|---|
| GET | `/projects` | List projects (owned + member of) |
| POST | `/projects` | Create project |
| GET | `/projects/{id}` | Get project |
| PATCH | `/projects/{id}` | Update project (owner only) |
| DELETE | `/projects/{id}` | Delete project (owner only) |
| POST | `/projects/{id}/qa` | Ask question across project |

### Project Members & Invites

| Method | Endpoint | Description |
|---|---|---|
| GET | `/projects/{id}/members` | List members |
| DELETE | `/projects/{id}/members/{user_id}` | Remove member |
| POST | `/projects/{id}/invites` | Generate invite code (owner only) |
| GET | `/projects/{id}/invites` | List active invites (owner only) |
| DELETE | `/projects/{id}/invites/{invite_id}` | Revoke invite (owner only) |
| POST | `/projects/join` | Join project via invite code |

### Papers

| Method | Endpoint | Description |
|---|---|---|
| POST | `/papers/upload` | Upload PDF |
| GET | `/papers` | List papers |
| GET | `/papers/{id}` | Get paper |
| PATCH | `/papers/{id}` | Update paper |
| DELETE | `/papers/{id}` | Delete paper |
| POST | `/papers/{id}/index` | Index paper for RAG |
| POST | `/papers/{id}/qa` | Ask question about paper |

### Experiments & Runs

| Method | Endpoint | Description |
|---|---|---|
| POST | `/projects/{project_id}/experiments` | Create experiment |
| GET | `/projects/{project_id}/experiments` | List experiments in project |
| GET | `/experiments/{id}` | Get experiment |
| PATCH | `/experiments/{id}` | Update experiment |
| DELETE | `/experiments/{id}` | Delete experiment |
| POST | `/experiments/{experiment_id}/runs` | Create run |
| GET | `/experiments/{experiment_id}/runs` | List runs |
| GET | `/runs/{id}` | Get run |
| PATCH | `/runs/{id}` | Update run |
| DELETE | `/runs/{id}` | Delete run |

### Notes

| Method | Endpoint | Description |
|---|---|---|
| POST | `/notes` | Create note |
| GET | `/notes` | List notes (filterable by project, paper, experiment, run) |
| PATCH | `/notes/{id}` | Update note |
| DELETE | `/notes/{id}` | Delete note |

## Project Structure

```
lab-assistant/
├── frontend/
│   ├── src/
│   │   ├── pages/          # Login, Dashboard, ProjectDetail, Papers,
│   │   │                   # PaperDetail, Experiments, ExperimentDetail,
│   │   │                   # Settings, JoinProject
│   │   ├── components/     # Layout, ProtectedRoute, Notes, ui/
│   │   ├── context/        # AuthContext (Supabase auth state)
│   │   ├── lib/            # supabase.ts, api-service.ts
│   │   └── types/          # TypeScript interfaces
│   ├── vercel.json         # Vercel SPA rewrite config
│   └── package.json
├── backend/
│   ├── app/
│   │   ├── api/routes/     # projects, papers, experiments, notes
│   │   ├── models/         # SQLAlchemy models (User, Project, Paper,
│   │   │                   # Experiment, ExperimentRun, Note, Chunk,
│   │   │                   # ProjectMember, ProjectInvite)
│   │   ├── schemas/        # Pydantic request/response models
│   │   ├── services/       # rag, embedding, pdf_extractor, llm_extractor
│   │   ├── core/config.py  # Settings from env vars
│   │   ├── deps.py         # Auth (JWT verification) & DB session
│   │   ├── db.py           # SQLAlchemy engine setup
│   │   └── main.py         # FastAPI app with CORS
│   ├── alembic/            # Database migrations
│   ├── tests/              # Pytest test suite
│   ├── Dockerfile
│   └── requirements.txt
└── docker-compose.yml      # PostgreSQL (pgvector) + Backend
```

## License

See [LICENSE](LICENSE).
