import xml.etree.ElementTree as ET
import re

THIS_VALIDATION_OPTION_NAME = "Variable Naming Conventions"

# --- Configuration for Serenity Domain Exception ---
# The exact domain of your Serenity API.
SERENITY_DATA_DOMAIN = "wdprapps.serenity.com"


# ----------------------------------------------------


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


def _resolve_udv_value(variable_name, root_element):
    """
    Attempts to find the literal value of a User Defined Variable (UDV)
    by searching through Arguments elements in the JMX.

    IMPORTANT CAVEAT: This is a simplistic lookup for static values only.
    It does NOT fully replicate JMeter's complex variable scoping rules
    (e.g., Test Plan vs. Thread Group scope). It will find the first literal
    definition encountered. It CANNOT resolve variables set by JMeter functions
    (__P, __V, etc.), dynamic scripting elements (JSR223), or other extractors.
    """
    for element in root_element.iter('Arguments'):
        if element.get('testclass') == 'Arguments':
            args_prop = element.find("./collectionProp[@name='Arguments.arguments']")
            if args_prop is not None:
                for arg_element in args_prop.findall("./elementProp[@elementType='Argument']"):
                    if arg_element.get('name') == variable_name:
                        value_prop = arg_element.find("./stringProp[@name='Argument.value']")
                        if value_prop is not None and value_prop.text:
                            return value_prop.text.strip()
    return None


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


def _validate_parameterization_variable_name(variable_name, source_element_name, container_context, issues_list):
    """Validates the naming convention for a Parameterization Variable (p_camelCase)."""
    if not variable_name.startswith('p_'):
        _add_issue(issues_list, 'ERROR', 'Parameterization Naming Convention', source_element_name,
                   f"Parameterization Variable '{variable_name}' does not start with 'p_'.",
                   container_context, source_element_name)
    else:
        camel_case_part = variable_name[2:]  # Part after 'p_'
        if not _is_camel_case(camel_case_part):
            _add_issue(issues_list, 'ERROR', 'Parameterization Naming Convention', source_element_name,
                       f"Parameterization Variable '{variable_name}' does not follow camelCase after 'p_'.",
                       container_context, source_element_name)


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
    # Flag to indicate if the current HTTP Sampler's domain (literal or via UDV) is a Serenity source
    current_http_sampler_is_serenity_source = False

    for element in root_element.iter():
        element_tag = element.tag
        element_name = _get_element_name(element)

        # Update current thread group/context and reset sampler context for new major containers
        if element_tag in ['ThreadGroup', 'SetupThreadGroup', 'PostThreadGroup', 'TestFragment']:
            current_thread_group_context = element_name
            current_http_sampler_is_serenity_source = False  # Reset flag for new logical blocks

        # Determine if the current HTTP Sampler is a Serenity data source
        if element_tag == 'HTTPSamplerProxy':
            current_http_sampler_is_serenity_source = False  # Reset flag for new sampler
            domain_prop = element.find("./stringProp[@name='HTTPSampler.domain']")
            if domain_prop is not None and domain_prop.text:
                domain_value = domain_prop.text.strip()

                # 1. Check for direct domain match
                if domain_value == SERENITY_DATA_DOMAIN:
                    current_http_sampler_is_serenity_source = True

                # 2. Check if it's a variable reference and attempt to resolve its value
                else:
                    # Check if it's a variable reference like ${variableName}
                    match_var_syntax = re.fullmatch(r'\$\{(\w+)\}', domain_value)
                    if match_var_syntax:
                        variable_name_in_domain = match_var_syntax.group(1)
                        # Attempt to resolve the variable's value from UDVs
                        resolved_domain = _resolve_udv_value(variable_name_in_domain, root_element)

                        # If the value is resolved and matches the Serenity domain
                        if resolved_domain and resolved_domain == SERENITY_DATA_DOMAIN:
                            current_http_sampler_is_serenity_source = True
            # else: current_http_sampler_is_serenity_source remains False if no domain or empty

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

        # --- Validate Variables from Extractors (Conditional p_ or c_) ---
        extractor_ref_name_prop = None
        is_json_post_processor = False

        if element_tag == 'JSONPostProcessor' and element.get('testclass') == 'JSONPostProcessor':
            extractor_ref_name_prop = element.find("./stringProp[@name='JSONPostProcessor.referenceNames']")
            is_json_post_processor = True
        elif element_tag == 'RegexExtractor' and element.get('testclass') == 'RegexExtractor':
            extractor_ref_name_prop = element.find("./stringProp[@name='RegexExtractor.refname']")
        elif element_tag == 'XPathExtractor' and element.get('testclass') == 'XPathExtractor':
            extractor_ref_name_prop = element.find("./stringProp[@name='XPathExtractor.refname']")
        elif element_tag == 'BoundaryExtractor' and element.get('testclass') == 'BoundaryExtractor':
            extractor_ref_name_prop = element.find("./stringProp[@name='BoundaryExtractor.refname']")
        elif element_tag == 'CssSelectorExtractor' and element.get('testclass') == 'CssSelectorExtractor':
            extractor_ref_name_prop = element.find("./stringProp[@name='CssSelectorExtractor.refname']")
        elif element_tag == 'JMSPathExtractor' and element.get('testclass') == 'JMSPathExtractor':
            extractor_ref_name_prop = element.find("./stringProp[@name='JMESPathExtractor.referenceName']")

        if extractor_ref_name_prop is not None and extractor_ref_name_prop.text:
            variable_names_to_check = []
            if is_json_post_processor:
                variable_names_to_check = [v.strip() for v in extractor_ref_name_prop.text.split(',') if v.strip()]
            else:
                variable_names_to_check.append(extractor_ref_name_prop.text.strip())

            # Apply validation based on whether the current sampler is a Serenity data source
            for variable_name in variable_names_to_check:
                if current_http_sampler_is_serenity_source:
                    _validate_parameterization_variable_name(variable_name, element_name, current_thread_group_context,
                                                             module_issues)
                else:
                    _validate_correlation_variable_name(variable_name, element_name, current_thread_group_context,
                                                        module_issues)

    return module_issues