"""Stanza (Stanford NLP) Chinese word segmenter plugin implementation.

Stanza is Stanford NLP's neural pipeline for many human languages.
It provides state-of-the-art performance with pre-trained neural models.

Installation:
    pip install stanza
    # Download Chinese model:
    import stanza
    stanza.download('zh')

Documentation:
    https://stanfordnlp.github.io/stanza/
"""

from typing import Dict, List, Optional
from ...core.plugin_interfaces import SegmenterPlugin
import logging

logger = logging.getLogger(__name__)


class StanzaPlugin(SegmenterPlugin):
    """Stanza (Stanford NLP) Chinese word segmentation plugin.

    Academic-grade neural segmenter with high accuracy.
    Uses pre-trained neural models from Stanford NLP Group.

    Configuration options:
        - lang: Language code (default: 'zh' for Chinese)
        - processors: Pipeline processors (default: 'tokenize')
        - tokenize_pretokenized: Process pre-tokenized text
        - use_gpu: Use GPU if available (default: False)
    """

    def __init__(self):
        """Initialize Stanza segmenter plugin."""
        super().__init__()
        self._stanza = None
        self._pipeline = None
        self._available = False

        # Check if Stanza is available
        try:
            import stanza
            self._stanza = stanza
            self._available = True
        except ImportError:
            logger.warning(
                "Stanza not installed. Install with: pip install stanza\n"
                "Then download Chinese model: import stanza; stanza.download('zh')\n"
                "See: https://stanfordnlp.github.io/stanza/"
            )
            self._stanza = None
            self._available = False

    @property
    def name(self) -> str:
        """Plugin name."""
        return "segmenter.stanza"

    @property
    def version(self) -> str:
        """Plugin version."""
        if not self._available:
            return "not-installed"
        try:
            return self._stanza.__version__
        except:
            return "unknown"

    def validate_config(self, config: Dict) -> bool:
        """Validate Stanza configuration.

        Args:
            config: Configuration dict

        Returns:
            True if valid
        """
        if not self._available:
            return False

        valid_langs = ['zh', 'zh-hans', 'zh-hant']
        if 'lang' in config and config['lang'] not in valid_langs:
            logger.error(
                f"Invalid language: {config['lang']}. "
                f"Must be one of {valid_langs}"
            )
            return False

        return True

    def initialize(self, config: Optional[Dict] = None) -> None:
        """Initialize Stanza segmenter.

        Args:
            config: Configuration dict
                - lang: Language code (default: 'zh')
                - processors: Pipeline processors (default: 'tokenize')
                - use_gpu: Use GPU if available (default: False)
                - download_method: None or 'auto' to auto-download models
        """
        if not self._available:
            raise ImportError(
                "Stanza is not installed. Install with: pip install stanza\n"
                "Then download Chinese model: import stanza; stanza.download('zh')\n"
                "See: https://stanfordnlp.github.io/stanza/"
            )

        super().initialize(config)
        config = config or {}

        lang = config.get('lang', 'zh')
        processors = config.get('processors', 'tokenize')
        use_gpu = config.get('use_gpu', False)
        download_method = config.get('download_method', None)

        try:
            # Auto-download models if requested
            if download_method == 'auto':
                logger.info(f"Downloading Stanza models for {lang}...")
                self._stanza.download(lang, logging_level='WARNING')

            # Initialize pipeline
            self._pipeline = self._stanza.Pipeline(
                lang=lang,
                processors=processors,
                use_gpu=use_gpu,
                logging_level='WARNING'
            )

            logger.info(f"Stanza pipeline initialized (lang={lang}, gpu={use_gpu})")

        except Exception as e:
            error_msg = (
                f"Failed to initialize Stanza pipeline: {e}\n"
                f"You may need to download the model first:\n"
                f"  import stanza\n"
                f"  stanza.download('{lang}')"
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    def segment(self, text: str, context: Optional[Dict] = None) -> List[str]:
        """Segment Chinese text using Stanza.

        Args:
            text: Chinese text to segment
            context: Optional context (not used)

        Returns:
            List of word segments
        """
        if not self._available or self._pipeline is None:
            raise RuntimeError(
                f"{self.name} not initialized. Call initialize() first or install Stanza."
            )

        try:
            # Process text through pipeline
            doc = self._pipeline(text)

            # Extract tokens from all sentences
            segments = []
            for sentence in doc.sentences:
                for token in sentence.tokens:
                    segments.append(token.text)

            return segments

        except Exception as e:
            logger.error(f"Stanza segmentation failed: {e}")
            raise

    def segment_with_metadata(
        self,
        text: str,
        context: Optional[Dict] = None
    ) -> List[Dict]:
        """Segment with metadata (position, POS tags, lemma, etc.).

        Args:
            text: Chinese text to segment
            context: Optional context

        Returns:
            List of dicts with 'word', 'position', 'pos', 'lemma', etc.
        """
        if not self._available or self._pipeline is None:
            raise RuntimeError(f"{self.name} not initialized")

        try:
            # Process text (need POS tagging)
            if 'pos' not in self._pipeline.processors:
                # Re-initialize with POS tagging
                config = self._config or {}
                config['processors'] = 'tokenize,pos'
                self.initialize(config)

            doc = self._pipeline(text)

            # Extract tokens with metadata
            result = []
            position = 0

            for sentence in doc.sentences:
                for word in sentence.words:
                    result.append({
                        'word': word.text,
                        'position': position,
                        'pos': word.upos if hasattr(word, 'upos') else word.xpos,
                        'lemma': word.lemma if hasattr(word, 'lemma') else None,
                        'confidence': 1.0  # Stanza doesn't provide confidence scores
                    })
                    position += 1

            return result

        except Exception as e:
            logger.error(f"Stanza segmentation with metadata failed: {e}")
            # Fallback to simple segmentation
            segments = self.segment(text, context)
            return [
                {
                    'word': word,
                    'position': i,
                    'pos': None,
                    'lemma': None,
                    'confidence': 1.0
                }
                for i, word in enumerate(segments)
            ]

    def supports_custom_dictionary(self) -> bool:
        """Stanza does not support custom dictionaries.

        Returns:
            False
        """
        return False

    def load_dictionary(self, dict_path: str) -> None:
        """Load custom dictionary.

        Args:
            dict_path: Path to dictionary file

        Raises:
            NotImplementedError: Stanza doesn't support custom dictionaries
        """
        raise NotImplementedError(
            "Stanza does not support custom dictionaries. "
            "It uses pre-trained neural models."
        )

    def get_available_models(self) -> List[str]:
        """Get list of available Stanza models for Chinese.

        Returns:
            List of model identifiers
        """
        if not self._available:
            return []

        try:
            # Stanza supports: zh, zh-hans, zh-hant
            return ['zh', 'zh-hans', 'zh-hant']
        except:
            return []

    def shutdown(self) -> None:
        """Shutdown plugin and cleanup resources."""
        super().shutdown()
        self._pipeline = None
