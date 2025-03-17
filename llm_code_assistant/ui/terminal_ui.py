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