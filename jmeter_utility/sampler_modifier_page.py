# sampler_modifier_page.py
import ttkbootstrap as ttk
from tkinter import StringVar, ttk, messagebox
from jmeter_methods.Jmeter_Automation_Methods import JMXModifier

class SamplerModifierPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=20)
        self.parent = parent
        self.text_var = StringVar()
        self.action_var = StringVar(value="")  # No default selection

        # Title
        title_label = ttk.Label(self, text="Sampler Modifier", font=("Arial", 22, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=20)

        # Text Input
        text_label = ttk.Label(self, text="Enter Sampler Name:", font=("Arial", 14))
        text_label.grid(row=1, column=0, padx=20, pady=10, sticky="w")

        text_entry = ttk.Entry(self, textvariable=self.text_var, width=50)
        text_entry.grid(row=1, column=1, padx=20, pady=10)

        # Radio Buttons for Action Selection
        action_label = ttk.Label(self, text="Select Action:", font=("Arial", 14))
        action_label.grid(row=2, column=0, padx=20, pady=10, sticky="w")

        ttk.Radiobutton(self, text="Enable", variable=self.action_var, value="enable").grid(row=3, column=1, pady=5, sticky="w")
        ttk.Radiobutton(self, text="Disable", variable=self.action_var, value="disable").grid(row=4, column=1, pady=5, sticky="w")
        ttk.Radiobutton(self, text="Delete", variable=self.action_var, value="delete").grid(row=5, column=1, pady=5, sticky="w")

        # Apply Button
        apply_button = ttk.Button(self, text="Apply Action", bootstyle="primary", command=self.apply_action)
        apply_button.grid(row=6, column=0, columnspan=2, pady=20)

        # Status Label
        self.status_label = ttk.Label(self, text="", font=("Arial", 14), anchor="center")
        self.status_label.grid(row=7, column=0, columnspan=2, pady=10)

    def apply_action(self):
        text = self.text_var.get().strip()
        action = self.action_var.get()

        if not text:
            self.status_label.config(text="Please enter text to match sampler name", bootstyle="danger")
            return

        if not action:
            self.status_label.config(text="Please select an action.", bootstyle="danger")
            return

        if not self.parent.file_upload_page.uploaded_file_paths:
            self.status_label.config(text="No files uploaded!", bootstyle="danger")
            return

        try:
            error_message = None
            for file_path in self.parent.file_upload_page.uploaded_file_paths:
                modifier = JMXModifier(file_path)
                if action == "enable":
                    success = modifier.enable_samplers_by_name(text)
                elif action == "disable":
                    success = modifier.disable_samplers_by_name(text)
                elif action == "delete":
                    success = modifier.delete_samplers_by_name(text)
                else:
                    self.status_label.config(text="Invalid action selected.", bootstyle="danger")
                    return

                if not success:
                    error_message = f"No matching samplers found in file: {file_path}"
                    break

                # Save changes
                output_path = file_path.replace(".jmx", "_modified.jmx")
                modifier.save_changes(output_path)

            if error_message:
                self.status_label.config(text=error_message, bootstyle="danger")
            else:
                self.status_label.config(text=f"Samplers {action}d successfully!", bootstyle="success")
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}", bootstyle="danger")
