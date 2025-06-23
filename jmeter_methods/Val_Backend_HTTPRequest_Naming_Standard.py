import xml.etree.ElementTree as ET
import re

THIS_VALIDATION_OPTION_NAME = "HTTP Request Naming (KPI_method_urlPath)"


def clean_url_path_for_naming(raw_path):
    """
    Cleans the raw URL path for use in naming conventions.
    Replaces JMeter variables/functions and standardizes slashes.
    """
    cleaned_path = raw_path.strip()

    # Replace JMeter variables like ${userID} with <VAR_NAME>
    # Capture the variable name itself for better readability in the cleaned path
    # Example: /users/${userID} -> /users/<userID>
    cleaned_path = re.sub(r'\$\{(\w+)\}', r'<\1>', cleaned_path)

    # Replace JMeter functions like __Random(1,100,)__ with <FUNC_NAME>
    # Capture the function name itself
    # Example: /data/${__time(YMD)} -> /data/<time>
    cleaned_path = re.sub(r'__(\w+)\(.*?\)', r'<\1>', cleaned_path)

    # Further clean common path issues
    if cleaned_path.startswith('/'):
        cleaned_path = cleaned_path[1:]
    if '?' in cleaned_path:
        cleaned_path = cleaned_path.split('?')[0]
    if '#' in cleaned_path:
        cleaned_path = cleaned_path.split('#')[0]
    if cleaned_path.endswith('/'):
        cleaned_path = cleaned_path.rstrip('/')

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
            if idx + 1 < len(children_of_top_level_controllers_hashtree) and children_of_top_level_controllers_hashtree[
                idx + 1].tag == 'hashTree':
                tg_children_hashtree = children_of_top_level_controllers_hashtree[idx + 1]

            if tg_children_hashtree is not None:
                for element in tg_children_hashtree.iter():
                    if element.tag == 'HTTPSamplerProxy':
                        http_request_name = element.get('testname')
                        method_elem = element.find(".//stringProp[@name='HTTPSampler.method']")
                        http_method = method_elem.text.strip().upper() if method_elem is not None and method_elem.text else 'UNKNOWN_METHOD'
                        path_elem = element.find(".//stringProp[@name='HTTPSampler.path']")
                        raw_http_path = path_elem.text.strip() if path_elem is not None and path_elem.text else 'UNKNOWN_PATH'

                        # Check if raw path contained variables/functions
                        contains_correlation_pattern = bool(
                            re.search(r'\$\{(\w+)\}', raw_http_path) or
                            re.search(r'__\w+\(.*?\)', raw_http_path)
                        )

                        # Cleaned path for the expected name calculation
                        http_path_for_name = clean_url_path_for_naming(raw_http_path)
                        expected_name = f"KPI_{http_method}_{http_path_for_name}"

                        if http_request_name:
                            # Rule 1: Check for KPI_method_urlPath format
                            if http_request_name != expected_name:
                                module_issues.append({
                                    'severity': 'ERROR',
                                    'validation_option_name': THIS_VALIDATION_OPTION_NAME,
                                    'type': 'HTTP Request Naming Format',
                                    'location': f"HTTP Request '{http_request_name}'",
                                    'description': f"HTTP Request name '{http_request_name}' does not follow 'KPI_method_urlPath' format. Expected: '{expected_name}'. Ensure correct method, and a cleaned URL path (no leading/trailing slashes, query params, or fragments). Consider variable standardization for path consistency.",
                                    'thread_group': current_tg_name
                                })

                            # Rule 2: Check for correlation patterns in the *actual* http_request_name
                            if contains_correlation_pattern and (
                                    re.search(r'\$\{\w+\}', http_request_name) or
                                    re.search(r'__\w+\(.*?\)', http_request_name)
                            ):
                                module_issues.append({
                                    'severity': 'ERROR',
                                    'validation_option_name': THIS_VALIDATION_OPTION_NAME,
                                    'type': 'URL Path Correlation in Name',
                                    'location': f"HTTP Request '{http_request_name}'",
                                    'description': f"HTTP Request name '{http_request_name}' contains uncleaned correlation patterns (e.g., '${{var}}' or '__func()__') in its URL path portion. For clarity and aggregation in reports, correlated parts of the URL path **must** be generalized to '<variableName>' (e.g., '/users/${{userID}}' should become 'KPI_GET_users_<userID>'). Expected cleaned format: '{http_path_for_name}'.",
                                    'thread_group': current_tg_name
                                })

                        else:
                            # If no name, issue error for missing name AND provide expected name with cleaned path
                            module_issues.append({
                                'severity': 'ERROR',
                                'validation_option_name': THIS_VALIDATION_OPTION_NAME,
                                'type': 'Missing HTTP Request Name',
                                'location': f"Unnamed HTTP Request (Method: {http_method}, Path: {raw_http_path})",
                                'description': f"HTTP Request has no name. It must follow 'KPI_method_urlPath' format. Expected: '{expected_name}'. Ensure correct method, and a cleaned URL path (no leading/trailing slashes, query params, or fragments). Consider variable standardization for path consistency.",
                                'thread_group': current_tg_name
                            })
                idx += 1
            else:
                pass  # No hashTree for Thread Group, skip
        else:
            # Handle other top-level elements that might have their own hashTrees but aren't Thread Groups
            if idx + 1 < len(children_of_top_level_controllers_hashtree) and children_of_top_level_controllers_hashtree[
                idx + 1].tag == 'hashTree':
                idx += 1  # Advance past the hashTree
        idx += 1
    return module_issues