from pydantic import BaseModel, Field, ValidationError

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
    
    # TODO: Query ChromaDB with validated.query
    # TODO: Return formatted results from validated.max_results runbooks
    
    # Placeholder implementation
    return f"🔍 Searching for: '{validated.query}' (max {validated.max_results} results)\n\nNo matching runbook found"