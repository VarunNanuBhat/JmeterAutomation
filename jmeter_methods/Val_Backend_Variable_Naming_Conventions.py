import xml.etree.ElementTree as ET
import re

THIS_VALIDATION_OPTION_NAME = "Variable Naming Conventions"


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


def _is_camel_case(s):
    """
    Checks if a string follows camelCase:
    - Starts with a lowercase letter.
    - Contains only alphanumeric characters (letters and numbers).
    - Does not contain underscores, hyphens, or other special characters.
    """
    if not s:
        return False
    # Regex for camelCase: starts with lowercase letter, followed by zero or more alphanumeric characters.
    match = re.fullmatch(r'^[a-z][a-zA-Z0-9]*$', s)
    return True if match else False


def _get_element_name(element):
    """Helper to safely get the 'testname' attribute of an element."""
    return element.get('testname', 'Unnamed Element')


def _validate_user_defined_variable_name(variable_name, udv_element_name, container_context, issues_list):
    """Validates the naming convention for a User Defined Variable (u_camelCase)."""
    if not variable_name.startswith('u_'):
        _add_issue(issues_list, 'ERROR', 'UDV Naming Convention', udv_element_name,
                   f"User Defined Variable '{variable_name}' does not start with 'u_'.",
                   container_context, udv_element_name)
    else:
        camel_case_part = variable_name[2:]  # Part after 'u_'
        if not _is_camel_case(camel_case_part):
            _add_issue(issues_list, 'ERROR', 'UDV Naming Convention', udv_element_name,
                       f"User Defined Variable '{variable_name}' does not follow camelCase after 'u_'.",
                       container_context, udv_element_name)


def _validate_parameterization_variable_name(variable_name, csv_element_name, container_context, issues_list):
    """Validates the naming convention for a Parameterization Variable (p_camelCase)."""
    if not variable_name.startswith('p_'):
        _add_issue(issues_list, 'ERROR', 'Parameterization Naming Convention', csv_element_name,
                   f"Parameterization Variable '{variable_name}' does not start with 'p_'.",
                   container_context, csv_element_name)
    else:
        camel_case_part = variable_name[2:]  # Part after 'p_'
        if not _is_camel_case(camel_case_part):
            _add_issue(issues_list, 'ERROR', 'Parameterization Naming Convention', csv_element_name,
                       f"Parameterization Variable '{variable_name}' does not follow camelCase after 'p_'.",
                       container_context, csv_element_name)


def _validate_correlation_variable_name(variable_name, extractor_element_name, container_context, issues_list):
    """Validates the naming convention for a Correlated Variable (c_camelCase)."""
    if not variable_name.startswith('c_'):
        _add_issue(issues_list, 'ERROR', 'Correlation Naming Convention', extractor_element_name,
                   f"Correlated Variable '{variable_name}' does not start with 'c_'.",
                   container_context, extractor_element_name)
    else:
        camel_case_part = variable_name[2:]  # Part after 'c_'
        if not _is_camel_case(camel_case_part):
            _add_issue(issues_list, 'ERROR', 'Correlation Naming Convention', extractor_element_name,
                       f"Correlated Variable '{variable_name}' does not follow camelCase after 'c_'.",
                       container_context, extractor_element_name)


def analyze_jmeter_script(root_element, enabled_validations):
    """
    Analyzes the JMeter script to categorize and validate variable naming conventions.
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

        # --- Validate User Defined Variables ---
        if element_tag == 'Arguments' and element.get('testclass') == 'Arguments':
            args_prop = element.find("./collectionProp[@name='Arguments.arguments']")
            if args_prop is not None:
                arg_elements = args_prop.findall("./elementProp[@elementType='Argument']")
                for arg_element in arg_elements:
                    variable_name = arg_element.get('name')
                    if variable_name:
                        _validate_user_defined_variable_name(variable_name, element_name, current_thread_group_context,
                                                             module_issues)

        # --- Validate CSV Data Set Config Variables (Parameterization) ---
        elif element_tag == 'CSVDataSet' and element.get('testclass') == 'CSVDataSet':
            variable_names_prop = element.find("./stringProp[@name='variableNames']")
            if variable_names_prop is not None and variable_names_prop.text:
                csv_variables = [v.strip() for v in variable_names_prop.text.split(',') if v.strip()]
                for variable_name in csv_variables:
                    _validate_parameterization_variable_name(variable_name, element_name, current_thread_group_context,
                                                             module_issues)

        # --- Validate Correlated Variables (Extractors) ---
        elif element_tag == 'JSONPostProcessor' and element.get('testclass') == 'JSONPostProcessor':
            ref_names_prop = element.find("./stringProp[@name='JSONPostProcessor.referenceNames']")
            if ref_names_prop is not None and ref_names_prop.text:
                json_variables = [v.strip() for v in ref_names_prop.text.split(',') if v.strip()]
                for variable_name in json_variables:
                    _validate_correlation_variable_name(variable_name, element_name, current_thread_group_context, module_issues)

        elif element_tag == 'RegexExtractor' and element.get('testclass') == 'RegexExtractor':
            ref_name_prop = element.find("./stringProp[@name='RegexExtractor.refname']")
            if ref_name_prop is not None and ref_name_prop.text:
                variable_name = ref_name_prop.text.strip()
                _validate_correlation_variable_name(variable_name, element_name, current_thread_group_context, module_issues)

        elif element_tag == 'XPathExtractor' and element.get('testclass') == 'XPathExtractor':
            ref_name_prop = element.find("./stringProp[@name='XPathExtractor.refname']")
            if ref_name_prop is not None and ref_name_prop.text:
                variable_name = ref_name_prop.text.strip()
                _validate_correlation_variable_name(variable_name, element_name, current_thread_group_context, module_issues)

        elif element_tag == 'BoundaryExtractor' and element.get('testclass') == 'BoundaryExtractor':
            ref_name_prop = element.find("./stringProp[@name='BoundaryExtractor.refname']")
            if ref_name_prop is not None and ref_name_prop.text:
                variable_name = ref_name_prop.text.strip()
                _validate_correlation_variable_name(variable_name, element_name, current_thread_group_context, module_issues)

        elif element_tag == 'CssSelectorExtractor' and element.get('testclass') == 'CssSelectorExtractor':
            ref_name_prop = element.find("./stringProp[@name='CssSelectorExtractor.refname']")
            if ref_name_prop is not None and ref_name_prop.text:
                variable_name = ref_name_prop.text.strip()
                _validate_correlation_variable_name(variable_name, element_name, current_thread_group_context, module_issues)

        elif element_tag == 'JMSPathExtractor' and element.get('testclass') == 'JMSPathExtractor':
            ref_name_prop = element.find("./stringProp[@name='JMESPathExtractor.referenceName']")
            if ref_name_prop is not None and ref_name_prop.text:
                variable_name = ref_name_prop.text.strip()
                _validate_correlation_variable_name(variable_name, element_name, current_thread_group_context, module_issues)

    return module_issues