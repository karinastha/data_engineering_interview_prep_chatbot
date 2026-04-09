"""
Test conversation history and follow-up project selection.
Simulates the exact user scenario: projects → ELT → should get ELT project details.
"""

from services.preprocessing import PreprocessingService
from utils.helper_cred import get_llm


def test_conversation_flow():
    """Test the complete conversation flow for project selection."""
    print("=" * 70)
    print("TESTING CONVERSATION FLOW: PROJECT SELECTION")
    print("=" * 70)

    try:
        llm = get_llm()
        preprocessing_service = PreprocessingService(llm)

        # Simulate the conversation history
        conversation_history = [
            {
                "role": "user",
                "content": "give me real based projects",
            },
            {
                "role": "assistant",
                "content": '📁 **Real-World Data Engineering Projects**\n\nI have hands-on projects to help you build your portfolio:\n\n1. **ETL to Insights** - Build a complete ETL pipeline\n2. **ELT with dbt** - Production-grade ELT pipeline\n\nWhich project interests you? Just say **"ETL project"** or **"ELT project"** for full details.',
            },
        ]

        # Test Case 1: First message - asking for projects
        print("\n" + "─" * 70)
        print("STEP 1: User asks for projects")
        print("─" * 70)
        print("Message: 'give me real based projects'")
        print("History: []")

        result1 = preprocessing_service.preprocess(
            message="give me real based projects",
            history=[],
        )

        print(f"Topic: {result1.topic}")
        print(f"Standalone query: '{result1.standalone_query}'")
        print(f"Is greeting: {result1.is_greeting}")

        if result1.topic == "Projects":
            print("✅ PASSED - Correctly classified as Projects")
        else:
            print("❌ FAILED - Should be Projects topic")
            return False

        # Test Case 2: Follow-up message - selecting ELT
        print("\n" + "─" * 70)
        print("STEP 2: User selects ELT project")
        print("─" * 70)
        print("Message: 'ELT'")
        print("Previous conversation shows project options...")

        result2 = preprocessing_service.preprocess(
            message="ELT",
            history=conversation_history,
        )

        print(f"Topic: {result2.topic}")
        print(f"Standalone query: '{result2.standalone_query}'")
        print(f"Is greeting: {result2.is_greeting}")

        # Check if it properly resolved context
        if result2.topic == "Projects":
            print("✅ PASSED - Correctly maintained Projects context")
        else:
            print("❌ FAILED - Should maintain Projects topic from context")
            return False

        if "ELT" in result2.standalone_query and "project" in result2.standalone_query.lower():
            print("✅ PASSED - Standalone query incorporates context")
        else:
            print("❌ FAILED - Standalone query should include 'ELT project'")
            print("   Expected something like 'ELT project details'")
            print(f"   Got: '{result2.standalone_query}'")
            return False

        # Test Case 3: Variations
        print("\n" + "─" * 70)
        print("STEP 3: Testing other variations")
        print("─" * 70)

        test_variations = [
            ("ETL", "Should resolve to ETL project"),
            ("tell me about the ELT one", "Should resolve to ELT project"),
            ("the ELT project", "Should resolve to ELT project"),
        ]

        for variation, expected in test_variations:
            print(f"Testing: '{variation}'")
            result = preprocessing_service.preprocess(
                message=variation,
                history=conversation_history,
            )
            print(f"  Topic: {result.topic}")
            print(f"  Query: {result.standalone_query}")

            if result.topic == "Projects":
                print("  ✅ Correct topic")
            else:
                print("  ❌ Wrong topic")

        print("\n" + "=" * 70)
        print("🎉 CONVERSATION FLOW TEST PASSED!")
        print("=" * 70)
        print("\nNow when you test in Streamlit:")
        print("1. Ask: 'give me real based projects'")
        print("   → Should show project options")
        print("2. Reply: 'ELT'")
        print("   → Should retrieve ELT_DBT.md and show detailed project info")
        print("   → NOT general ELT concepts!")

        return True

    except Exception as e:
        print(f"❌ TEST FAILED - Error: {e}")
        return False


if __name__ == "__main__":
    success = test_conversation_flow()
    exit(0 if success else 1)
