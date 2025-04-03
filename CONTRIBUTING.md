# Contributing to the Real-Time Sentiment Analysis Dashboard

Thank you for considering contributing to this project! Here are some guidelines to help you get started.

## Setting Up Development Environment

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```
   git clone https://github.com/yourusername/real-time-sentiment-analysis.git
   cd real-time-sentiment-analysis
   ```

3. Create a virtual environment and install dependencies:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. Create a `.env` file based on `.env.example` with your Reddit API credentials.

## Development Workflow

1. Create a new branch for your feature or bug fix:
   ```
   git checkout -b feature-name
   ```

2. Make your changes and ensure they work properly:
   - Test locally by running `python app.py`
   - Check for any errors in the console

3. Commit your changes with a descriptive message:
   ```
   git commit -am "Add feature X"
   ```

4. Push your branch to your fork:
   ```
   git push origin feature-name
   ```

5. Create a Pull Request on GitHub

## Project Structure

- `app.py`: Main Flask application with routes and WebSocket handlers
- `data_collector.py`: Classes for collecting data from Reddit and Twitter
- `sentiment_analyzer.py`: BERT-based sentiment analysis functionality
- `templates/`: HTML templates for the web interface
- `static/`: CSS, JavaScript, and other static files
- `requirements.txt`: Python dependencies

## Code Style

- Follow PEP 8 style guidelines for Python code
- Use clear, descriptive variable and function names
- Add comments for complex logic
- Update documentation when adding new features

## Adding Features

When adding new features, please:

1. Start with an issue describing what you want to add
2. Update the README.md file with any new functionality
3. Add appropriate error handling
4. Keep UI consistent with the existing design

## Testing

Before submitting a Pull Request, please test:

1. Application starts without errors
2. New features work as expected
3. Application works in both demo mode and with API credentials

## Reporting Bugs

When reporting bugs, please include:

1. Steps to reproduce the bug
2. Expected behavior
3. Actual behavior
4. Screenshots if applicable
5. Environment information (OS, Python version, browser)

## License

By contributing to this project, you agree that your contributions will be licensed under the same MIT license as the project. 