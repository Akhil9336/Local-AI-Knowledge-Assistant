"""Retrieval and context-grounded answer generation."""
import logging
from .ollama_client import OllamaClient
from .vector_store import VectorStore

logger = logging.getLogger(__name__)

INSUFFICIENT_INFO_MSG = "The available documents do not provide enough information to answer that question."


def build_qa_prompt(question: str, passages: list[dict], history: list[dict] | None = None) -> str:
    """Construct the grounding prompt with clear guidelines for synthesis, citations, and unknown aspects."""
    context_blocks = []
    for p in passages:
        meta = p.get("metadata", {})
        filename = meta.get("filename", "Document")
        page = meta.get("page")
        source_label = f"[Source: {filename}" + (f", page {page}" if page else "") + "]"
        context_blocks.append(f"{source_label}\n{p.get('text', '')}")
    context = "\n\n".join(context_blocks)

    prior = "\n".join(f"{m['role']}: {m['content']}" for m in (history or [])[-6:] if m.get("role") == "user")
    conversational_section = f"Recent user questions (for conversational context only):\n{prior}\n\n" if prior else ""

    prompt = (
        "You are a precise, document-grounded knowledge assistant. Answer the user's question directly, "
        "clearly, and thoroughly using only the facts provided in the document context below.\n\n"
        "Guidelines:\n"
        "1. Grounding: Rely strictly on the supplied document context as your sole source of truth. "
        "Do not bring in outside knowledge, speculative assumptions, or unverified claims.\n"
        "2. Synthesis: Synthesize relevant details across multiple passages where helpful.\n"
        "3. Partial Coverage: If the context answers part of the question but lacks details for other parts, "
        "answer the supported parts thoroughly and clearly state which aspects remain unmentioned in the documents.\n"
        "4. Insufficient Evidence: If the context contains no relevant evidence to answer the question, state: "
        f"\"{INSUFFICIENT_INFO_MSG}\"\n"
        "5. Citations: Cite the source filename and page (e.g., [Document.pdf, page X]) for factual statements "
        "based on the passage headers. Never invent citations or quotations.\n\n"
        f"{conversational_section}"
        f"Document Context:\n{context}\n\n"
        f"Question: {question}\n\n"
        "Answer:"
    )
    return prompt


def answer_question(question: str, history: list[dict], client: OllamaClient,
                    store: VectorStore, generation_model: str, embedding_model: str,
                    top_k: int = 5, threshold: float | None = None) -> tuple[str, list[dict]]:
    question = question.strip()
    if not question:
        raise ValueError("Enter a question.")

    logger.info("answer_question: question=%r (model=%s, embedding_model=%s, top_k=%d, threshold=%s)",
                question, generation_model, embedding_model, top_k, threshold)

    if store.collection.count() == 0:
        logger.info("Chroma collection is empty; returning early.")
        return "No documents are indexed yet. Upload and index a document first.", []

    query_vector = client.embed([question], embedding_model)[0]
    passages = store.search(query_vector, top_k=top_k, threshold=threshold, query_text=question)

    if not passages:
        logger.info("No matching passages retrieved for question=%r (threshold=%s)", question, threshold)
        return INSUFFICIENT_INFO_MSG, []

    for i, p in enumerate(passages, 1):
        meta = p.get("metadata", {})
        logger.info("Passage %d metadata: file=%s, page=%s, score=%.4f, text_len=%d",
                    i, meta.get("filename"), meta.get("page"), p.get("score", 0.0), len(p.get("text", "")))

    prompt = build_qa_prompt(question, passages, history)
    total_context_chars = sum(len(p.get("text", "")) for p in passages)
    logger.info("Prompt constructed: passages_count=%d, context_chars=%d, prompt_chars=%d",
                len(passages), total_context_chars, len(prompt))

    logger.info("Sending prompt to Ollama generation model=%s", generation_model)
    answer = client.generate(prompt, generation_model).strip()
    logger.info("Ollama generation returned: answer_len=%d, status=success", len(answer))

    return answer, passages
