# Lab Assistant

Lab Assistant is an AI-powered research management tool designed to help scientists and researchers organize their projects, papers, notes, and experiments in one centralized platform. It leverages modern AI (OpenAI) and vector search capabilities to enhance productivity and knowledge retrieval.

I built this because I often found my experiments and runs getting disorganized and hard to track. I think this could be a useful tool for anyone working in a research environment.

## Features

- **Project Management**: Organize your research into distinct projects.
- **Paper Repository**: Upload and manage research papers (PDFs).
- **AI-Powered Analysis**: Extract insights and summaries from papers using OpenAI.
- **Notes & Experiments**: Keep detailed logs of your thoughts, hypotheses, and experimental runs.
- **Vector Search**: Semantic search capabilities powered by `pgvector` to find relevant information across your knowledge base.

## RAG & AI Architecture

The project uses a Retrieval-Augmented Generation (RAG) pipeline to allow users to "chat" with their research papers.

1.  **Ingestion & Chunking**:
    *   When a PDF is uploaded, its text is extracted using `PyMuPDF`.
    *   The text is split into manageable chunks (e.g., paragraphs or fixed-size windows) to ensure semantic relevance.

2.  **Embedding Generation**:
    *   Each text chunk is passed to the OpenAI Embeddings API (e.g., `text-embedding-3-small`) to generate a vector representation.
    *   These vectors are stored in the PostgreSQL database using the `pgvector` extension.

3.  **Semantic Search (Retrieval)**:
    *   When you ask a question, your query is also embedded into a vector.
    *   The system performs a cosine similarity search in the database to find the text chunks most relevant to your question.

4.  **Answer Generation**:
    *   The relevant text chunks are fed into an LLM (OpenAI gpt-4o-mini) as "context".
    *   The LLM generates an answer based strictly on the provided context, ensuring grounded and accurate responses with citations.

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL with `pgvector` extension
- **ORM**: SQLAlchemy
- **Migrations**: Alembic
- **AI/LLM**: OpenAI API
- **Frontend**: React, TailwindCSS, Vite

## Getting Started

### Prerequisites

- Python 3.10+
- Docker & Docker Compose (for the database)

### Docker Setup (Recommended)

1.  **Clone the repository**
    ```bash
    git clone <repository-url>
    cd lab-assistant
    ```

2.  **Environment Configuration**
    Create a `.env` file in the `backend` directory. You can copy the example:
    ```bash
    cp backend/.env.example backend/.env
    ```
    Ensure your `backend/.env` contains the necessary keys (OpenAI, Database credentials).
    
    *Note: The `docker-compose.yml` uses `backend/.env.local` by default if it exists, otherwise it falls back to `.env`.*

3.  **Start the Application**
    Run the following command to build and start both the backend and database containers:
    ```bash
    docker-compose up --build
    ```
    
    The API will be available at `http://localhost:8000`.
    The Database will be available on port `5432`.

### Manual Backend Setup

1.  **Start the Database**
    The project uses a Dockerized PostgreSQL instance with the `pgvector` extension.
    ```bash
    docker-compose up -d
    ```

2.  **Navigate to the Backend Directory**
    ```bash
    cd backend
    ```

3.  **Create and Activate a Virtual Environment**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
    ```

4.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Environment Configuration**
    Create a `.env` file in the `backend` directory. You can copy the example:
    ```bash
    cp backend/.env.example backend/.env
    ```
    **Important**: If running manually (not via Docker), update `DATABASE_URL` to use `localhost` instead of `db`.

    *Example `.env` for Manual Run:*
    ```env
    # Database Credentials
    POSTGRES_USER=ai_lab_username
    POSTGRES_PASSWORD=ai_lab_password_1
    POSTGRES_DB=ai_lab

    # Consumed by the backend (Note: @localhost)
    DATABASE_URL=postgresql+psycopg2://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:5432/${POSTGRES_DB}
    
    OPENAI_API_KEY=your_openai_api_key_here
    ```

6.  **Run Database Migrations**
    Apply the database schema:
    ```bash
    alembic upgrade head
    ```

7.  **Start the Backend Server**
    ```bash
    uvicorn app.main:app --reload
    ```
    The API will be available at `http://localhost:8000`.
    You can view the interactive API documentation at `http://localhost:8000/docs`.

### Frontend Setup

1.  **Navigate to the Frontend Directory**
    ```bash
    cd frontend
    ```

2.  **Install Dependencies**
    ```bash
    npm install
    ```

3.  **Environment Configuration**
    Create a `.env.local` file in the `frontend` directory with the following variables:
    
    ```env
    VITE_API_BASE=http://localhost:8000
    # Add Supabase credentials if required for authentication/features:
    # VITE_SUPABASE_URL=your_supabase_url
    # VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
    ```

4.  **Start the Development Server**
    ```bash
    npm run dev
    ```
    The application will be available at `http://localhost:5173`.


