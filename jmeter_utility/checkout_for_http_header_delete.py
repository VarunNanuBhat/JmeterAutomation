import ttkbootstrap as ttk
from tkinter import Frame, BOTH
from jmeter_methods.Jmeter_Automation_Methods import JMXModifier


class CheckoutPageForHeaderDelete(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=20)
        self.parent = parent
        self.headers_to_delete = []  # Store headers queued for deletion

        # Title Label
        title_label = ttk.Label(self, text="Checkout Page", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)

        # Frame for previewing deletions
        self.preview_frame = ttk.Frame(self)
        self.preview_frame.pack(fill=BOTH, expand=True, pady=20)

        # Button Frame (For Back & Confirm)
        button_frame = ttk.Frame(self)
        button_frame.pack(fill="x", pady=10)

        # Back Button
        back_button = ttk.Button(button_frame, text="🔙 Back", bootstyle="secondary", command=self.go_back_to_delete_page)
        back_button.pack(side="left", padx=20, pady=10)

        # Confirm Button
        confirm_button = ttk.Button(button_frame, text="✔ Confirm Deletions", bootstyle="success", command=self.confirm_deletions)
        confirm_button.pack(side="right", padx=20, pady=10)

        # 🔥 Status Label (To show success/error messages)
        self.status_label = ttk.Label(self, text="", font=("Arial", 12, "bold"), bootstyle="info")
        self.status_label.pack(pady=10)

    def display_deletions(self, headers):
        """Display the headers queued for deletion."""
        self.headers_to_delete = headers

        # Clear the preview frame
        for widget in self.preview_frame.winfo_children():
            widget.destroy()

        # Display headers to delete
        for idx, header in enumerate(headers, start=1):
            ttk.Label(self.preview_frame, text=f"{idx}. {header}", font=("Arial", 12)).pack(anchor="w", padx=20, pady=5)

    def go_back_to_delete_page(self):
        """Navigate back to the delete page."""
        self.parent.show_page(self.parent.http_header_delete_page)

    def confirm_deletions(self):
        """Apply the deletions and provide feedback."""
        uploaded_files = self.parent.file_upload_page.get_uploaded_files()

        # Show error message if no files are uploaded
        if not uploaded_files:
            self.status_label.config(text="❌ No JMX files uploaded!", bootstyle="danger")
            return

        # Show error message if no headers are selected for deletion
        if not self.headers_to_delete:
            self.status_label.config(text="❌ No headers selected for deletion!", bootstyle="danger")
            return

        # Perform deletion
        try:
            for file_path in uploaded_files:
                modifier = JMXModifier(file_path)
                for header in self.headers_to_delete:
                    modifier.delete_http_header(header)

                # Save changes
                #output_path = file_path.replace(".jmx", "_modified.jmx")
                #modifier.save_changes(output_path)
                modifier.save_changes(file_path)

            num_headers_deleted = len(self.headers_to_delete)
            self.status_label.config(text=f"✅ {num_headers_deleted} headers deleted successfully!", bootstyle="success")

            # Navigate back after 2 seconds
            self.after(2000, self.go_back_to_file_upload)

        except Exception as e:
            self.status_label.config(text=f"❌ Error: {str(e)}", bootstyle="danger")

    def go_back_to_file_upload(self):
        """Navigate back to the file upload page."""
        # Reset the status label
        self.status_label.config(text="")

        # Show the file upload page
        self.parent.show_page(self.parent.file_upload_page)
