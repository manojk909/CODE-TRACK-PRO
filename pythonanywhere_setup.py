"""
PythonAnywhere Database Setup Script
Run this script once in PythonAnywhere console to set up your database
"""

import os
from app import app, db

def setup_database():
    """Create database tables for PythonAnywhere deployment"""
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            print("✅ Database tables created successfully!")
            
            # Print table names to confirm
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"📊 Created tables: {', '.join(tables)}")
            
        except Exception as e:
            print(f"❌ Error creating database: {e}")

if __name__ == "__main__":
    setup_database()