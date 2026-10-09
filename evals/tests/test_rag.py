from backend.app.config import KNOWLEDGE_DIR
from backend.app.rag.store import KnowledgeBase


def kb():
    return KnowledgeBase(KNOWLEDGE_DIR)


def test_loads_chunks():
    assert len(kb().chunks) >= 20


def test_sign_query_retrieves_that_sign_first():
    top = kb().search("Scorpio Scorpio career this year", k=3)
    assert top[0].title == "Scorpio" and top[0].label == "K1"


def test_concept_query_finds_concept():
    titles = [c.title for c in kb().search("what is a nakshatra dasha", k=3)]
    assert "Nakshatras" in titles or "Dashas" in titles


def test_nonsense_returns_nothing():
    assert kb().search("zzzz qqqq") == []
