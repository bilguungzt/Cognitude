import os
import sys
from types import SimpleNamespace

# Ensure in-memory SQLite is used for tests
os.environ['DATABASE_URL'] = 'sqlite+pysqlite:///:memory:'

from fastapi.testclient import TestClient

# Import the app after setting DATABASE_URL
import app.main as main
from app.security import get_organization_from_api_key
from app.database import get_db
from datetime import datetime
from types import SimpleNamespace

# Create a fake DB that will mimic the minimal methods used by the endpoint
class FakeDB:
    def __init__(self):
        # Simulate an existing RateLimitConfig for organization 1
        now = datetime.utcnow().isoformat()
        self._config = SimpleNamespace(
            id=1,
            organization_id=1,
            requests_per_minute=100,
            requests_per_hour=3000,
            requests_per_day=50000,
            enabled=True,
            created_at=now,
            updated_at=now
        )

    def query(self, model):
        # Return an object with filter(...).first() chain
        class Q:
            def __init__(self, cfg):
                self.cfg = cfg
            def filter(self, *args, **kwargs):
                return self
            def first(self):
                return self.cfg

        return Q(self._config)

    def add(self, obj):
        return None
    def commit(self):
        return None
    def refresh(self, obj):
        return None

fake_db = FakeDB()

# Override the organization dependency to return a fake org
def fake_org():
    return SimpleNamespace(id=1, name='TestOrg')

main.app.dependency_overrides[get_organization_from_api_key] = fake_org
main.app.dependency_overrides[get_db] = lambda: fake_db

# Run the test client
client = TestClient(main.app)

print('Making GET /rate-limits/config')
resp = client.get('/rate-limits/config', headers={'X-API-Key': 'dummy'})
print('Status code:', resp.status_code)
try:
    print('Response JSON:', resp.json())
except Exception as e:
    print('Failed to parse JSON response:', e)
    print('Response text:', resp.text)

# If there were exceptions printed to stdout by the app, they appear above.
