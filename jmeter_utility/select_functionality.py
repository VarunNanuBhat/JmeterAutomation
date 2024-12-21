import ttkbootstrap as ttk
from tkinter import StringVar

class SelectFunctionality(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=20)
        self.parent = parent
        self.dropdown_var = StringVar(value="Select an Option")

        dropdown_menu = ttk.Combobox(
            self, textvariable=self.dropdown_var,
            values=[
                "Modify HTTP Header Manager Values",
                "Delete HTTP Header Values",
                "Disable endpoints ending with certain texts",
                "Delete endpoints ending with certain texts",
                "Disable sampler"
            ],
            state="readonly", width=50
        )
        dropdown_menu.grid(row=0, column=0, padx=20, pady=30)

        action_button = ttk.Button(self, text="Apply", bootstyle="primary", command=self.handle_option_selection)
        action_button.grid(row=1, column=0, pady=20)

    def handle_option_selection(self):
        selected_option = self.dropdown_var.get()
        if selected_option == "Modify HTTP Header Manager Values":
            self.parent.show_page(self.parent.http_header_modify_page)
        if selected_option == "Delete HTTP Header Values":
            self.parent.show_page(self.parent.http_header_delete_page)