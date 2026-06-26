#!/usr/bin/env python
"""Test if the API can be started."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("Testing AI Manager API...")
print("=" * 50)

# Test imports
try:
    print("1. Testing core imports...")
    from manager.core.schemas import TaskSpec
    print("   ✓ Schemas imported")
except ImportError as e:
    print(f"   ✗ Failed to import schemas: {e}")
    sys.exit(1)

try:
    print("2. Testing database models...")
    from manager.store.models import DatabaseManager, create_db_and_tables
    print("   ✓ Database models imported")
except ImportError as e:
    print(f"   ✗ Failed to import database: {e}")
    sys.exit(1)

try:
    print("3. Testing API module...")
    from manager.api.http import app
    print("   ✓ API module imported")
except ImportError as e:
    print(f"   ✗ Failed to import API: {e}")
    sys.exit(1)

print("\n" + "=" * 50)
print("SUCCESS: All modules imported correctly!")
print("\nTo run the API server:")
print("  python -m uvicorn manager.api.http:app --reload")
print("\nOr use the Makefile:")
print("  make run")
