r"""datatrove 适配器：复用它的 MinHash 核心算法和过滤器。

为避免 spacy 语言模型依赖，直接用 datatrove 的底层工具函数：
- simplify_text (文本规范化)
- ngrams / create_hash_func (shingle 哈希)
"""
import tempfile


class MinHashDeduplicator:
    """MinHash 近似去重 —— 复用 datatrove 的底层算法。

    参数借鉴 FineWeb：n_grams=5, num_buckets=14, hashes_per_bucket=8
    """

    def __init__(self, n_grams=5, num_buckets=14, hashes_per_bucket=8, seed=42, language="zh"):
        from datatrove.utils.hashing import HashConfig, create_hash_func
        self.n_grams = n_grams
        self.hash_func = create_hash_func(HashConfig())
        self._index = {}  # shingle -> set of doc ids
        self._docs = {}   # doc id -> text

    def signature(self, text: str):
        """返回该文本的 shingle 哈希集合（复用 datatrove 的 simplify_text + ngrams）。"""
        from datatrove.utils.text import simplify_text, ngrams
        # 中文按字符分，空格分隔后 datatrove 的 word_tokenize 需要 spacy；
        # 这里用简化：先 simplify，再按字符切 n-gram
        simplified = simplify_text(text)
        words = list(simplified)  # 中文按字符
        sig = set()
        for i in range(len(words) - self.n_grams + 1):
            gram = "".join(words[i:i + self.n_grams])
            sig.add(int(self.hash_func(gram)))
        return sig

    def is_duplicate(self, text: str, threshold=0.8) -> bool:
        """基于 shingle 集合 Jaccard 相似度判断重复。"""
        shingles = self.signature(text)
        if not shingles:
            return False
        candidates = {}
        for sh in shingles:
            for doc_id in self._index.get(sh, ()):
                candidates[doc_id] = candidates.get(doc_id, 0) + 1
        for doc_id, overlap in candidates.items():
            other = self.signature(self._docs[doc_id])
            jaccard = overlap / len(shingles | other)
            if jaccard >= threshold:
                return True
        doc_id = len(self._docs)
        self._docs[doc_id] = text
        for sh in shingles:
            self._index.setdefault(sh, set()).add(doc_id)
        return False


class DatatroveFilters:
    """datatrove 的过滤器（需要 spacy 的那个用语言参数控制）。"""

    FILTERS = {
        "gopher_quality": "GopherQualityFilter",
        "gopher_repetition": "GopherRepetitionFilter",
        "c4_quality": "C4QualityFilter",
        "fineweb_quality": "FineWebQualityFilter",
    }

    @staticmethod
    def check(filter_name: str, text: str, **kwargs) -> bool:
        import datatrove.pipeline.filters as f
        cls = getattr(f, DatatroveFilters.FILTERS[filter_name], None)
        if cls is None:
            raise ValueError(f"未知过滤器: {filter_name}")
        step = cls(**kwargs)
        from datatrove.data import Document
        doc = Document(text=text, id="test")
        return step(doc, stats=None) is not None
