import ttkbootstrap as ttk
from jmeter_methods.Jmeter_Automation_Methods import JMXModifier
from pathlib import Path


class DeleteSelectedHeadersPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=20)
        self.parent = parent

        # Title Label
        title_label = ttk.Label(self, text="Delete Selected Headers", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=4, pady=10)

        # Frame to hold selected headers and their corresponding checkboxes
        self.headers_frame = ttk.Frame(self)
        self.headers_frame.grid(row=1, column=0, columnspan=4, pady=10)

        # Add "Delete Selected" button
        delete_button = ttk.Button(self, text="🗑 Delete", bootstyle="danger", command=self.delete_selected_headers)
        delete_button.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

        # Add "Back" button next to "Delete"
        back_button = ttk.Button(self, text="🔙 Back", bootstyle="secondary", command=self.go_back_to_list_headers_page)
        back_button.grid(row=2, column=1, padx=10, pady=10, sticky="ew")

        # Add a status label to display success or error messages (Use grid instead of pack)
        self.status_label = ttk.Label(self, text="", font=("Arial", 12, "bold"), bootstyle="info")
        self.status_label.grid(row=3, column=0, columnspan=2, pady=10, sticky="ew")

    def populate_headers(self, headers):
        """Populate the headers with checkboxes to delete (pre-selected)."""
        self.headers = headers  # Store the headers list

        # Clear the previous checkboxes
        for widget in self.headers_frame.winfo_children():
            widget.destroy()

        self.selected_headers = []  # Reset selected headers list

        # Create a Checkbutton for each header, ensuring they are pre-selected
        for i, header in enumerate(self.headers):
            var = ttk.BooleanVar(value=True)  # Set initial state to True (pre-selected)
            check_button = ttk.Checkbutton(self.headers_frame, text=header, variable=var)
            check_button.grid(row=i, column=0, sticky="w", padx=10, pady=5)
            self.selected_headers.append(var)

    def get_selected_headers(self):
        """Return the list of selected headers for deletion."""
        return [self.headers[i] for i, var in enumerate(self.selected_headers) if var.get()]

    def delete_selected_headers(self):
        """Delete the selected headers from the JMX files."""
        selected_headers = self.get_selected_headers()

        if not selected_headers:
            self.status_label.config(text="No headers selected for deletion!", bootstyle="danger")
            return

        uploaded_files = self.parent.file_upload_page.get_uploaded_files()

        if not uploaded_files:
            self.status_label.config(text="No JMX files uploaded!", bootstyle="danger")
            return

        # Perform deletion
        try:
            for file_path in uploaded_files:
                modifier = JMXModifier(file_path)
                for header in selected_headers:
                    modifier.delete_http_header(header)

                # Save changes
                output_path = Path(file_path).with_name(f"{Path(file_path).stem}_modified.jmx")
                modifier.save_changes(str(output_path))

            num_headers_deleted = len(selected_headers)
            self.status_label.config(text=f"✅ {num_headers_deleted} Headers deleted successfully!", bootstyle="success")
            self.after(2000, self.go_back_to_file_upload)
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}", bootstyle="danger")
            return

    def go_back_to_list_headers_page(self):
        """Navigate back to the ListHeadersPage."""
        self.parent.show_page(self.parent.http_header_list_page)


    def go_back_to_file_upload(self):
        # Reset the status label
        self.parent.file_upload_page.status_label.config(text="")

        # Clear status label in HttpHeaderPage (this clears success/error message)
        self.status_label.config(text="")

        # Show the file upload page
        self.parent.show_page(self.parent.file_upload_page)
