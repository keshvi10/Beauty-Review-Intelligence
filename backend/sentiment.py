from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer = SentimentIntensityAnalyzer()


def analyze_reviews(reviews: list) -> dict:
    """Classify each review as positive/neutral/negative and return percentages."""
    counts = {"positive": 0, "neutral": 0, "negative": 0}

    if not reviews:
        return {"positive": 0, "neutral": 0, "negative": 0}

    for text in reviews:
        score = _analyzer.polarity_scores(text)["compound"]
        if score >= 0.05:
            counts["positive"] += 1
        elif score <= -0.05:
            counts["negative"] += 1
        else:
            counts["neutral"] += 1

    total = sum(counts.values())
    return {key: round(value / total * 100) for key, value in counts.items()}
