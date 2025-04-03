import re
import nltk
import os
import numpy as np
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try importing the transformers package
try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    import torch
    TRANSFORMERS_AVAILABLE = True
    logger.info("Transformers and PyTorch successfully imported")
except ImportError as e:
    logger.warning(f"Error importing transformers or torch: {e}")
    logger.warning("Falling back to basic sentiment analysis")
    TRANSFORMERS_AVAILABLE = False

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
        
        if TRANSFORMERS_AVAILABLE:
            # Load pre-trained model and tokenizer
            self.model_name = "distilbert-base-uncased-finetuned-sst-2-english"
            print(f"Loading BERT model: {self.model_name}")
            print("This may take a few minutes on first run...")
            
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
                print("BERT model loaded successfully!")
                self.labels = ['negative', 'positive']
            except Exception as e:
                print(f"Error loading BERT model: {e}")
                print("Falling back to basic sentiment analysis...")
                self.tokenizer = None
                self.model = None
                TRANSFORMERS_AVAILABLE = False
        else:
            print("Transformers package not available, using basic sentiment analysis")
            self.tokenizer = None
            self.model = None
        
        # Define positive and negative word lists for basic analysis
        self.positive_words = [
            'good', 'great', 'awesome', 'excellent', 'like', 'love', 'happy', 'best', 
            'better', 'amazing', 'wonderful', 'fantastic', 'nice', 'perfect', 'enjoy',
            'beautiful', 'brilliant', 'outstanding', 'superb', 'helpful', 'positive'
        ]
        
        self.negative_words = [
            'bad', 'worst', 'terrible', 'awful', 'hate', 'dislike', 'sad', 'disappointing', 
            'sucks', 'poor', 'horrible', 'useless', 'wrong', 'waste', 'annoying', 'tough',
            'negative', 'slow', 'broken', 'difficult', 'angry', 'boring', 'fail'
        ]
    
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
        """Analyze the sentiment of a text using the pre-trained model or basic analysis."""
        # Clean the text
        cleaned_text = self.clean_text(text)
        
        # If text is empty after cleaning, return neutral
        if not cleaned_text:
            return 'neutral'
        
        # If transformers is not available or model failed to load, use basic analysis
        if not TRANSFORMERS_AVAILABLE or self.model is None or self.tokenizer is None:
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
        text = text.lower()
        
        # Count occurrences of positive and negative words
        positive_count = sum(1 for word in self.positive_words if word in text)
        negative_count = sum(1 for word in self.negative_words if word in text)
        
        # Additional heuristics to improve basic sentiment analysis
        # Check for negations that flip sentiment
        negations = ['not', "don't", "doesn't", 'no', 'never', "isn't", "aren't", "wasn't", "weren't"]
        for negation in negations:
            if negation in text:
                # Look for nearby positive words to flip
                for word in self.positive_words:
                    if f"{negation} {word}" in text or f"{negation} really {word}" in text:
                        positive_count -= 1
                        negative_count += 1
        
        # Determine sentiment based on counts
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral' 