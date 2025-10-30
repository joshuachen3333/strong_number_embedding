"""LAC (Lexical Analysis of Chinese) plugin for Chinese word segmentation.

LAC is developed by Baidu and uses Bi-GRU-CRF model for segmentation,
POS tagging, and named entity recognition.

Installation:
    pip install LAC

Documentation:
    https://github.com/baidu/lac
"""

from typing import Dict, List, Optional
from ...core.plugin_interfaces import SegmenterPlugin
import logging

logger = logging.getLogger(__name__)


class LACPlugin(SegmenterPlugin):
    """LAC (Baidu Lexical Analysis of Chinese) segmenter plugin."""

    def __init__(self):
        self._lac = None
        self._available = False

        # Check if LAC is available
        try:
            from LAC import LAC as LACSegmenter
            self._LAC = LACSegmenter
            self._available = True
        except ImportError:
            logger.warning(
                "LAC not installed. Install with: pip install LAC\n"
                "See: https://github.com/baidu/lac"
            )
            self._LAC = None
            self._available = False

    @property
    def name(self) -> str:
        return "lac"

    @property
    def version(self) -> str:
        if not self._available:
            return "not-installed"
        try:
            import LAC
            return getattr(LAC, '__version__', 'unknown')
        except:
            return "unknown"

    @property
    def supports_custom_dict(self) -> bool:
        return True

    def validate_config(self, config: Dict) -> bool:
        """Validate LAC configuration."""
        if not self._available:
            return False

        valid_modes = ['seg', 'lac']  # seg=segmentation only, lac=full analysis
        if 'mode' in config and config['mode'] not in valid_modes:
            return False
        return True

    def initialize(self, config: Optional[Dict] = None) -> None:
        """Initialize LAC segmenter.

        Config options:
            mode: 'seg' (segmentation only) or 'lac' (full analysis with POS)
            model_path: Custom model path (optional)
        """
        if not self._available:
            raise ImportError(
                "LAC is not installed. Install with: pip install LAC\n"
                "See: https://github.com/baidu/lac"
            )

        config = config or {}

        mode = config.get('mode', 'seg')
        model_path = config.get('model_path', None)

        # Initialize LAC
        if model_path:
            self._lac = self._LAC(model_path=model_path, mode=mode)
        else:
            self._lac = self._LAC(mode=mode)

        logger.info(f"LAC initialized (mode={mode})")

    def segment(self, text: str, context: Optional[Dict] = None) -> List[str]:
        """Segment Chinese text using LAC.

        Args:
            text: Chinese text to segment
            context: Optional context (not used for LAC)

        Returns:
            List of word segments
        """
        if not self._available or self._lac is None:
            raise RuntimeError(
                "LAC not initialized. Call initialize() first or install LAC."
            )

        # LAC returns (words, tags) tuple
        result = self._lac.run(text)

        # If result is a tuple, extract just the words
        if isinstance(result, tuple):
            words, tags = result
            return words
        else:
            # In 'seg' mode, might return just words
            return result

    def load_dictionary(self, dict_path: str) -> None:
        """Load custom dictionary for LAC.

        Args:
            dict_path: Path to custom dictionary file
        """
        if not self._available or self._lac is None:
            raise RuntimeError("LAC not initialized")

        # LAC supports custom dictionary loading
        self._lac.load_customization(dict_path)
        logger.info(f"LAC custom dictionary loaded: {dict_path}")

    def get_pos_tags(self, text: str) -> List[tuple]:
        """Get segmentation with POS tags.

        Args:
            text: Chinese text to analyze

        Returns:
            List of (word, pos_tag) tuples
        """
        if not self._available or self._lac is None:
            raise RuntimeError("LAC not initialized")

        words, tags = self._lac.run(text)
        return list(zip(words, tags))
