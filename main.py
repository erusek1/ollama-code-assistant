#!/usr/bin/env python3
"""
LLM Code Assistant

A Python-based assistant that leverages local LLMs through Ollama to 
provide code analysis, fixing, and generation features.

Usage:
  main.py analyze <file_path>   - Analyze a specific file or directory
  main.py fix <file_path>       - Fix issues in a specific file
  main.py generate              - Enter chat mode to generate new code
  main.py chat                  - Enter chat mode for general assistance
  main.py gui                   - Launch the graphical user interface
  main.py note list             - List all notes
  main.py note search <query>   - Search notes for a query
  main.py note get <id>         - Get a specific note by ID
  main.py note export <file>    - Export notes to a file
  main.py note import <file>    - Import notes from a file
"""

import os
import sys
import argparse
from pathlib import Path

from llm_code_assistant.assistant.code_analyzer import CodeAnalyzer
from llm_code_assistant.assistant.code_fixer import CodeFixer
from llm_code_assistant.assistant.code_generator import CodeGenerator
from llm_code_assistant.assistant.chat_assistant import ChatAssistant
from llm_code_assistant.services.llm_service import LLMService
from llm_code_assistant.services.file_service import FileService
from llm_code_assistant.utils.config import Config
from llm_code_assistant.utils.notes_manager import NotesManager

# Check for GUI dependencies and import conditionally
try:
    from llm_code_assistant.ui.app import Application
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False


def setup_parser():
    """Configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="LLM Code Assistant - A Python-based assistant for code analysis, fixing, and generation"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a file or directory")
    analyze_parser.add_argument("path", help="Path to file or directory to analyze")
    
    # Fix command
    fix_parser = subparsers.add_parser("fix", help="Fix issues in a file")
    fix_parser.add_argument("path", help="Path to file to fix")
    
    # Generate command
    subparsers.add_parser("generate", help="Enter chat mode to generate new code")
    
    # Chat command
    subparsers.add_parser("chat", help="Enter chat mode for general assistance")
    
    # GUI command
    subparsers.add_parser("gui", help="Launch the graphical user interface")
    
    # Note commands
    note_parser = subparsers.add_parser("note", help="Manage notes")
    note_subparsers = note_parser.add_subparsers(dest="note_command", help="Note command")
    
    # Note list command
    note_subparsers.add_parser("list", help="List all notes")
    
    # Note search command
    note_search_parser = note_subparsers.add_parser("search", help="Search notes")
    note_search_parser.add_argument("query", help="Search query")
    
    # Note get command
    note_get_parser = note_subparsers.add_parser("get", help="Get a specific note")
    note_get_parser.add_argument("id", help="Note ID")
    
    # Note export command
    note_export_parser = note_subparsers.add_parser("export", help="Export notes to a file")
    note_export_parser.add_argument("file", help="Output file path")
    
    # Note import command
    note_import_parser = note_subparsers.add_parser("import", help="Import notes from a file")
    note_import_parser.add_argument("file", help="Input file path")
    
    # Settings command
    settings_parser = subparsers.add_parser("settings", help="Configure settings")
    settings_parser.add_argument("--endpoint", help="Ollama API endpoint (e.g., http://localhost:11434)")
    settings_parser.add_argument("--model", help="Ollama model name (e.g., codellama:34b)")
    
    return parser


def main():
    """Main entry point for the application."""
    parser = setup_parser()
    args = parser.parse_args()
    
    # Initialize configuration
    config = Config()
    
    # Handle settings command
    if args.command == "settings":
        if args.endpoint:
            config.set("endpoint", args.endpoint)
        if args.model:
            config.set("model", args.model)
        
        # Save and display current settings
        config.save()
        print(f"Current settings:")
        print(f"  Endpoint: {config.get('endpoint')}")
        print(f"  Model: {config.get('model')}")
        return
    
    # Initialize services
    file_service = FileService()
    llm_service = LLMService(
        endpoint=config.get("endpoint"),
        model=config.get("model")
    )
    
    # Handle note commands
    if args.command == "note":
        notes_manager = NotesManager()
        
        if args.note_command == "list":
            notes = notes_manager.list_notes()
            
            if not notes:
                print("No notes found.")
                return
            
            print(f"Found {len(notes)} notes:")
            for note in notes:
                from datetime import datetime
                created = datetime.fromtimestamp(note["created"]).strftime("%Y-%m-%d %H:%M")
                print(f"  - [{note['id']}] {note['title']} ({created})")
        
        elif args.note_command == "search":
            notes = notes_manager.search_notes(args.query)
            
            if not notes:
                print(f"No notes found matching '{args.query}'.")
                return
            
            print(f"Found {len(notes)} notes matching '{args.query}':")
            for note in notes:
                from datetime import datetime
                created = datetime.fromtimestamp(note["created"]).strftime("%Y-%m-%d %H:%M")
                print(f"  - [{note['id']}] {note['title']} ({created})")
                
                # Show snippet of matching content
                content = note["content"]
                query_pos = content.lower().find(args.query.lower())
                if query_pos != -1:
                    start = max(0, query_pos - 20)
                    end = min(len(content), query_pos + len(args.query) + 60)
                    snippet = content[start:end]
                    
                    # Add ellipsis if truncated
                    if start > 0:
                        snippet = "..." + snippet
                    if end < len(content):
                        snippet += "..."
                    
                    print(f"    {snippet}")
        
        elif args.note_command == "get":
            note = notes_manager.get_note(args.id)
            
            if not note:
                print(f"Note with ID '{args.id}' not found.")
                return
            
            print(note["content"])
        
        elif args.note_command == "export":
            success = notes_manager.export_notes(args.file)
            
            if success:
                print(f"Notes successfully exported to '{args.file}'.")
            else:
                print(f"Error exporting notes to '{args.file}'.")
        
        elif args.note_command == "import":
            count = notes_manager.import_notes(args.file)
            
            if count > 0:
                print(f"Successfully imported {count} notes from '{args.file}'.")
            else:
                print(f"No notes imported from '{args.file}'.")
        
        else:
            parser.print_help()
        
        return
    
    # Check if Ollama is available
    try:
        success, message = llm_service.verify_connection()
        if not success:
            print(f"Error: {message}")
            print("Please check your settings with 'python main.py settings' and ensure Ollama is running")
            return
    except Exception as e:
        print(f"Error connecting to Ollama: {e}")
        print("Please check your settings with 'python main.py settings' and ensure Ollama is running")
        return
    
    # Process commands
    if args.command == "analyze":
        path = Path(args.path)
        if not path.exists():
            print(f"Error: Path '{path}' does not exist")
            return
        
        analyzer = CodeAnalyzer(llm_service, file_service)
        if path.is_file():
            result = analyzer.analyze_file(str(path))
            print(result)
        else:
            results = analyzer.analyze_directory(str(path))
            for file_path, result in results.items():
                print(f"\n{'=' * 30}\nAnalysis of {file_path}:\n{'=' * 30}")
                print(result)
    
    elif args.command == "fix":
        path = Path(args.path)
        if not path.exists() or not path.is_file():
            print(f"Error: File '{path}' does not exist")
            return
        
        # First analyze the file
        analyzer = CodeAnalyzer(llm_service, file_service)
        analysis_result = analyzer.analyze_file(str(path))
        print("Analysis result:")
        print(analysis_result)
        
        # Generate fixes
        fixer = CodeFixer(llm_service, file_service)
        fixes = fixer.generate_fixes(str(path), analysis_result)
        print("\nSuggested fixes:")
        print(fixes)
        
        # Ask for confirmation to apply fixes
        response = input("\nDo you want to apply these fixes? (y/n): ")
        if response.lower() == 'y':
            result = fixer.apply_fixes(str(path), fixes)
            print(result)
            
            # Ask to save as a note
            response = input("\nDo you want to save this fix as a note? (y/n): ")
            if response.lower() == 'y':
                notes_manager = NotesManager()
                
                title = input("Enter note title: ")
                
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                note_content = f"# {title}\n\n"
                note_content += f"Fixed {path}\n"
                note_content += f"Created: {timestamp}\n\n"
                note_content += "## Analysis\n"
                note_content += analysis_result + "\n\n"
                note_content += "## Fixes\n"
                note_content += fixes
                
                note_id = notes_manager.add_note(
                    title=title,
                    content=note_content,
                    tags=["fix"],
                    context={"file_path": str(path)}
                )
                
                print(f"Note saved with ID: {note_id}")
    
    elif args.command == "generate":
        generator = CodeGenerator(llm_service, file_service)
        generator.start_interactive_session()
    
    elif args.command == "chat":
        chat = ChatAssistant(llm_service, file_service)
        chat.start_interactive_session()
    
    elif args.command == "gui":
        if not GUI_AVAILABLE:
            print("Error: GUI dependencies not available. Install with: pip install tkinter")
            return
        
        app = Application(llm_service, file_service)
        app.run()
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()