#!/usr/bin/env python3
"""Lightweight DB inspector for local development.

Run from the repository root inside your venv to print organizations and
provider configs. Helpful to verify that an organization and API key hash
exist for the API key you're using from the frontend.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT)

from app.database import SessionLocal
from app import models


def main():
    session = SessionLocal()
    try:
        orgs = session.query(models.Organization).all()
        if not orgs:
            print("No organizations found in database.")
            return

        for org in orgs:
            print(f"Organization id={org.id} name={org.name}")
            print(f"  api_key_hash: {getattr(org, 'api_key_hash', None)}")
            # List provider configs
            providers = session.query(models.ProviderConfig).filter(models.ProviderConfig.organization_id == org.id).all()
            if not providers:
                print("  No provider configs")
            else:
                for p in providers:
                    print(f"  Provider id={p.id} provider={p.provider} enabled={p.enabled} priority={p.priority}")
    finally:
        session.close()


if __name__ == '__main__':
    main()
