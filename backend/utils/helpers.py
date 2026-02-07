import re


def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def keywords_from_text(text: str, limit: int = 40) -> list:
    text = normalize_text(text)
    words = re.findall(r"[a-z]{2,}", text)
    freq = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    sorted_words = sorted(freq.items(), key=lambda x: -x[1])
    return [w for w, _ in sorted_words[:limit]]
