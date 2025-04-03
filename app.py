import os
import json
import random
import gc
from datetime import datetime, timedelta
from flask import Flask, render_template
from flask_socketio import SocketIO
from dotenv import load_dotenv
import threading
import time
import logging
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add a startup message
logger.info("Initializing Sentiment Analysis Dashboard...")
logger.info("This may take a few minutes on first run while downloading models...")

# Initialize the Flask app early so we can serve errors if imports fail
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'sentiment-analysis-secret')

# Configure SocketIO with CORS
socketio = SocketIO(app, 
                   cors_allowed_origins=os.environ.get('CORS_ORIGINS', '*'),
                   async_mode=os.environ.get('SOCKETIO_ASYNC_MODE', 'eventlet'))

# Global flag for initialization error
initialization_error = None

# Load environment variables
load_dotenv()

# Set memory mode from environment variable (default to low memory mode)
low_memory_mode = os.environ.get('LOW_MEMORY_MODE', 'true').lower() == 'true'
logger.info(f"Running in {'low' if low_memory_mode else 'standard'} memory mode")

# Try importing components with error handling
try:
    from sentiment_analyzer import SentimentAnalyzer
    from data_collector import TwitterCollector, RedditCollector
except ImportError as e:
    error_msg = f"Error importing required modules: {str(e)}"
    logger.error(error_msg)
    initialization_error = error_msg
    
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
    'max_items': int(os.getenv('MAX_ITEMS', '50'))  # Reduced default
}

# Lock for thread-safe access to config
config_lock = threading.Lock()

# Flag to signal the analyzer thread to refresh its config
refresh_config = threading.Event()

# Initialize instances with error handling
try:
    if initialization_error is None:
        # Initialize analyzers and collectors
        logger.info("Loading sentiment analysis model...")
        # Use basic sentiment analyzer in low memory mode
        sentiment_analyzer = SentimentAnalyzer(use_transformers=not low_memory_mode)
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
except Exception as e:
    error_msg = f"Error during initialization: {str(e)}"
    logger.error(error_msg, exc_info=True)
    initialization_error = error_msg
    demo_mode = True

# Memory monitoring function
def log_memory_usage():
    """Log current memory usage"""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    mem_mb = mem_info.rss / 1024 / 1024  # Convert to MB
    logger.info(f"Memory usage: {mem_mb:.2f} MB")
    
    # Force garbage collection if memory usage is high
    if mem_mb > 400:  # Trigger cleanup before hitting 512MB limit
        logger.warning(f"High memory usage detected ({mem_mb:.2f} MB). Running garbage collection...")
        gc.collect()
        # Log memory after collection
        mem_after = process.memory_info().rss / 1024 / 1024
        logger.info(f"Memory after garbage collection: {mem_after:.2f} MB (freed {mem_mb - mem_after:.2f} MB)")

@app.route('/')
def index():
    if initialization_error:
        # Return error page if initialization failed
        return f"""
        <html>
        <head><title>Initialization Error</title></head>
        <body>
            <h1>Initialization Error</h1>
            <p>The application failed to initialize properly. Please check the logs.</p>
            <p>Error: {initialization_error}</p>
        </body>
        </html>
        """
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    logger.info('Client connected')
    # Send initial data to new clients
    socketio.emit('update_data', sentiment_data)
    if initialization_error:
        socketio.emit('initialization_error', {'error': initialization_error})

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
            new_max = int(data['max_items'])
            # Enforce limits in low memory mode
            if low_memory_mode and new_max > 100:
                new_max = 100
                logger.info(f"Limiting max items to 100 due to low memory mode")
                
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

def generate_sample_data(count=5):  # Reduced sample count
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
    sentiments = ['positive', 'negative', 'neutral']
    weights = [0.4, 0.4, 0.2]  # Distribution weights for sentiments
    sample_data = []
    
    for _ in range(count):
        text = random.choice(sample_texts)
        source = random.choice(sources)
        timestamp = (datetime.now() - timedelta(minutes=random.randint(1, 60))).isoformat()
        
        # If sentiment_analyzer is available, use it, otherwise choose randomly
        if 'sentiment_analyzer' in globals() and sentiment_analyzer is not None:
            try:
                sentiment = sentiment_analyzer.analyze(text)
            except Exception:
                sentiment = random.choices(sentiments, weights=weights)[0]
        else:
            sentiment = random.choices(sentiments, weights=weights)[0]
        
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
    
    # Store last collection time for memory monitoring
    last_mem_check = time.time()
    
    while True:
        try:
            # Log memory usage periodically
            if time.time() - last_mem_check > 60:  # Check every minute
                log_memory_usage()
                last_mem_check = time.time()
            
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
            
            if demo_mode or initialization_error is not None:
                # In demo mode, generate sample data
                logger.info("Generating sample data...")
                # Generate fewer samples in low memory mode
                sample_count = 5 if low_memory_mode else 10
                all_items = generate_sample_data(sample_count)
                
                for item in all_items:
                    if item['source'] == 'Twitter':
                        sentiment_data['sources']['twitter'] += 1
                    else:
                        sentiment_data['sources']['reddit'] += 1
                    
                    sentiment_data[item['sentiment']] += 1
            else:
                # In normal mode, collect real data
                # Limit items in low memory mode
                actual_max = min(max_items, 50) if low_memory_mode else max_items
                
                # Collect tweets
                tweets = twitter_collector.collect(search_terms, actual_max // 2)
                
                # Collect Reddit posts
                reddit_posts = reddit_collector.collect(search_terms, actual_max // 2)
                
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
            
            # Limit the number of stored items in low memory mode
            max_stored = 50 if low_memory_mode else 100
            
            # Keep only the most recent items
            sentiment_data['recent_items'] = (all_items + sentiment_data['recent_items'])[:max_stored]
            
            # Emit the updated data
            socketio.emit('update_data', sentiment_data)
            
            logger.info(f"Analyzed {len(all_items)} new items. Total: positive={sentiment_data['positive']}, negative={sentiment_data['negative']}, neutral={sentiment_data['neutral']}")
            
            # Run garbage collection after processing
            gc.collect()
            
            # Wait before the next collection
            sleep_time = 10 if demo_mode or initialization_error is not None else 60  # Faster updates in demo mode
            logger.info(f"Waiting {sleep_time} seconds for next update...")
            
            # Wait with timeout to allow for interruption from config changes
            refresh_config.wait(timeout=sleep_time)
            
        except Exception as e:
            logger.error(f"Error in analysis loop: {e}", exc_info=True)
            time.sleep(10)  # Wait a bit before retrying

if __name__ == '__main__':
    # Start the analyzer in a background thread only if no initialization error
    if initialization_error is None:
        analyzer_thread = threading.Thread(target=analyze_content, daemon=True)
        analyzer_thread.start()
    else:
        logger.warning("Skipping analyzer thread due to initialization error")
        # Set demo mode for static data generation
        demo_mode = True
        
        # Start a minimal thread just to provide sample data
        def minimal_data_thread():
            global sentiment_data
            while True:
                # Generate some sample data periodically
                all_items = generate_sample_data(3)  # Generate fewer items
                # Limit stored items
                max_stored = 50 if low_memory_mode else 100
                sentiment_data['recent_items'] = (all_items + sentiment_data['recent_items'])[:max_stored]
                socketio.emit('update_data', sentiment_data)
                # Run garbage collection
                gc.collect()
                time.sleep(15)  # Longer sleep time
                
        thread = threading.Thread(target=minimal_data_thread, daemon=True)
        thread.start()
    
    # Get port from environment variable for deployment compatibility
    port = int(os.environ.get('PORT', 5000))
    
    # Start the Flask app
    logger.info(f"Starting web server on port {port}")
    if initialization_error:
        logger.warning(f"Running in ERROR mode due to: {initialization_error}")
    elif demo_mode:
        logger.info("DEMO MODE ACTIVE: Open browser to see sample data")
    else:
        logger.info("LIVE MODE ACTIVE: Collecting and analyzing real-time data")
    
    socketio.run(app, debug=os.environ.get('DEBUG', 'True').lower() == 'true', 
                host='0.0.0.0', port=port) 