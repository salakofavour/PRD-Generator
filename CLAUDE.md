# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Product Requirements Document (PRD) Generator** built with Streamlit and OpenAI. It helps project managers, product owners, and stakeholders create comprehensive PRDs through natural language interaction with an AI assistant.

### Key Features
- **Natural Language Query (NLQ)**: Chat-like interface for PRD creation and iteration
- **Version Control**: Track and revert to previous PRD versions
- **Collaboration**: Share and approve PRDs for continuous improvement
- **Training Loop**: Approved PRDs feed back into the system to improve AI responses
- **Local Deployment**: Runs entirely locally with Streamlit

## Development Commands

### Setup and Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template and configure
cp .env.example .env
# Edit .env with your OpenAI API key
```

### Running the Application
```bash
# Start the Streamlit application
streamlit run app.py

# Run with specific port
streamlit run app.py --server.port 8501
```

### Testing
```bash
# Test API connection from within the app
# Go to Settings tab -> Test API Connection button
```

### Database Management
```bash
# Database is automatically initialized on first run
# Located at: data/prd_database.db
# No manual migration commands needed
```

## Architecture

### Core Components

1. **`app.py`** - Main Streamlit application entry point
   - Handles UI routing and state management
   - Integrates all components together
   - Manages user sessions and PRD workflows

2. **`src/models/prd_model.py`** - Database layer (SQLite)
   - `PRDDatabase` class manages all data operations
   - Handles PRDs, versions, chat sessions, and approvals
   - Automatic schema initialization

3. **`src/utils/llm_handler.py`** - AI integration layer
   - `LLMHandler` class manages OpenAI API calls
   - System prompts for PRD generation and iteration
   - Handles context and conversation history

4. **`src/components/chat_interface.py`** - UI components
   - `ChatInterface` class provides reusable UI elements
   - Chat display, forms, version history, and actions
   - Streamlit session state management

### Data Flow

1. **PRD Creation**: User input → LLM processing → PRD generation → Database storage
2. **PRD Iteration**: Existing PRD + user chat → LLM refinement → Updated content
3. **Version Control**: Each save creates new version entry with full history
4. **Training Loop**: Approved PRDs → Context for future LLM improvements

### Database Schema

- **`prds`**: Main PRD records with metadata
- **`prd_versions`**: Complete version history
- **`chat_sessions`**: Conversation logs for each PRD

## Configuration

### Environment Variables
- `OPENAI_API_KEY`: Required for LLM functionality
- Optional: Alternative LLM API keys (Anthropic, Google)

### Key Files
- `.env`: API keys and configuration (not in repo)
- `requirements.txt`: Python dependencies
- `data/`: SQLite database and generated files
- `logs/`: Application logs (auto-created)

## Development Guidelines

### Adding New Features
1. Follow the component-based architecture
2. Database changes should include migration logic in `PRDDatabase.init_database()`
3. New LLM prompts should be tested in the `LLMHandler` class
4. UI components should be added to `ChatInterface` class

### Code Patterns
- Use Streamlit session state for UI state management
- Database operations should be wrapped in try/catch blocks
- LLM calls should include error handling and user feedback
- All user inputs should be validated before processing

### Testing Strategy
- Manual testing through the Streamlit interface
- API connection testing in Settings tab
- Database integrity checks on startup
- Version control testing with multiple iterations

## Troubleshooting

### Common Issues
1. **API Key Not Set**: Check `.env` file and restart application
2. **Database Errors**: Delete `data/prd_database.db` to reset schema
3. **LLM Timeouts**: Check internet connection and API quota
4. **Version Loading Issues**: Verify PRD ID in session state

### Performance Notes
- Large PRDs (>10k chars) may hit LLM token limits
- Chat history is trimmed to last 10 messages for context
- Database queries are not optimized for large datasets (100+ PRDs)

## External Dependencies

### Required APIs
- OpenAI API (GPT-3.5-turbo) for content generation
- Internet connection for LLM calls

### References Used in System Prompts
- ProductPlan PRD guidelines: https://www.productplan.com/glossary/product-requirements-document/
- Industry best practices for comprehensive PRD structure