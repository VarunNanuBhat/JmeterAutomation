# Validator_options_page.py
import ttkbootstrap as ttk
from tkinter import messagebox


class ValidatorOptionsPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=40)
        self.parent = parent

        self.pack(fill="both", expand=True)

        self.validation_options = self._define_validation_options()
        self._create_widgets()

    def _define_validation_options(self):
        # Updated to include only the three specified options
        return {
            "Naming Convention (TXN_NN_Desc)": {"var": ttk.BooleanVar(value=True), "category": "Naming"},
            "HTTP Request Naming (KPI_method_urlPath)": {"var": ttk.BooleanVar(value=False), "category": "Naming"},
            "Server Name/Domain Hygiene": {"var": ttk.BooleanVar(value=True), "category": "Network"},
            "Extractor Variable Naming Standards": {"var": ttk.BooleanVar(value=True), "category": "Network"},
            "Variable Naming Conventions": {"var": ttk.BooleanVar(value=True), "category": "Network"},
            "Hardcoded Value Detection": {"var": ttk.BooleanVar(value=True), "category": "Network"},
            "Unused Extractors/Variables Detection": {"var": ttk.BooleanVar(value=True), "category": "Network"},
        }

    def _create_widgets(self):
        options_frame = ttk.Frame(self)
        options_frame.pack(pady=20, fill="both", expand=True)

        ttk.Label(options_frame, text="Select Validation Options:", font=("Arial", 20, "bold"),
                  bootstyle="primary").pack(pady=(0, 20))

        for text, config in self.validation_options.items():
            chk = ttk.Checkbutton(options_frame, text=f"[{config['category']}] {text}", variable=config['var'],
                                  bootstyle="info-round-toggle")
            chk.pack(anchor="w", padx=50, pady=3)

        button_frame = ttk.Frame(self)
        button_frame.pack(pady=20)

        generate_report_button = ttk.Button(button_frame, text="Generate Report", bootstyle="success",
                                            command=self.generate_report)
        generate_report_button.pack(side="left", padx=10, ipadx=30, ipady=15)

        back_button = ttk.Button(button_frame, text="Back to File Upload", bootstyle="secondary",
                                 command=lambda: self.parent.show_page(self.parent.validator_file_upload_page))
        back_button.pack(side="left", padx=10, ipadx=10, ipady=5)

    def get_selected_validations(self):
        selected = [name for name, config in self.validation_options.items() if config['var'].get()]
        return selected

    def generate_report(self):
        selected_files = self.parent.get_validator_jmx_files()
        selected_validations = self.get_selected_validations()

        if not selected_validations:
            messagebox.showwarning("No Validations Selected", "Please select at least one validation option.",
                                   parent=self.parent)
            return

        if not selected_files:
            messagebox.showwarning("No Files", "No JMX files were selected. Please go back and select files.",
                                   parent=self.parent)
            self.parent.show_page(self.parent.validator_file_upload_page)
            return

        # Delegate the report generation process to the ValidatorReportPage
        self.parent.validator_report_page.start_report_generation(selected_files, selected_validations)
        self.parent.show_page(self.parent.validator_report_page)