# LLM Code Assistant

A Python-based assistant that leverages local LLMs through Ollama to provide code analysis, fixing, and generation features.

## Features

- **Code Analysis**: Scan files or entire directories for issues, bugs, and improvement opportunities
- **Code Fixing**: Generate and apply fixes for identified issues
- **Code Generation**: Generate new code through a chat interface
- **Local LLM Integration**: Uses Ollama for local LLM inference

## Prerequisites

1. **Python 3.8+**: Make sure you have Python 3.8 or newer installed
2. **Ollama**: You need to have [Ollama](https://ollama.ai/) installed and running on your machine
   - Download from: https://ollama.ai/download

3. **CodeLlama Model**: Install the model with:
   ```
   ollama pull codellama:34b
   ```
   - For lower-end machines, you can also use:
   ```
   ollama pull codellama:7b
   ```

## Installation

1. Clone the repository or download the files
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

The assistant can be used in several ways:

### Command Line Interface

```
# Analyze a file
python main.py analyze path/to/file.py

# Analyze a directory
python main.py analyze path/to/directory

# Fix a file
python main.py fix path/to/file.py

# Generate code (interactive)
python main.py generate

# Chat with the assistant
python main.py chat

# Configure settings
python main.py settings --endpoint http://localhost:11434 --model codellama:34b
```

### Terminal UI (with Rich)

For a better terminal experience, you can use the Rich-based terminal UI:

```
python -m llm_code_assistant.ui.terminal_ui
```

### Graphical User Interface

The assistant also provides a simple GUI using Tkinter:

```
python main.py gui
```

## Configuration

The assistant can be configured by editing the configuration file at `~/.llmcodeassistant/config.json` or by using the settings command:

```
python main.py settings --endpoint http://localhost:11434 --model codellama:34b
```

## Development

### Project Structure

```
llm_code_assistant/
├── __init__.py
├── main.py                 # Main entry point with CLI interface
├── assistant/
│   ├── __init__.py
│   ├── code_analyzer.py    # Code analysis functionality
│   ├── code_fixer.py       # Code fixing functionality
│   ├── code_generator.py   # Code generation functionality
│   └── chat_assistant.py   # Chat interface for the assistant
├── services/
│   ├── __init__.py
│   ├── llm_service.py      # Ollama API integration
│   └── file_service.py     # File handling functionality
├── utils/
│   ├── __init__.py
│   ├── prompt_builder.py   # Utility for building prompts
│   └── config.py           # Configuration management
├── ui/
│   ├── __init__.py
│   ├── app.py              # Tkinter/GUI application
│   └── terminal_ui.py      # Terminal-based UI
└── README.md
```

## License

This project is licensed under the MIT License.

## Acknowledgements

- [CodeLlama](https://github.com/facebookresearch/codellama) - The underlying LLM model
- [Ollama](https://ollama.ai/) - Local LLM runtime
- [Rich](https://github.com/textualize/rich) - Terminal UI library