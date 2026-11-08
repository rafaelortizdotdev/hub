#!/usr/bin/env python3
"""Supervisor Hub - Flask Application Runner"""

from app import create_app


app = create_app()


if __name__ == '__main__':
    import os
    app.run(
        debug=os.getenv('FLASK_DEBUG', '1') == '1',
        host='127.0.0.1',
        port=5000
    )

