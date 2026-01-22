# mock_response.py - Fallback mocks for APIs
def mock_search_web(query):
    """Mock Tavily search."""
    return "Mock result: General flight info from ZUR - no delays reported."

def mock_policy(query):
    """Mock policy lookup."""
    return "Mock policy: Cancellations allowed 24h prior with full refund."