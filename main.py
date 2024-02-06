import tkinter as tk
from tkinter import ttk
import keyboard
import pyperclip
import shutil
import os

# Zwischenablage Speicher für Text und Dateipfade
clipboard_storage = {}

# Benutzerdefinierte Tastenkombinationen für Kopieren und Einfügen
copy_key = 'C'
paste_key = 'M'

custom_key = 'V'  # Die benutzerdefinierte Taste (Beispiel: 'V')

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
        item = clipboard_storage.get(key, {'type': 'N/A', 'content': 'Information nicht verfügbar'})
        
        detail_text.config(state=tk.NORMAL)
        detail_text.delete('1.0', tk.END)
        detail_text.insert(tk.END, f"Key: {key}\nType: {item['type']}\nContent: {item['content']}")
        detail_text.config(state=tk.DISABLED)

def copy_to_clipboard(key):
    text = pyperclip.paste()
    if text:
        clipboard_storage[key] = {'type': 'file' if os.path.isfile(text) else 'text', 'content': text}
        status_label.config(text=f"{'Dateipfad' if os.path.isfile(text) else 'Text'} unter {key} gespeichert: {text}")
        update_clipboard_history()
        show_details(key)
        # Hier wird die benutzerdefinierte Taste zusammen mit der Tastenkombination verwendet
        if custom_key:
            keyboard.press_and_release(f'ctrl+c+{paste_key}+{custom_key}')
    else:
        status_label.config(text="Die Zwischenablage ist leer.")

def paste_from_clipboard(key):
    if key in clipboard_storage:
        item = clipboard_storage[key]
        if item['type'] == 'text':
            text = item['content']
            if text:
                pyperclip.copy(text)
                keyboard.press_and_release('ctrl+v')
                status_label.config(text=f"Text von {key} eingefügt.")
            else:
                status_label.config(text="Der Text unter dem Key ist leer.")
        elif item['type'] == 'file':
            destination_path = os.getcwd()
            try:
                shutil.copy(item['content'], destination_path)
                status_label.config(text=f"Datei von {item['content']} nach {destination_path} kopiert.")
            except Exception as e:
                status_label.config(text=f"Fehler beim Kopieren der Datei: {e}")

def delete_from_clipboard(key):
    if key in clipboard_storage:
        del clipboard_storage[key]
        status_label.config(text=f"Inhalt unter {key} gelöscht.")
        update_clipboard_history()

def delete_item(event):
    selection = clipboard_listbox.curselection()
    if selection:
        index = selection[0]
        key = clipboard_listbox.get(index)
        if key in clipboard_storage:
            del clipboard_storage[key]
            status_label.config(text=f"Inhalt unter {key} gelöscht.")
            update_clipboard_history()
            detail_text.config(state=tk.NORMAL)
            detail_text.delete('1.0', tk.END)
            detail_text.config(state=tk.DISABLED)
        else:
            status_label.config(text="Kein Inhalt unter dem Key zu löschen gefunden.")
    else:
        status_label.config(text="Bitte wählen Sie ein Element zum Löschen aus.")

def show_settings():
    global copy_key, paste_key, custom_key, copy_key_entry, paste_key_entry

    settings_window = tk.Toplevel(root)
    settings_window.title("Einstellungen")
    
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

    copy_label = ttk.Label(settings_window, text="Tastenkombination für Kopieren:")
    copy_label.pack(padx=10, pady=5)
    copy_key_entry = ttk.Entry(settings_window)
    copy_key_entry.insert(0, f"CTRL + {copy_key}")
    copy_key_entry.pack(padx=10, pady=5)

    paste_label = ttk.Label(settings_window, text="Tastenkombination für Einfügen:")
    paste_label.pack(padx=10, pady=5)
    paste_key_entry = ttk.Entry(settings_window)
    paste_key_entry.insert(0, f"CTRL + M + {paste_key}")
    paste_key_entry.pack(padx=10, pady=5)

    custom_label = ttk.Label(settings_window, text="Benutzerdefinierte Taste für Einfügen:")
    custom_label.pack(padx=10, pady=5)
    custom_key_entry = ttk.Entry(settings_window)
    custom_key_entry.insert(0, custom_key)
    custom_key_entry.pack(padx=10, pady=5)

    copy_key_entry.bind("<Key>", set_copy_key)
    paste_key_entry.bind("<Key>", set_paste_key)
    custom_key_entry.bind("<Key>", set_custom_key)

    def save_shortcuts():
        settings_window.destroy()

    save_button = ttk.Button(settings_window, text="Speichern", command=save_shortcuts)
    save_button.pack(padx=10, pady=10)

# Erstelle das Hauptfenster
root = tk.Tk()
root.title("Clipboard Manager")

# Layout-Konfiguration
main_frame = ttk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True)

# Linker Bereich für die Historie
left_frame = ttk.Frame(main_frame, width=200)
left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

# Rechter Bereich für Statusmeldungen und Details
right_frame = ttk.Frame(main_frame)
right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

# Listbox für die Historie
clipboard_listbox = tk.Listbox(left_frame)
clipboard_listbox.pack(fill=tk.BOTH, expand=True)

# Statuslabel
status_label = tk.Label(right_frame, text="", wraplength=400)
status_label.pack(pady=10)

# Detailansicht für ausgewählte Elemente
detail_text = tk.Text(right_frame, height=15, wrap='word', state='disabled', background='#f0f0f0')
detail_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

# Erstellen des Kontextmenüs
context_menu = tk.Menu(root, tearoff=0)
context_menu.add_command(label="Löschen", command=lambda: delete_item(None))

# Binden des Kontextmenüs an die Listbox
clipboard_listbox.bind("<Button-3>", lambda e: context_menu.post(e.x_root, e.y_root))

clipboard_listbox.bind('<<ListboxSelect>>', show_details)
clipboard_listbox.bind('<<ListboxSelect>>', show_details)

# Menüleiste hinzufügen
menu_bar = tk.Menu(root)
root.config(menu=menu_bar)

# Einstellungsmenü hinzufügen
settings_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Einstellungen", menu=settings_menu)
settings_menu.add_command(label="Einstellungen öffnen", command=show_settings)

# Hotkeys beibehalten
valid_keys = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'
for key in valid_keys:
    keyboard.add_hotkey(f'ctrl+c+{key}', lambda k=key: copy_to_clipboard(k))
    keyboard.add_hotkey(f'ctrl+shift+{key}', lambda k=key: paste_from_clipboard(k))
    keyboard.add_hotkey(f'ctrl+alt+{key}', lambda k=key: delete_from_clipboard(k))

root.mainloop()
