from difflib import get_close_matches
import requests
import json
from typing import Dict, Union
import tkinter as tk
from tkinter import ttk, messagebox

class DictionaryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dictionary Application")
        self.root.geometry('600x400')
        
        # Initialize dictionary
        self.dictionary = Dictionary()
        
        # Create GUI elements
        self.create_widgets()
    
    def create_widgets(self):
        # Search frame
        search_frame = ttk.Frame(self.root, padding="10")
        search_frame.pack(fill=tk.X)
        
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=40)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.bind('<Return>', lambda e: self.on_search())
        
        search_btn = ttk.Button(search_frame, text="Search", command=self.on_search)
        search_btn.pack(side=tk.LEFT, padx=5)
        
        # Results frame
        results_frame = ttk.Frame(self.root, padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create a scrollable text area
        self.text_area = tk.Text(results_frame, wrap=tk.WORD, state=tk.DISABLED)
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.text_area.yview)
        self.text_area.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_area.pack(fill=tk.BOTH, expand=True)
    
    def on_search(self):
        word = self.search_var.get().strip()
        if not word:
            messagebox.showwarning("Warning", "Please enter a word to search")
            return
        
        result = self.dictionary.lookup(word)
        self.display_result(result)
    
    def display_result(self, result):
        self.text_area.config(state=tk.NORMAL)
        self.text_area.delete(1.0, tk.END)
        
        if 'error' in result:
            self.text_area.insert(tk.END, f"Error: {result['error']}\n\n")
            if result['suggestions']:
                self.text_area.insert(tk.END, "Did you mean:\n")
                for suggestion in result['suggestions']:
                    self.text_area.insert(tk.END, f"- {suggestion}\n")
        else:
            self.text_area.insert(tk.END, f"Definitions for '{result['word']}' (from {result['source']}):\n\n")
            for pos, definitions in result['meanings'].items():
                self.text_area.insert(tk.END, f"{pos.capitalize()}:\n")
                for i, definition in enumerate(definitions[:3], 1):
                    self.text_area.insert(tk.END, f"  {i}. {definition}\n")
                self.text_area.insert(tk.END, "\n")
        
        self.text_area.config(state=tk.DISABLED)

class Dictionary:
    def __init__(self):
        # Try to load local dictionary first
        self.local_dict = self._load_local_dictionary('dictionary.json')
        
    def _load_local_dictionary(self, filepath: str) -> Dict:
        """Load local dictionary file if available"""
        try:
            with open(filepath) as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def lookup(self, word: str) -> Dict:
        """Main lookup method with fallback strategies"""
        word = word.lower()
        
        # 1. Try local dictionary
        if self.local_dict and word in self.local_dict:
            return {
                'word': word,
                'source': 'local',
                'meanings': self.local_dict[word]
            }
        
        # 2. Try web API
        web_result = self._try_web_api(word)
        if web_result:
            return {
                'word': word,
                'source': 'web',
                'meanings': web_result
            }
        
        # 3. Suggest similar words
        suggestions = []
        if self.local_dict:
            suggestions = get_close_matches(
                word, 
                self.local_dict.keys(), 
                n=3, 
                cutoff=0.6
            )
        
        return {
            'error': 'Word not found',
            'suggestions': suggestions
        }

    def _try_web_api(self, word: str) -> Union[Dict, None]:
        """Try free DictionaryAPI with proper error handling"""
        try:
            response = requests.get(
                f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}",
                timeout=3  # 3 second timeout
            )
            if response.status_code == 200:
                return self._parse_api_response(response.json())
        except requests.exceptions.RequestException:
            return None
        return None

    def _parse_api_response(self, data: Dict) -> Dict:
        """Standardize API response format"""
        meanings = {}
        for entry in data:
            for meaning in entry.get('meanings', []):
                pos = meaning.get('partOfSpeech', 'unknown')
                definitions = [
                    d['definition'] 
                    for d in meaning.get('definitions', [])
                ]
                if pos not in meanings:
                    meanings[pos] = []
                meanings[pos].extend(definitions)
        return meanings

if __name__ == "__main__":
    root = tk.Tk()
    app = DictionaryApp(root)
    root.mainloop()