import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, Listbox, PhotoImage


class FileUploadPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=20)
        self.parent = parent
        self.uploaded_file_paths = []

        # Title Label with Icon
        try:
            icon = PhotoImage(file="upload_icon.png")
        except Exception:
            icon = None
        title_label = ttk.Label(self, text="  File Upload Tool", image=icon, compound=LEFT, font=("Arial", 26, "bold"))
        title_label.image = icon
        title_label.grid(row=0, column=0, columnspan=3, pady=20, sticky="n")

        # Upload Button
        upload_button = ttk.Button(
            self, text="Upload Files", bootstyle="primary outline", command=self.upload_file
        )
        upload_button.grid(row=1, column=0, columnspan=3, padx=20, pady=15, ipadx=30, ipady=12, sticky="ew")

        # File List Box with Scrollbar
        self.file_listbox = Listbox(self, height=12, width=80, bg="#f0f0f0", font=("Arial", 12))
        self.file_listbox.grid(row=2, column=0, padx=10, pady=10, columnspan=3, sticky="nsew")

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.file_listbox.yview)
        scrollbar.grid(row=2, column=3, sticky="ns")
        self.file_listbox.config(yscrollcommand=scrollbar.set)

        # Status Label
        self.status_label = ttk.Label(self, text="", font=("Arial", 14), bootstyle="info")
        self.status_label.grid(row=3, column=0, columnspan=3, pady=15)

        # Next Page Button
        self.next_page_button = ttk.Button(
            self, text="Proceed to Next Step", bootstyle="success", command=self.go_to_next_page
        )
        self.next_page_button.grid(row=4, column=0, columnspan=3, padx=20, pady=20, ipadx=20, ipady=10, sticky="ew")
        self.next_page_button.grid_remove()

    def upload_file(self):
        self.uploaded_file_paths = filedialog.askopenfilenames(
            title="Select JMeter Files",
            filetypes=(("JMX files", "*.jmx"), ("All files", "*.*"))
        )
        if self.uploaded_file_paths:
            self.file_listbox.delete(0, 'end')
            for file_path in self.uploaded_file_paths:
                self.file_listbox.insert('end', file_path)
            self.status_label.config(text="✅ Files Uploaded Successfully!", bootstyle="success")
            self.next_page_button.grid()

    def get_uploaded_files(self):
        return self.uploaded_file_paths

    def go_to_next_page(self):
        self.parent.show_page(self.parent.select_functionality)
