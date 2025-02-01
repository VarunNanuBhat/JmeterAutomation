import ttkbootstrap as ttk
from tkinter import StringVar
from jmeter_methods.Jmeter_Automation_Methods import JMXModifier


class EndpointActionPageForDomain(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=20)
        self.parent = parent
        self.domains_to_modify = []
        self.action_var = StringVar(value="")

        # Title Label
        title_label = ttk.Label(self, text="Endpoint Modifier", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=4, pady=10)

        # Add Domain button
        add_button = ttk.Button(self, text="+ Add Domain", bootstyle="success", command=self.add_domain_row)
        add_button.grid(row=1, column=0, pady=20, padx=20, sticky="w")

        # Preview Changes button
        preview_button = ttk.Button(self, text="Preview Changes", bootstyle="primary", command=self.navigate_to_checkout)
        preview_button.grid(row=1, column=3, pady=20, padx=20, sticky="e")

        # List Domains button
        list_button = ttk.Button(self, text="List Domains", bootstyle="info", command=self.navigate_to_list_domain_names)
        list_button.grid(row=1, column=1, pady=20, padx=20, sticky="e")

        # Go Back button
        back_button = ttk.Button(self, text="Go Back", bootstyle="danger", command=self.go_back_to_home)
        back_button.grid(row=1, column=2, pady=20, padx=20, sticky="e")

        # Action Selection
        action_label = ttk.Label(self, text="Select Action:", font=("Arial", 14))
        action_label.grid(row=2, column=0, padx=20, pady=10, sticky="w")

        ttk.Radiobutton(self, text="Enable", variable=self.action_var, value="enable").grid(row=2, column=1, padx=10, pady=5, sticky="w")
        ttk.Radiobutton(self, text="Disable", variable=self.action_var, value="disable").grid(row=2, column=2, padx=10, pady=5, sticky="w")
        ttk.Radiobutton(self, text="Delete", variable=self.action_var, value="delete").grid(row=2, column=3, padx=10, pady=5, sticky="w")

        # Status Label
        self.status_label = ttk.Label(self, text="", font=("Arial", 14), anchor="center", wraplength=500)
        self.status_label.grid(row=999, column=0, columnspan=4, pady=10, padx=20, sticky="s")

        # Configure grid row weight
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(999, weight=1)

        # Add the first domain input row by default
        self.add_domain_row()

    def add_domain_row(self):
        """Dynamically add a row for entering a domain to modify."""
        row_index = len(self.domains_to_modify) + 3
        domain_var = StringVar()

        domain_label = ttk.Label(self, text=f"Domain {row_index - 2}:", font=("Arial", 14))
        domain_label.grid(row=row_index, column=0, padx=20, pady=5, sticky="w")

        domain_entry = ttk.Entry(self, textvariable=domain_var, width=50)
        domain_entry.grid(row=row_index, column=1, columnspan=2, padx=20, pady=5, sticky="w")

        self.domains_to_modify.append(domain_var)

    def navigate_to_list_domain_names(self):
        """Navigate to the List Domain Names page."""
        try:
            uploaded_file_paths = self.parent.file_upload_page.get_uploaded_files()
            if not uploaded_file_paths:
                self.status_label.config(text="No files uploaded!", bootstyle="danger")
                return

            unique_domain_names = set()
            for file_path in uploaded_file_paths:
                modifier = JMXModifier(file_path)
                unique_domain_names.update(modifier.list_unique_domain_names())

            self.parent.domain_list_page.populate_domain_names(list(unique_domain_names))
            self.parent.show_page(self.parent.domain_list_page)

        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}", bootstyle="danger")

    def navigate_to_checkout(self):
        """Navigate to the checkout page with selected domains and action."""
        domains = [domain.get().strip() for domain in self.domains_to_modify if domain.get().strip()]
        action = self.action_var.get()

        if not domains:
            self.status_label.config(text="Please enter at least one domain.", bootstyle="danger")
            return

        if not action:
            self.status_label.config(text="Please select an action.", bootstyle="danger")
            return

        self.parent.checkout_for_domain_page.display_changes(domains, action)
        self.parent.show_page(self.parent.checkout_for_domain_page)

    def go_back_to_home(self):
        """Go back to the file upload page and reset the file list."""
        self.parent.file_upload_page.uploaded_file_paths = []
        self.parent.file_upload_page.file_listbox.delete(0, 'end')
        self.parent.file_upload_page.status_label.config(text="")
        self.parent.file_upload_page.next_page_button.grid_remove()
        self.status_label.config(text="")

        self.reset_domain_entries()
        self.parent.show_page(self.parent.file_upload_page)

    def reset_domain_entries(self):
        """Reset the domain entry fields to their initial state."""
        for widget in self.grid_slaves():
            if isinstance(widget, ttk.Entry) or isinstance(widget, ttk.Label):
                widget.grid_forget()

        self.domains_to_modify = []
        self.add_domain_row()
