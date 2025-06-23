import xml.etree.ElementTree as ET
import re
import os # Import os for path checking

THIS_VALIDATION_OPTION_NAME = "HTTP Request Naming (KPI_method_urlPath)"

def clean_url_path_for_naming(raw_path):
    cleaned_path = raw_path.strip()
    if cleaned_path.startswith('/'):
        cleaned_path = cleaned_path[1:]
    if '?' in cleaned_path:
        cleaned_path = cleaned_path.split('?')[0]
    if '#' in cleaned_path:
        cleaned_path = cleaned_path.split('#')[0]
    if cleaned_path.endswith('/'):
        cleaned_path = cleaned_path.rstrip('/')
    cleaned_path = re.sub(r'\$\{.*?\}', '_VAR_', cleaned_path)
    cleaned_path = re.sub(r'__\w+\(.*?\)__', '_FUNC_', cleaned_path)
    return cleaned_path

def analyze_jmeter_script(root_element, selected_validations_list):
    module_issues = []

    if THIS_VALIDATION_OPTION_NAME not in selected_validations_list:
        return []

    jmeter_test_plan_direct_hashtree = root_element.find('hashTree')
    if jmeter_test_plan_direct_hashtree is None:
        module_issues.append({
            'severity': 'ERROR',
            'validation_option_name': THIS_VALIDATION_OPTION_NAME,
            'type': 'Structure',
            'location': 'JMeter Test Plan',
            'description': "Root 'jmeterTestPlan' has no child 'hashTree'. Invalid JMX structure.",
            'thread_group': 'N/A'
        })
        return module_issues

    top_level_controllers_hashtree = None
    children_of_jmeter_test_plan_direct_hashtree = list(jmeter_test_plan_direct_hashtree)
    for i, elem in enumerate(children_of_jmeter_test_plan_direct_hashtree):
        if elem.tag == 'TestPlan':
            if i + 1 < len(children_of_jmeter_test_plan_direct_hashtree) and \
                    children_of_jmeter_test_plan_direct_hashtree[i + 1].tag == 'hashTree':
                top_level_controllers_hashtree = children_of_jmeter_test_plan_direct_hashtree[i + 1]
                break

    if top_level_controllers_hashtree is None:
        module_issues.append({
            'severity': 'ERROR',
            'validation_option_name': THIS_VALIDATION_OPTION_NAME,
            'type': 'Structure',
            'location': 'JMeter Test Plan',
            'description': "Could not locate the primary hashTree containing Thread Groups or Test Fragments. JMX structure might be unexpected.",
            'thread_group': 'N/A'
        })
        return module_issues

    children_of_top_level_controllers_hashtree = list(top_level_controllers_hashtree)
    idx = 0
    while idx < len(children_of_top_level_controllers_hashtree):
        top_level_elem = children_of_top_level_controllers_hashtree[idx]

        if top_level_elem.tag in ['ThreadGroup', 'SetupThreadGroup', 'PostThreadGroup', 'TestFragmentController']:
            current_tg_name = top_level_elem.get('testname') or f"Unnamed {top_level_elem.tag}"

            tg_children_hashtree = None
            if idx + 1 < len(children_of_top_level_controllers_hashtree) and children_of_top_level_controllers_hashtree[idx + 1].tag == 'hashTree':
                tg_children_hashtree = children_of_top_level_controllers_hashtree[idx + 1]

            if tg_children_hashtree is not None:
                for element in tg_children_hashtree.iter():
                    if element.tag == 'HTTPSamplerProxy':
                        http_request_name = element.get('testname')
                        method_elem = element.find(".//stringProp[@name='HTTPSampler.method']")
                        http_method = method_elem.text.strip().upper() if method_elem is not None and method_elem.text else 'UNKNOWN_METHOD'
                        path_elem = element.find(".//stringProp[@name='HTTPSampler.path']")
                        raw_http_path = path_elem.text.strip() if path_elem is not None and path_elem.text else 'UNKNOWN_PATH'

                        http_path_for_name = clean_url_path_for_naming(raw_http_path)
                        expected_name = f"KPI_{http_method}_{http_path_for_name}"

                        if http_request_name:
                            if http_request_name != expected_name:
                                module_issues.append({
                                    'severity': 'ERROR',
                                    'validation_option_name': THIS_VALIDATION_OPTION_NAME,
                                    'type': 'HTTP Request Naming',
                                    'location': f"HTTP Request '{http_request_name}'",
                                    'description': f"HTTP Request name '{http_request_name}' does not follow 'KPI_method_urlPath' format. Expected: '{expected_name}'. Ensure correct method, and a cleaned URL path (no leading/trailing slashes, query params, or fragments). Consider variable standardization for path consistency.",
                                    'thread_group': current_tg_name
                                })
                        else:
                            module_issues.append({
                                'severity': 'ERROR',
                                'validation_option_name': THIS_VALIDATION_OPTION_NAME,
                                'type': 'HTTP Request Naming',
                                'location': f"Unnamed HTTP Request (Method: {http_method}, Path: {raw_http_path})",
                                'description': f"HTTP Request has no name. It must follow 'KPI_method_urlPath' format. Expected: '{expected_name}'. Ensure correct method, and a cleaned URL path (no leading/trailing slashes, query params, or fragments). Consider variable standardization for path consistency.",
                                'thread_group': current_tg_name
                            })
                idx += 1
            else:
                pass
        else:
            if idx + 1 < len(children_of_top_level_controllers_hashtree) and children_of_top_level_controllers_hashtree[idx + 1].tag == 'hashTree':
                idx += 1
        idx += 1
    return module_issues

# --- Self-testing / Main block for local execution ---
if __name__ == "__main__":
    # Define the path to your JMX file for local testing
    jmx_file_to_test = r"D:\Projects\Python\JmeterAutomation\output.jmx"

    print(f"--- Running KPI Naming Convention Validation for: {jmx_file_to_test} ---")

    # List of validations to enable for this run (just the KPI one for now)
    # THIS_VALIDATION_OPTION_NAME refers to the string defined at the top of this file
    selected_validations = [THIS_VALIDATION_OPTION_NAME]

    root_element = None
    parsing_issues = []

    # Step 1: Parse the JMX file
    try:
        tree = ET.parse(jmx_file_to_test)
        root_element = tree.getroot()
        print("JMX file parsed successfully.")
    except ET.ParseError as e:
        parsing_issues.append({
            'severity': 'ERROR',
            'validation_option_name': "JMX File Parsing",
            'type': 'XML Parsing',
            'location': 'JMX File',
            'description': f"Failed to parse JMX file: {e}. Ensure it's a valid XML.",
            'thread_group': 'N/A'
        })
        print(f"ERROR: Failed to parse JMX file: {e}")
    except FileNotFoundError:
        parsing_issues.append({
            'severity': 'ERROR',
            'validation_option_name': "JMX File Parsing",
            'type': 'File Not Found',
            'location': 'JMX File',
            'description': f"JMX file not found at: {jmx_file_to_test}",
            'thread_group': 'N/A'
        })
        print(f"ERROR: JMX file not found: {jmx_file_to_test}")

    all_validation_issues = []
    all_validation_issues.extend(parsing_issues) # Add any parsing issues first

    # Step 2: Run the validation if parsing was successful
    if root_element is not None:
        print(f"Applying validation: '{THIS_VALIDATION_OPTION_NAME}'...")
        # Call the analyze_jmeter_script function within this same file
        kpi_issues = analyze_jmeter_script(root_element, selected_validations)
        all_validation_issues.extend(kpi_issues)
        print("Validation complete.")
    else:
        print("Skipping validation due to JMX parsing errors.")

    # Step 3: Print the results
    if all_validation_issues:
        print("\n--- Validation Results ---")
        for issue in all_validation_issues:
            print(f"Severity: {issue.get('severity', 'N/A')}")
            print(f"  Validation: {issue.get('validation_option_name', 'N/A')}")
            print(f"  Type: {issue.get('type', 'N/A')}")
            print(f"  Location: {issue.get('location', 'N/A')}")
            print(f"  Description: {issue.get('description', 'N/A')}")
            print(f"  Thread Group: {issue.get('thread_group', 'N/A')}")
            print("-" * 20)
    else:
        print("\n--- Validation Results ---")
        print(f"🥳 No issues found for '{THIS_VALIDATION_OPTION_NAME}' in {jmx_file_to_test}!")

    print(f"\n--- End of Validation for {jmx_file_to_test} ---")