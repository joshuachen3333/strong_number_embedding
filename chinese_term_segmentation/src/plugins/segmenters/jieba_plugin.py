"""Jieba Chinese word segmenter plugin implementation (結巴分詞)."""

from typing import List, Dict, Optional
import logging
from src.core.plugin_interfaces import SegmenterPlugin

logger = logging.getLogger(__name__)


class JiebaPlugin(SegmenterPlugin):
    """Jieba (結巴分詞) Chinese word segmentation plugin.

    Fast and popular Chinese word segmenter with custom dictionary support.
    Ideal for general-purpose Chinese text segmentation.

    Configuration options:
        - dict_path: Path to custom dictionary file (optional)
        - hmm: Enable HMM for new word discovery (default: True)
        - mode: Segmentation mode ('accurate', 'full', 'search')
    """

    def __init__(self):
        """Initialize Jieba segmenter plugin."""
        super().__init__()
        self._jieba = None
        self._custom_dict_loaded = False

    @property
    def name(self) -> str:
        """Plugin name."""
        return "segmenter.jieba"

    @property
    def version(self) -> str:
        """Plugin version."""
        return "1.0.0"

    def validate_config(self, config: Dict) -> bool:
        """Validate configuration.

        Args:
            config: Configuration dict

        Returns:
            True if valid
        """
        valid_modes = ['accurate', 'full', 'search']
        if 'mode' in config and config['mode'] not in valid_modes:
            logger.error(f"Invalid mode: {config['mode']}. Must be one of {valid_modes}")
            return False

        if 'dict_path' in config:
            import os
            if not os.path.exists(config['dict_path']):
                logger.warning(f"Dictionary path does not exist: {config['dict_path']}")

        return True

    def initialize(self, config: Dict) -> None:
        """Initialize jieba with configuration.

        Args:
            config: Configuration dict
        """
        super().initialize(config)

        try:
            import jieba
            self._jieba = jieba
            logger.info("Jieba library loaded successfully")

            # Load custom dictionary if specified
            if 'dict_path' in config:
                self.load_dictionary(config['dict_path'])

        except ImportError:
            raise RuntimeError(
                "Jieba library not installed. Install with: pip install jieba"
            )

    def segment(self, text: str, context: Optional[Dict] = None) -> List[str]:
        """Segment Chinese text into words.

        Args:
            text: Raw Chinese text string
            context: Optional context (not used in jieba)

        Returns:
            List of word segments
        """
        if not self.is_initialized or self._jieba is None:
            raise RuntimeError(f"{self.name} not initialized")

        mode = self._config.get('mode', 'accurate') if self._config else 'accurate'
        hmm = self._config.get('hmm', True) if self._config else True

        if mode == 'accurate':
            segments = list(self._jieba.cut(text, HMM=hmm))
        elif mode == 'full':
            segments = list(self._jieba.cut(text, cut_all=True))
        elif mode == 'search':
            segments = list(self._jieba.cut_for_search(text))
        else:
            segments = list(self._jieba.cut(text, HMM=hmm))

        return segments

    def segment_with_metadata(
        self,
        text: str,
        context: Optional[Dict] = None
    ) -> List[Dict]:
        """Segment with metadata (position, POS tags).

        Args:
            text: Raw Chinese text string
            context: Optional context

        Returns:
            List of dicts with 'word', 'position', 'pos' keys
        """
        if not self.is_initialized or self._jieba is None:
            raise RuntimeError(f"{self.name} not initialized")

        # Get segments
        segments = self.segment(text, context)

        # Get POS tags if posseg is available
        try:
            import jieba.posseg as pseg
            words_with_pos = list(pseg.cut(text))

            result = []
            for i, (word, pos) in enumerate(words_with_pos):
                result.append({
                    'word': word,
                    'position': i,
                    'pos': pos,
                    'confidence': 1.0  # Jieba doesn't provide confidence scores
                })
            return result

        except ImportError:
            # Fallback without POS tags
            return [
                {
                    'word': word,
                    'position': i,
                    'pos': None,
                    'confidence': 1.0
                }
                for i, word in enumerate(segments)
            ]

    def supports_custom_dictionary(self) -> bool:
        """Jieba supports custom dictionaries.

        Returns:
            True
        """
        return True

    def load_dictionary(self, dict_path: str) -> None:
        """Load custom dictionary.

        Args:
            dict_path: Path to dictionary file (one word per line)
        """
        if not self.is_initialized or self._jieba is None:
            raise RuntimeError(f"{self.name} not initialized. Call initialize() first.")

        try:
            self._jieba.load_userdict(dict_path)
            self._custom_dict_loaded = True
            logger.info(f"Loaded custom dictionary from {dict_path}")
        except Exception as e:
            logger.error(f"Failed to load dictionary from {dict_path}: {e}")
            raise

    def shutdown(self) -> None:
        """Shutdown plugin and cleanup resources."""
        super().shutdown()
        self._jieba = None
        self._custom_dict_loaded = False
