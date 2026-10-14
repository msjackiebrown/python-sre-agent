"""ChromaDB data access layer — pure storage operations.

LAYER 1 = DATA ACCESS (The Foundation)
========================================

This module ONLY handles database CRUD operations. It does NOT know about:
- File I/O (.md files on disk)
- YAML parsing, regex, frontmatter
- User input or output
- Business rules ("what makes a valid runbook")

WHY THIS SEPARATION?
--------------------
1. Swap databases easily: Change ChromaDB → Weaviate? Only edit THIS file.
2. Test independently: Test storage logic without loading any .md files.
3. Reuse everywhere: Same CRUD functions work for CLI, API server, or tests.

THE LAYER RULE — NEVER SKIP LAYERS:
-------------------------------------
   main.py (Layer 3) → calls → tools.py (Layer 2) → calls → db.py (Layer 1)
   
   Layer 3 can call Layer 2 ✓    Layer 3 CANNOT call Layer 1 directly ✗
   Layer 2 can call Layer 1 ✓    Layer 1 CANNOT call Layer 2 or 3 ✗

WHAT THIS MODULE CONTAINS:
---------------------------
- init_collection()   → Create/get ChromaDB collection
- add_runbook()       → INSERT into vector store  
- search_runbooks()   → QUERY by semantic similarity
- remove_runbook()    → DELETE from vector store
- count_runbooks()    → COUNT documents in collection

WHAT THIS MODULE DOES NOT CONTAIN:
-----------------------------------
- File reading (.md on disk) ← belongs in tools.py (Layer 2)
- YAML parsing ← belongs in tools.py (Layer 2)
- User input/output ← belongs in main.py (Layer 3)
- Validation rules ← belongs in tools.py (Layer 2)

PRACTICAL EXAMPLE — When you need to search:
----------------------------------------------
Step 1: You call the DATABASE layer directly → db.py
   >>> db.init_collection("my_runbooks")
   >>> results = db.search_runbooks(collection, "database timeout")

Step 2: Your tools layer uses it → tools.py (orphan function)
   def search(query):
       collection = get_my_collection()    # Get existing connection
       return db.search_runbooks(collection, query)  # Use db layer

Step 3: Your CLI calls the tools layer → main.py
   query = input("Enter query: ")
   results = search(query)    # Call tools layer — never talk to db.py directly!

WHY THE "ORPHAN FUNCTION" PATTERN?
-----------------------------------
In this project we use an ORPHAN FUNCTION pattern (not a class).
Each file has one main function that orphans onto the others:
- db.py has init_collection()  → tools.py calls it to get collection
- tools.py has search_runbooks() → main.py calls it to do work
- main.py has main()           → user calls it to start everything

This keeps things SIMPLE for a beginner — no classes, no complex patterns.