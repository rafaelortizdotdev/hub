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

    # -----------------------------
    # CLI commands (templates I/O)
    # -----------------------------
    def _tablename_filename(tablename: str) -> str:
        return f"{tablename}.json"

    def _model_files():
        from .models import iter_mapped_models
        return [(m, _tablename_filename(m.__tablename__)) for m in iter_mapped_models()]

    def _write_templates_dir(out_dir, templates):
        import json
        os.makedirs(out_dir, exist_ok=True)
        for tablename, obj in templates.items():
            path = os.path.join(out_dir, _tablename_filename(tablename))
            with open(path, 'w', encoding='utf-8') as f:
                json.dump([obj], f, ensure_ascii=False, indent=2)

    def _load_json(path):
        import json
        with open(path, 'r', encoding='utf-8') as f:
            try:
                return json.load(f) or []
            except json.JSONDecodeError:
                return []
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

    @app.cli.command("generate-all-templates")
    @click.argument('out_dir')
    def generate_all_templates(out_dir):
        """Generate JSON templates for all core tables into OUT_DIR."""
        from .models import generate_general_template
        templates = generate_general_template()
        _write_templates_dir(out_dir, templates)
        click.echo(f"Wrote templates to {out_dir}")

    @app.cli.command("load-templates")
    @click.argument('in_dir')
    @click.option('--reset-after', is_flag=True, default=True, help='Reset templates back to blank after load')
    @click.option('--only', multiple=True, help='Only load specified tables (can repeat)')
    @click.option('--except', 'except_', multiple=True, help='Skip specified tables (can repeat)')
    @click.option('--dry-run', is_flag=True, default=False, help='Validate and show counts, but do not commit')
    def load_templates(in_dir, reset_after, only, except_, dry_run):
        """Load JSON data from IN_DIR into tables; optionally reset templates afterwards.

        --only and --except take table names (matching __tablename__).
        FK-aware order is applied automatically based on model metadata.
        """
        from sqlalchemy.exc import IntegrityError
        from sqlalchemy import inspect as sa_inspect
        model_files = _model_files()

        # Filter by only/except
        if only:
            only_set = set(only)
            model_files = [(m, f) for (m, f) in model_files if m.__tablename__ in only_set]
        if except_:
            excl = set(except_)
            model_files = [(m, f) for (m, f) in model_files if m.__tablename__ not in excl]

        # Build FK dependency graph and sort (parents first)
        def deps_of(model):
            mapper = sa_inspect(model)
            deps = set()
            for col in model.__table__.columns:
                for fk in getattr(col, 'foreign_keys', []):
                    deps.add(fk.column.table.name)
            # keep only those we are actually loading
            return {d for d in deps}

        tab_to_model = {m.__tablename__: (m, f) for (m, f) in model_files}
        graph = {t: set() for t in tab_to_model}
        for t, (m, _f) in tab_to_model.items():
            graph[t] = {d for d in deps_of(m) if d in tab_to_model}

        # Kahn's algorithm for topo sort
        sorted_tabs = []
        no_deps = [t for t, ds in graph.items() if not ds]
        while no_deps:
            t = no_deps.pop()
            sorted_tabs.append(t)
            for u, ds in list(graph.items()):
                if t in ds:
                    ds.remove(t)
                    if not ds and u not in sorted_tabs and u not in no_deps:
                        no_deps.append(u)
        # Append any remaining (cycles) in arbitrary order
        remaining = [t for t in graph if t not in sorted_tabs]
        load_order = [(tab_to_model[t][0], tab_to_model[t][1]) for t in (sorted_tabs + remaining)]

        loaded_counts = {}
        with app.app_context():
            for model, filename in load_order:
                path = os.path.join(in_dir, filename)
                if not os.path.exists(path):
                    continue
                rows = _load_json(path)
                # Skip blank placeholder-only templates
                if len(rows) == 1 and all(v in ("", 0, None) for v in rows[0].values()):
                    loaded_counts[filename] = 0
                    continue

                count = 0
                model_columns = {c.name for c in model.__table__.columns}
                for row in rows:
                    try:
                        obj = model(**{k: v for k, v in row.items() if k in model_columns})
                        db.session.add(obj)
                        count += 1
                    except TypeError:
                        # Row had unknown fields; ignore
                        continue
                if dry_run:
                    db.session.rollback()
                else:
                    try:
                        db.session.commit()
                    except IntegrityError:
                        db.session.rollback()
                        # Fallback to upsert-ish: try merge each
                        count = 0
                        for row in rows:
                            try:
                                obj = model(**{k: v for k, v in row.items() if k in model_columns})
                                db.session.merge(obj)
                                count += 1
                            except TypeError:
                                continue
                        if dry_run:
                            db.session.rollback()
                        else:
                            db.session.commit()

                loaded_counts[filename] = count

        click.echo(f"Loaded data: {loaded_counts}")

        if reset_after:
            # Regenerate blank templates to neutral state
            from .models import generate_general_template
            templates = generate_general_template()
            _write_templates_dir(in_dir, templates)
            click.echo("Templates reset to neutral state.")

    return app
