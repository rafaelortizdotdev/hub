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
        from .database import get_db_connection
        
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
        from .database import get_db_connection
        conn = get_db_connection()
        conn.execute(f"DELETE FROM {table}")
        conn.commit()
        conn.close()
        print(f"Cleared table {table}")

    @app.cli.command()
    @click.argument('table')
    @click.argument('out_file')
    @click.option('--format', 'fmt', type=click.Choice(['json', 'csv']), default='json', help='Output format')
    def generate_template(table, out_file, fmt):
        """Generate a JSON/CSV template for inserting rows into a table."""
        import json
        import csv
        from .database import get_db_connection

        conn = get_db_connection()
        # Read table schema
        columns = [row[1] for row in conn.execute(f'PRAGMA table_info({table})')]
        conn.close()

        if not columns:
            click.echo(f"Table '{table}' not found.")
            return

        # Heuristic: exclude typical auto fields from template input
        excluded = { 'id' }
        template_cols = [c for c in columns if c not in excluded]

        if fmt == 'json':
            # Create one sample object with empty values
            obj = {col: "" for col in template_cols}
            with open(out_file, 'w', encoding='utf-8') as f:
                json.dump([obj], f, ensure_ascii=False, indent=2)
        else:
            with open(out_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=template_cols)
                writer.writeheader()
                writer.writerow({col: '' for col in template_cols})

        click.echo(f"Template for table '{table}' written to {out_file} in {fmt.upper()} format.")
        click.echo (f"Cmd for populating table: flask populate_table {table} {out_file}")

    return app
