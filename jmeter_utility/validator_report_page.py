# script_validator/validator_report_page.py
import ttkbootstrap as ttk
from tkinter import messagebox
import os
import threading
import webbrowser

# Import core validation logic
from jmeter_methods.Val_Backend_TXN_Naming_Convention import parse_jmeter_xml, analyze_jmeter_script, issues as global_issues

# Import report generation functions
from Report.report_generator import generate_html_report


class ValidatorReportPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=40)
        self.parent = parent

        self.pack(fill="both", expand=True)  # Ensure this frame fills the space

        self.report_label = ttk.Label(self, text="Report Generation Status", font=("Arial", 20, "bold"),
                                      bootstyle="primary")
        self.report_label.pack(pady=20)

        self.progress_bar = ttk.Progressbar(self, orient="horizontal", length=600, mode="determinate", bootstyle="info")
        self.progress_bar.pack(pady=10, padx=50, fill="x")

        self.status_label = ttk.Label(self, text="Awaiting JMX files...", font=("Arial", 12), bootstyle="info")
        self.status_label.pack(pady=5)

        # The button that caused the error
        self.open_report_button = ttk.Button(self, text="Open Report Folder", command=self.open_reports_folder,
                                             state=ttk.DISABLED, bootstyle="success outline")
        self.open_report_button.pack(pady=10)

        back_button = ttk.Button(self, text="Back to Options", bootstyle="secondary",
                                 command=lambda: self.parent.show_page(self.parent.validator_options_page))
        back_button.pack(pady=10)

        self.reports_generated_paths = []  # To store paths of generated reports

    def start_report_generation(self, files, validations):
        # print(f"DEBUG: Starting report generation with files: {files} and validations: {validations}")  # DEBUG
        self.reports_generated_paths = []  # Reset for a new run
        self.report_label.config(text="Report Generation in Progress...")
        self.progress_bar.config(mode="determinate", value=0)
        self.status_label.config(text="Starting validation process...")
        self.open_report_button.config(state=ttk.DISABLED)

        # Run report generation in a separate thread to prevent GUI freeze
        # daemon=True ensures the thread exits when the main application exits
        thread = threading.Thread(target=self._generate_reports_threaded, args=(files, validations), daemon=True)
        thread.start()

    def _generate_reports_threaded(self, files, validations):
        # print("DEBUG: _generate_reports_threaded function started.")  # DEBUG
        total_files = len(files)
        output_dir = "JMeter_Validation_Reports"

        try:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                # print(f"DEBUG: Created output directory: {output_dir}")  # DEBUG
            #else:
                # print(f"DEBUG: Output directory already exists: {output_dir}")  # DEBUG

            if not files:
                # print("DEBUG: No files provided to _generate_reports_threaded.")  # DEBUG
                self.status_label.config(text="No JMX files selected for validation.")
                messagebox.showwarning("No Files", "No JMX files were found to validate.", parent=self.parent)
                return  # Exit if no files

            for i, file_path in enumerate(files):
                # print(f"DEBUG: Processing file {i + 1}/{total_files}: {file_path}")  # DEBUG
                file_name = os.path.basename(file_path)
                self.status_label.config(text=f"Processing: {file_name} ({i + 1}/{total_files})")

                # Clear global issues list for each new file before analysis
                global_issues.clear()
                # print(
                #    f"DEBUG: Global issues cleared for {file_name}. Current issues count: {len(global_issues)}")  # DEBUG

                root_element = parse_jmeter_xml(file_path)

                if root_element is None:
                    # print(f"DEBUG: Failed to parse JMX for {file_name}. Skipping validation.")  # DEBUG
                    # Issues from parse_jmeter_xml would already be in global_issues
                    self.status_label.config(text=f"Skipped {file_name}: Failed to parse JMX. Check logs for details.")
                    # Still update progress even if parsing fails for one file
                    progress_value = ((i + 1) / total_files) * 100
                    self.progress_bar["value"] = progress_value
                    self.update_idletasks()
                    continue  # Move to the next file

                # print(f"DEBUG: Parsing successful for {file_name}. Calling analyze_jmeter_script.")  # DEBUG
                analyze_jmeter_script(root_element)  # This will populate global_issues

                # print(
                #    f"DEBUG: analyze_jmeter_script completed for {file_name}. Issues found: {len(global_issues)}")  # DEBUG

                report_data = {
                    "file_path": file_path,
                    "issues": list(global_issues)  # Take a copy
                }

                # Generate HTML report by default
                report_html_path = os.path.join(output_dir, f"{os.path.splitext(file_name)[0]}_validation_report.html")
                # print(f"DEBUG: Calling generate_html_report for {file_name} at {report_html_path}")  # DEBUG
                generate_html_report(report_data, report_html_path, validations)
                self.reports_generated_paths.append(report_html_path)

                # If you enabled PDF/Excel generation in report_generator.py and want to test:
                # report_pdf_path = os.path.join(output_dir, f"{os.path.splitext(file_name)[0]}_validation_report.pdf")
                # print(f"DEBUG: Calling generate_pdf_report for {file_name} at {report_pdf_path}") # DEBUG
                # generate_pdf_report(report_data, report_pdf_path, validations)
                # self.reports_generated_paths.append(report_pdf_path)

                # report_excel_path = os.path.join(output_dir, f"{os.path.splitext(file_name)[0]}_validation_report.xlsx")
                # print(f"DEBUG: Calling generate_excel_report for {file_name} at {report_excel_path}") # DEBUG
                # generate_excel_report(report_data, report_excel_path, validations)
                # self.reports_generated_paths.append(report_excel_path)

                progress_value = ((i + 1) / total_files) * 100
                self.progress_bar["value"] = progress_value
                self.update_idletasks()  # Update GUI immediately

            self.status_label.config(text="Report generation complete!")
            self.report_label.config(text="Reports Generated Successfully!")
            self.open_report_button.config(state=ttk.NORMAL)
            # print(f"DEBUG: All files processed. Reports generated to: {os.path.abspath(output_dir)}")  # DEBUG
            messagebox.showinfo("Reports Generated",
                                f"Validation reports have been generated in the '{output_dir}' folder.",
                                parent=self.parent)

        except Exception as e:
            # print(f"ERROR: An unexpected error occurred in _generate_reports_threaded: {e}")  # DEBUG
            import traceback
            traceback.print_exc()  # Print full traceback to console
            self.status_label.config(text=f"An error occurred: {e}", bootstyle="danger")
            self.report_label.config(text="Report Generation Failed!", bootstyle="danger")
            messagebox.showerror("Error",
                                 f"An unexpected error occurred during report generation: {e}. Check console for details.",
                                 parent=self.parent)
        finally:
            self.progress_bar["value"] = 100  # Ensure it always finishes at 100%
            # print("DEBUG: _generate_reports_threaded function finished.")  # DEBUG

    # This method MUST be defined as part of the ValidatorReportPage class
    def open_reports_folder(self):
        report_folder = "JMeter_Validation_Reports"
        if os.path.exists(report_folder):
            webbrowser.open(os.path.abspath(report_folder))  # Cross-platform way to open folder
        else:
            messagebox.showwarning("Folder Not Found", f"The report folder '{report_folder}' does not exist.",
                                   parent=self.parent)