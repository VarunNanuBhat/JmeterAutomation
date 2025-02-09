import ttkbootstrap as ttk
from tkinter import StringVar, BooleanVar, ttk
from jmeter_methods.Jmeter_Automation_Methods import JMXModifier

class ReplaceContentPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=20)
        self.parent = parent

        # Store multiple text replacement pairs
        self.texts_to_replace = []

        # Title for the page
        title_label = ttk.Label(self, text="Replace Content in Requests", font=("Arial", 22, "bold"))
        title_label.grid(row=0, column=0, columnspan=4, pady=20)

        # Add Text button
        add_button = ttk.Button(self, text="+ Add Text", bootstyle="success", command=self.add_text_row)
        add_button.grid(row=1, column=0, pady=20, padx=20, sticky="ew")

        # Preview Changes button
        preview_button = ttk.Button(self, text="👁 Preview Changes", bootstyle="primary",
                                    command=self.navigate_to_checkout)
        preview_button.grid(row=1, column=2, pady=20, padx=20, sticky="ew")

        # Home page button
        home_button = ttk.Button(self, text="🏠 Home", bootstyle="secondary", command=self.go_back_to_home)
        home_button.grid(row=1, column=1, pady=20, padx=20, sticky="ew")

        # Checkboxes for Replacement Scope
        self.replace_in_url_var = BooleanVar(value=False)
        replace_in_url_checkbox = ttk.Checkbutton(self, text="Replace in URL Path", variable=self.replace_in_url_var)
        replace_in_url_checkbox.grid(row=2, column=0, padx=20, pady=10, sticky="w")

        self.replace_in_body_params_var = BooleanVar(value=False)
        replace_in_body_params_checkbox = ttk.Checkbutton(
            self, text="Replace in Params and Body", variable=self.replace_in_body_params_var
        )
        replace_in_body_params_checkbox.grid(row=2, column=1, padx=20, pady=10, sticky="w")

        # Add the first input row by default
        self.add_text_row()

        # Status Label
        self.status_label = ttk.Label(self, text="", font=("Arial", 14), anchor="center")
        self.status_label.grid(row=999, column=0, columnspan=4, pady=10)

    def add_text_row(self):
        """Dynamically add a new row for entering a text replacement pair."""
        row_index = len(self.texts_to_replace) + 3  # Adjusted to accommodate checkboxes

        old_text_var = StringVar()
        new_text_var = StringVar()

        # Old Text Entry
        old_text_label = ttk.Label(self, text=f"Text to Replace {row_index - 2}:", font=("Arial", 12))
        old_text_label.grid(row=row_index, column=0, padx=10, pady=5, sticky="w")

        old_text_entry = ttk.Entry(self, textvariable=old_text_var, width=30)
        old_text_entry.grid(row=row_index, column=1, padx=10, pady=5)

        # New Text Entry
        new_text_label = ttk.Label(self, text="Replacement Text:", font=("Arial", 12))
        new_text_label.grid(row=row_index, column=2, padx=10, pady=5, sticky="w")

        new_text_entry = ttk.Entry(self, textvariable=new_text_var, width=30)
        new_text_entry.grid(row=row_index, column=3, padx=10, pady=5)

        # Store the entry variables
        self.texts_to_replace.append((old_text_var, new_text_var))

    def navigate_to_checkout(self):
        """Navigate to the checkout page to preview text replacements."""
        text_pairs = [(old_var.get().strip(), new_var.get().strip()) for old_var, new_var in self.texts_to_replace]
        text_pairs = [(old, new) for old, new in text_pairs if old and new]  # Remove empty fields

        if not text_pairs:
            self.status_label.config(text="Please enter at least one text pair.", bootstyle="danger")
            return

        replace_in_url = self.replace_in_url_var.get()
        replace_in_body_params = self.replace_in_body_params_var.get()

        if not (replace_in_url or replace_in_body_params):
            self.status_label.config(text="Please select at least one replacement scope.", bootstyle="danger")
            return

        self.parent.checkout_for_replace_contents_page.display_changes(text_pairs, replace_in_url, replace_in_body_params)
        self.parent.show_page(self.parent.checkout_for_replace_contents_page)

    def go_back_to_home(self):
        """Go back to the file upload page and reset the file list."""
        self.parent.file_upload_page.status_label.config(text="")
        self.status_label.config(text="")
        self.parent.show_page(self.parent.file_upload_page)

    def reset_text_entries(self):
        """Reset the text entry fields to their initial state."""
        for widget in self.grid_slaves():
            if isinstance(widget, ttk.Entry) or isinstance(widget, ttk.Label):
                widget.grid_forget()

        self.texts_to_replace = []
        self.add_text_row()
