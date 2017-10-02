#   encoding: utf-8
#   handlers.py

from datetime import datetime
from .telegram import send_message


def handle_update(update, sess, conn):
    print(update)
    msg = update['message']
    if msg['text'].startswith('/start'):
        user_id = msg['chat']['id']
        username = msg['chat'].get('username')
        first_name = msg['chat'].get('first_name')
        last_name = msg['chat'].get('last_name')
        last_seen_at = datetime.fromtimestamp(msg['date'])

        row = {'user_id': user_id, 'username': username,
               'first_name': first_name, 'last_name': last_name,
               'last_seen_at': last_seen_at}

        cursor = conn.execute("""
            INSERT INTO users (
                user_id, username, first_name, last_name, last_seen_at
            )
            VALUES (
                :user_id, :username, :first_name, :last_name, :last_seen_at
            )
            ON CONFLICT (user_id)
            DO NOTHING
            RETURNING state
            """, row)

        conn.commit()
        
        text = 'Hello! Please register to submit your homeworks. ' \
               'Send your *LastName FirstName*.'

    elif msg.get('text'):
        # TODO parse name and add student
        text = 'add student'
        pass

    elif msg.get('document'):
        text = 'receive submission'
        pass

    else:
        text = 'Sorry, I don\'t understand. If you are unregistered, please ' \
               'register. Otherwise, make a submission (your homework).'
        pass

    send_message(msg['chat']['id'], text, sess=sess)

    return update['update_id']

