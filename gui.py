import tkinter as tk
from tkinter import ttk, messagebox
import requests
import threading
import time

# ✅ Replace this with your Render API URL
API_URL = "https://kickmeter.onrender.com

class KickViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Kick Stream Viewer")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        self.root.configure(bg="#2c2f33")  # Dark Mode UI

        # Title Label
        self.title_label = tk.Label(root, text="Kick Stream Viewer", font=("Arial", 16, "bold"), fg="white", bg="#2c2f33")
        self.title_label.pack(pady=10)

        # Input Field
        self.entry_label = tk.Label(root, text="Enter Kick Username(s):", font=("Arial", 12), fg="white", bg="#2c2f33")
        self.entry_label.pack()
        self.username_entry = tk.Entry(root, width=40, font=("Arial", 12))
        self.username_entry.pack(pady=5)

        # Search Button
        self.search_button = tk.Button(root, text="Search", font=("Arial", 12, "bold"), command=self.get_stream_info, bg="#7289da", fg="white", relief="flat")
        self.search_button.pack(pady=10)

        # Viewer Count Table
        self.tree_frame = tk.Frame(root)
        self.tree_frame.pack(pady=10, fill="both", expand=True)

        self.tree = ttk.Treeview(self.tree_frame, columns=("Username", "Viewers"), show="headings", height=8)
        self.tree.heading("Username", text="Username")
        self.tree.heading("Viewers", text="Viewers")
        self.tree.column("Username", width=200, anchor="center")
        self.tree.column("Viewers", width=100, anchor="center")
        self.tree.pack(fill="both", expand=True)

        # Table Styling
        style = ttk.Style()
        style.configure("Treeview", font=("Arial", 12), background="#23272a", foreground="white", rowheight=25, fieldbackground="#23272a")
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"), background="#23272a", foreground="white")

        self.is_updating = False

    def get_stream_info(self):
        """Fetch and display Kick stream viewer counts"""
        usernames = self.username_entry.get().strip().split(",")
        usernames = [u.strip() for u in usernames if u.strip()]
        if not usernames:
            messagebox.showwarning("Warning", "Please enter at least one username.")
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