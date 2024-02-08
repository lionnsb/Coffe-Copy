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
import textwrap

clipboard_storage = {}
destination_path = None
destination_window = None
script_dir = os.path.dirname(os.path.realpath(__file__))
os.chdir(script_dir)

def check_if_clipboard_empty():
    for widget in history_frame.winfo_children():
        widget.destroy()
    if not clipboard_storage:
        show_empty_clipboard_message()
    else:
        hide_empty_clipboard_message()

placeholder_frame = None

def show_empty_clipboard_message():
    global placeholder_frame
    if placeholder_frame is not None:
        placeholder_frame.destroy()

    placeholder_frame = ttk.Frame(history_frame, padding=10)
    placeholder_frame.pack(expand=True, fill=tk.BOTH)

    empty_message_label = ttk.Label(placeholder_frame, text="Deine Zwischenablage ist leer\n"
                                                            "Lass uns gemeinsam Geschichte schreiben, "
                                                            "indem du mehrere Elemente kopierst.",
                                    background="#ffffff", foreground="#000000", wraplength=300)
    empty_message_label.pack(expand=True, pady=10)

def hide_empty_clipboard_message():
    global placeholder_frame
    if placeholder_frame is not None:
        placeholder_frame.pack_forget()

def update_clipboard_history():
    check_if_clipboard_empty()

    # Erstelle eine sortierte Liste der Schlüssel nach dem Zeitstempel, um die Reihenfolge der Karten zu steuern
    sorted_keys = sorted(clipboard_storage.keys(), key=lambda k: clipboard_storage[k]['timestamp'], reverse=True)

    max_width = 0
    max_height = 0

    # Durchlaufe die sortierten Schlüssel und erstelle die entsprechenden Karten
    for key in sorted_keys:
        item = clipboard_storage[key]
        card_frame, card_label = create_clipboard_card(key, item)
        card_width = card_frame.winfo_reqwidth()
        card_height = card_frame.winfo_reqheight()

        if card_width > max_width:
            max_width = card_width
        if card_height > max_height:
            max_height = card_height

    # Setze die maximale Breite und Höhe für alle Karten
    for key in sorted_keys:
        item = clipboard_storage[key]
        card_frame = item['frame']
        card_frame.config(width=max_width, height=max_height)

    update_scrollregion()

def create_clipboard_card(key, item):
    # Karte erstellen
    card_frame = ttk.Frame(history_frame, width=280, height=100, relief="solid", borderwidth=1, style="Custom.TFrame")  # Style hinzugefügt
    card_frame.pack(fill=tk.X, padx=5, pady=10)

    # Füge den Schlüssel 'frame' zum Dictionary 'item' hinzu
    item['frame'] = card_frame

    # Überprüfen, ob der Inhalt ein einzelner String oder eine Liste von Strings ist
    if isinstance(item['content'], list):
        content_str = ', '.join(item['content'])
        truncated_content = truncate_string(content_str)
    else:
        truncated_content = truncate_string(item['content'])

    # Label für den Schlüssel erstellen (fett gedruckt)
    key_label = ttk.Label(card_frame, text=key + ":", background="#ffffff", foreground="#000000", anchor="w", justify=tk.LEFT, font=("Helvetica", 10, "bold"))
    key_label.grid(row=0, column=0, sticky="w")

    # Label für den Inhalt erstellen
    content_label = ttk.Label(card_frame, text=truncated_content, background="#ffffff", foreground="#000000", wraplength=250, anchor="w", justify=tk.LEFT, font=("Helvetica", 10))
    content_label.grid(row=0, column=1, sticky="w")

    # Die Scrollregion aktualisieren, um sicherzustellen, dass neue Karten angezeigt werden
    update_scrollregion()

    return card_frame, (key_label, content_label)  # Rückgabe des Frame und der Labels als Tupel


def truncate_string(content, max_length=255):
    """
    Kürzt einen String auf die maximale Länge, einschließlich der Platzierung von '...'
    am Ende, falls der Text länger als die maximale Länge ist.
    """

    return textwrap.shorten(content, width=max_length, placeholder="...")

def copy_to_clipboard(key):
    file_paths = get_file_paths_from_clipboard()
    timestamp = datetime.datetime.now().strftime("%Y.%m.%d %H:%M:%S")

    if key not in clipboard_storage:
        clipboard_storage[key] = {'type': 'multiple', 'content': [], 'timestamp': timestamp, 'source': []}

    if file_paths:
        for file_path in file_paths:
            print(f"Element gefunden: {file_path}")
            clipboard_storage[key]['content'].insert(0, file_path)  # Neues Element oben einfügen
            clipboard_storage[key]['source'].insert(0, file_path)
        if os.path.isfile(file_paths[0]) and key.startswith('v'):
            ask_for_destination_path(clipboard_storage[key])
        update_clipboard_history()
    else:
        clipboard_content = pyperclip.paste()
        print("Keine Datei oder Ordner gefunden, speichere als Text.")
        clipboard_storage[key] = {'type': 'text', 'content': [clipboard_content], 'timestamp': timestamp, 'source': []}
        update_clipboard_history()

def paste_from_clipboard(key):
    global destination_path
    print(f"paste_from_clipboard aufgerufen mit key: {key}")
    if key in clipboard_storage:
        items = clipboard_storage[key]
        if items['type'] == 'multiple':
            if os.path.isfile(items['content'][0]):
                ask_for_destination_path(items)
            else:
                pyperclip.copy(items['content'][0])
                keyboard.send('ctrl+v')
                update_clipboard_history()
        else:
            content = items['content'][0]
            if os.path.isfile(content):
                ask_for_destination_path(items)
            else:
                pyperclip.copy(content)
                keyboard.send('ctrl+v')
                update_clipboard_history()
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
    # Anpassen der Scrollregion basierend auf der Höhe des Inhalts
    history_canvas.update_idletasks()
    canvas_height = history_canvas.winfo_height()
    frame_height = history_frame.winfo_reqheight()
    if frame_height > canvas_height:
        history_canvas.config(scrollregion="0 0 {} {}".format(history_frame.winfo_width(), frame_height))
    else:
        history_canvas.config(scrollregion="")

def on_mousewheel(event):
    history_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

root = tk.Tk()
root.title("Clipboard Manager")

root.geometry("295x392")  # Neue Größe angepasst
root.resizable(False, False)

root.configure(bg="#f0f0f0")

# Neuer Stil für den Rahmen der Karten hinzugefügt
style = ttk.Style()
style.configure("Custom.TFrame", background="#ffffff")

main_frame = ttk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

history_canvas = tk.Canvas(main_frame, yscrollincrement=15, bg="#f0f0f0")  # Hintergrundfarbe hinzugefügt
history_canvas.pack(side=tk.LEFT, fill="both", expand=True)

scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=history_canvas.yview)
scrollbar.pack(side=tk.RIGHT, fill="y")

history_canvas.configure(yscrollcommand=scrollbar.set)
history_frame = ttk.Frame(history_canvas)  # Hintergrundfarbe entfernt
history_canvas.create_window((0, 0), window=history_frame, anchor="nw")

history_frame.bind("<Configure>", update_scrollregion)

history_canvas.bind_all("<MouseWheel>", on_mousewheel)

context_menu = tk.Menu(root, tearoff=0)
root.config(menu=context_menu)

valid_keys = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'
for key in valid_keys:
    keyboard.add_hotkey(f'ctrl+c+{key}', lambda k=key: copy_to_clipboard(k))
    keyboard.add_hotkey(f'ctrl+shift+{key}', lambda k=key: paste_from_clipboard(k))
    keyboard.add_hotkey(f'ctrl+alt+{key}', lambda k=key: delete_from_clipboard(k))
    keyboard.add_hotkey(f'ctrl+v+{key}', lambda k=key: paste_from_clipboard(key))

root.mainloop()
