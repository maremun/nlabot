#   encoding: utf-8
#   jail.py

from docker import APIClient
from json import loads
from os.path import realpath


def grade(submission_id, path):
    #   TODO: get notebook filename by submission_id and path
    pset = 'test'
    filename = 'notebooks/testnotebook.ipynb'
    result = isolate(pset, filename)
    print(result)
    #   TODO: store grade into database
    #   TODO: notify student


def isolate(pset, filename):
    notebook = realpath(filename)
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

    json = loads(cli.logs(container).decode('utf8'))  # TODO: use output file

    return json
