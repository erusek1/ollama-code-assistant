"""
Terminal UI - A rich terminal user interface for the LLM Code Assistant
"""

import os
import sys
import re
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich.prompt import Prompt, Confirm
    from rich.table import Table
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

from services.llm_service import LLMService
from services.file_service import FileService
from assistant.code_analyzer import CodeAnalyzer
from assistant.code_fixer import CodeFixer
from assistant.code_generator import CodeGenerator
from assistant.chat_assistant import ChatAssistant
from utils.notes_manager import NotesManager


class TerminalUI:
    """Rich terminal user interface for the LLM Code Assistant."""
    
    def __init__(self, llm_service: LLMService, file_service: FileService):
        """
        Initialize the terminal UI.
        
        Args:
            llm_service: LLM service
            file_service: File service
        """
        self.llm_service = llm_service
        self.file_service = file_service
        
        if HAS_RICH:
            self.console = Console()
            self.code_analyzer = CodeAnalyzer(llm_service, file_service)
            self.code_fixer = CodeFixer(llm_service, file_service)
            self.code_generator = CodeGenerator(llm_service, file_service)
            self.chat_assistant = ChatAssistant(llm_service, file_service)
            self.notes_manager = NotesManager()
        else:
            print("Please install rich for better UI: pip install rich")
    
    def run(self):
        """Run the terminal UI."""
        if not HAS_RICH:
            # Fall back to basic chat assistant if rich is not available
            self.chat_assistant.start_interactive_session()
            return
        
        self.console.print(Panel.fit("LLM Code Assistant", style="bold cyan"))
        
        while True:
            self.console.print("\n[bold green]Choose an option:[/bold green]")
            self.console.print("[1] Analyze Code")
            self.console.print("[2] Fix Code")
            self.console.print("[3] Generate Code")
            self.console.print("[4] Chat with Assistant")
            self.console.print("[5] Manage Notes")
            self.console.print("[6] Exit")
            
            choice = Prompt.ask("Enter your choice", choices=["1", "2", "3", "4", "5", "6"])
            
            if choice == "1":
                self._analyze_code()
            elif choice == "2":
                self._fix_code()
            elif choice == "3":
                self._generate_code()
            elif choice == "4":
                self._chat_with_assistant()
            elif choice == "5":
                self._manage_notes()
            elif choice == "6":
                self.console.print("[bold green]Goodbye![/bold green]")
                break
    
    def _analyze_code(self):
        """Run the code analyzer."""
        file_path = Prompt.ask("Enter file or directory path")
        
        if not os.path.exists(file_path):
            self.console.print(f"[bold red]Error: Path '{file_path}' does not exist[/bold red]")
            return
        
        with self.console.status(f"Analyzing {file_path}...", spinner="dots"):
            if os.path.isfile(file_path):
                result = self.code_analyzer.analyze_file(file_path)
                self._display_analysis_result(file_path, result)
                
                # Ask to save as a note
                if Confirm.ask("Save this analysis as a note?"):
                    title = Prompt.ask("Enter note title", default=f"Analysis of {os.path.basename(file_path)}")
                    
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    note_content = f"# {title}\n\n"
                    note_content += f"Analysis of {file_path}\n"
                    note_content += f"Created: {timestamp}\n\n"
                    note_content += result
                    
                    note_id = self.notes_manager.add_note(
                        title=title,
                        content=note_content,
                        tags=["analysis"],
                        context={"file_path": file_path}
                    )
                    
                    self.console.print(f"[bold green]Note saved with ID: {note_id}[/bold green]")
            else:
                include_patterns = Prompt.ask("File patterns to include (e.g., *.py,*.js)", default="*.*")
                patterns = [p.strip() for p in include_patterns.split(",")]
                
                results = self.code_analyzer.analyze_directory(file_path, patterns)
                
                for file_path, result in results.items():
                    self._display_analysis_result(file_path, result)
                    
                    if Prompt.ask("Continue to next file? (y/n)", choices=["y", "n"], default="y") == "n":
                        break
    
    def _display_analysis_result(self, file_path: str, result: str):
        """
        Display the analysis result.
        
        Args:
            file_path: File path
            result: Analysis result
        """
        self.console.print(f"\n[bold cyan]Analysis of {file_path}[/bold cyan]")
        
        # Try to parse different sections from the result
        sections = re.split(r"##\s+([A-Za-z &]+)", result)
        
        if len(sections) > 1:
            # First section is everything before the first heading, which might be empty
            sections = sections[1:]
            
            # Pair section headings with their content
            for i in range(0, len(sections), 2):
                if i + 1 < len(sections):
                    heading = sections[i]
                    content = sections[i + 1].strip()
                    
                    self.console.print(f"[bold yellow]## {heading}[/bold yellow]")
                    self.console.print(Markdown(content))
        else:
            # If we couldn't parse sections, just display the raw result
            self.console.print(Markdown(result))
    
    def _fix_code(self):
        """Run the code fixer."""
        file_path = Prompt.ask("Enter file path")
        
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            self.console.print(f"[bold red]Error: File '{file_path}' does not exist[/bold red]")
            return
        
        # First analyze the file
        with self.console.status(f"Analyzing {file_path}...", spinner="dots"):
            analysis_result = self.code_analyzer.analyze_file(file_path)
        
        self._display_analysis_result(file_path, analysis_result)
        
        # Generate fixes
        with self.console.status(f"Generating fixes...", spinner="dots"):
            fixes = self.code_fixer.generate_fixes(file_path, analysis_result)
        
        # Extract the code block
        code_block = self._extract_code_block(fixes)
        
        if not code_block:
            self.console.print("[bold red]Error: Could not extract fixed code[/bold red]")
            return
        
        # Display the fixes
        self.console.print("\n[bold green]Generated Fixes:[/bold green]")
        
        # Get file content and language
        content, language = self.file_service.get_file_content(file_path)
        language = language or "python"
        
        # Generate diff
        with self.console.status("Generating diff...", spinner="dots"):
            diff = self.code_fixer.preview_fixes(content, fixes)
        
        self.console.print(Syntax(diff, "diff"))
        
        # Ask for confirmation to apply fixes
        if Confirm.ask("Do you want to apply these fixes?"):
            with self.console.status("Applying fixes...", spinner="dots"):
                result = self.code_fixer.apply_fixes(file_path, fixes)
            
            self.console.print(f"[bold green]{result}[/bold green]")
            
            # Ask to save as a note
            if Confirm.ask("Save this fix as a note?"):
                title = Prompt.ask("Enter note title", default=f"Fix for {os.path.basename(file_path)}")
                
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                note_content = f"# {title}\n\n"
                note_content += f"Fixed {file_path}\n"
                note_content += f"Created: {timestamp}\n\n"
                note_content += "## Analysis\n"
                note_content += analysis_result + "\n\n"
                note_content += "## Fixes\n"
                note_content += fixes
                
                note_id = self.notes_manager.add_note(
                    title=title,
                    content=note_content,
                    tags=["fix"],
                    context={"file_path": file_path}
                )
                
                self.console.print(f"[bold green]Note saved with ID: {note_id}[/bold green]")
    
    def _generate_code(self):
        """Run the code generator."""
        self.console.print("\n[bold cyan]Code Generator[/bold cyan]")
        self.console.print("Describe what you want to generate, and I'll help you create it.")
        
        description = Prompt.ask("Description")
        language = Prompt.ask("Programming language", default="python")
        
        with self.console.status(f"Generating {language} code...", spinner="dots"):
            result = self.code_generator.generate_code(description, language)
        
        # Display the result
        self.console.print("\n[bold green]Generated Code:[/bold green]")
        
        # Extract file paths and code blocks
        file_paths, code_blocks = self._extract_files_from_response(result)
        
        if file_paths and code_blocks:
            # Display each file separately
            for i, (path, code) in enumerate(zip(file_paths, code_blocks)):
                self.console.print(f"\n[bold blue]{path}[/bold blue]")
                self.console.print(Syntax(code, language))
                
                if i < len(file_paths) - 1:
                    self.console.print("---")
            
            # Ask if the user wants to save the files
            if Confirm.ask("Do you want to save these files?"):
                base_dir = Prompt.ask("Base directory", default=".")
                
                saved_files = []
                for path, code in zip(file_paths, code_blocks):
                    full_path = os.path.join(base_dir, path)
                    
                    # Create directory if it doesn't exist
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    
                    # Write content to file
                    with open(full_path, 'w') as f:
                        f.write(code)
                    
                    saved_files.append(full_path)
                
                self.console.print(f"[bold green]Saved {len(saved_files)} files:[/bold green]")
                for path in saved_files:
                    self.console.print(f"  - {path}")
                
                # Ask to save as a note
                if Confirm.ask("Save this code generation as a note?"):
                    title = Prompt.ask("Enter note title", default="Generated code")
                    
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    note_content = f"# {title}\n\n"
                    note_content += f"Generated code\n"
                    note_content += f"Created: {timestamp}\n\n"
                    note_content += "## Request\n"
                    note_content += description + "\n\n"
                    note_content += "## Generated Files\n"
                    
                    for i, path in enumerate(saved_files):
                        note_content += f"\n### {path}\n"
                        note_content += "```\n"
                        if i < len(code_blocks):
                            note_content += code_blocks[i]
                        note_content += "\n```\n"
                    
                    note_id = self.notes_manager.add_note(
                        title=title,
                        content=note_content,
                        tags=["code-generation"],
                        context={"generated_files": ",".join(saved_files)}
                    )
                    
                    self.console.print(f"[bold green]Note saved with ID: {note_id}[/bold green]")
        else:
            # Just display the raw result
            self.console.print(Markdown(result))
    
    def _chat_with_assistant(self):
        """Run the chat assistant."""
        self.console.print("\n[bold cyan]Chat with Assistant[/bold cyan]")
        self.console.print("Type 'exit' to return to the main menu.")
        self.console.print("Note commands: 'note save <title>', 'note list', 'note search <query>', 'note get <id>', 'note context <file_path>'")
        
        conversation_history = [
            ("system", "You are a helpful AI assistant for analyzing and generating code.")
        ]
        
        while True:
            try:
                user_input = Prompt.ask("\nYou")
                
                if user_input.lower() == 'exit':
                    break
                
                # Check for note commands
                if user_input.lower().startswith('note '):
                    parts = user_input[5:].strip().split(' ', 1)
                    sub_command = parts[0].lower()
                    
                    if sub_command == 'save':
                        if len(parts) < 2:
                            self.console.print("[bold red]Error: Please provide a title for the note.[/bold red]")
                            continue
                        
                        title = parts[1]
                        
                        # Get the last exchange
                        last_user_message = None
                        last_assistant_message = None
                        
                        for i in range(len(conversation_history) - 1, -1, -1):
                            role, content = conversation_history[i]
                            if role == "assistant" and last_assistant_message is None:
                                last_assistant_message = content
                            elif role == "user" and last_assistant_message is not None and last_user_message is None:
                                last_user_message = content
                                break
                        
                        if last_user_message is None or last_assistant_message is None:
                            self.console.print("[bold red]Error: No conversation to save.[/bold red]")
                            continue
                        
                        # Create note content
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        content = f"# {title}\n\n"
                        content += f"Created: {timestamp}\n\n"
                        content += f"## User\n{last_user_message}\n\n"
                        content += f"## Assistant\n{last_assistant_message}\n"
                        
                        # Determine context
                        context = {}
                        
                        # Check if the conversation relates to a specific file
                        file_match = re.search(r"([\"'].+[\"']|\S+\.\w+)", last_user_message)
                        if file_match:
                            possible_file = file_match.group(1).strip("\"'")
                            if os.path.exists(possible_file):
                                context["file_path"] = possible_file
                        
                        # Save the note
                        note_id = self.notes_manager.add_note(
                            title=title,
                            content=content,
                            tags=["conversation"],
                            context=context
                        )
                        
                        self.console.print(f"[bold green]Note saved with ID: {note_id}[/bold green]")
                    
                    elif sub_command == 'list':
                        notes = self.notes_manager.list_notes()
                        
                        if not notes:
                            self.console.print("[bold yellow]No notes found.[/bold yellow]")
                            continue
                        
                        table = Table(title=f"Found {len(notes)} notes")
                        table.add_column("ID", style="cyan")
                        table.add_column("Title", style="green")
                        table.add_column("Created", style="magenta")
                        table.add_column("Tags", style="yellow")
                        
                        for note in notes:
                            created = datetime.fromtimestamp(note["created"]).strftime("%Y-%m-%d %H:%M")
                            tags = ", ".join(note["tags"]) if note["tags"] else ""
                            table.add_row(note["id"], note["title"], created, tags)
                        
                        self.console.print(table)
                    
                    elif sub_command == 'search':
                        if len(parts) < 2:
                            self.console.print("[bold red]Error: Please provide a search query.[/bold red]")
                            continue
                        
                        query = parts[1]
                        notes = self.notes_manager.search_notes(query)
                        
                        if not notes:
                            self.console.print(f"[bold yellow]No notes found matching '{query}'.[/bold yellow]")
                            continue
                        
                        table = Table(title=f"Found {len(notes)} notes matching '{query}'")
                        table.add_column("ID", style="cyan")
                        table.add_column("Title", style="green")
                        table.add_column("Created", style="magenta")
                        table.add_column("Snippet", style="white")
                        
                        for note in notes:
                            created = datetime.fromtimestamp(note["created"]).strftime("%Y-%m-%d %H:%M")
                            
                            # Find snippet around the query
                            content = note["content"]
                            query_pos = content.lower().find(query.lower())
                            if query_pos != -1:
                                start = max(0, query_pos - 20)
                                end = min(len(content), query_pos + len(query) + 50)
                                snippet = content[start:end]
                                
                                # Add ellipsis if truncated
                                if start > 0:
                                    snippet = "..." + snippet
                                if end < len(content):
                                    snippet += "..."
                            else:
                                snippet = ""
                            
                            table.add_row(note["id"], note["title"], created, snippet)
                        
                        self.console.print(table)
                    
                    elif sub_command == 'get':
                        if len(parts) < 2:
                            self.console.print("[bold red]Error: Please provide a note ID.[/bold red]")
                            continue
                        
                        note_id = parts[1]
                        note = self.notes_manager.get_note(note_id)
                        
                        if not note:
                            self.console.print(f"[bold red]Note with ID '{note_id}' not found.[/bold red]")
                            continue
                        
                        self.console.print(Panel(Markdown(note["content"]), 
                                                title=note["title"],
                                                subtitle=f"Created: {datetime.fromtimestamp(note['created']).strftime('%Y-%m-%d %H:%M')}"))
                    
                    elif sub_command == 'context':
                        if len(parts) < 2:
                            self.console.print("[bold red]Error: Please provide a file path.[/bold red]")
                            continue
                        
                        file_path = parts[1]
                        
                        if not os.path.exists(file_path):
                            self.console.print(f"[bold red]File '{file_path}' does not exist.[/bold red]")
                            continue
                        
                        notes = self.notes_manager.get_context_notes("file_path", file_path)
                        
                        if not notes:
                            self.console.print(f"[bold yellow]No notes found for file '{file_path}'.[/bold yellow]")
                            continue
                        
                        table = Table(title=f"Found {len(notes)} notes for file '{file_path}'")
                        table.add_column("ID", style="cyan")
                        table.add_column("Title", style="green")
                        table.add_column("Created", style="magenta")
                        table.add_column("Tags", style="yellow")
                        
                        for note in notes:
                            created = datetime.fromtimestamp(note["created"]).strftime("%Y-%m-%d %H:%M")
                            tags = ", ".join(note["tags"]) if note["tags"] else ""
                            table.add_row(note["id"], note["title"], created, tags)
                        
                        self.console.print(table)
                    
                    else:
                        self.console.print(f"[bold red]Unknown note command: {sub_command}[/bold red]")
                        self.console.print("Available commands: save, list, search, get, context")
                    
                    continue
                
                # Add to conversation history
                conversation_history.append(("user", user_input))
                
                # Check for relevant notes to enhance the context
                with self.console.status("Checking for relevant notes...", spinner="dots"):
                    enhanced_context = self._check_for_relevant_notes(user_input)
                    
                    if enhanced_context:
                        system_msg = ("system", f"The following notes may be relevant to the user's query: {enhanced_context}")
                        conversation_history.append(system_msg)
                        self.console.print("[bold blue]Found relevant notes in your knowledge base.[/bold blue]")
                
                # Get response from LLM
                with self.console.status("Thinking...", spinner="dots"):
                    response = self.llm_service.continue_conversation(conversation_history)
                
                # Add to conversation history
                conversation_history.append(("assistant", response))
                
                # Display the response
                self.console.print("\n[bold green]Assistant:[/bold green]")
                self.console.print(Markdown(response))
                
                # Check for code generation
                file_paths, code_blocks = self._extract_files_from_response(response)
                
                if file_paths and code_blocks and len(file_paths) == len(code_blocks):
                    if Confirm.ask("Save generated files?"):
                        base_dir = Prompt.ask("Base directory", default=".")
                        
                        saved_files = []
                        for path, code in zip(file_paths, code_blocks):
                            full_path = os.path.join(base_dir, path)
                            
                            # Create directory if it doesn't exist
                            os.makedirs(os.path.dirname(full_path), exist_ok=True)
                            
                            # Write content to file
                            with open(full_path, 'w') as f:
                                f.write(code)
                            
                            saved_files.append(full_path)
                        
                        self.console.print(f"[bold green]Saved {len(saved_files)} files:[/bold green]")
                        for path in saved_files:
                            self.console.print(f"  - {path}")
            
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.console.print(f"[bold red]Error: {str(e)}[/bold red]")
    
    def _manage_notes(self):
        """Manage notes."""
        while True:
            self.console.print("\n[bold cyan]Notes Manager[/bold cyan]")
            self.console.print("[1] List All Notes")
            self.console.print("[2] Search Notes")
            self.console.print("[3] View Note")
            self.console.print("[4] Delete Note")
            self.console.print("[5] Export Notes")
            self.console.print("[6] Import Notes")
            self.console.print("[7] Return to Main Menu")
            
            choice = Prompt.ask("Enter your choice", choices=["1", "2", "3", "4", "5", "6", "7"])
            
            if choice == "1":
                self._list_notes()
            elif choice == "2":
                self._search_notes()
            elif choice == "3":
                self._view_note()
            elif choice == "4":
                self._delete_note()
            elif choice == "5":
                self._export_notes()
            elif choice == "6":
                self._import_notes()
            elif choice == "7":
                break
    
    def _list_notes(self):
        """List all notes."""
        notes = self.notes_manager.list_notes()
        
        if not notes:
            self.console.print("[bold yellow]No notes found.[/bold yellow]")
            return
        
        table = Table(title=f"Found {len(notes)} notes")
        table.add_column("ID", style="cyan")
        table.add_column("Title", style="green")
        table.add_column("Created", style="magenta")
        table.add_column("Tags", style="yellow")
        
        for note in notes:
            created = datetime.fromtimestamp(note["created"]).strftime("%Y-%m-%d %H:%M")
            tags = ", ".join(note["tags"]) if note["tags"] else ""
            table.add_row(note["id"], note["title"], created, tags)
        
        self.console.print(table)
    
    def _search_notes(self):
        """Search notes."""
        query = Prompt.ask("Enter search query")
        
        notes = self.notes_manager.search_notes(query)
        
        if not notes:
            self.console.print(f"[bold yellow]No notes found matching '{query}'.[/bold yellow]")
            return
        
        table = Table(title=f"Found {len(notes)} notes matching '{query}'")
        table.add_column("ID", style="cyan")
        table.add_column("Title", style="green")
        table.add_column("Created", style="magenta")
        table.add_column("Snippet", style="white")
        
        for note in notes:
            created = datetime.fromtimestamp(note["created"]).strftime("%Y-%m-%d %H:%M")
            
            # Find snippet around the query
            content = note["content"]
            query_pos = content.lower().find(query.lower())
            if query_pos != -1:
                start = max(0, query_pos - 20)
                end = min(len(content), query_pos + len(query) + 50)
                snippet = content[start:end]
                
                # Add ellipsis if truncated
                if start > 0:
                    snippet = "..." + snippet
                if end < len(content):
                    snippet += "..."
            else:
                snippet = ""
            
            table.add_row(note["id"], note["title"], created, snippet)
        
        self.console.print(table)
    
    def _view_note(self):
        """View a specific note."""
        note_id = Prompt.ask("Enter note ID")
        
        note = self.notes_manager.get_note(note_id)
        
        if not note:
            self.console.print(f"[bold red]Note with ID '{note_id}' not found.[/bold red]")
            return
        
        self.console.print(Panel(Markdown(note["content"]), 
                                title=note["title"],
                                subtitle=f"Created: {datetime.fromtimestamp(note['created']).strftime('%Y-%m-%d %H:%M')}"))
    
    def _delete_note(self):
        """Delete a note."""
        note_id = Prompt.ask("Enter note ID to delete")
        
        note = self.notes_manager.get_note(note_id)
        
        if not note:
            self.console.print(f"[bold red]Note with ID '{note_id}' not found.[/bold red]")
            return
        
        if Confirm.ask(f"Are you sure you want to delete note '{note['title']}'?"):
            success = self.notes_manager.delete_note(note_id)
            
            if success:
                self.console.print(f"[bold green]Note '{note['title']}' deleted successfully.[/bold green]")
            else:
                self.console.print(f"[bold red]Error deleting note '{note['title']}'.[/bold red]")
    
    def _export_notes(self):
        """Export notes to a file."""
        file_path = Prompt.ask("Enter export file path")
        
        success = self.notes_manager.export_notes(file_path)
        
        if success:
            self.console.print(f"[bold green]Notes exported successfully to '{file_path}'.[/bold green]")
        else:
            self.console.print(f"[bold red]Error exporting notes to '{file_path}'.[/bold red]")
    
    def _import_notes(self):
        """Import notes from a file."""
        file_path = Prompt.ask("Enter import file path")
        
        if not os.path.exists(file_path):
            self.console.print(f"[bold red]File '{file_path}' does not exist.[/bold red]")
            return
        
        count = self.notes_manager.import_notes(file_path)
        
        if count > 0:
            self.console.print(f"[bold green]Successfully imported {count} notes from '{file_path}'.[/bold green]")
        else:
            self.console.print(f"[bold red]No notes imported from '{file_path}'.[/bold red]")
    
    def _check_for_relevant_notes(self, user_input: str) -> Optional[str]:
        """
        Check if there are relevant notes for the user's input.
        
        Args:
            user_input: User's input message
            
        Returns:
            Enhanced context with relevant notes, or None if no relevant notes found
        """
        # Check if the input mentions a specific file
        file_match = re.search(r"([\"'].+[\"']|\S+\.\w+)", user_input)
        if file_match:
            possible_file = file_match.group(1).strip("\"'")
            if os.path.exists(possible_file):
                # Get notes related to this file
                file_notes = self.notes_manager.get_context_notes("file_path", possible_file)
                if file_notes:
                    # Format notes for context
                    context = f"Notes related to file '{possible_file}':\n"
                    for note in file_notes[:3]:  # Limit to 3 notes to avoid token limits
                        context += f"- {note['title']}:\n"
                        
                        # Get a brief snippet
                        content_lines = note["content"].split("\n")
                        relevant_lines = []
                        for line in content_lines:
                            if line.startswith("## Assistant"):