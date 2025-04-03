import re
import nltk
import os
import numpy as np
from nltk.sentiment.vader import SentimentIntensityAnalyzer

class SentimentAnalyzer:
    def __init__(self):
        # Download necessary NLTK resources
        try:
            nltk.data.find('vader_lexicon')
        except LookupError:
            print("Downloading NLTK vader lexicon...")
            nltk.download('vader_lexicon')
        
        # Initialize VADER sentiment analyzer
        print("Initializing VADER sentiment analyzer...")
        self.analyzer = SentimentIntensityAnalyzer()
        print("Sentiment analyzer initialized successfully!")
        
        # Define sentiment labels
        self.labels = ['negative', 'positive']
    
    def clean_text(self, text):
        """Clean text by removing URLs, mentions, hashtags, and special characters."""
        # Convert to string if not already
        if not isinstance(text, str):
            text = str(text)
            
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        
        # Remove user mentions and hashtags
        text = re.sub(r'@\w+|\#\w+', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def analyze(self, text):
        """Analyze the sentiment of a text using VADER."""
        # Clean the text
        cleaned_text = self.clean_text(text)
        
        # If text is empty after cleaning, return neutral
        if not cleaned_text:
            return 'neutral'
        
        try:
            # Get sentiment scores
            scores = self.analyzer.polarity_scores(cleaned_text)
            
            # Determine sentiment based on compound score
            if scores['compound'] >= 0.05:
                return 'positive'
            elif scores['compound'] <= -0.05:
                return 'negative'
            else:
                return 'neutral'
            
        except Exception as e:
            print(f"Error in sentiment analysis: {e}")
            return self._basic_sentiment_analysis(cleaned_text)
    
    def _basic_sentiment_analysis(self, text):
        """A simple rule-based sentiment analysis as fallback"""
        
        # Lists of positive and negative words
        positive_words = ['good', 'great', 'awesome', 'excellent', 'like', 'love', 'happy', 'best', 'better', 'amazing']
        negative_words = ['bad', 'worst', 'terrible', 'awful', 'hate', 'dislike', 'sad', 'disappointing', 'sucks', 'poor']
        
        text = text.lower()
        
        # Count occurrences
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        # Determine sentiment
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral' 