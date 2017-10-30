#   encoding: utf-8
#   jail.py

import logging

from docker import APIClient
from json import loads
from os.path import realpath, exists

from .telegram import get_file


def grade(submission_id, file_id, hw_id, filepath):
    #   TODO: pset = f'pset{hw_id}' when hw checkers are ready.
    pset = 'test'
    if not exists(filepath):
        file_to_check = get_file(file_id)
        with open(filepath, 'wb') as f:
            f.write(file_to_check)

    result = isolate(pset, filepath)
    print(result)
    #   TODO: store grade into database
    #   TODO: notify student


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

    print('container id is', container['Id'])

    try:
        cli.start(container)
    except Exception as e:  # TODO: correct exception handling
        print(e)
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
