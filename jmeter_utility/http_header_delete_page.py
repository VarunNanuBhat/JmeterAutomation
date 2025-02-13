import ttkbootstrap as ttk
from tkinter import StringVar
from jmeter_methods.Jmeter_Automation_Methods import JMXModifier


class HttpHeaderDeletePage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=20)
        self.parent = parent

        # List to store header input fields
        self.headers_to_delete = []

        # Title Label with Icon
        title_label = ttk.Label(self, text="🗑 Delete HTTP Headers", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=4, pady=10)

        # Add the first header row by default
        self.add_header_row()

        # Buttons with Icons
        add_button = ttk.Button(self, text="➕ Add Header", bootstyle="success", command=self.add_header_row)
        add_button.grid(row=1, column=0, pady=20, padx=20, sticky="ew")

        preview_button = ttk.Button(self, text="👁 Preview Deletions", bootstyle="primary", command=self.navigate_to_checkout)
        preview_button.grid(row=1, column=3, pady=20, padx=20, sticky="ew")

        list_button = ttk.Button(self, text="📜 List Headers", bootstyle="info", command=self.navigate_to_list_headers)
        list_button.grid(row=1, column=1, pady=20, padx=20, sticky="ew")

        home_button = ttk.Button(self, text="🏠 Home", bootstyle="secondary", command=self.go_back_to_home)
        home_button.grid(row=1, column=2, pady=20, padx=20, sticky="ew")

        # Status label at the bottom
        self.status_label = ttk.Label(self, text="", font=("Arial", 14), anchor="center", wraplength=500)
        self.status_label.grid(row=999, column=0, columnspan=4, pady=10, padx=20, sticky="s")

        # Configure grid row weight
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(999, weight=1)

    def add_header_row(self):
        """Dynamically add a row for a new header to delete."""
        row_index = len(self.headers_to_delete) + 2

        header_name_var = StringVar()

        header_name_label = ttk.Label(self, text="🔑 Header Name:", font=("Arial", 14))
        header_name_label.grid(row=row_index, column=0, padx=20, pady=5, sticky="w")

        header_name_entry = ttk.Entry(self, textvariable=header_name_var, width=30)
        header_name_entry.grid(row=row_index, column=1, padx=20, pady=5)

        self.headers_to_delete.append(header_name_var)

    def navigate_to_list_headers(self):
        """Navigate to the List Headers page."""
        try:
            uploaded_file_paths = self.parent.file_upload_page.get_uploaded_files()
            if not uploaded_file_paths:
                self.status_label.config(text="⚠ No files uploaded!", bootstyle="danger")
                return

            unique_headers = set()
            for file_path in uploaded_file_paths:
                modifier = JMXModifier(file_path)
                unique_headers.update(modifier.list_header_names())

            self.parent.http_header_list_page.populate_headers(list(sorted(unique_headers)))
            self.parent.show_page(self.parent.http_header_list_page)

        except Exception as e:
            self.status_label.config(text=f"❌ Error: {str(e)}", bootstyle="danger")

    def navigate_to_checkout(self):
        """Navigate to the checkout page with requested deletions."""
        headers_to_delete = [header.get().strip() for header in self.headers_to_delete if header.get().strip()]
        if not headers_to_delete:
            self.status_label.config(text="⚠ Please enter at least one header name to delete.", bootstyle="danger")
            return

        self.parent.checkout_for_http_header_delete.display_deletions(headers_to_delete)
        self.parent.show_page(self.parent.checkout_for_http_header_delete)

    def go_back_to_home(self):
        """Navigate back to the file upload page and reset the file list."""
        # self.parent.file_upload_page.uploaded_file_paths = []
        # self.parent.file_upload_page.file_listbox.delete(0, 'end')
        self.parent.file_upload_page.status_label.config(text="")
        # self.parent.file_upload_page.next_page_button.grid_remove()
        # self.status_label.config(text="")
        # self.reset_http_headers()
        self.parent.show_page(self.parent.file_upload_page)

    def reset_http_headers(self):
        """Reset the HTTP Header fields to their initial state."""
        for widget in self.grid_slaves():
            if isinstance(widget, ttk.Entry) or isinstance(widget, ttk.Label):
                widget.grid_forget()

        self.headers_to_delete = []
        self.add_header_row()
