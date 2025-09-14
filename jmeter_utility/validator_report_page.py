import ttkbootstrap as ttk
from tkinter import messagebox
import os
import threading
import webbrowser
import xml.etree.ElementTree as ET
from datetime import datetime
from queue import Queue, Empty

# Import core validation logic
from jmeter_methods.Val_Backend_TXN_Naming_Convention import analyze_jmeter_script as analyze_txn_naming_script, THIS_VALIDATION_OPTION_NAME as TXN_VALIDATION_OPTION_NAME
from jmeter_methods.Val_Backend_HTTPRequest_Naming_Standard import analyze_jmeter_script as analyze_kpi_naming_script, THIS_VALIDATION_OPTION_NAME as KPI_VALIDATION_OPTION_NAME
from jmeter_methods.Val_Backend_Server_Name_Hygiene import analyze_jmeter_script as analyze_server_hygiene_script, THIS_VALIDATION_OPTION_NAME as SERVER_HYGIENE_VALIDATION_OPTION_NAME
from jmeter_methods.Val_Backend_Extractor_Variable_Standards import analyze_jmeter_script as analyze_extractor_standards_script, THIS_VALIDATION_OPTION_NAME as EXTRACTOR_STANDARDS_VALIDATION_OPTION_NAME
from jmeter_methods.Val_Backend_Variable_Naming_Conventions import analyze_jmeter_script as analyze_variable_standards, THIS_VALIDATION_OPTION_NAME as VARIABLE_NAMING_CONVENTION_OPTION_NAME
from jmeter_methods.Val_Hardcoded_Value_Detection import analyze_jmeter_script as analyze_hardcoded_value_detection, THIS_VALIDATION_OPTION_NAME as HARDCODED_VALUE_DETECTION_OPTION_NAME
from jmeter_methods.Val_Backend_Unused_Extractors_And_Variables_Detection import analyze_jmeter_script as analyze_unused_extractor_and_variable_detection, THIS_VALIDATION_OPTION_NAME as UNUSED_EXTRACTOR_AND_VARIABLE_DETECTION_OPTION_NAME

# Import report generation functions
from Report.report_generator import generate_html_report

ALL_VALIDATION_OPTIONS = [
    TXN_VALIDATION_OPTION_NAME,
    KPI_VALIDATION_OPTION_NAME,
    SERVER_HYGIENE_VALIDATION_OPTION_NAME,
    EXTRACTOR_STANDARDS_VALIDATION_OPTION_NAME,
    VARIABLE_NAMING_CONVENTION_OPTION_NAME,
    HARDCODED_VALUE_DETECTION_OPTION_NAME,
    UNUSED_EXTRACTOR_AND_VARIABLE_DETECTION_OPTION_NAME
]

class ValidatorReportPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=40)
        self.parent = parent
        self.pack(fill="both", expand=True)
        self.queue = Queue()
        self.reports_generated_paths = []

        self.report_label = ttk.Label(self, text="Report Generation Status", font=("Arial", 20, "bold"), bootstyle="primary")
        self.report_label.pack(pady=20)

        self.progress_bar = ttk.Progressbar(self, orient="horizontal", length=600, mode="determinate", bootstyle="info")
        self.progress_bar.pack(pady=10, padx=50, fill="x")

        self.status_label = ttk.Label(self, text="Awaiting JMX files...", font=("Arial", 12), bootstyle="info")
        self.status_label.pack(pady=5)

        self.open_report_button = ttk.Button(self, text="Open Latest Report Folder", command=self.open_reports_folder, state=ttk.DISABLED, bootstyle="success outline")
        self.open_report_button.pack(pady=10)

        back_button = ttk.Button(self, text="Back to Options", bootstyle="secondary", command=lambda: self.parent.show_page(self.parent.validator_options_page))
        back_button.pack(pady=10)

        self.log_frame = ttk.Frame(self, borderwidth=2, relief="groove")
        self.log_frame.pack(pady=20, padx=20, fill="both", expand=True)

        self.log_label = ttk.Label(self.log_frame, text="Debug and Analysis Log", font=("Arial", 12, "bold"))
        self.log_label.pack(pady=(5, 0))

        self.log_text = ttk.Text(self.log_frame, wrap="word", height=15)
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.log_text.bind("<KeyPress>", lambda e: "break")

    def _update_ui(self):
        try:
            while True:
                func, args = self.queue.get_nowait()
                if isinstance(args, dict):
                    func(**args)
                else:
                    func(*args)
                self.queue.task_done()
        except Empty:
            pass
        self.after(100, self._update_ui)

    def _log_message(self, message):
        self.log_text.insert(ttk.END, message + "\n")
        self.log_text.see(ttk.END)
        self.parent.update_idletasks()

    def start_report_generation(self, files, validations):
        self.reports_generated_paths = []
        self.report_label.config(text="Report Generation in Progress...")
        self.progress_bar.config(mode="determinate", value=0)
        self.status_label.config(text="Starting validation process...")
        self.open_report_button.config(state=ttk.DISABLED)
        self.log_text.delete(1.0, ttk.END)

        thread = threading.Thread(target=self._generate_reports_threaded, args=(files, validations), daemon=True)
        thread.start()
        self.after(100, self._update_ui)

    def _generate_reports_threaded(self, files, validations):
        total_files = len(files)
        self.queue.put((self._log_message, ["Starting Report Generation Thread..."]))
        try:
            if not files:
                self.queue.put((self.status_label.config, {"text": "No JMX files selected for validation."}))
                self.queue.put((messagebox.showwarning, {"title": "No Files", "message": "No JMX files were found to validate.", "parent": self.parent}))
                return

            for i, file_path in enumerate(files):
                file_name = os.path.basename(file_path)
                self.queue.put((self.status_label.config, {"text": f"Processing: {file_name} ({i + 1}/{total_files})"}))
                self.queue.put((self._log_message, [f"\n--- Processing JMX file: {file_name} ---"]))
                jmx_file_directory = os.path.dirname(file_path)
                current_file_output_dir = os.path.join(jmx_file_directory, "JMeter_Validation_Reports")

                if not os.path.exists(current_file_output_dir):
                    os.makedirs(current_file_output_dir)

                root_element = None
                all_issues_for_current_file = []

                try:
                    self.queue.put((self._log_message, ["Parsing JMX file..."]))
                    tree = ET.parse(file_path)
                    root_element = tree.getroot()
                    self.queue.put((self._log_message, ["Parsing successful."]))
                except ET.ParseError as e:
                    error_msg = f"Failed to parse JMX file: {e}. Ensure it's a valid XML."
                    self.queue.put((self._log_message, [error_msg]))
                    all_issues_for_current_file.append({'severity': 'ERROR', 'validation_option_name': "JMX File Parsing", 'type': 'XML Parsing', 'location': 'JMX File', 'description': error_msg, 'thread_group': 'N/A'})
                except FileNotFoundError:
                    error_msg = f"JMX file not found at: {file_path}"
                    self.queue.put((self._log_message, [error_msg]))
                    all_issues_for_current_file.append({'severity': 'ERROR', 'validation_option_name': "JMX File Parsing", 'type': 'File Not Found', 'location': 'JMX File', 'description': error_msg, 'thread_group': 'N/A'})

                if root_element is not None:
                    validation_modules = {
                        TXN_VALIDATION_OPTION_NAME: analyze_txn_naming_script,
                        KPI_VALIDATION_OPTION_NAME: analyze_kpi_naming_script,
                        SERVER_HYGIENE_VALIDATION_OPTION_NAME: analyze_server_hygiene_script,
                        EXTRACTOR_STANDARDS_VALIDATION_OPTION_NAME: analyze_extractor_standards_script,
                        VARIABLE_NAMING_CONVENTION_OPTION_NAME: analyze_variable_standards,
                        HARDCODED_VALUE_DETECTION_OPTION_NAME: analyze_hardcoded_value_detection,
                        UNUSED_EXTRACTOR_AND_VARIABLE_DETECTION_OPTION_NAME: analyze_unused_extractor_and_variable_detection,
                    }

                    for option_name, analyze_func in validation_modules.items():
                        if option_name in validations:
                            self.queue.put((self.status_label.config, {"text": f"Processing {file_name}: Validating {option_name}..."}))

                            issues = []
                            debug_log = []
                            if option_name == UNUSED_EXTRACTOR_AND_VARIABLE_DETECTION_OPTION_NAME:
                                issues, debug_log = analyze_func(root_element, validations)
                            else:
                                issues = analyze_func(root_element, validations)

                            for msg in debug_log:
                                self.queue.put((self._log_message, [msg]))

                            if issues is not None:
                                all_issues_for_current_file.extend(issues)
                            else:
                                self.queue.put((self._log_message, [f"ERROR: {option_name} returned None. This is an internal module error."]))
                                all_issues_for_current_file.append({'severity': 'ERROR', 'validation_option_name': option_name, 'type': 'Internal Module Error', 'location': 'JMeter Script Analysis', 'description': f"The '{option_name}' validation module returned None instead of a list of issues. Please check its implementation.", 'thread_group': 'N/A'})

                report_data = {"file_path": file_path, "issues": all_issues_for_current_file}
                report_html_path = os.path.join(current_file_output_dir, f"{os.path.splitext(file_name)[0]}_validation_report.html")
                generate_html_report(report_data, report_html_path, validations)
                self.reports_generated_paths.append(report_html_path)

                progress_value = ((i + 1) / total_files) * 100
                self.queue.put((self.progress_bar.config, {"value": progress_value}))
                self.queue.put((self.status_label.config, {"text": f"Report generated for {file_name}."}))

            self.queue.put((self.status_label.config, {"text": "Report generation complete!"}))
            self.queue.put((self.report_label.config, {"text": "Reports Generated Successfully!"}))
            self.queue.put((self.open_report_button.config, {"state": ttk.NORMAL}))
            self.queue.put((self._log_message, ["All reports have been generated."]))

            if self.reports_generated_paths:
                first_report_example_dir = os.path.dirname(self.reports_generated_paths[0])
                self.queue.put((messagebox.showinfo, {"title": "Reports Generated", "message": f"Validation reports have been generated in 'JMeter_Validation_Reports' subfolders located alongside each JMX file (e.g., in '{first_report_example_dir}').", "parent": self.parent}))
            else:
                self.queue.put((messagebox.showwarning, {"title": "No Reports", "message": "No reports were generated due to errors or no files selected.", "parent": self.parent}))
        except Exception as e:
            self.queue.put((self.status_label.config, {"text": f"An unexpected error occurred: {e}", "bootstyle": "danger"}))
            self.queue.put((self.report_label.config, {"text": "Report Generation Failed!", "bootstyle": "danger"}))
            self.queue.put((messagebox.showerror, {"title": "Error", "message": f"An unexpected error occurred during report generation: {e}.", "parent": self.parent}))
        finally:
            self.queue.put((self.progress_bar.config, {"value": 100}))
            self.queue.put((self._log_message, ["--- Report Generation Finished ---"]))

    def open_reports_folder(self):
        if self.reports_generated_paths:
            last_report_path = self.reports_generated_paths[-1]
            report_folder_to_open = os.path.dirname(last_report_path)

            if os.path.exists(report_folder_to_open):
                webbrowser.open(os.path.abspath(report_folder_to_open))
            else:
                messagebox.showwarning("Folder Not Found", f"The report folder for the last JMX file does not exist: '{report_folder_to_open}'.", parent=self.parent)
        else:
            messagebox.showwarning("No Reports", "No reports have been generated yet to open a folder.", parent=self.parent)