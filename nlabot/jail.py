#   encoding: utf-8
#   jail.py

import logging

from docker import APIClient
from json import loads
from os.path import realpath, exists

from .telegram import get_file, send_message
from .utils import try_connect_db
from .settings import DB_URI

grade_reply = 'Hey, your submission to problem set #{:d} has been graded. ' \
              'Your grade for coding tasks is {:d}/{:d}. You have passed ' \
              '{:d}/{:d} tests.'


def grade(submission_id, file_id, hw_id, filepath, chat_id):
    if hw_id == 0:
        pset = 'test'
    else:
        pset = 'pset' + str(hw_id)
    if not exists(filepath):
        file_to_check = get_file(file_id)
        with open(filepath, 'wb') as f:
            f.write(file_to_check)

    logging.info('processing submission #%d', submission_id)
    result = isolate(pset, filepath)

    # calculate a grade
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
    # get points per func in homeworks table and calculate total points for
    # submission
    row = {'hw_id': hw_id}
    cursor = conn.execute("""
        SELECT pts_per_func FROM homeworks
        WHERE hw_id = :hw_id
    """, row)
    pts = 0
    pts_per_func = cursor.first()[0]
    for g, p in zip(grades, pts_per_func):
        pts += g * p
    total_pts = sum(pts_per_func)

    # update grade in db
    row = {'grade': pts, 'submission_id': submission_id}
    cursor = conn.execute("""
        UPDATE submissions
        SET grade = :grade
        WHERE submission_id = :submission_id
        RETURNING student_id
    """, row)
    conn.commit()
    logging.info('updated grade for submission %d, inserted value %d',
                 submission_id, pts)
    student_id = cursor.first()[0]
    logging.info('sending message to student %d', student_id)

    text = grade_reply.format(hw_id, pts, total_pts, passed_tests, total_tests)
    send_message(chat_id, text)
    logging.info('processing submission #%d finished', submission_id)


def isolate(pset, filename):
    notebook = realpath(filename)
    notebook = '/Users/maremun/projects/nlabot/' + filename
    cli = APIClient()
    container = cli.create_container(
        image='nlabot_cell',
        command=['imprison', pset, 'notebook.ipynb'],
        volumes=['/nlabot/notebook.ipynb'],
        host_config=cli.create_host_config(binds={
            notebook: {
                'bind': '/nlabot/notebook.ipynb',
                'mode': 'rw',
            },
        })
    )
    logging.info('container id is %s', container['Id'])

    try:
        cli.start(container)
    except Exception as e:  # TODO: correct exception handling
        logging.error(e)
        exit(1)

    retcode = cli.wait(container, 600)  # TODO: exc handling

    if retcode == -1:
        return 'timeout'
    elif retcode != 0:
        return 'fail'

    logging.info('%s', cli.logs(container).decode('utf8'))
    #   TODO: use output file
    json = loads(cli.logs(container, stderr=False).decode('utf8'))

    return json
