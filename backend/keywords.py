import re
from collections import Counter

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "is", "it", "this", "that", "to", "of",
    "for", "in", "on", "with", "was", "were", "be", "been", "i", "my", "me", "we",
    "you", "your", "they", "their", "are", "as", "at", "by", "from", "have", "has",
    "had", "not", "so", "if", "but", "very", "too", "just", "than", "then", "also",
    "after", "before", "while", "all", "its", "im", "ive", "did", "does", "do",
    "product", "products", "review", "reviews", "amazon", "nykaa", "myntra", "tira",
    "ajio", "really", "still", "only", "even", "much", "more", "most", "one", "use",
    "used", "using", "would", "could", "will", "can", "get", "got", "buy", "bought",
}

WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z'-]+")


def top_keywords(reviews: list, limit: int = 5) -> list:
    """Extract the most common meaningful unigrams/bigrams from review text."""
    if not reviews:
        return []

    counter = Counter()
    for text in reviews:
        words = [w.lower() for w in WORD_RE.findall(text) if w.lower() not in STOPWORDS and len(w) > 2]
        counter.update(words)
        for first, second in zip(words, words[1:]):
            counter[f"{first} {second}"] += 1

    return [word for word, _ in counter.most_common(limit)]
