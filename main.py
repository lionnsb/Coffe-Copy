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

clipboard_storage = {}
destination_path = None
destination_window = None

def update_clipboard_history():
    clipboard_listbox.delete(0, tk.END)
    for key, item in clipboard_storage.items():
        clipboard_listbox.insert(tk.END, key)

def update_detail_text(key):
    if key in clipboard_storage:
        item = clipboard_storage[key]
        detail_text.config(state='normal')
        detail_text.delete('1.0', tk.END)
        detail_text.insert(tk.END, f"Timestamp: {item['timestamp']}\nType: {item['type']}\nContent:\n")
        for content in item['content']:
            detail_text.insert(tk.END, f"- {content}\n")
        detail_text.config(state='disabled')

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
        update_clipboard_history()  # Liste aktualisieren
    else:
        clipboard_content = pyperclip.paste()
        print("Keine Datei oder Ordner gefunden, speichere als Text.")
        clipboard_storage[key] = {'type': 'text', 'content': [clipboard_content], 'timestamp': timestamp}
        update_clipboard_history()
        update_detail_text(key)  # Hier die Detailansicht aktualisieren

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
                update_clipboard_history()  # Aktualisierung der Historienliste
        else:
            content = items['content'][0]
            if os.path.isfile(content):  # Überprüfen, ob der Inhalt eine Datei ist
                ask_for_destination_path(items)
            else:
                pyperclip.copy(content)
                keyboard.send('ctrl+v')
                update_clipboard_history()  # Aktualisierung der Historienliste
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
    win32clipboard.OpenClipboard()
    paths = []
    if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_HDROP):
        data = win32clipboard.GetClipboardData(win32clipboard.CF_HDROP)
        for i in range(len(data)):
            paths.append(data[i])
    win32clipboard.CloseClipboard()
    return paths

def delete_from_clipboard(key):
    if key in clipboard_storage:
        del clipboard_storage[key]
        update_clipboard_history()

root = tk.Tk()
root.title("Clipboard Manager")

style = ttk.Style()
style.theme_use('clam')
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
context_menu.add_command(label="Delete", command=lambda: delete_from_clipboard(clipboard_listbox.get(tk.ACTIVE)))

clipboard_listbox.bind("<Button-3>", lambda e: context_menu.post(e.x_root, e.y_root))
clipboard_listbox.bind("<<ListboxSelect>>", lambda e: update_detail_text(clipboard_listbox.get(tk.ACTIVE)))

menu_bar = tk.Menu(root)
root.config(menu=menu_bar)

valid_keys = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'
for key in valid_keys:
    keyboard.add_hotkey(f'ctrl+c+{key}', lambda k=key: copy_to_clipboard(k))
    keyboard.add_hotkey(f'ctrl+shift+{key}', lambda k=key: paste_from_clipboard(k))
    keyboard.add_hotkey(f'ctrl+alt+{key}', lambda k=key: delete_from_clipboard(k))
    keyboard.add_hotkey(f'ctrl+v+{key}', lambda k=key: paste_from_clipboard(key))  # Hinzufügen dieser Zeile

root.mainloop()
