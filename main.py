import tkinter as tk
from tkinter import ttk
import keyboard
import pyperclip
import shutil
import os
from ttkthemes import ThemedStyle  # Import des ThemedStyle aus ttkthemes

clipboard_storage = {}
copy_key = 'C'
paste_key = 'M'
custom_key = 'V'
copy_key_entry = None
paste_key_entry = None

def update_clipboard_history():
    clipboard_listbox.delete(0, tk.END)
    for key, item in clipboard_storage.items():
        clipboard_listbox.insert(tk.END, key)

def show_details(event=None):
    selection = clipboard_listbox.curselection()
    if selection:
        index = selection[0]
        key = clipboard_listbox.get(index)
        item = clipboard_storage.get(key, {'type': 'N/A', 'content': 'Information not available'})
        
        detail_text.config(state=tk.NORMAL)
        detail_text.delete('1.0', tk.END)
        detail_text.insert(tk.END, f"Key: {key}\nType: {item['type']}\nContent: {item['content']}")
        detail_text.config(state=tk.DISABLED)

def copy_to_clipboard(key):
    text = pyperclip.paste()
    if text:
        clipboard_storage[key] = {'type': 'file' if os.path.isfile(text) else 'text', 'content': text}
        update_clipboard_history()
        show_details(key)
        if custom_key:
            keyboard.press_and_release(f'ctrl+c+{paste_key}+{custom_key}')
    else:
        status_label.config(text="Clipboard is empty.")

def paste_from_clipboard(key):
    if key in clipboard_storage:
        item = clipboard_storage[key]
        if item['type'] == 'text':
            text = item['content']
            if text:
                pyperclip.copy(text)
                keyboard.press_and_release('ctrl+v')
            else:
                status_label.config(text="The text under the key is empty.")
        elif item['type'] == 'file':
            destination_path = os.getcwd()
            try:
                shutil.copy(item['content'], destination_path)
            except Exception as e:
                status_label.config(text=f"Error copying the file: {e}")

def delete_from_clipboard(key):
    if key in clipboard_storage:
        del clipboard_storage[key]
        update_clipboard_history()

def delete_item(event):
    selection = clipboard_listbox.curselection()
    if selection:
        index = selection[0]
        key = clipboard_listbox.get(index)
        if key in clipboard_storage:
            del clipboard_storage[key]
            update_clipboard_history()
            detail_text.config(state=tk.NORMAL)
            detail_text.delete('1.0', tk.END)
            detail_text.config(state=tk.DISABLED)

def show_settings():
    global copy_key, paste_key, custom_key, copy_key_entry, paste_key_entry

    settings_window = tk.Toplevel(root)
    settings_window.title("Settings")
    
    def set_copy_key(event):
        global copy_key
        copy_key = event.name
        copy_key_entry.delete(0, tk.END)
        copy_key_entry.insert(0, f"CTRL + {copy_key}")

    def set_paste_key(event):
        global paste_key
        paste_key = event.name
        paste_key_entry.delete(0, tk.END)
        paste_key_entry.insert(0, f"CTRL + M + {paste_key}")

    def set_custom_key(event):
        global custom_key
        custom_key = event.name
        custom_key_entry.delete(0, tk.END)
        custom_key_entry.insert(0, custom_key)

    settings_frame = ttk.Frame(settings_window)
    settings_frame.pack(padx=10, pady=5)

    copy_label = ttk.Label(settings_frame, text="Copy Key Combination:")
    copy_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
    copy_key_entry = ttk.Entry(settings_frame)
    copy_key_entry.insert(0, f"CTRL + {copy_key}")
    copy_key_entry.grid(row=0, column=1, padx=5, pady=5)

    paste_label = ttk.Label(settings_frame, text="Paste Key Combination:")
    paste_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
    paste_key_entry = ttk.Entry(settings_frame)
    paste_key_entry.insert(0, f"CTRL + M + {paste_key}")
    paste_key_entry.grid(row=1, column=1, padx=5, pady=5)

    custom_label = ttk.Label(settings_frame, text="Custom Key for Paste:")
    custom_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")
    custom_key_entry = ttk.Entry(settings_frame)
    custom_key_entry.insert(0, custom_key)
    custom_key_entry.grid(row=2, column=1, padx=5, pady=5)

    copy_key_entry.bind("<Key>", set_copy_key)
    paste_key_entry.bind("<Key>", set_paste_key)
    custom_key_entry.bind("<Key>", set_custom_key)

    def save_shortcuts():
        settings_window.destroy()

    save_button = ttk.Button(settings_frame, text="Save", command=save_shortcuts)
    save_button.grid(row=3, columnspan=2, padx=5, pady=10)

root = tk.Tk()
root.title("Clipboard Manager")
root.title("Clipboard Manager")

# Verwendung des Arc Designs aus ttkthemes
style = ThemedStyle(root)
style.set_theme("arc")

main_frame = ttk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

history_frame = ttk.Frame(main_frame)
history_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

listbox_scrollbar = ttk.Scrollbar(history_frame, orient=tk.VERTICAL)
clipboard_listbox = tk.Listbox(history_frame, yscrollcommand=listbox_scrollbar.set)
listbox_scrollbar.config(command=clipboard_listbox.yview)
listbox_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
clipboard_listbox.pack(fill=tk.BOTH, expand=True)

status_detail_frame = ttk.Frame(main_frame)
status_detail_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

detail_text = tk.Text(status_detail_frame, height=10, wrap='word', state='disabled', background='#f0f0f0')
detail_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

context_menu = tk.Menu(root, tearoff=0)
context_menu.add_command(label="Delete", command=lambda: delete_item(None))

clipboard_listbox.bind("<Button-3>", lambda e: context_menu.post(e.x_root, e.y_root))

clipboard_listbox.bind('<<ListboxSelect>>', show_details)

menu_bar = tk.Menu(root)
root.config(menu=menu_bar)

settings_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Settings", menu=settings_menu)
settings_menu.add_command(label="Open Settings", command=show_settings)

valid_keys = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'
for key in valid_keys:
    keyboard.add_hotkey(f'ctrl+c+{key}', lambda k=key: copy_to_clipboard(k))
    keyboard.add_hotkey(f'ctrl+shift+{key}', lambda k=key: paste_from_clipboard(k))
    keyboard.add_hotkey(f'ctrl+alt+{key}', lambda k=key: delete_from_clipboard(k))

root.mainloop()
