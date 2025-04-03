import os

bind = "0.0.0.0:" + os.environ.get("PORT", "5000")
workers = 1
threads = 4
worker_class = "gthread"
timeout = 120

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info" 