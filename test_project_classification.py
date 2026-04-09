"""
Test project classification after preprocessing fix.
"""

from services.preprocessing import PreprocessingService
from utils.helper_cred import get_llm


def test_project_classification():
    """Test that project requests are properly classified as topic='Projects'."""
    print("=" * 60)
    print("TESTING PROJECT REQUEST CLASSIFICATION")
    print("=" * 60)

    llm = get_llm()
    preprocessing_service = PreprocessingService(llm)

    test_cases = [
        {
            "message": "give me real world ETL projects",
            "expected_topic": "Projects",
            "description": "Real world ETL project request",
        },
        {
            "message": "show me hands-on projects",
            "expected_topic": "Projects",
            "description": "Hands-on project request",
        },
        {
            "message": "ETL project",
            "expected_topic": "Projects",
            "description": "Direct ETL project request",
        },
        {
            "message": "ELT project",
            "expected_topic": "Projects",
            "description": "Direct ELT project request",
        },
        {
            "message": "portfolio projects",
            "expected_topic": "Projects",
            "description": "Portfolio project request",
        },
        {
            "message": "explain ETL pipelines",
            "expected_topic": "ETL",
            "description": "ETL concept question (should NOT be Projects)",
        },
    ]

    passed = 0
    failed = 0

    for i, test in enumerate(test_cases, 1):
        print(f"\n{'─' * 60}")
        print(f"Test {i}: {test['description']}")
        print(f"Message: '{test['message']}'")
        print(f"Expected topic: {test['expected_topic']}")

        try:
            result = preprocessing_service.preprocess(
                message=test["message"],
                history=[],
            )

            print(f"Actual topic: {result.topic}")
            print(f"Standalone query: '{result.standalone_query}'")
            print(f"Is greeting: {result.is_greeting}")

            if result.topic == test["expected_topic"]:
                print("✅ PASSED")
                passed += 1
            else:
                print("❌ FAILED - Incorrect topic classification")
                failed += 1

        except Exception as e:
            print(f"❌ FAILED - Error: {e}")
            failed += 1

    print(f"\n{'=' * 60}")
    print(f"CLASSIFICATION TEST RESULTS: {passed} passed, {failed} failed")
    print(f"{'=' * 60}")

    return failed == 0


if __name__ == "__main__":
    success = test_project_classification()
    if success:
        print("\n🎉 Project classification fix is working!")
        print("   Now 'give me real world ETL projects' should:")
        print("   1. Be classified as topic='Projects'")
        print("   2. Retrieve project overview + ETL_INSIGHTS.md")
        print("   3. Show project options instead of generic response")
    else:
        print("\n⚠️  Project classification needs more work")

    exit(0 if success else 1)
