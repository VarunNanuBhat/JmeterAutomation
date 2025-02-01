import ttkbootstrap as ttk

class ListDomains(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=20)
        self.parent = parent

        # List to store the selected domain names
        self.selected_domain_names = []  # Store BooleanVar objects for checkboxes

        # Action variable for radio buttons
        self.action_var = ttk.StringVar(value="")

        # Title Label
        title_label = ttk.Label(self, text="List of Domain Names", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=4, pady=10)

        # Scrollable Frame
        self.scrollable_frame = ttk.Frame(self)
        self.scrollable_frame.grid(row=1, column=0, columnspan=4, pady=20, sticky="nsew")

        # Add a Canvas for Scrollable Content
        self.canvas = ttk.Canvas(self.scrollable_frame)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        # Add a Vertical Scrollbar
        self.scrollbar = ttk.Scrollbar(self.scrollable_frame, orient="vertical", command=self.canvas.yview)
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Frame for the checkboxes inside the canvas
        self.checkbox_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.checkbox_frame, anchor="nw")

        # Add the Modify Endpoints button
        modify_button = ttk.Button(
            self, text="Modify Endpoints", bootstyle="primary", command=self.navigate_to_modify_domain
        )
        modify_button.grid(row=2, column=0, pady=10, padx=10, sticky="w")

        # Add the Delete Domains button
        delete_button = ttk.Button(
            self, text="Delete Domains", bootstyle="danger", command=self.navigate_to_delete_domains
        )
        delete_button.grid(row=2, column=1, pady=10, padx=10, sticky="w")

        # Radio Buttons for Action Selection
        action_label = ttk.Label(self, text="Select Action:", font=("Arial", 14))
        action_label.grid(row=3, column=0, padx=20, pady=10, sticky="w")

        # Uniform padding for radio buttons
        ttk.Radiobutton(self, text="Enable", variable=self.action_var, value="enable").grid(row=4, column=1, pady=5, sticky="w")
        ttk.Radiobutton(self, text="Disable", variable=self.action_var, value="disable").grid(row=5, column=1, pady=5, sticky="w")
        ttk.Radiobutton(self, text="Delete", variable=self.action_var, value="delete").grid(row=6, column=1, pady=5, sticky="w")

        # Add Go Back button
        back_button = ttk.Button(self, text="Go Back", bootstyle="secondary", command=self.go_back_to_http_header_page)
        back_button.grid(row=3, column=3, pady=20, padx=20, sticky="e")

    def populate_domain_names(self, domain_names):
        """Populate domain names with checkboxes."""
        self.domain_names = domain_names  # Store the domain names list

        # Clear previous checkboxes
        for widget in self.checkbox_frame.winfo_children():
            widget.destroy()

        self.selected_domain_names = []  # Reset selected domain names

        # Create a Checkbutton for each domain in the list
        for i, domain in enumerate(self.domain_names):
            var = ttk.BooleanVar(value=False)  # Set initial state to False (unselected)
            check_button = ttk.Checkbutton(self.checkbox_frame, text=domain, variable=var)
            check_button.grid(row=i, column=0, sticky="w", padx=10, pady=5)
            self.selected_domain_names.append(var)  # Store BooleanVar

        # Update the scroll region of the canvas after adding checkboxes
        self.checkbox_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def get_selected_domain_names(self):
        """Return the list of selected domain names."""
        selected = []
        for i, var in enumerate(self.selected_domain_names):
            if var.get():  # Check if checkbox is selected
                selected.append(self.domain_names[i])
        return selected

    def navigate_to_modify_domain(self):
        """Navigate to the ModifySelectedDomainsPage with the selected domains."""
        selected_domain_names = self.get_selected_domain_names()
        if not selected_domain_names:
            print("No domains selected for modification!")  # Debugging message
            return

        # Pass selected domains to the ModifySelectedDomainsPage
        self.parent.modify_selected_domains_page.populate_domain_names(selected_domain_names)

        # Show the modify domains page
        self.parent.show_page(self.parent.modify_selected_domains_page)

    def navigate_to_delete_domains(self):
        """Navigate to the DeleteSelectedDomainsPage with the selected domains."""
        selected_domain_names = self.get_selected_domain_names()
        if not selected_domain_names:
            print("No domain names selected for deletion!")  # Debugging message
            return

        # Pass selected domains to the DeleteSelectedDomainsPage
        self.parent.delete_selected_domains.populate_domain_names(selected_domain_names)

        # Show the delete domains page
        self.parent.show_page(self.parent.delete_selected_domains)

    def go_back_to_http_header_page(self):
        """Navigate back to the HTTP Header Page."""
        self.parent.show_page(self.parent.http_header_page)
