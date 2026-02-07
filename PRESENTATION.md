# Data Engineering Interview Prep Chatbot
## RAG-Powered Conversational AI for Interview Preparation

**Presented to: Lead AI Engineers**  
**Date: February 2026**  
**Team: AI Engineering**

---

# 📋 Agenda

1. Problem Statement
2. Proposed Solution
3. System Architecture
4. Technology Stack
5. Key Design Decisions
6. Challenges & Solutions
7. Results & Improvements
8. Future Roadmap

---

# 🎯 Problem Statement

## The Challenge

**Leapfrog needs to prepare Data Engineering candidates for interviews**, but:

| Pain Point | Impact |
|------------|--------|
| Inconsistent interview prep | Candidates miss key competencies |
| No structured competency framework | Interviewers assess differently |
| Generic prep materials | Not aligned with Leapfrog's expectations |
| Time-consuming 1:1 mentoring | Doesn't scale |

## Leapfrog Competency Framework

Our hiring evaluates candidates across **3 levels**:

```
┌─────────────────────────────────────────────────────────┐
│  🟢 MUST HAVE      │ Entry-level fundamentals           │
│  🟡 DESIRABLE      │ Practical application skills       │
│  🔴 ADVANCED/BEST  │ Senior-level expertise             │
└─────────────────────────────────────────────────────────┘
```

**Goal**: Build an AI assistant that helps candidates prepare using this framework.

---

# 💡 Proposed Solution

## RAG-Powered Interview Prep Chatbot

A conversational AI that:

✅ **Answers conceptual questions** using curated competency data  
✅ **Generates practice questions** at all difficulty levels  
✅ **Maintains conversation context** for natural multi-turn dialogue  
✅ **Filters by topic** (Python, SQL, Database, ETL) for focused prep  

## Core Capabilities

| Feature | Description |
|---------|-------------|
| **Knowledge-Grounded Answers** | Responses based on Leapfrog's competency framework |
| **Multi-Level Practice** | Basic → Intermediate → Advanced questions |
| **Topic Filtering** | Metadata-based retrieval for precise results |
| **Conversation Memory** | Resolves references like "more on that" |

---

# 🏗️ System Architecture

## High-Level Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                            │
│                      (Streamlit Chat UI)                          │
└─────────────────────────────┬────────────────────────────────────┘
                              │ User Message + History
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                    LLM CALL #1: PREPROCESSING                     │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ Input: User message + Recent user messages (last 5)        │  │
│  │ Output: {standalone_query, topic}                          │  │
│  │                                                             │  │
│  │ • Query Transformation: "more on that" → "more SQL joins"  │  │
│  │ • Topic Extraction: "lakehouse" → ETL (not Database!)      │  │
│  └────────────────────────────────────────────────────────────┘  │
└─────────────────────────────┬────────────────────────────────────┘
                              │ Standalone Query + Topic
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                      VECTOR RETRIEVAL                             │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ ChromaDB with Cosine Similarity                            │  │
│  │ • Semantic search on standalone query                      │  │
│  │ • Metadata filter: {"topic": "ETL"}                        │  │
│  │ • Similarity threshold: 0.3                                │  │
│  └────────────────────────────────────────────────────────────┘  │
└─────────────────────────────┬────────────────────────────────────┘
                              │ Relevant Documents (top-k)
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                  LLM CALL #2: ANSWER GENERATION                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ Input: System prompt + Context + History + Question        │  │
│  │ Output: Formatted response                                 │  │
│  │                                                             │  │
│  │ Format Selection (auto):                                   │  │
│  │ • Conceptual → Definition + Use Case + Example             │  │
│  │ • Practice → Basic + Intermediate + Advanced               │  │
│  └────────────────────────────────────────────────────────────┘  │
└─────────────────────────────┬────────────────────────────────────┘
                              │ Generated Response
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                            │
│                    (Display Response + History)                   │
└──────────────────────────────────────────────────────────────────┘
```

---

# 🏗️ Data Pipeline Architecture

## Document Ingestion Flow

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   CSV Files     │      │   Document      │      │   ChromaDB      │
│                 │ ──▶  │   Processing    │ ──▶  │   Vector Store  │
│ • Python.csv    │      │                 │      │                 │
│ • SQL.csv       │      │ • Row → Doc     │      │ • Embeddings    │
│ • Database.csv  │      │ • Metadata      │      │ • Metadata      │
│ • ETL.csv       │      │ • Formatting    │      │ • Cosine Index  │
└─────────────────┘      └─────────────────┘      └─────────────────┘
```

## Document Structure

Each CSV row becomes a document with:

```python
{
    "page_content": """
        Topic: Python
        Subtopic: List Comprehensions
        
        Definition (Foundational):
        Writes clean, readable Python code...
        
        Intermediate:
        Uses list/dict comprehensions for concise...
        
        Advanced:
        Writes generator expressions for memory-efficient...
    """,
    "metadata": {
        "topic": "Python",
        "subtopic": "Control flow",
        "source": "DE docs - Python.csv",
        "has_all_levels": True
    }
}
```

---

# 🛠️ Technology Stack

## Core Technologies

| Component | Technology | Why? |
|-----------|------------|------|
| **LLM** | Amazon Nova Lite (Bedrock) | Cost-effective, fast, good instruction following |
| **Embeddings** | sentence-transformers/all-MiniLM-L6-v2 | Lightweight, good quality, runs locally |
| **Vector Store** | ChromaDB | Simple, persistent, supports metadata filtering |
| **Orchestration** | LangChain | Structured outputs, prompt management, composability |
| **UI** | Streamlit | Rapid prototyping, built-in chat components |
| **Language** | Python 3.11+ | Team expertise, ecosystem |

## Key Libraries

```python
# LLM & Embeddings
langchain-aws          # Amazon Bedrock integration
langchain-huggingface  # Local embeddings
langchain-chroma       # Vector store

# Data Processing
pandas                 # CSV processing
pydantic              # Schema validation, structured outputs

# Application
streamlit             # Web UI
python-dotenv         # Configuration
```

---

# 🧠 Key Design Decisions

## Decision 1: Single Preprocessing Call

**Problem**: Original design had 3 LLM calls per request
- Intent classification (app.py)
- Query transformation (chat.py)  
- Answer generation

**Solution**: Combined into 2 calls
- Preprocessing: Query transform + Topic extraction
- Generation: Answer with context

**Impact**: 33% reduction in LLM calls, lower latency, lower cost

---

## Decision 2: Topic-Aware Classification

**Problem**: LLM classified "data warehouse vs lakehouse" as Database

**Root Cause**: LLM used semantic similarity, not our KB structure

**Solution**: Explicit topic boundaries in prompt

```
TOPIC DEFINITIONS:
- Database: RDBMS, ACID, transactions, indexing, normalization
- ETL: Data warehousing, OLAP, dimensional modeling, data lakes, lakehouses

CLASSIFICATION RULES:
- "data warehouse", "lakehouse", "OLAP" → ETL
- "ACID", "transactions", "normalization" → Database
```

**Impact**: Correct topic routing for edge cases

---

## Decision 3: User-Only History for Preprocessing

**Problem**: Full conversation history wasted tokens

```
# Before: 1000+ tokens in preprocessing
User: "explain joins"
Assistant: "[500 word explanation...]"
User: "more examples"
```

**Solution**: Only user messages, last 5

```
# After: ~100 tokens in preprocessing
1. "more examples"
2. "explain joins"
```

**Impact**: ~80% token reduction in preprocessing

---

## Decision 4: Cosine Similarity in ChromaDB

**Problem**: Default L2 distance gave unintuitive scores

```
# L2 Distance (default)
distance=0.98 → Is this good or bad? 🤷
```

**Solution**: Configure ChromaDB for cosine distance

```python
Chroma.from_documents(
    collection_metadata={"hnsw:space": "cosine"}
)
```

**Impact**: Intuitive similarity scores (0.7 = 70% similar)

---

# 🚧 Challenges & Solutions

## Challenge 1: Retrieval Not Working

**Symptom**: "No results above threshold" for every query

**Investigation**:
```python
# Debug showed distance scores ~0.98
# Similarity = 1 - 0.98 = 0.02 (below 0.3 threshold!)
```

**Root Cause**: ChromaDB defaulted to L2 distance, code assumed cosine

**Solution**: 
1. Recreate vector store with `hnsw:space: cosine`
2. Update distance-to-similarity conversion

---

## Challenge 2: Inconsistent Answer Formats

**Symptom**: Same type of question got different response structures

**Root Cause**: No explicit format guidance in system prompt

**Solution**: Added format templates with auto-selection

```
For conceptual questions:
📚 Definition → 💡 Use Case → 🚀 Example

For practice requests:
🟢 Basic → 🟡 Intermediate → 🔴 Advanced
```

---

## Challenge 3: Context Loss in Multi-Turn

**Symptom**: "more on that" didn't know what "that" was

**Root Cause**: 
1. Conversation history not passed to preprocessing
2. History included too much noise (assistant responses)

**Solution**:
1. Pass user message history (last 5) to preprocessing
2. Clear instructions: "CURRENT message is priority"
3. Examples showing reference resolution

---

## Challenge 4: Topic Misclassification

**Symptom**: "lakehouse" classified as Database instead of ETL

**Root Cause**: LLM didn't know our KB boundaries

**Solution**: Explicit classification rules in prompt

```
CLASSIFICATION RULES:
- "data warehouse", "lakehouse" → ETL (not Database!)
- "ACID", "transactions" → Database
```

---

# 📊 Results & Improvements

## Before vs After (v0 → v1)

| Metric | v0 (Original) | v1 (Improved) |
|--------|---------------|---------------|
| LLM Calls per Request | 3 | 2 |
| Preprocessing Tokens | ~1000 | ~200 |
| Topic Classification Accuracy | ~70% | ~95% |
| Response Format Consistency | Random | Structured |
| Multi-turn Context | Broken | Working |

## Architecture Simplification

```
BEFORE (Original):
User → Intent Classification → Handler Routing → Query Transform → Retrieve → Generate
       [LLM #1]                                  [LLM #2]                    [LLM #3]

AFTER (v1):
User → Preprocess (Query + Topic) → Retrieve → Generate
       [LLM #1]                                [LLM #2]
```

---

# 🔮 Future Roadmap

## Short-Term (Next Sprint)

| Enhancement | Description |
|-------------|-------------|
| **Streaming Responses** | Show tokens as they generate for better UX |
| **Citation Links** | Show which source doc each answer came from |
| **Confidence Scores** | Display retrieval confidence to user |

## Medium-Term

| Enhancement | Description |
|-------------|-------------|
| **Evaluation Pipeline** | Automated testing with golden Q&A pairs |
| **Hybrid Search** | Combine semantic + keyword search |
| **User Feedback Loop** | Thumbs up/down to improve over time |

## Long-Term

| Enhancement | Description |
|-------------|-------------|
| **Fine-Tuned Model** | Train on Leapfrog interview data |
| **Multi-Modal** | Support code execution, diagrams |
| **Interview Simulation** | Full mock interview mode |

---

# 📚 Lessons Learned

## Technical Insights

1. **Default configs matter**: ChromaDB's L2 default caused hours of debugging
2. **Prompt > Code**: Topic classification fixed with prompt engineering, not code
3. **Less is more**: Reducing history tokens improved quality AND cost
4. **Structure > Free-form**: Pydantic structured outputs are reliable

## Process Insights

1. **Error analysis first**: User testing revealed issues we couldn't find in code
2. **Align before coding**: V1 planning doc saved implementation time
3. **Keep it simple**: Removed intent classification entirely - not needed

---

# 🙏 Summary

## What We Built

A **RAG-powered conversational AI** that helps Data Engineers prepare for interviews using Leapfrog's competency framework.

## Key Achievements

✅ **2 LLM calls** per request (down from 3)  
✅ **~80% token reduction** in preprocessing  
✅ **Accurate topic classification** with explicit rules  
✅ **Consistent response formats** for different question types  
✅ **Working multi-turn conversations** with context resolution  

## Architecture Principles

🎯 **Simplicity**: Removed unnecessary intent classification  
🎯 **Efficiency**: User-only history, single preprocessing call  
🎯 **Reliability**: Structured outputs, explicit prompt rules  
🎯 **Maintainability**: Clear separation of concerns  

---

# ❓ Q&A

## Discussion Points

1. Should we add explicit question type classification, or is auto-detection sufficient?
2. What evaluation metrics should we track?
3. How do we handle knowledge base updates?

---

# 📎 Appendix

## Project Structure

```
data_engineering_interview_prep_chatbot/
├── app_v0.py              # Streamlit UI (simplified)
├── services/
│   ├── chat_v0.py         # Chat service with preprocessing
│   ├── retrieval.py       # Vector search with topic filtering
│   └── ingestion.py       # CSV → ChromaDB pipeline
├── core/
│   └── models.py          # Domain models (Topic, RAGResponse)
├── config/
│   └── settings.py        # Centralized configuration
├── data/
│   ├── raw_docs/          # Source CSVs
│   └── vector_db/         # ChromaDB persistence
└── docs/
    ├── WHAT TO DO.MD      # Initial problem statement
    └── V1_IMPROVEMENTS.md # V1 design decisions
```

## Key Configuration

```python
# RAG Settings
TOP_K = 4                    # Documents to retrieve
SIMILARITY_THRESHOLD = 0.3   # Minimum relevance
MAX_HISTORY_MESSAGES = 5     # User messages for context

# LLM Settings
MODEL = "amazon.nova-lite-v1:0"
TEMPERATURE = 0.5
MAX_TOKENS = 1500
```

---

*Thank you!*
