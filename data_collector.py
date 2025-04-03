import os
import tweepy
import praw
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class TwitterCollector:
    def __init__(self):
        # Initialize Twitter API client
        api_key = os.getenv('TWITTER_API_KEY')
        api_key_secret = os.getenv('TWITTER_API_KEY_SECRET')
        access_token = os.getenv('TWITTER_ACCESS_TOKEN')
        access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
        
        # Check if credentials are set
        if not all([api_key, api_key_secret, access_token, access_token_secret]):
            print("Notice: Twitter API credentials not found in .env file")
            print("Twitter API access requires a paid Developer Account subscription")
            print("Twitter data collection will be disabled")
            self.client = None
            return
            
        try:
            # Set up authentication
            auth = tweepy.OAuth1UserHandler(
                api_key, api_key_secret, access_token, access_token_secret
            )
            self.client = tweepy.API(auth)
            
            # Test connection
            self.client.verify_credentials()
            print("Twitter API authentication successful")
        except Exception as e:
            print(f"Error connecting to Twitter API: {e}")
            print("This may be due to incorrect credentials or Twitter API payment constraints.")
            print("Twitter API access requires a paid Developer Account subscription.")
            print("Twitter data collection will be disabled")
            self.client = None
        
    def collect(self, search_terms, max_items=50):
        """Collect tweets containing the specified search terms."""
        if not self.client:
            # Silently return empty list when Twitter is disabled
            return []
            
        collected_tweets = []
        
        try:
            # Collect tweets for each search term
            items_per_term = max(1, max_items // len(search_terms))
            
            for term in search_terms:
                print(f"Collecting tweets for: {term}")
                # Search for tweets
                tweets = tweepy.Cursor(
                    self.client.search_tweets,
                    q=term + " -filter:retweets", # Exclude retweets
                    tweet_mode="extended",
                    lang="en",
                    result_type="recent"
                ).items(items_per_term)
                
                # Process tweets
                term_count = 0
                for tweet in tweets:
                    tweet_data = {
                        'text': tweet.full_text if hasattr(tweet, 'full_text') else tweet.text,
                        'created_at': tweet.created_at.isoformat(),
                        'url': f"https://twitter.com/user/status/{tweet.id}"
                    }
                    collected_tweets.append(tweet_data)
                    term_count += 1
                
                print(f"  Collected {term_count} tweets for '{term}'")
                    
            return collected_tweets
            
        except Exception as e:
            print(f"Error collecting tweets: {e}")
            return []


class RedditCollector:
    def __init__(self):
        # Initialize Reddit API client
        client_id = os.getenv('REDDIT_CLIENT_ID')
        client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        user_agent = os.getenv('REDDIT_USER_AGENT')
        
        # Check if credentials are set
        if not all([client_id, client_secret, user_agent]):
            print("Warning: Reddit API credentials not found in .env file")
            print("Reddit data collection will be disabled")
            self.client = None
            return
            
        try:
            # Set up authentication
            self.client = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent
            )
            print("Reddit API authentication successful")
        except Exception as e:
            print(f"Error connecting to Reddit API: {e}")
            print("Reddit data collection will be disabled")
            self.client = None
        
    def collect(self, search_terms, max_items=50):
        """Collect Reddit posts containing the specified search terms."""
        if not self.client:
            print("Reddit client not initialized. Check API credentials in .env file.")
            return []
            
        collected_posts = []
        
        try:
            # Collect posts for each search term
            items_per_term = max(1, max_items // len(search_terms))
            
            for term in search_terms:
                print(f"Collecting Reddit posts for: {term}")
                term_count = 0
                
                # Search for posts
                for submission in self.client.subreddit("all").search(term, limit=items_per_term, sort="new"):
                    # Combine title and selftext for analysis
                    full_text = submission.title
                    if submission.selftext:
                        full_text += " " + submission.selftext
                        
                    post_data = {
                        'text': full_text,
                        'created_at': datetime.fromtimestamp(submission.created_utc).isoformat(),
                        'url': f"https://reddit.com{submission.permalink}"
                    }
                    collected_posts.append(post_data)
                    term_count += 1
                
                print(f"  Collected {term_count} Reddit posts for '{term}'")
                    
            return collected_posts
            
        except Exception as e:
            print(f"Error collecting Reddit posts: {e}")
            return [] 