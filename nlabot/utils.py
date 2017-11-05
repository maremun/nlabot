#   encoding: utf-8
#   utils.py

import logging
import os
from datetime import datetime
from time import sleep

from .models import connect_database
from .telegram import get_file

SUCCESS_UPLOAD_TEXT = 'Received hw #{:d} submission #{:d} from {:s} ' \
                          '{:s}. Coding parts of the homework are graded ' \
                          'automatically. I will let you know the grade soon.'
WRONG_TITLE_TEXT = "Uh-oh! Something wrong with your submission title. " \
                   "Please rename it as hw-_N_, where _N_ is the number of " \
                   "the homework you are trying to submit."
WRONG_TYPE_TEXT = 'Uh-oh! Your submission is not a Jupyter notebook!'
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
    hw_id = None
    filepath = None
    if file_size / 1048576 > 20:
        text = 'File is too big.'

    if mime_type in MIMES and file_name.endswith('.ipynb'):
        hw_id = check_title(file_name, conn)
        if hw_id is not None:
            student_id, last_name, first_name = student
            directory = os.path.join(f'notebooks',
                                     f'{last_name}-{first_name}-'
                                     f'{student_id:03}', f'hw{hw_id}')
            if not os.path.exists(directory):
                os.makedirs(directory)
            download = get_file(file_id)
            time = datetime.fromtimestamp(msg['date'])
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
                        LIMIT 1
                    ), deadline AS (
                        SELECT deadline < :submitted_at AS expired
                        FROM homeworks
                        WHERE hw_id = :hw_id
                        LIMIT 1
                    )
                    INSERT INTO submissions (
                        file_id, path, student_id, hw_id, ordinal,
                        submitted_at, expired
                    )
                    SELECT
                        :file_id, :path||'_'||next||'_'||
                        to_char(:submitted_at, 'YYMONDD-HHMISS')||'.ipynb',
                        :student_id, :hw_id, next, :submitted_at,
                        expired
                    FROM ord, deadline
                    RETURNING submission_id, ordinal, path
                """, row)

                submission_id, ordinal, filepath = cursor.first()

                with open(filepath, 'wb') as f:
                    f.write(download)

                #   TODO: replace with global var SUCCESS_UPLOAD_TEMPLATE
                text = SUCCESS_UPLOAD_TEXT.format(hw_id, ordinal,
                                                  first_name, last_name)
                conn.commit()

            except Exception as e:
                logging.error('%d', hw_id)
                logging.error('%s', type(e))
                logging.error('%s', e)
                conn.rollback()

        else:
            text = WRONG_TITLE_TEXT
    else:
        text = WRONG_TYPE_TEXT

    return text, submission_id, ordinal, file_id, hw_id, filepath


def try_connect_db(dsn, nattempts=5):
    template = 'failed database connection. next attempt in %d second(s).'
    for i in range(nattempts):
        try:
            conn = connect_database(dsn)
            conn.execute('SELECT 1')
            logging.info('connected to database.')
            return conn
        except:
            logging.warn(template, 2**i)
            sleep(2**i)
            continue
    logging.error('failed to connect to database.')


def check_title(file_name, conn):
    if not file_name.startswith('hw-'):
        return
    if file_name[3:-6] == 'test':
        hw_id = 0
        logging.info('testing notebook')
    else:
        try:
            hw_id = int(file_name[3:-6])
        except ValueError:
            return

        cursor = conn.execute("""
            SELECT EXISTS (
                SELECT *
                FROM homeworks
                WHERE hw_id = :hw_id)
        """, {'hw_id': hw_id})
        hw_exists = cursor.fetchone()[0]
        if not hw_exists:
            return

    return hw_id


def patch_magic():
    """Patch matplotlib magic with a stub function and set default matplotlib
    backend as `agg` which is suitable for non-interactive mode.
    """

    def stub(self, *args, **kwargs):
        """This function is a stub to avoid issue with interactivity in
        non-interactive mode that arises due to the use of `%matplotlib` magic.
        """
        pass

    try:
        from IPython.core.magics.pylab import PylabMagics
        PylabMagics.matplotlib = stub
        from matplotlib import use
        use('agg')
    except Exception as e:
        logging.error('CELL: during ipython magic patching an exception was '
                      'raised', exc_info=True)
        exit(1)
