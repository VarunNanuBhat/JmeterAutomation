import ttkbootstrap as ttk
from tkinter import Frame, BOTH
from jmeter_methods.Jmeter_Automation_Methods import JMXModifier


class CheckoutPageForReplaceDomain(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=20)
        self.parent = parent
        self.domain_replacements = []  # Stores domain replacement pairs

        # Title Label
        title_label = ttk.Label(self, text="Checkout Page - Replace Domain", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)

        # Frame for previewing domain replacements
        self.preview_frame = ttk.Frame(self)
        self.preview_frame.pack(fill=BOTH, expand=True, pady=20)

        # Back Button
        back_button = ttk.Button(self, text="Go Back", bootstyle="danger", command=self.go_back_to_replace_domain)
        back_button.pack(side="left", padx=20, pady=10)

        # Confirm Button
        confirm_button = ttk.Button(self, text="Confirm Changes", bootstyle="success", command=self.confirm_changes)
        confirm_button.pack(side="right", padx=20, pady=10)

    def display_changes(self, domain_pairs):
        """Display the domain replacement pairs in the preview frame."""
        self.domain_replacements = domain_pairs  # Store for confirmation step

        # Clear existing content in the preview frame
        for widget in self.preview_frame.winfo_children():
            widget.destroy()

        # Header row for the table
        ttk.Label(self.preview_frame, text="Old Domain", font=("Arial", 14, "bold")).grid(row=0, column=0, padx=20, pady=5)
        ttk.Label(self.preview_frame, text="New Domain", font=("Arial", 14, "bold")).grid(row=0, column=1, padx=20, pady=5)

        # Populate the preview with entered domain pairs
        for row, (old_domain, new_domain) in enumerate(domain_pairs, start=1):
            ttk.Label(self.preview_frame, text=old_domain, font=("Arial", 12)).grid(row=row, column=0, padx=20, pady=5, sticky="w")
            ttk.Label(self.preview_frame, text=new_domain, font=("Arial", 12)).grid(row=row, column=1, padx=20, pady=5, sticky="w")

    def go_back_to_replace_domain(self):
        """Navigate back to the Replace Domain Name page."""
        self.parent.show_page(self.parent.replace_domain_page)

    def confirm_changes(self):
        """Apply the domain replacements to the uploaded JMX files."""
        domain_pairs = self.domain_replacements
        uploaded_file_paths = self.parent.file_upload_page.uploaded_file_paths

        if not uploaded_file_paths:
            self.parent.file_upload_page.status_label.config(text="No files uploaded!", bootstyle="danger")
            return

        if not domain_pairs:
            self.parent.file_upload_page.status_label.config(text="No domain replacements provided!", bootstyle="danger")
            return

        # Apply changes to each file
        error_message = None
        for file_path in uploaded_file_paths:
            try:
                self.replace_domain_backend(file_path, domain_pairs)
            except ValueError as e:
                error_message = str(e)
                break

        # Update status
        if error_message:
            self.parent.file_upload_page.status_label.config(text=error_message, bootstyle="danger")
        else:
            self.parent.file_upload_page.status_label.config(text="Domain Replacements Applied Successfully!", bootstyle="success")

    @staticmethod
    def replace_domain_backend(file_path, domain_pairs):
        """Backend logic to replace domain names in the provided JMX file."""
        try:
            # Initialize JMXModifier with the uploaded file path
            modifier = JMXModifier(file_path)

            # Replace each domain pair in the file
            for old_domain, new_domain in domain_pairs:
                modifier.replace_domain_name(old_domain, new_domain)

            # Save the modified file with a new name
            output_path = file_path.replace(".jmx", "_modified.jmx")
            modifier.save_changes(output_path)

        except Exception as e:
            raise ValueError(f"Error modifying file {file_path}: {str(e)}")
