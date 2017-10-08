#   encoding: utf-8
#   handlers.py

from sqlalchemy.exc import ResourceClosedError, IntegrityError

from datetime import datetime
from .telegram import send_message
from .models import StateType
from .utils import check_started, check_registered, download_file


error_text = "Sorry, I don't understand. If you are unregistered, please " \
       "register by sending me a message with your *FirstName " \
       "LastName*. Otherwise, make a submission (your homework)."
not_started_text = "Send /start command to interact with me."
not_enrolled_text = "Uh-oh! You seem to be not in the list of enrolled " \
                       "students, please contact TA to correct this."
added_student_text = "Congrats! You have joined the NLA army! SVD bless you!"
taken_error = "Uh-oh! Somebody took you name! Please report this to your TA!"
started_text = "You've already started interaction with me."
registered_text = "You've already registered. To reset use /start command."
not_registered_text = "You haven't registered yet. Do it by sending me a " \
                      "message with your *Firstname Lastname*."
wrong_title_text = "Uh-oh! Something wrong with your submission title. " \
                  "Please rename it as HW#_N_, where _N_ is the number of " \
                  "the homework you are trying to submit."
wrong_type_text = 'Uh-oh! Your submission is not Jupyter notebook!'
name_format_text = '*Firstname Lastname*.'

def handle_update(update, sess, conn):
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
                text = not_started_text
                send_message(msg['chat']['id'], text, sess=sess)
                return update['update_id']

            if check_registered(user_id, conn)[0]:
                text = registered_text
                send_message(msg['chat']['id'], text, sess=sess)
                return update['update_id']

            split = msg['text'].strip().split(maxsplit=1)
            if len(split) != 2:
                text = name_format_text
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
                    text = not_enrolled_text
                else:
                    text = added_student_text

            except IntegrityError:
                text = taken_error
                conn.rollback()

            except Exception as e:
                print(type(e))
                print(e)

                text = error_text
                conn.rollback()

    elif msg.get('document'):
        if not started:
            text = not_started_text
            send_message(msg['chat']['id'], text, sess=sess)
            return update['update_id']

        registered, student = check_registered(user_id, conn)
        if not registered:
            text = not_registered_text
        else:
            text = download_file(msg, student, conn)

    else:
        text = error_text

    print(text)
    send_message(msg['chat']['id'], text, sess=sess)
    return update['update_id']
