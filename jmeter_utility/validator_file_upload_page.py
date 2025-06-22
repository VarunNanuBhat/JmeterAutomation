# script_validator/validator_file_upload_page.py
import ttkbootstrap as ttk
from tkinter import filedialog, messagebox
import os

class ValidatorFileUploadPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=40)
        self.parent = parent
        self.selected_files = []

        self.pack(fill="both", expand=True) # Ensure this frame fills the space

        # Center content
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)
        self.rowconfigure(3, weight=1)
        self.rowconfigure(4, weight=1)

        ttk.Label(self, text="Upload JMeter JMX Files for Validation", font=("Arial", 24, "bold"), bootstyle="primary").grid(row=0, column=0, pady=(50, 20), sticky="n")

        self.file_list_label = ttk.Label(self, text="No files selected.", font=("Arial", 12), bootstyle="info")
        self.file_list_label.grid(row=1, column=0, pady=10, sticky="n")

        upload_button = ttk.Button(self, text="Select JMX Files", bootstyle="info outline", command=self.select_files)
        upload_button.grid(row=2, column=0, ipadx=20, ipady=10, pady=20, sticky="n")

        proceed_button = ttk.Button(self, text="Proceed to Validations", bootstyle="success", command=self.proceed_to_validations)
        proceed_button.grid(row=3, column=0, ipadx=30, ipady=15, pady=30, sticky="n")

        back_button = ttk.Button(self, text="Back to Home", bootstyle="secondary", command=lambda: self.parent.show_page(self.parent.homepage))
        back_button.grid(row=4, column=0, ipadx=10, ipady=5, pady=10, sticky="s")


    def select_files(self):
        file_paths = filedialog.askopenfilenames(
            title="Select JMeter JMX Files",
            filetypes=[("JMeter JMX files", "*.jmx")]
        )
        if file_paths:
            self.selected_files = list(file_paths)
            file_names = [os.path.basename(f) for f in self.selected_files]
            self.file_list_label.config(text=f"Selected Files ({len(self.selected_files)}):\n" + "\n".join(file_names[:5]) + ("\n..." if len(file_names) > 5 else ""))
        else:
            self.selected_files = []
            self.file_list_label.config(text="No files selected.")

    def proceed_to_validations(self):
        if not self.selected_files:
            messagebox.showwarning("No Files Selected", "Please select one or more JMX files to proceed.", parent=self.parent)
            return

        # Pass selected files to the App class
        self.parent.set_validator_jmx_files(self.selected_files)
        self.parent.show_page(self.parent.validator_options_page)