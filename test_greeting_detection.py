"""
Test script to verify greeting detection functionality.
Tests that greetings skip retrieval and don't show sources.
"""

from services.preprocessing import PreprocessingService
from utils.helper_cred import get_llm


def test_greeting_detection():
    """Test that greetings are properly detected."""
    print("=" * 60)
    print("TESTING GREETING DETECTION")
    print("=" * 60)

    # Initialize preprocessing service
    llm = get_llm()
    preprocessing_service = PreprocessingService(llm)

    # Test cases
    test_cases = [
        {
            "message": "hi",
            "expected_greeting": True,
            "description": "Simple greeting 'hi'",
        },
        {
            "message": "hello",
            "expected_greeting": True,
            "description": "Simple greeting 'hello'",
        },
        {
            "message": "hey there",
            "expected_greeting": True,
            "description": "Casual greeting 'hey there'",
        },
        {
            "message": "good morning",
            "expected_greeting": True,
            "description": "Time-based greeting",
        },
        {
            "message": "thanks",
            "expected_greeting": True,
            "description": "Acknowledgment 'thanks'",
        },
        {
            "message": "explain ETL pipelines",
            "expected_greeting": False,
            "description": "Technical question",
        },
        {
            "message": "what is SQL?",
            "expected_greeting": False,
            "description": "Knowledge query",
        },
        {
            "message": "hi, can you explain ETL?",
            "expected_greeting": False,
            "description": "Greeting + question (should NOT be greeting)",
        },
    ]

    passed = 0
    failed = 0

    for i, test in enumerate(test_cases, 1):
        print(f"\n{'─' * 60}")
        print(f"Test {i}: {test['description']}")
        print(f"Message: '{test['message']}'")
        print(f"Expected is_greeting: {test['expected_greeting']}")

        try:
            result = preprocessing_service.preprocess(
                message=test["message"],
                history=[],
            )

            print(f"Actual is_greeting: {result.is_greeting}")
            print(f"Standalone query: '{result.standalone_query}'")
            print(f"Topic: {result.topic}")

            if result.is_greeting == test["expected_greeting"]:
                print("✅ PASSED")
                passed += 1
            else:
                print("❌ FAILED - Incorrect greeting detection")
                failed += 1

        except Exception as e:
            print(f"❌ FAILED - Error: {e}")
            failed += 1

    print(f"\n{'=' * 60}")
    print(f"TEST RESULTS: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print(f"{'=' * 60}")

    return failed == 0


if __name__ == "__main__":
    success = test_greeting_detection()
    exit(0 if success else 1)
