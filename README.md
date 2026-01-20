# Lab Assistant

Lab Assistant is an AI-powered research management tool designed to help scientists and researchers organize their projects, papers, notes, and experiments in one centralized platform. It leverages modern AI (OpenAI) and vector search capabilities to enhance productivity and knowledge retrieval.

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
    *   The relevant text chunks are fed into an LLM (OpenAI GPT-4/3.5) as "context".
    *   The LLM generates an answer based strictly on the provided context, ensuring grounded and accurate responses with citations.

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL with `pgvector` extension
- **ORM**: SQLAlchemy
- **Migrations**: Alembic
- **AI/LLM**: OpenAI API
- **Frontend**: React (in development)

## Getting Started

### Prerequisites

- Python 3.10+
- Docker & Docker Compose (for the database)

### Backend Setup

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
    Create a `.env` file in the `backend` directory (or ensure the root `.env` is accessible) with the following variables.
    
    *Example `.env`:*
    ```env
    DATABASE_URL=postgresql://ai_lab_user:ai_lab_password@localhost:5432/ai_lab
    OPENAI_API_KEY=your_openai_api_key_here
    ```
    *(Note: Database credentials match those in `docker-compose.yml`)*

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

## License

[MIT](LICENSE)
