# PRD Generator 📋

A comprehensive Product Requirements Document (PRD) generator with natural language chat interface, built with Streamlit and OpenAI.

## Features

- 🤖 **AI-Powered Generation**: Create detailed PRDs from natural language descriptions
- 💬 **Chat Interface**: Iterate and refine PRDs through conversational interaction
- 📚 **Version Control**: Track all changes and revert to previous versions
- ✅ **Approval System**: Mark PRDs as approved for quality feedback loop
- 🔄 **Continuous Learning**: Approved PRDs improve future AI responses
- 💾 **Local Storage**: All data stored locally in SQLite database

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API Key**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

3. **Run Application**
   ```bash
   streamlit run app.py
   ```

4. **Open Browser**
   - Navigate to `http://localhost:8501`
   - Start creating PRDs through the chat interface!

## Usage

### Creating a New PRD
1. Go to the "Chat & Generate" tab
2. Type your product idea or requirements in natural language
3. The AI will generate a comprehensive PRD
4. Iterate through chat to refine sections

### Managing PRDs
- **Save Versions**: Click "💾 Save Version" to create version snapshots
- **Approve PRDs**: Mark high-quality PRDs as approved for training data
- **View History**: Access all previous versions in the sidebar
- **Export**: Download PRDs as text files

### Best Practices
- Provide detailed initial descriptions for better PRD quality
- Use the chat interface to ask for specific section improvements
- Approve well-structured PRDs to improve future generations
- Save versions before major changes

## Project Structure

```
prd-generator/
├── app.py                          # Main Streamlit application
├── src/
│   ├── models/
│   │   └── prd_model.py            # Database models and operations
│   ├── utils/
│   │   └── llm_handler.py          # OpenAI integration
│   └── components/
│       └── chat_interface.py       # UI components
├── data/                           # SQLite database storage
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment template
└── CLAUDE.md                       # Development guide
```

## Requirements

- Python 3.8+
- OpenAI API key
- Internet connection for LLM calls

## License

MIT License - Feel free to modify and distribute.