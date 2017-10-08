#   encoding: utf-8
#   handlers.py

import os
from datetime import datetime
from sqlalchemy.exc import ResourceClosedError, IntegrityError

from datetime import datetime
from .telegram import send_message, get_file
from .models import StateType
from .utils import check_started, check_registered


error_text = "Sorry, I don\'t understand. If you are unregistered, please " \
       "register by sending me a message with your *FirstName " \
       "LastName*. Otherwise, make a submission (your homework)."
start_text = "You\'re note registered yet. Please send me your *Firstname " \
        "Lastname*."
not_enrolled_text = "Uh-oh! You seem to be not in the list of enrolled " \
                       "students, please contact TA to correct this."
added_student_text = "Congrats! You have joined the NLA army! SVD bless you!"
taken_error = "Uh-oh! Somebody took you name! Please report this to your TA!"
started_text = "You\'ve already started interaction with me."
registered_text = "You\'ve already registered. To reset use /start command."
wrong_title_text = "Uh-oh! Something wrong with your submission title. " \
                  "Please rename it as HW#_N_, where _N_ is the number of " \
                  "the homework you are trying to submit."
wrong_type_text = 'Uh-oh! Your submission is not Jupyter notebook!'


def handle_update(update, sess, conn):
    print(update)
    if update.get('message'):
        msg = update['message']
        user_id = msg['from']['id']
    else:
        # ignoring other update type for now
        return update['update_id']

    if msg.get('text'):
        if msg['text'].startswith('/start'):
            started = check_started({'user_id': user_id}, conn)
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
            try:
                first_name, last_name = msg['text'].strip().split(maxsplit=1)
                row = {'user_id': user_id, 'first_name': first_name,
                       'last_name': last_name}
                if check_started(row, conn):
                    text = started_text
                if check_registered(row, conn)[0]:
                    text = registered_text
                else:
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

            except ValueError:
                text = error_text

            except IntegrityError:
                text = taken_error
                conn.rollback()

            except Exception as e:
                print(type(e))
                print(e)

                text = error_text
                conn.rollback()

    elif msg.get('document'):
        row = {'user_id': user_id}
        registered, student_id = check_registered(row, conn)
        if not registered:
            text = start_text
        else:
            submission = msg.get('document')
            file_id = submission.get('file_id')
            file_name = submission.get('file_name')
            mime_type = submission.get('mime_type')
            if mime_type == 'text/plain' and file_name.endswith('.ipynb'):
                if file_name.startswith('HW'):
                    hw_id = int(file_name[3:4])
                    row = {'student_id': student_id}
                    cursor = conn.execute("""
                        SELECT first_name, last_name FROM students
                        WHERE student_id = :student_id
                    """, row)
                    first_name, last_name = cursor.first()
                    directory = last_name + first_name + '/' + f'HW{hw_id}/'
                    if not os.path.exists(directory):
                        os.makedirs(directory)
                    download = get_file(file_id)
                    n = len(os.listdir(directory))
                    ordinal = n + 1
                    time = datetime.fromtimestamp(
                               msg['date']
                           )
                    ftime = time.strftime('%Y-%m-%d_%H:%M:%S')
                    with open(f'{directory}{file_name[:4]}_{ordinal}_{time}' \
                              f'{file_name[4:]}', 'wb') as f:
                        f.write(download)
                    row = {'student_id': student_id, 'hw_id': hw_id, 'ordinal':
                            ordinal, 'submitted_at': time}
                    cursor = conn.execute("""
                        INSERT INTO submissions (
                            student_id, hw_id, ordinal, submitted_at
                        )
                        VALUES (
                            :student_id, :hw_id, :ordinal, :submitted_at
                        )
                        ON CONFLICT (submission_id)
                        DO NOTHING
                        RETURNING submission_id
                    """, row)
                    conn.commit()
                    text = f'received submission from {first_name} {last_name}'
                else:
                    text = wrong_title_text
            else:
                text = wrong_type_text

    else:
        text = error_text

    print(text)
    send_message(msg['chat']['id'], text, sess=sess)
    return update['update_id']
