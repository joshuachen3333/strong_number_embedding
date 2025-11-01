"""
Semantic Similarity Engines

This package contains concrete implementations of the SemanticEngine interface.

Available Engines:
- EditDistanceEngine: Character-based similarity using Levenshtein distance
- (Future) SentenceTransformerEngine: Semantic embeddings using neural models
- (Future) ChineseBertEngine: BERT-based semantic similarity

Created: 2025-11-01
Phase: 2.1 (Architecture Refactor)
"""

from .edit_distance_engine import EditDistanceEngine

__all__ = ['EditDistanceEngine']
