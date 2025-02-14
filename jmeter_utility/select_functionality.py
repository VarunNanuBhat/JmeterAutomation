import ttkbootstrap as ttk
from tkinter import StringVar


class SelectFunctionality(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=40)
        self.parent = parent
        self.selected_option = StringVar(value="")  # No pre-selection

        # Configure Full-Page Layout
        self.grid_columnconfigure(0, weight=1)

        # Title Label
        ttk.Label(
            self, text="Select Functionality", font=("Arial", 26, "bold"), bootstyle="primary"
        ).grid(row=0, column=0, pady=(20, 10), sticky="n")

        # Subtitle
        ttk.Label(
            self, text="Choose an action to proceed:", font=("Arial", 14), bootstyle="secondary"
        ).grid(row=1, column=0, pady=(0, 20), sticky="n")

        # Functionality Options
        options = [
            "Modify HTTP Header Manager Values",
            "Delete HTTP Header Values",
            "Enable/Disable/Delete endpoints ending with specific texts",
            "Enable/Disable/Delete endpoints with specific domains",
            "Replace domain names",
            "Replace contents in URL/Params & body",
            "Enable/Disable/Delete endpoints based on Sampler Names",
        ]

        # Radio Button Frame (for clean layout)
        radio_frame = ttk.Frame(self)
        radio_frame.grid(row=2, column=0, padx=40, pady=10, sticky="ew")

        for i, text in enumerate(options):
            ttk.Radiobutton(
                radio_frame, text=text, variable=self.selected_option, value=text,
                bootstyle="info toolbutton"
            ).grid(row=i, column=0, sticky="ew", pady=5, padx=10)

        # Apply Button
        ttk.Button(
            self, text="Apply", bootstyle="success outline",
            command=self.handle_option_selection
        ).grid(row=3, column=0, pady=30, ipadx=30, ipady=12, sticky="ew")

        self.status_label = ttk.Label(self, text="", font=("Arial", 14), bootstyle="danger")
        self.status_label.grid(row=4, column=0, pady=15)

    def handle_option_selection(self):
        selected_option = self.selected_option.get()

        if not selected_option:
            self.status_label.config(text="⚠ Please select an option before proceeding!")
            return

        # Page Redirection Logic
        pages = {
            "Modify HTTP Header Manager Values": self.parent.http_header_modify_page,
            "Delete HTTP Header Values": self.parent.http_header_delete_page,
            "Enable/Disable/Delete endpoints ending with specific texts": self.parent.endpoint_modifier_with_url,
            "Enable/Disable/Delete endpoints with specific domains": self.parent.endpoint_modifier_with_domain,
            "Replace domain names": self.parent.replace_domain_name_page,
            "Replace contents in URL/Params & body": self.parent.replace_contents_page,
            "Enable/Disable/Delete endpoints based on Sampler Names": self.parent.sampler_modifier_page,
        }

        self.parent.show_page(pages[selected_option])
