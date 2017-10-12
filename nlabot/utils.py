#   encoding: utf-8
#   utils.py

import os
from datetime import datetime

from .telegram import get_file

WRONG_TITLE_TEXT = "Uh-oh! Something wrong with your submission title. " \
                  "Please rename it as hw-_N_, where _N_ is the number of " \
                  "the homework you are trying to submit."
WRONG_TYPE_TEXT = 'Uh-oh! Your submission is not Jupyter notebook!'
MIMES = ['text/plain', 'application/x-ipynb+json']


def check_started(user_id, conn):
    row = {'user_id': user_id}
    cursor = conn.execute("""
        SELECT EXISTS(SELECT * FROM users
        WHERE user_id = :user_id)
    """, row)
    return cursor.first()[0]


def check_registered(user_id, conn):
    row = {'user_id': user_id}
    cursor = conn.execute("""
        SELECT students.student_id, students.last_name,
               students.first_name
        FROM students INNER JOIN users
        ON (students.student_id = users.student_id)
        WHERE user_id = :user_id
    """, row)
    result = cursor.first()
    if result is None:
        return False, None
    else:
        return True, result


def download_file(msg, student, conn):
    submission = msg['document']
    file_id = submission['file_id']
    file_name = submission.get('file_name', '')
    mime_type = submission.get('mime_type', '')
    file_size = submission.get('file_size', 0)
    submission_id = None
    filepath = None
    if file_size / 1048576 > 20:
        text = 'File is too big.'
        return text, submission_id, filepath

    if mime_type in MIMES and file_name.endswith('.ipynb'):
        if file_name.startswith('hw-'):
            hw_id = int(file_name[3:4])
            if hw_id < 1 and hw_id > 4:
                text = 'Homework number is not valid.'
                return text

            student_id, last_name, first_name = student
            directory = os.path.join(f'{last_name}-{first_name}-'
                                     f'{student_id:03}', f'hw{hw_id}')
            if not os.path.exists(directory):
                os.makedirs(directory)
            download = get_file(file_id)
            time = datetime.fromtimestamp(
                       msg['date']
                   )
            path = os.path.join(f'{directory}',
                                f'{last_name}-{first_name}-'
                                f'{file_name[:4]}')
            row = {'file_id': file_id, 'path': path,
                   'student_id': student_id, 'hw_id': hw_id,
                   'submitted_at': time}
            try:
                cursor = conn.execute("""
                    WITH ord AS (
                        SELECT COALESCE(MAX(ordinal), 0) + 1 AS next
                        FROM submissions
                        WHERE student_id = :student_id AND hw_id = :hw_id
                        LIMIT 1)
                    INSERT INTO submissions (
                        file_id, path, student_id, hw_id, ordinal, submitted_at
                    )
                    SELECT
                        :file_id, :path||'_'||next||'_'||to_char(:submitted_at,
                        'YYMONDD-HH:MI:SS')||'.ipynb',
                        :student_id, :hw_id, next, :submitted_at
                    FROM ord
                    RETURNING submission_id, ordinal, path
                """, row)

                submission_id, ordinal, filepath = cursor.first()

                with open(path, 'wb') as f:
                    f.write(download)

                text = f'Received hw#{hw_id} submission#{ordinal} from ' \
                       f'{first_name} {last_name}. Parts of the homework ' \
                       'are graded automatically. I will let you know the ' \
                       'grade soon.'

                conn.commit()

            except Exception as e:
                print(type(e))
                print(e)
                conn.rollback()

        else:
            text = WRONG_TITLE_TEXT
    else:
        text = WRONG_TYPE_TEXT

    return text, submission_id, filepath
