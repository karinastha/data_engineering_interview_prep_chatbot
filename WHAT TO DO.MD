# Data Engineering Interview Prep Chatbot - Analysis & Roadmap

## What Are We Trying to Achieve?

We are building a **simple chatbot** that helps data engineers at Leapfrog prepare for interviews. The chatbot leverages Leapfrog's competency framework which defines:
- **Must Have** - Entry-level requirements
- **Desirable** - Mid-level skills
- **Advanced/Best** - Senior-level expertise

**Core User Journey**: User asks a question → We retrieve relevant competencies → We generate a helpful answer.

---

## 🔴 Critical Issues Identified

### Issue #1: DOUBLE Query Transformation (Major AI Quality Issue)

The system transforms the user query **TWICE**, wasting tokens and adding latency:

1. **First transformation in `app.py` → `classify_intent()`** (lines 175-215):
   - LLM extracts `standalone_query` as part of intent classification
   - Uses structured output with `IntentAnalysis` model

2. **Second transformation in `services/chat.py` → `_transform_query()`** (lines 284-328):
   - ANOTHER LLM call to transform the query again
   - Uses `TransformedQuery` structured output

**Impact**: 
- 2 LLM calls just to understand what the user is asking
- Each call adds ~1-2 seconds latency
- Doubles the cost for query understanding

---

### Issue #2: Over-Engineered Intent Classification

**What the intern built**: A complex intent routing system with 6 intents (`GREETING`, `SELECT_TOPIC`, `GENERATE_PRACTICE`, `ASK_QUESTION`, `CHANGE_TOPIC`, `UNKNOWN`).

**What we actually need**: 
- The chatbot has ONE job: Answer data engineering interview questions using RAG
- Topics are just metadata filters, not "modes" the user switches between
- "Generate practice questions" is just another question to RAG

**The problem**: The intent classifier in `app.py` uses an LLM call BEFORE we even do RAG. This is backwards - we should let RAG handle everything.

**Current flow**:
```
User Input → LLM Intent Classification → Route to Handler → (Maybe) LLM Query Transform → Retrieval → LLM Generate
           ^-- UNNECESSARY                              ^-- REDUNDANT
```

**Should be**:
```
User Input → Retrieval → LLM Generate (with conversation context)
```

---

### Issue #3: Duplicate RAG Implementations

We have **TWO** RAG systems:
1. `services/` folder - The "new" refactored approach (`chat.py`, `retrieval.py`, `ingestion.py`)
2. `src/` folder - The "old" approach (`rag_retrieval.py`, `ingestion_csv.py`, `advanced_memory.py`)

The `src/rag_retrieval.py` has:
- Its own `RAGRetriever` class
- Its own prompt templates
- Its own few-shot examples (hardcoded)
- Imports `llm, embeddings` directly (tight coupling)

**Impact**: Confusion about which system is active, duplicated maintenance.

---

### Issue #4: Hardcoded Few-Shot Examples Not From Knowledge Base

In `src/rag_retrieval.py` (lines 37-127), there are **hardcoded few-shot examples**:

```python
FEWSHOT_EXAMPLES = {
    "Python": [
        {"question": "What are list comprehensions...", "answer": "..."}
    ],
    ...
}
```

**Problem**: 
- These examples are NOT from our actual knowledge base (the CSVs)
- They may contradict or be inconsistent with the competency data
- This is the opposite of grounding - we're injecting unverified content

---

### Issue #5: Topic Filtering Logic Adds Noise to Retrieval

In `services/retrieval.py` (line 77):
```python
if topic:
    search_query = f"Data engineering {topic.value}: {query}"
```

**Problem**: We're **modifying the semantic query** by prepending "Data engineering Python:". This can actually hurt retrieval quality because:
- The embeddings were trained on natural language, not this artificial prefix
- We already have metadata filtering - adding topic to query is redundant

---

### Issue #6: Conversation History Not Actually Used in Main Flow

Looking at `app.py`, the `_handle_question()` function (lines 289-302):
```python
def _handle_question(intent: IntentAnalysis, chat_service: ChatService) -> None:
    response = chat_service.answer_question(intent.standalone_query, topic=topic)
    # NOTE: No conversation history passed!
```

The `ChatService.answer_question()` accepts a `conversation` parameter but it's **never passed** from the UI. The conversation state exists only in `st.session_state.messages` but isn't converted to `ConversationState` and passed through.

**Impact**: Despite building query transformation that uses history, the history is never actually sent.

---

### Issue #7: Unused Advanced Memory Module

`src/advanced_memory.py` defines a sophisticated `ConversationMemoryManager` with:
- Session persistence
- Concept extraction
- Cross-session memory

**Problem**: It's completely unused. Dead code that adds confusion.

---

### Issue #8: Similarity Score Interpretation Bug

In `src/rag_retrieval.py` (lines 222-229):
```python
filtered_docs = [
    (doc, score) for doc, score in docs_with_scores 
    if score >= SIMILARITY_THRESHOLD  # Filtering where score >= 0.3
]
```

But ChromaDB returns **distance** (lower is better), not similarity! The `services/retrieval.py` correctly converts this, but the old code in `src/` gets it backwards.

---

### Issue #9: Overly Complex Prompts Reduce Reliability

The prompts in `services/chat.py` are massive walls of text:
- `QA_WITH_CONTEXT_TEMPLATE` - 30+ lines
- `PRACTICE_TEMPLATE` - 50+ lines  
- `QUERY_TRANSFORMATION_TEMPLATE` - 40+ lines

**Problems**:
- LLMs follow long prompts less reliably
- Hard to debug which instruction caused issues
- Token waste on every call

---

### Issue #10: No Streaming = Poor UX

All LLM calls use `.invoke()` which waits for the complete response. For a chatbot, streaming provides much better UX as users see tokens appear in real-time.

---

## 📋 Recommended Fixes (Priority Order)

### P0 - Must Fix (AI Quality)

1. **Remove double query transformation** - Pick ONE place to transform queries
2. **Simplify to single RAG flow** - Remove intent classification, let RAG handle everything
3. **Delete or consolidate `src/` folder** - One implementation, not two
4. **Actually pass conversation history** - Connect the state to the service

### P1 - Should Fix (Quality & Reliability)

5. **Remove hardcoded few-shot examples** - Or pull them from actual KB
6. **Fix similarity/distance bug** in old code (or just delete it)
7. **Simplify prompts** - Shorter, more focused instructions
8. **Remove query modification in retrieval** - Trust metadata filtering

### P2 - Nice to Have (UX)

9. **Add streaming** - Better chatbot experience
10. **Remove unused code** - `advanced_memory.py`, unused intent handlers

---

## 🎯 Simplified Architecture Target

```
┌─────────────────┐
│   Streamlit UI  │
└────────┬────────┘
         │ user message + history
         ▼
┌─────────────────┐
│  ChatService    │  ← Single service, no intent routing
│  - answer()     │
└────────┬────────┘
         │ query
         ▼
┌─────────────────┐
│ RetrievalService│  ← Simple vector search with optional topic filter
└────────┬────────┘
         │ relevant docs
         ▼
┌─────────────────┐
│   LLM Generate  │  ← One prompt: system + context + history + question
└─────────────────┘
```

**One LLM call per user message** (except for edge cases like "generate practice questions" which might be 2).
