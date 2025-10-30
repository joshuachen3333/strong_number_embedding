"""Plugin type interfaces for segmentation, embedding, alignment, and scoring.

Note: 'Segmentation' (分詞) refers to splitting Chinese text into words.
Neural model tokenizers (e.g., BertTokenizer) are internal to EmbeddingPlugin implementations.
"""

from abc import abstractmethod
from typing import List, Dict, Optional, Tuple
import numpy as np
from .plugin_base import Plugin


class SegmenterPlugin(Plugin):
    """Interface for Chinese word segmentation strategies (分詞工具).

    Segmenters break Chinese text into meaningful word/term units.
    Supports custom dictionaries for biblical terminology.

    Note: This is NOT for neural model tokenizers (BertTokenizer, etc.),
    which are internal to embedding plugin implementations.
    """

    @abstractmethod
    def segment(self, text: str, context: Optional[Dict] = None) -> List[str]:
        """Segment Chinese text into words/terms.

        Args:
            text: Raw Chinese text string to segment
            context: Optional context (verse references, surrounding text)

        Returns:
            List of word segments (strings)
        """
        pass

    @abstractmethod
    def segment_with_metadata(
        self,
        text: str,
        context: Optional[Dict] = None
    ) -> List[Dict]:
        """Segment with rich metadata (POS tags, confidence, etc.).

        Args:
            text: Raw Chinese text string to segment
            context: Optional context

        Returns:
            List of dicts with keys: 'word', 'position', 'pos', 'confidence'
        """
        pass

    @abstractmethod
    def supports_custom_dictionary(self) -> bool:
        """Whether this segmenter supports custom dictionaries.

        Returns:
            True if custom dictionaries supported, False otherwise
        """
        pass

    def load_dictionary(self, dict_path: str) -> None:
        """Load custom dictionary for segmentation.

        Args:
            dict_path: Path to dictionary file

        Raises:
            NotImplementedError: If custom dictionaries not supported
        """
        if not self.supports_custom_dictionary():
            raise NotImplementedError(
                f"{self.name} does not support custom dictionaries"
            )

    # Backward compatibility aliases (deprecated)
    def tokenize(self, text: str, context: Optional[Dict] = None) -> List[str]:
        """Deprecated: Use segment() instead."""
        return self.segment(text, context)

    def tokenize_with_metadata(
        self,
        text: str,
        context: Optional[Dict] = None
    ) -> List[Dict]:
        """Deprecated: Use segment_with_metadata() instead."""
        return self.segment_with_metadata(text, context)


class EmbeddingPlugin(Plugin):
    """Interface for word/sentence embedding strategies.

    Embeddings convert text into dense vector representations for
    semantic similarity calculations.
    """

    @abstractmethod
    def embed(self, text: str, context: Optional[Dict] = None) -> np.ndarray:
        """Generate embedding vector for text.

        Args:
            text: Text to embed
            context: Optional context for contextualized embeddings

        Returns:
            Embedding vector as numpy array
        """
        pass

    def batch_embed(self, texts: List[str]) -> np.ndarray:
        """Efficiently embed multiple texts.

        Args:
            texts: List of text strings

        Returns:
            2D numpy array of embeddings (one row per text)
        """
        # Default implementation - can be overridden for efficiency
        return np.array([self.embed(text) for text in texts])

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Embedding vector dimension.

        Returns:
            Dimension of embedding vectors
        """
        pass

    @abstractmethod
    def supports_contextualization(self) -> bool:
        """Whether embeddings are context-aware.

        Returns:
            True for contextual (BERT-like), False for static (Word2Vec)
        """
        pass


class AlignmentPlugin(Plugin):
    """Interface for alignment strategies.

    Aligners match source tokens to target tokens using semantic
    and positional similarity.
    """

    @abstractmethod
    def align(
        self,
        source_tokens: List[Dict],
        target_tokens: List[Dict],
        context: Optional[Dict] = None
    ) -> List[Tuple[int, int, float]]:
        """Align source and target tokens.

        Args:
            source_tokens: List of source token dicts with 'word', 'position', etc.
            target_tokens: List of target token dicts
            context: Optional context (surrounding verses, etc.)

        Returns:
            List of (source_idx, target_idx, confidence) tuples
        """
        pass

    @abstractmethod
    def supports_many_to_many(self) -> bool:
        """Whether this aligner supports many-to-many alignments.

        Returns:
            True if many-to-many supported, False if one-to-one only
        """
        pass

    @abstractmethod
    def confidence_threshold(self) -> float:
        """Minimum confidence for accepting an alignment.

        Returns:
            Confidence threshold (0.0 to 1.0)
        """
        pass


class ScorerPlugin(Plugin):
    """Interface for scoring/evaluation strategies.

    Scorers evaluate alignment quality against gold standards and
    calculate confidence scores.
    """

    @abstractmethod
    def score(
        self,
        predicted: List[Tuple],
        gold: List[Tuple]
    ) -> Dict[str, float]:
        """Score predicted alignments against gold standard.

        Args:
            predicted: List of predicted alignments (source_idx, target_idx, conf)
            gold: List of gold standard alignments

        Returns:
            Dict with metrics: {'precision': 0.85, 'recall': 0.82, 'f1': 0.83, ...}
        """
        pass

    def confidence_score(self, alignment: Tuple) -> float:
        """Calculate confidence score for single alignment.

        Args:
            alignment: (source_idx, target_idx, score) tuple

        Returns:
            Confidence value between 0.0 and 1.0
        """
        # Default: use alignment score directly
        return alignment[2] if len(alignment) > 2 else 0.0
