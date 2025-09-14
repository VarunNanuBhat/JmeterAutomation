import xml.etree.ElementTree as ET
import re

THIS_VALIDATION_OPTION_NAME = "Hardcoded Value Detection"

# --- Configuration for Hardcoded Value Detection ---
SENSITIVE_HEADERS = {'Authorization', 'X-API-Key', 'Cookie', 'Set-Cookie'}
SENSITIVE_PARAM_NAMES = {'password', 'pwd', 'token', 'access_token', 'refresh_token', 'client_secret', 'api_key'}
SENSITIVE_JSON_KEYS = [f'"{key}"' for key in SENSITIVE_PARAM_NAMES]
MIN_STRING_LENGTH = 8
ALPHA_NUMERIC_PATTERN = r'^[a-zA-Z0-9_\-.]+$'
HARDCODED_NUMBER_PATTERN = r'\b\d+\b'
NUMERIC_PATTERN = r'^\d+(\.\d+)?$'
HARDCODED_DATE_PATTERNS = [r'\b\d{4}-\d{2}-\d{2}\b', r'\b\d{4}-\d{2}\b', r'\b\d{2}/\d{2}/\d{4}\b', r'\b\d{2}-\d{2}-\d{4}\b', r'\b\d{2}-\d{2}\b']
EXCLUSION_LIST = {'GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS', 'PATCH', 'true', 'false', 'http', 'https', '200', '201', '204', '400', '401', '403', '404', '500', 'application/json', 'application/xml', 'text/plain', 'text/html', 'en-US', 'en-GB'}
HEADER_EXCLUSION_LIST = {'Content-Type', 'Accept', 'Accept-Encoding', 'Accept-Language', 'Cache-Control', 'Connection', 'Content-Length', 'Host', 'Origin', 'Referer', 'Upgrade-Insecure-Requests', 'User-Agent'}
ENVIRONMENT_HOST_PATTERNS = [r'^dev\.', r'^qa\.', r'^uat\.', r'\.internal$', r'\.local$', r'staging', r'preprod', r'-test\d*$', r'test\.org$', r'myapp-prod\d*', ]

def _add_issue(issues_list, severity, issue_type, location, description, thread_group="N/A", element_name="N/A", key_name="", hardcoded_value=""):
    issues_list.append({'severity': severity, 'validation_option_name': THIS_VALIDATION_OPTION_NAME, 'type': issue_type, 'location': location, 'description': description, 'thread_group': thread_group, 'element_name': element_name, 'key_name': key_name, 'hardcoded_value': hardcoded_value})

def _get_element_name(element):
    return element.get('testname', 'Unnamed Element')

def _is_jmeter_variable(s):
    if not isinstance(s, str):
        return False
    return s.strip().startswith('${') and s.strip().endswith('}')

def _is_hardcoded(value):
    if not isinstance(value, str):
        return False
    if _is_jmeter_variable(value):
        return False
    if value.strip() in EXCLUSION_LIST:
        return False
    return bool(value.strip())

def _is_ipv4(ip_string):
    if not isinstance(ip_string, str):
        return False
    pattern = r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    return re.match(pattern, ip_string) is not None

def _contains_env_specific_pattern(hostname):
    if not isinstance(hostname, str):
        return False
    for pattern in ENVIRONMENT_HOST_PATTERNS:
        if re.search(pattern, hostname, re.IGNORECASE):
            return True
    return False

def _get_thread_group_context(element):
    ancestor = element
    while ancestor is not None and ancestor.tag != 'TestPlan':
        if ancestor.tag in ['ThreadGroup', 'SetupThreadGroup', 'PostThreadGroup', 'TestFragmentController']:
            return _get_element_name(ancestor)
        ancestor = ancestor.getparent()
    return "Global/Unassigned"

def _check_general_value(value, element_name, container_context, property_name, issues_list, key_name="", hardcoded_value=""):
    if not _is_hardcoded(value):
        return
    for pattern in HARDCODED_DATE_PATTERNS:
        if re.search(pattern, value):
            _add_issue(issues_list, 'WARNING', 'Hardcoded Date (Correlation)', element_name, f"The value '{value}' in '{property_name}' contains a hardcoded date. This is a potential correlation value and should be a variable.", container_context, element_name, key_name, value)
            return
    if re.search(HARDCODED_NUMBER_PATTERN, value):
        _add_issue(issues_list, 'WARNING', 'Hardcoded Number (Correlation)', element_name, f"The value '{value}' in '{property_name}' contains a hardcoded number. This is a potential correlation value and should be a variable.", container_context, element_name, key_name, value)
        return
    if len(value) > MIN_STRING_LENGTH and re.fullmatch(ALPHA_NUMERIC_PATTERN, value):
        _add_issue(issues_list, 'WARNING', 'Hardcoded String', element_name, f"The value '{value}' in '{property_name}' is a hardcoded string. Consider using a variable for dynamic values.", container_context, element_name, key_name, value)

def _check_raw_body_for_patterns(body_string, element_name, container_context, issues_list):
    if not isinstance(body_string, str) or not body_string.strip():
        return
    for sensitive_key in SENSITIVE_JSON_KEYS:
        if re.search(sensitive_key, body_string):
            _add_issue(issues_list, 'ERROR', 'Hardcoded Credential', element_name, f"A hardcoded sensitive key or value for '{sensitive_key}' was found in the raw body data.", container_context, element_name, sensitive_key, body_string)
            return
    for match in re.finditer(r'"(\w+)":\s*(\d+)', body_string):
        key = match.group(1)
        value = match.group(2)
        _add_issue(issues_list, 'WARNING', 'Hardcoded Number (Correlation)', element_name, f"A hardcoded number '{value}' was found for key '{key}' in the raw body data. This is a potential correlation value and should be a variable.", container_context, element_name, key_name=key, hardcoded_value=value)
    for pattern in HARDCODED_DATE_PATTERNS:
        for match in re.finditer(fr'"(\w+)":\s*"{pattern}"', body_string):
            key = match.group(1)
            value = match.group(2)
            _add_issue(issues_list, 'WARNING', 'Hardcoded Date (Correlation)', element_name, f"A hardcoded date '{value}' was found for key '{key}' in the raw body data. This is a potential correlation value and should be a variable.", container_context, element_name, key_name=key, hardcoded_value=value)
    if len(body_string) > MIN_STRING_LENGTH:
        for match in re.finditer(r'"(\w+)":\s*"(.*?)"', body_string):
            key = match.group(1)
            value = match.group(2)
            if len(value) > MIN_STRING_LENGTH and re.fullmatch(ALPHA_NUMERIC_PATTERN, value) and not _is_jmeter_variable(value):
                _add_issue(issues_list, 'WARNING', 'Hardcoded String', element_name, f"A hardcoded string '{value}' was found for key '{key}' in the raw body data. Consider using a variable for dynamic values.", container_context, element_name, key_name=key, hardcoded_value=value)

def _check_timer_value(element, element_name, container_context, issues_list):
    if element.tag == 'ConstantTimer':
        delay = element.findtext("./stringProp[@name='ConstantTimer.delay']")
        if _is_hardcoded(delay) and re.match(NUMERIC_PATTERN, delay):
            _add_issue(issues_list, 'WARNING', 'Hardcoded Number', element_name, f"The delay '{delay}' in ConstantTimer is hardcoded. Consider using a variable.", container_context, element_name, 'ConstantTimer.delay', delay)
    elif element.tag == 'GaussianRandomTimer':
        offset = element.findtext("./stringProp[@name='RandomTimer.offset']")
        range_val = element.findtext("./stringProp[@name='RandomTimer.range']")
        if _is_hardcoded(offset) and re.match(NUMERIC_PATTERN, offset):
            _add_issue(issues_list, 'WARNING', 'Hardcoded Number', element_name, f"The offset '{offset}' in GaussianRandomTimer is hardcoded. Consider using a variable.", container_context, element_name, 'RandomTimer.offset', offset)
        if _is_hardcoded(range_val) and re.match(NUMERIC_PATTERN, range_val):
            _add_issue(issues_list, 'WARNING', 'Hardcoded Number', element_name, f"The range '{range_val}' in GaussianRandomTimer is hardcoded. Consider using a variable.", container_context, element_name, 'RandomTimer.range', range_val)
    elif element.tag == 'UniformRandomTimer':
        range_val = element.findtext("./stringProp[@name='RandomTimer.range']")
        delay = element.findtext("./stringProp[@name='ConstantTimer.delay']")
        if _is_hardcoded(range_val) and re.match(NUMERIC_PATTERN, range_val):
            _add_issue(issues_list, 'WARNING', 'Hardcoded Number', element_name, f"The range '{range_val}' in UniformRandomTimer is hardcoded. Consider using a variable.", container_context, element_name, 'RandomTimer.range', range_val)
        if _is_hardcoded(delay) and re.match(NUMERIC_PATTERN, delay):
            _add_issue(issues_list, 'WARNING', 'Hardcoded Number', element_name, f"The delay '{delay}' in UniformRandomTimer is hardcoded. Consider using a variable.", container_context, element_name, 'ConstantTimer.delay', delay)

def _find_similar_correlated_value(root_element, issue):
    if issue['type'] in ['Hardcoded Date (Correlation)', 'Hardcoded Number (Correlation)', 'Hardcoded String']:
        key_name = issue.get('key_name')
        if key_name and not key_name.startswith('URL_'):
            for element in root_element.iter():
                element_name = _get_element_name(element)
                if element.tag == 'HeaderManager':
                    for header_entry in element.findall("./collectionProp[@name='HeaderManager.headers']/elementProp"):
                        header_name = header_entry.findtext("./stringProp[@name='Header.name']")
                        header_value = header_entry.findtext("./stringProp[@name='Header.value']")
                        if header_name == key_name and _is_jmeter_variable(header_value):
                            return f"A correlated value ('{header_value}') was found in header '{header_name}' of element '{element_name}'."
                if element.tag == 'HTTPSamplerProxy':
                    args_prop = element.find("./elementProp[@name='HTTPsampler.Arguments']")
                    if args_prop is not None:
                        for arg_entry in args_prop.findall("./collectionProp[@name='Arguments.arguments']/elementProp"):
                            param_name = arg_entry.findtext("./stringProp[@name='Argument.name']")
                            param_value = arg_entry.findtext("./stringProp[@name='Argument.value']")
                            if param_name == key_name and _is_jmeter_variable(param_value):
                                return f"A correlated value ('{param_value}') was found for parameter '{param_name}' in element '{element_name}'."
                        if element.findtext("./boolProp[@name='HTTPSampler.postBodyRaw']") == 'true':
                            raw_body = args_prop.findtext("./collectionProp/elementProp/stringProp[@name='Argument.value']")
                            # FIXED: Now checks for both quoted and unquoted variables
                            if f'"{key_name}"' in raw_body and re.search(fr'"{re.escape(key_name)}"\s*:\s*(?:".*?\${{.*?\}}.*?"|\${{.*?\}})', raw_body):
                                return f"A correlated value was found for key '{key_name}' in a raw body of element '{element_name}'."
        elif key_name and key_name.startswith('URL_'):
            for element in root_element.iter('HTTPSamplerProxy'):
                element_name = _get_element_name(element)
                url_path = element.findtext("./stringProp[@name='HTTPSampler.path']")
                url_domain = element.findtext("./stringProp[@name='HTTPSampler.domain']")
                if _is_jmeter_variable(url_path):
                    return f"A correlated URL path ('{url_path}') was found in element '{element_name}'."
                if _is_jmeter_variable(url_domain):
                    return f"A correlated URL domain ('{url_domain}') was found in element '{element_name}'."
    return None

def analyze_jmeter_script(root_element, enabled_validations):
    module_issues = []
    if THIS_VALIDATION_OPTION_NAME not in enabled_validations:
        return module_issues
    initial_issues = []
    current_thread_group_context = "Global/Unassigned"
    for element in root_element.iter():
        element_tag = element.tag
        element_name = _get_element_name(element)
        if element_tag in ['ThreadGroup', 'SetupThreadGroup', 'PostThreadGroup', 'TestFragment']:
            current_thread_group_context = element_name
        if element_tag == 'AuthManager':
            for auth_entry in element.findall("./collectionProp[@name='AuthManager.auths']/elementProp"):
                username = auth_entry.findtext("./stringProp[@name='Authorization.username']")
                password = auth_entry.findtext("./stringProp[@name='Authorization.password']")
                if _is_hardcoded(username):
                    _add_issue(initial_issues, 'ERROR', 'Hardcoded Credential', element_name, f"Hardcoded username '{username}' found in AuthManager.", current_thread_group_context, element_name, 'username', username)
                if _is_hardcoded(password):
                    _add_issue(initial_issues, 'ERROR', 'Hardcoded Credential', element_name, f"Hardcoded password found in AuthManager.", current_thread_group_context, element_name, 'password', password)
        if element_tag == 'HeaderManager':
            for header_entry in element.findall("./collectionProp[@name='HeaderManager.headers']/elementProp"):
                header_name = header_entry.findtext("./stringProp[@name='Header.name']")
                header_value = header_entry.findtext("./stringProp[@name='Header.value']")
                if header_name and header_name.strip() in SENSITIVE_HEADERS and _is_hardcoded(header_value):
                    _add_issue(initial_issues, 'ERROR', 'Hardcoded Credential/Token', element_name, f"Hardcoded value found for sensitive header '{header_name}'.", current_thread_group_context, element_name, header_name, header_value)
                elif header_name and header_name.strip() not in SENSITIVE_HEADERS and header_name.strip() not in HEADER_EXCLUSION_LIST:
                    _check_general_value(header_value, element_name, current_thread_group_context, f"header '{header_name}'", initial_issues, key_name=header_name, hardcoded_value=header_value)
        if element_tag == 'HTTPSamplerProxy':
            args_prop = element.find("./elementProp[@name='HTTPsampler.Arguments']")
            if args_prop is not None:
                for arg_entry in args_prop.findall("./collectionProp[@name='Arguments.arguments']/elementProp"):
                    param_name = arg_entry.findtext("./stringProp[@name='Argument.name']")
                    param_value = arg_entry.findtext("./stringProp[@name='Argument.value']")
                    if param_name and param_name.strip() in SENSITIVE_PARAM_NAMES and _is_hardcoded(param_value):
                        _add_issue(initial_issues, 'ERROR', 'Hardcoded Credential', element_name, f"Hardcoded value found for sensitive parameter '{param_name}'.", current_thread_group_context, element_name, param_name, param_value)
        if 'Assertion' in element_tag or element_tag.endswith('Assertion'):
            continue
        if element_tag == 'HTTPSamplerProxy':
            domain = element.findtext("./stringProp[@name='HTTPSampler.domain']")
            path = element.findtext("./stringProp[@name='HTTPSampler.path']")
            port = element.findtext("./stringProp[@name='HTTPSampler.port']")
            if domain and ('/' in domain or '?' in domain or '#' in domain):
                _add_issue(initial_issues, 'ERROR', 'Malformed Server Name', f"HTTP Request '{element_name}'", f"Server Name/IP '{domain}' contains path segments, query parameters, or URL fragments.", current_thread_group_context, element_name)
            if _is_ipv4(domain):
                _add_issue(initial_issues, 'WARNING', 'Hardcoded IP Address', f"HTTP Request '{element_name}'", f"Server Name/IP '{domain}' is a hardcoded IP address.", current_thread_group_context, element_name, hardcoded_value=domain)
            elif _contains_env_specific_pattern(domain):
                _add_issue(initial_issues, 'ERROR', 'Hardcoded Environment Hostname', f"HTTP Request '{element_name}'", f"Server Name/IP '{domain}' appears to be a hardcoded environment-specific hostname.", current_thread_group_context, element_name, hardcoded_value=domain)
            if port and _is_hardcoded(port) and re.match(NUMERIC_PATTERN, port):
                _add_issue(initial_issues, 'WARNING', 'Hardcoded Port Number', f"HTTP Request '{element_name}'", f"The port number '{port}' is hardcoded. It should be parameterized.", current_thread_group_context, element_name, hardcoded_value=port)
            if domain and _is_hardcoded(domain) and not _is_ipv4(domain) and not _contains_env_specific_pattern(domain):
                _check_general_value(domain, element_name, current_thread_group_context, 'HTTPSampler.domain', initial_issues, key_name='URL_domain', hardcoded_value=domain)
            _check_general_value(path, element_name, current_thread_group_context, 'HTTPSampler.path', initial_issues, key_name='URL_path', hardcoded_value=path)
            args_prop = element.find("./elementProp[@name='HTTPsampler.Arguments']")
            if args_prop is not None:
                if element.findtext("./boolProp[@name='HTTPSampler.postBodyRaw']") == 'true':
                    raw_body = args_prop.findtext("./collectionProp/elementProp/stringProp[@name='Argument.value']")
                    _check_raw_body_for_patterns(raw_body, element_name, current_thread_group_context, initial_issues)
                else:
                    for arg_entry in args_prop.findall("./collectionProp[@name='Arguments.arguments']/elementProp"):
                        param_name = arg_entry.findtext("./stringProp[@name='Argument.name']")
                        param_value = arg_entry.findtext("./stringProp[@name='Argument.value']")
                        if param_name and param_name not in SENSITIVE_PARAM_NAMES:
                            _check_general_value(param_value, element_name, current_thread_group_context, f"parameter '{param_name}'", initial_issues, key_name=param_name, hardcoded_value=param_value)
        if element_tag in ['ConstantTimer', 'GaussianRandomTimer', 'UniformRandomTimer']:
            _check_timer_value(element, element_name, current_thread_group_context, initial_issues)
        if element_tag == 'LoopController':
            loops = element.findtext("./stringProp[@name='LoopController.loops']")
            if _is_hardcoded(loops) and re.match(NUMERIC_PATTERN, loops) and int(float(loops)) > -1:
                _add_issue(initial_issues, 'WARNING', 'Hardcoded Loop Count', element_name, f"Fixed loop count '{loops}' found. Consider using a variable for flexibility.", current_thread_group_context, element_name, hardcoded_value=loops)
    final_issues = []
    for issue in initial_issues:
        if issue['severity'] == 'ERROR' or 'Credential' in issue['type'] or 'Malformed' in issue['type']:
            final_issues.append(issue)
            continue
        correlated_info = _find_similar_correlated_value(root_element, issue)
        if correlated_info:
            issue['description'] = f"{issue['description']}\n[Found Correlation] {correlated_info}"
        final_issues.append(issue)
    return final_issues