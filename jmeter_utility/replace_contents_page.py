import ttkbootstrap as ttk
from tkinter import StringVar, BooleanVar
from jmeter_methods.Jmeter_Automation_Methods import JMXModifier

class ReplaceContentPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=20)
        self.parent = parent

        # Title for the page
        title_label = ttk.Label(self, text="Replace Content", font=("Arial", 22, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=20)

        # Text to Replace
        text_replace_label = ttk.Label(self, text="Text to Replace:", font=("Arial", 14))
        text_replace_label.grid(row=1, column=0, padx=20, pady=10, sticky="w")

        self.text_to_replace_var = StringVar()
        text_replace_entry = ttk.Entry(self, textvariable=self.text_to_replace_var, width=50)
        text_replace_entry.grid(row=1, column=1, padx=20, pady=10, sticky="w")

        # Replacement Text
        replacement_text_label = ttk.Label(self, text="Replacement Text:", font=("Arial", 14))
        replacement_text_label.grid(row=2, column=0, padx=20, pady=10, sticky="w")

        self.replacement_text_var = StringVar()
        replacement_text_entry = ttk.Entry(self, textvariable=self.replacement_text_var, width=50)
        replacement_text_entry.grid(row=2, column=1, padx=20, pady=10, sticky="w")

        # Checkboxes for Replacement Scope
        self.replace_in_url_var = BooleanVar(value=False)
        replace_in_url_checkbox = ttk.Checkbutton(self, text="Replace in URL Path", variable=self.replace_in_url_var)
        replace_in_url_checkbox.grid(row=3, column=0, padx=20, pady=10, sticky="w")

        self.replace_in_body_params_var = BooleanVar(value=False)
        replace_in_body_params_checkbox = ttk.Checkbutton(
            self, text="Replace in Params and Body", variable=self.replace_in_body_params_var
        )
        replace_in_body_params_checkbox.grid(row=3, column=1, padx=20, pady=10, sticky="w")

        # Replace Button
        replace_button = ttk.Button(self, text="Replace Content", bootstyle="success", command=self.replace_content)
        replace_button.grid(row=4, column=0, columnspan=2, pady=20)

        # Status Label
        self.status_label = ttk.Label(self, text="", font=("Arial", 14), anchor="center")
        self.status_label.grid(row=5, column=0, columnspan=2, pady=10)

    def replace_content(self):
        text_to_replace = self.text_to_replace_var.get()
        replacement_text = self.replacement_text_var.get()
        replace_in_url = self.replace_in_url_var.get()
        replace_in_body_params = self.replace_in_body_params_var.get()

        # Validation
        if not text_to_replace:
            self.status_label.config(text="Please enter the text to replace.", bootstyle="danger")
            return

        if not replacement_text:
            self.status_label.config(text="Please enter the replacement text.", bootstyle="danger")
            return

        if not (replace_in_url or replace_in_body_params):
            self.status_label.config(text="Please select at least one replacement scope.", bootstyle="danger")
            return

        # Replace logic
        try:
            error_message = None
            for file_path in self.parent.file_upload_page.uploaded_file_paths:
                error_message = self.replace_content_backend(
                    file_path, text_to_replace, replacement_text, replace_in_url, replace_in_body_params
                )
                if error_message:
                    break  # Stop processing if there's an error

            # Show success or failure message
            if error_message:
                self.status_label.config(text=error_message, bootstyle="danger")
            else:
                self.status_label.config(
                    text=f"'{text_to_replace}' replaced with '{replacement_text}' successfully!", bootstyle="success"
                )
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}", bootstyle="danger")

    def replace_content_backend(self, file_path, text_to_replace, replacement_text, replace_in_url, replace_in_body_params):
        """
        Replace content logic in the backend.

        :param file_path: Path of the JMX file to modify.
        :param text_to_replace: Text to be replaced.
        :param replacement_text: Text to replace with.
        :param replace_in_url: Boolean indicating replacement in URL path.
        :param replace_in_body_params: Boolean indicating replacement in params and body.
        :return: None if successful, or an error message if there is a failure.
        """
        try:
            # Initialize JMXModifier with the uploaded file path
            modifier = JMXModifier(file_path)

            # Perform replacements based on selected options
            if replace_in_url:
                modifier.replace_string_in_url(text_to_replace, replacement_text)

            if replace_in_body_params:
                modifier.replace_string_in_body_and_params(text_to_replace, replacement_text)

            # Save the modified file with a new name
            output_path = file_path.replace(".jmx", "_modified.jmx")
            modifier.save_changes(output_path)

            return None  # No errors, replacement successful

        except ValueError as e:
            return f"Error: {str(e)}"
        except Exception as e:
            return f"Error modifying file {file_path}: {str(e)}"
