# script_validator/validator_report_page.py
import ttkbootstrap as ttk
from tkinter import messagebox
import os
import threading
import webbrowser
# Removed: import sys (not strictly needed if base_script_dir is removed or not used for output_dir)

# Import core validation logic
from jmeter_methods.Val_Backend_TXN_Naming_Convention import parse_jmeter_xml, analyze_jmeter_script, \
    issues as global_issues

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

        # This list will store paths to ALL generated reports (HTML, PDF, etc.)
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

                # --- CHANGE HERE: Determine output directory based on current JMX file's location ---
                jmx_file_directory = os.path.dirname(file_path)
                current_file_output_dir = os.path.join(jmx_file_directory, "JMeter_Validation_Reports")

                # Ensure the report directory exists for this specific JMX file's location
                if not os.path.exists(current_file_output_dir):
                    os.makedirs(current_file_output_dir)
                # -----------------------------------------------------------------------------------

                global_issues.clear()  # Clear issues for the new file

                root_element = parse_jmeter_xml(file_path)

                if root_element is None:
                    # An error was already logged in parse_jmeter_xml if parsing failed
                    self.status_label.config(
                        text=f"Skipped {file_name}: Failed to parse JMX. See error log for details.")
                    progress_value = ((i + 1) / total_files) * 100
                    self.progress_bar["value"] = progress_value
                    self.update_idletasks()
                    continue

                analyze_jmeter_script(root_element, validations)  # This will populate global_issues

                report_data = {
                    "file_path": file_path,
                    "issues": list(global_issues)  # Take a copy of current issues
                }

                # Generate HTML report in the determined current_file_output_dir
                report_html_path = os.path.join(current_file_output_dir,
                                                f"{os.path.splitext(file_name)[0]}_validation_report.html")
                generate_html_report(report_data, report_html_path, validations)
                self.reports_generated_paths.append(report_html_path)  # Add to list for potential opening later

                # --- You can uncomment PDF/Excel generation here if needed,
                # --- ensuring output_path uses current_file_output_dir similarly.
                # report_pdf_path = os.path.join(current_file_output_dir, f"{os.path.splitext(file_name)[0]}_validation_report.pdf")
                # generate_pdf_report(report_data, report_pdf_path, validations)
                # self.reports_generated_paths.append(report_pdf_path)

                # report_excel_path = os.path.join(current_file_output_dir, f"{os.path.splitext(file_name)[0]}_validation_report.xlsx")
                # generate_excel_report(report_data, report_excel_path, validations)
                # self.reports_generated_paths.append(report_excel_path)

                progress_value = ((i + 1) / total_files) * 100
                self.progress_bar["value"] = progress_value
                self.update_idletasks()

            self.status_label.config(text="Report generation complete!")
            self.report_label.config(text="Reports Generated Successfully!")
            self.open_report_button.config(state=ttk.NORMAL)

            # Inform user where reports are generated. If multiple, pick one example.
            if self.reports_generated_paths:
                first_report_example_dir = os.path.dirname(self.reports_generated_paths[0])
                messagebox.showinfo("Reports Generated",
                                    f"Validation reports have been generated in 'JMeter_Validation_Reports' subfolders located alongside each JMX file (e.g., in '{first_report_example_dir}').",
                                    parent=self.parent)
            else:
                messagebox.showwarning("No Reports", "No reports were generated due to errors or no files selected.",
                                       parent=self.parent)

        except Exception as e:
            self.status_label.config(text=f"An error occurred: {e}", bootstyle="danger")
            self.report_label.config(text="Report Generation Failed!", bootstyle="danger")
            messagebox.showerror("Error", f"An unexpected error occurred during report generation: {e}.",
                                 parent=self.parent)
        finally:
            self.progress_bar["value"] = 100

    def open_reports_folder(self):
        """
        Opens the folder of the *last* generated report, as reports can now be in multiple locations.
        """
        if self.reports_generated_paths:
            # Get the directory of the last generated report file
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