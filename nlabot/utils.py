#   encoding: utf-8
#   utils.py

import os
from datetime import datetime

from .telegram import get_file

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
    if file_size / 1048576 > 20:
        text = 'File is too big.'
        return text

    if mime_type == 'text/plain' and file_name.endswith('.ipynb'):
        if file_name.startswith('HW'):
            hw_id = int(file_name[3:4])
            if hw_id < 1 and hw_id > 4:
                text = 'Homework number is not valid.'
                return text

            student_id, last_name, first_name = student
            directory = last_name + first_name + '/' + f'HW{hw_id}/'
            if not os.path.exists(directory):
                os.makedirs(directory)
            download = get_file(file_id)
            time = datetime.fromtimestamp(
                       msg['date']
                   )
            ftime = time.strftime('%Y-%m-%d%H:%M:%S')
            row = {'student_id': student_id, 'hw_id': hw_id,
                   'submitted_at': time}
            try:
                cursor = conn.execute("""
                    WITH ord AS (
                        SELECT COALESCE(MAX(ordinal), 0)
                        FROM submissions
                        WHERE student_id = :student_id AND hw_id = :hw_id)
                    INSERT INTO submissions (
                        student_id, hw_id, ordinal, submitted_at
                    )
                    VALUES (
                        :student_id, :hw_id, (SELECT * FROM ord),
                        :submitted_at
                    )
                    RETURNING ordinal;
                """, row)
                conn.commit()
                ordinal = cursor.first()[0] + 1

            except Exception as e:
                print(type(e))
                print(e)
                conn.rollback()

            # TODO download and insert symultaneously
            with open(f'{directory}{file_name[:4]}_{ordinal}_{time}' \
                      f'{file_name[4:]}', 'wb') as f:
                f.write(download)

            text = f'Received HW#{hw_id} submission#{ordinal} from ' \
                   f'{first_name} {last_name}.'
        else:
            text = wrong_title_text
    else:
        text = wrong_type_text

    return text
