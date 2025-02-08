import ttkbootstrap as ttk
from tkinter import StringVar, ttk, messagebox
from jmeter_methods.Jmeter_Automation_Methods import JMXModifier


class EndpointActionPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=20)
        self.parent = parent
        self.endpoints = []  # List to store endpoint input fields
        self.action_var = StringVar(value="")  # No default selection

        # Title Label
        title_label = ttk.Label(self, text="🔗 Endpoint Modifier (By URL)", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=4, pady=10)

        # Add the first endpoint row by default
        self.add_endpoint_row()

        # Buttons with Icons
        add_button = ttk.Button(self, text="➕ Add Endpoint", bootstyle="success", command=self.add_endpoint_row)
        add_button.grid(row=1, column=0, pady=20, padx=20, sticky="ew")

        preview_button = ttk.Button(self, text="👁 Preview Changes", bootstyle="primary", command=self.navigate_to_checkout)
        preview_button.grid(row=1, column=1, pady=20, padx=20, sticky="ew")

        home_button = ttk.Button(self, text="🏠 Home", bootstyle="secondary", command=self.go_back_to_home)
        home_button.grid(row=1, column=2, pady=20, padx=20, sticky="ew")

        # Action Selection
        action_label = ttk.Label(self, text="⚡ Select Action:", font=("Arial", 14))
        action_label.grid(row=2, column=0, padx=20, pady=10, sticky="w")

        ttk.Radiobutton(self, text="✔ Enable", variable=self.action_var, value="enable").grid(row=2, column=1, padx=10, pady=5, sticky="w")
        ttk.Radiobutton(self, text="🚫 Disable", variable=self.action_var, value="disable").grid(row=2, column=2, padx=10, pady=5, sticky="w")
        ttk.Radiobutton(self, text="🗑 Delete", variable=self.action_var, value="delete").grid(row=2, column=3, padx=10, pady=5, sticky="w")

        # Status Label
        self.status_label = ttk.Label(self, text="", font=("Arial", 14), anchor="center", wraplength=500)
        self.status_label.grid(row=999, column=0, columnspan=4, pady=10, padx=20, sticky="s")

        # Configure grid row weight
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(999, weight=1)

    def add_endpoint_row(self):
        """Dynamically add a row for entering an endpoint."""
        row_index = len(self.endpoints) + 3
        endpoint_var = StringVar()

        endpoint_label = ttk.Label(self, text="🔗 Endpoint:", font=("Arial", 14))
        endpoint_label.grid(row=row_index, column=0, padx=20, pady=5, sticky="w")

        endpoint_entry = ttk.Entry(self, textvariable=endpoint_var, width=50)
        endpoint_entry.grid(row=row_index, column=1, columnspan=2, padx=20, pady=5, sticky="w")

        self.endpoints.append(endpoint_var)


    def navigate_to_checkout(self):
        """Navigate to the checkout page with selected endpoints and action."""
        endpoints = [endpoint.get().strip() for endpoint in self.endpoints if endpoint.get().strip()]
        action = self.action_var.get()

        if not endpoints:
            self.status_label.config(text="⚠ Please enter at least one endpoint.")
            return

        if not action:
            self.status_label.config(text="⚠ Please select an action.")
            return

        self.parent.checkout_for_endpoint_modifier_with_url.display_changes(endpoints, action)
        self.parent.show_page(self.parent.checkout_for_endpoint_modifier_with_url)

    def go_back_to_home(self):
        """Go back to the file upload page and reset the form."""
        self.parent.file_upload_page.status_label.config(text="")
        self.status_label.config(text="")
        self.parent.show_page(self.parent.file_upload_page)
