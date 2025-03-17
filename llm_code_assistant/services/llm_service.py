"""
LLM Service - Interface with Ollama local API
"""

import json
import requests
from typing import List, Tuple, Dict, Optional, Any


class LLMService:
    """Service for interacting with Ollama LLM API."""
    
    def __init__(self, endpoint: str = None, model: str = None):
        """
        Initialize the LLM service.
        
        Args:
            endpoint: The Ollama API endpoint (default: "http://localhost:11434")
            model: The model name to use (default: "codellama:34b")
        """
        self.endpoint = endpoint or "http://localhost:11434"
        self.model = model or "codellama:34b"
        self.headers = {"Content-Type": "application/json"}
    
    def analyze_code(self, code: str, language: str) -> str:
        """
        Analyze code for issues.
        
        Args:
            code: The code to analyze
            language: The programming language
            
        Returns:
            Analysis results as a string
        """
        from llm_code_assistant.utils.prompt_builder import PromptBuilder
        
        prompt_builder = PromptBuilder()
        prompt = prompt_builder.build_analysis_prompt(code, language)
        return self.send_request(prompt)
    
    def generate_fixes(self, code: str, issues: str, language: str) -> str:
        """
        Generate fixes for identified issues.
        
        Args:
            code: The code to fix
            issues: Identified issues
            language: The programming language
            
        Returns:
            Fixed code as a string
        """
        from llm_code_assistant.utils.prompt_builder import PromptBuilder
        
        prompt_builder = PromptBuilder()
        prompt = prompt_builder.build_fix_prompt(code, issues, language)
        return self.send_request(prompt)
    
    def generate_code(self, description: str, language: str) -> str:
        """
        Generate new code based on a description.
        
        Args:
            description: Description of the code to generate
            language: The programming language
            
        Returns:
            Generated code as a string
        """
        from llm_code_assistant.utils.prompt_builder import PromptBuilder
        
        prompt_builder = PromptBuilder()
        prompt = prompt_builder.build_generation_prompt(description, language)
        return self.send_request(prompt)
    
    def continue_conversation(self, messages: List[Tuple[str, str]], new_message: str = "") -> str:
        """
        Continue a conversation with the LLM.
        
        Args:
            messages: Previous messages in the conversation as (role, content) tuples
            new_message: New message to send
            
        Returns:
            LLM response as a string
        """
        # Format messages for Ollama API
        ollama_messages = []
        for role, content in messages:
            # Convert role from OpenAI format to Ollama format if needed
            ollama_role = role
            if role == "assistant": ollama_role = "assistant"
            if role == "user": ollama_role = "user"
            if role == "system": ollama_role = "system"
            
            ollama_messages.append({"role": ollama_role, "content": content})
        
        # Add new message if provided
        if new_message:
            ollama_messages.append({"role": "user", "content": new_message})
        
        # Create request payload for Ollama
        payload = {
            "model": self.model,
            "messages": ollama_messages,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "top_p": 0.95,
                "num_predict": 4000
            }
        }
        
        try:
            response = requests.post(
                f"{self.endpoint}/api/chat",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            message_content = result["message"]["content"]
            return message_content
        except Exception as e:
            error_msg = f"Error communicating with local LLM: {str(e)}\n\n"
            error_msg += "Please ensure Ollama is running with the codellama:34b model installed.\n"
            error_msg += "You can install it with: ollama pull codellama:34b"
            return error_msg
    
    def send_request(self, prompt: str) -> str:
        """
        Send a request to the Ollama API.
        
        Args:
            prompt: The prompt to send
            
        Returns:
            LLM response as a string
        """
        # Create a simple conversation with just this prompt
        messages = [
            ("system", "You are a helpful AI assistant for analyzing and generating code."),
            ("user", prompt)
        ]
        
        return self.continue_conversation(messages)
    
    def verify_connection(self) -> Tuple[bool, str]:
        """
        Verify the Ollama connection and model availability.
        
        Returns:
            Tuple of (success, message)
        """
        try:
            # Check if Ollama is running
            response = requests.get(f"{self.endpoint}/api/tags")
            
            if response.status_code != 200:
                return False, f"Ollama server is not reachable at {self.endpoint}"
            
            # Parse response to check for the model
            data = response.json()
            
            # Verify if our model exists in the list
            models = data.get("models", [])
            model_found = False
            
            for model in models:
                name = model.get("name", "")
                if name and "codellama" in name:
                    model_found = True
                    break
            
            if not model_found:
                return False, "CodeLlama model not found. Please install with 'ollama pull codellama:34b'"
            
            return True, "Ollama is running and CodeLlama model is available"
        except Exception as e:
            return False, f"Error connecting to Ollama: {str(e)}"