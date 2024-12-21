import ttkbootstrap as ttk
from tkinter import StringVar
from jmeter_methods.Jmeter_Automation_Methods import JMXModifier

class HttpHeaderPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=20)
        self.parent = parent

        # Input fields for HTTP Header Manager
        self.header_name_var = StringVar()
        self.header_value_var = StringVar()

        header_name_label = ttk.Label(self, text="Header Name:", font=("Arial", 14))
        header_name_label.grid(row=0, column=0, padx=20, pady=10, sticky="w")

        header_name_entry = ttk.Entry(self, textvariable=self.header_name_var, width=50)
        header_name_entry.grid(row=0, column=1, padx=20, pady=10)

        header_value_label = ttk.Label(self, text="Header Value:", font=("Arial", 14))
        header_value_label.grid(row=1, column=0, padx=20, pady=10, sticky="w")

        header_value_entry = ttk.Entry(self, textvariable=self.header_value_var, width=50)
        header_value_entry.grid(row=1, column=1, padx=20, pady=10)

        apply_button = ttk.Button(self, text="Apply Changes", bootstyle="primary", command=self.modify_http_header)
        apply_button.grid(row=2, column=1, pady=20)

        self.status_label = ttk.Label(self, text="", font=("Arial", 14), anchor="center")
        self.status_label.grid(row=3, column=0, columnspan=2, pady=10)

    def modify_http_header(self):
        header_name = self.header_name_var.get()
        header_value = self.header_value_var.get()
        uploaded_file_paths = self.parent.file_upload_page.get_uploaded_files()

        if not header_name or not header_value:
            self.status_label.config(text="Please fill in both fields.", bootstyle="danger")
            return

        if not uploaded_file_paths:
            self.status_label.config(text="No files uploaded!", bootstyle="danger")
            return

        error_message = None
        for file_path in uploaded_file_paths:
            error_message = self.modify_http_header_backend(file_path, header_name, header_value)
            if error_message:
                break

        if error_message:
            self.status_label.config(text=error_message, bootstyle="danger")
        else:
            self.status_label.config(text="HTTP Header Modified Successfully!", bootstyle="success")

    @staticmethod
    def modify_http_header_backend(file_path, header_name, header_value):
        try:
            # Initialize JMXModifier with the uploaded file path
            modifier = JMXModifier(file_path)

            # Call the method to modify the HTTP header
            modifier.modify_http_header(header_name, header_value)

            # Save the modified file with a new name
            output_path = file_path.replace(".jmx", "_modified.jmx")
            modifier.save_changes(output_path)

            return None  # No errors, modification successful

        except ValueError as e:  # ValueError is raised when the header is not found
            return f"Error: {str(e)}"
        except Exception as e:
            return f"Error modifying file {file_path}: {str(e)}"
