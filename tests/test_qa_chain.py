from types import SimpleNamespace
from unittest.mock import Mock
from rag.qa_chain import answer_question, build_qa_prompt, INSUFFICIENT_INFO_MSG


FABRIC_AND_SKETCHES_FIXTURE = (
    "How I Would Handle the 200 Fabrics & Sketches\n"
    "Fabrics: Organize by Photo, Colour, Material, Texture, Finish, and Suitable Designs (Lehenga / Gown)\n"
    "Why: Instead of showing all 200 to a customer, show only 5-6 best matches to avoid confusion\n"
    "Sketches: When a customer brings a photo or rough drawing:\n"
    "Step 1: AI looks at the sketch and identifies: Size, Colour, Design, Special requirements (border, neck)\n"
    "Step 2: AI creates a neat summary and asks a human to check it\n"
    "Step 3: Human makes the final call — customized orders need a human touch"
)


def test_empty_index_and_unsupported_question():
    store = SimpleNamespace(collection=SimpleNamespace(count=lambda: 0))
    answer, sources = answer_question("unknown", [], None, store, "gen", "embed")
    assert "No documents" in answer and sources == []
    store.collection.count = lambda: 1
    store.search = lambda *args, **kwargs: []
    client = SimpleNamespace(embed=Mock(return_value=[[0.1]]))
    answer, sources = answer_question("unknown", [], client, store, "gen", "embed")
    assert "not provide enough" in answer and sources == []


def test_context_is_sent_to_local_generation():
    source = {"text": "The answer is 42.", "metadata": {"filename": "a.txt", "page": 0}, "score": .9}
    store = SimpleNamespace(collection=SimpleNamespace(count=lambda: 1), search=lambda *args, **kwargs: [source])
    client = SimpleNamespace(embed=lambda *args, **kwargs: [[0.1]], generate=Mock(return_value="42 [a.txt]"))
    answer, sources = answer_question("meaning?", [], client, store, "gen", "embed")
    assert answer.startswith("42") and sources == [source]
    assert "The answer is 42." in client.generate.call_args.args[0]


def test_generation_errors_propagate_for_ui_handling():
    source = {"text": "evidence", "metadata": {"filename": "a.txt", "page": 0}, "score": .9}
    store = SimpleNamespace(collection=SimpleNamespace(count=lambda: 1), search=lambda *args, **kwargs: [source])
    client = SimpleNamespace(embed=lambda *args, **kwargs: [[0.1]], generate=Mock(side_effect=RuntimeError("offline")))
    try:
        answer_question("question", [], client, store, "gen", "embed")
        assert False, "Expected generation error"
    except RuntimeError as exc:
        assert str(exc) == "offline"


def test_fabric_and_sketch_question_reaches_generation():
    """Regression test: verify retrieved 200 fabrics passage reaches prompt and generation."""
    source = {
        "text": FABRIC_AND_SKETCHES_FIXTURE,
        "metadata": {"filename": "Morpankh_AI_Assignment_Slides.pdf", "page": 6},
        "score": 0.6908
    }
    store = SimpleNamespace(collection=SimpleNamespace(count=lambda: 10), search=lambda *args, **kwargs: [source])
    client = SimpleNamespace(
        embed=Mock(return_value=[[0.1] * 1024]),
        generate=Mock(return_value="Organize 200 fabrics by photo, colour, material [Morpankh_AI_Assignment_Slides.pdf, page 6].")
    )
    question = "How I Would Handle the 200 Fabrics & Sketches?"
    answer, sources = answer_question(question, [], client, store, "llama3.2", "bge-m3")

    # Verify sources returned
    assert len(sources) == 1
    assert sources[0]["metadata"]["filename"] == "Morpankh_AI_Assignment_Slides.pdf"
    assert sources[0]["metadata"]["page"] == 6

    # Verify that the exact text reached generation prompt
    assert client.generate.called
    sent_prompt = client.generate.call_args.args[0]
    assert FABRIC_AND_SKETCHES_FIXTURE in sent_prompt
    assert "[Source: Morpankh_AI_Assignment_Slides.pdf, page 6]" in sent_prompt
    assert question in sent_prompt
    assert "Organize 200 fabrics" in answer


def test_unrelated_question_acknowledges_missing_evidence():
    """Verify that an unsupported question acknowledges missing information."""
    # Case 1: No retrieved passages from search
    store = SimpleNamespace(collection=SimpleNamespace(count=lambda: 5), search=lambda *args, **kwargs: [])
    client = SimpleNamespace(embed=Mock(return_value=[[0.1] * 1024]))
    unrelated_q = "What is the orbital speed of Jupiter's moon Europa?"
    answer, sources = answer_question(unrelated_q, [], client, store, "llama3.2", "bge-m3")
    assert answer == INSUFFICIENT_INFO_MSG
    assert sources == []

    # Case 2: Model determines context lacks answer
    unrelated_source = {
        "text": "The company produces ethnic lehengas.",
        "metadata": {"filename": "Morpankh.pdf", "page": 1},
        "score": 0.35
    }
    store2 = SimpleNamespace(collection=SimpleNamespace(count=lambda: 5), search=lambda *args, **kwargs: [unrelated_source])
    client2 = SimpleNamespace(
        embed=Mock(return_value=[[0.1] * 1024]),
        generate=Mock(return_value=INSUFFICIENT_INFO_MSG)
    )
    answer2, sources2 = answer_question(unrelated_q, [], client2, store2, "llama3.2", "bge-m3")
    assert answer2 == INSUFFICIENT_INFO_MSG
    assert len(sources2) == 1


def test_build_qa_prompt_guidelines_and_synthesis():
    """Verify prompt guidelines emphasize synthesis, partial coverage, citations, and grounding."""
    passages = [
        {"text": "Topic A details.", "metadata": {"filename": "doc1.pdf", "page": 2}},
        {"text": "Topic B details.", "metadata": {"filename": "doc2.txt", "page": 0}}
    ]
    prompt = build_qa_prompt("What about A and C?", passages, history=[{"role": "user", "content": "Prior Q"}])
    assert "Grounding:" in prompt
    assert "Synthesis:" in prompt
    assert "Partial Coverage:" in prompt
    assert "Insufficient Evidence:" in prompt
    assert "[Source: doc1.pdf, page 2]" in prompt
    assert "[Source: doc2.txt]" in prompt
    assert "Prior Q" in prompt
    assert "What about A and C?" in prompt
