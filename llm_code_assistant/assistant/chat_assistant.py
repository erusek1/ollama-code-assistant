"""
Chat Assistant - Interactive chat interface for the LLM code assistant
"""

import os
import re
import time
from typing import List, Tuple, Optional
from datetime import datetime

from llm_code_assistant.services.llm_service import LLMService
from llm_code_assistant.services.file_service import FileService
from llm_code_assistant.utils.notes_manager import NotesManager


class ChatAssistant:
    """Interactive chat interface for the LLM code assistant."""
    
    def __init__(self, llm_service: LLMService, file_service: FileService):
        """
        Initialize the chat assistant.
        
        Args:
            llm_service: LLM service for conversation
            file_service: File service for file operations
        """
        self.llm_service = llm_service
        self.file_service = file_service
        self.conversation_history = []
        self.notes_manager = NotesManager()
    
    def start_interactive_session(self):
        """Start an interactive chat session."""
        print("\nLLM Code Assistant Chat")
        print("----------------------")
        print("I can help you with code analysis, fixing, and generation.")
        print("Type 'exit' to quit, 'analyze <file_path>' to analyze a file, 'fix <file_path>' to fix a file.")
        print("\nNotes commands:")
        print("  'note save <title>' - Save the last exchange as a note")
        print("  'note list' - List all notes")
        print("  'note search <query>' - Search notes")
        print("  'note get <id>' - Show a specific note")
        print("  'note context <file_path>' - Show notes related to a file")
        
        # Initialize conversation history
        self.conversation_history = [
            ("system", "You are a helpful AI assistant for analyzing and generating code.")
        ]
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                
                if user_input.lower() == 'exit':
                    print("Goodbye!")
                    break
                
                # Check for note commands
                if user_input.lower().startswith('note '):
                    self._handle_note_command(user_input[5:])
                    continue
                
                # Check for other commands
                if user_input.lower().startswith('analyze '):
                    file_path = user_input[8:].strip()
                    self._analyze_file(file_path)
                    continue
                
                if user_input.lower().startswith('fix '):
                    file_path = user_input[4:].strip()
                    self._fix_file(file_path)
                    continue
                
                # Check if it's a request to look at a file
                file_match = re.search(r"(look|check|open|read|view|see|show) ([\"'].+[\"']|\S+)", user_input.lower())
                if file_match:
                    file_path = file_match.group(2).strip("\"'")
                    self._show_file(file_path)
                    continue
                
                # Add to conversation history
                self.conversation_history.append(("user", user_input))
                
                # Enhance with relevant notes if available
                enhanced_context = self._check_for_relevant_notes(user_input)
                if enhanced_context:
                    system_msg = ("system", f"The following notes may be relevant to the user's query: {enhanced_context}")
                    self.conversation_history.append(system_msg)
                
                # Get response from LLM
                response = self.llm_service.continue_conversation(self.conversation_history)
                
                # Check for code generation in the response
                self._check_for_code_generation(response)
                
                # Add to conversation history
                self.conversation_history.append(("assistant", response))
                
                print(f"\nAssistant: {response}")
            
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"\nError: {str(e)}")
    
    def _handle_note_command(self, command: str):
        """
        Handle note commands.
        
        Args:
            command: The note command (without the 'note ' prefix)
        """
        parts = command.strip().split(' ', 1)
        sub_command = parts[0].lower()
        
        if sub_command == 'save':
            # Save the last exchange as a note
            if len(parts) < 2:
                print("Error: Please provide a title for the note.")
                return
            
            title = parts[1]
            
            # Get the last exchange
            last_user_message = None
            last_assistant_message = None
            
            for i in range(len(self.conversation_history) - 1, -1, -1):
                role, content = self.conversation_history[i]
                if role == "assistant" and last_assistant_message is None:
                    last_assistant_message = content
                elif role == "user" and last_assistant_message is not None and last_user_message is None:
                    last_user_message = content
                    break
            
            if last_user_message is None or last_assistant_message is None:
                print("Error: No conversation to save.")
                return
            
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
            
            print(f"Note saved with ID: {note_id}")
        
        elif sub_command == 'list':
            # List all notes
            notes = self.notes_manager.list_notes()
            
            if not notes:
                print("No notes found.")
                return
            
            print(f"\nFound {len(notes)} notes:")
            for note in notes:
                created = datetime.fromtimestamp(note["created"]).strftime("%Y-%m-%d %H:%M")
                print(f"  - [{note['id']}] {note['title']} ({created})")
        
        elif sub_command == 'search':
            # Search notes
            if len(parts) < 2:
                print("Error: Please provide a search query.")
                return
            
            query = parts[1]
            notes = self.notes_manager.search_notes(query)
            
            if not notes:
                print(f"No notes found matching '{query}'.")
                return
            
            print(f"\nFound {len(notes)} notes matching '{query}':")
            for note in notes:
                created = datetime.fromtimestamp(note["created"]).strftime("%Y-%m-%d %H:%M")
                print(f"  - [{note['id']}] {note['title']} ({created})")
                
                # Show snippet of matching content
                max_snippet_length = 100
                content = note["content"]
                
                # Find the query in the content
                query_pos = content.lower().find(query.lower())
                if query_pos != -1:
                    start = max(0, query_pos - 20)
                    end = min(len(content), query_pos + len(query) + 60)
                    snippet = content[start:end]
                    
                    # Add ellipsis if truncated
                    if start > 0:
                        snippet = "..." + snippet
                    if end < len(content):
                        snippet += "..."
                    
                    print(f"    {snippet}")
                print()
        
        elif sub_command == 'get':
            # Get a specific note
            if len(parts) < 2:
                print("Error: Please provide a note ID.")
                return
            
            note_id = parts[1]
            note = self.notes_manager.get_note(note_id)
            
            if not note:
                print(f"Note with ID '{note_id}' not found.")
                return
            
            print(f"\n{note['content']}")
        
        elif sub_command == 'context':
            # Show notes related to a file
            if len(parts) < 2:
                print("Error: Please provide a file path.")
                return
            
            file_path = parts[1]
            
            if not os.path.exists(file_path):
                print(f"File '{file_path}' does not exist.")
                return
            
            notes = self.notes_manager.get_context_notes("file_path", file_path)
            
            if not notes:
                print(f"No notes found for file '{file_path}'.")
                return
            
            print(f"\nFound {len(notes)} notes for file '{file_path}':")
            for note in notes:
                created = datetime.fromtimestamp(note["created"]).strftime("%Y-%m-%d %H:%M")
                print(f"  - [{note['id']}] {note['title']} ({created})")
                
                # Show brief content snippet
                content_lines = note["content"].split("\n")
                snippet = "\n    ".join(content_lines[:3])
                if len(content_lines) > 3:
                    snippet += "\n    ..."
                
                print(f"    {snippet}\n")
        
        else:
            print(f"Unknown note command: {sub_command}")
            print("Available commands: save, list, search, get, context")
    
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
                                relevant_lines = []
                            elif relevant_lines or line.startswith("## User"):
                                relevant_lines.append(line)
                        
                        snippet = "\n  ".join(relevant_lines[:5])
                        if len(relevant_lines) > 5:
                            snippet += "\n  ..."
                        
                        context += f"  {snippet}\n\n"
                    
                    return context
        
        # Search for keywords in notes
        words = re.findall(r'\b\w{4,}\b', user_input.lower())
        for word in words:
            if len(word) < 4:
                continue
                
            notes = self.notes_manager.search_notes(word)
            if notes:
                # Format notes for context
                context = f"Notes related to '{word}':\n"
                for note in notes[:2]:  # Limit to 2 notes per keyword
                    context += f"- {note['title']}:\n"
                    
                    # Get a brief snippet around the keyword
                    content = note["content"]
                    keyword_pos = content.lower().find(word.lower())
                    if keyword_pos != -1:
                        start = max(0, keyword_pos - 40)
                        end = min(len(content), keyword_pos + len(word) + 100)
                        snippet = content[start:end]
                        
                        # Add ellipsis if truncated
                        if start > 0:
                            snippet = "..." + snippet
                        if end < len(content):
                            snippet += "..."
                        
                        context += f"  {snippet}\n\n"
                
                return context
        
        return None
    
    def _analyze_file(self, file_path: str):
        """
        Analyze a file and print the results.
        
        Args:
            file_path: Path to the file
        """
        if not os.path.exists(file_path):
            print(f"Error: File '{file_path}' does not exist.")
            return
        
        print(f"Analyzing '{file_path}'...")
        
        # Get file content and language
        content, language = self.file_service.get_file_content(file_path)
        
        if not content:
            print(f"Error: Could not read file '{file_path}'")
            return
        
        # Analyze the code
        try:
            from llm_code_assistant.assistant.code_analyzer import CodeAnalyzer
            analyzer = CodeAnalyzer(self.llm_service, self.file_service)
            result = analyzer.analyze_file(file_path)
            
            print("\nAnalysis Result:")
            print("---------------")
            print(result)
            
            # Ask to save as a note
            save = input("\nSave this analysis as a note? (y/n): ")
            if save.lower() == 'y':
                title = input("Enter note title: ")
                
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
                
                print(f"Note saved with ID: {note_id}")
            
            # Add to conversation history
            self.conversation_history.append(("user", f"Analyze this file: {file_path}"))
            self.conversation_history.append(("assistant", f"Here's my analysis of '{file_path}':\n\n{result}"))
        except Exception as e:
            print(f"Error analyzing file: {str(e)}")
    
    def _fix_file(self, file_path: str):
        """
        Fix a file and print the results.
        
        Args:
            file_path: Path to the file
        """
        if not os.path.exists(file_path):
            print(f"Error: File '{file_path}' does not exist.")
            return
        
        print(f"Analyzing and fixing '{file_path}'...")
        
        try:
            # First analyze the file
            from llm_code_assistant.assistant.code_analyzer import CodeAnalyzer
            analyzer = CodeAnalyzer(self.llm_service, self.file_service)
            analysis_result = analyzer.analyze_file(file_path)
            
            print("\nAnalysis Result:")
            print("---------------")
            print(analysis_result)
            
            # Generate fixes
            from llm_code_assistant.assistant.code_fixer import CodeFixer
            fixer = CodeFixer(self.llm_service, self.file_service)
            fixes = fixer.generate_fixes(file_path, analysis_result)
            
            print("\nSuggested Fixes:")
            print("---------------")
            print(fixes)
            
            # Ask for confirmation to apply fixes
            response = input("\nDo you want to apply these fixes? (y/n): ")
            if response.lower() == 'y':
                result = fixer.apply_fixes(file_path, fixes)
                print(result)
                
                # Ask to save as a note
                save = input("\nSave this fix as a note? (y/n): ")
                if save.lower() == 'y':
                    title = input("Enter note title: ")
                    
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
                    
                    print(f"Note saved with ID: {note_id}")
            
            # Add to conversation history
            self.conversation_history.append(("user", f"Fix this file: {file_path}"))
            self.conversation_history.append(("assistant", f"I've analyzed '{file_path}' and applied fixes. Here's the result:\n\n{fixes}"))
        except Exception as e:
            print(f"Error fixing file: {str(e)}")
    
    def _show_file(self, file_path: str):
        """
        Show the contents of a file.
        
        Args:
            file_path: Path to the file
        """
        if not os.path.exists(file_path):
            print(f"Error: File '{file_path}' does not exist.")
            return
        
        # Get file content
        content, language = self.file_service.get_file_content(file_path)
        
        if not content:
            print(f"Error: Could not read file '{file_path}'")
            return
        
        # Print the file content
        print(f"\nContents of '{file_path}':")
        print("----------------------------")
        print(content)
        
        # Add to conversation history
        self.conversation_history.append(("user", f"Show me the contents of this file: {file_path}"))
        self.conversation_history.append(("assistant", f"Here's the content of '{file_path}':\n\n```\n{content}\n```"))
    
    def _check_for_code_generation(self, response: str):
        """
        Check if the response contains generated code that should be saved.
        
        Args:
            response: The LLM response
        """
        # Look for file paths and code blocks
        file_path_pattern = r"([a-zA-Z0-9_\-/.]+\.[a-zA-Z0-9]+):"
        file_paths = re.findall(file_path_pattern, response)
        
        if not file_paths:
            return
        
        # Extract code blocks
        code_block_pattern = r"```(?:\w+)?\n([\s\S]*?)\n```"
        code_blocks = re.findall(code_block_pattern, response)
        
        if not code_blocks or len(code_blocks) != len(file_paths):
            return
        
        # Ask if the user wants to save the generated code
        print("\nI found generated code that could be saved to files:")
        for i, path in enumerate(file_paths):
            print(f"  {i+1}. {path}")
        
        save = input("Do you want to save these files? (y/n): ")
        if save.lower() != 'y':
            return
        
        # Save the files
        saved_files = []
        for i, path in enumerate(file_paths):
            try:
                if i < len(code_blocks):
                    # Create directory if it doesn't exist
                    directory = os.path.dirname(path)
                    if directory and not os.path.exists(directory):
                        os.makedirs(directory)
                    
                    # Write content to file
                    with open(path, 'w') as f:
                        f.write(code_blocks[i])
                    
                    saved_files.append(path)
            except Exception as e:
                print(f"Error saving '{path}': {str(e)}")
        
        if saved_files:
            print(f"Saved {len(saved_files)} files:")
            for path in saved_files:
                print(f"  - {path}")
            
            # Ask to save the code generation as a note
            save_note = input("\nSave this code generation as a note? (y/n): ")
            if save_note.lower() == 'y':
                title = input("Enter note title: ")
                
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                note_content = f"# {title}\n\n"
                note_content += f"Generated code\n"
                note_content += f"Created: {timestamp}\n\n"
                note_content += "## Generated Files\n"
                
                for i, path in enumerate(saved_files):
                    note_content += f"\n### {path}\n"
                    note_content += "```\n"
                    if i < len(code_blocks):
                        note_content += code_blocks[i]
                    note_content += "\n```\n"
                
                # Get the last user message as context
                last_user_message = None
                for i in range(len(self.conversation_history) - 1, -1, -1):
                    role, content = self.conversation_history[i]
                    if role == "user":
                        last_user_message = content
                        break
                
                if last_user_message:
                    note_content += f"\n## Request\n{last_user_message}\n"
                
                note_id = self.notes_manager.add_note(
                    title=title,
                    content=note_content,
                    tags=["code-generation"],
                    context={"generated_files": ",".join(saved_files)}
                )
                
                print(f"Note saved with ID: {note_id}")
