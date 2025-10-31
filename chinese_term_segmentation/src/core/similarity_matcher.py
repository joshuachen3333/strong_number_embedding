"""Similarity matching for Chinese text with pluggable engines.

提供可抽換的相似度匹配引擎，用於：
1. 子字串粒度選擇（從粗粒度詞中找出最佳子字串）
2. 字符變體處理（爲/為、衞/衛等）
3. 跨版本文本對齊

設計原則：
- 抽象接口：支援多種實現方式（編輯距離 → 詞向量 → Transformer）
- 先簡後繁：先用簡單實現上線，日後無痛升級
- 統一基礎：為跨版本映射提供一致的相似度計算
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
from difflib import SequenceMatcher


# 常見字符變體映射表（聖經文本中常見）
VARIANT_MAP = {
    # 為 的變體
    '爲': '為',  # U+7232 → U+70BA

    # 衛 的變體
    '衞': '衛',  # U+885E → U+885B

    # 線 的變體
    '綫': '線',  # U+7DAB → U+7DDA

    # 群 的變體
    '羣': '群',  # U+7FA3 → U+7FA4

    # 麼 的變體
    '麽': '麼',  # U+9EBD → U+9EBC

    # TODO: 根據實際測試結果擴充
}


def normalize_variants(text: str) -> str:
    """將字符變體規範化為標準字。

    Args:
        text: 原始文本

    Returns:
        規範化後的文本

    Example:
        >>> normalize_variants("因爲天國")
        '因為天國'
        >>> normalize_variants("大衞王")
        '大衛王'
    """
    result = text
    for variant, standard in VARIANT_MAP.items():
        result = result.replace(variant, standard)
    return result


class SimilarityMatcher(ABC):
    """相似度匹配器抽象基類。

    所有相似度引擎都必須實現此接口，以便日後無痛替換。
    """

    @abstractmethod
    def similarity(self, text1: str, text2: str) -> float:
        """計算兩個字串的相似度。

        Args:
            text1: 第一個字串
            text2: 第二個字串

        Returns:
            相似度分數 (0.0 - 1.0)
            1.0 = 完全相同
            0.0 = 完全不同
        """
        pass

    @abstractmethod
    def find_best_match(self,
                       source_substrings: List[str],
                       target_substrings: List[str],
                       threshold: float = 0.7) -> List[Tuple[str, str, float]]:
        """從子字串列表中找出最佳匹配對。

        Args:
            source_substrings: 源字串的所有子字串
            target_substrings: 目標字串的所有子字串
            threshold: 最低相似度閾值

        Returns:
            List of (source, target, similarity) tuples, sorted by similarity desc

        Example:
            >>> source = ["將他的獨生", "他的獨生", "獨生", "將", "他", ...]
            >>> target = ["賜下獨生子", "獨生子", "獨生", "賜", "下", ...]
            >>> matches = matcher.find_best_match(source, target, threshold=0.7)
            >>> matches[0]
            ('獨生', '獨生', 1.0)
        """
        pass


class SimpleSimilarityMatcher(SimilarityMatcher):
    """簡單相似度匹配器（Version 1）。

    基於：
    1. 字符變體規範化（爲→為）
    2. 編輯距離（SequenceMatcher）
    3. 完全匹配加權

    優點：
    - ✅ 無外部依賴
    - ✅ 快速
    - ✅ 可解釋性強

    缺點：
    - ⚠️ 無法處理同義詞（上帝/神）
    - ⚠️ 對詞序變化敏感

    日後可替換為 EmbeddingSimilarityMatcher 或 TransformerSimilarityMatcher
    """

    def __init__(self,
                 exact_match_bonus: float = 0.0,
                 variant_match_bonus: float = 0.05,
                 length_penalty_factor: float = 0.1):
        """初始化匹配器。

        Args:
            exact_match_bonus: 完全匹配時的額外加分 (default: 0.0)
            variant_match_bonus: 變體匹配時的額外加分 (default: 0.05)
            length_penalty_factor: 長度差異懲罰係數 (default: 0.1)
        """
        self.exact_match_bonus = exact_match_bonus
        self.variant_match_bonus = variant_match_bonus
        self.length_penalty_factor = length_penalty_factor

    def similarity(self, text1: str, text2: str) -> float:
        """計算相似度。

        策略：
        1. 完全匹配 → 1.0
        2. 變體匹配 → 0.95+
        3. 編輯距離 → 0.0-1.0
        4. 長度差異懲罰
        """
        # 1. 完全匹配
        if text1 == text2:
            return 1.0 + self.exact_match_bonus

        # 2. 字符變體規範化後匹配
        norm1 = normalize_variants(text1)
        norm2 = normalize_variants(text2)

        if norm1 == norm2:
            return 0.95 + self.variant_match_bonus

        # 3. 編輯距離相似度
        base_similarity = SequenceMatcher(None, norm1, norm2).ratio()

        # 4. 長度差異懲罰
        len_diff = abs(len(text1) - len(text2))
        max_len = max(len(text1), len(text2))
        length_penalty = (len_diff / max_len) * self.length_penalty_factor if max_len > 0 else 0

        final_similarity = max(0.0, base_similarity - length_penalty)

        return final_similarity

    def find_best_match(self,
                       source_substrings: List[str],
                       target_substrings: List[str],
                       threshold: float = 0.7) -> List[Tuple[str, str, float]]:
        """找出所有高於閾值的匹配對，按相似度排序。

        策略：
        1. 計算所有源-目標子字串對的相似度
        2. 過濾低於閾值的
        3. 按相似度降序排序
        4. 去重（同一個源或目標只保留最佳匹配）
        """
        matches = []

        # 計算所有配對的相似度
        for source in source_substrings:
            for target in target_substrings:
                sim = self.similarity(source, target)
                if sim >= threshold:
                    matches.append((source, target, sim))

        # 按相似度降序排序
        matches.sort(key=lambda x: x[2], reverse=True)

        # 去重：每個源字串只保留最佳匹配
        seen_sources = set()
        seen_targets = set()
        unique_matches = []

        for source, target, sim in matches:
            if source not in seen_sources and target not in seen_targets:
                unique_matches.append((source, target, sim))
                seen_sources.add(source)
                seen_targets.add(target)

        return unique_matches


def extract_substrings(text: str, min_length: int = 1, max_length: int = None) -> List[str]:
    """提取文本的所有子字串。

    Args:
        text: 源文本
        min_length: 最小子字串長度
        max_length: 最大子字串長度（None = 整個文本長度）

    Returns:
        所有子字串的列表（不包含重複）

    Example:
        >>> extract_substrings("獨生子", min_length=2)
        ['獨生', '生子', '獨生子']
    """
    if max_length is None:
        max_length = len(text)

    substrings = set()

    for length in range(min_length, min(max_length + 1, len(text) + 1)):
        for start in range(len(text) - length + 1):
            substring = text[start:start + length]
            substrings.add(substring)

    return list(substrings)


# TODO: 未來實現
# class EmbeddingSimilarityMatcher(SimilarityMatcher):
#     """基於詞向量的相似度匹配器（Version 2 - 未來實現）"""
#     pass

# class TransformerSimilarityMatcher(SimilarityMatcher):
#     """基於 Sentence-BERT 的相似度匹配器（Version 3 - 未來實現）"""
#     pass
