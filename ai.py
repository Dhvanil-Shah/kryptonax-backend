# from transformers import pipeline

# # 1. SETUP THE MODEL
# # We load "ProsusAI/finbert". It is the Gold Standard for financial sentiment.
# # WARNING: The first time you run this, it will download ~450MB. It might take 2-5 minutes.
# print("Loading AI Model... please wait...")
# sentiment_pipeline = pipeline("text-classification", model="ProsusAI/finbert")
# print("AI Model Loaded successfully!")

# def get_sentiment(text):
#     """
#     Input: "Tesla stock crashes after recall."
#     Output: "negative"
#     """
#     # The model returns a list like [{'label': 'negative', 'score': 0.95}]
#     try:
#         # We define the text max length to avoid errors if headline is too long
#         result = sentiment_pipeline(text, truncation=True, max_length=512)
#         label = result[0]['label'] # 'positive', 'negative', or 'neutral'
#         return label
#     except Exception as e:
#         print(f"AI Error: {e}")
#         return "neutral"

# # Test it immediately if we run this file directly
# if __name__ == "__main__":
#     test_headline = "Apple announces record-breaking profits for Q4."
#     print(f"Test Headline: {test_headline}")
#     print(f"Sentiment: {get_sentiment(test_headline)}")

from textblob import TextBlob

def get_sentiment(text):
    """
    Lightweight Sentiment Analysis for Free Hosting
    Input: "Tesla stock crashes"
    Output: "negative"
    """
    if not text:
        return "neutral"
        
    analysis = TextBlob(text)
    # Polarity is a float between -1.0 (Negative) and 1.0 (Positive)
    score = analysis.sentiment.polarity
    
    if score > 0.1:
        return "positive"
    elif score < -0.1:
        return "negative"
    else:
        return "neutral"