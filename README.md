# AI Research Assistant

A full-stack research assistant that lets you upload documents (PDF, TXT, or URL)
and ask questions that are answered only from those sources, with citations.

## What it does
- Upload and manage research sources per project.
- Ask questions in a chat interface with cited sources.
- Keeps projects, documents, and chat history separate per user.
- Uses retrieval-augmented generation (RAG) to ground answers in documents.
- Returns "I don't know." when the answer is not present in the sources.

## Tech stack
- Backend: FastAPI + SQLAlchemy + PostgreSQL
- Frontend: React (Vite)
- RAG: chunking + embeddings + cosine retrieval + OpenAI LLM

## Local development (Docker)
1. Start services:
   - `docker compose up --build`
2. Frontend: `http://localhost:5173`
3. Backend: `http://localhost:8000`

## Environment variables
Backend:
- `DATABASE_URL` (default in compose file)
- `JWT_SECRET`
- `OPENAI_API_KEY` (enables real embeddings + LLM answers)

Frontend:
- `VITE_API_URL` (defaults to `http://localhost:8000`)

## Usage notes
- If a PDF is scanned (no text layer), upload an OCR version for best results.
