# Exam Evaluation System (Teacher Reassessment Agent)

An AI-assisted dashboard for teachers. A teacher uploads an original assessment paper, uploads a student's marked answer script as a PDF, and receives a structured reassessment report with a mark range, a justification and suggestions for improvement for every question. Teachers can also upload course slides, which are chunked and embedded into a vector database for semantic search.

> **Repository scope.** This repository contains the React dashboard (`Frontend/`) and the slide ingestion and search API (`Backend/`). The assessment and reassessment AI endpoints that the dashboard calls are served by a separate backend hosted on a Hugging Face Space (see [Architecture](#architecture)).

## Features

- **Reassessment reports.** Upload a student's answer PDF and get a generated report with a student details section and a question-by-question evaluation (mark range, mark justification, suggestions for improvement). The report is rendered as Markdown and the raw output stays available in a collapsible view.
- **Assessment paper upload.** Upload the original paper and the AI extracts the subject and every question with its marks, then saves the assessment so student papers can be evaluated against it.
- **Slide ingestion and semantic search.** Upload PDF, DOCX, PPTX, XLSX or TXT slides with course and subject metadata. Files are split into overlapping chunks, embedded with Google `text-embedding-004`, and stored in Pinecone for similarity search.
- **Teacher authentication UI.** Login, signup, forgot password and reset password forms.
- **Loading feedback.** An animated "AI Evaluation in Progress" panel while reports are generated.

## Architecture

```
React dashboard (Vite, TypeScript)
   |
   |-- Assessment and reassessment calls ---> Hosted AI backend (Hugging Face Space)
   |        POST /api/v1/api/assessments/process-file      (extract questions and marks)
   |        POST /api/v1/api/reports/upload-files          (upload student PDF)
   |        POST /api/v1/api/reports/generate              (generate reassessment report)
   |
   '-- Slide calls ---> FastAPI service in Backend/
            POST /api/v1/slides/  ... ingest, chunk, embed, upsert
            GET  /api/v1/slides/search/  ... semantic search
                        |
                        v
              Google text-embedding-004 (768 dim) ---> Pinecone (cosine)
```

### Reassessment flow

1. The teacher uploads the original paper. The backend returns the subject and a list of questions with marks.
2. The teacher uploads a student's answer PDF. The dashboard uploads it, then requests report generation for the stored file path.
3. The generated report contains a **Student Details** section and a **Question-by-Question Evaluation** section. The dashboard parses these labeled sections into cards for each question.

### Slide ingestion flow

1. `POST /slides/` accepts a file plus `slide_name`, `course_name`, `subject_name` and an optional `description`. Files over 10 MB or empty files are rejected.
2. Text is extracted by file type (`pypdf`, `docx2python`, `python-pptx`, `openpyxl`, or plain text). File type is detected with `python-magic`, with a fallback to the extension.
3. Text is split with LangChain's `RecursiveCharacterTextSplitter` (1000 characters, 200 overlap).
4. Each chunk is embedded and upserted to Pinecone with metadata (slide, course and subject names, file name, content type, chunk index, total chunks, timestamps).
5. `GET /slides/search/?query=...&limit=5` embeds the query and returns the closest chunks.

## Tech Stack

| Area | Technology |
|---|---|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, shadcn/ui (Radix), Material UI |
| Frontend data and forms | TanStack Query, Axios, React Router, React Hook Form, Zod, react-dropzone |
| Report rendering | react-markdown with remark-gfm |
| Backend | Python, FastAPI, Uvicorn |
| Embeddings and vector store | Google `text-embedding-004` via `langchain-google-genai`, Pinecone |
| Document parsing | pypdf, docx2python, python-pptx, openpyxl, python-magic |
| Deployment | Vercel (backend config included), Hugging Face Spaces (AI backend) |

## Project Structure

```
Teacher_reassesment_agent/
├── Backend/
│   ├── api/index.py              Vercel entry point
│   ├── src/app/
│   │   ├── main.py               FastAPI app and CORS
│   │   ├── database.py           Pinecone client and index setup
│   │   ├── routers/slides.py     /slides routes
│   │   ├── controllers/          upload, embed, search logic
│   │   ├── schemas/ models/      Pydantic models
│   │   └── utils.py              parsing and chunking
│   ├── requirements.txt
│   └── vercel.json
└── Frontend/
    └── src/
        ├── pages/                Index, NotFound
        └── components/
            ├── auth/             login, signup, forgot and reset password
            └── dashboard/        TeacherDashboard, AssessmentUpload,
                                  ReassessmentPdfUpload, AiEvaluationLoader
```

## Getting Started

### Prerequisites

- Python 3.10+ and Node.js 18+
- A Pinecone API key
- A Google AI (Gemini) API key for embeddings

### Backend

```bash
cd Backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then fill in the values below
uvicorn src.app.main:app --reload --port 8000
```

Environment variables:

```
PINECONE_API_KEY=your-pinecone-key
PINECONE_INDEX=reassesment          # optional, default shown
GOOGLE_API_KEY=your-google-ai-key   # used by the embedding client
```

On first run the Pinecone index is created automatically with 768 dimensions and the cosine metric.

### Frontend

```bash
cd Frontend
npm install
npm run dev
```

Scripts: `npm run build`, `npm run preview`, `npm run lint`.

## API Reference (slides service)

| Method | Path | Description |
|---|---|---|
| POST | `/slides/` | Upload a slide file with metadata. Returns one record per embedded chunk. |
| GET | `/slides/search/` | Semantic search. Query params: `query` (required), `limit` (default 5). |
| GET | `/slides/` | List slides (not implemented yet). |
| GET | `/slides/{slide_id}` | Get one slide (not implemented yet). |

Interactive docs are available at `http://localhost:8000/docs`.

## Known Limitations and Roadmap

- Listing and fetching slides are placeholders and should be backed by Pinecone metadata queries or a database.
- Scanned PDFs and images are not supported because the parser has no OCR step.
- Legacy `.doc`, `.ppt` and `.xls` files may fail to parse.
- Chunks are embedded and upserted one at a time. Batching would speed up large uploads.
- Only the first uploaded student PDF is sent for evaluation.
- CORS currently allows all origins. Restrict it to the dashboard domain before production use.
- The reassessment report parser in the dashboard depends on the exact bold-label format of the AI output.
- Add automated tests and a dedicated health endpoint.

## Author

Ahsan Ali Gill, [GitHub](https://github.com/AhsanAliGill)
