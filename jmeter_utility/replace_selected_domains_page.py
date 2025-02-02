import ttkbootstrap as ttk
from tkinter import StringVar
from jmeter_methods.Jmeter_Automation_Methods import JMXModifier

class ReplaceSelectedDomainsPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=20)
        self.parent = parent

        # Title Label
        title_label = ttk.Label(self, text="Replace Selected Domains", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=4, pady=10)

        # Frame to hold selected domains and their corresponding textboxes
        self.domains_frame = ttk.Frame(self)
        self.domains_frame.grid(row=1, column=0, columnspan=4, pady=10)

        # "Apply Changes" button
        apply_changes_button = ttk.Button(self, text="Apply Changes", bootstyle="primary", command=self.apply_changes)
        apply_changes_button.grid(row=2, column=0, columnspan=4, pady=10)

        # "Back" button to go back to the ListDomains page
        back_button = ttk.Button(self, text="Go Back", bootstyle="danger", command=self.go_back_to_list_domains_page)
        back_button.grid(row=3, column=3, pady=20, padx=20, sticky="e")

        # Status Label to display success/error messages
        self.status_label = ttk.Label(self, text="", font=("Arial", 12), anchor="w")
        self.status_label.grid(row=4, column=0, columnspan=4, pady=10, sticky="w")

    def populate_domain_names(self, selected_domains):
        """Populate the selected domains with textboxes to enter new values."""
        self.selected_domains = selected_domains  # Store the selected domains

        # Clear the previous entries
        for widget in self.domains_frame.winfo_children():
            widget.destroy()

        self.domain_entries = []  # List to store Entry widgets

        # Create a Label and Entry for each selected domain
        for i, domain in enumerate(self.selected_domains):
            # Display the domain as a label
            domain_label = ttk.Label(self.domains_frame, text=domain, font=("Arial", 14))
            domain_label.grid(row=i, column=0, padx=10, pady=5, sticky="w")

            # Create an Entry widget to input the new domain value
            new_domain_entry = ttk.Entry(self.domains_frame, width=40)
            new_domain_entry.grid(row=i, column=1, padx=10, pady=5)
            self.domain_entries.append(new_domain_entry)

    def apply_changes(self):
        """Apply the domain modifications."""
        uploaded_file_paths = self.parent.file_upload_page.get_uploaded_files()

        if not uploaded_file_paths:
            self.status_label.config(text="No files uploaded!", bootstyle="danger")
            return

        domains_to_replace = {}
        for i, entry in enumerate(self.domain_entries):
            new_value = entry.get().strip()
            if new_value:
                domains_to_replace[self.selected_domains[i]] = new_value

        if not domains_to_replace:
            self.status_label.config(text="Please enter at least one new domain value.", bootstyle="danger")
            return

        error_message = None
        for file_path in uploaded_file_paths:
            try:
                self.replace_domains_backend(file_path, domains_to_replace)
            except ValueError as e:
                error_message = str(e)
                break

        if error_message:
            self.status_label.config(text=error_message, bootstyle="danger")
        else:
            self.status_label.config(text="Domains Replaced Successfully!", bootstyle="success")

    @staticmethod
    def replace_domains_backend(file_path, domains):
        try:
            # Call JMXModifier to replace domains
            modifier = JMXModifier(file_path)

            for old_domain, new_domain in domains.items():
                modifier.replace_domain_name(old_domain, new_domain)

            # Save the modified file with a new name
            output_path = file_path.replace(".jmx", "_modified.jmx")
            modifier.save_changes(output_path)

        except Exception as e:
            raise ValueError(f"Error modifying file {file_path}: {str(e)}")

    def go_back_to_list_domains_page(self):
        """Navigate back to the ListDomainsPage."""
        self.parent.show_page(self.parent.list_domains_page)
