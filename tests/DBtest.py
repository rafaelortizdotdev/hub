import os
import sys
import sqlite3
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from flask import current_app


class DatabaseInspector:
    """Helper class to inspect database schema and data"""
    
    def __init__(self):
        self.app = create_app()
    
    def _get_connection(self):
        """Get database connection within app context"""
        db_path = os.path.join(current_app.instance_path, 'honor_hub.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def list_tables(self):
        """List all tables in the database schema"""
        with self.app.app_context():
            conn = self._get_connection()
            tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
            conn.close()
            return tables
    
    def get_columns(self, table):
        """Get columns for a specific table"""
        with self.app.app_context():
            conn = self._get_connection()
            columns = [row[1] for row in conn.execute(f'PRAGMA table_info({table})')]
            conn.close()
            return columns
    
    def get_table_info(self, table):
        """Get detailed info about a table (columns with types)"""
        with self.app.app_context():
            conn = self._get_connection()
            info = conn.execute(f'PRAGMA table_info({table})').fetchall()
            conn.close()
            return info
    
    def print_schema(self):
        """Print complete database schema"""
        tables = self.list_tables()
        print("Database Schema:")
        print("=" * 50)
        
        for table in tables:
            if table == 'alembic_version':  # Skip migration table
                continue
                
            print(f"\nTable: {table}")
            print("-" * 20)
            columns = self.get_columns(table)
            for col in columns:
                print(f"  - {col}")


def uri_configured():
    """Test database URI configuration"""
    app = create_app()
    assert 'SQLALCHEMY_DATABASE_URI' in app.config
    uri = app.config['SQLALCHEMY_DATABASE_URI']
    assert isinstance(uri, str) and len(uri) > 0


if __name__ == '__main__':
    # Show database URI
    app = create_app()
    print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print()
    
"""
inspector = DatabaseInspector()

# Get all tables
tables = inspector.list_tables()

# Get columns for specific table
columns = inspector.get_columns('stores')

# Get detailed table info (with types, constraints)
info = inspector.get_table_info('users')

# Print complete schema
inspector.print_schema()
"""