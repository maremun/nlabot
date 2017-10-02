#   encoding: utf-8
#   cli.py
"""NLA bot's command line interface (cli)."""

import click
import logging

from requests import Session
from .models import connect_database
from .telegram import get_updates
from .handlers import handle_update


@click.group(help=__doc__)
def main():
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                        level=logging.INFO)

@main.command(help='Run long polling loop.')
def main_loop():
    conn = connect_database('postgres://nlabot@127.0.0.1/nlabot')
    sess = Session()
    offset = 0

    while True:
        updates = get_updates(offset=offset, sess=sess)

        if updates is None:
            continue

        for upd in updates.get('result'):
            upd_id = handle_update(upd, sess, conn)
            offset = max(offset, upd_id) + 1
