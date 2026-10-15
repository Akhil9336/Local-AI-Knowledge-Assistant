# Local AI Knowledge Assistant

A Windows-friendly document question-answering app using Streamlit, Ollama, ChromaDB, and a small local RAG pipeline. Uploaded documents and embeddings remain on the machine. No cloud API key is needed.

## How it works

1. PDF, TXT, and Markdown files are extracted locally (`pypdf` handles PDFs).
2. Text is split into configurable overlapping chunks that keep paragraphs and sentences together where possible. PDF page numbers are retained.
3. Ollama's `/api/embed` endpoint creates embeddings (default `bge-m3`), stored persistently in `data/chroma_db` using cosine distance.
4. Each question is matched by both embedding similarity and exact keyword overlap. Their rankings are combined, helping with both meaning-based questions and exact names, dates, and identifiers.
5. The retrieved passages are supplied to Ollama `/api/generate` (default `llama3.2`) at temperature zero. The prompt requires answers to rely on those passages and cite their filename and PDF page. Retrieved passages are shown under the answer.

Previous user questions may help interpret follow-ups, but assistant answers are never supplied as evidence. The local Chroma database does not contain the original uploaded files; remove operations only delete index entries.

## Prerequisites

- Windows 10/11
- Python 3.10 or newer (64-bit recommended)
- Ollama installed and running locally
- Models: `llama3.2` and `bge-m3` (or configure other compatible Ollama model names)

The app checks Ollama's local model list when it starts and displays an exact `ollama pull MODEL` command for any missing model. Pulls are manual, so large model downloads never start unexpectedly.

## Setup in PowerShell

Open PowerShell in this project directory:

```powershell
py -3 --version
py -3 -m venv .venv
```

Activate the environment if permitted:

```powershell
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, do not change the global execution policy. Call the venv interpreter directly instead:

```powershell
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

When activated, install dependencies with:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Verify Ollama and check installed models:

```powershell
ollama --version
ollama list
```

Only if absent, download the model(s) you want to use:

```powershell
ollama pull llama3.2
ollama pull bge-m3
```

The app defaults to `http://localhost:11434`. Ollama must be running when you index or ask questions.

## Run

```powershell
python -m streamlit run app.py
```

If the venv is not activated:

```powershell
.venv\Scripts\python.exe -m streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501). Stop the server with Ctrl+C in the terminal.

## Use the app

1. Select one or more PDF, TXT, or Markdown files in the sidebar. Files up to 50 MB are accepted by default.
2. Click **Index selected documents**. The app skips unchanged content and shows per-file status.
3. Ask a question in the main chat. Answers include citations when the retrieved source supports them; expand the source passages to inspect the excerpts.
4. Remove one document using its **Remove** button. To replace an updated file, upload and index it again; old chunks are removed after the replacement is embedded and stored.
5. **Clear complete index** asks for confirmation before deleting all Chroma records. It does not delete unrelated files or the database directory.
6. **Clear chat** removes only the current session conversation.

Encrypted, malformed, unreadable, empty, and unsupported files produce a status message. Scanned PDFs with no selectable text require OCR; OCR is not included. Chunk size, overlap, top-k, models, and Ollama URL are configurable in the sidebar or through environment variables. `.env.example` lists the available variables; copy settings into your shell environment as needed.

## Run tests

```powershell
python -m pytest
```

The test suite uses mock Ollama calls and a temporary Chroma database; it does not download models or require a running Ollama service.

## Local files and privacy

- Persistent vector index: `data/chroma_db/`
- Local diagnostics: `local_assistant.log`
- Uploaded files are processed in memory and are not copied to a project uploads folder.
- `.gitignore` excludes the virtual environment, local database, logs, `.env`, and temporary files.

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Local Ollama endpoint |
| `OLLAMA_GENERATION_MODEL` | `llama3.2` | Answer model |
| `OLLAMA_EMBEDDING_MODEL` | `bge-m3` | Embedding model |
| `RAG_DATA_DIR` | `data` | Parent directory for the persistent database |
| `RAG_CHUNK_SIZE` | `1000` | Chunk character length |
| `RAG_CHUNK_OVERLAP` | `150` | Overlap between adjacent chunks |
| `RAG_TOP_K` | `5` | Default retrieved passage count |
| `RAG_SIMILARITY_THRESHOLD` | unset | Optional cosine similarity floor |
| `RAG_MAX_FILE_MB` | `50` | Upload size limit |
| `OLLAMA_TIMEOUT` | `120` | Ollama request timeout, in seconds |

Chroma records the embedding model in collection metadata. Changing the configured embedding model while an index exists stops startup with instructions to clear the index first; this prevents mixed vector dimensions or semantics.

## Troubleshooting

- **`python` not found:** install Python from python.org and enable the Python launcher, then use `py -3`. Open a new terminal after installation.
- **PowerShell activation is blocked:** use `.venv\Scripts\python.exe` directly as shown above. Do not change global PowerShell policy.
- **`ollama` not found:** install/start Ollama, reopen PowerShell, and check `ollama --version`. The app also needs the Ollama service at the configured URL.
- **Model missing:** use the exact `ollama pull ...` command displayed in the sidebar. Check installed tags with `ollama list`.
- **Connection refused:** start Ollama and confirm `OLLAMA_BASE_URL`; the default service endpoint is `http://localhost:11434`.
- **Slow or timed out generation:** use a smaller Ollama model or increase `OLLAMA_TIMEOUT`.
- **Chroma install/import issue:** use a supported 64-bit Python 3.10+ release in a fresh `.venv`, then reinstall `requirements.txt`.
- **No answer from a PDF:** confirm that it contains selectable text. Scanned/image-only pages need an OCR step, which this version does not provide.
- **Changed embedding model:** clear the index in the sidebar before restarting with a different embedding model.

## Project layout

```text
app.py
config.py
rag/
  document_loader.py
  text_splitter.py
  ollama_client.py
  vector_store.py
  qa_chain.py
tests/
requirements.txt
```
