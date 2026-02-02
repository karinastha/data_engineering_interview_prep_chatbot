# Data Engineering Interview Prep Chatbot - Modern Architecture

A production-ready RAG chatbot built with Clean Architecture principles for data engineering interview preparation.

## 🚀 Features

- **Clean Architecture**: Domain-driven design with proper separation of concerns
- **Advanced RAG**: Retrieval-Augmented Generation with topic filtering and reranking
- **Few-Shot Learning**: Context-aware prompt engineering with examples
- **Conversation Memory**: Persistent chat history and context management
- **Production Ready**: Comprehensive error handling, logging, and monitoring
- **Scalable**: Modular design for easy extension and maintenance

## 🏗️ Architecture Overview

```
app_modern.py (Streamlit UI)
├── services/
│   ├── chat_service.py      # Conversation orchestration
│   ├── rag_service.py       # RAG pipeline management  
│   ├── memory_service.py    # Conversation persistence
│   └── prompt_service.py    # Template & few-shot management
├── infrastructure/
│   ├── vector_store/        # ChromaDB operations
│   ├── llm/                 # AWS Bedrock client
│   └── embeddings/          # HuggingFace embeddings
├── core/
│   ├── models/              # Domain models & data structures
│   └── exceptions/          # Custom exception hierarchy
└── config/
    └── settings.py          # Configuration management
```

## 📋 Requirements

- Python 3.8+
- AWS Account with Bedrock access
- 4GB+ RAM (for embeddings model)

## ⚡ Quick Start

### 1. Setup Environment

```bash
# Clone or navigate to project directory
cd data_engineering_interview_prep_chatbot

# Run setup script
python setup_modern.py
```

### 2. Configure AWS Credentials

Edit the `.env` file created by setup:

```env
# AWS Configuration
AWS_ACCESS_KEY_ID=your_actual_access_key
AWS_SECRET_ACCESS_KEY=your_actual_secret_key  
AWS_REGION=us-east-1

# Optional: Adjust other settings
LLM_MODEL_ID=amazon.nova-lite-v1:0
ENVIRONMENT=development
```

### 3. Migrate Existing Data (if applicable)

```bash
# Migrate from old system
python migrate.py
```

### 4. Launch Application

```bash
# Start the modern chatbot
streamlit run app_modern.py
```

## 🔧 Configuration

The system uses environment-based configuration with the following structure:

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `development` | Environment mode (development/production) |
| `AWS_ACCESS_KEY_ID` | - | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | - | AWS secret key |
| `AWS_REGION` | `us-east-1` | AWS region |
| `LLM_MODEL_ID` | `amazon.nova-lite-v1:0` | Bedrock model ID |
| `VECTOR_STORE_PERSIST_PATH` | `./data/vector_store_new` | ChromaDB storage path |
| `MEMORY_STORAGE_PATH` | `./data/memory` | Conversation storage path |

### Topic Categories

The system automatically categorizes questions into:
- **SQL**: Database queries, optimization, joins
- **Python**: Data processing, pandas, programming
- **ETL**: Pipeline design, data transformation
- **Database**: Architecture, design, NoSQL/SQL

## 🎯 Key Features Explained

### 1. Few-Shot Prompt Engineering

The system includes curated examples for each topic:

```python
# Automatic example selection based on query topic
if query_topic == Topic.SQL:
    # Includes relevant SQL examples in prompt
    examples = get_few_shot_examples(Topic.SQL)
```

### 2. Conversation Memory

- **Persistent Storage**: Conversations saved as JSON
- **Context Awareness**: Maintains conversation flow
- **Session Management**: Multiple concurrent sessions
- **Export Capability**: Download conversation history

### 3. Advanced RAG Pipeline

```python
# Multi-step RAG process
1. Query Analysis → Topic Detection
2. Document Retrieval → Similarity Search  
3. Context Filtering → Relevance Threshold
4. Prompt Generation → Few-shot + Context
5. Response Generation → LLM + Post-processing
```

### 4. Production Features

- **Health Monitoring**: Service health checks
- **Error Handling**: Graceful failure recovery
- **Logging**: Comprehensive activity tracking
- **Configuration**: Environment-based settings
- **Backup**: Automated data protection

## 🔍 Usage Examples

### Basic Queries
```
"How do I optimize a slow SQL query?"
"Explain ETL pipeline best practices"
"What's the difference between data lake and data warehouse?"
```

### Advanced Features
- **Topic Filtering**: Automatic categorization improves accuracy
- **Context Awareness**: References previous conversation
- **Debug Mode**: Toggle to see retrieval metrics
- **Export**: Download conversation for review

## 📊 Monitoring & Statistics

Access comprehensive statistics via the sidebar:
- **Session Metrics**: Message counts, topics discussed
- **System Health**: Component status checks  
- **Performance**: Response times, retrieval stats
- **Storage**: Memory usage, document counts

## 🛠️ Development

### Architecture Components

1. **Domain Layer** (`core/models/`)
   - Pure business logic
   - Data structures and validation
   - No external dependencies

2. **Service Layer** (`services/`)
   - Business operations orchestration
   - Cross-cutting concerns
   - Dependency injection

3. **Infrastructure Layer** (`infrastructure/`)
   - External service integration
   - Database operations
   - API clients

4. **Application Layer** (`app_modern.py`)
   - User interface
   - Request handling
   - Service coordination

### Adding New Features

1. **New Topic Category**:
   - Add to `Topic` enum in `core/models/conversation.py`
   - Create few-shot examples in `services/prompt_service.py`
   - Update topic inference logic

2. **New Service**:
   - Create in `services/` directory
   - Follow dependency injection pattern
   - Add health check method

3. **New Configuration**:
   - Add to `config/settings.py`
   - Update environment template
   - Add validation

## 🔒 Security & Privacy

- **Credentials**: Environment-based configuration
- **Data**: Local storage, no external transmission
- **Logs**: Sensitive data filtering
- **Access**: Session-based isolation

## 🚨 Troubleshooting

### Common Issues

1. **AWS Credentials Error**
   ```bash
   # Verify credentials
   python -c "import boto3; print(boto3.client('bedrock-runtime').list_foundation_models())"
   ```

2. **Vector Store Issues**
   ```bash
   # Reset vector database
   rm -rf data/vector_store_new
   python migrate.py
   ```

3. **Memory Errors**
   ```bash
   # Clear conversation memory
   rm -rf data/memory
   mkdir -p data/memory
   ```

### Debug Mode

Enable debug mode in the sidebar to see:
- Retrieval timing and document counts
- Context length and processing stats
- Error details and stack traces

### Logs

Check `chatbot.log` for detailed system activity:
```bash
tail -f chatbot.log
```

## 🔄 Migration Guide

### From Old System

1. **Backup**: Run `python migrate.py` (includes automatic backup)
2. **Data**: Migrates existing ChromaDB and CSV documents  
3. **Config**: Creates new environment-based configuration
4. **Verify**: Automatic health checks ensure successful migration

### Manual Migration

If automatic migration fails:

1. **Vector Store**: Copy `db/` or `data/vector_db/` to new location
2. **Documents**: Re-run ingestion with `migrate.py`
3. **Config**: Manually create `.env` from template

## 📈 Performance Optimization

### Memory Usage
- **Embedding Model**: ~500MB RAM
- **ChromaDB**: Scales with document count
- **Conversations**: ~1KB per message

### Response Times
- **Cold Start**: 2-3 seconds (model loading)
- **Warm Queries**: 0.5-1.5 seconds
- **Retrieval**: ~100ms for 10K documents

### Scaling Considerations
- **Documents**: Tested up to 100K+ documents
- **Concurrent Users**: Streamlit handles multiple sessions
- **Storage**: Linear scaling with conversation history

## 🤝 Contributing

1. **Fork** the repository
2. **Create** feature branch (`git checkout -b feature/amazing-feature`)
3. **Follow** architecture patterns and add tests
4. **Commit** changes (`git commit -m 'Add amazing feature'`)
5. **Push** to branch (`git push origin feature/amazing-feature`)
6. **Open** Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: Create GitHub issue with detailed description
- **Questions**: Use GitHub Discussions
- **Documentation**: Check inline code documentation

---

**Built with ❤️ for the data engineering community**