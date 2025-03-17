"""
Code Analyzer - Analyze code for issues and improvement opportunities
"""

import os
from typing import Dict, List, Optional
from pathlib import Path

from llm_code_assistant.services.llm_service import LLMService
from llm_code_assistant.services.file_service import FileService


class CodeAnalyzer:
    """Analyzes code for issues and improvement opportunities."""
    
    def __init__(self, llm_service: LLMService, file_service: FileService):
        """
        Initialize the code analyzer.
        
        Args:
            llm_service: LLM service for code analysis
            file_service: File service for file operations
        """
        self.llm_service = llm_service
        self.file_service = file_service
    
    def analyze_file(self, file_path: str) -> str:
        """
        Analyze a single file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Analysis result as a string
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
        
        # Analyze the code
        try:
            print(f"Analyzing {file_path}...")
            analysis_result = self.llm_service.analyze_code(content, language)
            return analysis_result
        except Exception as e:
            return f"Error analyzing file: {str(e)}"
    
    def analyze_directory(self, directory_path: str, file_patterns: Optional[List[str]] = None) -> Dict[str, str]:
        """
        Analyze all files in a directory.
        
        Args:
            directory_path: Path to the directory
            file_patterns: List of file patterns to include (e.g., ["*.py", "*.js"])
            
        Returns:
            Dictionary of file paths and their analysis results
        """
        results = {}
        
        # Get all files in the directory
        files = self.file_service.get_all_files(
            directory_path, 
            include_patterns=file_patterns or ["*.*"]
        )
        
        # Analyze each file
        for file_path, content in files.items():
            language = self.file_service.determine_language(file_path)
            
            try:
                print(f"Analyzing {file_path}...")
                results[file_path] = self.llm_service.analyze_code(content, language)
            except Exception as e:
                results[file_path] = f"Error analyzing file: {str(e)}"
        
        return results
    
    def analyze_project(self, directory_path: str) -> str:
        """
        Analyze a project as a whole, providing a summary and highlights of issues.
        
        Args:
            directory_path: Path to the project directory
            
        Returns:
            Project analysis summary
        """
        # First, analyze individual files
        file_results = self.analyze_directory(directory_path)
        
        # Now, create a prompt for the LLM to analyze the project as a whole
        prompt = [
            "You are an expert code reviewer analyzing an entire project. Based on the following individual file analyses, ",
            "provide a comprehensive project-level analysis that identifies:",
            "1. Overall code quality assessment",
            "2. Common patterns of issues across files",
            "3. Architectural concerns or improvements",
            "4. Project-wide recommendations",
            "",
            "Individual file analyses:",
        ]
        
        # Add summaries of each file analysis (limit to avoid token limits)
        for file_path, analysis in file_results.items():
            # Extract just the summary section to keep the prompt manageable
            summary = self._extract_summary(analysis)
            file_name = os.path.basename(file_path)
            prompt.append(f"\n### {file_name}\n{summary}")
        
        # Request project-level analysis
        try:
            result = self.llm_service.send_request("\n".join(prompt))
            return result
        except Exception as e:
            return f"Error generating project analysis: {str(e)}"
    
    def _extract_summary(self, analysis: str, max_length: int = 300) -> str:
        """
        Extract the summary section from an analysis.
        
        Args:
            analysis: The full analysis text
            max_length: Maximum length of the summary
            
        Returns:
            The summary section or a truncated version of the analysis
        """
        # Try to find the Summary section
        if "## Summary" in analysis:
            summary_start = analysis.find("## Summary")
            next_section = analysis.find("##", summary_start + 10)
            
            if next_section > -1:
                summary = analysis[summary_start:next_section].strip()
            else:
                summary = analysis[summary_start:].strip()
            
            return summary
        
        # If no Summary section, just truncate the analysis
        return analysis[:max_length] + "..." if len(analysis) > max_length else analysis