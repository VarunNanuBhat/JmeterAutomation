import ttkbootstrap as ttk
from tkinter import StringVar, ttk
from tkinter import messagebox
from jmeter_methods.Jmeter_Automation_Methods import JMXModifier


class HttpHeaderDeletePage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=20)
        self.parent = parent

        # Title for the page
        title_label = ttk.Label(self, text="Delete HTTP Header Key-Value Pair", font=("Arial", 22, "bold"))
        title_label.grid(row=0, column=0, pady=20, columnspan=2)

        # Label and Entry for Header Name
        header_name_label = ttk.Label(self, text="Enter Header Name to Delete:", font=("Arial", 14))
        header_name_label.grid(row=1, column=0, padx=20, pady=10, sticky="w")

        self.header_name_var = StringVar()
        header_name_entry = ttk.Entry(self, textvariable=self.header_name_var, width=50)
        header_name_entry.grid(row=1, column=1, padx=20, pady=10)

        # Buttons
        delete_button = ttk.Button(self, text="Preview Deletions", bootstyle="info", command=self.navigate_to_checkout)
        delete_button.grid(row=2, column=0, columnspan=2, pady=20)

        # Status Label
        self.status_label = ttk.Label(self, text="", font=("Arial", 14), anchor="center")
        self.status_label.grid(row=3, column=0, columnspan=2, pady=10)

    def navigate_to_checkout(self):
        header_name = self.header_name_var.get().strip()
        if not header_name:
            self.status_label.config(text="Please enter a header name.", bootstyle="danger")
            return

        # Pass the header name to the checkout page
        self.parent.checkout_for_http_header_delete.display_deletions([header_name])
        self.parent.show_page(self.parent.checkout_for_http_header_delete)