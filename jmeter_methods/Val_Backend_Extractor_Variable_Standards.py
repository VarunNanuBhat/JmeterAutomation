# jmeter_methods/Val_Backend_Extractor_Variable_Standards.py
import xml.etree.ElementTree as ET
import re

THIS_VALIDATION_OPTION_NAME = "Extractor Variable Naming Standards"


def _add_issue(issues_list, severity, issue_type, location, description, thread_group="N/A", element_name="N/A"):
    """Helper function to add a consistent issue dictionary to the list."""
    # Removed print statements; issues are now solely added to the list for report generation.
    issues_list.append({
        'severity': severity,
        'validation_option_name': THIS_VALIDATION_OPTION_NAME,
        'type': issue_type,
        'location': location,
        'description': description,
        'thread_group': thread_group,
        'element_name': element_name
    })


def _is_camel_case(s):
    """Checks if a string follows camelCase (starts with lowercase, no underscores/hyphens)."""
    if not s:
        return False
    if not s[0].islower():
        return False
    if '_' in s or '-' in s:
        return False
    return True


def _get_element_name(element):
    """Helper to safely get the 'testname' attribute of an element."""
    return element.get('testname', 'Unnamed Element')


def _get_property_value(element, prop_name):
    """Helper to safely get the text content of a stringProp with a given name."""
    prop_element = element.find(f"./stringProp[@name='{prop_name}']")
    # print(f"DEBUG_PROP: Element='{_get_element_name(element)}', Looking for prop='{prop_name}', Found: '{prop_element.text if prop_element is not None else 'NOT FOUND'}'")
    return prop_element.text if prop_element is not None else ""


def _get_bool_property_value(element, prop_name):
    """Helper to safely get the boolean value of a boolProp with a given name."""
    prop_element = element.find(f"./boolProp[@name='{prop_name}']")
    if prop_element is not None:
        # print(f"DEBUG_BOOL_PROP: Element='{_get_element_name(element)}', Looking for bool prop='{prop_name}', Found: '{prop_element.text}'")
        return prop_element.text.lower() == 'true'
    return False


def _validate_common_extractor_rules(extractor_element, issues, container_context):
    """Applies common validation rules to all extractor types."""
    element_name = _get_element_name(extractor_element)
    # print(f"DEBUG: Validating common rules for extractor: '{element_name}' (Tag: {extractor_element.tag}) in Context: {container_context}")

    variable_name = ""
    default_value = ""
    match_no_str = ""
    scope = ""

    if extractor_element.tag == 'JSONPostProcessor':
        variable_name = _get_property_value(extractor_element, 'JSONPostProcessor.referenceNames')
        default_value = _get_property_value(extractor_element, 'JSONPostProcessor.defaultValues')
        match_no_str = _get_property_value(extractor_element, 'JSONPostProcessor.match_numbers')
        scope = _get_property_value(extractor_element, 'JSONPostProcessor.scope')
    elif extractor_element.tag == 'RegexExtractor':
        variable_name = _get_property_value(extractor_element, 'RegexExtractor.refname')
        default_value = _get_property_value(extractor_element, 'RegexExtractor.default')
        match_no_str = _get_property_value(extractor_element, 'RegexExtractor.match_number')
        scope = _get_property_value(extractor_element, 'RegexExtractor.scope')
    elif extractor_element.tag == 'XPathExtractor':
        variable_name = _get_property_value(extractor_element, 'XPathExtractor.refname')
        default_value = _get_property_value(extractor_element, 'XPathExtractor.default')
        match_no_str = _get_property_value(extractor_element, 'XPathExtractor.matchNumber') # Corrected property name
        scope = _get_property_value(extractor_element, 'XPathExtractor.scope')
    elif extractor_element.tag == 'CssSelectorExtractor':
        variable_name = _get_property_value(extractor_element, 'CssSelectorExtractor.refname')
        default_value = _get_property_value(extractor_element, 'CssSelectorExtractor.defaultValue')
        match_no_str = _get_property_value(extractor_element, 'CssSelectorExtractor.matchNumber')
        scope = _get_property_value(extractor_element, 'CssSelectorExtractor.scope')
    elif extractor_element.tag == 'BoundaryExtractor':
        variable_name = _get_property_value(extractor_element, 'BoundaryExtractor.refname')
        default_value = _get_property_value(extractor_element, 'BoundaryExtractor.default') # Corrected property name
        match_no_str = _get_property_value(extractor_element, 'BoundaryExtractor.match_number')
        scope = _get_property_value(extractor_element, 'BoundaryExtractor.scope')
    else: # Fallback for unknown extractor types, using generic property names if they exist
        variable_name = _get_property_value(extractor_element, 'Extractor.variable')
        default_value = _get_property_value(extractor_element, 'Extractor.default')
        match_no_str = _get_property_value(extractor_element, 'Extractor.match_number')
        scope = _get_property_value(extractor_element, 'Extractor.scope')

    # print(f"DEBUG:   Common Props -> Var Name: '{variable_name}', Default: '{default_value}', Match No: '{match_no_str}', Scope: '{scope}'")

    # 1. JMeter Variable Naming (Reference Name field)
    if not variable_name.startswith('c_'):
        _add_issue(issues, 'ERROR', 'JMeter Variable Naming', element_name,
                   f"Variable name '{variable_name}' does not start with 'c_'.", container_context, element_name)
    else:
        camel_case_part = variable_name[2:]
        if not _is_camel_case(camel_case_part):
            _add_issue(issues, 'ERROR', 'JMeter Variable Naming', element_name,
                       f"Variable name '{variable_name}' does not follow camelCase after 'c_'.", container_context,
                       element_name)

    # 2. Required Default Value
    if not default_value:
        _add_issue(issues, 'ERROR', 'Required Default Value', element_name,
                   f"Default Value for extractor '{element_name}' is empty.", container_context, element_name)

    # 3. Match No. Type & Value Convention
    try:
        if match_no_str:
            match_no = int(match_no_str)
            if match_no > 1:
                _add_issue(issues, 'WARNING', 'Match No. Value Convention', element_name,
                           f"Match No. '{match_no_str}' is a specific positive integer (>1), which can make scripts brittle.",
                           container_context, element_name)
        else:
             _add_issue(issues, 'ERROR', 'Match No. Type', element_name,
                   f"Match No. is empty for '{element_name}'. It should be an integer.",
                   container_context, element_name)
    except ValueError:
        _add_issue(issues, 'ERROR', 'Match No. Type', element_name,
                   f"Match No. '{match_no_str}' is not a valid integer for '{element_name}'.",
                   container_context, element_name)

    # 4. Preferred Scope
    if scope and scope != 'Main sample only':
        _add_issue(issues, 'WARNING', 'Preferred Scope', element_name,
                   f"Scope for extractor '{element_name}' is '{scope}'. 'Main sample only' is generally preferred.",
                   container_context, element_name)

    # 5. Extractor Element Naming (UI Name) - Type Prefix & Contains Variable Name
    extractor_type_prefix = ""
    if extractor_element.tag == 'RegexExtractor':
        extractor_type_prefix = "REGEXP_"
    elif extractor_element.tag == 'JSONPostProcessor':
        extractor_type_prefix = "JSON_"
    elif extractor_element.tag == 'XPathExtractor':
        extractor_type_prefix = "XPATH_"
    elif extractor_element.tag == 'CssSelectorExtractor':
        extractor_type_prefix = "CSS_"
    elif extractor_element.tag == 'BoundaryExtractor':
        extractor_type_prefix = "BOUNDARY_"

    if extractor_type_prefix and not element_name.startswith(extractor_type_prefix):
        _add_issue(issues, 'WARNING', 'Extractor Element Naming', element_name,
                   f"Extractor '{element_name}' does not start with a recognized type prefix (e.g., {extractor_type_prefix}).",
                   container_context, element_name)

    if variable_name and variable_name not in element_name:
        _add_issue(issues, 'WARNING', 'Extractor Element Naming', element_name,
                   f"Extractor '{element_name}' should contain its exact variable name '{variable_name}'.",
                   container_context, element_name)


def _validate_json_extractor(extractor_element, issues, container_context):
    """Validates rules specific to JSON Extractor."""
    element_name = _get_element_name(extractor_element)
    _validate_common_extractor_rules(extractor_element, issues, container_context)
    # print(f"DEBUG: Validating JSON specific rules for '{element_name}'")

    json_path = _get_property_value(extractor_element, 'JSONPostProcessor.jsonPathExprs')

    # print(f"DEBUG:   JSON Path: '{json_path}'")

    if not json_path:
        _add_issue(issues, 'ERROR', 'Malformed Extractor Expression', element_name,
                   f"JSON Path expression for '{element_name}' is empty.", container_context, element_name)
    elif not json_path.startswith('$.'):
        _add_issue(issues, 'ERROR', 'Malformed Extractor Expression', element_name,
                   f"JSON Path expression '{json_path}' does not start with '$.'.", container_context, element_name)

    match_no_str = _get_property_value(extractor_element, 'JSONPostProcessor.match_numbers')
    compute_concat = _get_bool_property_value(extractor_element, 'JSONPostProcessor.compute_concat')

    # print(f"DEBUG:   Match No: '{match_no_str}', Compute Concat: {compute_concat}")

    if match_no_str == '-1' and compute_concat:
        _add_issue(issues, 'WARNING', 'Compute Concat Var', element_name,
                   f"'Compute concatenation var' is enabled for '{element_name}' with Match No. -1.", container_context,
                   element_name)


def _validate_regex_extractor(extractor_element, issues, container_context):
    """Validates rules specific to Regular Expression Extractor."""
    element_name = _get_element_name(extractor_element)
    _validate_common_extractor_rules(extractor_element, issues, container_context)
    # print(f"DEBUG: Validating RegEx specific rules for '{element_name}'")

    regex_pattern = _get_property_value(extractor_element, 'RegexExtractor.regex')
    template = _get_property_value(extractor_element, 'RegexExtractor.template')
    # print(f"DEBUG:   Regex Pattern: '{regex_pattern}', Template: '{template}'")

    if not regex_pattern:
        _add_issue(issues, 'ERROR', 'Malformed Extractor Expression', element_name,
                   f"Regular Expression for '{element_name}' is empty.", container_context, element_name)

    if not template:
        _add_issue(issues, 'ERROR', 'Malformed Extractor Expression', element_name,
                   f"Template field for '{element_name}' is empty.", container_context, element_name)
    elif template == '$0$':
        _add_issue(issues, 'WARNING', 'RegEx Template \'$0$\' Usage', element_name,
                   f"Template for '{element_name}' uses '$0$', which matches the entire string and may not be intended.",
                   container_context, element_name)


def _validate_xpath_extractor(extractor_element, issues, container_context):
    """Validates rules specific to XPath Extractor."""
    element_name = _get_element_name(extractor_element)
    _validate_common_extractor_rules(extractor_element, issues, container_context)
    # print(f"DEBUG: Validating XPath specific rules for '{element_name}'")

    xpath_query = _get_property_value(extractor_element, 'XPathExtractor.xpathQuery')
    # print(f"DEBUG:   XPath Query: '{xpath_query}'")
    if not xpath_query:
        _add_issue(issues, 'ERROR', 'Malformed Extractor Expression', element_name,
                   f"XPath query for '{element_name}' is empty.", container_context, element_name)


def _validate_css_extractor(extractor_element, issues, container_context):
    """Validates rules specific to CSS Selector Extractor."""
    element_name = _get_element_name(extractor_element)
    _validate_common_extractor_rules(extractor_element, issues, container_context)
    # print(f"DEBUG: Validating CSS specific rules for '{element_name}'")

    css_selector = _get_property_value(extractor_element, 'CssSelectorExtractor.selector')
    # print(f"DEBUG:   CSS Selector: '{css_selector}'")
    if not css_selector:
        _add_issue(issues, 'ERROR', 'Malformed Extractor Expression', element_name,
                   f"CSS Selector for '{element_name}' is empty.", container_context, element_name)


def _validate_boundary_extractor(extractor_element, issues, container_context):
    """Validates rules specific to Boundary Extractor."""
    element_name = _get_element_name(extractor_element)
    _validate_common_extractor_rules(extractor_element, issues, container_context)
    # print(f"DEBUG: Validating Boundary specific rules for '{element_name}'")

    left_boundary = _get_property_value(extractor_element, 'BoundaryExtractor.lboundary')
    right_boundary = _get_property_value(extractor_element, 'BoundaryExtractor.rboundary')
    # print(f"DEBUG:   Left Boundary: '{left_boundary}', Right Boundary: '{right_boundary}'")

    if not left_boundary:
        _add_issue(issues, 'ERROR', 'Malformed Extractor Expression', element_name,
                   f"Left Boundary for '{element_name}' is empty.", container_context, element_name)
    if not right_boundary:
        _add_issue(issues, 'ERROR', 'Malformed Extractor Expression', element_name,
                   f"Right Boundary for '{element_name}' is empty.", container_context, element_name)


def analyze_jmeter_script(root_element, enabled_validations):
    """
    Analyzes the JMeter script for Extractor and Variable Naming & Configuration Standards.
    Args:
        root_element (ET.Element): The root element of the JMeter JMX XML.
        enabled_validations (list): A list of validation option names enabled by the user.
    Returns:
        list: A list of dictionaries, each representing an issue found.
    """
    module_issues = []
    # Removed print statements for function calls and enabled validations.
    # print(f"\n--- DEBUG: analyze_jmeter_script for {THIS_VALIDATION_OPTION_NAME} called ---")
    # print(f"DEBUG: Enabled validations: {enabled_validations}")

    if THIS_VALIDATION_OPTION_NAME not in enabled_validations:
        # print(f"DEBUG: Validation '{THIS_VALIDATION_OPTION_NAME}' is not enabled. Skipping.")
        return module_issues

    current_thread_group_context = "Global/Unassigned"

    for element in root_element.iter():
        element_tag = element.tag
        element_name = _get_element_name(element)

        if element_tag in ['ThreadGroup', 'SetupThreadGroup', 'PostThreadGroup', 'TestFragment']:
            current_thread_group_context = element_name
            # print(f"DEBUG: Updated current context to: '{current_thread_group_context}' (Type: {element_tag})")

        if element_tag in ['RegexExtractor', 'JSONPostProcessor', 'XPathExtractor', 'CssSelectorExtractor',
                           'BoundaryExtractor']:
            # print(f"DEBUG:   Found extractor: Tag='{element_tag}', Name='{element_name}' within context '{current_thread_group_context}'")

            if element_tag == 'RegexExtractor':
                _validate_regex_extractor(element, module_issues, current_thread_group_context)
            elif element_tag == 'JSONPostProcessor':
                _validate_json_extractor(element, module_issues, current_thread_group_context)
            elif element_tag == 'XPathExtractor':
                _validate_xpath_extractor(element, module_issues, current_thread_group_context)
            elif element_tag == 'CssSelectorExtractor':
                _validate_css_extractor(element, module_issues, current_thread_group_context)
            elif element_tag == 'BoundaryExtractor':
                _validate_boundary_extractor(element, module_issues, current_thread_group_context)

    # print(f"--- DEBUG: analyze_jmeter_script for {THIS_VALIDATION_OPTION_NAME} finished. Found {len(module_issues)} issues. ---\n")
    return module_issues