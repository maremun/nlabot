#   encoding: utf8
#   settings.py

from os.path import dirname, join, realpath


# Debug and profiling settings
DEBUG = True
PROFILE = False

# Telegram API credentials
API_TOKEN = None
API_URL = 'https://api.telegram.org/bot{token}/{method}'
API_DOWNLOAD_URL = 'https://api.telegram.org/file/bot{token}/{file_path}'

# Database settings
DB_URI = 'postgres://nlabot@127.0.0.1/nlabot'

# override default settings(ignore F401 and F403 flake8 errors)
try:
    from nlabot_settings import API_TOKEN
except ImportError:
    pass
