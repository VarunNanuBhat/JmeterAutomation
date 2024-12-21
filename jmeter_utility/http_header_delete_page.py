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
        title_label.grid(row=0, column=0, pady=20)

        # Label and Entry for Header Name
        header_name_label = ttk.Label(self, text="Enter Header Name to Delete:", font=("Arial", 14))
        header_name_label.grid(row=1, column=0, padx=20, pady=10, sticky="w")

        self.header_name_var = StringVar()
        header_name_entry = ttk.Entry(self, textvariable=self.header_name_var, width=50)
        header_name_entry.grid(row=1, column=1, padx=20, pady=10)

        # Button to delete the specified header
        delete_button = ttk.Button(self, text="Delete Header", bootstyle="danger", command=self.delete_header)
        delete_button.grid(row=2, column=0, columnspan=2, pady=20)

        # Status Label
        self.status_label = ttk.Label(self, text="", font=("Arial", 14), anchor="center")
        self.status_label.grid(row=3, column=0, columnspan=2, pady=10)

    def delete_header(self):
        header_name = self.header_name_var.get()
        if not header_name:
            self.status_label.config(text="Please enter a header name.", bootstyle="danger")
            return

        # Call the method to delete the header from the uploaded files
        try:
            error_message = None
            for file_path in self.parent.file_upload_page.uploaded_file_paths:
                error_message = self.delete_http_header_backend(file_path, header_name)
                if error_message:
                    break  # Stop processing if there's an error

            # Show success or failure message
            if error_message:
                self.status_label.config(text=error_message, bootstyle="danger")
            else:
                self.status_label.config(text=f"Header '{header_name}' deleted successfully!", bootstyle="success")
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}", bootstyle="danger")

    def delete_http_header_backend(self, file_path, header_name):
        """
        Deletes the specified HTTP header key-value pair from the JMX file.

        :param file_path: Path of the JMX file to modify.
        :param header_name: Header name to delete.
        :return: None if successful, or an error message if there is a failure.
        """
        try:
            # Initialize JMXModifier with the uploaded file path
            modifier = JMXModifier(file_path)

            # Call the method to delete the specified HTTP header
            modifier.delete_http_header(header_name)

            # Save the modified file with a new name
            output_path = file_path.replace(".jmx", "_modified.jmx")
            modifier.save_changes(output_path)

            return None  # No errors, deletion successful

        except ValueError as e:
            return f"Error: {str(e)}"
        except Exception as e:
            return f"Error modifying file {file_path}: {str(e)}"
