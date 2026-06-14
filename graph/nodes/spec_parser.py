import hashlib
import json
from pathlib import Path

import yaml

from config import GENERATED_TESTS_DIR
from graph.state import QAState

CACHE_FILE = GENERATED_TESTS_DIR / ".cache.json"


def _load_cache() -> dict:
    if CACHE_FILE.exists():
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    return {}


def _resolve_refs(obj: object, raw_spec: dict, visited: frozenset = frozenset()) -> object:
    """Recursively replace $ref pointers with the actual schema they point to."""
    if isinstance(obj, dict):
        if "$ref" in obj:
            ref = obj["$ref"]
            if ref in visited:
                return obj  # circular reference guard
            # "#/components/schemas/Post" → ["components", "schemas", "Post"]
            parts = ref.lstrip("#/").split("/")
            resolved = raw_spec
            for part in parts:
                resolved = resolved[part]
            return _resolve_refs(resolved, raw_spec, visited | {ref})
        return {k: _resolve_refs(v, raw_spec, visited) for k, v in obj.items()}

    if isinstance(obj, list):
        return [_resolve_refs(item, raw_spec, visited) for item in obj]

    return obj


def spec_parser(state: QAState) -> dict:
    # Tests pre-loaded via --reuse-tests — skip all parsing and cache checks
    if state.get("tests"):
        return {}

    spec_path = Path(state["spec"]["path"])

    if not spec_path.exists():
        return {"error": f"Spec file not found: {spec_path}"}

    try:
        content = spec_path.read_text(encoding="utf-8")
        raw = yaml.safe_load(content) if spec_path.suffix in (".yaml", ".yml") else json.loads(content)
    except Exception as e:
        return {"error": f"Failed to parse spec file: {e}"}

    spec_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

    # Cache hit — reuse tests already in tests/
    cache = _load_cache()
    if spec_hash in cache:
        cached_tests = sorted(str(p) for p in GENERATED_TESTS_DIR.glob("test_*.py"))
        if cached_tests:
            print(f"  (cache hit — reusing existing tests in {GENERATED_TESTS_DIR})")
            info = raw.get("info", {})
            return {
                "spec": {
                    "title": info.get("title", ""),
                    "version": info.get("version", ""),
                    "base_url": (raw.get("servers") or [{}])[0].get("url", ""),
                    "endpoints": [],
                    "raw": raw,
                },
                "spec_hash": spec_hash,
                "tests": cached_tests,
            }

    info = raw.get("info", {})
    servers = raw.get("servers", [])
    base_url = servers[0]["url"] if servers else ""

    endpoints = []
    for path, path_item in raw.get("paths", {}).items():
        test_ids = path_item.get("x-test-ids", {})
        for method, operation in path_item.items():
            if method in ("get", "post", "put", "patch", "delete"):
                endpoints.append({
                    "path": path,
                    "method": method.upper(),
                    "operationId": operation.get("operationId", ""),
                    "summary": operation.get("summary", ""),
                    "parameters": _resolve_refs(operation.get("parameters", []), raw),
                    "requestBody": _resolve_refs(operation.get("requestBody", {}), raw),
                    "responses": _resolve_refs(operation.get("responses", {}), raw),
                    "tags": operation.get("tags", []),
                    "testIds": test_ids,
                })

    return {
        "spec": {
            "title": info.get("title", ""),
            "version": info.get("version", ""),
            "base_url": base_url,
            "endpoints": endpoints,
            "raw": raw,
        },
        "spec_hash": spec_hash,
    }
