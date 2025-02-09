import ttkbootstrap as ttk
from tkinter import BOTH
from jmeter_methods.Jmeter_Automation_Methods import JMXModifier

class CheckoutPageForReplaceText(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=20)
        self.parent = parent
        self.text_replacements = []  # Stores text replacement details

        # 🏷️ Title Label
        title_label = ttk.Label(self, text="Checkout Page - Replace Text", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)

        # 📄 Frame for previewing text replacements
        self.preview_frame = ttk.Frame(self)
        self.preview_frame.pack(fill=BOTH, expand=True, pady=20)

        # 🛠 Button Frame (Align buttons)
        button_frame = ttk.Frame(self)
        button_frame.pack(fill="x", pady=10)

        # 🔙 Back Button
        back_button = ttk.Button(button_frame, text="🔙 Back", bootstyle="secondary",
                                 command=self.go_back_to_replace_text)
        back_button.pack(side="left", padx=20, pady=10)

        # ✅ Confirm Button
        confirm_button = ttk.Button(button_frame, text="✔ Confirm Changes", bootstyle="success",
                                    command=self.confirm_changes)
        confirm_button.pack(side="right", padx=20, pady=10)

        # 🔥 Status Label (Below Buttons)
        self.status_label = ttk.Label(self, text="", font=("Arial", 12, "bold"), bootstyle="info")
        self.status_label.pack(pady=10)

    def display_changes(self, replacements, replace_in_url, replace_in_body_params):
        """
        Display the text replacement pairs in the preview frame.
        :param replacements: List of tuples (old_text, new_text).
        :param replace_in_url: Boolean - Whether to replace in URL.
        :param replace_in_body_params: Boolean - Whether to replace in body params.
        """
        # Store replacements along with their scope
        self.text_replacements = [(old, new, replace_in_url, replace_in_body_params) for old, new in replacements]

        # Clear existing content in the preview frame
        for widget in self.preview_frame.winfo_children():
            widget.destroy()

        # 🎯 First row: "Replace in URL" and "Replace in Body"
        header_frame = ttk.Frame(self.preview_frame)
        header_frame.pack(fill="x", pady=5)

        ttk.Label(header_frame, text="Replace in URL", font=("Arial", 14, "bold")).grid(row=0, column=0, padx=20,
                                                                                        pady=5)
        ttk.Label(header_frame, text="Replace in Body", font=("Arial", 14, "bold")).grid(row=0, column=1, padx=20,
                                                                                         pady=5)

        ttk.Label(header_frame, text="✔" if replace_in_url else "❌", font=("Arial", 12)).grid(row=1, column=0, padx=20,
                                                                                              pady=5)
        ttk.Label(header_frame, text="✔" if replace_in_body_params else "❌", font=("Arial", 12)).grid(row=1, column=1,
                                                                                                      padx=20, pady=5)

        # 🎯 Second row: "Old Text" and "New Text"
        content_frame = ttk.Frame(self.preview_frame)
        content_frame.pack(fill="x", pady=5)

        ttk.Label(content_frame, text="Old Text", font=("Arial", 14, "bold")).grid(row=0, column=0, padx=20, pady=5)
        ttk.Label(content_frame, text="New Text", font=("Arial", 14, "bold")).grid(row=0, column=1, padx=20, pady=5)

        # 🔄 Populate the preview with entered replacement details
        for row, (old_text, new_text, _, _) in enumerate(self.text_replacements, start=1):
            ttk.Label(content_frame, text=f"🔵 {old_text}", font=("Arial", 12)).grid(row=row, column=0, padx=20, pady=5,
                                                                                     sticky="w")
            ttk.Label(content_frame, text=f"🟢 {new_text}", font=("Arial", 12)).grid(row=row, column=1, padx=20, pady=5,
                                                                                     sticky="w")

    def go_back_to_replace_text(self):
        """Navigate back to the Replace Content page."""
        self.parent.show_page(self.parent.replace_content_page)  # Fixed reference to correct page

    def confirm_changes(self):
        """Apply the text replacements to the uploaded JMX files."""
        uploaded_file_paths = self.parent.file_upload_page.uploaded_file_paths

        if not uploaded_file_paths:
            self.status_label.config(text="❌ No files uploaded!", bootstyle="danger")
            return

        if not self.text_replacements:
            self.status_label.config(text="❌ No text replacements provided!", bootstyle="danger")
            return

        # 🔄 Apply changes to each file
        error_messages = []
        success = False  # Track if at least one modification succeeded

        for file_path in uploaded_file_paths:
            try:
                modified = self.replace_text_backend(file_path, self.text_replacements)
                if modified:
                    success = True  # Mark success if modification happened
                else:
                    error_messages.append(f"⚠ No occurrences of given text found in {file_path}.")
            except ValueError as e:
                error_messages.append(f"❌ {str(e)}")

        # ✅ Display success or errors
        if success:
            self.status_label.config(text="✅ Text Replacements Applied Successfully!", bootstyle="success")
            self.after(2000, self.go_back_to_file_upload)
        else:
            self.status_label.config(text="\n".join(error_messages), bootstyle="danger")

    def go_back_to_file_upload(self):
        """Reset status and navigate back to file upload page."""
        self.status_label.config(text="")
        self.parent.file_upload_page.status_label.config(text="")
        self.parent.show_page(self.parent.file_upload_page)

    @staticmethod
    def replace_text_backend(file_path, text_replacements):
        """
        Backend logic to replace text in the provided JMX file.
        :param file_path: Path of the JMX file to modify.
        :param text_replacements: List of (old_text, new_text, replace_in_url, replace_in_body).
        :return: True if modifications occurred, False otherwise.
        """
        try:
            # Initialize JMXModifier with the uploaded file path
            modifier = JMXModifier(file_path)
            modified = False  # Flag to check if any change was made

            # Replace each text pair in the file based on selection
            for old_text, new_text, replace_in_url, replace_in_body in text_replacements:
                if replace_in_url:
                    result_url = modifier.replace_string_in_url(old_text, new_text)
                    if result_url:
                        modified = True

                if replace_in_body:
                    result_body = modifier.replace_string_in_body_and_params(old_text, new_text)
                    if result_body:
                        modified = True

            # If no modifications were made, return False
            if not modified:
                return False

            # Save the modified file with a new name
            output_path = file_path.replace(".jmx", "_modified.jmx")
            modifier.save_changes(output_path)
            return True  # Indicate success

        except Exception as e:
            raise ValueError(f"Error modifying file {file_path}: {str(e)}")
