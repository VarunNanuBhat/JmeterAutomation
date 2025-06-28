import xml.etree.ElementTree as ET
import re

THIS_VALIDATION_OPTION_NAME = "Variable Naming Conventions"


def _add_issue(issues_list, severity, issue_type, location, description, thread_group="N/A", element_name="N/A"):
    """Helper function to add a consistent issue dictionary to the list."""
    # Keeping prints for debugging, remove in production if too verbose
    print(f"\n--- ISSUE DETECTED ({THIS_VALIDATION_OPTION_NAME}) ---")
    print(f"Severity: {severity}")
    print(f"Type: {issue_type}")
    print(f"Location: {location}")
    print(f"Element Name: {element_name}")
    print(f"Thread Group/Context: {thread_group}")
    print(f"Description: {description}")
    print(f"-----------------------------------\n")
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
    print(f"DEBUG: _is_camel_case called with: '{s}'")
    if not s:
        print(f"DEBUG: _is_camel_case returned False (empty string)")
        return False
    # Regex for camelCase: starts with lowercase letter, followed by zero or more alphanumeric characters.
    match = re.fullmatch(r'^[a-z][a-zA-Z0-9]*$', s)
    if match:
        print(f"DEBUG: _is_camel_case returned True (match)")
        return True
    else:
        print(f"DEBUG: _is_camel_case returned False (no match)")
        return False


def _get_element_name(element):
    """Helper to safely get the 'testname' attribute of an element."""
    return element.get('testname', 'Unnamed Element')


def _validate_user_defined_variable_name(variable_name, udv_element_name, container_context, issues_list):
    """Validates the naming convention for a User Defined Variable (u_camelCase)."""
    print(f"DEBUG: Validating UDV: '{variable_name}' from element '{udv_element_name}'")
    if not variable_name.startswith('u_'):
        print(f"DEBUG: UDV '{variable_name}' - Prefix 'u_' MISSING.")
        _add_issue(issues_list, 'ERROR', 'UDV Naming Convention', udv_element_name,
                   f"User Defined Variable '{variable_name}' does not start with 'u_'.",
                   container_context, udv_element_name)
    else:
        camel_case_part = variable_name[2:]  # Part after 'u_'
        print(f"DEBUG: UDV '{variable_name}' - Checking camelCase part: '{camel_case_part}'")
        if not _is_camel_case(camel_case_part):
            print(f"DEBUG: UDV '{variable_name}' - CamelCase Suffix VIOLATED.")
            _add_issue(issues_list, 'ERROR', 'UDV Naming Convention', udv_element_name,
                       f"User Defined Variable '{variable_name}' does not follow camelCase after 'u_'.",
                       container_context, udv_element_name)
        else:
            print(f"DEBUG: UDV '{variable_name}' - Valid.")


def _validate_parameterization_variable_name(variable_name, csv_element_name, container_context, issues_list):
    """Validates the naming convention for a Parameterization Variable (p_camelCase)."""
    print(f"DEBUG: Validating Param Var: '{variable_name}' from element '{csv_element_name}'")
    if not variable_name.startswith('p_'):
        print(f"DEBUG: Param Var '{variable_name}' - Prefix 'p_' MISSING.")
        _add_issue(issues_list, 'ERROR', 'Parameterization Naming Convention', csv_element_name,
                   f"Parameterization Variable '{variable_name}' does not start with 'p_'.",
                   container_context, csv_element_name)
    else:
        camel_case_part = variable_name[2:]  # Part after 'p_'
        print(f"DEBUG: Param Var '{variable_name}' - Checking camelCase part: '{camel_case_part}'")
        if not _is_camel_case(camel_case_part):
            print(f"DEBUG: Param Var '{variable_name}' - CamelCase Suffix VIOLATED.")
            _add_issue(issues_list, 'ERROR', 'Parameterization Naming Convention', csv_element_name,
                       f"Parameterization Variable '{variable_name}' does not follow camelCase after 'p_'.",
                       container_context, csv_element_name)
        else:
            print(f"DEBUG: Param Var '{variable_name}' - Valid.")


def _validate_correlation_variable_name(variable_name, extractor_element_name, container_context, issues_list):
    """Validates the naming convention for a Correlated Variable (c_camelCase)."""
    print(f"DEBUG: Validating Correlated Var: '{variable_name}' from extractor '{extractor_element_name}'")
    if not variable_name.startswith('c_'):
        print(f"DEBUG: Correlated Var '{variable_name}' - Prefix 'c_' MISSING.")
        _add_issue(issues_list, 'ERROR', 'Correlation Naming Convention', extractor_element_name,
                   f"Correlated Variable '{variable_name}' does not start with 'c_'.",
                   container_context, extractor_element_name)
    else:
        camel_case_part = variable_name[2:]  # Part after 'c_'
        print(f"DEBUG: Correlated Var '{variable_name}' - Checking camelCase part: '{camel_case_part}'")
        if not _is_camel_case(camel_case_part):
            print(f"DEBUG: Correlated Var '{variable_name}' - CamelCase Suffix VIOLATED.")
            _add_issue(issues_list, 'ERROR', 'Correlation Naming Convention', extractor_element_name,
                       f"Correlated Variable '{variable_name}' does not follow camelCase after 'c_'.",
                       container_context, extractor_element_name)
        else:
            print(f"DEBUG: Correlated Var '{variable_name}' - Valid.")


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
    print(f"\n--- DEBUG: Entering {THIS_VALIDATION_OPTION_NAME} Validation Module ---")
    print(f"DEBUG: Enabled Validations passed: {enabled_validations}")

    if THIS_VALIDATION_OPTION_NAME not in enabled_validations:
        print(f"DEBUG: Validation '{THIS_VALIDATION_OPTION_NAME}' is NOT enabled. Skipping analysis.")
        return module_issues

    print(f"DEBUG: Validation '{THIS_VALIDATION_OPTION_NAME}' IS enabled. Proceeding with analysis.")
    current_thread_group_context = "Global/Unassigned"
    element_count = 0

    for element in root_element.iter():
        element_count += 1
        element_tag = element.tag
        element_name = _get_element_name(element)
        # print(f"DEBUG: Processing element: Tag='{element_tag}', Name='{element_name}'")

        # Update current thread group/context
        if element_tag in ['ThreadGroup', 'SetupThreadGroup', 'PostThreadGroup', 'TestFragment']:
            current_thread_group_context = element_name
            print(f"DEBUG: Context updated to: '{current_thread_group_context}' (Type: {element_tag})")

        # --- Validate User Defined Variables ---
        if element_tag == 'Arguments' and element.get('testclass') == 'Arguments':
            print(
                f"DEBUG: FOUND User Defined Variables (Arguments type, Testclass='Arguments') element: '{element_name}'")
            args_prop = element.find("./collectionProp[@name='Arguments.arguments']")
            if args_prop is not None:
                print(f"DEBUG: Found Arguments.arguments collectionProp for UDV.")
                arg_elements = args_prop.findall("./elementProp[@elementType='Argument']")
                if not arg_elements:
                    print(f"DEBUG: No Argument elements found within UDV '{element_name}'.")
                for arg_element in arg_elements:
                    variable_name = arg_element.get('name')
                    if variable_name:
                        print(f"DEBUG: Extracting UDV variable name: '{variable_name}'")
                        _validate_user_defined_variable_name(variable_name, element_name, current_thread_group_context,
                                                             module_issues)
                    else:
                        print(f"DEBUG: Encountered an empty UDV variable name in '{element_name}'.")
            else:
                print(f"DEBUG: No Arguments.arguments collectionProp found in '{element_name}' for UDV.")

        # --- Validate CSV Data Set Config Variables (Parameterization) ---
        elif element_tag == 'CSVDataSet' and element.get('testclass') == 'CSVDataSet':
            print(f"DEBUG: Found CSVDataSet element (Testclass='CSVDataSet'): '{element_name}'")
            variable_names_prop = element.find("./stringProp[@name='variableNames']")
            if variable_names_prop is not None and variable_names_prop.text:
                print(f"DEBUG: Found variableNames prop. Text: '{variable_names_prop.text}'")
                csv_variables = [v.strip() for v in variable_names_prop.text.split(',') if v.strip()]
                if not csv_variables:
                    print(f"DEBUG: No variable names found after splitting CSV string.")
                for variable_name in csv_variables:
                    print(f"DEBUG: Extracting CSV variable name: '{variable_name}'")
                    _validate_parameterization_variable_name(variable_name, element_name, current_thread_group_context,
                                                             module_issues)
            else:
                print(f"DEBUG: No 'variableNames' stringProp or empty text found in '{element_name}'.")

        # --- Validate Correlated Variables (Extractors) ---
        elif element_tag == 'JSONPostProcessor' and element.get('testclass') == 'JSONPostProcessor':
            print(f"DEBUG: Found JSONPostProcessor: '{element_name}'")
            ref_names_prop = element.find("./stringProp[@name='JSONPostProcessor.referenceNames']")
            if ref_names_prop is not None and ref_names_prop.text:
                json_variables = [v.strip() for v in ref_names_prop.text.split(',') if v.strip()]
                for variable_name in json_variables:
                    print(f"DEBUG: Extracting JSON variable name: '{variable_name}'")
                    _validate_correlation_variable_name(variable_name, element_name, current_thread_group_context,
                                                        module_issues)
            else:
                print(f"DEBUG: No 'JSONPostProcessor.referenceNames' found or empty in '{element_name}'.")

        elif element_tag == 'RegexExtractor' and element.get('testclass') == 'RegexExtractor':
            print(f"DEBUG: Found RegexExtractor: '{element_name}'")
            ref_name_prop = element.find("./stringProp[@name='RegexExtractor.refname']")
            if ref_name_prop is not None and ref_name_prop.text:
                variable_name = ref_name_prop.text.strip()
                print(f"DEBUG: Extracting Regex variable name: '{variable_name}'")
                _validate_correlation_variable_name(variable_name, element_name, current_thread_group_context,
                                                    module_issues)
            else:
                print(f"DEBUG: No 'RegexExtractor.refname' found or empty in '{element_name}'.")

        elif element_tag == 'XPathExtractor' and element.get('testclass') == 'XPathExtractor':
            print(f"DEBUG: Found XPathExtractor: '{element_name}'")
            ref_name_prop = element.find("./stringProp[@name='XPathExtractor.refname']")
            if ref_name_prop is not None and ref_name_prop.text:
                variable_name = ref_name_prop.text.strip()
                print(f"DEBUG: Extracting XPath variable name: '{variable_name}'")
                _validate_correlation_variable_name(variable_name, element_name, current_thread_group_context,
                                                    module_issues)
            else:
                print(f"DEBUG: No 'XPathExtractor.refname' found or empty in '{element_name}'.")

        # Added Boundary Extractor
        elif element_tag == 'BoundaryExtractor' and element.get('testclass') == 'BoundaryExtractor':
            print(f"DEBUG: Found BoundaryExtractor: '{element_name}'")
            ref_name_prop = element.find("./stringProp[@name='BoundaryExtractor.refname']")
            if ref_name_prop is not None and ref_name_prop.text:
                variable_name = ref_name_prop.text.strip()
                print(f"DEBUG: Extracting Boundary variable name: '{variable_name}'")
                _validate_correlation_variable_name(variable_name, element_name, current_thread_group_context,
                                                    module_issues)
            else:
                print(f"DEBUG: No 'BoundaryExtractor.refname' found or empty in '{element_name}'.")

        # Added CSS/JQuery Extractor
        elif element_tag == 'CssSelectorExtractor' and element.get('testclass') == 'CssSelectorExtractor':
            print(f"DEBUG: Found CssSelectorExtractor: '{element_name}'")
            ref_name_prop = element.find("./stringProp[@name='CssSelectorExtractor.refname']")
            if ref_name_prop is not None and ref_name_prop.text:
                variable_name = ref_name_prop.text.strip()
                print(f"DEBUG: Extracting CSS/JQuery variable name: '{variable_name}'")
                _validate_correlation_variable_name(variable_name, element_name, current_thread_group_context,
                                                    module_issues)
            else:
                print(f"DEBUG: No 'CssSelectorExtractor.refname' found or empty in '{element_name}'.")

        # Added JSON JMESPath Extractor
        elif element_tag == 'JMSPathExtractor' and element.get('testclass') == 'JMSPathExtractor':
            print(f"DEBUG: Found JMSPathExtractor: '{element_name}'")
            # Note: JMESPath Extractor uses 'JMESPathExtractor.referenceName'
            ref_name_prop = element.find("./stringProp[@name='JMESPathExtractor.referenceName']")
            if ref_name_prop is not None and ref_name_prop.text:
                variable_name = ref_name_prop.text.strip()
                print(f"DEBUG: Extracting JMESPath variable name: '{variable_name}'")
                _validate_correlation_variable_name(variable_name, element_name, current_thread_group_context,
                                                    module_issues)
            else:
                print(f"DEBUG: No 'JMESPathExtractor.referenceName' found or empty in '{element_name}'.")

    print(f"\n--- DEBUG: Exiting {THIS_VALIDATION_OPTION_NAME} Validation Module ---")
    print(f"DEBUG: Total elements processed: {element_count}")
    print(f"DEBUG: Final issues count for {THIS_VALIDATION_OPTION_NAME}: {len(module_issues)}")
    return module_issues