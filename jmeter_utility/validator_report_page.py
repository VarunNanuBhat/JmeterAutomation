# script_validator/validator_report_page.py
import ttkbootstrap as ttk
from tkinter import messagebox
import os
import threading
import webbrowser
import xml.etree.ElementTree as ET # Added for local XML parsing in _generate_reports_threaded

# Import core validation logic for TXN Naming
from jmeter_methods.Val_Backend_TXN_Naming_Convention import analyze_jmeter_script as analyze_txn_naming_script, \
    THIS_VALIDATION_OPTION_NAME as TXN_VALIDATION_OPTION_NAME # Renamed for clarity and consistency

# Import core validation logic for KPI Naming
from jmeter_methods.Val_Backend_HTTPRequest_Naming_Standard import analyze_jmeter_script as analyze_kpi_naming_script, \
    THIS_VALIDATION_OPTION_NAME as KPI_VALIDATION_OPTION_NAME # Renamed for clarity and consistency

# Import report generation functions
from Report.report_generator import generate_html_report


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
        self.reports_generated_paths = []  # Reset for each new generation
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
                self.update_idletasks() # Update UI immediately

                jmx_file_directory = os.path.dirname(file_path)
                current_file_output_dir = os.path.join(jmx_file_directory, "JMeter_Validation_Reports")

                if not os.path.exists(current_file_output_dir):
                    os.makedirs(current_file_output_dir)

                root_element = None
                all_issues_for_current_file = [] # This will collect all issues for the current JMX file

                # --- Centralized JMX Parsing ---
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
                    self.status_label.config(text=f"Skipped {file_name}: Failed to parse JMX. Report generated with parsing error.", bootstyle="danger")
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
                    self.status_label.config(text=f"Skipped {file_name}: JMX file not found. Report generated with error.", bootstyle="danger")
                    self.update_idletasks()

                # --- ONLY proceed with validation if root_element was successfully parsed ---
                if root_element is not None:
                    # Execute TXN Naming Convention Validation if selected
                    if TXN_VALIDATION_OPTION_NAME in validations:
                        self.status_label.config(text=f"Processing {file_name}: Validating {TXN_VALIDATION_OPTION_NAME}...", bootstyle="info")
                        self.update_idletasks()
                        txn_issues = analyze_txn_naming_script(root_element, validations)
                        # --- Defensive check for NoneType ---
                        if txn_issues is not None:
                            all_issues_for_current_file.extend(txn_issues)
                        else:
                            print(f"WARNING: {TXN_VALIDATION_OPTION_NAME} in {file_name} returned None. It should return an empty list or issues. Adding internal error issue.")
                            all_issues_for_current_file.append({
                                'severity': 'ERROR',
                                'validation_option_name': TXN_VALIDATION_OPTION_NAME,
                                'type': 'Internal Module Error',
                                'location': 'JMeter Script Analysis',
                                'description': f"The '{TXN_VALIDATION_OPTION_NAME}' validation module returned None instead of a list of issues. Please check its implementation.",
                                'thread_group': 'N/A'
                            })

                    # Execute KPI Naming Standards Validation if selected
                    if KPI_VALIDATION_OPTION_NAME in validations:
                        self.status_label.config(text=f"Processing {file_name}: Validating {KPI_VALIDATION_OPTION_NAME}...", bootstyle="info")
                        self.update_idletasks()
                        kpi_issues = analyze_kpi_naming_script(root_element, validations)
                        # --- Defensive check for NoneType ---
                        if kpi_issues is not None:
                            all_issues_for_current_file.extend(kpi_issues)
                        else:
                            print(f"WARNING: {KPI_VALIDATION_OPTION_NAME} in {file_name} returned None. It should return an empty list or issues. Adding internal error issue.")
                            all_issues_for_current_file.append({
                                'severity': 'ERROR',
                                'validation_option_name': KPI_VALIDATION_OPTION_NAME,
                                'type': 'Internal Module Error',
                                'location': 'JMeter Script Analysis',
                                'description': f"The '{KPI_VALIDATION_OPTION_NAME}' validation module returned None instead of a list of issues. Please check its implementation.",
                                'thread_group': 'N/A'
                            })

                    # Add other validations here following the same pattern
                    # e.g., Server Name (Domain) Hygiene if it's implemented:
                    # if "Server Name (Domain) Hygiene" in validations:
                    #     server_issues = analyze_server_naming_script(root_element, validations)
                    #     if server_issues is not None:
                    #         all_issues_for_current_file.extend(server_issues)
                    #     else:
                    #         # Add an internal error message for this module too
                    #         pass


                report_data = {
                    "file_path": file_path,
                    "issues": all_issues_for_current_file # This will contain parsing error or validation issues
                }

                # Generate HTML report
                report_html_path = os.path.join(current_file_output_dir,
                                                f"{os.path.splitext(file_name)[0]}_validation_report.html")
                generate_html_report(report_data, report_html_path, validations) # Pass all selected validations for the report
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
            self.update_idletasks() # Ensure final UI update

    def open_reports_folder(self):
        """
        Opens the folder of the *last* generated report, as reports can now be in multiple locations.
        """
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