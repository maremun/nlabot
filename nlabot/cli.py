#   encoding: utf-8
#   cli.py
"""NLA bot's command line interface (cli)."""

import click
import logging
from redis import Redis
from rq import Connection, Queue, Worker

from requests import Session
from .models import connect_database
from .telegram import get_updates
from .handlers import handle_update


@click.group(help=__doc__)
def main():
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                        level=logging.INFO)


@main.command(help='Run long polling loop.')
@click.option('--dsn', default='postgres://nlabot@127.0.0.1/nlabot')
@click.option('--redis-host', default='127.0.0.1', help='')
def main_loop(dsn, redis_host):
    queue = Queue(connection=Redis(host=redis_host))
    conn = connect_database(dsn)
    sess = Session()
    offset = 0

    while True:
        updates = get_updates(offset=offset, sess=sess)

        if updates is None:
            continue

        for upd in updates.get('result'):
            upd_id = handle_update(upd, sess, conn, queue)
            offset = max(offset, upd_id) + 1


@main.command(help='')
@click.option('--dsn', default='postgres://nlabot@127.0.0.1/nlabot')
@click.option('--redis-host', default='127.0.0.1', help='')
def worker(dsn, redis_host):
    with Connection(Redis(host=redis_host)):
        worker = Worker(['default'])
        worker.work()
