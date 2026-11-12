from app.db.repositories import score_kb_relevance


PYTHON_SEED = "Python is a high-level, interpreted programming language known for its readability and versatility. It supports multiple programming paradigms including procedural, object-oriented, and functional programming."
QUANTUM_SEED = "Quantum computing leverages quantum mechanical phenomena like superposition and entanglement to perform computations. Qubits can represent 0, 1, or both simultaneously, enabling parallel processing for certain problems."
EUROPEAN_CAPITALS_SEED = "Major European capitals include: Paris (France), Berlin (Germany), Rome (Italy), Madrid (Spain), London (UK), Amsterdam (Netherlands), Vienna (Austria), Warsaw (Poland), Stockholm (Sweden), and Copenhagen (Denmark)."


def test_weather_climate_does_not_match_unrelated_seed_documents() -> None:
    query = "Explain the difference between weather and climate."

    assert score_kb_relevance(query, PYTHON_SEED) == 0.0
    assert score_kb_relevance(query, QUANTUM_SEED) == 0.0
    assert score_kb_relevance(query, EUROPEAN_CAPITALS_SEED) == 0.0


def test_capital_of_france_matches_european_capitals_seed() -> None:
    assert score_kb_relevance("What is the capital of France?", EUROPEAN_CAPITALS_SEED) >= 0.34
