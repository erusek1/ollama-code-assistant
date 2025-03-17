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
