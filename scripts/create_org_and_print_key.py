import os
import sys
from fastapi.testclient import TestClient

# Ensure project package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import main

client = TestClient(main.app)

resp = client.post('/auth/register', json={'name': 'Local Demo Org'})
print('Status:', resp.status_code)
try:
    print(resp.json())
except Exception:
    print(resp.text)
