import os
import json
import random
from datetime import datetime, timedelta
from flask import Flask, render_template
from flask_socketio import SocketIO
from dotenv import load_dotenv
import threading
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add a startup message
logger.info("Initializing Sentiment Analysis Dashboard...")
logger.info("This may take a few minutes on first run while downloading models...")

# Try importing components with error handling
try:
    from sentiment_analyzer import SentimentAnalyzer
    from data_collector import TwitterCollector, RedditCollector
except ImportError as e:
    logger.error(f"Error importing required modules: {e}")
    raise

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'sentiment-analysis-secret')

# Configure SocketIO with CORS
socketio = SocketIO(app, 
                   cors_allowed_origins=os.environ.get('CORS_ORIGINS', '*'),
                   async_mode=os.environ.get('SOCKETIO_ASYNC_MODE', 'eventlet'))

# Initialize analyzers and collectors
logger.info("Loading sentiment analysis model...")
sentiment_analyzer = SentimentAnalyzer()
logger.info("Initializing Twitter collector...")
twitter_collector = TwitterCollector()
logger.info("Initializing Reddit collector...")
reddit_collector = RedditCollector()
logger.info("Initialization complete!")

# Check if we are in demo mode (no API keys)
demo_mode = twitter_collector.client is None and reddit_collector.client is None
if demo_mode:
    logger.info("RUNNING IN DEMO MODE: No valid API keys found. Will generate sample data.")
    logger.info("To use real data, please add valid API keys to the .env file.")

# Global data storage
sentiment_data = {
    'positive': 0,
    'negative': 0,
    'neutral': 0,
    'sources': {
        'twitter': 0,
        'reddit': 0
    },
    'recent_items': []
}

# Configuration storage
config = {
    'search_terms': os.getenv('SEARCH_TERMS', 'python,data science,AI').split(','),
    'max_items': int(os.getenv('MAX_ITEMS', '100'))
}

# Lock for thread-safe access to config
config_lock = threading.Lock()

# Flag to signal the analyzer thread to refresh its config
refresh_config = threading.Event()

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    logger.info('Client connected')
    # Send initial data to new clients
    socketio.emit('update_data', sentiment_data)

@socketio.on('disconnect')
def handle_disconnect():
    logger.info('Client disconnected')

@socketio.on('get_config')
def handle_get_config():
    """Handle request for current configuration"""
    with config_lock:
        socketio.emit('config_data', {
            'search_terms': config['search_terms'],
            'max_items': config['max_items']
        })

@socketio.on('update_config')
def handle_update_config(data):
    """Handle updates to the configuration"""
    global config
    
    logger.info(f"Received config update: {data}")
    update_made = False
    
    with config_lock:
        # Update search terms if provided
        if 'search_terms' in data:
            # Parse the comma-separated string into a list
            new_terms = [term.strip() for term in data['search_terms'].split(',')]
            if new_terms != config['search_terms']:
                config['search_terms'] = new_terms
                update_made = True
                logger.info(f"Updated search terms to: {config['search_terms']}")
        
        # Update max items if provided
        if 'max_items' in data:
            new_max = data['max_items']
            if new_max != config['max_items']:
                config['max_items'] = new_max
                update_made = True
                logger.info(f"Updated max items to: {config['max_items']}")
    
    # If updates were made, signal analyzer thread to refresh
    if update_made:
        # Clear sentiment data for fresh start with new terms
        reset_sentiment_data()
        # Signal the analyzer thread
        refresh_config.set()
        # Send the updated config back to all clients
        socketio.emit('config_data', {
            'search_terms': config['search_terms'],
            'max_items': config['max_items']
        })

def reset_sentiment_data():
    """Reset the sentiment data counters and items"""
    global sentiment_data
    sentiment_data = {
        'positive': 0,
        'negative': 0,
        'neutral': 0,
        'sources': {
            'twitter': 0,
            'reddit': 0
        },
        'recent_items': []
    }
    socketio.emit('update_data', sentiment_data)

def generate_sample_data(count=10):
    """Generate sample data for demo mode"""
    sample_texts = [
        "I love this new product! It's amazing and works perfectly.",
        "The service was terrible and the staff was rude.",
        "Just bought the latest smartphone and it's okay, nothing special.",
        "Can't believe how bad the weather is today.",
        "The movie was fantastic, highly recommend watching it.",
        "This restaurant has the best food in town!",
        "So disappointed with my recent purchase, it broke after one use.",
        "Not sure how I feel about the new update, some good features but also some problems.",
        "The concert last night was incredible!",
        "Just had a mediocre experience at the new cafe downtown."
    ]
    
    sources = ['Twitter', 'Reddit']
    sample_data = []
    
    for _ in range(count):
        text = random.choice(sample_texts)
        source = random.choice(sources)
        timestamp = (datetime.now() - timedelta(minutes=random.randint(1, 60))).isoformat()
        sentiment = sentiment_analyzer.analyze(text)
        
        sample_data.append({
            'text': text,
            'source': source,
            'timestamp': timestamp,
            'sentiment': sentiment,
            'url': 'https://example.com/sample'
        })
        
    return sample_data

def analyze_content():
    global sentiment_data, config
    
    while True:
        try:
            # Check if config needs to be refreshed
            if refresh_config.is_set():
                logger.info("Refreshing configuration...")
                refresh_config.clear()
            
            # Get current config safely
            with config_lock:
                search_terms = config['search_terms'].copy()
                max_items = config['max_items']
            
            logger.info(f"Analyzing with terms: {search_terms}, max items: {max_items}")
            
            all_items = []
            
            if demo_mode:
                # In demo mode, generate sample data
                logger.info("Generating sample data...")
                all_items = generate_sample_data(10)  # Generate 10 sample items
                
                for item in all_items:
                    if item['source'] == 'Twitter':
                        sentiment_data['sources']['twitter'] += 1
                    else:
                        sentiment_data['sources']['reddit'] += 1
                    
                    sentiment_data[item['sentiment']] += 1
            else:
                # In normal mode, collect real data
                # Collect tweets
                tweets = twitter_collector.collect(search_terms, max_items // 2)
                
                # Collect Reddit posts
                reddit_posts = reddit_collector.collect(search_terms, max_items // 2)
                
                # Analyze tweets
                for tweet in tweets:
                    sentiment = sentiment_analyzer.analyze(tweet['text'])
                    all_items.append({
                        'text': tweet['text'],
                        'source': 'Twitter',
                        'timestamp': tweet['created_at'],
                        'sentiment': sentiment,
                        'url': tweet['url'] if 'url' in tweet else None
                    })
                    sentiment_data['sources']['twitter'] += 1
                    sentiment_data[sentiment] += 1
                
                # Analyze Reddit posts
                for post in reddit_posts:
                    sentiment = sentiment_analyzer.analyze(post['text'])
                    all_items.append({
                        'text': post['text'],
                        'source': 'Reddit',
                        'timestamp': post['created_at'],
                        'sentiment': sentiment,
                        'url': post['url']
                    })
                    sentiment_data['sources']['reddit'] += 1
                    sentiment_data[sentiment] += 1
            
            # Keep only the most recent items
            sentiment_data['recent_items'] = (all_items + sentiment_data['recent_items'])[:100]
            
            # Emit the updated data
            socketio.emit('update_data', sentiment_data)
            
            logger.info(f"Analyzed {len(all_items)} new items. Total: positive={sentiment_data['positive']}, negative={sentiment_data['negative']}, neutral={sentiment_data['neutral']}")
            
            # Wait before the next collection
            sleep_time = 10 if demo_mode else 60  # Faster updates in demo mode
            logger.info(f"Waiting {sleep_time} seconds for next update...")
            
            # Wait with timeout to allow for interruption from config changes
            refresh_config.wait(timeout=sleep_time)
            
        except Exception as e:
            logger.error(f"Error in analysis loop: {e}", exc_info=True)
            time.sleep(10)  # Wait a bit before retrying

if __name__ == '__main__':
    # Start the analyzer in a background thread
    analyzer_thread = threading.Thread(target=analyze_content, daemon=True)
    analyzer_thread.start()
    
    # Get port from environment variable for deployment compatibility
    port = int(os.environ.get('PORT', 5000))
    
    # Start the Flask app
    logger.info(f"Starting web server on port {port}")
    if demo_mode:
        logger.info("DEMO MODE ACTIVE: Open browser to see sample data")
    else:
        logger.info("LIVE MODE ACTIVE: Collecting and analyzing real-time data")
    
    socketio.run(app, debug=os.environ.get('DEBUG', 'True').lower() == 'true', 
                host='0.0.0.0', port=port) 