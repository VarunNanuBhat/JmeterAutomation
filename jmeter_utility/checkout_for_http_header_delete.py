import ttkbootstrap as ttk
from tkinter import StringVar, ttk
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

        # Back and Confirm Buttons
        back_button = ttk.Button(self, text="🔙 Back", bootstyle="secondary", command=self.go_back_to_delete_page)
        back_button.pack(side="left", padx=20, pady=10)

        confirm_button = ttk.Button(self, text="Confirm Deletions", bootstyle="success", command=self.confirm_deletions)
        confirm_button.pack(side="right", padx=20, pady=10)

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
        if not uploaded_files:
            self.parent.file_upload_page.status_label.config(text="No files uploaded!", bootstyle="danger")
            return

        if not self.headers_to_delete:
            self.parent.file_upload_page.status_label.config(text="No headers selected for deletion!", bootstyle="danger")
            return

        # Perform deletion
        try:
            for file_path in uploaded_files:
                modifier = JMXModifier(file_path)
                for header in self.headers_to_delete:
                    modifier.delete_http_header(header)

                # Save changes
                output_path = file_path.replace(".jmx", "_modified.jmx")
                modifier.save_changes(output_path)

            self.parent.file_upload_page.status_label.config(text="Headers deleted successfully!", bootstyle="success")
            self.parent.show_page(self.parent.file_upload_page)

        except Exception as e:
            self.parent.file_upload_page.status_label.config(text=f"Error: {str(e)}", bootstyle="danger")