#!/usr/bin/env python3
from app.database import engine
from sqlalchemy import text
try:
    with engine.connect() as conn:
        result = conn.execute(text('SELECT 1'))
        print('Database connection: OK')

        result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
        tables = [row[0] for row in result]
        print(f'Tables: {tables}')

        if 'organizations' in tables:
            print('Organizations table exists')
        else:
            print('Organizations table missing!')

except Exception as e:
    print(f'Database error: {e}')