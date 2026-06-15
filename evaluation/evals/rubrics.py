PLANNER_RUBRIC = """
Score whether the test plan adequately covers the API spec provided.

5 - All endpoints covered, scenarios match HTTP methods, correct test IDs used, expected status codes match the spec
3 - Most endpoints covered but missing scenarios or wrong status codes
1 - Endpoints missing, wrong IDs used, or status codes contradict the spec
"""

FAILURE_ANALYZER_RUBRIC = """
Score whether the failure classification is correct.

5 - Classification (test_bug / spec_bug / backend_bug) is correct, reasoning clearly explains why, suggested fix targets the right thing
3 - Classification is correct but reasoning is vague or suggested fix is off
1 - Wrong classification type, or reasoning contradicts the evidence
"""

FIX_SUGGESTER_RUBRIC = """
Score whether the fixed file content correctly addresses the failures.

5 - All flagged failures fixed, no other tests changed, assertions not weakened, file structure intact
3 - Failures partially fixed or minor unrelated changes introduced
1 - Failures not fixed, tests removed, or assertions weakened to force a pass
"""
