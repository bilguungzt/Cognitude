#!/usr/bin/env python3
import sys
sys.path.insert(0, '/code')

from app.database import get_db
from app import models

db = next(get_db())
provider = db.query(models.ProviderConfig).filter(models.ProviderConfig.provider == 'google').first()
print(f'Found provider: {provider}')
if provider:
    provider.api_key_encrypted = 'AIzaSyAwCM5JJ9ZgIDqfcFzILwJX8dUm8CIWQH0'
    db.commit()
    print('Updated Google API key')
else:
    print('Google provider not found')