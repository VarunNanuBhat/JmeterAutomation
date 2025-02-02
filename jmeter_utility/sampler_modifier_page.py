import ttkbootstrap as ttk
from tkinter import StringVar, ttk, messagebox
from jmeter_methods.Jmeter_Automation_Methods import JMXModifier

class SamplerModifierPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=20)
        self.parent = parent
        self.sampler_entries = []  # Stores sampler name entries
        self.action_var = StringVar(value="")  # No default selection

        # Title
        title_label = ttk.Label(self, text="Sampler Modifier", font=("Arial", 22, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=20)

        # Add Sampler button
        add_button = ttk.Button(self, text="+ Add Sampler", bootstyle="success", command=self.add_sampler_row)
        add_button.grid(row=1, column=0, pady=10, padx=20, sticky="w")

        # List Domains button
        list_button = ttk.Button(self, text="List Samplers", bootstyle="info",
                                 command=self.navigate_to_list_sampler_names)
        list_button.grid(row=1, column=1, pady=20, padx=20, sticky="e")

        # Preview Changes button
        preview_button = ttk.Button(self, text="Preview Changes", bootstyle="primary",command=self.navigate_to_checkout)
        preview_button.grid(row=1, column=3, pady=20, padx=20, sticky="e")

        # Action Selection
        action_label = ttk.Label(self, text="Select Action:", font=("Arial", 14))
        action_label.grid(row=2, column=0, padx=20, pady=10, sticky="w")

        ttk.Radiobutton(self, text="Enable", variable=self.action_var, value="enable").grid(row=2, column=1, pady=5, sticky="w")
        ttk.Radiobutton(self, text="Disable", variable=self.action_var, value="disable").grid(row=3, column=1, pady=5, sticky="w")
        ttk.Radiobutton(self, text="Delete", variable=self.action_var, value="delete").grid(row=4, column=1, pady=5, sticky="w")

        # Status Label
        self.status_label = ttk.Label(self, text="", font=("Arial", 14), anchor="center")
        self.status_label.grid(row=999, column=0, columnspan=3, pady=10, padx=20, sticky="s")

        # Configure grid row weight
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(999, weight=1)

        # Add the first sampler input row by default
        self.add_sampler_row()

    def add_sampler_row(self):
        """Dynamically add a row for entering a sampler name to modify."""
        row_index = len(self.sampler_entries) + 5
        sampler_var = StringVar()

        sampler_label = ttk.Label(self, text=f"Sampler {len(self.sampler_entries) + 1}:", font=("Arial", 14))
        sampler_label.grid(row=row_index, column=0, padx=20, pady=5, sticky="w")

        sampler_entry = ttk.Entry(self, textvariable=sampler_var, width=50)
        sampler_entry.grid(row=row_index, column=1, columnspan=2, padx=20, pady=5, sticky="w")

        self.sampler_entries.append(sampler_var)

    def navigate_to_checkout(self):
        """Navigate to the checkout page with selected samplers and action."""
        samplers = [sampler.get().strip() for sampler in self.sampler_entries if sampler.get().strip()]
        action = self.action_var.get()

        if not samplers:
            self.status_label.config(text="Please enter at least one sampler.", bootstyle="danger")
            return

        if not action:
            self.status_label.config(text="Please select an action.", bootstyle="danger")
            return

        # Pass the samplers and action to the checkout page
        self.parent.checkout_for_sampler_page.display_changes(samplers, action)
        self.parent.show_page(self.parent.checkout_for_sampler_page)


    def navigate_to_list_sampler_names(self):
        """Navigate to the List Domain Names page."""
        try:
            uploaded_file_paths = self.parent.file_upload_page.get_uploaded_files()
            if not uploaded_file_paths:
                self.status_label.config(text="No files uploaded!", bootstyle="danger")
                return

            unique_sampler_names = set()
            for file_path in uploaded_file_paths:
                modifier = JMXModifier(file_path)
                unique_sampler_names.update(modifier.list_unique_sampler_names())

            self.parent.sampler_list_page.populate_sampler_names(list(unique_sampler_names))
            self.parent.show_page(self.parent.sampler_list_page)

        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}", bootstyle="danger")


