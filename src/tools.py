from pydantic import BaseModel, Field, ValidationError
from db import init_collection, add_runbooks_batch, search_runbooks as db_search

# ============================================================================
# GLOBAL STATE: Initialize ChromaDB collection at module import
# ============================================================================

_collection = None


def _get_collection():
    """Lazy-load ChromaDB collection (singleton pattern)."""
    global _collection
    if _collection is None:
        from db import seed_runbooks
        _collection, _ = seed_runbooks()
    return _collection


# ============================================================================
# VALIDATION: Pydantic models for tool arguments
# ============================================================================

class SearchRunbooksInput(BaseModel):
    """Validates arguments for search_runbooks tool."""
    
    query: str = Field(
        ...,  # Required
        min_length=3,
        max_length=100,
        description="Search keywords (e.g., 'database timeout', 'memory leak')"
    )
    max_results: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum results to return (1-20)"
    )


# ============================================================================
# TOOL IMPLEMENTATION
# ============================================================================

def search_runbooks(query: str, max_results: int = 5) -> str:
    """Search runbooks for troubleshooting steps and incident procedures.
    
    Use ONLY if user mentions: incident, error, failure, alert, SOP, 
    troubleshooting, workaround, root cause, or outage.
    
    Do NOT use for: general knowledge, conceptual questions, learning, 
    or non-incident contexts.
    
    Args:
        query: Search term extracted from user message (validated: 3-100 chars)
        max_results: Max runbooks to return (validated: 1-20)
        
    Returns:
        Structured runbook instructions (steps, context, contact info) 
        or error message if validation fails or no runbooks found
    """
    
    # Validate inputs
    try:
        validated = SearchRunbooksInput(query=query, max_results=max_results)
    except ValidationError as e:
        error_msg = e.errors()[0]['msg'] if e.errors() else "Validation failed"
        return f"❌ Invalid arguments: {error_msg}"
    
    # Query ChromaDB with validated inputs
    collection = _get_collection()
    results = db_search(
        collection=collection,
        query=validated.query,
        n_results=validated.max_results
    )
    
    # Format results for LLM consumption
    if not results:
        return f"❌ No matching runbooks found for: '{validated.query}'"
    
    # Build formatted response with runbook summaries
    response = f"✅ Found {len(results)} matching runbooks for: '{validated.query}'\n\n"
    for i, result in enumerate(results, 1):
        response += f"**{i}. {result['id']} — {result['title']}**\n"
        response += f"   Severity: {result['severity']} | Match score: {1 - result['distance']:.2f}\n"
        response += f"   Preview: {result['document_preview']}\n\n"
    
    return response