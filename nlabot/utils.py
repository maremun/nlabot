def check_started(row, conn):
    cursor = conn.execute("""
        SELECT * FROM users
        WHERE user_id = :user_id
    """, row)
    result = cursor.first()
    if result is None:
        return False
    else:
        return True


def check_registered(row, conn):
    cursor = conn.execute("""
        SELECT student_id FROM users
        WHERE user_id = :user_id
    """, row)
    result = cursor.first()
    if result[0] is None:
        return False, None
    else:
        return True, result[0]
