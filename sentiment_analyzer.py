import re
import nltk
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import numpy as np
import os

class SentimentAnalyzer:
    def __init__(self):
        # Download necessary NLTK resources
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            print("Downloading NLTK punkt tokenizer...")
            nltk.download('punkt')
        
        # Set cache directory explicitly to avoid permission issues
        os.environ['TRANSFORMERS_CACHE'] = os.path.join(os.getcwd(), 'models_cache')
        
        # Load pre-trained model and tokenizer
        self.model_name = "distilbert-base-uncased-finetuned-sst-2-english"
        print(f"Loading BERT model: {self.model_name}")
        print("This may take a few minutes on first run...")
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            print("BERT model loaded successfully!")
        except Exception as e:
            print(f"Error loading BERT model: {e}")
            print("Falling back to basic sentiment analysis...")
            self.tokenizer = None
            self.model = None
        
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
        """Analyze the sentiment of a text using the pre-trained model."""
        # Clean the text
        cleaned_text = self.clean_text(text)
        
        # If text is empty after cleaning, return neutral
        if not cleaned_text:
            return 'neutral'
        
        # If model failed to load, use a simple lexicon-based approach
        if self.model is None or self.tokenizer is None:
            return self._basic_sentiment_analysis(cleaned_text)
        
        try:
            # Tokenize the text and prepare for the model
            inputs = self.tokenizer(cleaned_text, return_tensors="pt", truncation=True, max_length=512)
            
            # Get prediction
            with torch.no_grad():
                outputs = self.model(**inputs)
                predictions = outputs.logits
                
            # Get sentiment scores
            scores = torch.nn.functional.softmax(predictions, dim=1).detach().numpy()[0]
            
            # Determine sentiment
            max_score_index = np.argmax(scores)
            sentiment = self.labels[max_score_index]
            
            # Add a neutral category for borderline cases
            confidence = scores[max_score_index]
            if confidence < 0.65:  # Threshold for neutral sentiment
                return 'neutral'
                
            return sentiment
            
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