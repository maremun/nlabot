#   encoding: utf-8
#   handlers.py

from datetime import datetime
from .telegram import send_message


error_text = 'Sorry, I don\'t understand. If you are unregistered, please ' \
       'register by sending me a message with your FirstName ' \
       'LastName. Otherwise, make a submission (your homework).'


def handle_update(update, sess, conn):
    print(update)
    msg = update['message']
    if msg.get('text'):
        if msg['text'].startswith('/start'):
            user_id = msg['from']['id']
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
                   'Send your *LastName FirstName*.'
        else:
            # TODO parse name and add student
            try:
                last_name, first_name = msg['text'].strip().split(maxsplit=1)

            #    cursor = conn.execute("""
            #
            #    """, )
                text = 'add student'
                # TODO if student is already in the database, then his state
                # will be 'registered', so text = 'You're already registered.'

                # TODO Another case is when student enters name that is not in
                # the list of students, then text = 'Uh-oh! You seem to be not
                # in the list of enrolled students, please contact TA to
                # correct this.'

                # TODO When the state is 'not registered' and the name entered
                # is in the list, then text = 'Congrats! You have joined the
                # NLA army! SVD bless!'

            except:
                text = error_text

    elif msg.get('document'):
        user_id = msg['from']['id']
        submission = msg.get('document')
        # TODO parse submission title to get HW number.
        file_name = submission.get('file_name')
        mime_type = submission.get('mime_type')
        if mime_type == 'text/plain' and file_name.endswith('.ipynb'):
            if file_name.startswith('HW'):
                hw_number = int(file_name[3:4])
                # TODO find student with this user_id, get her/his first_name,
                # last_name
                text = 'received submission from {first_name last_name}'
            else:
                text = 'Uh-oh! Something wrong with your submission title. ' \
                        'Please rename it as HW#_N_, where _N_ is the ' \
                        'number of the homework you are trying to submit.'
        else:
            text = 'Uh-oh! Your submission is not jupyter notebook!'

    else:
        text = error_text

    send_message(msg['chat']['id'], text, sess=sess)

    return update['update_id']
