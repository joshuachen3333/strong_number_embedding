"""
Semantic Similarity Engines

This package contains concrete implementations of the SemanticEngine interface.

Available Engines:
- EditDistanceEngine: Character-based similarity using Levenshtein distance (Phase 2.1)
- SentenceTransformerEngine: Neural semantic embeddings (Phase 2.2.1)
- (Future) ChineseBertEngine: BERT-based semantic similarity (Phase 2.2.1)

Created: 2025-11-01
Updated: Phase 2.2.1 (Neural Engines)
"""

from .edit_distance_engine import EditDistanceEngine

# Optional neural engines (graceful import)
try:
    from .sentence_transformer_engine import SentenceTransformerEngine
    __all__ = ['EditDistanceEngine', 'SentenceTransformerEngine']
except ImportError:
    # sentence-transformers not installed
    __all__ = ['EditDistanceEngine']
