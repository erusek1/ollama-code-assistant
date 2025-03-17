"""
GUI Application - A simple Tkinter GUI for the LLM Code Assistant
"""

import os
import re
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from typing import Optional, List, Tuple

from services.llm_service import LLMService
from services.file_service import FileService
from assistant.code_analyzer import CodeAnalyzer
from assistant.code_fixer import CodeFixer
from assistant.code_generator import CodeGenerator
from utils.notes_manager import NotesManager


class Application:
    """Tkinter GUI application for the LLM Code Assistant."""
    
    def __init__(self, llm_service: LLMService, file_service: FileService):
        """
        Initialize the application.
        
        Args:
            llm_service: LLM service
            file_service: File service
        """
        self.llm_service = llm_service
        self.file_service = file_service
        self.code_analyzer = CodeAnalyzer(llm_service, file_service)
        self.code_fixer = CodeFixer(llm_service, file_service)
        self.code_generator = CodeGenerator(llm_service, file_service)
        self.notes_manager = NotesManager()
        
        self.root = None
        self.notebook = None
        self.chat_messages = []
    
    def run(self):
        """Run the application."""
        self.root = tk.Tk()
        self.root.title("LLM Code Assistant")
        self.root.geometry("900x700")
        
        # Create tabbed interface
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self._create_analyze_tab()
        self._create_fix_tab()
        self._create_generate_tab()
        self._create_chat_tab()
        
        # Set up GUI theme
        style = ttk.Style()
        style.configure("TButton", padding=6, relief="flat", background="#ccc")
        style.configure("TLabel", padding=6)
        style.configure("TNotebook", background="#f0f0f0")
        style.configure("TNotebook.Tab", padding=[10, 4], font=('Arial', 10))
        
        # Start the main loop
        self.root.mainloop()
    
    def _create_analyze_tab(self):
        """Create the Analyze tab."""
        analyze_tab = ttk.Frame(self.notebook)
        self.notebook.add(analyze_tab, text="Analyze Code")
        
        # File selection
        file_frame = ttk.Frame(analyze_tab)
        file_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(file_frame, text="File or Directory:").pack(side=tk.LEFT, padx=5)
        self.analyze_path_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.analyze_path_var, width=50).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(file_frame, text="Browse", command=self._browse_analyze_path).pack(side=tk.LEFT, padx=5)
        
        # Results area
        result_frame = ttk.Frame(analyze_tab)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.analyze_result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, font=("Courier", 10))
        self.analyze_result_text.pack(fill=tk.BOTH, expand=True)
        self.analyze_result_text.config(state=tk.DISABLED)
        
        # Buttons
        button_frame = ttk.Frame(analyze_tab)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="Analyze", command=self._analyze_file).pack(side=tk.RIGHT, padx=5)
    
    def _create_fix_tab(self):
        """Create the Fix tab."""
        fix_tab = ttk.Frame(self.notebook)
        self.notebook.add(fix_tab, text="Fix Code")
        
        # File selection
        file_frame = ttk.Frame(fix_tab)
        file_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(file_frame, text="File:").pack(side=tk.LEFT, padx=5)
        self.fix_path_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.fix_path_var, width=50).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(file_frame, text="Browse", command=self._browse_fix_path).pack(side=tk.LEFT, padx=5)
        
        # Analysis and fixed code areas
        paned_window = ttk.PanedWindow(fix_tab, orient=tk.VERTICAL)
        paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Analysis frame
        analysis_frame = ttk.LabelFrame(paned_window, text="Analysis")
        paned_window.add(analysis_frame, weight=1)
        
        self.fix_analysis_text = scrolledtext.ScrolledText(analysis_frame, wrap=tk.WORD, font=("Courier", 10))
        self.fix_analysis_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.fix_analysis_text.config(state=tk.DISABLED)
        
        # Fixed code frame
        fixed_frame = ttk.LabelFrame(paned_window, text="Fixed Code")
        paned_window.add(fixed_frame, weight=1)
        
        self.fix_code_text = scrolledtext.ScrolledText(fixed_frame, wrap=tk.WORD, font=("Courier", 10))
        self.fix_code_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.fix_code_text.config(state=tk.DISABLED)
        
        # Buttons
        button_frame = ttk.Frame(fix_tab)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="Apply Fixes", command=self._apply_fixes).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Generate Fixes", command=self._generate_fixes).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Analyze", command=self._analyze_fix_file).pack(side=tk.RIGHT, padx=5)
    
    def _create_generate_tab(self):
        """Create the Generate tab."""
        generate_tab = ttk.Frame(self.notebook)
        self.notebook.add(generate_tab, text="Generate Code")
        
        # Description frame
        desc_frame = ttk.LabelFrame(generate_tab, text="Description")
        desc_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=10)
        
        # Language selection
        lang_frame = ttk.Frame(desc_frame)
        lang_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(lang_frame, text="Language:").pack(side=tk.LEFT, padx=5)
        self.language_var = tk.StringVar(value="python")
        language_combo = ttk.Combobox(lang_frame, textvariable=self.language_var, 
                                    values=["python", "javascript", "java", "c++", "csharp", "go", "rust"])
        language_combo.pack(side=tk.LEFT, padx=5)
        
        # Description text
        self.description_text = scrolledtext.ScrolledText(desc_frame, wrap=tk.WORD, height=6, font=("Arial", 10))
        self.description_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Results area
        result_frame = ttk.LabelFrame(generate_tab, text="Generated Code")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.generate_result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, font=("Courier", 10))
        self.generate_result_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.generate_result_text.config(state=tk.DISABLED)
        
        # Buttons
        button_frame = ttk.Frame(generate_tab)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="Save Code", command=self._save_generated_code).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Generate", command=self._generate_code).pack(side=tk.RIGHT, padx=5)
    
    def _create_chat_tab(self):
        """Create the Chat tab."""
        chat_tab = ttk.Frame(self.notebook)
        self.notebook.add(chat_tab, text="Chat Assistant")
        
        # Chat history frame
        history_frame = ttk.LabelFrame(chat_tab, text="Conversation")
        history_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.chat_history_text = scrolledtext.ScrolledText(history_frame, wrap=tk.WORD, font=("Arial", 10))
        self.chat_history_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.chat_history_text.config(state=tk.DISABLED)
        
        # Input frame
        input_frame = ttk.Frame(chat_tab)
        input_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.chat_input_text = scrolledtext.ScrolledText(input_frame, wrap=tk.WORD, height=4, font=("Arial", 10))
        self.chat_input_text.pack(fill=tk.X, expand=True, side=tk.LEFT, padx=5)
        self.chat_input_text.bind("<Control-Return>", lambda event: self._send_chat_message())
        
        ttk.Button(input_frame, text="Send", command=self._send_chat_message).pack(side=tk.RIGHT, padx=5)
    
    def _browse_analyze_path(self):
        """Open a file dialog to select a file or directory for analysis."""
        path = filedialog.askopenfilename(title="Select File") or \
            filedialog.askdirectory(title="Select Directory")
        
        if path:
            self.analyze_path_var.set(path)
    
    def _browse_fix_path(self):
        """Open a file dialog to select a file for fixing."""
        path = filedialog.askopenfilename(title="Select File")
        
        if path:
            self.fix_path_var.set(path)
    
    def _analyze_file(self):
        """Analyze the selected file or directory."""
        path = self.analyze_path_var.get()
        
        if not path:
            messagebox.showerror("Error", "Please select a file or directory")
            return
        
        if not os.path.exists(path):
            messagebox.showerror("Error", f"Path '{path}' does not exist")
            return
        
        # Clear the result text
        self.analyze_result_text.config(state=tk.NORMAL)
        self.analyze_result_text.delete(1.0, tk.END)
        self.analyze_result_text.insert(tk.END, f"Analyzing {path}...\n\n")
        self.analyze_result_text.config(state=tk.DISABLED)
        
        # Run analysis in a separate thread
        def run_analysis():
            try:
                if os.path.isfile(path):
                    result = self.code_analyzer.analyze_file(path)
                    
                    # Update the result text
                    self.analyze_result_text.config(state=tk.NORMAL)
                    self.analyze_result_text.delete(1.0, tk.END)
                    self.analyze_result_text.insert(tk.END, result)
                    self.analyze_result_text.config(state=tk.DISABLED)
                else:
                    results = self.code_analyzer.analyze_directory(path)
                    
                    # Update the result text
                    self.analyze_result_text.config(state=tk.NORMAL)
                    self.analyze_result_text.delete(1.0, tk.END)
                    
                    for file_path, result in results.items():
                        self.analyze_result_text.insert(tk.END, f"\n{'=' * 30}\nAnalysis of {file_path}:\n{'=' * 30}\n")
                        self.analyze_result_text.insert(tk.END, result)
                        self.analyze_result_text.insert(tk.END, "\n\n")
                    
                    self.analyze_result_text.config(state=tk.DISABLED)
            except Exception as e:
                messagebox.showerror("Error", f"Error analyzing code: {str(e)}")
                
                self.analyze_result_text.config(state=tk.NORMAL)
                self.analyze_result_text.delete(1.0, tk.END)
                self.analyze_result_text.insert(tk.END, f"Error: {str(e)}")
                self.analyze_result_text.config(state=tk.DISABLED)
        
        thread = threading.Thread(target=run_analysis)
        thread.daemon = True
        thread.start()
    
    def _analyze_fix_file(self):
        """Analyze the selected file for fixing."""
        path = self.fix_path_var.get()
        
        if not path:
            messagebox.showerror("Error", "Please select a file")
            return
        
        if not os.path.exists(path) or not os.path.isfile(path):
            messagebox.showerror("Error", f"File '{path}' does not exist")
            return
        
        # Clear the analysis text
        self.fix_analysis_text.config(state=tk.NORMAL)
        self.fix_analysis_text.delete(1.0, tk.END)
        self.fix_analysis_text.insert(tk.END, f"Analyzing {path}...\n\n")
        self.fix_analysis_text.config(state=tk.DISABLED)
        
        # Run analysis in a separate thread
        def run_analysis():
            try:
                result = self.code_analyzer.analyze_file(path)
                
                # Update the analysis text
                self.fix_analysis_text.config(state=tk.NORMAL)
                self.fix_analysis_text.delete(1.0, tk.END)
                self.fix_analysis_text.insert(tk.END, result)
                self.fix_analysis_text.config(state=tk.DISABLED)
            except Exception as e:
                messagebox.showerror("Error", f"Error analyzing code: {str(e)}")
                
                self.fix_analysis_text.config(state=tk.NORMAL)
                self.fix_analysis_text.delete(1.0, tk.END)
                self.fix_analysis_text.insert(tk.END, f"Error: {str(e)}")
                self.fix_analysis_text.config(state=tk.DISABLED)
        
        thread = threading.Thread(target=run_analysis)
        thread.daemon = True
        thread.start()
    
    def _generate_fixes(self):
        """Generate fixes for the analyzed file."""
        path = self.fix_path_var.get()
        
        if not path:
            messagebox.showerror("Error", "Please select a file")
            return
        
        if not os.path.exists(path) or not os.path.isfile(path):
            messagebox.showerror("Error", f"File '{path}' does not exist")
            return
        
        # Get the analysis result
        analysis_result = self.fix_analysis_text.get(1.0, tk.END)
        
        if not analysis_result.strip():
            messagebox.showerror("Error", "Please analyze the file first")
            return
        
        # Clear the fixed code text
        self.fix_code_text.config(state=tk.NORMAL)
        self.fix_code_text.delete(1.0, tk.END)
        self.fix_code_text.insert(tk.END, f"Generating fixes...\n\n")
        self.fix_code_text.config(state=tk.DISABLED)
        
        # Run fix generation in a separate thread
        def run_fix_generation():
            try:
                fixes = self.code_fixer.generate_fixes(path, analysis_result)
                
                # Extract the code block
                code_block = self._extract_code_block(fixes)
                
                # Update the fixed code text
                self.fix_code_text.config(state=tk.NORMAL)
                self.fix_code_text.delete(1.0, tk.END)
                self.fix_code_text.insert(tk.END, code_block if code_block else fixes)
                self.fix_code_text.config(state=tk.DISABLED)
            except Exception as e:
                messagebox.showerror("Error", f"Error generating fixes: {str(e)}")
                
                self.fix_code_text.config(state=tk.NORMAL)
                self.fix_code_text.delete(1.0, tk.END)
                self.fix_code_text.insert(tk.END, f"Error: {str(e)}")
                self.fix_code_text.config(state=tk.DISABLED)
        
        thread = threading.Thread(target=run_fix_generation)
        thread.daemon = True
        thread.start()
    
    def _apply_fixes(self):
        """Apply the generated fixes to the file."""
        path = self.fix_path_var.get()
        
        if not path:
            messagebox.showerror("Error", "Please select a file")
            return
        
        if not os.path.exists(path) or not os.path.isfile(path):
            messagebox.showerror("Error", f"File '{path}' does not exist")
            return
        
        # Get the fixed code
        fixed_code = self.fix_code_text.get(1.0, tk.END)
        
        if not fixed_code.strip():
            messagebox.showerror("Error", "No fixes to apply")
            return
        
        # Confirm application of fixes
        if not messagebox.askyesno("Confirm", "Are you sure you want to apply these fixes?"):
            return
        
        try:
            result = self.code_fixer.apply_fixes(path, fixed_code)
            messagebox.showinfo("Success", result)
        except Exception as e:
            messagebox.showerror("Error", f"Error applying fixes: {str(e)}")
    
    def _generate_code(self):
        """Generate code from the description."""
        description = self.description_text.get(1.0, tk.END)
        language = self.language_var.get()
        
        if not description.strip():
            messagebox.showerror("Error", "Please enter a description")
            return
        
        # Clear the result text
        self.generate_result_text.config(state=tk.NORMAL)
        self.generate_result_text.delete(1.0, tk.END)
        self.generate_result_text.insert(tk.END, f"Generating {language} code...\n\n")
        self.generate_result_text.config(state=tk.DISABLED)
        
        # Run code generation in a separate thread
        def run_code_generation():
            try:
                result = self.code_generator.generate_code(description, language)
                
                # Update the result text
                self.generate_result_text.config(state=tk.NORMAL)
                self.generate_result_text.delete(1.0, tk.END)
                self.generate_result_text.insert(tk.END, result)
                self.generate_result_text.config(state=tk.DISABLED)
            except Exception as e:
                messagebox.showerror("Error", f"Error generating code: {str(e)}")
                
                self.generate_result_text.config(state=tk.NORMAL)
                self.generate_result_text.delete(1.0, tk.END)
                self.generate_result_text.insert(tk.END, f"Error: {str(e)}")
                self.generate_result_text.config(state=tk.DISABLED)
        
        thread = threading.Thread(target=run_code_generation)
        thread.daemon = True
        thread.start()
    
    def _save_generated_code(self):
        """Save the generated code to files."""
        generated_code = self.generate_result_text.get(1.0, tk.END)
        
        if not generated_code.strip():
            messagebox.showerror("Error", "No code to save")
            return
        
        # Extract file paths and code blocks
        file_paths, code_blocks = self._extract_files_from_response(generated_code)
        
        if file_paths and code_blocks and len(file_paths) == len(code_blocks):
            # Ask for the base directory
            base_dir = filedialog.askdirectory(title="Select Base Directory")
            
            if not base_dir:
                return
            
            # Save the files
            saved_files = []
            for path, code in zip(file_paths, code_blocks):
                full_path = os.path.join(base_dir, path)
                
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                # Write content to file
                with open(full_path, 'w') as f:
                    f.write(code)
                
                saved_files.append(full_path)
            
            messagebox.showinfo("Success", f"Saved {len(saved_files)} files")
        else:
            # Save as a single file
            file_path = filedialog.asksaveasfilename(title="Save Code", defaultextension=f".{self.language_var.get()}")
            
            if not file_path:
                return
            
            with open(file_path, 'w') as f:
                f.write(generated_code)
            
            messagebox.showinfo("Success", f"Saved code to {file_path}")
    
    def _send_chat_message(self):
        """Send a chat message to the LLM."""
        message = self.chat_input_text.get(1.0, tk.END).strip()
        
        if not message:
            return
        
        # Add the message to the chat history
        self.chat_history_text.config(state=tk.NORMAL)
        self.chat_history_text.insert(tk.END, f"\nYou: {message}\n")
        self.chat_history_text.see(tk.END)
        self.chat_history_text.config(state=tk.DISABLED)
        
        # Clear the input text
        self.chat_input_text.delete(1.0, tk.END)
        
        # Add to conversation history
        if not self.chat_messages:
            self.chat_messages.append(("system", "You are a helpful AI assistant for analyzing and generating code."))
        
        self.chat_messages.append(("user", message))
        
        # Run LLM response in a separate thread
        def run_chat_response():
            try:
                # Get response from LLM
                response = self.llm_service.continue_conversation(self.chat_messages)
                
                # Add to conversation history
                self.chat_messages.append(("assistant", response))
                
                # Update the chat history
                self.chat_history_text.config(state=tk.NORMAL)
                self.chat_history_text.insert(tk.END, f"\nAssistant: {response}\n")
                self.chat_history_text.see(tk.END)
                self.chat_history_text.config(state=tk.DISABLED)
                
                # Check for code generation
                file_paths, code_blocks = self._extract_files_from_response(response)
                
                if file_paths and code_blocks and len(file_paths) == len(code_blocks):
                    if messagebox.askyesno("Save Files", "Would you like to save the generated files?"):
                        # Ask for the base directory
                        base_dir = filedialog.askdirectory(title="Select Base Directory")
                        
                        if not base_dir:
                            return
                        
                        # Save the files
                        saved_files = []
                        for path, code in zip(file_paths, code_blocks):
                            full_path = os.path.join(base_dir, path)
                            
                            # Create directory if it doesn't exist
                            os.makedirs(os.path.dirname(full_path), exist_ok=True)
                            
                            # Write content to file
                            with open(full_path, 'w') as f:
                                f.write(code)
                            
                            saved_files.append(full_path)
                        
                        messagebox.showinfo("Success", f"Saved {len(saved_files)} files")
            except Exception as e:
                messagebox.showerror("Error", f"Error getting response: {str(e)}")
                
                self.chat_history_text.config(state=tk.NORMAL)
                self.chat_history_text.insert(tk.END, f"\nError: {str(e)}\n")
                self.chat_history_text.see(tk.END)
                self.chat_history_text.config(state=tk.DISABLED)
        
        thread = threading.Thread(target=run_chat_response)
        thread.daemon = True
        thread.start()
    
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
        
        return None
    
    def _extract_files_from_response(self, response: str) -> Tuple[List[str], List[str]]:
        """
        Extract file paths and code blocks from a response.
        
        Args:
            response: LLM response
            
        Returns:
            Tuple of (file_paths, code_blocks)
        """
        # Look for file paths
        file_path_pattern = r"([a-zA-Z0-9_\-/.]+\.[a-zA-Z0-9]+):"
        file_paths = re.findall(file_path_pattern, response)
        
        # Extract code blocks
        code_block_pattern = r"```(?:\w+)?\n([\s\S]*?)\n```"
        code_blocks = re.findall(code_block_pattern, response)
        
        return file_paths, code_blocks