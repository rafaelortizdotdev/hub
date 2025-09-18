import os
import click
from flask import Flask
from flask_migrate import Migrate
from .extensions import db


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.secret_key = 'SECRET_KEY'  # TODO: load from env in production
    os.makedirs(app.instance_path, exist_ok=True)

    # Database URI: default to SQLite in instance/ unless DATABASE_URL provided
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'honor_hub.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Init extensions
    db.init_app(app)
    from . import models
    Migrate(app, db)

    # Register blueprints
    from .routes.auth import auth_bp
    from .routes.dashboard import dashboard_bp
    from .routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    # CLI commands
    @app.cli.command()
    @click.argument('table')
    @click.argument('data_file')
    def populate_table(table, data_file):
        """Populate any table from JSON/CSV file"""
        import json
        from .db import get_db_connection
        
        with open(data_file, 'r') as f:
            if data_file.endswith('.json'):
                data = json.load(f)
            else:  # CSV
                import csv
                reader = csv.DictReader(f)
                data = list(reader)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        for row in data:
            columns = ', '.join(row.keys())
            placeholders = ', '.join(['?' for _ in row])
            cursor.execute(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", list(row.values()))
        
        conn.commit()
        conn.close()
        print(f"Inserted {len(data)} rows into {table}")

    @app.cli.command()
    @click.argument('table')
    def clear_table(table):
        """Clear all data from a table"""
        from .db import get_db_connection
        conn = get_db_connection()
        conn.execute(f"DELETE FROM {table}")
        conn.commit()
        conn.close()
        print(f"Cleared table {table}")

    return app
