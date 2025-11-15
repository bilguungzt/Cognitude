#!/usr/bin/env python3
"""
Diagnostic script to understand where configuration is being loaded from.
"""

import os
import sys
from pathlib import Path

def diagnose_config_loading():
    """Diagnose how configuration is being loaded."""
    print("=== CONFIGURATION LOADING DIAGNOSIS ===\n")
    
    # Check if .env file exists and is readable
    print("1. .ENV FILE STATUS:")
    env_path = Path('.env')
    print(f"   .env file exists: {env_path.exists()}")
    if env_path.exists():
        print(f"   .env file readable: {os.access(env_path, os.R_OK)}")
        print(f"   .env file size: {env_path.stat().st_size} bytes")
        
        # Show the actual content (masking secrets)
        print("   .env file content:")
        with open(env_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line and not line.startswith('#'):
                    if 'KEY' in line or 'PASSWORD' in line or 'TOKEN' in line:
                        # Mask sensitive values
                        key, value = line.split('=', 1)
                        print(f"     {line_num}: {key}=***")
                    else:
                        print(f"     {line_num}: {line}")
                elif line.startswith('#'):
                    print(f"     {line_num}: {line}")
    print()
    
    # Check Python path
    print("2. PYTHON PATH:")
    for i, path in enumerate(sys.path):
        print(f"   {i}: {path}")
    print()
    
    # Check environment before and after loading
    print("3. ENVIRONMENT VARIABLES BEFORE LOADING:")
    db_url_before = os.getenv('DATABASE_URL')
    print(f"   DATABASE_URL: {'SET' if db_url_before else 'NOT SET'}")
    
    # Try to load .env manually
    print("\n4. TRYING TO LOAD .ENV MANUALLY:")
    try:
        from dotenv import load_dotenv
        loaded = load_dotenv()
        print(f"   load_dotenv() returned: {loaded}")
        
        db_url_after = os.getenv('DATABASE_URL')
        print(f"   DATABASE_URL after load_dotenv(): {'SET' if db_url_after else 'NOT SET'}")
        if db_url_after and db_url_after != db_url_before:
            print("   ✓ .env file was loaded successfully")
        else:
            print("   ⚠ .env file was not loaded or DATABASE_URL not found in it")
            
    except ImportError:
        print("   ✗ python-dotenv not installed")
    print()
    
    # Check Pydantic settings loading
    print("5. PYDANTIC SETTINGS LOADING:")
    try:
        from app.config import get_settings
        settings = get_settings()
        
        print(f"   Settings loaded from: {settings.__class__.__name__}")
        print(f"   Config env_file: {settings.__class__.Config.env_file}")
        print(f"   DATABASE_URL in settings: {'SET' if settings.DATABASE_URL else 'NOT SET'}")
        
        # Check where it might be coming from if not from .env
        if settings.DATABASE_URL and not os.getenv('DATABASE_URL'):
            print("   ⚠ DATABASE_URL is set in settings but not in environment!")
            print("   This suggests it's coming from:")
            print("     - alembic.ini configuration")
            print("     - Default value in config.py")
            print("     - Another configuration source")
            
    except Exception as e:
        print(f"   ✗ Error loading settings: {e}")
    print()
    
    # Check alembic.ini for database URL
    print("6. ALEMBIC.INI DATABASE URL:")
    try:
        with open('alembic.ini', 'r') as f:
            for line in f:
                if 'sqlalchemy.url' in line and not line.strip().startswith('#'):
                    print(f"   {line.strip()}")
                    break
    except Exception as e:
        print(f"   ✗ Error reading alembic.ini: {e}")
    print()

if __name__ == "__main__":
    diagnose_config_loading()