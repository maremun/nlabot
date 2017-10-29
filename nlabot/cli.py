#   encoding: utf-8
#   cli.py
"""NLA bot's command line interface (cli)."""

import click
import logging

from redis import Redis
from requests import Session
from rq import Connection, Queue, Worker

from .models import connect_database
from .telegram import get_updates
from .handlers import handle_update
from .settings import DB_URI, REDIS_HOST


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
