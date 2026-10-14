def search_runbooks(query: str) -> str:
  """Search runbooks for troubleshooting steps and incident procedures.
  
  Use ONLY if user mentions: incident, error, failure, alert, SOP, 
  troubleshooting, workaround, root cause, or outage.
  
  Do NOT use for: general knowledge, conceptual questions, learning, 
  or non-incident contexts.
  
  Args:
    query: Search term extracted from user message
    
  Returns:
    Structured runbook instructions (steps, context, contact info) 
    or "No matching runbook found" if no relevant runbook exists
  """
  # Implement the search logic here
  # For now, return a placeholder response
  return "No matching runbook found"