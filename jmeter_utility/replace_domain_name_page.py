import ttkbootstrap as ttk
from tkinter import StringVar, ttk
from tkinter import messagebox
from jmeter_methods.Jmeter_Automation_Methods import JMXModifier


class ReplaceDomainNamePage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=20)
        self.parent = parent

        # Store multiple domain pairs
        self.domains_to_replace = []

        # Title for the page
        title_label = ttk.Label(self, text="Replace Domain Name in Requests", font=("Arial", 22, "bold"))
        title_label.grid(row=0, column=0, columnspan=4, pady=20)

        # Add Domain button
        add_button = ttk.Button(self, text="+ Add Domain", bootstyle="success", command=self.add_domain_row)
        add_button.grid(row=1, column=0, pady=20, padx=20, sticky="ew")

        # Preview Changes button
        preview_button = ttk.Button(self, text="👁 Preview Changes", bootstyle="primary", command=self.navigate_to_checkout)
        preview_button.grid(row=1, column=3, pady=20, padx=20, sticky="ew")

        # List Domains button
        list_button = ttk.Button(self, text="📜 List Domains", bootstyle="info",
                                 command=self.navigate_to_list_domain_names)
        list_button.grid(row=1, column=1, pady=20, padx=20, sticky="ew")

        # Home page button
        home_button = ttk.Button(self, text="🏠 Home", bootstyle="secondary", command=self.go_back_to_home)
        home_button.grid(row=1, column=2, pady=20, padx=20, sticky="ew")


        # Status Label
        self.status_label = ttk.Label(self, text="", font=("Arial", 14), anchor="center")
        self.status_label.grid(row=999, column=0, columnspan=4, pady=10)

        # Add the first input row by default
        self.add_domain_row()

    def add_domain_row(self):
        """Dynamically add a new row for entering a domain replacement pair."""
        row_index = len(self.domains_to_replace) + 2

        old_domain_var = StringVar()
        new_domain_var = StringVar()

        # Old Domain Entry
        old_domain_label = ttk.Label(self, text=f"Old Domain {row_index - 1}:", font=("Arial", 12))
        old_domain_label.grid(row=row_index, column=0, padx=10, pady=5, sticky="w")

        old_domain_entry = ttk.Entry(self, textvariable=old_domain_var, width=30)
        old_domain_entry.grid(row=row_index, column=1, padx=10, pady=5)

        # New Domain Entry
        new_domain_label = ttk.Label(self, text="New Domain:", font=("Arial", 12))
        new_domain_label.grid(row=row_index, column=2, padx=10, pady=5, sticky="w")

        new_domain_entry = ttk.Entry(self, textvariable=new_domain_var, width=30)
        new_domain_entry.grid(row=row_index, column=3, padx=10, pady=5)

        # Store the entry variables
        self.domains_to_replace.append((old_domain_var, new_domain_var))

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

            self.parent.domain_list_page.populate_domain_names(list(sorted(unique_domain_names)))
            self.parent.show_page(self.parent.domain_list_page)

        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}", bootstyle="danger")


    def navigate_to_checkout(self):
        """Navigate to the checkout page to preview domain replacements."""
        domain_pairs = [(old_var.get().strip(), new_var.get().strip()) for old_var, new_var in self.domains_to_replace]
        domain_pairs = [(old, new) for old, new in domain_pairs if old and new]  # Remove empty fields

        if not domain_pairs:
            self.status_label.config(text="Please enter at least one domain pair.", bootstyle="danger")
            return

        self.parent.checkout_for_replace_domain_page.display_changes(domain_pairs)
        self.parent.show_page(self.parent.checkout_for_replace_domain_page)

    def replace_domain(self):
        """Replace all specified domains in the uploaded JMX files."""
        domain_pairs = [(old_var.get().strip(), new_var.get().strip()) for old_var, new_var in self.domains_to_replace]
        domain_pairs = [(old, new) for old, new in domain_pairs if old and new]  # Remove empty fields

        if not domain_pairs:
            self.status_label.config(text="Please enter at least one domain pair.", bootstyle="danger")
            return

        try:
            error_message = None
            for file_path in self.parent.file_upload_page.uploaded_file_paths:
                error_message = self.replace_domain_backend(file_path, domain_pairs)
                if error_message:
                    break  # Stop if an error occurs

            if error_message:
                self.status_label.config(text=error_message, bootstyle="danger")
            else:
                self.status_label.config(text="Domains replaced successfully!", bootstyle="success")

        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}", bootstyle="danger")

    def replace_domain_backend(self, file_path, domain_pairs):
        """Replace multiple domain names in the JMX file."""
        try:
            modifier = JMXModifier(file_path)

            for old_domain, new_domain in domain_pairs:
                modifier.replace_domain_name(old_domain, new_domain)

            #output_path = file_path.replace(".jmx", "_modified.jmx")
            #modifier.save_changes(output_path)
            modifier.save_changes(file_path)

            return None  # No errors

        except ValueError as e:
            return f"Error: {str(e)}"
        except Exception as e:
            return f"Error modifying file {file_path}: {str(e)}"

    def go_back_to_home(self):
        """Go back to the file upload page and reset the file list."""
        # self.parent.file_upload_page.uploaded_file_paths = []
        # self.parent.file_upload_page.file_listbox.delete(0, 'end')
        self.parent.file_upload_page.status_label.config(text="")
        # self.parent.file_upload_page.next_page_button.grid_remove()
        self.status_label.config(text="")
        # self.reset_domain_entries()
        self.parent.show_page(self.parent.file_upload_page)


    def reset_domain_entries(self):
        """Reset the domain entry fields to their initial state."""
        for widget in self.grid_slaves():
            if isinstance(widget, ttk.Entry) or isinstance(widget, ttk.Label):
                widget.grid_forget()

        self.domains_to_modify = []
        self.add_domain_row()
