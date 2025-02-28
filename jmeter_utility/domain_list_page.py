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
        title_label = ttk.Label(self, text="📜 List of Domain Names", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=4, pady=10)

        # Scrollable Frame
        self.scrollable_frame = ttk.Frame(self, padding=10)
        self.scrollable_frame.grid(row=1, column=0, columnspan=3, pady=5, sticky="nsew")

        # Add a Canvas for Scrollable Content
        self.canvas = ttk.Canvas(self.scrollable_frame, width=500, height=600)
        self.canvas.pack(side="left", fill="both", expand=True)

        # Add a Vertical Scrollbar
        self.scrollbar = ttk.Scrollbar(self.scrollable_frame, orient="vertical", command=self.canvas.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Frame for the checkboxes inside the canvas
        self.checkbox_frame = ttk.Frame(self.canvas, padding=10, width=380)
        self.canvas.create_window((0, 0), window=self.checkbox_frame, anchor="nw")

        button_frame = ttk.Frame(self)
        button_frame.grid(row=2, column=0, columnspan=3, pady=10, sticky="ew")

        # Add the Modify Endpoints button
        modify_button = ttk.Button(button_frame, text="✏ Modify Endpoints", bootstyle="primary", command=self.navigate_to_modify_domain)
        modify_button.pack(side="left", fill="x", expand=True, padx=5)

        # Add the replace Domains button
        delete_button = ttk.Button(button_frame, text="🗑 Replace Domains", bootstyle="danger", command=self.navigate_to_replace_domains)
        delete_button.pack(side="left", fill="x", expand=True, padx=5)

        home_button = ttk.Button(button_frame, text="🏠 Home", bootstyle="secondary", command=self.go_back_to_home)
        home_button.pack(side="left", fill="x", expand=True, padx=5)

        # Status Label for error messages
        self.status_label = ttk.Label(self, text="", font=("Arial", 12), bootstyle="danger")
        self.status_label.grid(row=3, column=0, columnspan=3, pady=10)

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
            self.status_label.config(text = "⚠ No domains selected for modification!", bootstyle="danger")  # Debugging message
            return

        # Pass selected domains to the ModifySelectedDomainsPage
        self.parent.modify_selected_domains_page.populate_domain_names(selected_domain_names)

        # Show the modify domains page
        self.parent.show_page(self.parent.modify_selected_domains_page)

    def navigate_to_replace_domains(self):
        """Navigate to the ReplaceSelectedDomainsPage with the selected domains."""
        selected_domain_names = self.get_selected_domain_names()
        if not selected_domain_names:
            self.status_label.config(text = "⚠ No domain names selected for replacement!", bootstyle="danger")  # Debugging message
            return

        # Pass selected domains to the ReplaceSelectedDomainsPage
        self.parent.replace_selected_domains_page.populate_domain_names(selected_domain_names)

        # Show the replace domains page
        self.parent.show_page(self.parent.replace_selected_domains_page)

    def go_back_to_http_header_page(self):
        """Navigate back to the HTTP Header Page."""
        self.parent.show_page(self.parent.http_header_page)

    def go_back_to_home(self):
        """Go back to the file upload page and reset the file list."""
        # Reset the status label
        self.parent.file_upload_page.status_label.config(text="")

        # Clear status label in HttpHeaderPage (this clears success/error message)
        # self.status_label.config(text="")

        # Show the file upload page
        self.parent.show_page(self.parent.file_upload_page)
