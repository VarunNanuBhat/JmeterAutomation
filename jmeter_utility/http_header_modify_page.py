import ttkbootstrap as ttk
from tkinter import StringVar
from jmeter_methods.Jmeter_Automation_Methods import JMXModifier

# enable reset_http_headers method if you want to reset header page on re-starting


class HttpHeaderPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=20)
        self.parent = parent

        # List to store header input fields
        self.headers = []

        # Title Label
        title_label = ttk.Label(self, text="HTTP Header Manager", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=4, pady=10)

        # Add the first header row by default
        self.add_header_row()

        # Add Header button
        add_button = ttk.Button(self, text="+ Add Header", bootstyle="success", command=self.add_header_row)
        add_button.grid(row=1, column=0, pady=20, padx=20, sticky="w")

        # Apply Changes button
        apply_button = ttk.Button(self, text="Apply Changes", bootstyle="primary", command=self.modify_http_headers)
        apply_button.grid(row=1, column=3, pady=20, padx=20, sticky="e")

        # Go Back button (navigate back to home)
        back_button = ttk.Button(self, text="Go Back", bootstyle="danger", command=self.go_back_to_home)
        back_button.grid(row=2, column=3, pady=20, padx=20, sticky="e")

        # Status label at the bottom
        self.status_label = ttk.Label(self, text="", font=("Arial", 14), anchor="center", wraplength=500)
        self.status_label.grid(row=999, column=0, columnspan=4, pady=10, padx=20, sticky="s")

        # Configure grid row weight to make the header section flexible and push the status label down
        self.grid_rowconfigure(0, weight=0)  # Title row should not expand
        self.grid_rowconfigure(1, weight=0)  # Button row should not expand
        self.grid_rowconfigure(999, weight=1)  # Status row should be pushed to the bottom

    def add_header_row(self):
        """Dynamically add a row for a new header."""
        row_index = len(self.headers) + 2

        header_name_var = StringVar()
        header_value_var = StringVar()

        header_name_label = ttk.Label(self, text="Header Name:", font=("Arial", 14))
        header_name_label.grid(row=row_index, column=0, padx=20, pady=5, sticky="w")

        header_name_entry = ttk.Entry(self, textvariable=header_name_var, width=30)
        header_name_entry.grid(row=row_index, column=1, padx=20, pady=5)

        header_value_label = ttk.Label(self, text="Header Value:", font=("Arial", 14))
        header_value_label.grid(row=row_index, column=2, padx=20, pady=5, sticky="w")

        header_value_entry = ttk.Entry(self, textvariable=header_value_var, width=30)
        header_value_entry.grid(row=row_index, column=3, padx=20, pady=5)

        self.headers.append((header_name_var, header_value_var))

    def modify_http_headers(self):
        """Apply modifications for all entered headers."""
        uploaded_file_paths = self.parent.file_upload_page.get_uploaded_files()

        if not uploaded_file_paths:
            self.status_label.config(text="No files uploaded!", bootstyle="danger")
            return

        headers_to_modify = {}
        for header_name_var, header_value_var in self.headers:
            header_name = header_name_var.get().strip()
            header_value = header_value_var.get().strip()
            if header_name and header_value:
                headers_to_modify[header_name] = header_value

        if not headers_to_modify:
            self.status_label.config(text="Please enter at least one header name and value.", bootstyle="danger")
            return

        error_message = None
        for file_path in uploaded_file_paths:
            try:
                self.modify_http_headers_backend(file_path, headers_to_modify)
            except ValueError as e:
                error_message = str(e)
                break

        if error_message:
            self.status_label.config(text=error_message, bootstyle="danger")
        else:
            self.status_label.config(text="HTTP Headers Modified Successfully!", bootstyle="success")

    @staticmethod
    def modify_http_headers_backend(file_path, headers):
        try:
            # Initialize JMXModifier with the uploaded file path
            modifier = JMXModifier(file_path)

            # Call the method to modify all HTTP headers
            modifier.modify_http_headers(headers)

            # Save the modified file with a new name
            output_path = file_path.replace(".jmx", "_modified.jmx")
            modifier.save_changes(output_path)

        except Exception as e:
            raise ValueError(f"Error modifying file {file_path}: {str(e)}")

    def go_back_to_home(self):
        """Go back to the file upload page and reset the file list."""
        # Reset the uploaded file list in the file upload page
        self.parent.file_upload_page.uploaded_file_paths = []

        # Clear the listbox to show an empty state
        self.parent.file_upload_page.file_listbox.delete(0, 'end')

        # Reset the status label
        self.parent.file_upload_page.status_label.config(text="")

        # Hide the 'Next Page' button initially
        self.parent.file_upload_page.next_page_button.grid_remove()

        # Clear status label in HttpHeaderPage (this clears success/error message)
        self.status_label.config(text="")

        # Reset the HTTP Header fields (clear existing header rows and messages)
        # enable this method if you want to reset header page on re-starting
        #self.reset_http_headers()

        # Show the file upload page
        self.parent.show_page(self.parent.file_upload_page)

    def reset_http_headers(self):
        """Reset the HTTP Header fields to their initial state."""

        # Clear all dynamically added header input fields and labels
        for widget in self.grid_slaves():
            if isinstance(widget, ttk.Entry) or isinstance(widget, ttk.Label):
                widget.grid_forget()

        # Reinitialize the headers list and add the first empty header row
        self.headers = []  # Clear all previously entered headers
        self.add_header_row()  # Add a fresh header row