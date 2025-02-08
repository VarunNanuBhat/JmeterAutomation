import ttkbootstrap as ttk
from tkinter import BOTH
from jmeter_methods.Jmeter_Automation_Methods import JMXModifier

class CheckoutForSamplerPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=20)
        self.parent = parent
        self.samplers_to_modify = []
        self.action = ""

        # 🏷️ Title Label
        title_label = ttk.Label(self, text="Checkout - Sampler Modifier", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)

        # 📄 Frame for previewing changes
        self.preview_frame = ttk.Frame(self)
        self.preview_frame.pack(fill=BOTH, expand=True, pady=20)

        # 🛠 Button Frame (Align buttons)
        button_frame = ttk.Frame(self)
        button_frame.pack(fill="x", pady=10)

        # 🔙 Back Button
        back_button = ttk.Button(button_frame, text="🔙 Back", bootstyle="secondary",
                                 command=self.go_back_to_sampler_modifier_page)
        back_button.pack(side="left", padx=20, pady=10)

        # ✅ Confirm Button
        confirm_button = ttk.Button(button_frame, text="✔ Confirm Changes", bootstyle="success",
                                    command=self.confirm_changes)
        confirm_button.pack(side="right", padx=20, pady=10)

        # 🔥 Status Label (Below Buttons)
        self.status_label = ttk.Label(self, text="", font=("Arial", 12, "bold"), bootstyle="info")
        self.status_label.pack(pady=10)

    def display_changes(self, samplers, action):
        """Display the selected samplers and action in a structured way."""
        self.samplers_to_modify = samplers
        self.action = action

        # Clear existing content in the preview frame
        for widget in self.preview_frame.winfo_children():
            widget.destroy()

        # 🎯 Header row
        ttk.Label(self.preview_frame, text=f"Action: {action.capitalize()}", font=("Arial", 14, "bold")).pack(anchor="w", padx=20, pady=10)

        # 🔄 List samplers
        if not samplers:
            ttk.Label(self.preview_frame, text="⚠ No samplers selected!", font=("Arial", 12), bootstyle="warning").pack(anchor="w", padx=20, pady=5)
        else:
            for idx, sampler in enumerate(samplers, start=1):
                ttk.Label(self.preview_frame, text=f"{idx}. {sampler}", font=("Arial", 12)).pack(anchor="w", padx=20, pady=5)

        self.status_label.config(text="")  # Reset status message

    def confirm_changes(self):
        """Apply the changes to uploaded JMX files and handle success/failure messages."""
        uploaded_files = self.parent.file_upload_page.uploaded_file_paths
        samplers = self.samplers_to_modify
        action = self.action

        if not uploaded_files:
            self.status_label.config(text="❌ No files uploaded!", bootstyle="danger")
            return

        if not samplers:
            self.status_label.config(text="❌ No samplers selected for modification!", bootstyle="danger")
            return

        if not action:
            self.status_label.config(text="❌ No action selected!", bootstyle="danger")
            return

        error_messages = []  # Collect errors per file
        success = False  # Track if at least one modification was successful

        for file_path in uploaded_files:
            try:
                modifier = JMXModifier(file_path)

                for sampler in samplers:
                    if action == "enable":
                        modified = modifier.enable_samplers_by_name(sampler)
                    elif action == "disable":
                        modified = modifier.disable_samplers_by_name(sampler)
                    elif action == "delete":
                        modified = modifier.delete_samplers_by_name(sampler)
                    else:
                        self.status_label.config(text="❌ Invalid action selected!", bootstyle="danger")
                        return

                    if not modified:
                        error_messages.append(f"⚠ No matching sampler '{sampler}' found in {file_path}.")
                    else:
                        success = True  # At least one modification was successful

                # Save changes only if any sampler was modified
                if success:
                    output_path = file_path.replace(".jmx", "_modified.jmx")
                    modifier.save_changes(output_path)

            except Exception as e:
                error_messages.append(f"❌ Error in {file_path}: {str(e)}")

        # ✅ Display success or errors
        if success:
            self.status_label.config(text="✅ Sampler modifications applied successfully!", bootstyle="success")
            self.after(2000, self.go_back_to_file_upload)
        else:
            self.status_label.config(text="\n".join(error_messages), bootstyle="danger")

    def go_back_to_file_upload(self):
        """Reset status and navigate back to file upload page."""
        self.status_label.config(text="")
        self.parent.file_upload_page.status_label.config(text="")
        self.parent.show_page(self.parent.file_upload_page)

    def go_back_to_sampler_modifier_page(self):
        """Go back to the Sampler Modifier Page."""
        self.status_label.config(text="")
        self.parent.show_page(self.parent.sampler_modifier_page)
