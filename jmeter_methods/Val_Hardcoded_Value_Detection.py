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
HARDCODED_DATE_PATTERNS = [r'\b\d{4}-\d{2}-\d{2}\b', r'\b\d{4}-\d{2}\b', r'\b\d{2}/\d{2}/\d{4}\b',
                           r'\b\d{2}-\d{2}-\d{4}\b', r'\b\d{2}-\d{2}\b']
EXCLUSION_LIST = {'GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS', 'PATCH', 'true', 'false', 'http', 'https', '200',
                  '201', '204', '400', '401', '403', '404', '500', 'application/json', 'application/xml', 'text/plain',
                  'text/html', 'en-US', 'en-GB'}
HEADER_EXCLUSION_LIST = {'Content-Type', 'Accept', 'Accept-Encoding', 'Accept-Language', 'Cache-Control', 'Connection',
                         'Content-Length', 'Host', 'Origin', 'Referer', 'Upgrade-Insecure-Requests', 'User-Agent'}
ENVIRONMENT_HOST_PATTERNS = [r'^dev\.', r'^qa\.', r'^uat\.', r'\.internal$', r'\.local$', r'staging', r'preprod',
                             r'-test\d*$', r'test\.org$', r'myapp-prod\d*', ]


def _add_issue(issues_list, severity, issue_type, location, description, thread_group="N/A", element_name="N/A",
               key_name="", hardcoded_value="", hardcoded_segment="", element_obj=None):
    issues_list.append({'severity': severity, 'validation_option_name': THIS_VALIDATION_OPTION_NAME, 'type': issue_type,
                        'location': location, 'description': description, 'thread_group': thread_group,
                        'element_name': element_name, 'key_name': key_name, 'hardcoded_value': hardcoded_value,
                        'hardcoded_segment': hardcoded_segment, 'element_obj': element_obj})


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


def _get_full_url(sampler):
    domain = sampler.findtext("./stringProp[@name='HTTPSampler.domain']")
    path = sampler.findtext("./stringProp[@name='HTTPSampler.path']")
    return f"{domain}{path}"


def _check_general_value(value, element_name, container_context, property_name, issues_list, key_name="",
                         hardcoded_value="", element_obj=None):
    if not _is_hardcoded(value):
        return
    for pattern in HARDCODED_DATE_PATTERNS:
        match = re.search(pattern, value)
        if match:
            hardcoded_segment = match.group(0)
            _add_issue(issues_list, 'WARNING', 'Hardcoded Date (Correlation)', element_name,
                       f"The value '{value}' in '{property_name}' contains a hardcoded date. This is a potential correlation value and should be a variable.",
                       container_context, element_name, key_name, value, hardcoded_segment, element_obj)
            return
    match = re.search(HARDCODED_NUMBER_PATTERN, value)
    if match:
        hardcoded_segment = match.group(0)
        _add_issue(issues_list, 'WARNING', 'Hardcoded Number (Correlation)', element_name,
                   f"The value '{value}' in '{property_name}' contains a hardcoded number. This is a potential correlation value and should be a variable.",
                   container_context, element_name, key_name, value, hardcoded_segment, element_obj)
        return
    if len(value) > MIN_STRING_LENGTH and re.fullmatch(ALPHA_NUMERIC_PATTERN, value):
        _add_issue(issues_list, 'WARNING', 'Hardcoded String', element_name,
                   f"The value '{value}' in '{property_name}' is a hardcoded string. Consider using a variable for dynamic values.",
                   container_context, element_name, key_name, value, value, element_obj)


def _check_raw_body_for_patterns(body_string, element_name, container_context, issues_list, element_obj):
    if not isinstance(body_string, str) or not body_string.strip():
        return
    for sensitive_key in SENSITIVE_JSON_KEYS:
        if re.search(sensitive_key, body_string):
            _add_issue(issues_list, 'ERROR', 'Hardcoded Credential', element_name,
                       f"A hardcoded sensitive key or value for '{sensitive_key}' was found in the raw body data.",
                       container_context, element_name, sensitive_key, body_string, body_string, element_obj)
            return
    for match in re.finditer(r'"(\w+)":\s*(\d+)', body_string):
        key = match.group(1)
        value = match.group(2)
        _add_issue(issues_list, 'WARNING', 'Hardcoded Number (Correlation)', element_name,
                   f"A hardcoded number '{value}' was found for key '{key}' in the raw body data. This is a potential correlation value and should be a variable.",
                   container_context, element_name, key_name=key, hardcoded_value=value, hardcoded_segment=value,
                   element_obj=element_obj)
    for pattern in HARDCODED_DATE_PATTERNS:
        for match in re.finditer(fr'"(\w+)":\s*"(.*?)"', body_string):
            key = match.group(1)
            value = match.group(2)
            if re.search(pattern, value):
                hardcoded_segment = re.search(pattern, value).group(0)
                _add_issue(issues_list, 'WARNING', 'Hardcoded Date (Correlation)', element_name,
                           f"A hardcoded date '{value}' was found for key '{key}' in the raw body data. This is a potential correlation value and should be a variable.",
                           container_context, element_name, key_name=key, hardcoded_value=value,
                           hardcoded_segment=hardcoded_segment, element_obj=element_obj)
    if len(body_string) > MIN_STRING_LENGTH:
        for match in re.finditer(r'"(\w+)":\s*"(.*?)"', body_string):
            key = match.group(1)
            value = match.group(2)
            if len(value) > MIN_STRING_LENGTH and re.fullmatch(ALPHA_NUMERIC_PATTERN,
                                                               value) and not _is_jmeter_variable(value):
                _add_issue(issues_list, 'WARNING', 'Hardcoded String', element_name,
                           f"A hardcoded string '{value}' was found for key '{key}' in the raw body data. Consider using a variable for dynamic values.",
                           container_context, element_name, key_name=key, hardcoded_value=value,
                           hardcoded_segment=value, element_obj=element_obj)


def _check_timer_value(element, element_name, container_context, issues_list):
    if element.tag == 'ConstantTimer':
        delay = element.findtext("./stringProp[@name='ConstantTimer.delay']")
        if _is_hardcoded(delay) and re.match(NUMERIC_PATTERN, delay):
            _add_issue(issues_list, 'WARNING', 'Hardcoded Number', element_name,
                       f"The delay '{delay}' in ConstantTimer is hardcoded. Consider using a variable.",
                       container_context, element_name, 'ConstantTimer.delay', delay, delay, element_obj=element)
    elif element.tag == 'GaussianRandomTimer':
        offset = element.findtext("./stringProp[@name='RandomTimer.offset']")
        range_val = element.findtext("./stringProp[@name='RandomTimer.range']")
        if _is_hardcoded(offset) and re.match(NUMERIC_PATTERN, offset):
            _add_issue(issues_list, 'WARNING', 'Hardcoded Number', element_name,
                       f"The offset '{offset}' in GaussianRandomTimer is hardcoded. Consider using a variable.",
                       container_context, element_name, 'RandomTimer.offset', offset, offset, element_obj=element)
        if _is_hardcoded(range_val) and re.match(NUMERIC_PATTERN, range_val):
            _add_issue(issues_list, 'WARNING', 'Hardcoded Number', element_name,
                       f"The range '{range_val}' in GaussianRandomTimer is hardcoded. Consider using a variable.",
                       container_context, element_name, 'RandomTimer.range', range_val, range_val, element_obj=element)
    elif element.tag == 'UniformRandomTimer':
        range_val = element.findtext("./stringProp[@name='RandomTimer.range']")
        delay = element.findtext("./stringProp[@name='ConstantTimer.delay']")
        if _is_hardcoded(range_val) and re.match(NUMERIC_PATTERN, range_val):
            _add_issue(issues_list, 'WARNING', 'Hardcoded Number', element_name,
                       f"The range '{range_val}' in UniformRandomTimer is hardcoded. Consider using a variable.",
                       container_context, element_name, 'RandomTimer.range', range_val, range_val, element_obj=element)
        if _is_hardcoded(delay) and re.match(NUMERIC_PATTERN, delay):
            _add_issue(issues_list, 'WARNING', 'Hardcoded Number', element_name,
                       f"The delay '{delay}' in UniformRandomTimer is hardcoded. Consider using a variable.",
                       container_context, element_name, 'ConstantTimer.delay', delay, delay, element_obj=element)


def _find_similar_correlated_value(root_element, issue, parent_map):
    hardcoded_value = issue.get('hardcoded_value')
    hardcoded_segment = issue.get('hardcoded_segment')

    if not hardcoded_value or not issue.get('key_name'):
        return None

    # URL domain correlation check
    if issue['key_name'] == 'URL_domain':
        issue_path = issue['element_obj'].findtext("./stringProp[@name='HTTPSampler.path']")
        for element in root_element.iter('HTTPSamplerProxy'):
            element_name = _get_element_name(element)
            url_domain = element.findtext("./stringProp[@name='HTTPSampler.domain']")
            url_path = element.findtext("./stringProp[@name='HTTPSampler.path']")

            # Check for a variable and a similar path
            if _is_jmeter_variable(url_domain) and url_path == issue_path:
                return f"A correlated URL domain ('{url_domain}') was found in element '{element_name}' with a similar URL path."

    # URL path correlation check
    if issue['key_name'] == 'URL_path':
        # Construct a regex pattern to match a URL path with a variable in place of the hardcoded segment
        try:
            hardcoded_path_pattern = re.escape(hardcoded_value).replace(re.escape(hardcoded_segment), r'\${[^}]+}')
            hardcoded_path_regex = re.compile(hardcoded_path_pattern)
        except re.error:
            return None  # Invalid regex pattern

        for element in root_element.iter('HTTPSamplerProxy'):
            element_name = _get_element_name(element)
            url_path = element.findtext("./stringProp[@name='HTTPSampler.path']")
            if url_path and hardcoded_path_regex.fullmatch(url_path):
                return f"A correlated URL path ('{url_path}') was found in element '{element_name}'."

    # Check other correlations (headers, params, etc.)
    for element in root_element.iter():
        element_name = _get_element_name(element)

        parent_sampler = parent_map.get(element)
        while parent_sampler is not None and parent_sampler.tag != 'HTTPSamplerProxy':
            parent_sampler = parent_map.get(parent_sampler)

        url_message = f" in URL '{_get_full_url(parent_sampler)}'" if parent_sampler else ""

        if element.tag == 'HeaderManager':
            for header_entry in element.findall("./collectionProp[@name='HeaderManager.headers']/elementProp"):
                header_name = header_entry.findtext("./stringProp[@name='Header.name']")
                header_value = header_entry.findtext("./stringProp[@name='Header.value']")
                if header_name == issue['key_name'] and _is_jmeter_variable(header_value):
                    return f"A correlated value ('{header_value}') was found in header '{header_name}' of element '{element_name}'{url_message}."

        if element.tag == 'HTTPSamplerProxy':
            args_prop = element.find("./elementProp[@name='HTTPsampler.Arguments']")
            if args_prop is not None:
                if element.findtext("./boolProp[@name='HTTPSampler.postBodyRaw']") == 'true':
                    raw_body = args_prop.findtext("./collectionProp/elementProp/stringProp[@name='Argument.value']")
                    if raw_body and f'"{issue["key_name"]}"' in raw_body and re.search(
                            fr'"{re.escape(issue["key_name"])}"\s*:\s*(?:".*?\${{.*?\}}.*?"|\${{.*?\}})', raw_body):
                        return f"A correlated value was found for key '{issue['key_name']}' in a raw body of element '{element_name}'{url_message}."
                else:
                    for arg_entry in args_prop.findall("./collectionProp[@name='Arguments.arguments']/elementProp"):
                        param_name = arg_entry.findtext("./stringProp[@name='Argument.name']")
                        param_value = arg_entry.findtext("./stringProp[@name='Argument.value']")
                        if param_name == issue['key_name'] and _is_jmeter_variable(param_value):
                            return f"A correlated value ('{param_value}') was found for parameter '{param_name}' in element '{element_name}'{url_message}."
    return None


def analyze_jmeter_script(root_element, enabled_validations):
    module_issues = []
    if THIS_VALIDATION_OPTION_NAME not in enabled_validations:
        return module_issues, []

    # Step 1: Pre-process the entire tree to build a reliable scope map.
    element_to_controller_map = {}
    controller_stack = ["Global/Unassigned"]

    # We need a parent map to check for direct nesting.
    parent_map = {c: p for p in root_element.iter() for c in p}

    for element in root_element.iter():
        element_tag = element.tag
        element_name = _get_element_name(element)

        parent_element = parent_map.get(element)

        # Check for start of a new controller scope
        if element_tag in ['ThreadGroup', 'SetupThreadGroup', 'PostThreadGroup', 'TestFragmentController',
                           'TransactionController']:
            controller_stack.append(element_name)

        # All elements are mapped to the current controller at the top of the stack.
        element_to_controller_map[element] = controller_stack[-1]

        # Pop from the stack when a controller's scope ends. The 'hashTree' tag is a good
        # signal for this. A controller's content is contained within a hashTree.
        if element_tag == 'hashTree' and parent_element is not None and parent_element.tag in ['TestPlan',
                                                                                               'ThreadGroup',
                                                                                               'SetupThreadGroup',
                                                                                               'PostThreadGroup',
                                                                                               'TestFragmentController',
                                                                                               'TransactionController']:
            if len(controller_stack) > 1:
                controller_stack.pop()

    # The rest of the script is largely the same, but now uses the correct mapping.
    initial_issues = []

    for element in root_element.iter():
        element_tag = element.tag
        element_name = _get_element_name(element)

        # Use the pre-computed map for the thread group context
        thread_group_context = element_to_controller_map.get(element, "Global/Unassigned")

        if element_tag == 'AuthManager':
            for auth_entry in element.findall("./collectionProp[@name='AuthManager.auths']/elementProp"):
                username = auth_entry.findtext("./stringProp[@name='Authorization.username']")
                password = auth_entry.findtext("./stringProp[@name='Authorization.password']")
                if _is_hardcoded(username):
                    _add_issue(initial_issues, 'ERROR', 'Hardcoded Credential', element_name,
                               f"Hardcoded username '{username}' found in AuthManager.", thread_group_context,
                               element_name, 'username', username, username, element_obj=element)
                if _is_hardcoded(password):
                    _add_issue(initial_issues, 'ERROR', 'Hardcoded Credential', element_name,
                               f"Hardcoded password found in AuthManager.", thread_group_context, element_name,
                               'password', password, password, element_obj=element)
        elif element_tag == 'HeaderManager':
            for header_entry in element.findall("./collectionProp[@name='HeaderManager.headers']/elementProp"):
                header_name = header_entry.findtext("./stringProp[@name='Header.name']")
                header_value = header_entry.findtext("./stringProp[@name='Header.value']")
                if header_name and header_name.strip() in SENSITIVE_HEADERS and _is_hardcoded(header_value):
                    _add_issue(initial_issues, 'ERROR', 'Hardcoded Credential/Token', element_name,
                               f"Hardcoded value found for sensitive header '{header_name}'.", thread_group_context,
                               element_name, header_name, header_value, header_value, element_obj=element)
                elif header_name and header_name.strip() not in SENSITIVE_HEADERS and header_name.strip() not in HEADER_EXCLUSION_LIST:
                    _check_general_value(header_value, element_name, thread_group_context, f"header '{header_name}'",
                                         initial_issues, key_name=header_name, hardcoded_value=header_value,
                                         element_obj=element)
        elif element_tag == 'HTTPSamplerProxy':
            domain = element.findtext("./stringProp[@name='HTTPSampler.domain']")
            path = element.findtext("./stringProp[@name='HTTPSampler.path']")
            port = element.findtext("./stringProp[@name='HTTPSampler.port']")
            if domain and ('/' in domain or '?' in domain or '#' in domain):
                _add_issue(initial_issues, 'ERROR', 'Malformed Server Name', f"HTTP Request '{element_name}'",
                           f"Server Name/IP '{domain}' contains path segments, query parameters, or URL fragments.",
                           thread_group_context, element_name, hardcoded_value=domain, element_obj=element)
            if _is_ipv4(domain):
                _add_issue(initial_issues, 'WARNING', 'Hardcoded IP Address', f"HTTP Request '{element_name}'",
                           f"Server Name/IP '{domain}' is a hardcoded IP address.", thread_group_context, element_name,
                           hardcoded_value=domain, element_obj=element)
            elif _contains_env_specific_pattern(domain):
                _add_issue(initial_issues, 'ERROR', 'Hardcoded Environment Hostname', f"HTTP Request '{element_name}'",
                           f"Server Name/IP '{domain}' appears to be a hardcoded environment-specific hostname.",
                           thread_group_context, element_name, hardcoded_value=domain, element_obj=element)
            if port and _is_hardcoded(port) and re.match(NUMERIC_PATTERN, port):
                _add_issue(initial_issues, 'WARNING', 'Hardcoded Port Number', f"HTTP Request '{element_name}'",
                           f"The port number '{port}' is hardcoded. It should be parameterized.", thread_group_context,
                           element_name, hardcoded_value=port, element_obj=element)
            if domain and _is_hardcoded(domain) and not _is_ipv4(domain) and not _contains_env_specific_pattern(domain):
                _check_general_value(domain, element_name, thread_group_context, 'HTTPSampler.domain', initial_issues,
                                     key_name='URL_domain', hardcoded_value=domain, element_obj=element)
            _check_general_value(path, element_name, thread_group_context, 'HTTPSampler.path', initial_issues,
                                 key_name='URL_path', hardcoded_value=path, element_obj=element)

            args_prop = element.find("./elementProp[@name='HTTPsampler.Arguments']")
            if args_prop is not None:
                if element.findtext("./boolProp[@name='HTTPSampler.postBodyRaw']") == 'true':
                    raw_body = args_prop.findtext("./collectionProp/elementProp/stringProp[@name='Argument.value']")
                    _check_raw_body_for_patterns(raw_body, element_name, thread_group_context, initial_issues,
                                                 element_obj=element)
                else:
                    for arg_entry in args_prop.findall("./collectionProp[@name='Arguments.arguments']/elementProp"):
                        param_name = arg_entry.findtext("./stringProp[@name='Argument.name']")
                        param_value = arg_entry.findtext("./stringProp[@name='Argument.value']")
                        if param_name and param_name.strip() in SENSITIVE_PARAM_NAMES and _is_hardcoded(param_value):
                            _add_issue(initial_issues, 'ERROR', 'Hardcoded Credential', element_name,
                                       f"Hardcoded value found for sensitive parameter '{param_name}'.",
                                       thread_group_context, element_name, param_name, param_value, param_value,
                                       element_obj=element)
                        elif param_name:
                            _check_general_value(param_value, element_name, thread_group_context,
                                                 f"parameter '{param_name}'", initial_issues, key_name=param_name,
                                                 hardcoded_value=param_value, element_obj=element)
        elif element_tag in ['ConstantTimer', 'GaussianRandomTimer', 'UniformRandomTimer']:
            _check_timer_value(element, element_name, thread_group_context, initial_issues)
        elif element_tag == 'LoopController':
            loops = element.findtext("./stringProp[@name='LoopController.loops']")
            if _is_hardcoded(loops) and re.match(NUMERIC_PATTERN, loops) and int(float(loops)) > -1:
                _add_issue(initial_issues, 'WARNING', 'Hardcoded Loop Count', element_name,
                           f"Fixed loop count '{loops}' found. Consider using a variable for flexibility.",
                           thread_group_context, element_name, hardcoded_value=loops, hardcoded_segment=loops,
                           element_obj=element)

    final_issues = []
    for issue in initial_issues:
        if issue['severity'] == 'ERROR' or 'Credential' in issue['type'] or 'Malformed' in issue['type']:
            final_issues.append(issue)
            continue
        # The parent_map used here is now correctly generated
        parent_map = {c: p for p in root_element.iter() for c in p}
        correlated_info = _find_similar_correlated_value(root_element, issue, parent_map)
        if correlated_info:
            issue['description'] = f"{issue['description']}\n[Found Correlation] {correlated_info}"
        final_issues.append(issue)

    return final_issues, []