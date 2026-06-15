"""Delete all cached test plans and generated tests so the next run regenerates everything."""
import shutil
from config import GENERATED_TESTS_DIR, TESTPLAN_DIR

removed = []

for path in [
    TESTPLAN_DIR / ".cache.json",
    TESTPLAN_DIR / "test_plan.json",
    GENERATED_TESTS_DIR / ".cache.json",
]:
    if path.exists():
        path.unlink()
        removed.append(str(path))

for path in GENERATED_TESTS_DIR.glob("test_*.py"):
    path.unlink()
    removed.append(str(path))

if removed:
    for p in removed:
        print(f"  removed {p}")
else:
    print("  nothing to clear")
