#   encoding: utf-8
#   cli.py
"""NLA bot's command line interface (cli)."""

import click
import logging

from importlib import import_module
from json import dump
from os.path import basename, dirname, realpath, splitext
from redis import Redis
from requests import Session
from rq import Connection, Queue, Worker
from sys import path, stdout

from .telegram import get_updates
from .handlers import handle_update
from .settings import DB_URI, REDIS_HOST
from .utils import try_connect_db, patch_magic


@click.group(help=__doc__)
def main():
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                        level=logging.INFO)


@main.command(help='Run long polling loop.')
@click.option('--dsn', default=DB_URI, help='Data Service Name.')
@click.option('--redis-host',
              default=REDIS_HOST,
              help='Redis Queue (RQ) message broker.')
def serve(dsn, redis_host):
    logging.info('nla bot started.')
    conn = try_connect_db(dsn)
    #   TODO: check if redis is connected before processing updates.
    queue = Queue(connection=Redis(host=redis_host))
    sess = Session()
    offset = 0

    while True:
        updates = get_updates(offset=offset, sess=sess)

        if updates is None:
            continue

        for upd in updates.get('result'):
            upd_id = handle_update(upd, sess, conn, queue)
            offset = max(offset, upd_id) + 1


@main.command(help='Launch worker for homework processing.')
@click.option('--dsn', default=DB_URI, help='Data Service Name.')
@click.option('--redis-host',
              default=REDIS_HOST,
              help='Redis Queue (RQ) message broker.')
def work(dsn, redis_host):
    logging.info('nla ta started.')
    with Connection(Redis(host=redis_host)):
        worker = Worker(['default'])
        worker.work()


@main.command(help='Isolate homework processing.')
@click.option('-o', '--output',
              type=click.Path(),
              help='Optional output file.')
@click.argument('pset', type=click.Choice(['test']))
@click.argument('filename', type=click.Path(exists=True))
def imprison(output, pset, filename):
    logging.info('CELL: cell created for %s.', filename)
    logging.info('CELL: patch ipython matplotlib magic')

    patch_magic()
    path.append(dirname(realpath(filename)))

    try:
        from .nbloader import NotebookFinder  # noqa
        module = import_module(splitext(basename(filename))[0])
    except Exception as e:
        logging.error('CELL: during homework processing an exception was '
                      'raised.', exc_info=True)
        exit(0)

    import nlabot.checkers as checkers

    try:
        checker = getattr(checkers, f'{pset.capitalize()}Checker')
        result = checker(module)()
    except Exception as e:
        logging.error('CELL: checker failed.', exc_info=True)
        exit(1)

    if output:
        fout = open(output, 'w')
    else:
        fout = stdout

    dump(result, fout, ensure_ascii=False)
    fout.flush()
    fout.close()
