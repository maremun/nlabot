#   encoding: utf-8
#   handlers.py

def handle_update(update, sess, conn):
    print(update)
    return update['update_id']

