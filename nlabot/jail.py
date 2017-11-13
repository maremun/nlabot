#   encoding: utf-8
#   jail.py

import logging

from docker import APIClient
from json import JSONDecodeError, loads
from os.path import basename, exists, join

from .telegram import get_file, send_sticker, send_message
from .utils import try_connect_db
from .settings import DB_URI, HOST_PATH
from .stickers import get_random_sticker, FAIL, SORRY, SUCCESS, TRY

GRADE_REPLY = 'Hey, your submission #{:d} to problem set #{:d} has been ' \
              'graded. The submission scored {:.2f}/{:.2f} points. You ' \
              'have passed {:d}/{:d} tests and received \[ {:s} ] points ' \
              'per each task. Your maximum grade for the problem set is ' \
              '{:.2f}.'
TIMEOUT_TEXT = 'You submission seems to run too long. This is indicative of ' \
               'an error. Please revise your submission and try again!'
SORRY_TEXT = 'There has been some trouble preparing to check you submission' \
             '. Report this to TA.'
PROBLEM_TEXT = 'There has been a trouble with your submission. This can be ' \
               'due to using Python 2, trying to connect to a network or ' \
               'using more memory than available. Also check that your ' \
               'submission is a proper Jupyter notebook and resubmit.'


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
            send_sticker(chat_id, get_random_sticker(SORRY))
        elif code == 2:
            send_message(chat_id, TIMEOUT_TEXT)
        elif code == 4:
            send_message(chat_id, PROBLEM_TEXT)
            send_sticker(chat_id, get_random_sticker(TRY))
        elif code == 5:
            send_message(chat_id, 'Problem set numbet you are trying to '
                                  'submit is not available.')
            send_sticker(chat_id, get_random_sticker(TRY))

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
# TODO send Memory and Syntax errors.
        p = sum(f['pass'])
        n = len(f['pass'])
        if p == n and n > 0:
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
    cursor = conn.execute("""
        WITH update_sub AS (
            UPDATE submissions
            SET grades = :grades,
                grade = (SELECT SUM(s) FROM UNNEST(:grades) s)
            WHERE submission_id = :submission_id
            RETURNING student_id, expired
        ), previous AS (
            SELECT grades[:hw_id] AS grade
            FROM students
            WHERE student_id = (SELECT student_id FROM update_sub)
        )
        UPDATE students
        SET grades[:hw_id] = (
            CASE (SELECT grade FROM previous) < (
                    CASE (SELECT expired from update_sub)
                    WHEN TRUE THEN (SELECT SUM(s) FROM UNNEST(:grades) s) / 2.
                    WHEN FALSE THEN (SELECT SUM(s) FROM UNNEST(:grades) s)
                    END)
            WHEN TRUE THEN (
                CASE (SELECT expired from update_sub)
                WHEN TRUE THEN (SELECT SUM(s) FROM UNNEST(:grades) s) / 2.
                WHEN FALSE THEN (SELECT SUM(s) FROM UNNEST(:grades) s)
                END)
            WHEN FALSE THEN (SELECT grade FROM previous)
            END)
        WHERE student_id = (SELECT student_id FROM update_sub)
        RETURNING student_id, grades[:hw_id], (
            CASE (SELECT expired FROM update_sub)
            WHEN TRUE THEN (SELECT SUM(s) FROM UNNEST(:grades) s) / 2.
            WHEN FALSE THEN (SELECT SUM(s) FROM UNNEST(:grades) s)
            END)

    """, row)
    conn.commit()
    logging.info('updated grade for submission %d, inserted value %r',
                 submission_id, pts_seq)
    student_id, grade, sub_grade = cursor.first()
    logging.info('sending message to student %d', student_id)

    text = GRADE_REPLY.format(ordinal, hw_id, sub_grade, total_pts,
                              passed_tests, total_tests,
                              ', '.join(str(p) for p in pts_seq), grade)
    send_message(chat_id, text)
    if sub_grade == total_pts:
        send_sticker(chat_id, get_random_sticker(SUCCESS))
    elif sub_grade == 0:
        send_sticker(chat_id, get_random_sticker(FAIL))
    else:
        send_sticker(chat_id, get_random_sticker(TRY))

    logging.ingo('sent message: %s', text)
    logging.info('finished grading submission #%d.', submission_id)
    return


def isolate(pset, filename):
    notebook = join(HOST_PATH, filename)
    ref_notebook = join(HOST_PATH, 'notebooks', pset + '.ipynb')
    result = join('/tmp', basename(filename) + '.txt')
    tests_module = join(HOST_PATH, 'nlabot', pset + '_tests.py')
    data = join(HOST_PATH, 'notebooks', 'data')
    open(result, 'w').close()
    logging.info(ref_notebook)
    if exists(ref_notebook):
        return 5, 'finished grading submission #%d due to wrong pset number.'

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
            },
            ref_notebook: {
                'bind': '/nlabot/data/reference.ipynb',
                'mode': 'ro',
            },
            tests_module: {
                'bind': '/nlabot/tests.py',
                'mode': 'rw',
            },
            data: {
                'bind': '/nlabot/data',
                'mode': 'ro',
            },
            # TODO: put this settings into settings.py
        }, cpu_period=100000, cpu_quota=100000, mem_limit='5g')
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
        logging.warn('file is empty.')
        return 4, 'finished grading submission #%d due to a problem in ' \
                  'the notebook.'

    try:
        return 0, loads(content)
    except JSONDecodeError as e:
        logging.error('could not decode json', exc_info=True)
        return 3, 'finished grading submission #%d due to some internal ' \
                  'problem.'
