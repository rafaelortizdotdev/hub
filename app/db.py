import os
import sqlite3
from flask import current_app


def get_db_connection():
    db_path = os.path.join(current_app.instance_path, 'honor_hub.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


