import tkinter as tk
from tkinter import ttk, messagebox
import requests
import threading
import time

# ✅ Replace this with your Render API URL
API_URL = "https://kickmeter.onrender.com/viewer_count/"

class KickViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Kick Stream Viewer")
        self.root.geometry("600x450")
        self.root.configure(bg="#1E1E1E")  # Dark theme background
        self.root.resizable(True, True)

        # Title Label with Custom Font
        self.title_label = tk.Label(root, text="🎥 Kick Stream Viewer", font=("Arial", 18, "bold"), fg="white", bg="#1E1E1E")
        self.title_label.pack(pady=10)

        # Input Frame
        self.input_frame = tk.Frame(root, bg="#1E1E1E")
        self.input_frame.pack(pady=5)

        self.entry_label = tk.Label(self.input_frame, text="Enter Kick Usernames:", font=("Arial", 12), fg="white", bg="#1E1E1E")
        self.entry_label.grid(row=0, column=0, padx=10, pady=5)

        self.username_entry = tk.Entry(self.input_frame, width=40, font=("Arial", 12), bg="#2A2A2A", fg="white", insertbackground="white")
        self.username_entry.grid(row=0, column=1, padx=10, pady=5)

        # Search Button with Modern Styling
        self.search_button = tk.Button(root, text="🔍 Search", font=("Arial", 12, "bold"), command=self.get_stream_info, bg="#00A86B", fg="white", relief="flat", padx=10, pady=5)
        self.search_button.pack(pady=10)

        # Treeview (Table) Frame
        self.tree_frame = tk.Frame(root)
        self.tree_frame.pack(pady=10, fill="both", expand=True)

        # Styled Table
        self.tree = ttk.Treeview(self.tree_frame, columns=("Username", "Viewers"), show="headings", height=8)
        self.tree.heading("Username", text="🎮 Username", anchor="center")
        self.tree.heading("Viewers", text="👥 Viewers", anchor="center")
        self.tree.column("Username", width=250, anchor="center")
        self.tree.column("Viewers", width=120, anchor="center")
        self.tree.pack(fill="both", expand=True)

        # Apply Custom Treeview Style
        style = ttk.Style()
        style.theme_use("clam")  # Modern look
        style.configure("Treeview", font=("Arial", 12), background="#262626", foreground="white", rowheight=30, fieldbackground="#262626")
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"), background="#00A86B", foreground="white")

        self.is_updating = False

    def get_stream_info(self):
        """Fetch and display Kick stream viewer counts"""
        usernames = self.username_entry.get().strip().split(",")
        usernames = [u.strip() for u in usernames if u.strip()]
        if not usernames:
            messagebox.showwarning("⚠ Warning", "Please enter at least one username.")
            return

        self.tree.delete(*self.tree.get_children())  # Clear old data
        self.is_updating = True
        threading.Thread(target=self.update_viewer_counts, args=(usernames,), daemon=True).start()

    def update_viewer_counts(self, usernames):
        """Continuously update viewer counts"""
        while self.is_updating:
            for username in usernames:
                viewer_count = self.fetch_viewers(username)
                if viewer_count is not None:
                    found = False
                    for item in self.tree.get_children():
                        values = self.tree.item(item, "values")
                        if values[0] == username:
                            self.tree.item(item, values=(username, viewer_count))
                            found = True
                            break
                    if not found:
                        self.tree.insert("", "end", values=(username, viewer_count))
            time.sleep(10)  # Update every 10 sec

    def fetch_viewers(self, username):
        """Fetch viewer count from API"""
        try:
            response = requests.get(API_URL + username)
            if response.status_code == 200:
                data = response.json()
                return data.get("viewers", 0)
            else:
                return None
        except requests.RequestException:
            return None

    def stop_updating(self):
        """Stop updating when app is closed"""
        self.is_updating = False

if __name__ == "__main__":
    root = tk.Tk()
    app = KickViewerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.stop_updating)
    root.mainloop()