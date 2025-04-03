import os
import time
import logging
import tweepy
import praw
from datetime import datetime
from urllib.parse import quote
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class TwitterCollector:
    def __init__(self):
        """Initialize the Twitter collector with API credentials"""
        # Get Twitter API credentials from environment variables
        bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
        
        self.client = None
        if bearer_token:
            try:
                self.client = tweepy.Client(bearer_token)
                logger.info("Twitter API client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Twitter client: {str(e)}", exc_info=True)
        else:
            logger.warning("No Twitter bearer token found. Twitter collection disabled.")
    
    def collect(self, search_terms, max_count=10):
        """Collect tweets based on search terms
        
        Args:
            search_terms (list): List of terms to search for
            max_count (int): Maximum number of tweets to collect
            
        Returns:
            list: List of processed tweet data
        """
        if not self.client:
            logger.warning("Twitter client not available. Returning empty list.")
            return []
        
        results = []
        try:
            for term in search_terms:
                logger.info(f"Collecting tweets for term: {term}")
                
                # Use tweepy's search_recent_tweets endpoint
                # This requires Twitter API v2 Academic Research or Elevated access
                query = f"{term} -is:retweet lang:en"
                tweets = self.client.search_recent_tweets(
                    query=query,
                    max_results=min(max_count, 10),  # Twitter API limits to 10-100 per request
                    tweet_fields=['created_at', 'text', 'id']
                )
                
                if tweets and tweets.data:
                    for tweet in tweets.data:
                        tweet_data = {
                            'id': tweet.id,
                            'text': tweet.text,
                            'created_at': tweet.created_at.isoformat(),
                            'url': f"https://twitter.com/twitter/status/{tweet.id}"
                        }
                        results.append(tweet_data)
                
                # Don't overwhelm the API with requests
                if len(search_terms) > 1:
                    time.sleep(2)
                
                # Break early if we have enough results
                if len(results) >= max_count:
                    break
            
            logger.info(f"Collected {len(results)} tweets")
            return results

        except tweepy.TooManyRequests:
            logger.error("Twitter API rate limit exceeded. Try again later.")
            return results
        except tweepy.Unauthorized:
            logger.error("Twitter API authentication error. Check your credentials.")
            return results
        except Exception as e:
            logger.error(f"Error collecting tweets: {str(e)}", exc_info=True)
            return results


class RedditCollector:
    def __init__(self):
        """Initialize the Reddit collector with API credentials"""
        # Get Reddit API credentials from environment variables
        client_id = os.getenv('REDDIT_CLIENT_ID')
        client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        user_agent = os.getenv('REDDIT_USER_AGENT', 'sentiment_analysis_app by /u/yourusername')
        
        self.client = None
        if client_id and client_secret:
            try:
                self.client = praw.Reddit(
                    client_id=client_id,
                    client_secret=client_secret,
                    user_agent=user_agent
                )
                logger.info("Reddit API client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Reddit client: {str(e)}", exc_info=True)
        else:
            logger.warning("Missing Reddit API credentials. Reddit collection disabled.")
    
    def collect(self, search_terms, max_count=10):
        """Collect Reddit posts based on search terms
        
        Args:
            search_terms (list): List of terms to search for
            max_count (int): Maximum number of posts to collect
            
        Returns:
            list: List of processed Reddit post data
        """
        if not self.client:
            logger.warning("Reddit client not available. Returning empty list.")
            return []
        
        results = []
        try:
            for term in search_terms:
                logger.info(f"Collecting Reddit posts for term: {term}")
                
                # Search for term across all subreddits
                try:
                    submissions = self.client.subreddit('all').search(term, sort='new', time_filter='day', limit=max_count)
                    
                    for submission in submissions:
                        if len(results) >= max_count:
                            break
                            
                        # Process and store submission data
                        submission_data = {
                            'id': submission.id,
                            'text': submission.title,  # Using title as content
                            'created_at': datetime.fromtimestamp(submission.created_utc).isoformat(),
                            'url': f"https://www.reddit.com{submission.permalink}"
                        }
                        results.append(submission_data)
                    
                    # Don't overwhelm the API with requests
                    if len(search_terms) > 1:
                        time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error searching Reddit for term '{term}': {str(e)}")
                    continue
                
                # Break early if we have enough results
                if len(results) >= max_count:
                    break
            
            logger.info(f"Collected {len(results)} Reddit posts")
            return results
            
        except Exception as e:
            logger.error(f"Error collecting Reddit posts: {str(e)}", exc_info=True)
            return results 