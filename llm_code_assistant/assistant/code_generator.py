"""
Code Generator - Generate code from descriptions and create project structures
"""

import os
import re
from typing import Dict, List, Tuple, Optional
from pathlib import Path

from llm_code_assistant.services.llm_service import LLMService
from llm_code_assistant.services.file_service import FileService
from llm_code_assistant.utils.prompt_builder import PromptBuilder


class CodeGenerator:
    """Generates code and project structures from descriptions."""
    
    def __init__(self, llm_service: LLMService, file_service: FileService):
        """
        Initialize the code generator.
        
        Args:
            llm_service: LLM service for code generation
            file_service: File service for file operations
        """
        self.llm_service = llm_service
        self.file_service = file_service
        self.prompt_builder = PromptBuilder()
        self.conversation_history = []
    
    def generate_code(self, description: str, language: str) -> str:
        """
        Generate code from a description.
        
        Args:
            description: Description of the code to generate
            language: Programming language
            
        Returns:
            Generated code as a string
        """
        try:
            print(f"Generating {language} code...")
            code = self.llm_service.generate_code(description, language)
            return code
        except Exception as e:
            return f"Error generating code: {str(e)}"
    
    def generate_project_structure(self, description: str) -> str:
        """
        Generate a project structure from a description.
        
        Args:
            description: Description of the project
            
        Returns:
            Project structure as a string
        """
        prompt = self.prompt_builder.build_file_structure_prompt(description)
        
        try:
            print("Generating project structure...")
            structure = self.llm_service.send_request(prompt)
            return structure
        except Exception as e:
            return f"Error generating project structure: {str(e)}"
    
    def create_project(self, base_dir: str, project_description: str) -> Tuple[bool, str]:
        """
        Create a project from a description.
        
        Args:
            base_dir: Base directory to create the project in
            project_description: Description of the project
            
        Returns:
            Tuple of (success, message)
        """
        # First, generate the project structure
        structure = self.generate_project_structure(project_description)
        
        # Extract the file structure from the response
        file_structure = self._extract_file_structure(structure)
        
        if not file_structure:
            return False, "Failed to generate a valid project structure."
        
        # Create the base directory if it doesn't exist
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
        
        # Parse the file structure and create files
        created_files = []
        errors = []
        
        # First, extract the project root folder name
        first_line = file_structure.strip().split('\n')[0].strip()
        project_root = first_line.rstrip('/') if first_line.endswith('/') else first_line
        
        # Now, use the LLM to generate each file
        for file_info in self._parse_file_structure(file_structure):
            if file_info['type'] == 'file':
                file_path = os.path.join(base_dir, file_info['path'])
                
                # Skip directories and files without extensions
                if os.path.isdir(file_path) or not os.path.splitext(file_path)[1]:
                    continue
                
                # Determine the language from the file extension
                language = self.file_service.determine_language(file_path)
                
                # Generate code for the file
                description = f"Create a {language} file for: {file_info['description']}\n"
                description += f"File path: {file_info['path']}\n"
                description += f"Within project context: {project_description}"
                
                code = self.generate_code(description, language)
                
                # Extract the code block
                code_block = self._extract_code_block(code)
                
                if code_block:
                    # Create the directory if it doesn't exist
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    
                    # Write the file
                    try:
                        with open(file_path, 'w') as f:
                            f.write(code_block)
                        created_files.append(file_path)
                    except Exception as e:
                        errors.append(f"Error creating {file_path}: {str(e)}")
            elif file_info['type'] == 'directory':
                dir_path = os.path.join(base_dir, file_info['path'])
                try:
                    os.makedirs(dir_path, exist_ok=True)
                except Exception as e:
                    errors.append(f"Error creating directory {dir_path}: {str(e)}")
        
        # Generate summary message
        summary = f"Project created with {len(created_files)} files.\n"
        
        if errors:
            summary += f"\nErrors ({len(errors)}):\n"
            for error in errors[:5]:  # Show only the first 5 errors
                summary += f"- {error}\n"
            if len(errors) > 5:
                summary += f"- ...and {len(errors) - 5} more errors.\n"
        
        success = len(created_files) > 0 and len(errors) < len(created_files)
        return success, summary
    
    def _extract_file_structure(self, text: str) -> Optional[str]:
        """
        Extract the file structure from the LLM response.
        
        Args:
            text: LLM response text
            
        Returns:
            File structure or None if not found
        """
        # Try to find the file structure within triple backticks
        pattern = r"```(?:plaintext)?\n([\s\S]*?)\n```"
        matches = re.findall(pattern, text)
        
        if matches:
            return matches[0]
        
        # If no backticks, look for lines with typical file structure pattern
        lines = text.split('\n')
        structure_lines = []
        started = False
        
        for line in lines:
            # Look for typical directory structure indicators
            if ('/' in line or '\\' in line) and ('#' in line or not structure_lines):
                started = True
                structure_lines.append(line)
            elif started and (line.strip().startswith('│') or line.strip().startswith('├') or line.strip().startswith('└')):
                structure_lines.append(line)
            elif started and not line.strip():
                started = False
        
        if structure_lines:
            return '\n'.join(structure_lines)
        
        return None
    
    def _parse_file_structure(self, structure: str) -> List[Dict[str, str]]:
        """
        Parse the file structure into a list of files and directories.
        
        Args:
            structure: File structure string
            
        Returns:
            List of dictionaries with file information
        """
        result = []
        lines = structure.split('\n')
        
        # Skip the first line (project root)
        current_path = ""
        
        for line in lines[1:]:
            # Skip empty lines
            if not line.strip():
                continue
            
            # Parse the line
            stripped = line.strip()
            
            # Calculate indent level
            indent = len(line) - len(stripped)
            
            # Extract path and description
            if '├──' in stripped or '└──' in stripped or '│' in stripped:
                # Handle ASCII tree structure
                parts = stripped.split('#', 1)
                path_part = parts[0].strip()
                description = parts[1].strip() if len(parts) > 1 else ""
                
                # Extract the file/directory name
                name = path_part.split('─')[-1].strip()
                
                # Determine if it's a file or directory
                is_dir = name.endswith('/')
                name = name.rstrip('/')
                
                # Build the path based on indent level
                path_parts = current_path.split('/')
                path_parts = path_parts[:max(1, indent//2)]
                path_parts.append(name)
                
                new_path = '/'.join(filter(None, path_parts))
                
                if is_dir:
                    new_path += '/'
                    result.append({
                        'type': 'directory',
                        'path': new_path,
                        'description': description
                    })
                else:
                    result.append({
                        'type': 'file',
                        'path': new_path,
                        'description': description
                    })
                
                current_path = new_path
            else:
                # Fallback for other formats
                parts = stripped.split('#', 1)
                path = parts[0].strip()
                description = parts[1].strip() if len(parts) > 1 else ""
                
                if path.endswith('/'):
                    result.append({
                        'type': 'directory',
                        'path': path,
                        'description': description
                    })
                else:
                    result.append({
                        'type': 'file',
                        'path': path,
                        'description': description
                    })
        
        return result
    
    def _extract_code_block(self, text: str) -> Optional[str]:
        """
        Extract code block from text.
        
        Args:
            text: Text containing code block
            
        Returns:
            Code block or None if not found
        """
        # Try to find triple backtick code blocks
        pattern = r"```(?:\w+)?\n([\s\S]*?)\n```"
        matches = re.findall(pattern, text)
        
        if matches:
            return matches[0]
        
        # If no code block found, try to find just the code
        if text.count('\n') > 5:
            return text
        
        return None
    
    def start_interactive_session(self):
        """Start an interactive session for code generation."""
        print("\nCode Generator Interactive Session")
        print("----------------------------------")
        print("Describe what you want to build, and I'll help you create it.")
        print("Type 'exit' to quit, 'create project' to create a project structure.")
        
        self.conversation_history = [
            ("system", "You are a helpful AI assistant for generating code.")
        ]
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                
                if user_input.lower() == 'exit':
                    print("Goodbye!")
                    break
                
                if user_input.lower() == 'create project':
                    project_desc = input("Describe the project you want to create: ").strip()
                    base_dir = input("Enter the base directory path: ").strip()
                    
                    print("\nGenerating project structure...")
                    success, message = self.create_project(base_dir, project_desc)
                    print(message)
                    
                    continue
                
                # Check if it's a request to generate code
                if any(keyword in user_input.lower() for keyword in ["generate", "create", "write", "make", "code"]):
                    language_match = re.search(r"in (\w+)", user_input.lower())
                    language = language_match.group(1) if language_match else None
                    
                    if not language:
                        language = input("What programming language? ").strip().lower()
                    
                    code = self.generate_code(user_input, language)
                    print(f"\nAssistant: Here's the {language} code:\n")
                    print(code)
                else:
                    # Add to conversation history
                    self.conversation_history.append(("user", user_input))
                    
                    # Get response from LLM
                    response = self.llm_service.continue_conversation(self.conversation_history)
                    
                    # Add to conversation history
                    self.conversation_history.append(("assistant", response))
                    
                    print(f"\nAssistant: {response}")
            
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"\nError: {str(e)}")