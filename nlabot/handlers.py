#   encoding: utf-8
#   handlers.py

import logging

from datetime import datetime
from sqlalchemy.exc import IntegrityError

from .jail import grade
from .telegram import send_message
from .utils import check_started, check_registered, download_file

ADDED_STUDENT_TEXT = "Congrats! You have joined the NLA army! SVD bless you!"
DB_ERROR_TEXT = "Sorry, there has been an internal problem. Please report " \
                "this to TA."
ERROR_TEXT = "Sorry, I don't understand. If you are unregistered, please " \
             "register by sending me a message with your *FirstName " \
             "LastName*. Otherwise, make a submission (your homework)."
NAME_FORMAT_TEXT = '*Firstname Lastname*.'
NOT_ENROLLED_TEXT = "Uh-oh! You seem to be not in the list of enrolled " \
                    "students, please contact TA to correct this."
NOT_STARTED_TEXT = "Send /start command to interact with me."
NOT_REGISTERED_TEXT = "You haven't registered yet. Do it by sending me a " \
                      "message with your *Firstname Lastname* (as they " \
                      "appear in Canvas)."
ON_START_TEXT = "Hello! Please register to submit your homeworks. " \
                "Send your *FirstName LastName* (as they appear in Canvas)."
REGISTERED_TEXT = "You've already registered. To reset use /start command."
RESET_TEXT = "Resetted your registration."
STARTED_TEXT = "You've already started interaction with me."
TAKEN_ERROR = "Uh-oh! Somebody took your name! Please report this to your TA!"


def handle_update(update, sess, conn, queue):
    print(update)
    if update.get('message'):
        msg = update['message']
        user_id = msg['from']['id']
        chat_id = msg['chat']['id']
    else:
        # ignoring other update type for now
        return update['update_id']

    started = check_started(user_id, conn)
    if msg.get('text'):
        if msg['text'].startswith('/start'):
            prefix = ''
            # STARTING (ADD USER TO users TABLE)
            if started:
                prefix = RESET_TEXT
                cursor = conn.execute("""
                    DELETE FROM users
                    WHERE user_id = :user_id
                """, {'user_id': user_id})
                conn.commit()

            username = msg['from'].get('username')
            first_name = msg['from']['first_name']
            last_name = msg['from'].get('last_name')
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

            text = ' '.join((prefix, ON_START_TEXT))
        else:
            # REGISTRATION (CHANGE state TO registered)
            if not started:
                text = NOT_STARTED_TEXT
                send_message(msg['chat']['id'], text, sess=sess)
                return update['update_id']

            if not check_registered(user_id, conn)[0]:
                # try register
                split = msg['text'].strip().split(maxsplit=1)
                if len(split) != 2:
                    text = NAME_FORMAT_TEXT
                    send_message(msg['chat']['id'], text, sess=sess)
                    return update['update_id']

                first_name, last_name = split
                row = {'user_id': user_id, 'first_name': first_name,
                       'last_name': last_name}
                try:
                    cursor = conn.execute("""
                        UPDATE users
                        SET state = 'registered',
                            student_id = students.student_id
                        FROM students
                        WHERE user_id = :user_id AND students.first_name =
                        :first_name AND students.last_name = :last_name
                        RETURNING students.student_id;
                    """, row)
                    conn.commit()
                    result = cursor.first()
                    if result is None:
                        text = NOT_ENROLLED_TEXT
                    else:
                        text = ADDED_STUDENT_TEXT

                # oops, smbd took your place already
                except IntegrityError:
                    text = TAKEN_ERROR
                    conn.rollback()

                # smth wrong
                except Exception as e:
                    logging.error(e)
                    text = DB_ERROR_TEXT
                    conn.rollback()
            else:
                text = REGISTERED_TEXT
                send_message(msg['chat']['id'], text, sess=sess)
                return update['update_id']

    elif msg.get('document'):
        if not started:
            text = NOT_STARTED_TEXT
            send_message(msg['chat']['id'], text, sess=sess)
            return update['update_id']

        registered, student = check_registered(user_id, conn)
        if not registered:
            text = NOT_REGISTERED_TEXT
        else:
            d_params = download_file(msg, student, conn)
            text, submission_id, file_id, hw_id, filepath = d_params
            if filepath is not None:
                queue.enqueue_call(grade, timeout='21m', result_ttl='168h',
                                   ttl='168h', args=(submission_id,
                                                     file_id,
                                                     hw_id,
                                                     filepath,
                                                     chat_id))
    else:
        text = ERROR_TEXT

    send_message(chat_id, text, sess=sess)

    return update['update_id']
