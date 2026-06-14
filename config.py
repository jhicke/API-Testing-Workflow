from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = "claude-sonnet-4-6"
MAX_TOKENS = 8192
MAX_RETRIES = 3
GENERATED_TESTS_DIR = Path("tests")
TESTPLAN_DIR = Path("testplan")
REPORTS_DIR = Path("reports")
ANTHROPIC_API_KEY_ENV = "ANTHROPIC_API_KEY"
BASE_API_URL = "https://jsonplaceholder.typicode.com"
