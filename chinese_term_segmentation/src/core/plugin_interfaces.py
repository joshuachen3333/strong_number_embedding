"""Plugin type interfaces for tokenization, embedding, alignment, and scoring."""

from abc import abstractmethod
from typing import List, Dict, Optional, Tuple
import numpy as np
from .plugin_base import Plugin


class TokenizerPlugin(Plugin):
    """Interface for tokenization strategies.

    Tokenizers break Chinese text into meaningful word/term units.
    Supports custom dictionaries for biblical terminology.
    """

    @abstractmethod
    def tokenize(self, text: str, context: Optional[Dict] = None) -> List[str]:
        """Tokenize text into words/terms.

        Args:
            text: Raw text string to tokenize
            context: Optional context (verse references, surrounding text)

        Returns:
            List of word tokens (strings)
        """
        pass

    @abstractmethod
    def tokenize_with_metadata(
        self,
        text: str,
        context: Optional[Dict] = None
    ) -> List[Dict]:
        """Tokenize with rich metadata.

        Args:
            text: Raw text string to tokenize
            context: Optional context

        Returns:
            List of dicts with keys: 'word', 'position', 'pos', 'confidence'
        """
        pass

    @abstractmethod
    def supports_custom_dictionary(self) -> bool:
        """Whether this tokenizer supports custom dictionaries.

        Returns:
            True if custom dictionaries supported, False otherwise
        """
        pass

    def load_dictionary(self, dict_path: str) -> None:
        """Load custom dictionary for tokenization.

        Args:
            dict_path: Path to dictionary file

        Raises:
            NotImplementedError: If custom dictionaries not supported
        """
        if not self.supports_custom_dictionary():
            raise NotImplementedError(
                f"{self.name} does not support custom dictionaries"
            )


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
