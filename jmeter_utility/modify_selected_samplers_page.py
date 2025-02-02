import ttkbootstrap as ttk
from tkinter import StringVar
from jmeter_methods.Jmeter_Automation_Methods import JMXModifier  # Import your JMXModifier module


class ModifySelectedSamplersPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=20)
        self.parent = parent
        self.selected_samplers = []  # Store selected sampler names
        self.action_var = StringVar(value="enable")  # Store common action

        # Title Label
        title_label = ttk.Label(self, text="Modify Selected Samplers", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=10)

        # **Common Action Selection**
        action_label = ttk.Label(self, text="Select Action for All Samplers:", font=("Arial", 14))
        action_label.grid(row=1, column=0, padx=20, pady=10, sticky="w")

        ttk.Radiobutton(self, text="Enable", variable=self.action_var, value="enable").grid(row=1, column=1, padx=5, sticky="w")
        ttk.Radiobutton(self, text="Disable", variable=self.action_var, value="disable").grid(row=1, column=2, padx=5, sticky="w")
        ttk.Radiobutton(self, text="Delete", variable=self.action_var, value="delete").grid(row=1, column=3, padx=5, sticky="w")

        # Scrollable Frame for sampler list
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
        apply_changes = ttk.Button(self, text="Apply Changes", bootstyle="primary", command=self.apply_changes)
        apply_changes.grid(row=3, column=0, pady=20, padx=10, sticky="w")

        back_button = ttk.Button(self, text="Go Back", bootstyle="danger", command=self.go_back_to_list_samplers)
        back_button.grid(row=3, column=3, pady=20, padx=10, sticky="e")

    def populate_sampler_names(self, selected_samplers):
        """Populate the page with selected samplers."""
        # Clear previous entries
        for widget in self.inner_frame.winfo_children():
            widget.destroy()

        self.selected_samplers = selected_samplers  # Store original sampler names

        # Create a label for each sampler
        for i, sampler in enumerate(selected_samplers):
            sampler_label = ttk.Label(self.inner_frame, text=sampler, font=("Arial", 12))
            sampler_label.grid(row=i, column=0, padx=10, pady=5, sticky="w")

        # Update canvas scroll area
        self.inner_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def apply_changes(self):
        """Apply the selected action (Enable, Disable, Delete) to selected samplers."""
        try:
            uploaded_files = self.parent.file_upload_page.get_uploaded_files()
            if not uploaded_files:
                self.parent.file_upload_page.status_label.config(text="No files uploaded!", bootstyle="danger")
                return

            selected_action = self.action_var.get()

            if not self.selected_samplers:
                self.parent.file_upload_page.status_label.config(text="No samplers selected for modification!", bootstyle="danger")
                return

            for file_path in uploaded_files:
                modifier = JMXModifier(file_path)

                for sampler in self.selected_samplers:
                    if selected_action == "enable":
                        modifier.enable_samplers_by_name(sampler)
                    elif selected_action == "disable":
                        modifier.disable_samplers_by_name(sampler)
                    elif selected_action == "delete":
                        modifier.delete_samplers_by_name(sampler)

                # Save the modified JMX file
                output_path = file_path.replace(".jmx", "_modified.jmx")
                modifier.save_changes(output_path)

            self.parent.file_upload_page.status_label.config(text="Changes applied successfully!", bootstyle="success")
            self.parent.show_page(self.parent.file_upload_page)

        except Exception as e:
            self.parent.file_upload_page.status_label.config(text=f"Error: {str(e)}", bootstyle="danger")

    def go_back_to_list_samplers(self):
        """Go back to the List Samplers page."""
        self.parent.show_page(self.parent.sampler_list_page)
