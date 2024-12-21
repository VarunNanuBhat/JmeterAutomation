import ttkbootstrap as ttk
from tkinter import filedialog, Listbox


class FileUploadPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=20)
        self.parent = parent
        self.uploaded_file_paths = []  # Initialize as an empty list

        title_label = ttk.Label(self, text="File Upload Tool", font=("Arial", 22, "bold"))
        title_label.grid(row=0, column=0, pady=20)

        upload_button = ttk.Button(self, text="Upload Files", bootstyle="primary", command=self.upload_file)
        upload_button.grid(row=1, column=0, padx=10, pady=10)

        self.file_listbox = Listbox(self, height=15, width=80)
        self.file_listbox.grid(row=2, column=0, padx=10, pady=10, columnspan=2)

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.file_listbox.yview)
        scrollbar.grid(row=2, column=2, sticky="ns")
        self.file_listbox.config(yscrollcommand=scrollbar.set)

        self.status_label = ttk.Label(self, text="", font=("Arial", 14))
        self.status_label.grid(row=3, column=0, pady=10)

        self.next_page_button = ttk.Button(self, text="Next Page", bootstyle="secondary", command=self.go_to_next_page)
        self.next_page_button.grid(row=4, column=0, pady=20)
        self.next_page_button.grid_remove()  # Initially hidden

    def upload_file(self):
        self.uploaded_file_paths = filedialog.askopenfilenames(
            title="Select Files",
            filetypes=(("JMX files", "*.jmx"), ("All files", "*.*"))
        )
        if self.uploaded_file_paths:
            self.file_listbox.delete(0, 'end')
            for file_path in self.uploaded_file_paths:
                self.file_listbox.insert('end', file_path)
            self.status_label.config(text="Files Uploaded Successfully!", bootstyle="success")
            self.next_page_button.grid()

    def get_uploaded_files(self):
        return self.uploaded_file_paths

    def go_to_next_page(self):
        self.parent.show_page(self.parent.select_functionality)
