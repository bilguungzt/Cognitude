#!/usr/bin/env python3
"""
Debug script for Google provider on server
"""
import sys
import os
sys.path.insert(0, '/code')

try:
    from app.database import SessionLocal
    from app import models, crud
    
    print("Testing database connection...")
    db = SessionLocal()
    
    # Check organizations
    orgs = db.query(models.Organization).all()
    print(f"Found {len(orgs)} organizations:")
    for org in orgs:
        print(f"  - ID: {org.id}, Name: {org.name}")
        
        # Check providers for this org
        providers = db.query(models.ProviderConfig).filter(
            models.ProviderConfig.organization_id == org.id
        ).all()
        print(f"    Providers: {len(providers)}")
        for p in providers:
            print(f"      - {p.provider}: enabled={p.enabled}, priority={p.priority}")
            if p.provider == 'google':
                try:
                    api_key = p.get_api_key()
                    print(f"        Google API key length: {len(api_key) if api_key else 0}")
                    print(f"        API key starts with: {api_key[:10] if api_key else 'None'}...")
                except Exception as e:
                    print(f"        Error getting Google API key: {e}")
    
    db.close()
    print("✅ Database test completed")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
