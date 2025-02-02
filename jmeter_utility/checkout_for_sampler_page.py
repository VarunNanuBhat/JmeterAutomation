import ttkbootstrap as ttk
from tkinter import StringVar, Text
from jmeter_methods.Jmeter_Automation_Methods import JMXModifier

class CheckoutForSamplerPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=20)
        self.parent = parent
        self.samplers = []
        self.action = ""

        # Title Label
        title_label = ttk.Label(self, text="Sampler Modifier - Preview Changes", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=10)

        # Changes Display Textbox
        self.changes_textbox = Text(self, height=10, width=70, wrap="word", state="disabled")
        self.changes_textbox.grid(row=1, column=0, columnspan=3, padx=20, pady=10)

        # Apply Changes Button
        apply_button = ttk.Button(self, text="Apply Changes", bootstyle="success", command=self.apply_changes)
        apply_button.grid(row=2, column=0, pady=20, padx=20, sticky="w")

        # Go Back Button
        back_button = ttk.Button(self, text="Go Back", bootstyle="danger", command=self.go_back)
        back_button.grid(row=2, column=2, pady=20, padx=20, sticky="e")

        # Status Label
        self.status_label = ttk.Label(self, text="", font=("Arial", 14), anchor="center", wraplength=500)
        self.status_label.grid(row=3, column=0, columnspan=3, pady=10, padx=20, sticky="s")

    def display_changes(self, samplers, action):
        """Display the selected samplers and action in the textbox."""
        self.samplers = samplers
        self.action = action

        self.changes_textbox.config(state="normal")
        self.changes_textbox.delete("1.0", "end")  # Clear previous text

        summary_text = f"Action: {action.upper()}\n\nSamplers to modify:\n" + "\n".join(samplers)
        self.changes_textbox.insert("1.0", summary_text)
        self.changes_textbox.config(state="disabled")

        self.status_label.config(text="")

    def apply_changes(self):
        """Trigger the apply_action method from the sampler modifier page."""

        samplers = self.samplers  # Use the samplers set in display_changes()
        action = self.action  # Use the action set in display_changes()

        if not samplers:
            self.status_label.config(text="No samplers selected!", bootstyle="danger")
            return

        if not action:
            self.status_label.config(text="No action selected!", bootstyle="danger")
            return

        if not self.parent.file_upload_page.uploaded_file_paths:
            self.status_label.config(text="No files uploaded!", bootstyle="danger")
            return

        try:
            error_message = None
            for file_path in self.parent.file_upload_page.uploaded_file_paths:
                modifier = JMXModifier(file_path)

                for sampler_name in samplers:
                    if action == "enable":
                        success = modifier.enable_samplers_by_name(sampler_name)
                    elif action == "disable":
                        success = modifier.disable_samplers_by_name(sampler_name)
                    elif action == "delete":
                        success = modifier.delete_samplers_by_name(sampler_name)
                    else:
                        self.status_label.config(text="Invalid action selected.", bootstyle="danger")
                        return

                    if not success:
                        error_message = f"No matching sampler '{sampler_name}' found in file: {file_path}"
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


    def go_back(self):
        """Go back to the Sampler Modifier Page."""
        self.status_label.config(text="")
        self.parent.show_page(self.parent.sampler_modifier_page)
