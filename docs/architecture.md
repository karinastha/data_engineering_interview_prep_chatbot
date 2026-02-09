# Architecture Document (Living Document)

> **Version**: 1.0.0  
> **Last Updated**: 2025-02-09  
> **Authors**: Staff Engineers (Refactoring Team)  
> **Status**: ✅ V1 Implementation Complete

---

## Table of Contents

1. [Design Philosophy](#design-philosophy)
2. [V1 vs V2 Scope](#v1-vs-v2-scope)
3. [Current State Analysis](#current-state-analysis)
4. [SOLID Violations](#solid-violations)
5. [Refactoring Decisions](#refactoring-decisions)
6. [V1 Implementation Plan](#v1-implementation-plan)
7. [Open Questions (V1)](#open-questions-v1)
8. [Decision Log](#decision-log)

---

## Design Philosophy

We follow **Clean Code** principles by Robert C. Martin (Uncle Bob):

1. **Single Responsibility Principle (SRP)**: A class should have one, and only one, reason to change.
2. **Open/Closed Principle (OCP)**: Software entities should be open for extension, but closed for modification.
3. **Liskov Substitution Principle (LSP)**: Objects should be replaceable with instances of their subtypes.
4. **Interface Segregation Principle (ISP)**: Many client-specific interfaces are better than one general-purpose interface.
5. **Dependency Inversion Principle (DIP)**: Depend on abstractions, not concretions.

Additional principles we value:
- **Meaningful Names**: Names should reveal intent
- **Small Functions**: Functions should do one thing
- **DRY (Don't Repeat Yourself)**: But not at the cost of clarity
- **YAGNI (You Aren't Gonna Need It)**: Don't over-engineer

---

## V1 vs V2 Scope

### V1 Scope (Current Phase) - Code Quality Refactoring

**Goal**: Improve code quality and maintainability without changing architecture patterns.

| Area | What We're Doing | What We're NOT Doing |
|------|------------------|----------------------|
| **Prompts** | Extract to external files | - |
| **Conversation History** | Keep current Streamlit session state | Migrate to LangChain memory |
| **Project Structure** | Split large files, improve organization | Full `src/` restructure |
| **SOLID Compliance** | Fix obvious violations | Over-abstract |
| **Testing** | None | Unit/integration tests |
| **Architecture Pattern** | Keep chains | Migrate to agents |

### V2 Scope (Future Phase) - Architecture Evolution

| Area | Consideration |
|------|---------------|
| **LangChain Memory** | Evaluate `InMemorySaver`, `SummarizationMiddleware` |
| **Agent Pattern** | Evaluate migration from chains to `create_agent` |
| **Testing** | Comprehensive unit and integration tests |
| **Project Structure** | Full `src/` layout if needed |
| **Persistence** | Evaluate PostgresSaver for conversation history |

### Decisions Made

| Question | Decision | Rationale |
|----------|----------|-----------|
| Prompt management | **Extract to external files** | Prompts will iterate even post-production |
| Agent vs Chain | **Keep chains for V1** | Current pattern works, evaluate in V2 |
| Testing | **None for V1** | Focus on refactoring, tests in V2 |
| Streamlit vs LangChain memory | **Keep Streamlit for V1** | Works today, evaluate LangChain in V2 |
| Conversation history | **Keep current implementation** | Evaluate LangChain migration in V2 |

---

## Current State Analysis

### What Works Well ✅

| Aspect | Observation |
|--------|-------------|
| **Separation of Services** | `chat.py`, `ingestion.py`, `retrieval.py` show good domain separation |
| **Configuration Centralization** | `config/settings.py` and `config/topics.py` consolidate config |
| **Type Hints** | Partial coverage, showing intent |
| **Docstrings** | Present on most public functions |
| **Dataclasses** | Using `@dataclass` for domain models |

### Architecture Diagram (Current)

```
┌─────────────────────────────────────────────────────────────────┐
│                    Streamlit Application                         │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                      app/ package                            │ │
│  │  ┌────────────┐  ┌────────────┐  ┌────────┐  ┌──────────┐  │ │
│  │  │ session.py │  │components.py│ │handlers │  │ main.py  │  │ │
│  │  │  (61 loc)  │  │ (153 loc)  │  │(69 loc) │  │ (50 loc) │  │ │
│  │  └────────────┘  └────────────┘  └────────┘  └──────────┘  │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                              │  run.py (entry point)             │
└──────────────────────────────┼───────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Services Layer                              │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    ChatService (orchestrator)               │ │
│  │                         (187 loc)                           │ │
│  └────────────────────────────────────────────────────────────┘ │
│            │                    │                    │           │
│            ▼                    ▼                    ▼           │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────┐ │
│  │ preprocessing  │  │  generation    │  │    history         │ │
│  │   (101 loc)    │  │   (169 loc)    │  │    (80 loc)        │ │
│  └────────────────┘  └────────────────┘  └────────────────────┘ │
│                              │                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              retrieval.py  │  ingestion.py                │   │
│  │               (231 loc)    │    (444 loc)                 │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                               │
┌──────────────────────────────┼───────────────────────────────────┐
│                    prompts/ package                              │
│  ┌────────────┐  ┌────────────────┐  ┌─────────────┐            │
│  │ system.py  │  │preprocessing.py│  │ templates.py│            │
│  │ (141 loc)  │  │   (68 loc)     │  │  (44 loc)   │            │
│  └────────────┘  └────────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Infrastructure                                │
│  ┌────────────────┐  ┌──────────────────┐  ┌────────────────┐  │
│  │  helper_cred   │  │    ChromaDB      │  │ Amazon Bedrock │  │
│  │  (LLM/Embed)   │  │  (vectorstore)   │  │  (Nova Lite)   │  │
│  └────────────────┘  └──────────────────┘  └────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## SOLID Violations

### 1. Single Responsibility Principle (SRP) Violations

#### `app.py` (344 lines) - Multiple Responsibilities
```
Current responsibilities:
├── Session state management
├── UI rendering (header, sidebar, welcome)
├── Mermaid diagram rendering
├── Source citation display
├── Message handling (streaming and non-streaming)
├── Chat service initialization
└── Main application loop
```

**Impact**: Any change to UI, state management, or message handling requires modifying this file.

#### `ChatService` (602 lines) - Too Many Responsibilities
```
Current responsibilities:
├── Query preprocessing (LLM call #1)
├── Topic extraction
├── History formatting (multiple formats)
├── Answer generation (LLM call #2)
├── Streaming response handling
├── Practice question generation
├── Prompt template management (200+ line prompts inline)
└── Response caching (_last_response)
```

**Impact**: Changes to prompts, history format, or generation logic all require modifying this class.

---

### 2. Open/Closed Principle (OCP) Violations

#### Hardcoded Prompt Templates in `chat.py`
```python
# Current: Prompts are hardcoded strings inside the class
SYSTEM_PROMPT = """You are a Data Engineering Interview Coach..."""  # 200+ lines
```

**Problem**: To change prompt behavior, we must modify `chat.py`.

**Solution Options**:
| Option | Tradeoff |
|--------|----------|
| A. External files (`prompts/*.txt`) | + Easy to edit, - Requires file I/O, - Loses IDE autocomplete |
| B. Prompt registry class | + Type-safe, + Versioning, - More abstraction |
| C. LangChain PromptTemplate with variables | + Native LangChain, - Learning curve |

**Decision**: TBD - Need to evaluate based on iteration frequency of prompts.

---

### 3. Dependency Inversion Principle (DIP) Violations

#### Direct Instantiation of Dependencies

```python
# Current: ChatService creates its own prompt templates
class ChatService:
    def __init__(self, llm, retrieval_service):
        self._qa_prompt = ChatPromptTemplate.from_messages([...])  # Hardcoded!
```

**Problem**: Cannot swap prompt templates for testing or A/B testing.

#### Global Singletons in `helper_cred.py`

```python
# Current: Module-level singletons with lazy loading
_llm: Optional[BaseChatModel] = None
_embeddings: Optional[Embeddings] = None
```

**Problem**: 
- Tight coupling to specific implementations
- Difficult to test (need to reset globals)
- Hidden dependencies

**Solution Options**:
| Option | Tradeoff |
|--------|----------|
| A. Dependency injection container | + Clean, - Adds complexity, - Learning curve |
| B. Factory pattern | + Flexible, - Still some coupling |
| C. Constructor injection (simple) | + Explicit, + Testable, - Manual wiring |

**Decision**: TBD - Lean toward (C) for simplicity per YAGNI.

---

### 4. Liskov Substitution Principle (LSP)

Currently, we don't have many inheritance hierarchies, so LSP violations are minimal. However, this is worth watching as we add abstractions.

---

### 5. Interface Segregation Principle (ISP)

#### `ChatService` Has Too Broad an Interface

```python
class ChatService:
    def answer(...)          # Synchronous answer
    def answer_stream(...)   # Streaming answer  
    def get_last_response()  # State access
    def generate_practice_questions(...)  # Different concern
```

**Problem**: Clients that only need streaming must depend on the entire class.

**Solution Options**:
| Option | Tradeoff |
|--------|----------|
| A. Split into `ChatService` + `PracticeQuestionService` | + Clear separation, - More classes |
| B. Protocol/Interface for each concern | + Composition, - Abstract overhead |
| C. Keep as-is, document clearly | + Simple, - Grows over time |

---

## Refactoring Decisions

### Decision 1: Conversation History Management

#### Current Implementation
```python
# app.py - Manual list management
if "messages" not in st.session_state:
    st.session_state.messages = []

def add_message(role: str, content: str, sources: list = None):
    message = {"role": role, "content": content}
    st.session_state.messages.append(message)
```

```python
# chat.py - Manual history formatting
def _format_history_for_preprocessing(self, messages: List[Dict], max_messages: int = 6):
    recent = messages[-max_messages:]
    # ... manual truncation logic
```

#### Problems
1. Reinventing the wheel - LangChain has built-in memory management
2. Stringly-typed (`List[Dict]` instead of typed messages)
3. No token-aware truncation
4. No summarization for long conversations
5. Scattered across `app.py` and `chat.py`

#### LangChain Options (from docs research)

| Option | Description | Tradeoff |
|--------|-------------|----------|
| **InMemorySaver** | Simple in-memory checkpointer | + Simple, - Lost on restart |
| **PostgresSaver** | Persistent DB storage | + Durable, - Requires DB |
| **SummarizationMiddleware** | Auto-summarize when token limit hit | + Smart truncation, - Extra LLM calls |
| **Message trimming middleware** | Keep last N messages | + Predictable, - May lose context |
| **LangChain Messages** | `HumanMessage`, `AIMessage`, `SystemMessage` | + Type-safe, + Native |

#### Recommendation

Use **LangChain's native message types** + **InMemorySaver** for V1:

```python
# Proposed: Use LangChain message types
from langchain.messages import HumanMessage, AIMessage, SystemMessage

# Instead of: {"role": "user", "content": "..."}
# Use: HumanMessage(content="...")
```

**Rationale**:
1. Type-safe - IDE autocomplete, runtime validation
2. Compatible with LangChain's memory management
3. Enables future migration to `SummarizationMiddleware` or `InMemorySaver`
4. No custom code to maintain

**For V2**: Evaluate `SummarizationMiddleware` for long conversations.

---

### Decision 2: Project Structure

#### Current
```
├── app.py              # 344 lines, mixed concerns
├── main.py             # CLI entry point
├── schemas.py          # Domain models
├── config/
├── services/
├── utils/
└── tests/              # Empty
```

#### Options

| Option | Structure | Tradeoff |
|--------|-----------|----------|
| A. Keep flat, split files | `app/components/*.py` | + Minimal change, - Still messy |
| B. Full `src/` layout | `src/app/`, `src/core/`, `src/services/` | + Clean, - Big refactor |
| C. Domain-driven | `src/chat/`, `src/retrieval/`, `src/ingestion/` | + DDD, - Maybe overkill |

**Decision**: TBD - Discuss with team. Lean toward (A) for V1, (B) for V2.

---

### Decision 3: Prompt Management

#### Current
200+ line prompts hardcoded in `chat.py`.

#### Options

| Option | Pros | Cons |
|--------|------|------|
| A. External `.txt` files | Easy editing, non-dev friendly | File I/O, lose type safety |
| B. YAML/JSON config | Structured, versionable | Parsing overhead |
| C. Python constants module | Type-safe, IDE support | Still code changes |
| D. LangChain Hub | Community sharing, versioning | External dependency |

**Decision**: ✅ **Option A - External files** 

**Rationale**: Prompts will be iterated upon even after going to production. External files allow:
- Non-developers to edit prompts
- Version control visibility (clear diffs)
- No code deployment for prompt changes
- Easy A/B testing by swapping files

---

## V1 Implementation Plan

### Task 1: Extract Prompts to External Files

**Current State**: 
- `SYSTEM_PROMPT` (~200 lines) in `chat.py`
- `PREPROCESSING_PROMPT` in `chat.py`
- `QA_PROMPT_TEMPLATE` in `chat.py`
- `PRACTICE_QUESTIONS_PROMPT` in `chat.py`

**Proposed Structure**:
```
prompts/
├── system.txt              # Main system prompt
├── preprocessing.txt       # Query transformation prompt
├── qa_template.txt         # Q&A generation template
└── practice_questions.txt  # Practice question generation
```

**Questions to resolve**:
1. Should prompts have version suffixes (e.g., `system_v1.txt`)?
2. How to handle prompt variables (e.g., `{context}`, `{history}`)?
3. Should we create a `PromptLoader` utility or keep it simple with `Path.read_text()`?

---

### Task 2: Split `app.py` (344 lines)

**Current Responsibilities**:
```
app.py
├── Session state management (init_session_state, add_message, get_history)
├── UI components (render_header, render_sidebar, render_welcome)
├── Mermaid rendering (render_content_with_mermaid)
├── Source display (render_sources_used)
├── Message handling (handle_message_streaming, handle_message)
└── Main loop (main)
```

**Proposed Split**:
```
app/
├── __init__.py
├── main.py                 # Entry point, main() function
├── session.py              # Session state management
├── components/
│   ├── __init__.py
│   ├── header.py           # render_header
│   ├── sidebar.py          # render_sidebar
│   ├── chat.py             # render_chat_messages, render_content_with_mermaid
│   └── sources.py          # render_sources_used
└── handlers/
    ├── __init__.py
    └── message.py          # handle_message, handle_message_streaming
```

**Questions to resolve**:
1. Is this granularity right, or is it over-splitting?
2. Should `app/` be at root or inside a `src/` folder?
3. How to handle the Streamlit entry point (`streamlit run app.py` vs `streamlit run app/main.py`)?

---

### Task 3: Split `ChatService` (602 lines)

**Current Responsibilities**:
```
ChatService
├── Prompts (SYSTEM_PROMPT, PREPROCESSING_PROMPT, etc.)
├── Query preprocessing (_preprocess_query)
├── History formatting (_format_history_for_preprocessing, _format_history_for_generation)
├── Answer generation (answer, answer_stream)
├── Practice questions (generate_practice_questions)
└── State (_last_response)
```

**Option A - Extract Prompts Only** (minimal change):
```
services/
├── chat.py                 # ChatService (now ~400 lines)
└── prompts/                # Moved to prompts/ at root
```

**Option B - Split by Concern**:
```
services/
├── chat.py                 # ChatService - orchestration only
├── preprocessing.py        # QueryPreprocessor
├── generation.py           # ResponseGenerator
└── history.py              # HistoryFormatter
```

**Questions to resolve**:
1. Option A or B? A is simpler, B is more SOLID.
2. If B, how do these classes interact? Composition in ChatService?

---

### Task 4: Fix DIP Violations (Optional for V1)

**Current**: Global singletons in `helper_cred.py`

**Options**:
1. **Keep as-is for V1** - Works, refactor in V2
2. **Simple constructor injection** - Pass dependencies explicitly

**Recommendation**: Keep as-is for V1 unless it blocks other work.

---

## Open Questions (V1) - ✅ RESOLVED

All questions resolved. Final decisions:

| Question | Decision | Rationale |
|----------|----------|-----------|
| **Q1: Prompt Format** | Python module (`.py`) with string constants or LangChain `PromptTemplate` | Type-safe, IDE support, no YAML overhead |
| **Q2: App Structure** | Minimal split with handlers separated | `components.py` (pure rendering) + `handlers.py` (orchestration) |
| **Q3: ChatService** | Split by concern | `QueryPreprocessor`, `ResponseGenerator`, `HistoryFormatter` |
| **Q4: Directory Layout** | Flat | `prompts/`, `app/`, `services/` at root |

---

## V1 Final Structure

### Target Directory Layout
```
├── app/
│   ├── __init__.py
│   ├── main.py              # Entry point, main() function
│   ├── session.py           # Session state management
│   ├── components.py        # All render_* functions (pure UI)
│   └── handlers.py          # handle_message_* (orchestration with side effects)
├── prompts/
│   ├── __init__.py
│   ├── system.py            # SYSTEM_PROMPT
│   ├── preprocessing.py     # PREPROCESSING_PROMPT  
│   ├── templates.py         # QA_PROMPT_TEMPLATE, PRACTICE_QUESTIONS_PROMPT
│   └── loader.py            # Optional: PromptLoader utility
├── services/
│   ├── __init__.py
│   ├── chat.py              # ChatService (orchestrator, ~150 lines)
│   ├── preprocessing.py     # QueryPreprocessor
│   ├── generation.py        # ResponseGenerator
│   ├── history.py           # HistoryFormatter
│   ├── retrieval.py         # RetrievalService (unchanged)
│   └── ingestion.py         # IngestionService (unchanged)
├── config/                   # Unchanged
├── utils/                    # Unchanged
├── schemas.py               # Unchanged
├── main.py                  # CLI entry (unchanged)
└── run.py                   # New: simple entry point for `streamlit run run.py`
```

### Streamlit Entry Point
Create `run.py` at root for clean invocation:
```python
# run.py
from app.main import main
main()
```
Usage: `streamlit run run.py`

---

## Decision Log

| Date | Decision | Rationale | Status |
|------|----------|-----------|--------|
| 2026-02-09 | Document created | Align on refactoring approach | ✅ |
| 2026-02-09 | Follow Clean Code / SOLID | Team design philosophy | ✅ |
| 2026-02-09 | Extract prompts to external files | Prompts iterate post-production | ✅ |
| 2026-02-09 | Keep chains, no agent migration | Current pattern works for V1 | ✅ |
| 2026-02-09 | No tests in V1 | Focus on refactoring, tests in V2 | ✅ |
| 2026-02-09 | Keep Streamlit session state | Works today, evaluate LangChain in V2 | ✅ |
| 2026-02-09 | Keep current conversation history | Evaluate LangChain migration in V2 | ✅ |
| 2026-02-09 | Q1: Python module for prompts | Type-safe, IDE support | ✅ |
| 2026-02-09 | Q2: Minimal split + separate handlers | Pure rendering vs orchestration | ✅ |
| 2026-02-09 | Q3: Split ChatService by concern | SRP compliance | ✅ |
| 2026-02-09 | Q4: Flat directory layout | Simple, no `src/` overhead | ✅ |

---

## Next Steps

1. [x] Review this document together
2. [x] Decide on conversation memory approach → Keep current for V1
3. [x] Answer V1 open questions (Q1-Q4)
4. [x] **V1 Implementation Complete**
   - [x] Task 1: Extract prompts to `prompts/` module (system.py, preprocessing.py, templates.py)
   - [x] Task 2: Split `app.py` → `app/` package (session.py, components.py, handlers.py, main.py)
   - [x] Task 3: Split `ChatService` by concern (preprocessing.py, generation.py, history.py)
   - [x] Task 4: Create `run.py` entry point
5. [ ] V2 planning (tests, LangChain memory evaluation)

### V1 Implementation Summary

| Before | After | Lines |
|--------|-------|-------|
| `services/chat.py` (602 lines) | Split into 4 focused modules | chat.py: 187, preprocessing.py: 101, generation.py: 169, history.py: 80 |
| `app.py` (344 lines) | Split into `app/` package | session.py: 61, components.py: 153, handlers.py: 69, main.py: 50 |
| Prompts inline in chat.py | `prompts/` package | system.py: 141, preprocessing.py: 68, templates.py: 44 |
| No clean entry point | `run.py` | 12 lines |

**Total reduction in largest files**:
- `chat.py`: 602 → 187 lines (69% reduction)
- Original `app.py` preserved for backward compatibility, new `app/` package created

---

## V2 Backlog (For Future Reference)

Items deferred to V2:
- [ ] Evaluate LangChain `InMemorySaver` / `SummarizationMiddleware`
- [ ] Evaluate agent pattern migration
- [ ] Comprehensive test suite (unit + integration)
- [ ] Consider `src/` layout restructure
- [ ] Performance baseline metrics
- [ ] Swap `List[Dict]` for LangChain message types

---

*This is a living document. Update as decisions are made.*
