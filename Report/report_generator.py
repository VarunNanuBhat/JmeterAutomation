# report_generator.py
import os
from datetime import datetime
from collections import defaultdict

# For HTML report generation
from jinja2 import Environment, FileSystemLoader

def _group_issues_by_thread_group(issues_list):
    """Helper to group issues by thread_group for organized reporting."""
    issues_by_thread_group = {}
    for issue in issues_list:
        tg_name = issue.get('thread_group', 'N/A')
        if tg_name not in issues_by_thread_group:
            issues_by_thread_group[tg_name] = []
        issues_by_thread_group[tg_name].append(issue)
    return issues_by_thread_group

def _group_issues_by_validation_option(issues_list):
    """Helper to group issues by validation_option_name."""
    issues_by_validation = defaultdict(list)
    for issue in issues_list:
        # Get the validation_option_name, default to 'Uncategorized Issues' if not found
        validation_name = issue.get('validation_option_name', 'Uncategorized Issues')
        issues_by_validation[validation_name].append(issue)
    return issues_by_validation

def generate_html_report(report_data, output_path, selected_validations):
    """
    Generates an HTML report from the collected issues.
    `report_data` is a dict with 'file_path' and 'issues' (list of dicts).
    `output_path` is the full path where the HTML file should be saved.
    `selected_validations` is a list of strings of the validations that were run.
    """
    # Assuming the template file 'report_template.html' is in the same directory as report_generator.py
    env = Environment(loader=FileSystemLoader(os.path.dirname(__file__)))
    template = env.get_template('report_template.html')

    file_name = os.path.basename(report_data['file_path'])
    total_issues = len(report_data['issues'])

    issues_by_validation_option = _group_issues_by_validation_option(report_data['issues'])

    html_content = template.render(
        file_name=file_name,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        selected_validations=selected_validations,
        issues_by_validation_option=issues_by_validation_option,
        _group_issues_by_thread_group=_group_issues_by_thread_group, # Pass helper to template if needed
        total_issues=total_issues
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)