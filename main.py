import tkinter as tk
from tkinter import ttk
import keyboard
import pyperclip
import shutil
import os

# Zwischenablage Speicher für Text und Dateipfade
clipboard_storage = {}
def update_clipboard_history():
    clipboard_listbox.delete(0, tk.END)
    for key, item in clipboard_storage.items():
        clipboard_listbox.insert(tk.END, f"{key}: {item['type']}")

def show_details(event=None):
    selection = clipboard_listbox.curselection()
    if selection:
        index = selection[0]
        key = clipboard_listbox.get(index).split(":")[0]  # Trenne den Key vom Typ
        item = clipboard_storage.get(key, {'type': 'N/A', 'content': 'Information nicht verfügbar'})
        
        detail_text.config(state=tk.NORMAL)
        detail_text.delete('1.0', tk.END)
        detail_text.insert(tk.END, f"Key: {key}\nType: {item['type']}\nContent: {item['content']}")
        detail_text.config(state=tk.DISABLED)

def show_details_directly(key, text):
    # Stellen Sie sicher, dass die Informationen verfügbar sind
    item = clipboard_storage.get(key, {'type': 'N/A', 'content': 'Information nicht verfügbar'})
    detail_text.config(state=tk.NORMAL)
    detail_text.delete('1.0', tk.END)
    # Hier können Sie entscheiden, welche Informationen angezeigt werden sollen
    detail_text.insert(tk.END, f"Key: {key}\nType: {item['type']}\nContent: {item['content']}")
    detail_text.config(state=tk.DISABLED)
def copy_to_clipboard(key):
    text = pyperclip.paste()
    if text:
        clipboard_storage[key] = {'type': 'file' if os.path.isfile(text) else 'text', 'content': text}
        status_label.config(text=f"{'Dateipfad' if os.path.isfile(text) else 'Text'} unter {key} gespeichert: {text}")
        update_clipboard_history()
        # Rufen Sie die neue Funktion mit den aktuellen Informationen auf
        show_details_directly(key, text)
    else:
        status_label.config(text="Die Zwischenablage ist leer.")


# Funktion zum Einfügen von Inhalten aus der Zwischenablage
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
    else:
        status_label.config(text="Kein Inhalt unter dem Key gefunden.")

# Funktion zum Löschen von Inhalten aus der Zwischenablage
def delete_from_clipboard(key):
    if key in clipboard_storage:
        del clipboard_storage[key]
        status_label.config(text=f"Inhalt unter {key} gelöscht.")
        update_clipboard_history()
    else:
        status_label.config(text="Kein Inhalt unter dem Key zu löschen gefunden.")

def delete_item_on_double_click(event=None):
    selection = clipboard_listbox.curselection()
    if selection:
        index = selection[0]
        key = clipboard_listbox.get(index).split(":")[0]  # Extrahiere den Key
        delete_from_clipboard(key)  # Lösche das Element
        update_clipboard_history()  # Aktualisiere die Liste
        detail_text.config(state=tk.NORMAL)  # Bereite das detail_text Widget vor
        detail_text.delete('1.0', tk.END)  # Lösche den aktuellen Inhalt
        detail_text.insert(tk.END, f"Eintrag {key} wurde gelöscht.")  # Zeige Nachricht
        detail_text.config(state=tk.DISABLED)  # Verhindere Bearbeitung



def delete_from_clipboard(key):
    if key in clipboard_storage:
        del clipboard_storage[key]
        status_label.config(text=f"Inhalt unter {key} gelöscht.")
        update_clipboard_history()
        detail_text.config(state=tk.NORMAL)
        detail_text.delete('1.0', tk.END)
        detail_text.config(state=tk.DISABLED)
    else:
        status_label.config(text="Kein Inhalt unter dem Key zu löschen gefunden.")


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

clipboard_listbox.bind('<<ListboxSelect>>', show_details)
clipboard_listbox.bind('<Double-1>', delete_item_on_double_click)

# Hotkeys beibehalten
valid_keys = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'
for key in valid_keys:
    keyboard.add_hotkey(f'ctrl+c+{key}', lambda k=key: copy_to_clipboard(k))
    keyboard.add_hotkey(f'ctrl+shift+{key}', lambda k=key: paste_from_clipboard(k))
    keyboard.add_hotkey(f'ctrl+alt+{key}', lambda k=key: delete_from_clipboard(k))

root.mainloop()
