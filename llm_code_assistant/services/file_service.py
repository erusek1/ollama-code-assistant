"""
File Service - Handle file operations for code analysis and management
"""

import os
import fnmatch
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional


class FileService:
    """Service for handling file operations."""
    
    # File extensions to programming language mapping
    LANGUAGE_MAP = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".html": "html",
        ".css": "css",
        ".java": "java",
        ".c": "c",
        ".cpp": "cpp",
        ".h": "c",
        ".hpp": "cpp",
        ".cs": "csharp",
        ".go": "go",
        ".rs": "rust",
        ".php": "php",
        ".rb": "ruby",
        ".swift": "swift",
        ".kt": "kotlin",
        ".scala": "scala",
        ".sh": "bash",
        ".json": "json",
        ".xml": "xml",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".md": "markdown",
        ".txt": "plaintext",
        ".sql": "sql"
    }
    
    # Binary file extensions to skip
    BINARY_EXTENSIONS = {
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".ico", 
        ".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx",
        ".zip", ".tar", ".gz", ".7z", ".rar", ".exe", ".dll",
        ".so", ".dylib", ".class", ".pyc", ".pyo", ".o"
    }
    
    def __init__(self, skip_dirs: Set[str] = None, max_file_size: int = 1024 * 100):
        """
        Initialize the file service.
        
        Args:
            skip_dirs: Set of directory names to skip (default: [".git", "__pycache__", "node_modules"])
            max_file_size: Maximum file size in bytes to process (default: 100KB)
        """
        self.skip_dirs = skip_dirs or {".git", "__pycache__", "node_modules", "venv", ".venv", ".env"}
        self.max_file_size = max_file_size
    
    def get_file_content(self, file_path: str) -> Tuple[str, str]:
        """
        Get the content of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (content, language)
        """
        path = Path(file_path)
        
        # Check if file exists
        if not path.exists() or not path.is_file():
            return "", ""
        
        # Get file extension and determine language
        extension = path.suffix.lower()
        language = self.LANGUAGE_MAP.get(extension, "plaintext")
        
        # Check file size
        if path.stat().st_size > self.max_file_size:
            return f"File too large: {path.stat().st_size / 1024:.1f} KB exceeds limit of {self.max_file_size / 1024:.1f} KB", language
        
        # Skip binary files
        if extension in self.BINARY_EXTENSIONS:
            return f"Skipping binary file with extension {extension}", language
        
        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content, language
        except UnicodeDecodeError:
            return f"Skipping binary file (detected during read)", language
        except Exception as e:
            return f"Error reading file: {str(e)}", language
    
    def update_file_content(self, file_path: str, new_content: str) -> bool:
        """
        Update the content of a file.
        
        Args:
            file_path: Path to the file
            new_content: New content to write
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True
        except Exception:
            return False
    
    def create_file(self, file_path: str, content: str) -> bool:
        """
        Create a new file with the given content.
        
        Args:
            file_path: Path to the file
            content: Content to write
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
            
            # Write content to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
        except Exception:
            return False
    
    def get_all_files(self, directory: str, include_patterns: List[str] = None, exclude_patterns: List[str] = None) -> Dict[str, str]:
        """
        Get all files in a directory recursively.
        
        Args:
            directory: Path to the directory
            include_patterns: List of patterns to include (e.g., ["*.py", "*.js"])
            exclude_patterns: List of patterns to exclude (e.g., ["*_test.py", "*.min.js"])
            
        Returns:
            Dictionary of file paths and their content
        """
        files = {}
        
        include_patterns = include_patterns or ["*.*"]
        exclude_patterns = exclude_patterns or []
        
        for root, dirs, filenames in os.walk(directory):
            # Skip directories in self.skip_dirs
            dirs[:] = [d for d in dirs if d not in self.skip_dirs]
            
            for filename in filenames:
                file_path = os.path.join(root, filename)
                
                # Check if file matches include patterns
                included = any(fnmatch.fnmatch(filename, pattern) for pattern in include_patterns)
                
                # Check if file matches exclude patterns
                excluded = any(fnmatch.fnmatch(filename, pattern) for pattern in exclude_patterns)
                
                if included and not excluded:
                    content, _ = self.get_file_content(file_path)
                    if content and not content.startswith("File too large") and not content.startswith("Skipping binary"):
                        files[file_path] = content
        
        return files
    
    def determine_language(self, file_path: str) -> str:
        """
        Determine the programming language from the file extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Programming language name
        """
        extension = Path(file_path).suffix.lower()
        return self.LANGUAGE_MAP.get(extension, "plaintext")
    
    def create_directory(self, directory_path: str) -> bool:
        """
        Create a directory if it doesn't exist.
        
        Args:
            directory_path: Path to the directory
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not os.path.exists(directory_path):
                os.makedirs(directory_path)
            return True
        except Exception:
            return False