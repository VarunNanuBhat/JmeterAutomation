import ttkbootstrap as ttk
from tkinter import StringVar
from jmeter_methods.Jmeter_Automation_Methods import JMXModifier


class ReplaceSelectedDomainsPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=20)
        self.parent = parent
        self.selected_domains = []
        self.domain_entries = []

        # 🌟 **Title Label with Icon**
        title_label = ttk.Label(self, text="🔄 Replace Selected Domains", font=("Arial", 18, "bold"))
        title_label.grid(row=0, column=0, columnspan=4, pady=(10, 20), sticky="n")

        # 📜 **Scrollable Frame for Domains**
        self.scrollable_frame = ttk.Frame(self, bootstyle="light")
        self.scrollable_frame.grid(row=1, column=0, columnspan=4, pady=10, sticky="nsew")

        self.canvas = ttk.Canvas(self.scrollable_frame, height=250)
        self.canvas.pack(side="left", fill="both", expand=True)

        self.scrollbar = ttk.Scrollbar(self.scrollable_frame, orient="vertical", command=self.canvas.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.inner_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")

        # 🔘 **Buttons Section**
        button_frame = ttk.Frame(self)
        button_frame.grid(row=2, column=0, columnspan=4, pady=(20, 10), sticky="ew")

        apply_button = ttk.Button(button_frame, text="✅ Apply Changes", bootstyle="primary", command=self.apply_changes)
        apply_button.pack(side="left", padx=10)

        back_button = ttk.Button(button_frame, text="🔙 Back", bootstyle="secondary", command=self.go_back_to_list_domains)
        back_button.pack(side="right", padx=10)

        # 📝 **Status Label**
        self.status_label = ttk.Label(self, text="", font=("Arial", 12, "bold"), bootstyle="info", width=60, anchor="center")
        self.status_label.grid(row=3, column=0, columnspan=4, pady=10, sticky="n")

        # 🎯 Make Grid Responsive
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        self.columnconfigure(3, weight=1)

    def populate_domain_names(self, selected_domains):
        """Dynamically populate the page with selected domains and input fields."""
        for widget in self.inner_frame.winfo_children():
            widget.destroy()

        self.selected_domains = selected_domains
        self.domain_entries = []

        for i, domain in enumerate(selected_domains):
            # 🌐 Domain Label
            ttk.Label(self.inner_frame, text=f"🌐 {domain}", font=("Arial", 12)).grid(row=i, column=0, padx=10, pady=5, sticky="w")

            # ✏️ Input Field for New Domain
            new_domain_entry = ttk.Entry(self.inner_frame, width=40)
            new_domain_entry.grid(row=i, column=1, padx=10, pady=5)
            self.domain_entries.append(new_domain_entry)

        self.inner_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def apply_changes(self):
        """Apply the domain modifications."""
        uploaded_file_paths = self.parent.file_upload_page.get_uploaded_files()

        if not uploaded_file_paths:
            self.status_label.config(text="⚠ No files uploaded!", bootstyle="danger")
            return

        domains_to_replace = {}
        for i, entry in enumerate(self.domain_entries):
            new_value = entry.get().strip()
            if new_value:
                domains_to_replace[self.selected_domains[i]] = new_value

        if not domains_to_replace:
            self.status_label.config(text="⚠ Please enter at least one new domain value.", bootstyle="warning")
            return

        error_message = None
        for file_path in uploaded_file_paths:
            try:
                self.replace_domains_backend(file_path, domains_to_replace)
            except ValueError as e:
                error_message = str(e)
                break

        if error_message:
            self.status_label.config(text=f"❌ Error: {error_message}", bootstyle="danger")
        else:
            self.status_label.config(text="✅ Domains Replaced Successfully!", bootstyle="success")
            self.after(2000, self.go_back_to_home)

    @staticmethod
    def replace_domains_backend(file_path, domains):
        """Call JMXModifier to replace domains."""
        try:
            modifier = JMXModifier(file_path)

            for old_domain, new_domain in domains.items():
                modifier.replace_domain_name(old_domain, new_domain)

            output_path = file_path.replace(".jmx", "_modified.jmx")
            modifier.save_changes(output_path)

        except Exception as e:
            raise ValueError(f"Error modifying file {file_path}: {str(e)}")

    def go_back_to_list_domains(self):
        """Navigate back to the domain selection page."""
        self.status_label.config(text="")
        self.parent.show_page(self.parent.domain_list_page)

    def go_back_to_home(self):
        """Go back to the file upload page and reset the file list."""
        self.parent.file_upload_page.status_label.config(text="")
        self.status_label.config(text="")
        self.parent.show_page(self.parent.file_upload_page)
