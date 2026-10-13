## Description
<!-- Briefly describe what changes you made (e.g., "Implemented search_runbooks tool using ChromaDB") -->

## Phase Gate Check
- [ ] Does this code run locally without Cloud dependencies?
- [ ] Have I added unit tests for any new tools or logic?
- [ ] Did I update the PROJECT_GUIDE.md if I solved one of the design questions?
- [ ] Is the tool schema clearly defined in Ollama JSON format?

## Testing Steps
<!-- How can a reviewer verify this works? -->
1. Run `ollama pull llama3` (or supported model)
2. Run `python src/main.py`
3. Ask: "..."
