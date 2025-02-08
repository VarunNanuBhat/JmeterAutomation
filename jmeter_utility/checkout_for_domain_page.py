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

        # Back and Confirm Buttons
        back_button = ttk.Button(self, text="🔙 Back", bootstyle="secondary", command=self.go_back_to_endpoint_modifier_with_domain)
        back_button.pack(side="left", padx=20, pady=10)

        confirm_button = ttk.Button(self, text="✔ Confirm Changes", bootstyle="success", command=self.confirm_changes)
        confirm_button.pack(side="right", padx=20, pady=10)

        # 🔥 Status Label (To show success/error messages)
        self.status_label = ttk.Label(self, text="", font=("Arial", 12, "bold"), bootstyle="info")
        self.status_label.pack(pady=10)

    def display_changes(self, domains, action):
        """Display the changes queued for confirmation."""
        self.domains_to_modify = domains
        self.action = action

        # Clear the preview frame
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
        try:
            uploaded_files = self.parent.file_upload_page.uploaded_file_paths
            if not uploaded_files:
                self.parent.file_upload_page.status_label.config(text="No files uploaded!", bootstyle="danger")
                return

            if not self.domains_to_modify:
                self.parent.file_upload_page.status_label.config(text="No domains selected for modification!", bootstyle="danger")
                return

            for file_path in uploaded_files:
                modifier = JMXModifier(file_path)
                for domain in self.domains_to_modify:
                    modifier.update_domain_endpoints(domain, self.action)

                # Save changes
                output_path = file_path.replace(".jmx", "_modified.jmx")
                modifier.save_changes(output_path)

            self.parent.file_upload_page.status_label.config(text="Changes applied successfully!", bootstyle="success")
            self.parent.show_page(self.parent.file_upload_page)

        except Exception as e:
            self.parent.file_upload_page.status_label.config(text=f"Error: {str(e)}", bootstyle="danger")
