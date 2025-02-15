import ttkbootstrap as ttk
from jmeter_methods.Jmeter_Automation_Methods import JMXModifier

class CheckoutPageForDomain(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=20)
        self.parent = parent
        self.domains_to_modify = []
        self.action = ""

        # Title Label
        title_label = ttk.Label(self, text="Checkout Page", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)

        # Frame for previewing changes
        self.preview_frame = ttk.Frame(self)
        self.preview_frame.pack(fill="both", expand=True, pady=20)

        # Button Frame (Keeps buttons aligned)
        button_frame = ttk.Frame(self)
        button_frame.pack(fill="x", pady=10)

        # Back Button
        back_button = ttk.Button(button_frame, text="🔙 Back", bootstyle="secondary",
                                 command=self.go_back_to_endpoint_modifier_with_domain)
        back_button.pack(side="left", padx=20, pady=10)

        # Confirm Button
        confirm_button = ttk.Button(button_frame, text="✔ Confirm Changes", bootstyle="success",
                                    command=self.confirm_changes)
        confirm_button.pack(side="right", padx=20, pady=10)

        # 🔥 Status Label (Below Buttons)
        self.status_label = ttk.Label(self, text="", font=("Arial", 12, "bold"), bootstyle="info")
        self.status_label.pack(pady=10)

    def display_changes(self, domains, action):
        """Display the changes queued for confirmation."""
        self.domains_to_modify = domains
        self.action = action

        # Clear previous preview
        for widget in self.preview_frame.winfo_children():
            widget.destroy()

        # Display action and domains
        ttk.Label(self.preview_frame, text=f"Action: {action.capitalize()}", font=("Arial", 14, "bold")).pack(anchor="w", padx=20, pady=10)
        for idx, domain in enumerate(domains, start=1):
            ttk.Label(self.preview_frame, text=f"{idx}. {domain}", font=("Arial", 12)).pack(anchor="w", padx=20, pady=5)

    def go_back_to_endpoint_modifier_with_domain(self):
        self.parent.show_page(self.parent.endpoint_modifier_with_domain)

    def confirm_changes(self):
        """Apply the changes and provide feedback."""
        uploaded_files = self.parent.file_upload_page.uploaded_file_paths
        if not uploaded_files:
            self.status_label.config(text="❌ No files uploaded!", bootstyle="danger")
            return

        if not self.domains_to_modify:
            self.status_label.config(text="❌ No domains selected for modification!", bootstyle="danger")
            return

        error_messages = []  # Collect errors per file
        success = False  # Track if any domain was modified successfully

        for file_path in uploaded_files:
            try:
                modifier = JMXModifier(file_path)
                for domain in self.domains_to_modify:
                    result = modifier.update_domain_endpoints(domain, self.action)

                    if not result:  # If no endpoints were modified, return a warning
                        error_messages.append(f"⚠ No endpoints with '{domain}' found.")
                    else:
                        success = True  # At least one modification succeeded

                # Save changes if any modification was successful
                if success:
                    #output_path = file_path.replace(".jmx", "_modified.jmx")
                    modifier.save_changes(file_path)

            except Exception as e:
                error_messages.append(f"❌ Error in {file_path}: {str(e)}")

        # ✅ Display success or errors
        if success:
            self.status_label.config(text="✅ Changes applied successfully!", bootstyle="success")
            self.after(2000, self.go_back_to_file_upload)
        else:
            self.status_label.config(text="\n".join(error_messages), bootstyle="danger")

    def go_back_to_file_upload(self):
        # Reset status label
        self.status_label.config(text="")
        self.parent.file_upload_page.status_label.config(text="")

        # Show the file upload page
        self.parent.show_page(self.parent.file_upload_page)
