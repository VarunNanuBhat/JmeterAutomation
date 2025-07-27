import xml.etree.ElementTree as ET
import re

THIS_VALIDATION_OPTION_NAME = "Hardcoded Value Detection"

# --- Configuration for Hardcoded Value Detection ---
# Category 1: High-Confidence Hardcoded Values (ERROR)
SENSITIVE_HEADERS = {'Authorization', 'X-API-Key', 'Cookie', 'Set-Cookie'}
# Updated to also detect sensitive keys within raw body data
SENSITIVE_PARAM_NAMES = {'password', 'pwd', 'token', 'access_token', 'refresh_token', 'client_secret', 'api_key'}
SENSITIVE_JSON_KEYS = [f'"{key}"' for key in SENSITIVE_PARAM_NAMES]

# Category 2: General Hardcoded Values (WARNING)
# Minimum length for a string to be considered a potential hardcoded issue.
MIN_STRING_LENGTH = 8

# A regex to define what is "predominantly alphanumeric". This pattern allows
# letters, numbers, and common symbols like underscores, hyphens, and periods,
# which are often found in IDs and tokens. It excludes spaces and complex punctuation.
ALPHA_NUMERIC_PATTERN = r'^[a-zA-Z0-9_\-.]+$'

# A regex to find sequences of digits that are not part of a larger word,
# e.g., to find '123' in `{"id": 123}` but not in `id123abc`.
HARDCODED_NUMBER_PATTERN = r'\b\d+\b'

# A regex to check for any numeric value, including floats (e.g., '123.45').
NUMERIC_PATTERN = r'^\d+(\.\d+)?$'

# Regex patterns for common hardcoded date formats.
HARDCODED_DATE_PATTERNS = [
    r'\b\d{4}-\d{2}-\d{2}\b',  # YYYY-MM-DD
    r'\b\d{4}-\d{2}\b',  # NEW: YYYY-MM
    r'\b\d{2}/\d{2}/\d{4}\b',  # MM/DD/YYYY or DD/MM/YYYY
    r'\b\d{2}-\d{2}-\d{4}\b',  # MM-DD-YYYY or DD-MM-YYYY
    r'\b\d{2}-\d{2}\b'  # MM-YY or DD-MM
]

# A list of specific values to ignore. Add any hardcoded strings here
# that are intentional and should not be flagged.
EXCLUSION_LIST = {
    'GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS', 'PATCH',
    'true', 'false',
    'http', 'https',
    '200', '201', '204', '400', '401', '403', '404', '500',
    'application/json', 'application/xml', 'text/plain', 'text/html',
    'en-US', 'en-GB'  # Example language headers
}


# ---------------------------------------------------


def _add_issue(issues_list, severity, issue_type, location, description, thread_group="N/A", element_name="N/A"):
    """Helper function to add a consistent issue dictionary to the list."""
    issues_list.append({
        'severity': severity,
        'validation_option_name': THIS_VALIDATION_OPTION_NAME,
        'type': issue_type,
        'location': location,
        'description': description,
        'thread_group': thread_group,
        'element_name': element_name
    })


def _get_element_name(element):
    """Helper to safely get the 'testname' attribute of an element."""
    return element.get('testname', 'Unnamed Element')


def _is_jmeter_variable(s):
    """Checks if a string is a JMeter variable reference, e.g., "${my_variable}"."""
    return s and s.strip().startswith('${') and s.strip().endswith('}')


def _is_hardcoded(value):
    """Checks if a string value is hardcoded (not a variable) and not in the exclusion list."""
    if not isinstance(value, str):
        return False
    # Check if it's a variable reference
    if _is_jmeter_variable(value):
        return False
    # Check against the exclusion list
    if value.strip() in EXCLUSION_LIST:
        return False
    # All other non-empty strings are considered hardcoded for this check
    return bool(value.strip())


def _check_general_value(value, element_name, container_context, property_name, issues_list):
    """
    Checks a hardcoded value based on Category 2 criteria.
    - Flags dates and numbers regardless of length.
    - Flags non-numeric, non-date strings > MIN_STRING_LENGTH.
    """
    if not _is_hardcoded(value):
        return

    # NEW RULE: Check for dates
    for pattern in HARDCODED_DATE_PATTERNS:
        if re.search(pattern, value):
            _add_issue(issues_list, 'WARNING', 'Hardcoded Date (Correlation)', element_name,
                       f"The value '{value}' in '{property_name}' contains a hardcoded date. This is a potential correlation value and should be a variable.",
                       container_context, element_name)
            return

    # NEW RULE: Check for numbers regardless of length
    # This check now uses a more flexible regex to find numbers within a string, not just a standalone number.
    if re.search(HARDCODED_NUMBER_PATTERN, value):
        _add_issue(issues_list, 'WARNING', 'Hardcoded Number (Correlation)', element_name,
                   f"The value '{value}' in '{property_name}' contains a hardcoded number. This is a potential correlation value and should be a variable.",
                   container_context, element_name)
        return

    # OLD RULE: Check for non-numeric strings based on length and pattern
    if len(value) > MIN_STRING_LENGTH and re.fullmatch(ALPHA_NUMERIC_PATTERN, value):
        _add_issue(issues_list, 'WARNING', 'Hardcoded String', element_name,
                   f"The value '{value}' in '{property_name}' is a hardcoded string. Consider using a variable for dynamic values.",
                   container_context, element_name)


def _check_raw_body_for_patterns(body_string, element_name, container_context, issues_list):
    """Uses regex to find hardcoded numbers, dates, and sensitive keys within a raw body string."""
    if not _is_hardcoded(body_string):
        return

    # NEW RULE: Check for sensitive JSON keys (Category 1 - ERROR)
    for sensitive_key in SENSITIVE_JSON_KEYS:
        # We need to use re.search here to check for the key within the full body string.
        if re.search(sensitive_key, body_string):
            _add_issue(issues_list, 'ERROR', 'Hardcoded Credential', element_name,
                       f"A hardcoded sensitive key or value for '{sensitive_key}' was found in the raw body data.",
                       container_context, element_name)
            return

    # Check for hardcoded numbers (Category 2 - WARNING)
    found_numbers = re.findall(HARDCODED_NUMBER_PATTERN, body_string)
    if found_numbers:
        unique_numbers = sorted(list(set(found_numbers)))
        for number in unique_numbers:
            _add_issue(issues_list, 'WARNING', 'Hardcoded Number (Correlation)', element_name,
                       f"A hardcoded number '{number}' was found in the raw body data. This is a potential correlation value and should be a variable.",
                       container_context, element_name)

    # Check for hardcoded dates (Category 2 - WARNING)
    for pattern in HARDCODED_DATE_PATTERNS:
        found_dates = re.findall(pattern, body_string)
        if found_dates:
            unique_dates = sorted(list(set(found_dates)))
            for date in unique_dates:
                _add_issue(issues_list, 'WARNING', 'Hardcoded Date (Correlation)', element_name,
                           f"A hardcoded date '{date}' was found in the raw body data. This is a potential correlation value and should be a variable.",
                           container_context, element_name)


def _check_timer_value(element, element_name, container_context, issues_list):
    """Checks for hardcoded values in various timer types, including floats."""
    if element.tag == 'ConstantTimer':
        delay = element.findtext("./stringProp[@name='ConstantTimer.delay']")
        if _is_hardcoded(delay) and re.match(NUMERIC_PATTERN, delay):
            _add_issue(issues_list, 'WARNING', 'Hardcoded Number', element_name,
                       f"The delay '{delay}' in ConstantTimer is hardcoded. Consider using a variable.",
                       container_context, element_name)
    elif element.tag == 'GaussianRandomTimer':
        offset = element.findtext("./stringProp[@name='RandomTimer.offset']")
        range_val = element.findtext("./stringProp[@name='RandomTimer.range']")
        if _is_hardcoded(offset) and re.match(NUMERIC_PATTERN, offset):
            _add_issue(issues_list, 'WARNING', 'Hardcoded Number', element_name,
                       f"The offset '{offset}' in GaussianRandomTimer is hardcoded. Consider using a variable.",
                       container_context, element_name)
        if _is_hardcoded(range_val) and re.match(NUMERIC_PATTERN, range_val):
            _add_issue(issues_list, 'WARNING', 'Hardcoded Number', element_name,
                       f"The range '{range_val}' in GaussianRandomTimer is hardcoded. Consider using a variable.",
                       container_context, element_name)
    elif element.tag == 'UniformRandomTimer':
        range_val = element.findtext("./stringProp[@name='RandomTimer.range']")
        delay = element.findtext("./stringProp[@name='ConstantTimer.delay']")
        if _is_hardcoded(range_val) and re.match(NUMERIC_PATTERN, range_val):
            _add_issue(issues_list, 'WARNING', 'Hardcoded Number', element_name,
                       f"The range '{range_val}' in UniformRandomTimer is hardcoded. Consider using a variable.",
                       container_context, element_name)
        if _is_hardcoded(delay) and re.match(NUMERIC_PATTERN, delay):
            _add_issue(issues_list, 'WARNING', 'Hardcoded Number', element_name,
                       f"The delay '{delay}' in UniformRandomTimer is hardcoded. Consider using a variable.",
                       container_context, element_name)


def analyze_jmeter_script(root_element, enabled_validations):
    """
    Analyzes the JMeter script for hardcoded values based on a hybrid strategy.
    Args:
        root_element (ET.Element): The root element of the JMeter JMX XML.
        enabled_validations (list): A list of validation option names enabled by the user.
    Returns:
        list: A list of dictionaries, each representing an issue found.
    """
    module_issues = []

    if THIS_VALIDATION_OPTION_NAME not in enabled_validations:
        return module_issues

    current_thread_group_context = "Global/Unassigned"

    for element in root_element.iter():
        element_tag = element.tag
        element_name = _get_element_name(element)

        # Update current thread group/context
        if element_tag in ['ThreadGroup', 'SetupThreadGroup', 'PostThreadGroup', 'TestFragment']:
            current_thread_group_context = element_name

        # --- Category 1: High-Confidence Hardcoded Values (ERROR) ---
        # 1. Check AuthManager for hardcoded username/password
        if element_tag == 'AuthManager':
            for auth_entry in element.findall("./collectionProp[@name='AuthManager.auths']/elementProp"):
                username = auth_entry.findtext("./stringProp[@name='Authorization.username']")
                password = auth_entry.findtext("./stringProp[@name='Authorization.password']")
                if _is_hardcoded(username):
                    _add_issue(module_issues, 'ERROR', 'Hardcoded Credential', element_name,
                               f"Hardcoded username '{username}' found in AuthManager.",
                               current_thread_group_context, element_name)
                if _is_hardcoded(password):
                    _add_issue(module_issues, 'ERROR', 'Hardcoded Credential', element_name,
                               f"Hardcoded password found in AuthManager.",
                               current_thread_group_context, element_name)

        # 2. Check HeaderManager for sensitive headers
        if element_tag == 'HeaderManager':
            for header_entry in element.findall("./collectionProp[@name='HeaderManager.headers']/elementProp"):
                header_name = header_entry.findtext("./stringProp[@name='Header.name']")
                header_value = header_entry.findtext("./stringProp[@name='Header.value']")
                if header_name and header_name.strip() in SENSITIVE_HEADERS and _is_hardcoded(header_value):
                    _add_issue(module_issues, 'ERROR', 'Hardcoded Credential/Token', element_name,
                               f"Hardcoded value found for sensitive header '{header_name}'.",
                               current_thread_group_context, element_name)

        # 3. Check HTTP Sampler body for sensitive parameters
        if element_tag == 'HTTPSamplerProxy':
            args_prop = element.find("./elementProp[@name='HTTPsampler.Arguments']")
            if args_prop is not None:
                for arg_entry in args_prop.findall("./collectionProp[@name='Arguments.arguments']/elementProp"):
                    param_name = arg_entry.findtext("./stringProp[@name='Argument.name']")
                    param_value = arg_entry.findtext("./stringProp[@name='Argument.value']")
                    if param_name and param_name.strip() in SENSITIVE_PARAM_NAMES and _is_hardcoded(param_value):
                        _add_issue(module_issues, 'ERROR', 'Hardcoded Credential', element_name,
                                   f"Hardcoded value found for sensitive parameter '{param_name}'.",
                                   current_thread_group_context, element_name)

        # --- Category 2: General Hardcoded Values (WARNING) ---
        # Exclude assertion elements as per user request
        if 'Assertion' in element_tag or element_tag.endswith('Assertion'):
            continue

        # 1. Check HTTP Sampler properties
        if element_tag == 'HTTPSamplerProxy':
            # Check domain and path
            domain = element.findtext("./stringProp[@name='HTTPSampler.domain']")
            path = element.findtext("./stringProp[@name='HTTPSampler.path']")

            _check_general_value(domain, element_name, current_thread_group_context, 'HTTPSampler.domain',
                                 module_issues)
            _check_general_value(path, element_name, current_thread_group_context, 'HTTPSampler.path', module_issues)

            # Check for generic hardcoded values in parameters and raw body
            args_prop = element.find("./elementProp[@name='HTTPsampler.Arguments']")
            if args_prop is not None:
                # Check for raw body data
                if element.findtext("./boolProp[@name='HTTPSampler.postBodyRaw']") == 'true':
                    raw_body = args_prop.findtext("./collectionProp/elementProp/stringProp[@name='Argument.value']")
                    _check_raw_body_for_patterns(raw_body, element_name, current_thread_group_context, module_issues)
                else:  # Check regular URL or form-data parameters
                    for arg_entry in args_prop.findall("./collectionProp[@name='Arguments.arguments']/elementProp"):
                        param_name = arg_entry.findtext("./stringProp[@name='Argument.name']")
                        param_value = arg_entry.findtext("./stringProp[@name='Argument.value']")
                        # Only check if param_name is not a sensitive one
                        if param_name and param_name not in SENSITIVE_PARAM_NAMES:
                            _check_general_value(param_value, element_name, current_thread_group_context,
                                                 f"parameter '{param_name}'", module_issues)

        # 2. Check Timers for hardcoded delays/ranges
        if element_tag in ['ConstantTimer', 'GaussianRandomTimer', 'UniformRandomTimer']:
            _check_timer_value(element, element_name, current_thread_group_context, module_issues)

        # 3. Check Loop Controller for fixed loop counts
        if element_tag == 'LoopController':
            loops = element.findtext("./stringProp[@name='LoopController.loops']")
            if _is_hardcoded(loops) and re.match(NUMERIC_PATTERN, loops) and int(float(loops)) > -1:
                _add_issue(module_issues, 'WARNING', 'Hardcoded Loop Count', element_name,
                           f"Fixed loop count '{loops}' found. Consider using a variable for flexibility.",
                           current_thread_group_context, element_name)

    return module_issues