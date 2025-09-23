# script_validator/validator_report_page.py
import ttkbootstrap as ttk
from tkinter import messagebox
import os
import threading
import webbrowser
import xml.etree.ElementTree as ET
from datetime import datetime

# Import core validation logic for TXN Naming
from jmeter_methods.Val_Backend_TXN_Naming_Convention import analyze_jmeter_script as analyze_txn_naming_script, \
    THIS_VALIDATION_OPTION_NAME as TXN_VALIDATION_OPTION_NAME

# Import core validation logic for KPI Naming
from jmeter_methods.Val_Backend_HTTPRequest_Naming_Standard import analyze_jmeter_script as analyze_kpi_naming_script, \
    THIS_VALIDATION_OPTION_NAME as KPI_VALIDATION_OPTION_NAME

# Import core validation logic for Server Name/Domain Hygiene
from jmeter_methods.Val_Backend_Server_Name_Hygiene import analyze_jmeter_script as analyze_server_hygiene_script, \
    THIS_VALIDATION_OPTION_NAME as SERVER_HYGIENE_VALIDATION_OPTION_NAME

# Import core validation logic for Extractor and Variable Naming Standards
from jmeter_methods.Val_Backend_Extractor_Variable_Standards import \
    analyze_jmeter_script as analyze_extractor_standards_script, \
    THIS_VALIDATION_OPTION_NAME as EXTRACTOR_STANDARDS_VALIDATION_OPTION_NAME

# Import core validation logic for Variable Naming Convention
from jmeter_methods.Val_Backend_Variable_Naming_Conventions import analyze_jmeter_script as analyze_variable_standards, \
    THIS_VALIDATION_OPTION_NAME as VARIABLE_NAMING_CONVENTION_OPTION_NAME

# Import core validation logic for Hard coded value detection
from jmeter_methods.Val_Hardcoded_Value_Detection import analyze_jmeter_script as analyze_hardcoded_value_detection, \
    THIS_VALIDATION_OPTION_NAME as HARDCODED_VALUE_DETECTION_OPTION_NAME

# Import core validation logic for unused extractor variable detection.
from jmeter_methods.Val_Backend_Unused_Extractors_And_Variables_Detection import \
    analyze_jmeter_script as analyze_unused_extrator_and_variable_detection, \
    THIS_VALIDATION_OPTION_NAME as UNUSED_EXTRACTOR_AND_VARIABLE_DETECTION

# Import core validation logic for Unextracted Variables Detection
from jmeter_methods.Val_Backend_Unextracted_Variable_Detection import \
    analyze_jmeter_script as analyze_unextracted_variable_detection, \
    THIS_VALIDATION_OPTION_NAME as UNEXTRACTED_VARIABLE_DETECTION

# Import core validation logic for Duplicate extractors
from jmeter_methods.Val_Backend_Duplicate_Extractors import analyze_jmeter_script as analyze_duplicate_extractor_detection, \
    THIS_VALIDATION_OPTION_NAME as DUPLICATE_EXTRACTOR_DETECTION_OPTION_NAME

# Import report generation functions
from Report.report_generator import generate_html_report

# --- IMPORTANT: Update this list with all your validation option names ---
ALL_VALIDATION_OPTIONS = [
    TXN_VALIDATION_OPTION_NAME,
    KPI_VALIDATION_OPTION_NAME,
    SERVER_HYGIENE_VALIDATION_OPTION_NAME,
    EXTRACTOR_STANDARDS_VALIDATION_OPTION_NAME,
    VARIABLE_NAMING_CONVENTION_OPTION_NAME,
    HARDCODED_VALUE_DETECTION_OPTION_NAME,
    UNUSED_EXTRACTOR_AND_VARIABLE_DETECTION,
    UNEXTRACTED_VARIABLE_DETECTION,
    DUPLICATE_EXTRACTOR_DETECTION_OPTION_NAME
    # ADDED THIS LINE
]


class ValidatorReportPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=40)
        self.parent = parent
        self.pack(fill="both", expand=True)

        self.report_label = ttk.Label(self, text="Report Generation Status", font=("Arial", 20, "bold"),
                                      bootstyle="primary")
        self.report_label.pack(pady=20)

        self.progress_bar = ttk.Progressbar(self, orient="horizontal", length=600, mode="determinate", bootstyle="info")
        self.progress_bar.pack(pady=10, padx=50, fill="x")

        self.status_label = ttk.Label(self, text="Awaiting JMX files...", font=("Arial", 12), bootstyle="info")
        self.status_label.pack(pady=5)

        self.open_report_button = ttk.Button(self, text="Open Latest Report Folder", command=self.open_reports_folder,
                                             state=ttk.DISABLED, bootstyle="success outline")
        self.open_report_button.pack(pady=10)

        back_button = ttk.Button(self, text="Back to Options", bootstyle="secondary",
                                 command=lambda: self.parent.show_page(self.parent.validator_options_page))
        back_button.pack(pady=10)

        self.reports_generated_paths = []

    def start_report_generation(self, files, validations):
        self.reports_generated_paths = []
        self.report_label.config(text="Report Generation in Progress...")
        self.progress_bar.config(mode="determinate", value=0)
        self.status_label.config(text="Starting validation process...")
        self.open_report_button.config(state=ttk.DISABLED)

        thread = threading.Thread(target=self._generate_reports_threaded, args=(files, validations), daemon=True)
        thread.start()

    def _generate_reports_threaded(self, files, validations):
        total_files = len(files)

        try:
            if not files:
                self.status_label.config(text="No JMX files selected for validation.")
                messagebox.showwarning("No Files", "No JMX files were found to validate.", parent=self.parent)
                return

            for i, file_path in enumerate(files):
                file_name = os.path.basename(file_path)
                self.status_label.config(text=f"Processing: {file_name} ({i + 1}/{total_files})")
                self.update_idletasks()

                jmx_file_directory = os.path.dirname(file_path)
                current_file_output_dir = os.path.join(jmx_file_directory, "JMeter_Validation_Reports")

                if not os.path.exists(current_file_output_dir):
                    os.makedirs(current_file_output_dir)

                root_element = None
                all_issues_for_current_file = []

                try:
                    tree = ET.parse(file_path)
                    root_element = tree.getroot()
                except ET.ParseError as e:
                    all_issues_for_current_file.append({
                        'severity': 'ERROR',
                        'validation_option_name': "JMX File Parsing",
                        'type': 'XML Parsing',
                        'location': 'JMX File',
                        'description': f"Failed to parse JMX file: {e}. Ensure it's a valid XML.",
                        'thread_group': 'N/A'
                    })
                    self.status_label.config(
                        text=f"Skipped {file_name}: Failed to parse JMX. Report generated with parsing error.",
                        bootstyle="danger")
                    self.update_idletasks()
                except FileNotFoundError:
                    all_issues_for_current_file.append({
                        'severity': 'ERROR',
                        'validation_option_name': "JMX File Parsing",
                        'type': 'File Not Found',
                        'location': 'JMX File',
                        'description': f"JMX file not found at: {file_path}",
                        'thread_group': 'N/A'
                    })
                    self.status_label.config(
                        text=f"Skipped {file_name}: JMX file not found. Report generated with error.",
                        bootstyle="danger")
                    self.update_idletasks()

                if root_element is not None:
                    # The following blocks now correctly unpack the (issues, debug_log) tuple
                    # and append issues to the master list.

                    if TXN_VALIDATION_OPTION_NAME in validations:
                        self.status_label.config(
                            text=f"Processing {file_name}: Validating {TXN_VALIDATION_OPTION_NAME}...",
                            bootstyle="info")
                        self.update_idletasks()
                        txn_issues, _ = analyze_txn_naming_script(root_element, validations)
                        if txn_issues is not None:
                            all_issues_for_current_file.extend(txn_issues)
                        else:
                            all_issues_for_current_file.append(
                                {'severity': 'ERROR', 'validation_option_name': TXN_VALIDATION_OPTION_NAME,
                                 'type': 'Internal Module Error', 'location': 'JMeter Script Analysis',
                                 'description': f"The '{TXN_VALIDATION_OPTION_NAME}' validation module returned None.",
                                 'thread_group': 'N/A'})

                    if KPI_VALIDATION_OPTION_NAME in validations:
                        self.status_label.config(
                            text=f"Processing {file_name}: Validating {KPI_VALIDATION_OPTION_NAME}...",
                            bootstyle="info")
                        self.update_idletasks()
                        kpi_issues, _ = analyze_kpi_naming_script(root_element, validations)
                        if kpi_issues is not None:
                            all_issues_for_current_file.extend(kpi_issues)
                        else:
                            all_issues_for_current_file.append(
                                {'severity': 'ERROR', 'validation_option_name': KPI_VALIDATION_OPTION_NAME,
                                 'type': 'Internal Module Error', 'location': 'JMeter Script Analysis',
                                 'description': f"The '{KPI_VALIDATION_OPTION_NAME}' validation module returned None.",
                                 'thread_group': 'N/A'})

                    if SERVER_HYGIENE_VALIDATION_OPTION_NAME in validations:
                        self.status_label.config(
                            text=f"Processing {file_name}: Validating {SERVER_HYGIENE_VALIDATION_OPTION_NAME}...",
                            bootstyle="info")
                        self.update_idletasks()
                        server_hygiene_issues, _ = analyze_server_hygiene_script(root_element, validations)
                        if server_hygiene_issues is not None:
                            all_issues_for_current_file.extend(server_hygiene_issues)
                        else:
                            all_issues_for_current_file.append(
                                {'severity': 'ERROR', 'validation_option_name': SERVER_HYGIENE_VALIDATION_OPTION_NAME,
                                 'type': 'Internal Module Error', 'location': 'JMeter Script Analysis',
                                 'description': f"The '{SERVER_HYGIENE_VALIDATION_OPTION_NAME}' validation module returned None.",
                                 'thread_group': 'N/A'})

                    if EXTRACTOR_STANDARDS_VALIDATION_OPTION_NAME in validations:
                        self.status_label.config(
                            text=f"Processing {file_name}: Validating {EXTRACTOR_STANDARDS_VALIDATION_OPTION_NAME}...",
                            bootstyle="info")
                        self.update_idletasks()
                        extractor_issues, _ = analyze_extractor_standards_script(root_element, validations)
                        if extractor_issues is not None:
                            all_issues_for_current_file.extend(extractor_issues)
                        else:
                            all_issues_for_current_file.append({'severity': 'ERROR',
                                                                'validation_option_name': EXTRACTOR_STANDARDS_VALIDATION_OPTION_NAME,
                                                                'type': 'Internal Module Error',
                                                                'location': 'JMeter Script Analysis',
                                                                'description': f"The '{EXTRACTOR_STANDARDS_VALIDATION_OPTION_NAME}' validation module returned None.",
                                                                'thread_group': 'N/A'})

                    if VARIABLE_NAMING_CONVENTION_OPTION_NAME in validations:
                        self.status_label.config(
                            text=f"Processing {file_name}: Validating {VARIABLE_NAMING_CONVENTION_OPTION_NAME}...",
                            bootstyle="info")
                        self.update_idletasks()
                        variable_naming_convention_issues, _ = analyze_variable_standards(root_element, validations)
                        if variable_naming_convention_issues is not None:
                            all_issues_for_current_file.extend(variable_naming_convention_issues)
                        else:
                            all_issues_for_current_file.append(
                                {'severity': 'ERROR', 'validation_option_name': VARIABLE_NAMING_CONVENTION_OPTION_NAME,
                                 'type': 'Internal Module Error', 'location': 'JMeter Script Analysis',
                                 'description': f"The '{VARIABLE_NAMING_CONVENTION_OPTION_NAME}' validation module returned None.",
                                 'thread_group': 'N/A'})

                    if HARDCODED_VALUE_DETECTION_OPTION_NAME in validations:
                        self.status_label.config(
                            text=f"Processing {file_name}: Validating {HARDCODED_VALUE_DETECTION_OPTION_NAME}...",
                            bootstyle="info")
                        self.update_idletasks()
                        hardcoded_value_detecion_issues, _ = analyze_hardcoded_value_detection(root_element,
                                                                                               validations)
                        if hardcoded_value_detecion_issues is not None:
                            all_issues_for_current_file.extend(hardcoded_value_detecion_issues)
                        else:
                            all_issues_for_current_file.append(
                                {'severity': 'ERROR', 'validation_option_name': HARDCODED_VALUE_DETECTION_OPTION_NAME,
                                 'type': 'Internal Module Error', 'location': 'JMeter Script Analysis',
                                 'description': f"The '{HARDCODED_VALUE_DETECTION_OPTION_NAME}' validation module returned None.",
                                 'thread_group': 'N/A'})

                    if UNUSED_EXTRACTOR_AND_VARIABLE_DETECTION in validations:
                        self.status_label.config(
                            text=f"Processing {file_name}: Validating {UNUSED_EXTRACTOR_AND_VARIABLE_DETECTION}...",
                            bootstyle="info")
                        self.update_idletasks()
                        unused_extrators_and_variable_detection_issues, _ = analyze_unused_extrator_and_variable_detection(
                            root_element, validations)
                        if unused_extrators_and_variable_detection_issues is not None:
                            all_issues_for_current_file.extend(unused_extrators_and_variable_detection_issues)
                        else:
                            all_issues_for_current_file.append(
                                {'severity': 'ERROR', 'validation_option_name': UNUSED_EXTRACTOR_AND_VARIABLE_DETECTION,
                                 'type': 'Internal Module Error', 'location': 'JMeter Script Analysis',
                                 'description': f"The '{UNUSED_EXTRACTOR_AND_VARIABLE_DETECTION}' validation module returned None.",
                                 'thread_group': 'N/A'})

                    # NEW BLOCK for Unextracted Variables Detection
                    if UNEXTRACTED_VARIABLE_DETECTION in validations:
                        self.status_label.config(
                            text=f"Processing {file_name}: Validating {UNEXTRACTED_VARIABLE_DETECTION}...",
                            bootstyle="info")
                        self.update_idletasks()
                        unextracted_variable_issues, _ = analyze_unextracted_variable_detection(root_element,
                                                                                                validations)
                        if unextracted_variable_issues is not None:
                            all_issues_for_current_file.extend(unextracted_variable_issues)
                        else:
                            all_issues_for_current_file.append(
                                {'severity': 'ERROR', 'validation_option_name': UNEXTRACTED_VARIABLE_DETECTION,
                                 'type': 'Internal Module Error', 'location': 'JMeter Script Analysis',
                                 'description': f"The '{UNEXTRACTED_VARIABLE_DETECTION}' validation module returned None.",
                                 'thread_group': 'N/A'})

                    if DUPLICATE_EXTRACTOR_DETECTION_OPTION_NAME in validations:
                        self.status_label.config(
                            text=f"Processing {file_name}: Validating {DUPLICATE_EXTRACTOR_DETECTION_OPTION_NAME}...",
                            bootstyle="info")
                        self.update_idletasks()
                        duplicate_extractor_issues, _ = analyze_duplicate_extractor_detection(root_element,
                                                                                                validations)
                        if duplicate_extractor_issues is not None:
                            all_issues_for_current_file.extend(duplicate_extractor_issues)
                        else:
                            all_issues_for_current_file.append(
                                {'severity': 'ERROR', 'validation_option_name': DUPLICATE_EXTRACTOR_DETECTION_OPTION_NAME,
                                 'type': 'Internal Module Error', 'location': 'JMeter Script Analysis',
                                 'description': f"The '{DUPLICATE_EXTRACTOR_DETECTION_OPTION_NAME}' validation module returned None.",
                                 'thread_group': 'N/A'})


                report_data = {
                    "file_path": file_path,
                    "issues": all_issues_for_current_file
                }

                report_html_path = os.path.join(current_file_output_dir,
                                                f"{os.path.splitext(file_name)[0]}_validation_report.html")
                generate_html_report(report_data, report_html_path,
                                     validations)
                self.reports_generated_paths.append(report_html_path)

                progress_value = ((i + 1) / total_files) * 100
                self.progress_bar["value"] = progress_value
                self.update_idletasks()

            self.status_label.config(text="Report generation complete!")
            self.report_label.config(text="Reports Generated Successfully!")
            self.open_report_button.config(state=ttk.NORMAL)

            if self.reports_generated_paths:
                first_report_example_dir = os.path.dirname(self.reports_generated_paths[0])
                messagebox.showinfo("Reports Generated",
                                    f"Validation reports have been generated in 'JMeter_Validation_Reports' subfolders located alongside each JMX file (e.g., in '{first_report_example_dir}').",
                                    parent=self.parent)
            else:
                messagebox.showwarning("No Reports", "No reports were generated due to errors or no files selected.",
                                       parent=self.parent)

        except Exception as e:
            self.status_label.config(text=f"An unexpected error occurred: {e}", bootstyle="danger")
            self.report_label.config(text="Report Generation Failed!", bootstyle="danger")
            messagebox.showerror("Error", f"An unexpected error occurred during report generation: {e}.",
                                 parent=self.parent)
        finally:
            self.progress_bar["value"] = 100
            self.update_idletasks()

    def open_reports_folder(self):
        if self.reports_generated_paths:
            last_report_path = self.reports_generated_paths[-1]
            report_folder_to_open = os.path.dirname(last_report_path)
            if os.path.exists(report_folder_to_open):
                webbrowser.open(os.path.abspath(report_folder_to_open))
            else:
                messagebox.showwarning("Folder Not Found",
                                       f"The report folder for the last JMX file does not exist: '{report_folder_to_open}'.",
                                       parent=self.parent)
        else:
            messagebox.showwarning("No Reports", "No reports have been generated yet to open a folder.",
                                   parent=self.parent)