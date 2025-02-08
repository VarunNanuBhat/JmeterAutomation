import ttkbootstrap as ttk
from tkinter import StringVar
from pathlib import Path
from jmeter_methods.Jmeter_Automation_Methods import JMXModifier

class ModifySelectedHeadersPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=20)
        self.parent = parent

        # Title Label
        title_label = ttk.Label(self, text="Modify Selected Headers", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=4, pady=10)

        # Frame to hold selected headers and their corresponding textboxes
        self.headers_frame = ttk.Frame(self)
        self.headers_frame.grid(row=1, column=0, columnspan=4, pady=10)

        # Add "Apply Changes" button
        apply_changes_button = ttk.Button(self, text="Apply Changes", bootstyle="primary", command=self.apply_changes)
        apply_changes_button.grid(row=2, column=0, columnspan=4, pady=10)

        # Add a "Back" button to go back to the ListHeadersPage
        back_button = ttk.Button(self, text="Go Back", bootstyle="danger", command=self.go_back_to_list_headers_page)
        back_button.grid(row=3, column=3, pady=20, padx=20, sticky="e")

        # Add a status label to display success or error messages
        self.status_label = ttk.Label(self, text="", font=("Arial", 12), anchor="w")
        self.status_label.grid(row=4, column=0, columnspan=4, pady=10, sticky="w")

    def populate_headers(self, selected_headers):
        """Populate the selected headers with textboxes to modify their values."""
        self.selected_headers = selected_headers  # Store the selected headers

        # Clear the previous entries
        for widget in self.headers_frame.winfo_children():
            widget.destroy()

        self.header_entries = []  # List to store Entry widgets

        # Create a Label and Entry for each selected header
        for i, header in enumerate(self.selected_headers):
            # Display the header as a label
            header_label = ttk.Label(self.headers_frame, text=header, font=("Arial", 14))
            header_label.grid(row=i, column=0, padx=10, pady=5, sticky="w")

            # Create an Entry widget to input the new value for this header
            new_value_entry = ttk.Entry(self.headers_frame, width=40)
            new_value_entry.grid(row=i, column=1, padx=10, pady=5)
            self.header_entries.append(new_value_entry)

    def apply_changes(self):
        """Apply the modifications to the selected headers."""
        uploaded_file_paths = self.parent.file_upload_page.get_uploaded_files()

        if not uploaded_file_paths:
            self.status_label.config(text="❌ No files uploaded!", bootstyle="danger")
            return

        headers_to_modify = {}
        for i, entry in enumerate(self.header_entries):
            new_value = entry.get().strip()
            if new_value:
                headers_to_modify[self.selected_headers[i]] = new_value

        if not headers_to_modify:
            self.status_label.config(text="❌ Please enter at least one header value.", bootstyle="danger")
            return

        # Apply changes to each file
        error_message = None
        for file_path in uploaded_file_paths:
            try:
                self.modify_http_headers_backend(file_path, headers_to_modify)
            except ValueError as e:
                error_message = str(e)
                break  # Stop processing if an error occurs

        # Update status with success or error message
        if error_message:
            self.status_label.config(text=f"❌ {error_message}", bootstyle="danger")
            return  # Stay on the same page to show the error message
        else:
            num_headers_modified = len(headers_to_modify)
            self.status_label.config(text=f"✅ {num_headers_modified} headers modified successfully!",
                                     bootstyle="success")
            #self.after(2000, self.go_back_to_list_headers_page)  # Redirect after 2s
            self.after(2000, self.go_back_to_file_upload)



    @staticmethod
    def modify_http_headers_backend(file_path, headers):
        try:
            # Initialize JMXModifier with the uploaded file path
            modifier = JMXModifier(file_path)

            # Call the method to modify all HTTP headers
            modifier.modify_http_headers(headers)

            # Save the modified file with a new name
            output_path = Path(file_path).with_name(f"{Path(file_path).stem}_modified.jmx")
            modifier.save_changes(output_path)

        except Exception as e:
            raise ValueError(f"Error modifying file {file_path}: {str(e)}")

    def go_back_to_list_headers_page(self):
        """Navigate back to the ListHeadersPage."""
        self.parent.show_page(self.parent.http_header_list_page)


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
