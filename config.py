from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = "claude-sonnet-4-6"
JUDGE_MODEL_NAME = "claude-haiku-4-5-20251001"
MAX_TOKENS = 2048
MAX_RETRIES = 3
GENERATED_TESTS_DIR = Path("generated")
TESTPLAN_DIR = Path("testplan")
REPORTS_DIR = Path("reports")
ANTHROPIC_API_KEY_ENV = "ANTHROPIC_API_KEY"
BASE_API_URL = "https://jsonplaceholder.typicode.com"
