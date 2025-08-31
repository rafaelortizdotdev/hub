#!/usr/bin/env python3
"""
Database initialization script for Honor Supervisor Hub
Creates all necessary tables and adds sample data
"""

import sqlite3
from datetime import datetime, date

def init_database():
    conn = sqlite3.connect('honor_hub.db')
    cursor = conn.cursor()
    
    # Create users table for supervisors
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            honor_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            password_hash TEXT DEFAULT "honor1##",
            is_first_login BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert test supervisor user
    cursor.execute('''
        INSERT OR IGNORE INTO users (honor_id, name, password_hash, is_first_login)
        VALUES (?, ?, ?, ?)
    ''', ('aw0142420', 'Test Supervisor', 'honor1##', 0))
    
    # Create pending_clients table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pending_clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            organization TEXT DEFAULT 'VE001',
            emp_type TEXT DEFAULT 'MSS Non-HN FF',
            nationality TEXT DEFAULT 'Venezuela',
            name TEXT NOT NULL,
            gender TEXT NOT NULL,
            contact_number TEXT NOT NULL,
            email TEXT,
            province TEXT NOT NULL,
            city TEXT NOT NULL,
            supervisor_id INTEGER NOT NULL,
            entry_date DATE DEFAULT CURRENT_DATE,
            status TEXT DEFAULT 'PENDING',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create pending_stores table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pending_stores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_name TEXT NOT NULL,
            avenida TEXT NOT NULL,
            street TEXT NOT NULL,
            market_center TEXT NOT NULL,
            level TEXT,
            local TEXT,
            city TEXT NOT NULL,
            capacity INTEGER,
            sales_last_month INTEGER,
            facade BOOLEAN DEFAULT 0,
            table_available BOOLEAN DEFAULT 0,
            supervisor_id INTEGER NOT NULL,
            status TEXT DEFAULT 'PENDING',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    

    

    
    # Create stores table for existing stores with APSVE codes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            apsve_code TEXT UNIQUE NOT NULL,
            store_name TEXT NOT NULL,
            avenida TEXT NOT NULL,
            street TEXT NOT NULL,
            market_center TEXT NOT NULL,
            level TEXT,
            local TEXT,
            city TEXT NOT NULL,
            capacity INTEGER,
            sales_last_month INTEGER,
            facade BOOLEAN DEFAULT 0,
            table_available BOOLEAN DEFAULT 0,
            supervisor_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create client_store relationship table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS client_store (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            store_id INTEGER NOT NULL,
            store_type TEXT NOT NULL,  -- 'pending' or 'existing'
            supervisor_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(client_id, store_id, store_type)
        )
    ''')
    

    
    # Insert sample stores for testing (assuming supervisor_id = 1)
    stores_data = [
        ('APS001', 'Flash Movil San Fernando', 'AV', 'Calle Principal', 'Mercado Central', 'PB', 'Local 1', 'San Fernando de Apure', 100, 85, 1, 1, 1),
        ('APS002', 'Flash Movil Maracay', 'AV', 'Calle Bolivar', 'Centro Comercial', '1er Nivel', 'Local 5', 'Maracay', 150, 120, 1, 0, 1),
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO stores (apsve_code, store_name, avenida, street, market_center, level, local, city, capacity, sales_last_month, facade, table_available, supervisor_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', stores_data)
    
    
    
    # Insert sample pending clients
    client_data = [
        ('Juan Pérez', 'Masculino', '4121234567', 'juan.perez@email.com', 'Apure', 'San Fernando de Apure', 1),
        ('María González', 'Femenino', '4149876543', 'maria.gonzalez@email.com', 'Aragua', 'Maracay', 1),
        ('Carlos Rodríguez', 'Masculino', '4165551234', 'carlos.rodriguez@email.com', 'Carabobo', 'Valencia', 1),
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO pending_clients 
        (name, gender, contact_number, email, province, city, supervisor_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', client_data)
    
    # Insert sample pending stores
    store_data = [
        ('Flash Móvil', 'San Fernando de Apure', 'Calle Principal', 'Mercado Central', 'PB', 'S/N', 'San Fernando de Apure', 100, 85, 1, 1, 1),
        ('Honor Store', 'Maracay', 'Av. Bolívar', 'Centro Comercial Sambil', '1', 'A-15', 'Maracay', 150, 120, 1, 1, 1),
        ('Móvil Express', 'Valencia', 'Calle Comercial', 'Mall del Centro', '2', 'B-20', 'Valencia', 200, 180, 1, 1, 1),
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO pending_stores 
        (store_name, city, street, market_center, level, local, city, capacity, sales_last_month, facade, table_available, supervisor_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', store_data)
    
    conn.commit()
    conn.close()
    
    print("Database initialized successfully!")
    print("Created tables: users, pending_clients, pending_stores, market_centers, stores, client_store")
    print("Added test user: aw0142420 (password: honor1##)")
    print("Added sample data for testing")

if __name__ == '__main__':
    init_database()
