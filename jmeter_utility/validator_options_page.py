# script_validator/validator_options_page.py
import ttkbootstrap as ttk
from tkinter import messagebox


class ValidatorOptionsPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=40)
        self.parent = parent

        self.pack(fill="both", expand=True)  # Ensure this frame fills the space

        # Frame for options to allow scrolling if many options
        options_frame = ttk.Frame(self)
        options_frame.pack(pady=20, fill="both", expand=True)

        ttk.Label(options_frame, text="Select Validation Options:", font=("Arial", 20, "bold"),
                  bootstyle="primary").pack(pady=(0, 20))

        # Define your validation options (matching `ReportPage`'s expectations)
        self.validation_options = {
            "Naming Convention (TXN_NN_Desc)": {"var": ttk.BooleanVar(value=True), "category": "Naming"},
            "Transaction Sequence (Contiguous)": {"var": ttk.BooleanVar(value=True), "category": "Sequencing"},
            "Module Controller Target Resolution": {"var": ttk.BooleanVar(value=True), "category": "Structure"},
            "Hardcoded URLs/IPs": {"var": ttk.BooleanVar(value=False), "category": "Best Practices"},
            "Presence of Timers (per Transaction)": {"var": ttk.BooleanVar(value=False), "category": "Best Practices"},
            "No Debug Samplers in Production": {"var": ttk.BooleanVar(value=True), "category": "Best Practices"},
            "Use of HTTP Cache Manager": {"var": ttk.BooleanVar(value=False), "category": "Performance"},
            "Use of HTTP Cookie Manager": {"var": ttk.BooleanVar(value=False), "category": "Performance"},
            "Assertions within Transaction/Sampler Scope": {"var": ttk.BooleanVar(value=False),
                                                            "category": "Structure"},
            "No Disabled Elements": {"var": ttk.BooleanVar(value=False), "category": "Cleanliness"},
            "Presence of User Defined Variables": {"var": ttk.BooleanVar(value=False), "category": "Best Practices"},
            "Listener Usage (Recommended Off for Load Test)": {"var": ttk.BooleanVar(value=False),
                                                               "category": "Performance"},
            "Proper Variable Parameterization (e.g., no raw numbers in requests)": {"var": ttk.BooleanVar(value=False),
                                                                                    "category": "Parameterization"},
            "Correlation for Dynamic Data": {"var": ttk.BooleanVar(value=False), "category": "Correlation"},
            "Error Handling (Listeners/Assertions for Errors)": {"var": ttk.BooleanVar(value=False),
                                                                 "category": "Error Handling"},
        }

        # Create checkboxes for each option
        self.checkboxes = []
        for text, config in self.validation_options.items():
            chk = ttk.Checkbutton(options_frame, text=f"[{config['category']}] {text}", variable=config['var'],
                                  bootstyle="info-round-toggle")
            chk.pack(anchor="w", padx=50, pady=3)
            self.checkboxes.append(chk)

        # Action Buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=20)

        generate_report_button = ttk.Button(button_frame, text="Generate Report", bootstyle="success",
                                            command=self.generate_report)
        generate_report_button.pack(side="left", padx=10, ipadx=30, ipady=15)

        back_button = ttk.Button(button_frame, text="Back to File Upload", bootstyle="secondary",
                                 command=lambda: self.parent.show_page(self.parent.validator_file_upload_page))
        back_button.pack(side="left", padx=10, ipadx=10, ipady=5)

    def get_selected_validations(self):
        # Returns a list of strings representing the selected validation names
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

        # Pass data to the ReportPage and show it
        self.parent.validator_report_page.start_report_generation(selected_files, selected_validations)
        self.parent.show_page(self.parent.validator_report_page)