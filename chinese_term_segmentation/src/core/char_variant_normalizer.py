"""Character variant normalizer for Chinese text.

Handles Unicode character variants commonly found in different Chinese Bible
translations (LCC vs UNV), converting them to standard forms for matching.

Common variants in biblical texts:
- 爲 (U+7232, ancient/variant) → 為 (U+70BA, modern standard)
- 衞 (U+885E, variant) → 衛 (U+885B, modern standard)
- 綫 (U+7DAB, variant) → 線 (U+7DDA, modern standard)
- 眞 (U+771E, variant) → 真 (U+771F, modern standard)
- 羣 (U+7FA3, variant) → 群 (U+7FA4, modern standard)
"""

from typing import Dict


class CharVariantNormalizer:
    """Normalizes Chinese character variants to standard forms.

    Uses a mapping dictionary to convert variant characters to their standard
    equivalents, enabling better text matching across Bible versions.

    Example:
        >>> normalizer = CharVariantNormalizer()
        >>> normalizer.normalize("因爲")
        '因為'
        >>> normalizer.normalize("衞兵")
        '衛兵'
    """

    # Character variant mapping: variant → standard
    # Sourced from common biblical text variants and Unicode variant databases
    VARIANT_MAP: Dict[str, str] = {
        # 為 variants
        '爲': '為',  # U+7232 → U+70BA (most common in LCC)

        # 衛 variants
        '衞': '衛',  # U+885E → U+885B

        # 線 variants
        '綫': '線',  # U+7DAB → U+7DDA

        # 真 variants
        '眞': '真',  # U+771E → U+771F

        # 群 variants
        '羣': '群',  # U+7FA3 → U+7FA4

        # 說 variants
        '説': '說',  # U+8AAC → U+8AAA

        # 讀 variants
        '讀': '讀',  # U+FA19 → U+8B80 (normalize to standard form)

        # 著 variants
        '着': '著',  # U+7740 → U+8457 (context-dependent, but safe for matching)

        # 與 variants
        '与': '與',  # U+4E0E → U+8207 (simplified to traditional)

        # 啓 variants
        '启': '啟',  # U+542F → U+5553 (simplified to traditional)

        # Add more variants as discovered in testing
    }

    def __init__(self, custom_variants: Dict[str, str] = None):
        """Initialize the normalizer.

        Args:
            custom_variants: Optional additional variant mappings to use.
                            Will override default mappings if keys conflict.
        """
        self.variant_map = self.VARIANT_MAP.copy()
        if custom_variants:
            self.variant_map.update(custom_variants)

    def normalize(self, text: str) -> str:
        """Normalize all character variants in text to standard forms.

        Args:
            text: Input text with potential variant characters

        Returns:
            Text with all variants replaced by standard forms

        Example:
            >>> normalizer = CharVariantNormalizer()
            >>> normalizer.normalize("因爲上帝衞護")
            '因為上帝衛護'
        """
        if not text:
            return text

        # Use str.translate for efficient character-by-character replacement
        translation_table = str.maketrans(self.variant_map)
        return text.translate(translation_table)

    def has_variants(self, text: str) -> bool:
        """Check if text contains any known variant characters.

        Args:
            text: Input text to check

        Returns:
            True if text contains variant characters, False otherwise

        Example:
            >>> normalizer = CharVariantNormalizer()
            >>> normalizer.has_variants("因爲")
            True
            >>> normalizer.has_variants("因為")
            False
        """
        return any(char in self.variant_map for char in text)

    def get_variants(self, text: str) -> Dict[str, str]:
        """Get all variant characters found in text with their standard forms.

        Args:
            text: Input text to analyze

        Returns:
            Dictionary mapping found variants to their standard forms

        Example:
            >>> normalizer = CharVariantNormalizer()
            >>> normalizer.get_variants("因爲上帝衞護")
            {'爲': '為', '衞': '衛'}
        """
        found_variants = {}
        for char in text:
            if char in self.variant_map:
                found_variants[char] = self.variant_map[char]
        return found_variants

    def add_variant(self, variant: str, standard: str):
        """Add a new variant mapping.

        Args:
            variant: The variant character
            standard: The standard form to normalize to

        Example:
            >>> normalizer = CharVariantNormalizer()
            >>> normalizer.add_variant('鳥', '鸟')
            >>> normalizer.normalize("飛鳥")
            '飛鸟'
        """
        self.variant_map[variant] = standard

    def remove_variant(self, variant: str):
        """Remove a variant mapping.

        Args:
            variant: The variant character to remove from mapping
        """
        self.variant_map.pop(variant, None)

    @classmethod
    def get_all_variants(cls) -> Dict[str, str]:
        """Get all default variant mappings.

        Returns:
            Copy of the default variant mapping dictionary
        """
        return cls.VARIANT_MAP.copy()


# Global singleton instance for convenience
_default_normalizer = None


def get_normalizer() -> CharVariantNormalizer:
    """Get the default global normalizer instance.

    Returns:
        Global CharVariantNormalizer instance
    """
    global _default_normalizer
    if _default_normalizer is None:
        _default_normalizer = CharVariantNormalizer()
    return _default_normalizer


def normalize(text: str) -> str:
    """Convenience function to normalize text using default normalizer.

    Args:
        text: Input text with potential variant characters

    Returns:
        Text with all variants replaced by standard forms
    """
    return get_normalizer().normalize(text)
