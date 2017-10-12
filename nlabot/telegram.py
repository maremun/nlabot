#   encoding: utf8
#   telegram.py
"""Defines binding for Telegram Bot API. Only the most useful
methods are defined. Others are skipped.

See for details https://core.telegram.org/bots/api.
"""

import logging

from requests import Session, get
from .settings import API_URL, API_TOKEN, API_DOWNLOAD_URL


def send_request(method=None, params=None, sess=None):
    if not sess:
        sess = Session()

    url = API_URL.format(token=API_TOKEN, method=method)
    r = sess.get(url, params=params)

    if r.status_code != 200:
        logging.error('request failed with status code %d', r.status_code)
        logging.error(r.json())
        return None

    content_type = r.headers.get('Content-Type', '')

    if not content_type.startswith('application/json'):
        logging.error('wrong content-type: %s', content_type)
        return None

    try:
        json = r.json()
    except ValueError:
        logging.error('invalid json: %s', r.text)
        return None

    return json


def get_me(sess=None):
    """A simple method for testing your bot's auth token. Requires no
    parameters. Returns basic information about the bot in form of a User
    object.

    See for details https://core.telegram.org/bots/api#getme.
    """
    return send_request('getMe', sess)


def get_updates(offset=None, limit=100, timeout=60, sess=None):
    params = dict(offset=offset, limit=limit, timeout=60)
    return send_request('getUpdates', params, sess)


def send_message(chat_id, text, reply_markup=None, parse_mode='Markdown',
                 sess=None):
    params = dict(chat_id=chat_id, text=text, parse_mode=parse_mode)
    if reply_markup:
        params['reply_markup'] = reply_markup
    return send_request('sendMessage', params, sess)


def answer_callback_query(callback_query_id, text=None):
    params = dict(callback_query_id=callback_query_id, text=text)
    return send_request('answerCallbackQuery', params)


def edit_message_text(chat_id, message_id, text, reply_markup=None):
    params = dict(chat_id=chat_id, message_id=message_id, text=text)
    if reply_markup:
        params['reply_markup'] = reply_markup
    return send_request('editMessageText', params)


def set_webhook(url, certificate=None, max_connections=None,
                allowed_updates=None):

    """Use this method to specify a url and receive incoming updates via an
    outgoing webhook.

    See https://core.telegram.org/bots/api#setwebhook
    """
    params = dict(url=url,
                  certificate=certificate,
                  max_connections=max_connections,
                  allowed_updates=allowed_updates)
    return send_request('setWebhook', params)


def get_file(file_id, sess=None):
    r = send_request('getFile', {'file_id': file_id})
    print(r)
    file_path = r['result']['file_path']
    download_link = API_DOWNLOAD_URL.format(token=API_TOKEN,
                                            file_path=file_path)
# TODO if file is loo big?
    download = get(download_link)
    return download.content
