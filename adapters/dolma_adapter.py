r"""Dolma 适配器：复用 Gopher/C4 质量规则的阈值和逻辑。

Dolma 的 tagger 依赖它自己的包，这里把核心规则逻辑移植过来，
保持轻量且可中文特化。
"""
import re
from collections import Counter


def gopher_quality(text: str) -> dict:
    """Gopher 质量规则（中文特化：按字符 n-gram，不用空格分词）。"""
    chars = len(text)
    # 中文/日文按字符，英文按空格词
    zh = len(re.findall(r"[\u4e00-\u9fff]", text))
    is_zh = zh > chars * 0.3
    words = list(text) if is_zh else text.split()
    result = {
        "char_count": chars,
        "word_count": len(words),
        "median_word_len": _median([len(w) for w in words]) if words else 0,
        "symbol_ratio": sum(not c.isalnum() and not c.isspace() and c not in "，。！？；：、""''（）" for c in text) / max(chars, 1),
        "dup_line_frac": 0.0,
        "dup_ngram_frac": 0.0,
        "is_zh": is_zh,
    }
    # 重复行
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if lines:
        result["dup_line_frac"] = (len(lines) - len(set(lines))) / len(lines)
    # 重复 5-gram 字符占比（中文用较长 gram 避免误判）
    n = 12 if is_zh else 5
    grams = [text[i:i+n] for i in range(max(0, chars - n + 1))]
    if grams:
        c = Counter(grams)
        result["dup_ngram_frac"] = sum(v for v in c.values() if v > 1) / len(grams)
    return result


def c4_quality(text: str) -> dict:
    """C4 质量规则（中文特化：中文标点也算结尾）。"""
    lines = [l for l in text.split("\n") if l.strip()]
    zh_punct = ".?!。！？；…\"'"
    punct_end = sum(1 for l in lines if l.rstrip()[-1:] in zh_punct)
    zh = len(re.findall(r"[\u4e00-\u9fff]", text))
    is_zh = zh > len(text) * 0.3
    return {
        "line_count": len(lines),
        "frac_lines_no_ending_punct": 1 - (punct_end / len(lines)) if lines else 1.0,
        "frac_lines_too_few_words": sum(1 for l in lines if len(l.split()) < 3) / len(lines) if lines else 1.0,
        "has_lorem_ipsum": "lorem ipsum" in text.lower(),
        "has_javascript": "function(" in text or "var " in text,
        "is_zh": is_zh,
    }


def passes_gopher(text: str, min_chars=100, max_symbol_ratio=0.3, max_dup_line=0.3, max_dup_ngram=0.5) -> bool:
    r = gopher_quality(text)
    # 中文文本的重复行判断放宽（中文文章通常不分行）
    dup_line_ok = r["dup_line_frac"] <= max_dup_line or r["is_zh"]
    return (r["char_count"] >= min_chars and r["symbol_ratio"] <= max_symbol_ratio
            and dup_line_ok and r["dup_ngram_frac"] <= max_dup_ngram)


def passes_c4(text: str, max_no_punct=0.12, max_short_line=0.67) -> bool:
    r = c4_quality(text)
    # 中文按句读判断：整段末尾有中文标点就算通过（中文文章分段少）
    punct_ok = (r["frac_lines_no_ending_punct"] <= max_no_punct or
                (r["is_zh"] and text.rstrip()[-1:] in "。！？…\"'"))
    short_ok = r["frac_lines_too_few_words"] <= max_short_line or r["is_zh"]
    return punct_ok and short_ok and not r["has_lorem_ipsum"]


def _median(values):
    s = sorted(values)
    n = len(s)
    return s[n//2] if n % 2 else (s[n//2-1] + s[n//2]) / 2
