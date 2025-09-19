import xml.etree.ElementTree as ET
import re

THIS_VALIDATION_OPTION_NAME = "Server Name/Domain Hygiene"

# --- Configuration for environment-specific hostnames ---
# Add or modify patterns here based on your organization's specific environment naming conventions
ENVIRONMENT_HOST_PATTERNS = [ # Corrected variable name
    r'^dev\.',        # Starts with 'dev.' (e.g., dev.myapp.com)
    r'^qa\.',         # Starts with 'qa.' (e.g., qa.test.org)
    r'^uat\.',        # Starts with 'uat.' (e.g., uat.system.net)
    r'\.internal$',   # Ends with '.internal' (e.g., api.internal)
    r'\.local$',      # Ends with '.local' (e.g., myapp.local)
    r'staging',       # Contains 'staging' (e.g., staging-api.example.com)
    r'preprod',       # Contains 'preprod' (e.g., preprod-web.com)
    r'-test\d*$',     # Ends with '-test' or '-test1', '-test2', etc.
    r'test\.org$',    # Ends with 'test.org' (e.g., myapp.test.org)
    r'myapp-prod\d*', # Specific app production instances that might be hardcoded accidentally
    # Add more specific patterns if needed for your environment (e.g., full domains like 'dev.example.com')
]


def is_ipv4(ip_string):
    """
    Checks if a string is a valid IPv4 address.
    """
    pattern = r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    return re.match(pattern, ip_string) is not None

def is_jmeter_variable(s):
    """
    Checks if a string is a JMeter variable (e.g., ${variableName}).
    """
    # Matches strings that start with ${ and end with } with at least one word character in between.
    return re.match(r'^\$\{\w+\}$', s) is not None

def contains_env_specific_pattern(hostname):
    """
    Checks if a hostname matches any defined environment-specific patterns.
    """
    for pattern in ENVIRONMENT_HOST_PATTERNS: # Corrected from PATTERSE to PATTERNS
        if re.search(pattern, hostname, re.IGNORECASE): # Ignore case for hostnames
            return True
    return False

def analyze_jmeter_script(root_element, selected_validations_list):
    module_issues = []

    if THIS_VALIDATION_OPTION_NAME not in selected_validations_list:
        return []

    # Standard boilerplate to find the main hashTree and TestPlan
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

    # Iterate through Thread Groups and Test Fragments
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
                # Iterate through all elements within the Thread Group/Test Fragment to find HTTP Requests
                for element in tg_children_hashtree.iter():
                    if element.tag == 'HTTPSamplerProxy':
                        http_request_name = element.get('testname') or "Unnamed HTTP Request"

                        # Get the domain (Server Name or IP)
                        domain_elem = element.find(".//stringProp[@name='HTTPSampler.domain']")
                        server_name = domain_elem.text.strip() if domain_elem is not None and domain_elem.text else ''

                        # Skip checks if server_name is empty (often means inherited from config elements, which is fine)
                        if not server_name:
                            continue

                        # --- NEW Rule: Server Name format (ERROR) ---
                        # Check if the server_name contains path separators, query parameters, or fragments.
                        if '/' in server_name or '?' in server_name or '#' in server_name:
                            module_issues.append({
                                'severity': 'ERROR',
                                'validation_option_name': THIS_VALIDATION_OPTION_NAME,
                                'type': 'Malformed Server Name',
                                'location': f"HTTP Request '{http_request_name}'",
                                'description': f"Server Name/IP '{server_name}' contains path segments, query parameters, or URL fragments. These should be in the 'Path' field, not the 'Server Name or IP' field. Expected format: 'domain.com', 'sub.domain.com', or an IP address (e.g., 192.168.1.1).",
                                'thread_group': current_tg_name
                            })
                            continue # Stop further checks for this server_name as it's fundamentally malformed.

                        # --- Rule 1: Hardcoded IP Addresses (WARNING) ---
                        if is_ipv4(server_name):
                            module_issues.append({
                                'severity': 'WARNING',
                                'validation_option_name': THIS_VALIDATION_OPTION_NAME,
                                'type': 'Hardcoded IP Address',
                                'location': f"HTTP Request '{http_request_name}'",
                                'description': f"Server Name/IP '{server_name}' is a hardcoded IP address. It should ideally be replaced with a parameterized hostname (e.g., '${{HOSTNAME}}') for flexibility.",
                                'thread_group': current_tg_name
                            })
                        # --- Rule 2: Hardcoded Environment-Specific Hostnames/Domains (ERROR) ---
                        elif contains_env_specific_pattern(server_name):
                            module_issues.append({
                                'severity': 'ERROR',
                                'validation_option_name': THIS_VALIDATION_OPTION_NAME,
                                'type': 'Hardcoded Environment Hostname',
                                'location': f"HTTP Request '{http_request_name}'",
                                'description': f"Server Name/IP '{server_name}' appears to be a hardcoded environment-specific hostname. It **must** be parameterized (e.g., '${{HOSTNAME}}' or '${{BASE_URL}}') to ensure environment independence.",
                                'thread_group': current_tg_name
                            })
                        # --- Rule 3: Server Name must be parameterized (WARNING) ---
                        elif not is_jmeter_variable(server_name):
                            module_issues.append({
                                'severity': 'WARNING',
                                'validation_option_name': THIS_VALIDATION_OPTION_NAME,
                                'type': 'Hardcoded Server Hostname',
                                'location': f"HTTP Request '{http_request_name}'",
                                'description': f"Server Name/IP '{server_name}' is a hardcoded hostname. It should be parameterized (e.g., '${{baseURL}}' or '${{HOSTNAME}}') to ensure environment independence and easier management.",
                                'thread_group': current_tg_name
                            })
                idx += 1 # Advance past the hashTree
            else:
                pass # No hashTree for Thread Group, skip
        else:
            # If not a Thread Group/Test Fragment, check if it has a hashTree to skip it
            if idx + 1 < len(children_of_top_level_controllers_hashtree) and children_of_top_level_controllers_hashtree[idx + 1].tag == 'hashTree':
                idx += 1 # Advance past the hashTree
        idx += 1
    return module_issues, []


# --- Self-testing / Main block for local execution (Optional, for development) ---
if __name__ == "__main__":
    # Define the path to your JMX file for local testing
    # IMPORTANT: Replace with a real path to a JMX file that has HTTP Requests
    # including ones with IPs, environment-specific hostnames, and generic hardcoded hostnames for testing.
    jmx_file_to_test = r"D:\Projects\Python\JmeterAutomation\Sample_Script.jmx" # <--- UPDATE THIS PATH

    print(f"--- Running Server Name/Domain Hygiene Validation for: {jmx_file_to_test} ---")

    selected_validations = [THIS_VALIDATION_OPTION_NAME]

    root_element = None
    parsing_issues = []

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
    all_validation_issues.extend(parsing_issues)

    if root_element is not None:
        print(f"Applying validation: '{THIS_VALIDATION_OPTION_NAME}'...")
        hygiene_issues = analyze_jmeter_script(root_element, selected_validations)
        all_validation_issues.extend(hygiene_issues)
        print("Validation complete.")
    else:
        print("Skipping validation due to JMX parsing errors.")

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