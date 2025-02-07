import ttkbootstrap as ttk
from tkinter import StringVar

class SelectFunctionality(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=40)
        self.parent = parent
        self.dropdown_var = StringVar(value="Select an Option")

        # Configure Full-Page Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Title Label
        title_label = ttk.Label(self, text="Select Functionality", font=("Arial", 24, "bold"))
        title_label.grid(row=0, column=0, pady=30, sticky="n")

        # Styled Dropdown Menu
        style = ttk.Style()
        style.configure("Custom.TCombobox", font=("Arial", 14), padding=10)

        dropdown_menu = ttk.Combobox(
            self, textvariable=self.dropdown_var, style="Custom.TCombobox",
            values=[
                "Modify HTTP Header Manager Values",
                "Delete HTTP Header Values",
                "Enable/Disable/Delete endpoints ending with specific texts",
                "Enable/Disable/Delete endpoints ending with specific domains",
                "Replace domain names",
                "Replace contents in URL/Params & body",
                "Enable/Disable/Delete endpoints based on Sampler Names"
            ],
            state="readonly", width=70
        )
        dropdown_menu.grid(row=1, column=0, padx=40, pady=40, sticky="ew")

        # Apply Button (Resized & Styled)
        action_button = ttk.Button(
            self, text="Apply",
            bootstyle="success outline",
            command=self.handle_option_selection
        )
        action_button.grid(row=2, column=0, pady=40, ipadx=20, ipady=12, sticky="ew")

    def handle_option_selection(self):
        selected_option = self.dropdown_var.get()
        if selected_option == "Modify HTTP Header Manager Values":
            self.parent.show_page(self.parent.http_header_modify_page)
        elif selected_option == "Delete HTTP Header Values":
            self.parent.show_page(self.parent.http_header_delete_page)
        elif selected_option == "Enable/Disable/Delete endpoints ending with specific texts":
            self.parent.show_page(self.parent.endpoint_modifier_with_url)
        elif selected_option == "Enable/Disable/Delete endpoints ending with specific domains":
            self.parent.show_page(self.parent.endpoint_modifier_with_domain)
        elif selected_option == "Replace domain names":
            self.parent.show_page(self.parent.replace_domain_name_page)
        elif selected_option == "Replace contents in URL/Params & body":
            self.parent.show_page(self.parent.replace_contents_page)
        elif selected_option == "Enable/Disable/Delete endpoints based on Sampler Names":
            self.parent.show_page(self.parent.sampler_modifier_page)
