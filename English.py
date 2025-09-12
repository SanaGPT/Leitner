import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import pyttsx3
import json
import os
from dk import Dictionary

class VocabularyApp:
    def __init__(self, root):
        self.root = root
        self.root.geometry('400x300')
        self.root.title('Vocabulary App')
        self.dictionary = Dictionary()
        
        # Initialize text-to-speech engine
        self.tts = pyttsx3.init()
        
        # Data storage
        self.data_file = 'vocabulary_data.json'
        self.vocabulary = {}
        
        # Load existing data
        self.load_data()
        
        # Create UI
        self.create_widgets()
        
        # Populate tree with loaded data
        self.populate_tree()
    
    def create_widgets(self):
        # Frame for entry and button
        entry_frame = tk.Frame(self.root)
        entry_frame.pack(pady=10)
        
        # Entry for new words
        self.entry = tk.Entry(entry_frame, width=30)
        self.entry.pack(side=tk.LEFT, padx=5)
        
        # Button to add words
        add_btn = tk.Button(entry_frame, text='Add Word', command=self.add_word)
        add_btn.pack(side=tk.LEFT)
        
        # Treeview to display vocabulary
        self.tree = ttk.Treeview(self.root)
        self.tree.pack(expand=True, fill=tk.BOTH, padx=10, pady=5)

        #dictionary button
        dict_btn = tk.Button(self.root, text = 'getting definition', command = self.lookup_definition)
        dict_btn.pack(side = tk.RIGHT, padx=5)
        
        # Bind double click event
        self.tree.bind("<Double-1>", self.on_item_double_click)
        
        # Button to remove selected item
        remove_btn = tk.Button(self.root, text='Remove Selected', command=self.remove_selected)
        remove_btn.pack(pady=5)
    
    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    self.vocabulary = json.load(f)
            except:
                self.vocabulary = {}
    
    def save_data(self):
        with open(self.data_file, 'w') as f:
            json.dump(self.vocabulary, f)
    
    def populate_tree(self):
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add words from vocabulary
        for word, details in self.vocabulary.items():
            parent_id = self.tree.insert("", "end", text=word, values=[word])
            
            # Add child items
            self.tree.insert(parent_id, "end", text="Audio", values=["audio"])
            if "example" in details:
                self.tree.insert(parent_id, "end", text=f"Example: {details['example']}", values=["example"])
            else:
                self.tree.insert(parent_id, "end", text="Add Example", values=["example"])
            
            if "meaning" in details:
                self.tree.insert(parent_id, "end", text=f"Meaning: {details['meaning']}", values=["meaning"])
            else:
                self.tree.insert(parent_id, "end", text="Add Meaning", values=["meaning"])
    
    def add_word(self):
        word = self.entry.get().strip()
        if word:
            if word not in self.vocabulary:
                self.vocabulary[word] = {}
                self.save_data()
                self.populate_tree()
                self.entry.delete(0, tk.END)
            else:
                messagebox.showinfo("Info", "Word already exists!")
    
    def on_item_double_click(self, event):
        item = self.tree.focus()
        item_values = self.tree.item(item, 'values')
        
        if not item_values:  # This shouldn't happen but just in case
            return
            
        action = item_values[0]
        word = self.tree.item(self.tree.parent(item), 'text') if action in ["audio", "example", "meaning"] else None
        
        if action == "audio":
            self.tts.say(word)
            self.tts.runAndWait()
        elif action in ["example", "meaning"]:
            self.edit_property(word, action)
    
    def edit_property(self, word, prop_type):
        # Create dialog window
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Edit {prop_type.capitalize()} for '{word}'")
        dialog.geometry('400x200')
        
        # Get current value if exists
        current_value = self.vocabulary[word].get(prop_type, "")
        
        # Label
        tk.Label(dialog, text=f"Enter {prop_type} for '{word}':").pack(pady=10)
        
        # Text widget for multi-line input (especially useful for examples)
        text_widget = tk.Text(dialog, height=5, width=40)
        text_widget.pack(pady=5, padx=10)
        text_widget.insert("1.0", current_value)
        
        # Save button
        def save_changes():
            new_value = text_widget.get("1.0", "end-1c").strip()
            self.vocabulary[word][prop_type] = new_value
            self.save_data()
            self.populate_tree()
            dialog.destroy()
        
        tk.Button(dialog, text="Save", command=save_changes).pack(pady=5)
    
    def remove_selected(self):
        item = self.tree.focus()
        if not item:
            messagebox.showwarning("Warning", "No item selected!")
            return
            
        # Get the word (parent item if child is selected)
        if self.tree.parent(item):  # This is a child item
            word = self.tree.item(self.tree.parent(item), 'text')
        else:  # This is a word (parent item)
            word = self.tree.item(item, 'text')
        
        # Confirm deletion
        if messagebox.askyesno("Confirm", f"Delete '{word}' and all its data?"):
            if word in self.vocabulary:
                del self.vocabulary[word]
                self.save_data()
                self.populate_tree()

    def lookup_definition(self):
        item = self.tree.focus()
        if not item:
            messagebox.showwarning('warning', 'no word selected')
            return
        
        word = self.tree.item(item, 'text')
        if self.tree.parent(item):
            word = self.tree.item(self.tree.parent(item), 'text')

        result = self.dictionary.lookup(word)
        self.show_definition_popup(word, result)

    
    def show_definition_popup(self, word, result):
        popup = tk.Toplevel(self.root)
        popup.title(f"Definition: {word}")
        popup.geometry("500x300")

        text = tk.Text(popup, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(popup, command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text.pack(fill=tk.BOTH, expand=True)

        if 'error' in result:
            text.insert(tk.END, f"Error: {result['error']}\n")
            if result['suggestions']:
                text.insert(tk.END, "\nDid you mean:\n")
                for suggestion in result['suggestions']:
                    text.insert(tk.END, f"- {suggestion}\n")
        else:
            text.insert(tk.END, f"Definitions from {result['source']}:\n\n")
            for pos, meanings in result['meanings'].items():
               text.insert(tk.END, f"{pos.capitalize()}:\n")
            for meaning in meanings[:3]:  # Show first 3 definitions
                text.insert(tk.END, f"  • {meaning}\n")
                text.insert(tk.END, "\n")

        text.config(state=tk.DISABLED)  # Make read-only

if __name__ == "__main__":
    root = tk.Tk()
    app = VocabularyApp(root)

root.mainloop()