import ttkbootstrap as ttk
from tkinter import StringVar
from jmeter_methods.Jmeter_Automation_Methods import JMXModifier  # Import your JMXModifier module


class ModifySelectedDomainsPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=20)
        self.parent = parent
        self.selected_domains = []  # Store selected domain names
        self.action_var = StringVar(value="enable")  # Store common action

        # Title Label
        title_label = ttk.Label(self, text="Modify Selected Domains", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=10)

        # **Common Action Selection**
        action_label = ttk.Label(self, text="Select Action for All Domains:", font=("Arial", 14))
        action_label.grid(row=1, column=0, padx=20, pady=10, sticky="w")

        ttk.Radiobutton(self, text="Enable", variable=self.action_var, value="enable").grid(row=1, column=1, padx=5, sticky="w")
        ttk.Radiobutton(self, text="Disable", variable=self.action_var, value="disable").grid(row=1, column=2, padx=5, sticky="w")
        ttk.Radiobutton(self, text="Delete", variable=self.action_var, value="delete").grid(row=1, column=3, padx=5, sticky="w")

        # Scrollable Frame for domain list
        self.scrollable_frame = ttk.Frame(self)
        self.scrollable_frame.grid(row=2, column=0, columnspan=4, pady=10, sticky="nsew")

        # Canvas for scrolling
        self.canvas = ttk.Canvas(self.scrollable_frame)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        # Scrollbar
        self.scrollbar = ttk.Scrollbar(self.scrollable_frame, orient="vertical", command=self.canvas.yview)
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Inner frame inside canvas
        self.inner_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")

        # Buttons for navigation
        apply_changes = ttk.Button(self, text="🔄 Apply Changes", bootstyle="primary", command=self.apply_changes)
        apply_changes.grid(row=3, column=0, pady=20, padx=10, sticky="w")

        back_button = ttk.Button(self, text="🔙 Back", bootstyle="secondary", command=self.go_back_to_list_domains)
        back_button.grid(row=3, column=1, pady=20, padx=20, sticky="e")

        # Add a status label to display success or error messages
        self.status_label = ttk.Label(self, text="", font=("Arial", 12), anchor="w")
        self.status_label.grid(row=4, column=0, columnspan=4, pady=10, sticky="w")

        # Add a status label to display success or error messages
        self.status_label = ttk.Label(self, text="", font=("Arial", 12, "bold"), bootstyle="info", width=50,
                                      anchor="center")
        self.status_label.grid(row=4, column=0, columnspan=4, pady=10, sticky="n")

    def populate_domain_names(self, selected_domains):
        """Populate the page with selected domains."""
        # Clear previous entries
        for widget in self.inner_frame.winfo_children():
            widget.destroy()

        self.selected_domains = selected_domains  # Store original domain names

        # Create a label for each domain
        for i, domain in enumerate(selected_domains):
            domain_label = ttk.Label(self.inner_frame, text=domain, font=("Arial", 12))
            domain_label.grid(row=i, column=0, padx=10, pady=5, sticky="w")

        # Update canvas scroll area
        self.inner_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def apply_changes(self):
        """Apply the selected action (Enable, Disable, Delete) to selected domains."""
        try:
            uploaded_files = self.parent.file_upload_page.get_uploaded_files()
            if not uploaded_files:
                self.parent.file_upload_page.status_label.config(text="No files uploaded!", bootstyle="danger")
                return

            selected_action = self.action_var.get()

            if not self.selected_domains:
                self.parent.file_upload_page.status_label.config(text="No domains selected for modification!", bootstyle="danger")
                return

            for file_path in uploaded_files:
                modifier = JMXModifier(file_path)

                for domain in self.selected_domains:
                    if selected_action == "enable":
                        modifier.enable_domain_endpoints(domain)
                    elif selected_action == "disable":
                        modifier.disable_domain_endpoints(domain)
                    elif selected_action == "delete":
                        modifier.delete_domain_endpoints(domain)

                # Save the modified JMX file
                output_path = file_path.replace(".jmx", "_modified.jmx")
                modifier.save_changes(output_path)

            self.parent.file_upload_page.status_label.config(text="Changes applied successfully!", bootstyle="success")
            self.parent.show_page(self.parent.file_upload_page)

        except Exception as e:
            self.parent.file_upload_page.status_label.config(text=f"Error: {str(e)}", bootstyle="danger")

    def go_back_to_list_domains(self):
        """Go back to the List Domains page."""
        self.parent.show_page(self.parent.domain_list_page)
