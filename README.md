# 💼 Data Engineering Interview Prep Chatbot

A conversational RAG-based (Retrieval-Augmented Generation) chatbot powered by **LangChain** and **Amazon Nova Lite** to help you prepare for Data Engineering interviews. The chatbot provides structured answers with definitions, use cases, and real-world examples based on comprehensive competency frameworks.

## 🌟 Features

- **🎯 Conversational Flow**: Natural conversation flow asking for practice questions → topic selection → generating content
- **📚 Structured Learning**: Answers formatted with:
  - **📚 Definition** - Clear explanation of concepts
  - **💡 Use Case** - Practical applications
  - **🚀 Real-World Example** - Industry examples and best practices
- **🔍 RAG Architecture**: ChromaDB vector store + LangChain retrieval for accurate, context-aware answers
- **⚡ Amazon Nova Lite**: Fast, cost-effective LLM for interview prep
- **🗄️ Vector Search**: Amazon Titan Embeddings for semantic search
- **💬 Streamlit Interface**: Beautiful, interactive chat interface
- **📊 Topic Coverage**: Python, SQL, Database, ETL competencies from CSV documentation

## 📋 Prerequisites

- Python 3.10+
- AWS Account with Bedrock access (Nova Lite & Titan Embeddings)
- AWS credentials configured
- UV package manager (recommended) or pip

## 🚀 Quick Start

### 1. Clone and Setup

```bash
cd data_engineering_interview_prep_chatbot
```

### 2. Install Dependencies

Using UV (recommended):
```bash
uv sync
```

Or using pip:
```bash
pip install -r requirements.txt
```

### 3. Configure AWS Credentials

Create a `.env` file in the project root:

```env
# AWS Bedrock Configuration
AWS_REGION=us-east-1
aws_access_key_id=YOUR_AWS_ACCESS_KEY_ID
aws_secret_access_key=YOUR_AWS_SECRET_ACCESS_KEY
# aws_session_token=YOUR_SESSION_TOKEN  # Optional: if using temporary credentials
```

**Note**: Copy `.env.example` to `.env` and fill in your credentials.

### 4. Initialize Vector Store (First Time Only)

This creates the ChromaDB vector database from CSV documentation:

```bash
python src/ingestion_csv.py
```

Expected output:
```
======================================================================
  DATA ENGINEERING INTERVIEW PREP - VECTOR STORE SETUP
======================================================================

🆕 Creating new vector store...
📄 Loading DE docs - Python.csv...
📄 Loading DE docs - SQL.csv...
📄 Loading DE docs - Database.csv...
✅ Loaded 150+ documents from CSV files
🔄 Creating vector store with 150+ documents...
✅ Vector store created and persisted to data/vector_db

======================================================================
  SETUP COMPLETE!
======================================================================
```

### 5. Run the Chatbot

**Streamlit Web App** (Recommended):
```bash
streamlit run app.py
```

Then open your browser to `http://localhost:8501`

## 📖 Usage Guide

### Conversation Flow

The chatbot follows a natural conversation flow:

1. **Welcome**: Bot introduces itself and available topics
2. **Request Practice**: User says "give me practice questions" or similar
3. **Topic Selection**: User chooses: Python, SQL, Database, or ETL
4. **Generate Content**: Bot retrieves relevant competencies and generates:
   - Interview practice questions (Entry/Mid/Advanced levels)
   - Key competencies with Definition, Use Case, and Real-World Examples
5. **Continue Learning**: Ask follow-up questions or explore more topics

### Example Interaction

```
👋 Welcome! I'm here to help you prepare for Data Engineering interviews.

I can help you practice with interview questions and learn key competencies in:
- 🐍 Python - Data engineering with Python
- 💾 SQL - Queries and database operations
- 🗄️ Database - RDBMS design and optimization
- 🔄 ETL - Data pipelines and transformations

How would you like to get started?

---

User: give me practice questions for the interview

AI: Which topic would you like to practice?

Please select ONE topic to get started:
  - 🐍 Python
  - 💾 SQL
  - 🗄️ Database
  - 🔄 ETL

---

User: Python

AI: [Generates comprehensive practice content including:]

📚 Interview Practice Questions for Python

Entry-Level Questions (Must Have):
1. Explain the difference between lists, tuples, and dictionaries...
2. How do you handle errors in Python?...

Mid-Level Questions (Desirable):
3. What are decorators and when would you use them?...

Advanced Questions (Best Practice):
4. How would you optimize a data pipeline for large-scale processing?...

Key Competencies:

**Topic: List Comprehensions**

📚 Definition:
List comprehensions provide a concise way to create lists...

💡 Use Case:
Used in ETL pipelines for data transformation...

🚀 Real-World Example:
In a production data pipeline, filtering millions of records...

---

💡 Want to dive deeper? Ask specific questions about Python,
   or say 'more topics' to explore other areas!

---

User: Tell me more about decorators

AI: [Generates detailed answer with definition, use case, example]

---

User: great give me more topics

AI: [Returns to topic selection]
```
What are list comprehensions?

Definition:
List comprehensions are concise, Pythonic syntax for creating new lists by applying 
an expression to each item in an iterable, optionally filtering items with a condition.

Use Case:
Used extensively in data engineering for transforming, filtering, and processing data 
in ETL pipelines, especially when working with in-memory datasets before loading into 
databases or data warehouses.

Real-World Example:
In a data pipeline, you might extract user IDs from a list of user dictionaries while 
filtering out inactive users:
active_user_ids = [user['id'] for user in users if user['status'] == 'active']

Code Example:
# Transform and filter in one line
# Extract email domains from valid email addresses
emails = ['john@gmail.com', 'invalid', 'jane@yahoo.com', 'bob@']
domains = [email.split('@')[1] for email in emails if '@' in email and '.' in email]
# Result: ['gmail.com', 'yahoo.com']

Key Interview Notes:
- More readable and faster than equivalent for-loops
- Can include if conditions for filtering
- Can be nested but avoid deep nesting for readability
```

## 🏗️ Architecture

### Project Structure

```
data_engineering_interview_prep_chatbot/
├── app.py                   # Streamlit chatbot application
├── data/
│   ├── raw_docs/            # Source CSV files
│   │   ├── DE docs - Python.csv
│   │   ├── DE docs - SQL.csv
│   │   ├── DE docs - Database.csv
│   │   └── DE docs - ETL.csv
│   └── vector_db/           # ChromaDB vector store (created after ingestion)
│       └── chroma.sqlite3
├── src/
│   ├── __init__.py
│   ├── ingestion_csv.py     # CSV document loading and vector store creation
│   └── rag_retrieval.py     # RAG retrieval and answer generation
├── utils/
│   └── helper_cred.py       # AWS Bedrock LLM & embeddings configuration
├── .env                     # Environment variables (create from .env.example)
├── .env.example             # Environment template
├── pyproject.toml           # UV project configuration
├── requirements.txt         # Python dependencies
└── README.md
```

### RAG Pipeline Flow

```
User Input: "give me practice questions"
     ↓
Chatbot: "Which topic?"
     ↓
User: "Python"
     ↓
Vector Store Retrieval (ChromaDB)
  - Filters by topic metadata
  - Retrieves top 10 relevant documents
     ↓
Retrieved Context + User Query + Instructions
     ↓
Amazon Nova Lite LLM
     ↓
Structured Response:
  - Practice questions (Entry/Mid/Advanced)
  - Competency breakdown:
    * 📚 Definition
    * 💡 Use Case
    * 🚀 Real-World Example
```

### Conversation State Management

The chatbot maintains three conversation stages:
1. **greeting** - Initial welcome
2. **topic_selection** - User selects topic
3. **practicing** - Active Q&A session

## 🔧 Configuration

### Model Information

The chatbot uses AWS Bedrock services:
- **LLM**: Amazon Nova Lite v1:0 (`amazon.nova-lite-v1:0`)
  - Temperature: 0.5
  - Max tokens: 1000
- **Embeddings**: Amazon Titan Embed Text v1 (`amazon.titan-embed-text-v1`)
- **Vector Store**: ChromaDB with persistent storage
- **Region**: us-east-1 (configurable via .env)

All configuration is in [utils/helper_cred.py](utils/helper_cred.py)

### Customization Options

**Change LLM Parameters** - Edit [utils/helper_cred.py](utils/helper_cred.py):
```python
llm = ChatBedrock(
    model_id="amazon.nova-lite-v1:0",
    model_kwargs={
        "temperature": 0.7,      # Adjust creativity (0-1)
        "max_new_tokens": 2000   # Adjust response length
    }
)
```

**Modify Retrieval** - Edit [src/rag_retrieval.py](src/rag_retrieval.py):
```python
self.retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 10}  # Number of documents to retrieve
)
```

**Customize Prompts** - Edit prompt templates in [src/rag_retrieval.py](src/rag_retrieval.py)

## 📊 Data Format

The CSV files follow this competency framework structure:

| Competency Area | Topics | Must Have | Desirable | Advanced/ Best |
|----------------|--------|-----------|-----------|----------------|
| Python | List comprehensions | Basic usage | Advanced patterns | Production optimization |

Each competency level provides:
- **Must Have**: Foundational knowledge (Definition)
- **Desirable**: Intermediate application (Use Case)
- **Advanced**: Best practices (Real-World Example)

## 🛠️ Development

### Adding New Topics

1. Add CSV file to `data/raw_docs/` following the competency format
2. Update topic mapping in [src/ingestion_csv.py](src/ingestion_csv.py):
```python
csv_files = {
    "Python": "DE docs - Python.csv",
    "SQL": "DE docs - SQL.csv",
    "Database": "DE docs - Database.csv",
    "ETL": "DE docs - ETL.csv",
    "AWS": "DE docs - AWS.csv"  # New topic
}
```
3. Update topic detection in [app.py](app.py) `detect_topic_from_message()` function
4. Re-run ingestion: `python src/ingestion_csv.py`

### Testing the System

```bash
# Test vector store creation
python src/ingestion_csv.py

# Test RAG retrieval
python src/rag_retrieval.py

# Run the Streamlit app
streamlit run app.py
```

## 🐛 Troubleshooting

### "No vector store found" or "Collection not found"
**Solution**: Run the ingestion script to create the vector store:
```bash
python src/ingestion_csv.py
```

### AWS Credentials Error
**Solutions**:
- Ensure `.env` file exists with valid AWS credentials
- Verify the region supports Bedrock (use `us-east-1`)
- Check that your AWS account has Bedrock access enabled
- Verify Nova Lite and Titan Embeddings models are available

### Import Errors
**Solution**: Install all dependencies:
```bash
uv sync
# or
pip install -r requirements.txt
```

### ChromaDB Errors
**Solution**: Delete and recreate the vector store:
```bash
# Windows
Remove-Item -Recurse -Force data\vector_db

# Linux/Mac
rm -rf data/vector_db

# Re-run ingestion
python src/ingestion_csv.py
```

### Streamlit Port Already in Use
**Solution**: Use a different port:
```bash
streamlit run app.py --server.port 8502
```

## 💡 Tips for Best Results

1. **Be Specific**: Ask detailed questions about specific concepts
2. **Use Topic Names**: Mention the topic area in your questions
3. **Follow the Flow**: Let the chatbot guide you through topic selection
4. **Explore Systematically**: Work through one topic at a time
5. **Ask Follow-ups**: Dig deeper into concepts that interest you

## 📝 Answer Format

Every response includes structured sections:

```
Question:
[User's question repeated]

Definition:
[Clear, interview-level definition]

Use Case:
[When/why used in data engineering]

Real-World Example:
[Industry-relevant example]

Code Example (if applicable):
[Clean, production-quality code with comments]

Key Interview Notes:
- [Important point 1]
- [Important point 2]
- [Important point 3]
```

## 🚧 Future Enhancements

- [ ] Add AWS-specific documentation
- [ ] Support for follow-up questions with context
- [ ] Export conversation history
- [ ] Add more topics (Spark, Kafka, Airflow, etc.)
- [ ] Quiz mode for self-assessment
- [ ] Difficulty levels (Junior, Mid-level, Senior)

## 📄 License

MIT License

**Example Response:**
```
📚 Interview Practice Questions for Python

Entry-Level Questions (Must Have):
1. What are the main differences between lists and tuples in Python?
2. How do you handle exceptions in Python?
3. Explain basic list comprehensions.

Mid-Level Questions (Desirable):
4. How would you use decorators in a data pipeline?
5. What's the difference between map/filter/reduce?

Advanced Questions (Best Practice):
6. How do you optimize memory usage in large-scale data processing?

---

**Concept: List Comprehensions**

📚 Definition:
List comprehensions provide a concise, readable way to create lists 
by applying an expression to each item in an iterable.

💡 Use Case:
Commonly used in ETL pipelines to transform data efficiently without 
explicit for-loops. Ideal for filtering and mapping operations on datasets.

🚀 Real-World Example:
In a production data pipeline processing user events, you might extract 
active user IDs: `active_users = [user['id'] for user in users if user['status'] == 'active']`
This is more efficient and readable than traditional loops.
```

## 🌟 Features Highlight

- ✅ **Conversational Interface** - Natural dialogue flow
- ✅ **Topic-Filtered Retrieval** - Accurate, relevant content
- ✅ **Multi-Level Questions** - Entry, Mid, Advanced practice questions
- ✅ **Structured Answers** - Consistent format for learning
- ✅ **AWS Bedrock Integration** - Production-ready LLM
- ✅ **Vector Search** - Fast, semantic document retrieval
- ✅ **Persistent Storage** - ChromaDB for efficient queries
- ✅ **Streamlit UI** - Beautiful, responsive interface

## 🤝 Contributing

Contributions are welcome! To contribute:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test thoroughly
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Ideas for Contributions
- Add more topics (AWS, Spark, Kafka, etc.)
- Enhance prompt templates
- Add more example questions
- Improve UI/UX
- Add testing coverage
- Optimize retrieval performance

## 📄 License

This project is for educational purposes. Check individual dependencies for their licenses.

## 🙏 Acknowledgments

- LangChain for the RAG framework
- AWS Bedrock for Nova Lite and Titan Embeddings
- ChromaDB for vector storage
- Streamlit for the beautiful UI
- The Data Engineering community for competency frameworks

---

**Good luck with your Data Engineering interviews! 💼🚀**
