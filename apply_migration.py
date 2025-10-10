#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Apply database migration for pending_stores table"""

import sqlite3
import os
import sys

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def apply_migration():
    db_path = os.path.join('instance', 'honor_hub.db')
    
    if not os.path.exists(db_path):
        print(f"[ERROR] Database not found at {db_path}")
        return False
    
    print(f"[INFO] Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(pending_stores)")
        columns = [col[1] for col in cursor.fetchall()]
        
        print(f"[INFO] Current columns in pending_stores: {columns}")
        
        # Add street column if not exists
        if 'street' not in columns:
            print("[+] Adding 'street' column...")
            cursor.execute("ALTER TABLE pending_stores ADD COLUMN street VARCHAR")
            print("[OK] Added 'street' column")
        else:
            print("[SKIP] 'street' column already exists")
        
        # Add level column if not exists
        if 'level' not in columns:
            print("[+] Adding 'level' column...")
            cursor.execute("ALTER TABLE pending_stores ADD COLUMN level VARCHAR")
            print("[OK] Added 'level' column")
        else:
            print("[SKIP] 'level' column already exists")
        
        # Add local column if not exists
        if 'local' not in columns:
            print("[+] Adding 'local' column...")
            cursor.execute("ALTER TABLE pending_stores ADD COLUMN local VARCHAR")
            print("[OK] Added 'local' column")
        else:
            print("[SKIP] 'local' column already exists")
        
        # Check if store_assignments table exists, if not create it
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='store_assignments'
        """)
        
        if not cursor.fetchone():
            print("[+] Creating 'store_assignments' table...")
            cursor.execute("""
                CREATE TABLE store_assignments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    staff_type VARCHAR NOT NULL,
                    staff_id VARCHAR NOT NULL,
                    store_type VARCHAR NOT NULL,
                    store_id VARCHAR NOT NULL,
                    role VARCHAR NOT NULL,
                    supervisor_id VARCHAR NOT NULL,
                    assigned_date DATETIME NOT NULL,
                    end_date DATETIME,
                    status VARCHAR NOT NULL DEFAULT 'PENDING',
                    approved_by VARCHAR,
                    approved_date DATETIME,
                    rejection_reason TEXT,
                    synced_to_erp BOOLEAN DEFAULT 0,
                    created_at DATETIME,
                    updated_at DATETIME,
                    FOREIGN KEY (supervisor_id) REFERENCES users(id),
                    FOREIGN KEY (approved_by) REFERENCES users(id)
                )
            """)
            print("[OK] Created 'store_assignments' table")
            
            # Create indexes
            print("[+] Creating indexes...")
            cursor.execute("CREATE INDEX idx_staff ON store_assignments(staff_type, staff_id)")
            cursor.execute("CREATE INDEX idx_store ON store_assignments(store_type, store_id)")
            cursor.execute("CREATE INDEX idx_role ON store_assignments(role)")
            cursor.execute("CREATE INDEX idx_status ON store_assignments(status)")
            cursor.execute("CREATE INDEX idx_supervisor ON store_assignments(supervisor_id)")
            print("[OK] Created indexes")
        else:
            print("[SKIP] 'store_assignments' table already exists")
        
        conn.commit()
        print("\n[SUCCESS] Migration completed successfully!")
        
        # Show updated schema
        print("\n[INFO] Updated pending_stores columns:")
        cursor.execute("PRAGMA table_info(pending_stores)")
        for col in cursor.fetchall():
            print(f"   - {col[1]} ({col[2]})")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    print("HONOR Hub Database Migration")
    print("=" * 50)
    success = apply_migration()
    print("=" * 50)
    exit(0 if success else 1)

