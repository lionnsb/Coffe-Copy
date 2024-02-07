import tkinter as tk
from tkinter import ttk
import keyboard
import pyperclip
import shutil
import os
import datetime
from ttkthemes import ThemedStyle
import base64
import win32clipboard
import win32con
import functools  # Hinzugefügte Zeile
import threading 
import time

clipboard_storage = {}
copy_key = 'C'
paste_key = 'M'
custom_key = 'V'
copy_key_entry = None
paste_key_entry = None
destination_path = None  # Variable zur Speicherung des Zielverzeichnisses
destination_window = None  # Variable zur Speicherung des Eingabefensters


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
        timestamp = item.get('timestamp', 'No timestamp available')
        source = item.get('source', 'No source available')
        
        detail_text.config(state=tk.NORMAL)
        detail_text.delete('1.0', tk.END)
        detail_text.insert(tk.END, f"Key: {key}\nType: {item['type']}\nContent: {item['content']}\nTimestamp: {timestamp}\nSource: {source}")
        detail_text.config(state=tk.DISABLED)
def is_text(s, text_characters="".join(map(chr, range(32, 127))) + "\n\r\t\b", threshold=0.30):
    # Funktion, um zu prüfen, ob der Inhalt als Text betrachtet werden kann
    if "\0" in s:
        return False  # Enthält Nullbytes, also wahrscheinlich kein Text
    if not s:  # Leerer String ist "Text"
        return True
    # Eine einfache Heuristik, um zu prüfen, ob zu großer Anteil des Strings druckbare Zeichen sind
    non_text_chars = s.translate({ord(c): None for c in text_characters})
    return len(non_text_chars) / len(s) <= threshold

def get_file_paths_from_clipboard():
    win32clipboard.OpenClipboard()
    paths = []
    if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_HDROP):
        data = win32clipboard.GetClipboardData(win32clipboard.CF_HDROP)
        for i in range(len(data)):
            paths.append(data[i])
    win32clipboard.CloseClipboard()
    return paths

def copy_to_clipboard(key):
    file_paths = get_file_paths_from_clipboard()
    timestamp = datetime.datetime.now().strftime("%Y.%m.%d %H:%M:%S")
    
    if file_paths:
        for file_path in file_paths:
            print(f"Datei gefunden: {file_path}")  # Bestätigen, dass es eine Datei ist
            clipboard_storage[key] = {
                'type': 'file',
                'content': file_path,  # Speichert den Pfad der Datei
                'timestamp': timestamp,
                'source': file_path
            }
            break  # Nehmen Sie nur den ersten Pfad, wenn mehrere vorhanden sind
    else:
        clipboard_content = pyperclip.paste()
        print("Keine Datei gefunden, speichere als Text.")  # Hinweis, wenn kein Dateipfad
        clipboard_storage[key] = {
            'type': 'text',
            'content': clipboard_content,
            'timestamp': timestamp,
            'source': 'Direct input' if clipboard_content else 'Unknown'
        }
    update_clipboard_history()

def paste_from_clipboard(key):
    global destination_path  # Verwendung der globalen Variable
    print(f"paste_from_clipboard aufgerufen mit key: {key}")  # Debugging-Ausgabe
    if key in clipboard_storage:
        item = clipboard_storage[key]
        print(f"Item-Typ: {item['type']}")  # Loggen des Typs des Items
        if item['type'] == 'text':
            text = item['content']
            pyperclip.copy(text)
            keyboard.press_and_release('ctrl+v')
        elif item['type'] == 'file':
            print(f"Frage nach Zielverzeichnis für: {item['content']}")  # Vor dem Dialog anzeigen
            ask_for_destination_path(item)  # Änderung: Übergeben des Items an die Funktion
    else:
        print(f"Kein Item gefunden für key: {key}")  # Wenn der Schlüssel nicht gefunden wurde

def ask_for_destination_path(item):
    global destination_path, destination_window
    destination_window = tk.Toplevel()
    destination_window.title("Destination Path")
    
    label = ttk.Label(destination_window, text="Enter the destination folder path:")
    label.pack(padx=10, pady=5)
    
    entry = ttk.Entry(destination_window)
    entry.pack(padx=10, pady=5)
    
    def set_destination_path():
        global destination_path
        path = entry.get()
        if path:
            destination_path = path  # Hier speicherst du nur den Ordnerpfad
            show_loading_indicator()
            # Übergib den vollständigen Pfad, einschließlich Dateiname, an die Funktion
            threading.Thread(target=copy_file_and_hide_indicator, args=(item['content'], path)).start()
    
    button = ttk.Button(destination_window, text="OK", command=set_destination_path)
    button.pack(padx=10, pady=5)

def copy_file_and_hide_indicator(source, destination_folder):
    global destination_window
    try:
        # Bereite den Dateinamen vor
        filename = os.path.basename(source)  # Extrahiere den Dateinamen aus dem Quellpfad
        destination_path = os.path.join(destination_folder, filename)  # Füge den Dateinamen zum Zielordnerpfad hinzu
        new_filename = generate_new_filename(destination_folder, filename)  # Generiere einen neuen Dateinamen, falls erforderlich
        final_destination = os.path.join(destination_folder, new_filename)
        
        shutil.copy(source, final_destination)
        print(f"Datei erfolgreich nach {final_destination} kopiert.")
    except Exception as e:
        print(f"Fehler beim Kopieren der Datei: {e}")
    finally:
        if destination_window is not None:
            destination_window.after(100, destination_window.destroy)

def show_loading_indicator():
    global loading_progressbar
    loading_label = ttk.Label(destination_window, text="Übertragung läuft, bitte warten...")
    loading_label.pack(pady=(10, 0))
    
    loading_progressbar = ttk.Progressbar(destination_window, orient="horizontal", length=200, mode="determinate")
    loading_progressbar.pack(pady=10)
    loading_progressbar['maximum'] = 100
    loading_progressbar['value'] = 0

def hide_loading_indicator():
    if loading_label is not None:
        loading_label.destroy()

def generate_new_filename(path, filename):
    """
    Generiert einen neuen Dateinamen, wenn eine Datei mit demselben Namen bereits existiert.
    Fügt ' - Copy' oder ' - Copy{IncrementZahl}' zum Dateinamen hinzu.
    """
    base, extension = os.path.splitext(filename)
    counter = 1
    new_filename = filename
    while os.path.exists(os.path.join(path, new_filename)):
        new_filename = f"{base} - Copy"
        if counter > 1:
            new_filename += f"{counter}"
        new_filename += extension
        counter += 1
    return new_filename

def update_progressbar(value):
    global loading_progressbar
    loading_progressbar['value'] += value
    if loading_progressbar['value'] >= loading_progressbar['maximum']:
        loading_progressbar['value'] = loading_progressbar['maximum']

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
    
    # Hier bleibt die Konfiguration der Tastenkombinationen unverändert
    
    settings_frame = ttk.Frame(settings_window)
    settings_frame.pack(padx=10, pady=5)

    # Hier bleibt die Konfiguration der Tastenkombinationen unverändert

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
