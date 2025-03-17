"""
Prompt Builder - Utility for building prompts for the LLM
"""


class PromptBuilder:
    """Utility class for building prompts for the LLM."""
    
    def build_analysis_prompt(self, code: str, language: str) -> str:
        """
        Build a prompt for analyzing code.
        
        Args:
            code: The code to analyze
            language: The programming language
            
        Returns:
            A prompt for code analysis
        """
        prompt = [
            "You are an expert code reviewer specialized in identifying issues, bugs, and optimization opportunities. "
            "Analyze the following code and provide detailed feedback.",
            "",
            f"Programming Language: {language}",
            "",
            "Code to analyze:",
            "```",
            code,
            "```",
            "",
            "Provide your analysis in this structured format:",
            "## Summary\n[Brief overview of the code and its quality]",
            "## Critical Issues\n[List any bugs, errors, or critical problems]",
            "## Performance Concerns\n[Identify performance bottlenecks or inefficient code]",
            "## Readability & Maintainability\n[Suggestions to improve code structure and readability]",
            "## Security Considerations\n[Highlight any security vulnerabilities or risks]",
            "## Improvement Recommendations\n[Specific actionable suggestions for improvement]"
        ]
        
        return "\n".join(prompt)
    
    def build_fix_prompt(self, code: str, issues: str, language: str) -> str:
        """
        Build a prompt for fixing code issues.
        
        Args:
            code: The original code
            issues: The identified issues
            language: The programming language
            
        Returns:
            A prompt for generating code fixes
        """
        prompt = [
            "You are an expert programmer tasked with improving and fixing the following code based on identified issues. "
            "Provide the complete fixed code.",
            "",
            f"Programming Language: {language}",
            "",
            "Original code:",
            "```",
            code,
            "```",
            "",
            "Issues to address:",
            issues,
            "",
            "Please provide:",
            "1. A summary of changes you're making to address the issues",
            "2. The complete fixed code (not just the changes)",
            "3. Comment your fixes within the code to explain important changes",
            "",
            "Present the full fixed code inside a single code block marked with triple backticks."
        ]
        
        return "\n".join(prompt)
    
    def build_generation_prompt(self, description: str, language: str) -> str:
        """
        Build a prompt for generating code from a description.
        
        Args:
            description: Description of the code to generate
            language: The programming language
            
        Returns:
            A prompt for code generation
        """
        prompt = [
            "You are an expert developer tasked with generating high-quality, production-ready code based on the following requirements.",
            "",
            f"Programming Language: {language}",
            "",
            "Requirements:",
            description,
            "",
            "Please generate complete, well-structured code with the following characteristics:",
            "- Include proper error handling",
            "- Add comprehensive comments explaining complex sections",
            "- Follow best practices and design patterns for this language",
            "- Optimize for readability and maintainability",
            "- Include necessary imports/dependencies",
            "",
            "For each file, start with the file path, followed by the code in a code block with triple backticks."
        ]
        
        return "\n".join(prompt)
    
    def build_file_structure_prompt(self, description: str) -> str:
        """
        Build a prompt for generating a file structure from a description.
        
        Args:
            description: Description of the program to generate
            
        Returns:
            A prompt for file structure generation
        """
        prompt = [
            "You are a software architecture expert. Based on the following program description, "
            "generate a well-organized file structure including all necessary files and directories.",
            "",
            "Program Description:",
            description,
            "",
            "Please provide the file structure in the following format:",
            "```",
            "project_root/",
            "  ├── file1.ext         # Description of file1",
            "  ├── directory/",
            "  │   ├── file2.ext     # Description of file2",
            "  │   └── file3.ext     # Description of file3",
            "  └── file4.ext         # Description of file4",
            "```",
            "",
            "After the file structure, provide a brief explanation of the overall architecture and how the components work together."
        ]
        
        return "\n".join(prompt)
