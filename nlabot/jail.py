#   encoding: utf-8
#   jail.py

import logging

from docker import APIClient
from json import JSONDecodeError, loads
from os.path import basename, exists, join

from .telegram import get_file, send_message
from .utils import try_connect_db
from .settings import DB_URI, HOST_PATH

GRADE_REPLY = 'Hey, your submission #{:d} to problem set #{:d} has been ' \
              'graded. Your grade for coding tasks is {:.2f}/{:.2f}. You ' \
              'have passed {:d}/{:d} tests.'
TIMEOUT_TEXT = 'You submission seems to run too long. This is indicative of ' \
               'an error. Please revise your submission and try again!'
SORRY_TEXT = 'There has been some trouble preparing to check you submission' \
             '. It will be resolved as soon as possible.'
PROBLEM_TEXT = 'There has been a trouble with your submission. Make sure it ' \
               'is a proper Jupyter notebook and resubmit.'


def grade(submission_id, ordinal, file_id, hw_id, filepath, chat_id):
    if hw_id == 0:
        pset = 'test'
    else:
        pset = 'pset' + str(hw_id)
    if not exists(filepath):
        file_to_check = get_file(file_id)
        with open(filepath, 'wb') as f:
            f.write(file_to_check)

    logging.info('processing submission #%d', submission_id)
    code, result = isolate(pset, filepath)

    if code != 0:
        if code in [1, 3]:
            send_message(chat_id, SORRY_TEXT)
        elif code == 2:
            send_message(chat_id, TIMEOUT_TEXT)
        elif code == 4:
            send_message(chat_id, PROBLEM_TEXT)
        logging.warn(result, submission_id)
        return

    # Calculate a grade
    grades = []
    passed_tests = 0
    total_tests = 0
    for i, f in enumerate(result):
        logging.info('function %d: %r', i, f)
        if f.get('exc_info', False):
            logging.error('%s', f['exc_info'])
        p = sum(f['pass'])
        n = len(f['pass'])
        if p == n:
            grades.append(1)
        else:
            grades.append(0)
        passed_tests += p
        total_tests += n

    conn = try_connect_db(DB_URI)
    # Get points per func in homeworks table and calculate total points for
    # submission
    row = {'hw_id': hw_id}
    cursor = conn.execute("""
        SELECT pts_per_func FROM homeworks
        WHERE hw_id = :hw_id
    """, row)
    pts_per_func = cursor.first()[0]

    pts_seq = []
    for g, p in zip(grades, pts_per_func):
        pts_seq.append(g * p)
    total_pts = sum(pts_per_func)

    # Update grade in db
    # Penalize while sending message/building reports
    row = {'grades': pts_seq, 'submission_id': submission_id,
           'hw_id': hw_id+1}
    # TODO: Fix to pick the best grade among submissions.
    cursor = conn.execute("""
        WITH update_sub AS (
            UPDATE submissions
            SET grades = :grades,
                grade = (SELECT SUM(s) FROM UNNEST(:grades) s)
            WHERE submission_id = :submission_id
            RETURNING student_id, expired
        )
        UPDATE students
        SET grades[:hw_id] = (
            CASE (SELECT expired from update_sub)
            WHEN TRUE THEN (SELECT SUM(s) FROM UNNEST(:grades) s) / 2.
            WHEN FALSE THEN (SELECT SUM(s) FROM UNNEST(:grades) s)
            END)
        WHERE student_id = (SELECT student_id FROM update_sub)
        RETURNING student_id, grades[:hw_id]
    """, row)
    conn.commit()
    logging.info('updated grade for submission %d, inserted value %r',
                 submission_id, pts_seq)
    student_id, grade = cursor.first()
    logging.info('sending message to student %d', student_id)

    text = GRADE_REPLY.format(ordinal, hw_id, grade, total_pts,
                              passed_tests, total_tests)
    send_message(chat_id, text)
    logging.info('finished grading submission #%d.', submission_id)
    return


def isolate(pset, filename):
    notebook = join(HOST_PATH, filename)
    result = join('/tmp', basename(filename) + '.txt')
    open(result, 'w').close()

    cli = APIClient()
    container = cli.create_container(
        image='nlabot_cell',
        command=['imprison', '-o', 'result.txt', pset, 'notebook.ipynb'],
        volumes=['/nlabot/notebook.ipynb'],
        network_disabled=True,
        host_config=cli.create_host_config(binds={
            notebook: {
                'bind': '/nlabot/notebook.ipynb',
                'mode': 'rw',
            },
            result: {
                'bind': '/nlabot/result.txt',
                'mode': 'rw',
            }
        }, cpu_period=50000, cpu_quota=100000, mem_limit='4g')
    )
    logging.info('container id is %s', container['Id'])

    try:
        cli.start(container)
    except Exception as e:
        logging.error('failed to start container.', exc_info=True)
        # TODO: send alert
        return 1, 'finished grading submission #%d due to container failure.'

    retcode = cli.wait(container, 1200)  # 20 minutes to grade
    logging.info('retcode is %d', retcode)
    logging.info('%s', cli.logs(container).decode('utf8'))

    if retcode == -1:
        return 2, 'finished grading submission #%d due to timeout.'
    elif retcode != 0:
        return 3, 'finished grading submission #%d due to some internal ' \
                  'problem.'

    with open(result) as f:
        content = f.read()

    if content == '':
        logging.warn('stdout is empty.')
        return 4, 'finished grading submission #%d due to a problem in ' \
                  'the notebook.'

    try:
        return 0, loads(content)
    except JSONDecodeError as e:
        logging.error('could not decode json', exc_info=True)
        return 3, 'finished grading submission #%d due to some internal ' \
                  'problem.'
