# jmeter_methods/Val_Backend_HTTPRequest_Naming_Standard.py
import xml.etree.ElementTree as ET
import re

# Global list to store issues for this validation module
issues = []

# Define the specific validation option name this module is responsible for
THIS_VALIDATION_OPTION_NAME = "HTTP Request Naming (KPI_method_urlPath)"


def analyze_jmeter_script(root_element, selected_validations_list):
    """
    Analyzes the JMeter script to validate HTTP Request naming standards.
    Ensures every HTTP Request name strictly follows 'KPI_method_urlPath' format,
    with simplified URL path cleaning.
    """
    global issues
    issues = []  # Reset issues for this module on each run

    # If this validation is not selected, clear any issues and return.
    if THIS_VALIDATION_OPTION_NAME not in selected_validations_list:
        return

    # --- Start JMeter Tree Traversal Setup ---
    # First, find the main hashTree under jmeterTestPlan (where Thread Groups and Test Fragments reside)
    jmeter_test_plan_direct_hashtree = root_element.find('hashTree')
    if jmeter_test_plan_direct_hashtree is None:
        issues.append({
            'severity': 'ERROR',
            'validation_option_name': THIS_VALIDATION_OPTION_NAME,
            'type': 'Structure',
            'location': 'JMeter Test Plan',
            'description': "Root 'jmeterTestPlan' has no child 'hashTree'. Invalid JMX structure.",
            'thread_group': 'N/A'
        })
        return

    # Find the TestPlan element and its immediate hashTree child (which contains top-level controllers like Thread Groups)
    top_level_controllers_hashtree = None
    children_of_jmeter_test_plan_direct_hashtree = list(jmeter_test_plan_direct_hashtree)
    for i, elem in enumerate(children_of_jmeter_test_plan_direct_hashtree):
        if elem.tag == 'TestPlan':
            if i + 1 < len(children_of_jmeter_test_plan_direct_hashtree) and \
                    children_of_jmeter_test_plan_direct_hashtree[i + 1].tag == 'hashTree':
                top_level_controllers_hashtree = children_of_jmeter_test_plan_direct_hashtree[i + 1]
                break

    if top_level_controllers_hashtree is None:
        issues.append({
            'severity': 'ERROR',
            'validation_option_name': THIS_VALIDATION_OPTION_NAME,
            'type': 'Structure',
            'location': 'JMeter Test Plan',
            'description': "Could not locate the primary hashTree containing Thread Groups or Test Fragments. JMX structure might be unexpected.",
            'thread_group': 'N/A'
        })
        return

    # --- Traverse Thread Groups/Test Fragments and their descendants ---
    children_of_top_level_controllers_hashtree = list(top_level_controllers_hashtree)
    idx = 0
    while idx < len(children_of_top_level_controllers_hashtree):
        top_level_elem = children_of_top_level_controllers_hashtree[idx]

        # Check if the current top-level element is a Thread Group or Test Fragment (these define the 'thread_group' context)
        if top_level_elem.tag in ['ThreadGroup', 'SetupThreadGroup', 'PostThreadGroup', 'TestFragmentController']:
            # Get the name of the current Thread Group/Test Fragment for reporting
            current_tg_name = top_level_elem.get('testname') or f"Unnamed {top_level_elem.tag}"

            # Find the hashTree directly after this controller, which contains its children
            tg_children_hashtree = None
            if idx + 1 < len(children_of_top_level_controllers_hashtree) and children_of_top_level_controllers_hashtree[
                idx + 1].tag == 'hashTree':
                tg_children_hashtree = children_of_top_level_controllers_hashtree[idx + 1]

            if tg_children_hashtree is not None:
                # Iterate through all descendants within this Thread Group's/Test Fragment's hashTree
                for element in tg_children_hashtree.iter():
                    if element.tag == 'HTTPSamplerProxy':  # Found an HTTP Request sampler
                        http_request_name = element.get('testname')

                        # Get HTTP method from <stringProp name="HTTPSampler.method">
                        method_elem = element.find(".//stringProp[@name='HTTPSampler.method']")
                        http_method = method_elem.text.strip().upper() if method_elem is not None and method_elem.text else 'UNKNOWN_METHOD'

                        # Get URL path from <stringProp name="HTTPSampler.path">
                        path_elem = element.find(".//stringProp[@name='HTTPSampler.path']")
                        raw_http_path = path_elem.text.strip() if path_elem is not None and path_elem.text else 'UNKNOWN_PATH'

                        # --- Simplified URL Path Cleaning ---
                        http_path_for_name = raw_http_path
                        # 1. Remove leading slash if present
                        if http_path_for_name.startswith('/'):
                            http_path_for_name = http_path_for_name[1:]
                        # 2. Remove query parameters (anything after '?')
                        if '?' in http_path_for_name:
                            http_path_for_name = http_path_for_name.split('?')[0]
                        # --- End Simplified URL Path Cleaning ---

                        # Construct the expected name based on the specified format
                        # Note: The expected name will now contain slashes, dots, hyphens etc., if they were in the original path
                        expected_name = f"KPI_{http_method}_{http_path_for_name}"

                        if http_request_name:  # If the HTTP Request has a name
                            if http_request_name != expected_name:
                                issues.append({
                                    'severity': 'ERROR',  # Set to ERROR as this is a strict format requirement
                                    'validation_option_name': THIS_VALIDATION_OPTION_NAME,
                                    'type': 'HTTP Request Naming',
                                    'location': f"HTTP Request '{http_request_name}'",
                                    'description': f"HTTP Request name '{http_request_name}' does not follow 'KPI_method_urlPath' format. Expected: '{expected_name}'.",
                                    'thread_group': current_tg_name
                                })
                        else:  # If the HTTP Request has no name
                            issues.append({
                                'severity': 'ERROR',
                                'validation_option_name': THIS_VALIDATION_OPTION_NAME,
                                'type': 'HTTP Request Naming',
                                'location': f"Unnamed HTTP Request (Method: {http_method}, Path: {raw_http_path})",
                                'description': f"HTTP Request has no name. It must follow 'KPI_method_urlPath' format. Expected: '{expected_name}'.",
                                'thread_group': current_tg_name
                            })
                idx += 1  # Advance past the hashTree if it was processed
        idx += 1  # Always advance to the next top-level element