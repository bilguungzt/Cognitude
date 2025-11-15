#!/usr/bin/env python3
import sys
sys.path.append('/code')

from app.database import get_db
from app import crud, schemas, security
from sqlalchemy.orm import Session

def test_registration():
    db = next(get_db())
    try:
        # Test data
        test_name = "Test Org API"
        api_key = security.create_api_key()
        hashed_api_key = security.get_password_hash(api_key)

        print(f"Creating organization: {test_name}")
        print(f"API Key: {api_key[:20]}...")

        # Create organization
        org = crud.create_organization(
            db=db,
            organization=schemas.OrganizationCreate(name=test_name),
            api_key_hash=hashed_api_key,
            api_key_digest=security.compute_api_key_digest(api_key),
        )

        print(f"Success! Organization ID: {org.id}, Name: {org.name}")
        return True

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    test_registration()