import pytest
from langchain_core.language_models import FakeListChatModel

from app.agents.scam.graph import scam_graph
from app.core import llm

# We will patch get_llm to return a fake model that spits out a standard JSON response.
fake_predatory_llm = FakeListChatModel(
    responses=[
        '{"risk_summary": "Extremely high interest rate.", "risk_score": 0.9}'
    ]
)

fake_safe_llm = FakeListChatModel(
    responses=[
        '{"risk_summary": "No risks found.", "risk_score": 0.1}'
    ]
)

@pytest.fixture(autouse=True)
def mock_llm_and_embeddings(monkeypatch, request):
    """Mock the LLM and Embeddings to return predefined responses for fast, deterministic unit tests."""
    from langchain_core.embeddings import FakeEmbeddings
    fake_embeddings = FakeEmbeddings(size=384)
    
    if "safe" in request.node.name:
        monkeypatch.setattr(llm, "get_llm", lambda **kwargs: fake_safe_llm)
    else:
        monkeypatch.setattr(llm, "get_llm", lambda **kwargs: fake_predatory_llm)
        
    monkeypatch.setattr(llm, "get_embeddings", lambda **kwargs: fake_embeddings)
    
    # We must also patch it in the graph module where it's imported if needed,
    # but since graph.py calls `get_llm()` and `get_embeddings()` at runtime, 
    # patching `app.core.llm` works perfectly.
    import app.agents.scam.graph
    monkeypatch.setattr(app.agents.scam.graph, "get_llm", lambda **kwargs: fake_safe_llm if "safe" in request.node.name else fake_predatory_llm)
    monkeypatch.setattr(app.agents.scam.graph, "get_embeddings", lambda **kwargs: fake_embeddings)

@pytest.mark.asyncio
async def test_scam_graph_predatory_clause():
    """Test that the Scam Graph correctly identifies a predatory clause."""
    verified_text = (
        "Loan Agreement\n"
        "The borrower agrees to the terms.\n"
        "Interest shall accrue at the rate of 1.5% per day on the outstanding principal balance.\n"
        "If you default, we will seize your vehicle without notice."
    )
    
    initial_state = {
        "document_id": "test-doc-123",
        "raw_text": "",
        "verified_text": verified_text,
        "matched_clauses": [],
        "risk_score": None,
        "risk_summary": None,
        "language": "en"
    }
    
    final_state = await scam_graph.ainvoke(initial_state)
    
    assert final_state is not None
    assert "matched_clauses" in final_state
    
    # We should have matched something from the LanceDB seed data
    assert len(final_state["matched_clauses"]) > 0
    
    # Risk score should be populated and high
    assert final_state["risk_score"] is not None
    assert final_state["risk_score"] >= 0.5
    assert "high interest" in final_state["risk_summary"].lower()

@pytest.mark.asyncio
async def test_scam_graph_safe_clause():
    """Test that a completely benign document yields a low risk score."""
    verified_text = (
        "Loan Agreement\n"
        "The interest rate is 5% per annum.\n"
        "No hidden fees are applied."
    )
    
    initial_state = {
        "document_id": "test-doc-safe",
        "raw_text": "",
        "verified_text": verified_text,
        "matched_clauses": [],
        "risk_score": None,
        "risk_summary": None,
        "language": "en"
    }
    
    final_state = await scam_graph.ainvoke(initial_state)
    
    assert final_state is not None
    assert final_state["risk_score"] is not None
    assert final_state["risk_score"] < 0.5
    assert "No risks" in final_state["risk_summary"]
