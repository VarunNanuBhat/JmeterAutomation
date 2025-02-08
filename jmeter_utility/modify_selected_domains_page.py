import ttkbootstrap as ttk
from tkinter import StringVar
from jmeter_methods.Jmeter_Automation_Methods import JMXModifier


class ModifySelectedDomainsPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=20)
        self.parent = parent
        self.selected_domains = []  # Store selected domains
        self.action_var = StringVar()  # Store selected action (Enable/Disable/Delete)

        # 🌟 Title Label with Icon
        title_label = ttk.Label(self, text="🌍 Modify Selected Domains", font=("Arial", 18, "bold"))
        title_label.grid(row=0, column=0, columnspan=4, pady=(10, 20), sticky="n")

        # 🎯 **Common Action Selection**
        action_frame = ttk.Frame(self)
        action_frame.grid(row=1, column=0, columnspan=4, pady=10)

        action_label = ttk.Label(action_frame, text="🛠 Select Action:", font=("Arial", 14, "bold"))
        action_label.pack(side="left", padx=(10, 10))

        ttk.Radiobutton(action_frame, text="✅ Enable", variable=self.action_var, value="enable").pack(side="left", padx=5)
        ttk.Radiobutton(action_frame, text="🚫 Disable", variable=self.action_var, value="disable").pack(side="left", padx=5)
        ttk.Radiobutton(action_frame, text="🗑 Delete", variable=self.action_var, value="delete").pack(side="left", padx=5)

        # 📜 **Scrollable Frame for Domains**
        self.scrollable_frame = ttk.Frame(self, bootstyle="light")
        self.scrollable_frame.grid(row=2, column=0, columnspan=4, pady=10, sticky="nsew")

        self.canvas = ttk.Canvas(self.scrollable_frame, height=200)
        self.canvas.pack(side="left", fill="both", expand=True)

        self.scrollbar = ttk.Scrollbar(self.scrollable_frame, orient="vertical", command=self.canvas.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.inner_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")

        # 🔘 **Buttons Section**
        button_frame = ttk.Frame(self)
        button_frame.grid(row=3, column=0, columnspan=4, pady=(20, 10), sticky="ew")

        apply_button = ttk.Button(button_frame, text="🔄 Apply Changes", bootstyle="primary", command=self.apply_changes)
        apply_button.pack(side="left", padx=10)

        back_button = ttk.Button(button_frame, text="🔙 Back", bootstyle="secondary", command=self.go_back_to_list_domains)
        back_button.pack(side="right", padx=10)

        # 📝 **Status Label**
        self.status_label = ttk.Label(self, text="", font=("Arial", 12, "bold"), bootstyle="info", width=60, anchor="center")
        self.status_label.grid(row=4, column=0, columnspan=4, pady=10, sticky="n")

        # 🎯 Make Grid Responsive
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        self.columnconfigure(3, weight=1)

    def populate_domain_names(self, selected_domains):
        """Dynamically populate the page with selected domains."""
        for widget in self.inner_frame.winfo_children():
            widget.destroy()

        self.selected_domains = selected_domains

        for i, domain in enumerate(selected_domains):
            ttk.Label(self.inner_frame, text=f"🌐 {domain}", font=("Arial", 12)).grid(row=i, column=0, padx=20, pady=5, sticky="w")

        self.inner_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def apply_changes(self):
        """Apply the selected action to domains."""
        try:
            uploaded_files = self.parent.file_upload_page.get_uploaded_files()
            if not uploaded_files:
                self.status_label.config(text="⚠ No files uploaded!", bootstyle="danger")
                return

            selected_action = self.action_var.get()
            if not selected_action:
                self.status_label.config(text="⚠ Please select an action!", bootstyle="warning")
                return

            if not self.selected_domains:
                self.status_label.config(text="⚠ No domains selected for modification!", bootstyle="warning")
                return

            error_message = None
            for file_path in uploaded_files:
                try:
                    modifier = JMXModifier(file_path)
                    for domain in self.selected_domains:
                        if selected_action == "enable":
                            modifier.enable_domain_endpoints(domain)
                        elif selected_action == "disable":
                            modifier.disable_domain_endpoints(domain)
                        elif selected_action == "delete":
                            modifier.delete_domain_endpoints(domain)

                    output_path = file_path.replace(".jmx", "_modified.jmx")
                    modifier.save_changes(output_path)

                except Exception as e:
                    error_message = str(e)
                    break

            if error_message:
                self.status_label.config(text=f"❌ Error: {error_message}", bootstyle="danger")
            else:
                self.status_label.config(text="✅ Changes applied successfully!", bootstyle="success")
                self.after(2000, self.go_back_to_home)

        except Exception as e:
            self.status_label.config(text=f"❌ Error: {str(e)}", bootstyle="danger")

    def go_back_to_list_domains(self):
        """Navigate back to the domain selection page."""
        self.status_label.config(text="")
        self.parent.show_page(self.parent.domain_list_page)

    def go_back_to_home(self):
        """Go back to the file upload page and reset the file list."""

        # Reset the status label
        self.parent.file_upload_page.status_label.config(text="")

        # Clear status label in HttpHeaderPage (this clears success/error message)
        self.status_label.config(text="")

        # Show the file upload page
        self.parent.show_page(self.parent.file_upload_page)