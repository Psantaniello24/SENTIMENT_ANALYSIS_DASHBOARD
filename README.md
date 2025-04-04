# Real-Time Sentiment Analysis Dashboard

A real-time sentiment analysis dashboard that collects content from Reddit (and optionally Twitter), analyzes sentiment using BERT, and displays results in a web interface with live updates.

> **Note**: By default, the application only collects data from Reddit due to Twitter API payment constraints. Twitter functionality is included in the code but requires a paid Twitter Developer Account.

- ## Video example

![Demo GIF](./sentiment_demo.gif)

## Features

- **Data Collection**: Collects posts from Reddit (and optionally Twitter) in real-time.
- **Text Cleaning**: Removes URLs, mentions, and other noise from the collected text.
- **Sentiment Analysis**: Uses a pre-trained BERT model from Hugging Face to analyze sentiment.
- **Real-Time Dashboard**: Displays sentiment analysis results in a web application with charts and tables.
- **Live Updates**: Uses WebSockets to provide real-time updates to the dashboard.
- **Dynamic Search Terms**: Update search terms directly from the web interface without restarting.

## Demo Mode

The application includes a demonstration mode that generates sample data if API credentials are not provided. This allows you to test the functionality without setting up API access.

## Requirements

- Python 3.7+
- Reddit Developer Account (for API access)
- Twitter Developer Account (optional, requires paid subscription)

## Installation

1. Clone this repository:
```
git clone https://github.com/Psantaniello24/SENTIMENT_ANALYSIS_DASHBOARD.git
```

2. Create a virtual environment and activate it:
```
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS/Linux
python -m venv venv
source venv/bin/activate
```

3. Install the required packages:
```
pip install -r requirements.txt
```

4. Create a `.env` file in the project root directory with your API credentials:
```
# Reddit API Credentials (Required for live data)
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT="script:sentiment_analyzer:v1.0 (by /u/your_username)"

# Twitter API Credentials (Optional - requires paid subscription)
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_KEY_SECRET=your_twitter_api_key_secret
TWITTER_ACCESS_TOKEN=your_twitter_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret

# Search Configuration
SEARCH_TERMS=climate change,technology,politics
MAX_ITEMS=100
```

## Local Usage

1. Run the Flask application:
```
python app.py
```

2. Open your web browser and navigate to:
```
http://localhost:5000
```

## Customization

- Change search terms directly from the web interface
- Modify the `.env` file to change default search terms and maximum number of items to collect
- Adjust the update frequency by changing the `sleep_time` value in the `analyze_content` function in `app.py`
- Customize the UI by modifying the HTML, CSS, and JavaScript files

## License

MIT 
