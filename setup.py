from setuptools import setup, find_packages

setup(
    name="sentiment-analysis-dashboard",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "flask==2.0.1",
        "tweepy==4.10.0",
        "praw==7.6.0",
        "transformers==4.35.0",
        "torch>=2.2.0",
        "plotly==5.10.0",
        "pandas==1.4.2",
        "nltk==3.7",
        "Flask-SocketIO==5.1.1",
        "python-dotenv==0.20.0",
        "werkzeug==2.0.1",
        "gunicorn==20.1.0",
        "eventlet==0.33.3",
    ],
) 