# core/sentiment.py
from textblob import TextBlob

def analyze_sentiment(text: str) -> dict:
    """
    Analyzes text and returns a dictionary with polarity, subjectivity, and an emotional label.
    Polarity: -1.0 (very negative) to 1.0 (very positive)
    Subjectivity: 0.0 (objective) to 1.0 (subjective)
    """
    try:
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        
        # Determine label based on polarity
        if polarity <= -0.5:
            label = "Very Stressed or Upset"
        elif polarity < -0.1:
            label = "Negative or Stressed"
        elif polarity > 0.5:
            label = "Very Happy or Excited"
        elif polarity > 0.1:
            label = "Positive or Cheerful"
        else:
            label = "Neutral or Focused"
            
        return {
            "polarity": round(polarity, 2),
            "subjectivity": round(subjectivity, 2),
            "label": label
        }
    except Exception as e:
        print(f"⚠ Sentiment Analysis Failed: {e}")
        return {
            "polarity": 0.0,
            "subjectivity": 0.0,
            "label": "Neutral"
        }
