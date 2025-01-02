import ttkbootstrap as ttk
from tkinter import StringVar, ttk
from tkinter import messagebox
from jmeter_methods.Jmeter_Automation_Methods import JMXModifier


class ReplaceDomainNamePage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=20)
        self.parent = parent

        # Title for the page
        title_label = ttk.Label(self, text="Replace Domain Name in Requests", font=("Arial", 22, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=20)

        # Label and Entry for the Old Domain Name
        old_domain_label = ttk.Label(self, text="Enter Domain Name to Replace:", font=("Arial", 14))
        old_domain_label.grid(row=1, column=0, padx=20, pady=10, sticky="w")

        self.old_domain_var = StringVar()
        old_domain_entry = ttk.Entry(self, textvariable=self.old_domain_var, width=50)
        old_domain_entry.grid(row=1, column=1, padx=20, pady=10)

        # Label and Entry for the New Domain Name
        new_domain_label = ttk.Label(self, text="Enter New Domain Name or New Text:", font=("Arial", 14))
        new_domain_label.grid(row=2, column=0, padx=20, pady=10, sticky="w")

        self.new_domain_var = StringVar()
        new_domain_entry = ttk.Entry(self, textvariable=self.new_domain_var, width=50)
        new_domain_entry.grid(row=2, column=1, padx=20, pady=10)

        # Button to replace the domain name
        replace_button = ttk.Button(self, text="Replace Domain Name", bootstyle="primary", command=self.replace_domain)
        replace_button.grid(row=3, column=0, columnspan=2, pady=20)

        # Status Label
        self.status_label = ttk.Label(self, text="", font=("Arial", 14), anchor="center")
        self.status_label.grid(row=4, column=0, columnspan=2, pady=10)

    def replace_domain(self):
        old_domain = self.old_domain_var.get()
        new_domain = self.new_domain_var.get()

        if not old_domain or not new_domain:
            self.status_label.config(
                text="Both the old domain name and new domain name are required.",
                bootstyle="danger"
            )
            return

        # Call the method to replace the domain in the uploaded files
        try:
            error_message = None
            for file_path in self.parent.file_upload_page.uploaded_file_paths:
                error_message = self.replace_domain_backend(file_path, old_domain, new_domain)
                if error_message:
                    break  # Stop processing if there's an error

            # Show success or failure message
            if error_message:
                self.status_label.config(text=error_message, bootstyle="danger")
            else:
                self.status_label.config(
                    text=f"Domain '{old_domain}' successfully replaced with '{new_domain}'!",
                    bootstyle="success"
                )
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}", bootstyle="danger")

    def replace_domain_backend(self, file_path, old_domain, new_domain):
        """
        Replace the specified domain name in the JMX file.

        :param file_path: Path of the JMX file to modify.
        :param old_domain: Domain name to replace.
        :param new_domain: New domain name to replace with.
        :return: None if successful, or an error message if there is a failure.
        """
        try:
            # Initialize JMXModifier with the uploaded file path
            modifier = JMXModifier(file_path)

            # Call the method to replace the domain name
            modifier.replace_domain_name(old_domain, new_domain)

            # Save the modified file with a new name
            output_path = file_path.replace(".jmx", "_modified.jmx")
            modifier.save_changes(output_path)

            return None  # No errors, replacement successful

        except ValueError as e:
            return f"Error: {str(e)}"
        except Exception as e:
            return f"Error modifying file {file_path}: {str(e)}"
