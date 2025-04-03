import re
import nltk
import os
import numpy as np
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set NLTK data path
nltk_data_path = os.path.join(os.getcwd(), 'nltk_data')
if not os.path.exists(nltk_data_path):
    try:
        os.makedirs(nltk_data_path)
    except:
        # Use default if we can't create the directory
        nltk_data_path = None

# Configure NLTK data path
if nltk_data_path:
    nltk.data.path.append(nltk_data_path)
    logger.info(f"NLTK data path set to: {nltk_data_path}")

# Define global variable for transformers availability
TRANSFORMERS_AVAILABLE = False

# Try importing the transformers package
try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    import torch
    TRANSFORMERS_AVAILABLE = True
    logger.info("Transformers and PyTorch successfully imported")
except ImportError as e:
    logger.warning(f"Error importing transformers or torch: {e}")
    logger.warning("Falling back to basic sentiment analysis")

class SentimentAnalyzer:
    def __init__(self):
        # Download necessary NLTK resources
        try:
            nltk.data.find('tokenizers/punkt')
            logger.info("NLTK punkt tokenizer already downloaded")
        except LookupError:
            logger.info("Downloading NLTK punkt tokenizer...")
            try:
                nltk.download('punkt', download_dir=nltk_data_path)
                logger.info("NLTK punkt tokenizer downloaded successfully")
            except Exception as e:
                logger.error(f"Error downloading NLTK data: {e}")
                logger.info("Trying to download to default location")
                nltk.download('punkt')
        
        # Set cache directory explicitly to avoid permission issues
        os.environ['TRANSFORMERS_CACHE'] = os.path.join(os.getcwd(), 'models_cache')
        
        if TRANSFORMERS_AVAILABLE:
            # Load pre-trained model and tokenizer
            self.model_name = "distilbert-base-uncased-finetuned-sst-2-english"
            logger.info(f"Loading BERT model: {self.model_name}")
            logger.info("This may take a few minutes on first run...")
            
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
                logger.info("BERT model loaded successfully!")
                self.labels = ['negative', 'positive']
            except Exception as e:
                logger.error(f"Error loading BERT model: {e}")
                logger.info("Falling back to basic sentiment analysis...")
                self.tokenizer = None
                self.model = None
        else:
            logger.info("Transformers package not available, using basic sentiment analysis")
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
            logger.error(f"Error in sentiment analysis: {e}")
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