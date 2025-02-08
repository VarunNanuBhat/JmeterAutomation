import ttkbootstrap as ttk
from tkinter import Frame, BOTH
from jmeter_methods.Jmeter_Automation_Methods import JMXModifier


class CheckoutPageForHeaderModify(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=20)
        self.parent = parent
        self.headers_displayed = {}  # Store displayed headers

        # Title Label
        title_label = ttk.Label(self, text="Checkout Page", font=("Arial", 18, "bold"))
        title_label.pack(pady=10)

        # Frame for header modifications
        self.preview_frame = ttk.Frame(self)
        self.preview_frame.pack(fill=BOTH, expand=True, pady=20)

        # Button Frame (For Back & Confirm)
        button_frame = ttk.Frame(self)
        button_frame.pack(fill="x", pady=10)

        # Back Button
        back_button = ttk.Button(button_frame, text="Back", bootstyle="danger", command=self.go_back_to_header_modify)
        back_button.pack(side="left", padx=20, pady=10)

        # Confirm Button
        confirm_button = ttk.Button(button_frame, text="Confirm Changes", bootstyle="success", command=self.confirm_changes)
        confirm_button.pack(side="right", padx=20, pady=10)

        # 🔥 Status Label (To show success/error messages)
        self.status_label = ttk.Label(self, text="", font=("Arial", 12, "bold"), bootstyle="info")
        self.status_label.pack(pady=10)

    def display_modifications(self, headers_to_modify):
        """Display the headers and their new values in the preview frame."""
        self.headers_displayed = headers_to_modify  # Save headers for later use

        # Clear existing content in the preview frame
        for widget in self.preview_frame.winfo_children():
            widget.destroy()

        # Header row for the table
        ttk.Label(self.preview_frame, text="Header Name", font=("Arial", 14, "bold")).grid(row=0, column=0, padx=20, pady=5)
        ttk.Label(self.preview_frame, text="Header Value", font=("Arial", 14, "bold")).grid(row=0, column=1, padx=20, pady=5)

        # Populate headers
        for row, (header_name, header_value) in enumerate(headers_to_modify.items(), start=1):
            ttk.Label(self.preview_frame, text=header_name, font=("Arial", 12)).grid(row=row, column=0, padx=20, pady=5, sticky="w")
            ttk.Label(self.preview_frame, text=header_value, font=("Arial", 12)).grid(row=row, column=1, padx=20, pady=5, sticky="w")


    def confirm_changes(self):
        """Confirm the changes and apply modifications."""
        headers_to_modify = self.headers_displayed  # Retrieve saved headers
        uploaded_file_paths = self.parent.file_upload_page.get_uploaded_files()

        if not uploaded_file_paths:
            self.status_label.config(text="❌ No files uploaded!", bootstyle="danger")
            return

        if not headers_to_modify:
            self.status_label.config(text="❌ No headers to modify!", bootstyle="danger")
            return

        # Apply changes to each file
        error_message = None
        for file_path in uploaded_file_paths:
            try:
                self.modify_http_headers_backend(file_path, headers_to_modify)
            except ValueError as e:
                error_message = str(e)
                break

        # Update status with success or error message
        if error_message:
            self.status_label.config(text=f"❌ {error_message}", bootstyle="danger")
            #self.after(2000, self.go_back_to_file_upload) # if you want to land at file upload page
            return
        else:
            num_headers_modified = len(headers_to_modify)
            self.status_label.config(text=f"✅ {num_headers_modified} headers modified successfully!", bootstyle="success")
            self.after(2000, self.go_back_to_file_upload)


    def go_back_to_header_modify(self):
        self.parent.show_page(self.parent.http_header_modify_page)

    def go_back_to_file_upload(self):
        # Reset the uploaded file list in the file upload page
        #self.parent.file_upload_page.uploaded_file_paths = []

        # Clear the listbox to show an empty state
        # self.parent.file_upload_page.file_listbox.delete(0, 'end')

        # Reset the status label
        self.parent.file_upload_page.status_label.config(text="")

        # Hide the 'Next Page' button initially
        # self.parent.file_upload_page.next_page_button.grid_remove()

        # Clear status label in HttpHeaderPage (this clears success/error message)
        self.status_label.config(text="")

        # Reset the HTTP Header fields (clear existing header rows and messages)
        # enable this method if you want to reset header page on re-starting
        # self.reset_http_headers()

        # Show the file upload page
        self.parent.show_page(self.parent.file_upload_page)


    @staticmethod
    def modify_http_headers_backend(file_path, headers):
        """Backend logic to modify HTTP headers in the provided JMX file."""
        try:
            # Initialize JMXModifier with the uploaded file path
            modifier = JMXModifier(file_path)

            # Modify HTTP headers using the provided dictionary
            modifier.modify_http_headers(headers)

            # Save the modified file with a new name
            output_path = file_path.replace(".jmx", "_modified.jmx")
            modifier.save_changes(output_path)

        except Exception as e:
            raise ValueError(f"Error modifying file {file_path}: {str(e)}")
