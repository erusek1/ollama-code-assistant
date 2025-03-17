"""
Notes Manager - Store and retrieve notes for the LLM Code Assistant
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Union, Any


class NotesManager:
    """Manages notes and memory for the LLM Code Assistant."""
    
    def __init__(self, notes_dir: Optional[str] = None):
        """
        Initialize the notes manager.
        
        Args:
            notes_dir: Directory to store notes (default: ~/.llmcodeassistant/notes)
        """
        if notes_dir is None:
            home_dir = Path.home()
            config_dir = home_dir / ".llmcodeassistant"
            self.notes_dir = config_dir / "notes"
        else:
            self.notes_dir = Path(notes_dir)
        
        # Create the notes directory if it doesn't exist
        self.notes_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize notes index
        self.index_file = self.notes_dir / "index.json"
        self._load_index()
    
    def _load_index(self) -> None:
        """Load the notes index from disk."""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r') as f:
                    self.index = json.load(f)
            except Exception as e:
                print(f"Error loading notes index: {e}")
                self.index = {"notes": []}
        else:
            self.index = {"notes": []}
    
    def _save_index(self) -> None:
        """Save the notes index to disk."""
        try:
            with open(self.index_file, 'w') as f:
                json.dump(self.index, f, indent=2)
        except Exception as e:
            print(f"Error saving notes index: {e}")
    
    def add_note(self, title: str, content: str, tags: Optional[List[str]] = None, 
                 context: Optional[Dict[str, Any]] = None) -> str:
        """
        Add a new note.
        
        Args:
            title: Note title
            content: Note content
            tags: List of tags
            context: Context information (e.g., file path, project name)
            
        Returns:
            Note ID
        """
        # Generate a unique ID for the note
        note_id = f"note_{int(time.time() * 1000)}"
        
        # Create note metadata
        note_meta = {
            "id": note_id,
            "title": title,
            "created": time.time(),
            "updated": time.time(),
            "tags": tags or [],
            "context": context or {}
        }
        
        # Add to index
        self.index["notes"].append(note_meta)
        
        # Save note content
        note_file = self.notes_dir / f"{note_id}.txt"
        with open(note_file, 'w') as f:
            f.write(content)
        
        # Save updated index
        self._save_index()
        
        return note_id
    
    def update_note(self, note_id: str, title: Optional[str] = None, 
                   content: Optional[str] = None, tags: Optional[List[str]] = None, 
                   context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update an existing note.
        
        Args:
            note_id: Note ID
            title: New title (or None to keep existing)
            content: New content (or None to keep existing)
            tags: New tags (or None to keep existing)
            context: New context (or None to keep existing)
            
        Returns:
            True if the note was updated, False otherwise
        """
        # Find note in index
        note_meta = None
        note_index = -1
        
        for i, note in enumerate(self.index["notes"]):
            if note["id"] == note_id:
                note_meta = note
                note_index = i
                break
        
        if note_meta is None:
            return False
        
        # Update metadata
        if title is not None:
            note_meta["title"] = title
        
        if tags is not None:
            note_meta["tags"] = tags
        
        if context is not None:
            note_meta["context"].update(context)
        
        note_meta["updated"] = time.time()
        
        # Update in index
        self.index["notes"][note_index] = note_meta
        
        # Update content if provided
        if content is not None:
            note_file = self.notes_dir / f"{note_id}.txt"
            with open(note_file, 'w') as f:
                f.write(content)
        
        # Save updated index
        self._save_index()
        
        return True
    
    def delete_note(self, note_id: str) -> bool:
        """
        Delete a note.
        
        Args:
            note_id: Note ID
            
        Returns:
            True if the note was deleted, False otherwise
        """
        # Find note in index
        note_index = -1
        
        for i, note in enumerate(self.index["notes"]):
            if note["id"] == note_id:
                note_index = i
                break
        
        if note_index == -1:
            return False
        
        # Remove from index
        self.index["notes"].pop(note_index)
        
        # Delete content file
        note_file = self.notes_dir / f"{note_id}.txt"
        if note_file.exists():
            note_file.unlink()
        
        # Save updated index
        self._save_index()
        
        return True
    
    def get_note(self, note_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a note by ID.
        
        Args:
            note_id: Note ID
            
        Returns:
            Note or None if not found
        """
        # Find note in index
        note_meta = None
        
        for note in self.index["notes"]:
            if note["id"] == note_id:
                note_meta = note
                break
        
        if note_meta is None:
            return None
        
        # Read content
        note_file = self.notes_dir / f"{note_id}.txt"
        if not note_file.exists():
            return None
        
        with open(note_file, 'r') as f:
            content = f.read()
        
        # Build complete note
        note = note_meta.copy()
        note["content"] = content
        
        return note
    
    def list_notes(self, tag: Optional[str] = None, context_key: Optional[str] = None, 
                  context_value: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all notes, optionally filtered by tag or context.
        
        Args:
            tag: Filter by tag
            context_key: Filter by context key
            context_value: Filter by context value
            
        Returns:
            List of note metadata (without content)
        """
        notes = []
        
        for note in self.index["notes"]:
            # Apply filters
            if tag and tag not in note["tags"]:
                continue
            
            if context_key and (context_key not in note["context"] or 
                               (context_value and note["context"][context_key] != context_value)):
                continue
            
            notes.append(note.copy())
        
        # Sort by updated time (newest first)
        notes.sort(key=lambda x: x["updated"], reverse=True)
        
        return notes
    
    def search_notes(self, query: str) -> List[Dict[str, Any]]:
        """
        Search notes by title and content.
        
        Args:
            query: Search query
            
        Returns:
            List of matching notes with metadata and content
        """
        query = query.lower()
        results = []
        
        for note_meta in self.index["notes"]:
            match_title = query in note_meta["title"].lower()
            
            # Read content
            note_file = self.notes_dir / f"{note_meta['id']}.txt"
            if not note_file.exists():
                continue
            
            with open(note_file, 'r') as f:
                content = f.read()
            
            match_content = query in content.lower()
            
            if match_title or match_content:
                note = note_meta.copy()
                note["content"] = content
                results.append(note)
        
        return results
    
    def get_context_notes(self, context_key: str, context_value: str) -> List[Dict[str, Any]]:
        """
        Get notes with specific context.
        
        Args:
            context_key: Context key (e.g., 'file_path', 'project')
            context_value: Context value
            
        Returns:
            List of matching notes with metadata and content
        """
        results = []
        
        for note_meta in self.index["notes"]:
            if context_key in note_meta["context"] and note_meta["context"][context_key] == context_value:
                # Read content
                note_file = self.notes_dir / f"{note_meta['id']}.txt"
                if not note_file.exists():
                    continue
                
                with open(note_file, 'r') as f:
                    content = f.read()
                
                note = note_meta.copy()
                note["content"] = content
                results.append(note)
        
        return results
    
    def get_all_tags(self) -> List[str]:
        """
        Get all unique tags across all notes.
        
        Returns:
            List of tags
        """
        tags = set()
        
        for note in self.index["notes"]:
            for tag in note["tags"]:
                tags.add(tag)
        
        return sorted(list(tags))
    
    def export_notes(self, export_file: str) -> bool:
        """
        Export all notes to a JSON file.
        
        Args:
            export_file: Path to export file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            notes_with_content = []
            
            for note_meta in self.index["notes"]:
                note_file = self.notes_dir / f"{note_meta['id']}.txt"
                if not note_file.exists():
                    continue
                
                with open(note_file, 'r') as f:
                    content = f.read()
                
                note = note_meta.copy()
                note["content"] = content
                notes_with_content.append(note)
            
            with open(export_file, 'w') as f:
                json.dump({"notes": notes_with_content}, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error exporting notes: {e}")
            return False
    
    def import_notes(self, import_file: str) -> int:
        """
        Import notes from a JSON file.
        
        Args:
            import_file: Path to import file
            
        Returns:
            Number of notes imported
        """
        try:
            with open(import_file, 'r') as f:
                imported_data = json.load(f)
            
            if "notes" not in imported_data:
                return 0
            
            count = 0
            for note in imported_data["notes"]:
                if "id" not in note or "title" not in note or "content" not in note:
                    continue
                
                note_id = note["id"]
                title = note["title"]
                content = note["content"]
                tags = note.get("tags", [])
                context = note.get("context", {})
                
                # Check if note already exists
                note_exists = False
                for existing_note in self.index["notes"]:
                    if existing_note["id"] == note_id:
                        note_exists = True
                        break
                
                if note_exists:
                    # Update existing note
                    self.update_note(note_id, title, content, tags, context)
                else:
                    # Create note with specific ID
                    note_meta = {
                        "id": note_id,
                        "title": title,
                        "created": note.get("created", time.time()),
                        "updated": note.get("updated", time.time()),
                        "tags": tags,
                        "context": context
                    }
                    
                    # Add to index
                    self.index["notes"].append(note_meta)
                    
                    # Save note content
                    note_file = self.notes_dir / f"{note_id}.txt"
                    with open(note_file, 'w') as f:
                        f.write(content)
                
                count += 1
            
            # Save updated index
            self._save_index()
            
            return count
        except Exception as e:
            print(f"Error importing notes: {e}")
            return 0
