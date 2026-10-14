"""ChromaDB data access layer — pure database operations.

This module ONLY handles storage mechanics (add, remove, search).
It does NOT know about files, ingestion, or user interfaces.

Why this separation?
- Database logic is reusable across all layers (CLI can use same API as API server)
- You can swap ChromaDB for another vector store later (just change THIS file)
- Tests stay simple: test storage logic independently from file I/O
"""
import chromadb
import yaml
from pathlib import Path


def init_collection(collection_name: str = "runbooks", space: str = "cosine") -> tuple:
    """Create or get a ChromaDB collection.
    
    Args:
        collection_name: Name of the collection to create/get
        space: Similarity metric (e.g., 'cosine', 'euclidean', 'ip')
        
    Returns:
        Tuple of (client, collection) for later use
    """
    client = chromadb.EphemeralClient()
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": space}
    )
    return (client, collection)


def add_runbook(collection, runbook_id: str, document: str, metadata: dict) -> bool:
    """Add a single runbook to the vector store.
    
    Args:
        collection: ChromaDB collection object
        runbook_id: Unique identifier (e.g., 'INCIDENT-001')
        document: Full runbook markdown text (what gets searched)
        metadata: YAML frontmatter fields (used for filtering)
        
    Returns:
        True if added successfully, False if duplicate ID exists
    """
    try:
        collection.add(
            documents=[document],
            metadatas=[metadata],
            ids=[runbook_id]
        )
        return True
    except ValueError as e:
        # ChromaDB raises ValueError on duplicate IDs
        if "already exists" in str(e):
            return False
        raise


def add_runbooks_batch(collection, runbooks: list[dict]) -> int:
    """Add multiple runbooks to the vector store.
    
    Args:
        collection: ChromaDB collection object
        runbooks: List of dicts with keys: id, document, metadata
        
    Returns:
        Number of runbooks successfully added
    """
    ids = [r["id"] for r in runbooks]
    documents = [r["document"] for r in runbooks]
    metadatas = [r["metadata"] for r in runbooks]
    
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    return len(runbooks)


def search_runbooks(collection, query: str, n_results: int = 3) -> list[dict]:
    """Search runbooks by semantic similarity.
    
    Args:
        collection: ChromaDB collection object
        query: Search keywords (e.g., 'database timeout')
        n_results: Max number of results to return
        
    Returns:
        List of dicts: [{id, title, severity, distance, document_preview}, ...]
    """
    if collection.count() == 0:
        return []
    
    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        include=["documents", "metadatas", "distances"]
    )
    
    matching = []
    for i in range(len(results["ids"][0])):
        matching.append({
            "id": results["ids"][0][i],
            "title": results["metadatas"][0][i].get("title", ""),
            "severity": results["metadatas"][0][i].get("severity", "unknown"),
            "distance": results["distances"][0][i],
            "document_preview": results["documents"][0][i][:200] + "...",
        })
    return matching


def remove_runbook(collection, runbook_id: str) -> bool:
    """Remove a single runbook from the collection.
    
    Args:
        collection: ChromaDB collection object
        runbook_id: ID of runbook to remove
        
    Returns:
        True if deleted successfully, False if not found
    """
    try:
        collection.delete(ids=[runbook_id])
        return True
    except ValueError:
        # Runbook ID doesn't exist
        return False


def count_runbooks(collection) -> int:
    """Return number of runbooks in the collection."""
    return collection.count()


# ============================================================================
# PHASE 2: RUNBOOK LOADING — Parse markdown + bulk ingest
# ============================================================================

def parse_frontmatter(markdown: str) -> dict:
    """Extract YAML frontmatter from markdown document.
    
    Args:
        markdown: Markdown text with optional YAML frontmatter block
        
    Returns:
        Dictionary of frontmatter key-value pairs, or {} if not found/empty
        
    Example:
        >>> md = '''---
        ... id: INCIDENT-001
        ... title: Database Timeout
        ... ---
        ... Body text'''
        >>> parse_frontmatter(md)
        {'id': 'INCIDENT-001', 'title': 'Database Timeout'}
    """
    if not markdown.startswith("---"):
        return {}
    
    # Find the closing --- marker
    parts = markdown.split("---", 2)
    if len(parts) < 3:
        return {}
    
    frontmatter_block = parts[1].strip()
    if not frontmatter_block:
        return {}
    
    try:
        return yaml.safe_load(frontmatter_block) or {}
    except yaml.YAMLError:
        return {}


def seed_runbooks(
    data_dir: str = "src/data",
    collection_name: str = "runbooks"
) -> tuple:
    """Load all markdown runbooks from directory into ChromaDB collection.
    
    Args:
        data_dir: Directory containing .md runbook files
        collection_name: Name of the ChromaDB collection to create/use
        
    Returns:
        Tuple of (collection, count) where count is number of runbooks seeded
        
    Example:
        >>> collection, count = seed_runbooks("src/data")
        >>> print(f"Loaded {count} runbooks")
        Loaded 7 runbooks
    """
    # Initialize collection
    _, collection = init_collection(collection_name=collection_name)
    
    # Discover all .md files
    data_path = Path(data_dir)
    if not data_path.exists():
        return (collection, 0)
    
    md_files = sorted(data_path.glob("*.md"))
    
    # Load and ingest each file
    runbooks = []
    for filepath in md_files:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Extract frontmatter for metadata
        metadata = parse_frontmatter(content)
        if not metadata or "id" not in metadata:
            continue  # Skip files without valid frontmatter + id
        
        runbook_id = metadata["id"]
        runbooks.append({
            "id": runbook_id,
            "document": content,
            "metadata": metadata
        })
    
    # Bulk add to ChromaDB
    if runbooks:
        add_runbooks_batch(collection, runbooks)
    
    return (collection, len(runbooks))


# ============================================================================
# MODULE ENTRY POINT — Test seeding at module run
# ============================================================================

if __name__ == "__main__":
    print("🚀 Phase 2: Data Ingestion - Testing ChromaDB + Runbook Seeding")
    print("=" * 70)
    
    # Load all runbooks from src/data
    collection, count = seed_runbooks()
    print(f"✅ Seeded {count} runbooks into ChromaDB (cosine similarity)")
    
    # Test search
    if count > 0:
        print(f"\n📚 Collection contains {count_runbooks(collection)} runbooks")
        
        # Try a sample search
        sample_query = "database timeout connection pool"
        results = search_runbooks(collection, query=sample_query, n_results=2)
        print(f"\n🔍 Test search: '{sample_query}'")
        for r in results:
            print(f"  - {r['id']} ({r['severity']}): {r['distance']:.3f}")
    else:
        print("⚠️  No runbooks found in src/data. Check data files exist with frontmatter.")
