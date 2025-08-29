"""Debug TaskQueue test in isolation."""

import subprocess
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
src_dir = project_root / "src"
src_path = str(src_dir).replace('\\', '\\\\')

test_code = f"""
import sys
sys.path.insert(0, r'{src_path}')

# Test TaskQueue basic functionality
from manager.core.queue import TaskQueue
from manager.core.schemas import TaskSpec

# Create a temporary database
import tempfile
import os
temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
temp_db.close()

print(f"temp_db created: {{temp_db.name}}")

# Set database URL for testing
os.environ['MANAGER_DB_URL'] = f'sqlite:///{{temp_db.name}}'

try:
    # Test TaskQueue initialization
    queue = TaskQueue()
    print("TaskQueue created successfully")
    
    print("Test completed successfully")
    
except Exception as e:
    print(f"ERROR: {{e}}")
    import traceback
    traceback.print_exc()

finally:
    # Cleanup
    if os.path.exists(temp_db.name):
        os.unlink(temp_db.name)
        print("Cleaned up temp database")
"""

print("Running TaskQueue debug test:")
print("=" * 40)

result = subprocess.run([sys.executable, "-c", test_code], 
                       capture_output=True, text=True, timeout=15)

print(f"Return code: {result.returncode}")
print(f"Output:\n{result.stdout}")
if result.stderr:
    print(f"Errors:\n{result.stderr}")