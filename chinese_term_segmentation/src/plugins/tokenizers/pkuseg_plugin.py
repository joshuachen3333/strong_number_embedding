"""PKUSeg tokenizer plugin implementation."""

from typing import List, Dict, Optional
import logging
from src.core.plugin_interfaces import TokenizerPlugin

logger = logging.getLogger(__name__)


class PKUSegPlugin(TokenizerPlugin):
    """PKU (北大分詞) Chinese word segmentation plugin.

    Higher accuracy segmentation with domain-specific model support.
    Slower than jieba but more accurate for specialized text.

    Configuration options:
        - model_name: Pre-trained model ('default', 'news', 'web', 'medicine', 'tourism')
        - dict_path: Path to custom dictionary file (optional)
        - postag: Enable POS tagging (default: False)
    """

    def __init__(self):
        """Initialize PKUSeg plugin."""
        super().__init__()
        self._seg = None
        self._custom_dict_loaded = False

    @property
    def name(self) -> str:
        """Plugin name."""
        return "tokenizer.pkuseg"

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
        valid_models = ['default', 'news', 'web', 'medicine', 'tourism']
        if 'model_name' in config and config['model_name'] not in valid_models:
            logger.error(f"Invalid model_name: {config['model_name']}. Must be one of {valid_models}")
            return False

        return True

    def initialize(self, config: Dict) -> None:
        """Initialize PKUSeg with configuration.

        Args:
            config: Configuration dict
        """
        super().initialize(config)

        try:
            import pkuseg

            model_name = config.get('model_name', 'default')
            postag = config.get('postag', False)

            # Initialize segmenter
            if model_name == 'default':
                self._seg = pkuseg.pkuseg(postag=postag)
            else:
                self._seg = pkuseg.pkuseg(model_name=model_name, postag=postag)

            logger.info(f"PKUSeg loaded with model: {model_name}, postag: {postag}")

            # Load custom dictionary if specified
            if 'dict_path' in config:
                self.load_dictionary(config['dict_path'])

        except ImportError:
            raise RuntimeError(
                "PKUSeg library not installed. Install with: pip install pkuseg"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize PKUSeg: {e}")

    def tokenize(self, text: str, context: Optional[Dict] = None) -> List[str]:
        """Tokenize Chinese text.

        Args:
            text: Raw Chinese text string
            context: Optional context (not used in pkuseg)

        Returns:
            List of word tokens
        """
        if not self.is_initialized or self._seg is None:
            raise RuntimeError(f"{self.name} not initialized")

        try:
            tokens = self._seg.cut(text)
            return tokens
        except Exception as e:
            logger.error(f"Error during tokenization: {e}")
            return []

    def tokenize_with_metadata(
        self,
        text: str,
        context: Optional[Dict] = None
    ) -> List[Dict]:
        """Tokenize with metadata (position, POS tags if available).

        Args:
            text: Raw Chinese text string
            context: Optional context

        Returns:
            List of dicts with 'word', 'position', 'pos' keys
        """
        if not self.is_initialized or self._seg is None:
            raise RuntimeError(f"{self.name} not initialized")

        postag = self._config.get('postag', False) if self._config else False

        try:
            if postag:
                # PKUSeg with POS tags returns list of tuples
                result = []
                words_with_pos = self._seg.cut(text)

                for i, item in enumerate(words_with_pos):
                    if isinstance(item, tuple):
                        word, pos = item
                    else:
                        word, pos = item, None

                    result.append({
                        'word': word,
                        'position': i,
                        'pos': pos,
                        'confidence': 1.0  # PKUSeg doesn't provide confidence
                    })
                return result
            else:
                # Without POS tags
                tokens = self.tokenize(text, context)
                return [
                    {
                        'word': word,
                        'position': i,
                        'pos': None,
                        'confidence': 1.0
                    }
                    for i, word in enumerate(tokens)
                ]

        except Exception as e:
            logger.error(f"Error during tokenization with metadata: {e}")
            return []

    def supports_custom_dictionary(self) -> bool:
        """PKUSeg supports custom dictionaries.

        Returns:
            True
        """
        return True

    def load_dictionary(self, dict_path: str) -> None:
        """Load custom dictionary.

        Note: PKUSeg requires reinitialization with custom dictionary.

        Args:
            dict_path: Path to dictionary file (one word per line)
        """
        if not self.is_initialized:
            raise RuntimeError(f"{self.name} not initialized. Call initialize() first.")

        try:
            import pkuseg

            model_name = self._config.get('model_name', 'default') if self._config else 'default'
            postag = self._config.get('postag', False) if self._config else False

            # Reinitialize with custom dictionary
            if model_name == 'default':
                self._seg = pkuseg.pkuseg(user_dict=dict_path, postag=postag)
            else:
                self._seg = pkuseg.pkuseg(
                    model_name=model_name,
                    user_dict=dict_path,
                    postag=postag
                )

            self._custom_dict_loaded = True
            logger.info(f"Loaded custom dictionary from {dict_path}")

        except Exception as e:
            logger.error(f"Failed to load dictionary from {dict_path}: {e}")
            raise

    def shutdown(self) -> None:
        """Shutdown plugin and cleanup resources."""
        super().shutdown()
        self._seg = None
        self._custom_dict_loaded = False
