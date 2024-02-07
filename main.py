import tkinter as tk
from tkinter import ttk, filedialog
import keyboard
import pyperclip
import shutil
import os
import datetime
import threading
import win32clipboard
import win32con
import time

clipboard_storage = {}
destination_path = None
destination_window = None
script_dir = os.path.dirname(os.path.realpath(__file__))
os.chdir(script_dir)

def check_if_clipboard_empty():
    # Lösche die vorherige Nachricht, wenn vorhanden, und zeige eine neue an, falls leer.
    for widget in history_frame.winfo_children():
        widget.destroy()  # Entferne alle vorhandenen Widgets
    if not clipboard_storage:
        show_empty_clipboard_message()
    else:
        hide_empty_clipboard_message()  # Verstecke den Platzhalter, wenn die Zwischenablage nicht leer ist

placeholder_frame = None  # Neuer Frame für den Platzhaltertext

def show_empty_clipboard_message():
    global placeholder_frame
    # Lösche den vorhandenen Platzhalter, falls vorhanden
    if placeholder_frame is not None:
        placeholder_frame.destroy()
    
    # Neuer Frame für den Platzhalter
    placeholder_frame = ttk.Frame(history_frame, padding=10)  
    placeholder_frame.pack(expand=True, fill=tk.BOTH)  

    # Text für den Platzhalter ohne Bild
    empty_message_label = ttk.Label(placeholder_frame, text="Deine Zwischenablage ist leer\n"
                                                            "Lass uns gemeinsam Geschichte schreiben, "
                                                            "indem du mehrere Elemente kopierst.",
                                    background="white", wraplength=300)
    empty_message_label.pack(expand=True, pady=10)  # Zentriere den Text

def hide_empty_clipboard_message():
    global placeholder_frame
    if placeholder_frame is not None:
        placeholder_frame.pack_forget()

def update_clipboard_history():
    # Lösche alle vorherigen Cards und prüfe, ob die Zwischenablage leer ist
    check_if_clipboard_empty()

    # Erstelle für jedes Item in clipboard_storage eine Card
    for key, item in clipboard_storage.items():
        create_clipboard_card(key, item)

    # Aktualisiere die Scrollregion des Canvas
    update_scrollregion()

def create_clipboard_card(key, item):
    card_frame = ttk.Frame(history_frame)
    card_frame.pack(fill=tk.X, padx=5, pady=5)

    card_label = ttk.Label(card_frame, text=f"{key}: {item['content']}", background="white", wraplength=300)  # Hier die wraplength anpassen
    card_label.pack(side=tk.LEFT, padx=5, pady=5)

    card_menu_button = ttk.Menubutton(card_frame, text="...", direction="above")
    card_menu = tk.Menu(card_menu_button, tearoff=0)
    card_menu.add_command(label="Delete", command=lambda k=key: delete_from_clipboard(k))
    card_menu_button['menu'] = card_menu
    card_menu_button.pack(side=tk.RIGHT, padx=5, pady=5)

def copy_to_clipboard(key):
    file_paths = get_file_paths_from_clipboard()
    timestamp = datetime.datetime.now().strftime("%Y.%m.%d %H:%M:%S")
    
    if key not in clipboard_storage:
        clipboard_storage[key] = {'type': 'multiple', 'content': [], 'timestamp': timestamp, 'source': []}
    
    if file_paths:
        for file_path in file_paths:
            print(f"Element gefunden: {file_path}")
            clipboard_storage[key]['content'].append(file_path)
            clipboard_storage[key]['source'].append(file_path)
        if os.path.isfile(file_paths[0]) and key.startswith('v'):  # Nur öffnen, wenn STRG + V + Key gedrückt wurde und der Key einer Datei entspricht
            ask_for_destination_path(clipboard_storage[key])
        update_clipboard_history()  # Cards aktualisieren
    else:
        clipboard_content = pyperclip.paste()
        print("Keine Datei oder Ordner gefunden, speichere als Text.")
        clipboard_storage[key] = {'type': 'text', 'content': [clipboard_content], 'timestamp': timestamp}
        update_clipboard_history()

def paste_from_clipboard(key):
    global destination_path
    print(f"paste_from_clipboard aufgerufen mit key: {key}")
    if key in clipboard_storage:
        items = clipboard_storage[key]
        if items['type'] == 'multiple':
            if os.path.isfile(items['content'][0]):  # Überprüfen, ob der Inhalt eine Datei ist
                ask_for_destination_path(items)
            else:
                pyperclip.copy(items['content'][0])
                keyboard.send('ctrl+v')
                update_clipboard_history()  # Aktualisierung der Historien-Cards
        else:
            content = items['content'][0]
            if os.path.isfile(content):  # Überprüfen, ob der Inhalt eine Datei ist
                ask_for_destination_path(items)
            else:
                pyperclip.copy(content)
                keyboard.send('ctrl+v')
                update_clipboard_history()  # Aktualisierung der Historien-Cards
    else:
        print(f"Kein Item gefunden für key: {key}")

def ask_for_destination_path(items):
    global destination_path, destination_window

    destination_window = tk.Toplevel()
    destination_window.title("Destination Path")
    destination_window.transient(root) 
    destination_window.grab_set()  

    label = ttk.Label(destination_window, text="Select the destination folder path:")
    label.pack(padx=10, pady=5)

    path_display = ttk.Label(destination_window, text="No path selected")
    path_display.pack(padx=10, pady=5)

    def open_file_dialog():
        global destination_path
        path = filedialog.askdirectory()
        if path:
            destination_path = path
            path_display.config(text="Selected path: " + path)
            proceed_button.config(state=tk.NORMAL)  

    browse_button = ttk.Button(destination_window, text="Browse...", command=open_file_dialog)
    browse_button.pack(padx=10, pady=5)

    def proceed_with_selected_path():
        if destination_path:
            show_loading_indicator()
            for item in items['content']:
                thread = threading.Thread(target=copy_file_and_hide_indicator, args=(item, destination_path))
                thread.start()
            destination_window.destroy()

    proceed_button = ttk.Button(destination_window, text="OK", command=proceed_with_selected_path, state=tk.DISABLED)
    proceed_button.pack(padx=10, pady=10)

    destination_window.protocol("WM_DELETE_WINDOW", lambda: None)  
    root.wait_window(destination_window)  

def copy_file_and_hide_indicator(source, destination_folder):
    global destination_window
    try:
        if os.path.isdir(source):
            basename = os.path.basename(source.rstrip("\\/"))
            final_destination = os.path.join(destination_folder, basename)
            final_destination = generate_new_destination(final_destination)
            shutil.copytree(source, final_destination)
            message = f"Ordner erfolgreich nach {final_destination} kopiert."
        else:
            basename = os.path.basename(source)
            final_destination = os.path.join(destination_folder, basename)
            final_destination = generate_new_destination(final_destination)
            shutil.copy(source, final_destination)
            message = f"Datei erfolgreich nach {final_destination} kopiert."
    except Exception as e:
        message = f"Fehler beim Kopieren: {e}"
    
    root.after(0, lambda: update_gui_after_copy(message))

def update_gui_after_copy(message):
    print(message)
    if destination_window is not None:
        destination_window.destroy()

def generate_new_destination(destination_path):
    if os.path.exists(destination_path):
        base, extension = os.path.splitext(destination_path)
        counter = 1
        while os.path.exists(f"{base} - Copy{counter}{extension}"):
            counter += 1
        return f"{base} - Copy{counter}{extension}"
    return destination_path

def show_loading_indicator():
    loading_label = ttk.Label(destination_window, text="Übertragung läuft, bitte warten...")
    loading_label.pack(pady=(10, 0))
    
    loading_progressbar = ttk.Progressbar(destination_window, orient="horizontal", length=200, mode="determinate")
    loading_progressbar.pack(pady=10)
    loading_progressbar['maximum'] = 100
    loading_progressbar['value'] = 0

def get_file_paths_from_clipboard():
    max_attempts = 5
    for _ in range(max_attempts):
        try:
            win32clipboard.OpenClipboard()
            paths = []
            if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_HDROP):
                data = win32clipboard.GetClipboardData(win32clipboard.CF_HDROP)
                for i in range(len(data)):
                    paths.append(data[i])
            win32clipboard.CloseClipboard()
            return paths
        except Exception as e:
            print(f"Error accessing clipboard: {e}. Retrying...")
            time.sleep(1)
    raise Exception("Failed to access clipboard after multiple attempts")

def delete_from_clipboard(key):
    del clipboard_storage[key]
    update_clipboard_history()

def update_scrollregion(event=None):
    history_canvas.configure(scrollregion=history_canvas.bbox("all"))

def on_mousewheel(event):
    history_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

root = tk.Tk()
root.title("Clipboard Manager")

# Setze die Größe der Anwendung auf 395x292 Pixel und deaktiviere das Ändern der Größe
root.geometry("395x292")
root.resizable(False, False)

# Rahmen und Hintergrundfarben entsprechend dem ursprünglichen Design des Clipboard Managers
root.configure(bg="#f0f0f0")

# Erstelle ein Frame, um das Canvas und die Scrollbaacar zu umgeben
main_frame = ttk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

# Erstelle ein Canvas Widget, um die history_frame zu umgeben
history_canvas = tk.Canvas(main_frame)
history_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Füge eine Scrollbar hinzu und verbinde sie mit dem Canvas
scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=history_canvas.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
history_canvas.configure(yscrollcommand=scrollbar.set)

# Erstelle ein Frame im Canvas, um die Karten anzuzeigen
history_frame = ttk.Frame(history_canvas)
history_frame.pack(fill=tk.BOTH, expand=True)  # Ändern Sie hier 'pack' zu 'grid', wenn das Layout nicht wie erwartet ist

# Erstelle eine Canvas-Window-Konfiguration
history_canvas.create_window((0, 0), window=history_frame, anchor="nw")

# Binden des Scrollregion-Updates an die Änderungen in history_frame
history_frame.bind("<Configure>", update_scrollregion)

# Mausrad-Scrollen hinzufügen
history_canvas.bind_all("<MouseWheel>", on_mousewheel)

context_menu = tk.Menu(root, tearoff=0)
# Menu zur GUI hinzufügen
root.config(menu=context_menu)

valid_keys = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'
for key in valid_keys:
    keyboard.add_hotkey(f'ctrl+c+{key}', lambda k=key: copy_to_clipboard(k))
    keyboard.add_hotkey(f'ctrl+shift+{key}', lambda k=key: paste_from_clipboard(k))
    keyboard.add_hotkey(f'ctrl+alt+{key}', lambda k=key: delete_from_clipboard(k))
    keyboard.add_hotkey(f'ctrl+v+{key}', lambda k=key: paste_from_clipboard(key))  # Hinzufügen dieser Zeile

root.mainloop()
