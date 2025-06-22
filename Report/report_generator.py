# script_validator/report_generator.py
import os
from datetime import datetime

# For HTML report generation
from jinja2 import Environment, FileSystemLoader  # Make sure you have 'pip install Jinja2'

# For PDF generation (Optional: Requires wkhtmltopdf installed and in PATH, and `pdfkit` Python library)
# pip install pdfkit
# import pdfkit

# For Excel generation (Optional: Requires openpyxl)
# pip install openpyxl
import openpyxl
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter


def _group_issues_by_thread_group(issues_list):
    """Helper to group issues by thread_group for organized reporting."""
    issues_by_thread_group = {}
    for issue in issues_list:
        tg_name = issue.get('thread_group', 'N/A')
        if tg_name not in issues_by_thread_group:
            issues_by_thread_group[tg_name] = []
        issues_by_thread_group[tg_name].append(issue)
    return issues_by_thread_group


def generate_html_report(report_data, output_path, selected_validations):
    """
    Generates an HTML report from the collected issues.
    `report_data` is a dict with 'file_path' and 'issues' (list of dicts).
    `output_path` is the full path where the HTML file should be saved.
    `selected_validations` is a list of strings of the validations that were run.
    """
    # Configure Jinja2 to look for templates in the same directory as this script
    env = Environment(loader=FileSystemLoader(os.path.dirname(__file__)))
    template = env.get_template('report_template.html')  # This is the HTML template file

    file_name = os.path.basename(report_data['file_path'])
    issues_by_tg = _group_issues_by_thread_group(report_data['issues'])
    total_issues = len(report_data['issues'])

    # Render the template with the provided data
    html_content = template.render(
        file_name=file_name,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        selected_validations=selected_validations,
        issues_by_tg=issues_by_tg,
        total_issues=total_issues
    )

    # Write the generated HTML to the output file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    # print(f"Generated HTML report: {output_path}")




