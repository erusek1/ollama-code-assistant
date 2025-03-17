"""
Code Fixer - Generate and apply fixes for identified issues
"""

import re
from typing import Optional, Tuple

from llm_code_assistant.services.llm_service import LLMService
from llm_code_assistant.services.file_service import FileService


class CodeFixer:
    """Generates and applies fixes for identified code issues."""
    
    def __init__(self, llm_service: LLMService, file_service: FileService):
        """
        Initialize the code fixer.
        
        Args:
            llm_service: LLM service for code fixing
            file_service: File service for file operations
        """
        self.llm_service = llm_service
        self.file_service = file_service
    
    def generate_fixes(self, file_path: str, analysis_result: str) -> str:
        """
        Generate fixes for a file based on analysis results.
        
        Args:
            file_path: Path to the file
            analysis_result: Analysis results from the CodeAnalyzer
            
        Returns:
            Fixed code as a string
        """
        # Get file content and language
        content, language = self.file_service.get_file_content(file_path)
        
        if not content:
            return f"Error: Could not read file '{file_path}'"
        
        # Skip files that are too large or binary
        if content.startswith("File too large") or content.startswith("Skipping binary"):
            return content
        
        # Check if we have a valid language
        if not language:
            language = self.file_service.determine_language(file_path)
        
        # Generate fixes
        try:
            print(f"Generating fixes for {file_path}...")
            fixed_code = self.llm_service.generate_fixes(content, analysis_result, language)
            return fixed_code
        except Exception as e:
            return f"Error generating fixes: {str(e)}"
    
    def apply_fixes(self, file_path: str, fixed_code: str) -> str:
        """
        Apply the fixed code to the file.
        
        Args:
            file_path: Path to the file
            fixed_code: Fixed code to apply
            
        Returns:
            Success message or error
        """
        # Extract code block if present
        code_block = self._extract_code_block(fixed_code)
        
        if not code_block:
            return "Error: No code block found in the fixes. Cannot apply changes."
        
        # Apply the fixed code
        success = self.file_service.update_file_content(file_path, code_block)
        
        if success:
            return f"Successfully applied fixes to '{file_path}'"
        else:
            return f"Error: Failed to apply fixes to '{file_path}'"
    
    def preview_fixes(self, original_code: str, fixed_code: str) -> str:
        """
        Generate a diff-like preview of the fixes.
        
        Args:
            original_code: Original code
            fixed_code: Fixed code
            
        Returns:
            Diff-like preview as a string
        """
        # Extract code block if present
        code_block = self._extract_code_block(fixed_code)
        
        if not code_block:
            return "Error: No code block found in the fixes."
        
        # Simple line-by-line diff
        orig_lines = original_code.splitlines()
        fixed_lines = code_block.splitlines()
        
        result = []
        result.append("```diff")
        
        # Generate basic diff
        from difflib import unified_diff
        diff = unified_diff(
            orig_lines, 
            fixed_lines, 
            fromfile="Original", 
            tofile="Fixed", 
            lineterm=""
        )
        
        for line in diff:
            result.append(line)
        
        result.append("```")
        
        return "\n".join(result)
    
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
        
        # If no code block found, try to find just the code without the summary
        sections = re.split(r"##\s+", text)
        
        if len(sections) > 1:
            # Try to find section with the code (often the last one)
            for section in reversed(sections):
                if "```" not in section and section.strip():
                    lines = section.strip().splitlines()
                    if len(lines) > 5:  # Assume it's code if it has enough lines
                        return section.strip()
        
        # If still no code block found, just return everything after "Here's the fixed code:" if present
        if "Here's the fixed code:" in text:
            code_start = text.find("Here's the fixed code:")
            return text[code_start + len("Here's the fixed code:"):].strip()
        
        # Last resort: if the text has a lot of newlines, it might be code
        if text.count('\n') > 10:
            return text
        
        return None
    
    def fix_specific_issue(self, file_path: str, issue_description: str) -> Tuple[str, str]:
        """
        Fix a specific issue in a file.
        
        Args:
            file_path: Path to the file
            issue_description: Description of the issue to fix
            
        Returns:
            Tuple of (fixed code, message)
        """
        # Get file content and language
        content, language = self.file_service.get_file_content(file_path)
        
        if not content:
            return "", f"Error: Could not read file '{file_path}'"
        
        # Skip files that are too large or binary
        if content.startswith("File too large") or content.startswith("Skipping binary"):
            return "", content
        
        # Check if we have a valid language
        if not language:
            language = self.file_service.determine_language(file_path)
        
        # Create a specific prompt for fixing this issue
        prompt = [
            f"Fix the following specific issue in this {language} code:",
            "",
            "Issue to fix:",
            issue_description,
            "",
            "Code:",
            "```",
            content,
            "```",
            "",
            "Please provide:",
            "1. A brief explanation of the fix",
            "2. The complete fixed code (not just the changes)",
            "",
            "Present the full fixed code inside a single code block marked with triple backticks."
        ]
        
        # Generate fix
        try:
            response = self.llm_service.send_request("\n".join(prompt))
            fixed_code = self._extract_code_block(response)
            
            if not fixed_code:
                return "", "Error: Could not extract fixed code from the response."
            
            # Get explanation (everything before the code block)
            explanation = response.split("```")[0].strip()
            
            return fixed_code, explanation
        except Exception as e:
            return "", f"Error fixing issue: {str(e)}"