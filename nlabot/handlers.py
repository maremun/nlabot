#   encoding: utf-8
#   handlers.py

from sqlalchemy.exc import IntegrityError
from requests import Session

from datetime import datetime
from .telegram import send_message
from .utils import check_started, check_registered, download_file


ERROR_TEXT = "Sorry, I don't understand. If you are unregistered, please " \
       "register by sending me a message with your *FirstName " \
       "LastName*. Otherwise, make a submission (your homework)."
NOT_STARTED_TEXT = "Send /start command to interact with me."
NOT_ENROLLED_TEXT = "Uh-oh! You seem to be not in the list of enrolled " \
                       "students, please contact TA to correct this."
ADDED_STUDENT_TEXT = "Congrats! You have joined the NLA army! SVD bless you!"
taken_error = "Uh-oh! Somebody took you name! Please report this to your TA!"
STARTED_TEXT = "You've already started interaction with me."
REGISTERED_TEXT = "You've already registered. To reset use /start command."
NOT_REGISTERED_TEXT = "You haven't registered yet. Do it by sending me a " \
                      "message with your *Firstname Lastname*."
NAME_FORMAT_TEXT = '*Firstname Lastname*.'


def handle_update(update, sess, conn, queue):
    print(update)
    if update.get('message'):
        msg = update['message']
        user_id = msg['from']['id']
    else:
        # ignoring other update type for now
        return update['update_id']

    started = check_started(user_id, conn)
    if msg.get('text'):
        if msg['text'].startswith('/start'):
            # STARTING (ADD USER TO users TABLE)
            if started:
                cursor = conn.execute("""
                    DELETE FROM users
                    WHERE user_id = :user_id
                """, {'user_id': user_id})

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

            text = 'Hello! Please register to submit your homeworks. ' \
                   'Send your *FirstName LastName*.'
        else:
            # REGISTERATION (CHANGE state TO registered)
            if not started:
                text = NOT_STARTED_TEXT
                send_message(msg['chat']['id'], text, sess=sess)
                return update['update_id']

            if check_registered(user_id, conn)[0]:
                text = REGISTERED_TEXT
                send_message(msg['chat']['id'], text, sess=sess)
                return update['update_id']

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
                    SET state = 'registered', student_id = students.student_id
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

            except IntegrityError:
                text = taken_error
                conn.rollback()

            except Exception as e:
                print(type(e))
                print(e)

                text = ERROR_TEXT
                conn.rollback()

    elif msg.get('document'):
        if not started:
            text = NOT_STARTED_TEXT
            send_message(msg['chat']['id'], text, sess=sess)
            return update['update_id']

        registered, student = check_registered(user_id, conn)
        if not registered:
            text = NOT_REGISTERED_TEXT
        else:
            text, submission_id, filepath = download_file(msg, student, conn)
            queue.enqueue_call(grade, args=(submission_id, filepath))

    else:
        text = ERROR_TEXT

    print(text)
    send_message(msg['chat']['id'], text, sess=sess)

    return update['update_id']


def respond(user_id):
    print(f'respond to {user_id}')
    text = 'fasdf'
    sess = Session()
    send_message(user_id, text, sess=sess)


def grade(submission_id, path):
    pass
