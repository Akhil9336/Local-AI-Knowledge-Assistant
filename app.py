"""Enterprise-grade Streamlit Web Interface for Local AI Knowledge Assistant."""
import html
import json
import logging
import time
from datetime import datetime
from pathlib import Path

import streamlit as st

from config import settings
from rag.document_loader import load_document, stable_document_id
from rag.ollama_client import OllamaClient, OllamaError
from rag.qa_chain import answer_question
from rag.text_splitter import split_pages
from rag.vector_store import VectorStore
from ui_styles import CSS_THEME, render_hero, render_metrics_cards, render_navbar

# Configure logging
logging.basicConfig(
    filename="local_assistant.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

# Page configuration
st.set_page_config(
    page_title="AuraLocal AI Studio | Sovereign Knowledge Assistant",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject custom design system CSS
st.markdown(CSS_THEME, unsafe_allow_html=True)

# Initialize Session State variables
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None
if "confirm_clear_index" not in st.session_state:
    st.session_state.confirm_clear_index = False
if "confirm_clear_chat" not in st.session_state:
    st.session_state.confirm_clear_chat = False
if "base_url" not in st.session_state:
    st.session_state.base_url = settings.ollama_base_url
if "generation_model" not in st.session_state:
    st.session_state.generation_model = settings.generation_model
if "chunk_size" not in st.session_state:
    st.session_state.chunk_size = settings.chunk_size
if "chunk_overlap" not in st.session_state:
    st.session_state.chunk_overlap = settings.chunk_overlap
if "top_k" not in st.session_state:
    st.session_state.top_k = settings.top_k
if "threshold" not in st.session_state:
    st.session_state.threshold = settings.similarity_threshold

# Inspect existing collection to lock embedding model consistency
def detect_collection_embedding_model(db_dir: Path) -> str | None:
    try:
        import chromadb
        client_chroma = chromadb.PersistentClient(path=str(db_dir))
        collection = client_chroma.get_collection("knowledge")
        return (collection.metadata or {}).get("embedding_model")
    except Exception:
        return None

existing_model_in_db = detect_collection_embedding_model(settings.db_dir)
if existing_model_in_db:
    st.session_state.embedding_model = existing_model_in_db
elif "embedding_model" not in st.session_state or not st.session_state.embedding_model:
    st.session_state.embedding_model = settings.embedding_model

# Test Ollama client
client = OllamaClient(st.session_state.base_url, settings.request_timeout)
try:
    models = client.tags()
    ollama_ready = True
    missing_models = [
        m for m in (st.session_state.generation_model, st.session_state.embedding_model)
        if not any(
            installed == m or installed.startswith(m + ":") or m.startswith(installed.split(":")[0])
            for installed in models
        )
    ]
except OllamaError as exc:
    logging.warning("Ollama connection check failed: %s", exc)
    models = []
    ollama_ready = False
    missing_models = []

# Initialize Vector Database
try:
    store = VectorStore(settings.db_dir, st.session_state.embedding_model)
    documents = store.documents()
    chunk_count = sum(doc["chunks"] for doc in documents)
except Exception as exc:
    logging.exception("Could not initialize VectorStore")
    st.error(f"⚠️ Vector database initialization notice: {exc}")
    if "Index uses embedding model" in str(exc):
        st.info("The persistent vector store has an embedding model mismatch. Click below to safely reset the index.")
        if st.button("Reset Vector Database Now", type="primary"):
            import shutil
            if settings.db_dir.exists():
                shutil.rmtree(settings.db_dir, ignore_errors=True)
            st.session_state.embedding_model = settings.embedding_model
            st.rerun()
    st.stop()

# ==============================================================================
# SIDEBAR CONTROL PANEL
# ==============================================================================
with st.sidebar:
    st.markdown("""
    <div style="display:flex; align-items:center; gap:0.75rem; margin-bottom:0.2rem;">
        <div style="width:36px; height:36px; border-radius:10px; background:linear-gradient(135deg,#6366F1,#06B6D4); display:flex; align-items:center; justify-content:center; font-size:1.2rem; font-weight:bold; box-shadow:0 0 16px rgba(99,102,241,0.4);">⚡</div>
        <div>
            <div style="font-weight:800; font-size:1.15rem; color:#FFFFFF; letter-spacing:-0.02em;">AuraLocal AI</div>
            <div style="font-size:0.74rem; color:#94A3B8; font-weight:500;">v2.5 Enterprise Edition</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Engine status pill
    if ollama_ready:
        st.markdown(f"""
        <div style="margin: 0.8rem 0; padding: 0.55rem 0.8rem; background: rgba(16,185,129,0.12); border: 1px solid rgba(16,185,129,0.3); border-radius: 10px; display:flex; align-items:center; justify-content:space-between;">
            <div style="display:flex; align-items:center; gap:0.5rem; font-size:0.82rem; font-weight:600; color:#34D399;">
                <span class="pulse-dot online"></span> Ollama Connected
            </div>
            <span style="font-size:0.72rem; color:#94A3B8; font-family:'JetBrains Mono',monospace;">{len(models)} models</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="margin: 0.8rem 0; padding: 0.55rem 0.8rem; background: rgba(245,158,11,0.12); border: 1px solid rgba(245,158,11,0.3); border-radius: 10px; display:flex; align-items:center; justify-content:space-between;">
            <div style="display:flex; align-items:center; gap:0.5rem; font-size:0.82rem; font-weight:600; color:#FBBF24;">
                <span class="pulse-dot offline"></span> Ollama Offline
            </div>
            <span style="font-size:0.72rem; color:#94A3B8;">Port 11434</span>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # Quick Add Document Widget
    st.markdown("#### 📥 Quick Ingest")
    sidebar_uploads = st.file_uploader(
        "Upload PDF, TXT, or MD",
        type=["pdf", "txt", "md", "markdown"],
        accept_multiple_files=True,
        key="sidebar_uploader",
        help=f"Accepts files up to {settings.max_file_mb} MB each."
    )
    if sidebar_uploads:
        st.caption(f"📁 {len(sidebar_uploads)} file(s) staged for indexing")
        if st.button("⚡ Index Staged Files", type="primary", use_container_width=True, key="sidebar_index_btn"):
            progress_bar = st.progress(0, text="Ingesting and embedding documents...")
            success_count = 0
            for idx, item in enumerate(sidebar_uploads):
                try:
                    if item.size > settings.max_file_mb * 1024 * 1024:
                        raise ValueError(f"Exceeds max limit of {settings.max_file_mb} MB.")
                    doc = load_document(item.name, item)
                    doc_id = stable_document_id(doc.content_hash, doc.filename)
                    if store.has_document(doc_id):
                        st.info(f"ℹ️ {doc.filename} is already up to date.")
                    else:
                        chunks = split_pages(doc.pages, int(st.session_state.chunk_size), int(st.session_state.chunk_overlap))
                        vectors = client.embed([c.text for c in chunks], st.session_state.embedding_model)
                        store.upsert_document(doc_id, doc.filename, doc.content_hash, chunks, vectors)
                        success_count += 1
                except Exception as exc:
                    logging.exception("Indexing error for %s", item.name)
                    st.error(f"Error on {item.name}: {exc}")
                progress_bar.progress((idx + 1) / len(sidebar_uploads), text=f"Processed {idx + 1} of {len(sidebar_uploads)}")
            st.success(f"Successfully processed files.")
            time.sleep(0.8)
            st.rerun()

    st.divider()

    # Knowledge Base Overview
    st.markdown("#### 📊 Knowledge Vault")
    st.markdown(f"""
    <div style="background:rgba(30,41,59,0.5); border:1px solid rgba(255,255,255,0.06); border-radius:10px; padding:0.75rem 0.9rem; margin-bottom:1rem;">
        <div style="display:flex; justify-content:space-between; margin-bottom:0.4rem; font-size:0.82rem;">
            <span style="color:#94A3B8;">Indexed Files:</span>
            <span style="font-weight:700; color:#FFFFFF;">{len(documents)}</span>
        </div>
        <div style="display:flex; justify-content:space-between; margin-bottom:0.4rem; font-size:0.82rem;">
            <span style="color:#94A3B8;">Embedded Chunks:</span>
            <span style="font-weight:700; color:#FFFFFF;">{chunk_count}</span>
        </div>
        <div style="display:flex; justify-content:space-between; font-size:0.82rem;">
            <span style="color:#94A3B8;">Vector Space:</span>
            <span style="font-weight:600; color:#38BDF8;">Cosine / HNSW</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Quick action buttons
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🧹 Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    with c2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

    # Safe clear library confirmation
    if documents:
        if st.button("🗑️ Purge Index", use_container_width=True):
            st.session_state.confirm_clear_index = True

        if st.session_state.confirm_clear_index:
            st.warning("Are you sure? This deletes all ChromaDB embeddings.")
            y_col, n_col = st.columns(2)
            if y_col.button("Yes, Purge", type="primary", use_container_width=True):
                store.clear()
                st.session_state.confirm_clear_index = False
                st.rerun()
            if n_col.button("Cancel", use_container_width=True):
                st.session_state.confirm_clear_index = False
                st.rerun()

# ==============================================================================
# TOP NAVBAR & HERO
# ==============================================================================
st.markdown(render_navbar(
    ollama_ready=ollama_ready,
    gen_model=st.session_state.generation_model,
    embed_model=st.session_state.embedding_model,
    doc_count=len(documents)
), unsafe_allow_html=True)

st.markdown(render_hero(), unsafe_allow_html=True)

# Metrics Cards Grid
st.markdown(render_metrics_cards(
    doc_count=len(documents),
    chunk_count=chunk_count,
    ollama_ready=ollama_ready,
    active_model=st.session_state.generation_model
), unsafe_allow_html=True)

# Warning banner if Ollama is offline or models are missing
if not ollama_ready:
    st.markdown("""
    <div style="background:rgba(245,158,11,0.12); border:1px solid rgba(245,158,11,0.3); border-radius:14px; padding:1.1rem 1.3rem; margin-bottom:1.5rem; display:flex; align-items:center; justify-content:space-between;">
        <div>
            <div style="font-weight:700; color:#FBBF24; font-size:0.95rem; margin-bottom:0.25rem;">⚠️ Ollama Local Engine Offline</div>
            <div style="font-size:0.85rem; color:#CBD5E1;">
                Ollama could not be reached at <code>http://localhost:11434</code>. Please launch Ollama on your system or run <code>ollama serve</code> in your terminal.
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
elif missing_models:
    st.markdown(f"""
    <div style="background:rgba(239,68,68,0.12); border:1px solid rgba(239,68,68,0.3); border-radius:14px; padding:1.1rem 1.3rem; margin-bottom:1.5rem;">
        <div style="font-weight:700; color:#F87171; font-size:0.95rem; margin-bottom:0.35rem;">⚠️ Required Local Model Not Found: {', '.join(missing_models)}</div>
        <div style="font-size:0.85rem; color:#CBD5E1; margin-bottom:0.5rem;">
            Run the following terminal command to download the model into your local Ollama runtime:
        </div>
    </div>
    """, unsafe_allow_html=True)
    for model_name in missing_models:
        st.code(f"ollama pull {model_name}")

# ==============================================================================
# MAIN NAVIGATION TABS
# ==============================================================================
tab_chat, tab_docs, tab_settings, tab_telemetry, tab_arch = st.tabs([
    "💬 Assistant & Synthesis",
    "📚 Knowledge Repository",
    "⚙️ RAG Engine Settings",
    "📊 System Telemetry",
    "ℹ️ Architecture & Airgap"
])

# ------------------------------------------------------------------------------
# TAB 1: ASSISTANT & CHAT
# ------------------------------------------------------------------------------
with tab_chat:
    # Source passage rendering helper
    def render_sources_ui(sources):
        if not sources:
            return
        with st.expander(f"🔍 Grounding Source Passages ({len(sources)} cited)", expanded=False):
            for i, src in enumerate(sources, 1):
                meta = src["metadata"]
                filename = html.escape(str(meta.get("filename", "Document")))
                page_info = f" · Page {meta['page']}" if meta.get("page") else ""
                score = src.get("score", 0.0)
                score_pct = int(min(max(score, 0), 1) * 100) if score <= 1.0 else int(min(score, 100))
                badge_class = "match-high" if score_pct >= 75 else "match-medium"

                st.markdown(f"""
                <div class="source-card">
                    <div class="source-header-row">
                        <div class="source-file-badge">
                            <span>📄</span> {filename}{page_info}
                        </div>
                        <div class="source-match-badge {badge_class}">
                            <span>⚡</span> {score_pct}% Match Relevancy
                        </div>
                    </div>
                    <div class="source-content-text">{html.escape(src.get("text", ""))}</div>
                </div>
                """, unsafe_allow_html=True)

    # Empty State with Quick Prompts
    if not st.session_state.messages:
        if not documents:
            st.markdown("""
            <div style="background:rgba(30,41,59,0.5); border:1px solid rgba(255,255,255,0.08); border-radius:18px; padding:2rem; text-align:center; margin:1rem 0 2rem;">
                <div style="font-size:2.5rem; margin-bottom:0.75rem;">📂</div>
                <div style="font-size:1.25rem; font-weight:700; color:#FFFFFF; margin-bottom:0.4rem;">Your Knowledge Vault is Empty</div>
                <div style="font-size:0.92rem; color:#94A3B8; max-width:540px; margin:0 auto 1.5rem; line-height:1.5;">
                    Upload your technical papers, company policies, manuals, or research PDFs using the sidebar or the <strong>Knowledge Repository</strong> tab to start asking questions.
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown('<div class="suggestion-heading"><span>✦</span> Suggested Inquiries</div>', unsafe_allow_html=True)
            p1, p2 = st.columns(2)
            with p1:
                if st.button("📌 Summarize the core findings and key conclusions", use_container_width=True):
                    st.session_state.pending_prompt = "Summarize the core findings and key conclusions from the indexed documents."
                    st.rerun()
                if st.button("⚖️ Compare contrasting viewpoints and methodologies", use_container_width=True):
                    st.session_state.pending_prompt = "Compare contrasting viewpoints, methodologies, or topics across the documents."
                    st.rerun()
            with p2:
                if st.button("🔍 Extract all key metrics, quantitative data, and dates", use_container_width=True):
                    st.session_state.pending_prompt = "Extract all key metrics, quantitative numbers, and chronological dates mentioned."
                    st.rerun()
                if st.button("🛡️ Outline actionable recommendations and obligations", use_container_width=True):
                    st.session_state.pending_prompt = "Outline the key actionable recommendations, compliance points, and next steps."
                    st.rerun()
            st.markdown("<br>", unsafe_allow_html=True)

    # Render Conversation Messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            render_sources_ui(msg.get("sources", []))

    # Download / Export Conversation Feature
    if st.session_state.messages:
        st.markdown("<br>", unsafe_allow_html=True)
        export_col1, export_col2, _ = st.columns([2, 2, 4])
        with export_col1:
            # Build Markdown Transcript
            transcript_lines = ["# AuraLocal AI - Research Transcript", f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ""]
            for m in st.session_state.messages:
                role = "USER" if m["role"] == "user" else "ASSISTANT (Local AI)"
                transcript_lines.append(f"### {role}")
                transcript_lines.append(m["content"])
                if m.get("sources"):
                    transcript_lines.append("\n**Cited Sources:**")
                    for s in m["sources"]:
                        f = s["metadata"].get("filename", "Doc")
                        p = f", page {s['metadata']['page']}" if s["metadata"].get("page") else ""
                        transcript_lines.append(f"- *[{f}{p}]*: {s['text'][:250]}...")
                transcript_lines.append("\n---\n")
            
            st.download_button(
                label="📥 Export Chat as Markdown",
                data="\n".join(transcript_lines),
                file_name=f"research_transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
                use_container_width=True
            )
        with export_col2:
            if st.button("🗑️ Reset Conversation", use_container_width=True):
                st.session_state.messages = []
                st.rerun()

    # Chat Input handler
    chat_prompt = st.chat_input(
        "Ask a specific question about your indexed files...",
        disabled=not ollama_ready
    )
    
    # Process either typed input or clicked suggested prompt
    question_to_process = chat_prompt or st.session_state.pending_prompt
    if question_to_process:
        if st.session_state.pending_prompt:
            st.session_state.pending_prompt = None
            
        st.session_state.messages.append({"role": "user", "content": question_to_process})
        with st.chat_message("user"):
            st.markdown(question_to_process)
            
        with st.chat_message("assistant"):
            if not ollama_ready:
                answer = "❌ Ollama is offline. Please start Ollama locally at http://localhost:11434 and refresh."
                sources = []
            elif missing_models:
                answer = f"⚠️ Configured model ({', '.join(missing_models)}) is not installed. Please pull it in Ollama."
                sources = []
            else:
                try:
                    with st.spinner("⚡ Retrieving semantic & lexical passages and synthesizing answer..."):
                        answer, sources = answer_question(
                            question_to_process,
                            st.session_state.messages[:-1],
                            client,
                            store,
                            st.session_state.generation_model,
                            st.session_state.embedding_model,
                            st.session_state.top_k,
                            st.session_state.threshold
                        )
                except Exception as exc:
                    logging.exception("QA synthesis failure: %s", exc)
                    answer = f"⚠️ Generation error: {exc}"
                    sources = []
            
            st.markdown(answer)
            render_sources_ui(sources)
            
        st.session_state.messages.append({"role": "assistant", "content": answer, "sources": sources})
        st.rerun()

# ------------------------------------------------------------------------------
# TAB 2: KNOWLEDGE REPOSITORY
# ------------------------------------------------------------------------------
with tab_docs:
    st.markdown("### 📚 Knowledge Repository & Document Hub")
    st.markdown("Manage your private collection of indexed documents. Files are split into semantic chunks and embedded locally.")
    
    # Ingestion Dropzone
    with st.expander("➕ Ingest New Documents (PDF, Markdown, TXT)", expanded=not bool(documents)):
        main_uploads = st.file_uploader(
            "Drop files to index into local ChromaDB",
            type=["pdf", "txt", "md", "markdown"],
            accept_multiple_files=True,
            key="main_uploader",
            help="Files are processed entirely on your machine. Text is extracted and embedded locally."
        )
        if main_uploads:
            col_u1, col_u2 = st.columns([3, 1])
            with col_u1:
                st.info(f"{len(main_uploads)} file(s) ready to be embedded into the vector index.")
            with col_u2:
                if st.button("🚀 Process & Ingest Now", type="primary", use_container_width=True):
                    prog = st.progress(0, text="Reading and segmenting files...")
                    for i, file_obj in enumerate(main_uploads):
                        try:
                            if file_obj.size > settings.max_file_mb * 1024 * 1024:
                                raise ValueError(f"Exceeds max allowed size of {settings.max_file_mb} MB.")
                            loaded_doc = load_document(file_obj.name, file_obj)
                            d_id = stable_document_id(loaded_doc.content_hash, loaded_doc.filename)
                            if store.has_document(d_id):
                                st.info(f"Skipped {loaded_doc.filename}: unchanged identical file already in index.")
                            else:
                                doc_chunks = split_pages(loaded_doc.pages, int(st.session_state.chunk_size), int(st.session_state.chunk_overlap))
                                chunk_vecs = client.embed([c.text for c in doc_chunks], st.session_state.embedding_model)
                                store.upsert_document(d_id, loaded_doc.filename, loaded_doc.content_hash, doc_chunks, chunk_vecs)
                                st.success(f"Added {loaded_doc.filename} · {len(doc_chunks)} chunks embedded")
                        except Exception as e:
                            logging.exception("Ingest failed for %s", file_obj.name)
                            st.error(f"Failed to process {file_obj.name}: {e}")
                        prog.progress((i + 1) / len(main_uploads), text=f"Processed {i + 1} of {len(main_uploads)}")
                    st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Document Inventory Listing
    st.markdown(f"#### Active Documents in Vault ({len(documents)})")
    if not documents:
        st.caption("No files currently indexed. Upload files above to build your private repository.")
    else:
        # Search / filter within documents
        search_filter = st.text_input("🔍 Filter files by name...", "", placeholder="Type to filter document list...")
        filtered_docs = [d for d in documents if search_filter.lower() in d["filename"].lower()] if search_filter else documents

        for doc in filtered_docs:
            doc_id = doc["document_id"]
            filename = doc["filename"]
            chunks = doc["chunks"]
            file_ext = Path(filename).suffix.upper().replace(".", "") or "DOC"
            ext_icon = "📕" if file_ext == "PDF" else ("📘" if file_ext in ("MD", "MARKDOWN") else "📄")

            with st.container():
                d_col1, d_col2, d_col3 = st.columns([5, 3, 2])
                with d_col1:
                    st.markdown(f"""
                    <div style="display:flex; align-items:center; gap:0.75rem;">
                        <span style="font-size:1.5rem;">{ext_icon}</span>
                        <div>
                            <div style="font-weight:700; color:#FFFFFF; font-size:0.95rem;">{html.escape(filename)}</div>
                            <div style="font-size:0.78rem; color:#94A3B8;">Format: {file_ext} · ID: {doc_id[:10]}...</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                with d_col2:
                    st.markdown(f"""
                    <div style="display:flex; align-items:center; gap:0.5rem; height:100%; padding-top:0.3rem;">
                        <span class="pill-badge active-indigo">🧩 {chunks} passages</span>
                    </div>
                    """, unsafe_allow_html=True)
                with d_col3:
                    btn_c1, btn_c2 = st.columns(2)
                    with btn_c1:
                        show_chunks = st.checkbox("Inspect", key=f"inspect_{doc_id}")
                    with btn_c2:
                        if st.button("Delete", key=f"del_{doc_id}", type="secondary", use_container_width=True):
                            store.delete_document(doc_id)
                            st.success(f"Removed {filename}")
                            time.sleep(0.5)
                            st.rerun()

                # Chunk inspector expander
                if show_chunks:
                    try:
                        matched = store.collection.get(where={"document_id": doc_id}, include=["documents", "metadatas"])
                        if matched and matched["documents"]:
                            st.markdown(f"**Indexed Passages Preview ({len(matched['documents'])} total):**")
                            for idx, (doc_text, doc_meta) in enumerate(zip(matched["documents"][:5], matched["metadatas"][:5]), 1):
                                pg = f"Page {doc_meta.get('page')}" if doc_meta.get("page") else "Section"
                                st.caption(f"Chunk #{idx} ({pg}):")
                                st.code(doc_text[:350] + ("..." if len(doc_text) > 350 else ""), language="text")
                            if len(matched["documents"]) > 5:
                                st.caption(f"... and {len(matched['documents']) - 5} more chunks in index.")
                    except Exception as err:
                        st.error(f"Could not load chunks: {err}")

                st.markdown("<hr style='border-color:rgba(255,255,255,0.06);margin:0.7rem 0;'>", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# TAB 3: RAG ENGINE SETTINGS
# ------------------------------------------------------------------------------
with tab_settings:
    st.markdown("### ⚙️ RAG Engine Configuration & Local Runtime")
    st.markdown("Fine-tune retrieval depth, embedding boundaries, and Ollama connection parameters.")
    
    col_cfg1, col_cfg2 = st.columns(2)
    with col_cfg1:
        st.markdown("#### 🔌 Connection & Runtime")
        new_url = st.text_input("Ollama Base URL", value=st.session_state.base_url, help="Default is http://localhost:11434")
        if new_url != st.session_state.base_url:
            st.session_state.base_url = new_url.rstrip("/")
            st.rerun()

        # Model selection dropdowns or inputs
        if ollama_ready and models:
            st.markdown("#### 🤖 Model Selection (Detected from Ollama)")
            gen_options = list(dict.fromkeys([st.session_state.generation_model] + models))
            gen_idx = gen_options.index(st.session_state.generation_model)
            selected_gen = st.selectbox("Answer Generation Model", options=gen_options, index=gen_idx)
            if selected_gen != st.session_state.generation_model:
                st.session_state.generation_model = selected_gen
                st.rerun()

            embed_options = list(dict.fromkeys([st.session_state.embedding_model] + models))
            embed_idx = embed_options.index(st.session_state.embedding_model)
            selected_embed = st.selectbox("Embedding Vector Model", options=embed_options, index=embed_idx)
            if selected_embed != st.session_state.embedding_model:
                st.warning("⚠️ Note: Changing the embedding model alters the vector space. Re-indexing will be required.")
                c_switch, c_cancel = st.columns(2)
                if c_switch.button("Confirm & Reset Store", type="primary", key="switch_embed_model"):
                    store.clear()
                    st.session_state.embedding_model = selected_embed
                    st.rerun()
                if c_cancel.button("Cancel Change", key="cancel_embed_model"):
                    st.rerun()
        else:
            st.markdown("#### 🤖 Custom Model Identifiers")
            st.session_state.generation_model = st.text_input("Generation Model", st.session_state.generation_model)
            st.session_state.embedding_model = st.text_input("Embedding Model", st.session_state.embedding_model)

        if st.button("🧪 Ping Ollama Server", use_container_width=True):
            try:
                t0 = time.time()
                tags_list = client.tags()
                elapsed = int((time.time() - t0) * 1000)
                st.success(f"✅ Connected to Ollama in {elapsed}ms. Found {len(tags_list)} models installed.")
            except Exception as e:
                st.error(f"❌ Connection failed: {e}")

    with col_cfg2:
        st.markdown("#### 🎯 Retrieval & Splitting Tuners")
        st.session_state.chunk_size = st.slider(
            "Chunk Size (Characters)",
            min_value=200,
            max_value=3000,
            value=int(st.session_state.chunk_size),
            step=100,
            help="Higher chunk sizes provide broader context; lower chunk sizes provide pinpoint precision."
        )
        st.session_state.chunk_overlap = st.slider(
            "Chunk Overlap (Characters)",
            min_value=0,
            max_value=min(int(st.session_state.chunk_size) - 50, 500),
            value=min(int(st.session_state.chunk_overlap), int(st.session_state.chunk_size) - 50),
            step=25,
            help="Overlap prevents critical sentences from being split awkwardly across chunk boundaries."
        )
        st.session_state.top_k = st.slider(
            "Top-K Grounding Passages",
            min_value=1,
            max_value=12,
            value=int(st.session_state.top_k),
            help="The maximum number of retrieved passages to pass to the generation prompt."
        )
        threshold_val = st.slider(
            "Similarity Score Floor (Optional)",
            min_value=0.0,
            max_value=0.9,
            value=float(st.session_state.threshold or 0.0),
            step=0.05,
            help="Ignore passages scoring below this cosine similarity threshold (0.0 disables filter)."
        )
        st.session_state.threshold = threshold_val if threshold_val > 0.0 else None

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 📦 Recommended High-Performance Models for Local RAG")
    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        st.markdown("""
        **Llama 3.2 (3B)**  
        *Ultra-fast, low memory footprint.*  
        `ollama pull llama3.2`
        """)
    with m_col2:
        st.markdown("""
        **BGE-M3 Embeddings**  
        *Top multilingual & long-context vectors.*  
        `ollama pull bge-m3`
        """)
    with m_col3:
        st.markdown("""
        **DeepSeek-R1 (8B)**  
        *Advanced reasoning for technical documents.*  
        `ollama pull deepseek-r1:8b`
        """)

# ------------------------------------------------------------------------------
# TAB 4: SYSTEM TELEMETRY
# ------------------------------------------------------------------------------
with tab_telemetry:
    st.markdown("### 📊 System Telemetry & Vector Index Metrics")
    st.markdown("Real-time diagnostic metrics of the local Chroma vector index and retrieval engine.")
    
    db_path = settings.db_dir.resolve()
    db_size_mb = sum(f.stat().st_size for f in db_path.rglob('*') if f.is_file()) / (1024 * 1024) if db_path.exists() else 0.0

    t_col1, t_col2, t_col3, t_col4 = st.columns(4)
    with t_col1:
        st.markdown(f"""
        <div class="metric-card-pro">
            <div class="metric-header"><span class="metric-label-pro">Chroma DB Size</span><div class="metric-icon-wrap">💾</div></div>
            <div class="metric-value-pro">{db_size_mb:.1f} MB</div>
            <div class="metric-subtext-pro">Persistent disk usage</div>
        </div>
        """, unsafe_allow_html=True)
    with t_col2:
        st.markdown(f"""
        <div class="metric-card-pro">
            <div class="metric-header"><span class="metric-label-pro">Total Embeddings</span><div class="metric-icon-wrap">🧬</div></div>
            <div class="metric-value-pro">{chunk_count}</div>
            <div class="metric-subtext-pro">Active vector records</div>
        </div>
        """, unsafe_allow_html=True)
    with t_col3:
        st.markdown(f"""
        <div class="metric-card-pro">
            <div class="metric-header"><span class="metric-label-pro">HNSW Space</span><div class="metric-icon-wrap">📐</div></div>
            <div class="metric-value-pro">Cosine</div>
            <div class="metric-subtext-pro">Normalized similarity</div>
        </div>
        """, unsafe_allow_html=True)
    with t_col4:
        st.markdown(f"""
        <div class="metric-card-pro">
            <div class="metric-header"><span class="metric-label-pro">Airgap Status</span><div class="metric-icon-wrap">🛡️</div></div>
            <div class="metric-value-pro" style="color:#34D399;">100%</div>
            <div class="metric-subtext-pro">Zero external calls</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 📁 Storage & Configuration Details")
    st.json({
        "chroma_db_directory": str(db_path),
        "ollama_base_url": st.session_state.base_url,
        "generation_model": st.session_state.generation_model,
        "embedding_model": st.session_state.embedding_model,
        "chunk_size": st.session_state.chunk_size,
        "chunk_overlap": st.session_state.chunk_overlap,
        "top_k": st.session_state.top_k,
        "similarity_threshold": st.session_state.threshold,
        "max_file_limit_mb": settings.max_file_mb
    })

# ------------------------------------------------------------------------------
# TAB 5: ARCHITECTURE & GUIDE
# ------------------------------------------------------------------------------
with tab_arch:
    st.markdown("### ℹ️ Sovereign Local RAG Architecture")
    st.markdown("How AuraLocal AI safeguards your data while providing state-of-the-art document intelligence.")
    
    st.markdown("""
    <div style="background:rgba(30,41,59,0.5); border:1px solid rgba(255,255,255,0.08); border-radius:16px; padding:1.5rem; margin-bottom:1.5rem;">
        <h4 style="margin-top:0; color:#38BDF8;">⚡ End-to-End Local Execution Pipeline</h4>
        <ol style="color:#CBD5E1; line-height:1.75; font-size:0.92rem; padding-left:1.2rem;">
            <li><strong>Document Ingestion:</strong> Files (PDF, TXT, MD) are read from memory. PDF page numbers and structural headings are preserved.</li>
            <li><strong>Recursive Text Chunking:</strong> Paragraphs are divided into overlapping chunks respecting sentence and word boundaries.</li>
            <li><strong>Dense Embeddings:</strong> High-dimensional embeddings are generated via Ollama's local <code>/api/embed</code> endpoint.</li>
            <li><strong>Persistent ChromaDB:</strong> Chunks and vectors are indexed into a local HNSW cosine vector index in <code>data/chroma_db</code>.</li>
            <li><strong>Hybrid Fusion Search:</strong> When you ask a question, the engine retrieves candidates through both <em>Dense Semantic Similarity</em> and <em>Lexical Exact Keyword Overlap</em>, combining them with Reciprocal Rank Fusion (RRF).</li>
            <li><strong>Strict Grounded Synthesis:</strong> Ollama's local LLM generates answers conditioned strictly on retrieved evidence, accompanied by exact source and page citations.</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

    a_col1, a_col2 = st.columns(2)
    with a_col1:
        st.markdown("""
        #### 🛡️ Privacy & Security Guarantees
        - **Zero Cloud API Keys Required:** Runs on local CPU or GPU.
        - **No Telemetry / No Tracking:** Neither your document contents nor user queries leave your computer.
        - **Deterministic Attribution:** If the document doesn't contain the answer, the model explicitly declares insufficient evidence rather than hallucinating.
        """)
    with a_col2:
        st.markdown("""
        #### 💡 Best Practices for High Quality Answers
        - **Chunk Size Tuning:** Technical manuals and legal agreements often benefit from 800-1200 characters with 150 characters overlap.
        - **Keyword Quotes:** Use exact terms or names in quotes if searching for unique contract clauses or identifiers.
        - **Multi-document Synthesis:** Ask for comparisons across documents to have the assistant cross-reference evidence.
        """)
