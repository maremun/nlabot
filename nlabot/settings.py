#   encoding: utf8
#   settings.py

from os import getenv


# Debug and profiling settings
DEBUG = True
PROFILE = False

# Telegram API credentials
API_TOKEN = None
API_URL = 'https://api.telegram.org/bot{token}/{method}'
API_DOWNLOAD_URL = 'https://api.telegram.org/file/bot{token}/{file_path}'

# Proxy server settings
HTTP_PROXY = getenv('http_proxy')
HTTPS_PROXY = getenv('https_proxy')

# Database settings
DB_URI = 'postgres://nlabot@127.0.0.1/nlabot'
REDIS_HOST = '127.0.0.1'

# Other settings
HOST_PATH = None

# override default settings(ignore F401 and F403 flake8 errors)
try:
    from nlabot_settings import *  # noqa
except ImportError:
    pass

PROXIES = dict(http=HTTP_PROXY, https=HTTPS_PROXY)
