import xml.etree.ElementTree as ET
import re

THIS_VALIDATION_OPTION_NAME = "Variable Naming Conventions"

# --- Configuration for Serenity Domain Exception ---
# IMPORTANT: Replace "your-serenity-domain.com" with the actual domain of your Serenity API.
# Example: SERENITY_DATA_DOMAIN = "api.myserenitytool.com"
# Use the exact domain as it appears in your JMeter HTTP Request's "Server Name or IP" field.
SERENITY_DATA_DOMAIN = "wdprapps.serenity.com"  # Configured for Serenity domain


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
    # Tracks the domain of the most recently encountered HTTP Sampler
    current_http_sampler_domain = None

    for element in root_element.iter():
        element_tag = element.tag
        element_name = _get_element_name(element)

        # Update current thread group/context and reset sampler context for new major containers
        if element_tag in ['ThreadGroup', 'SetupThreadGroup', 'PostThreadGroup', 'TestFragment']:
            current_thread_group_context = element_name
            current_http_sampler_domain = None  # Reset sampler domain for new major logical blocks

        # Update current HTTP Sampler domain
        if element_tag == 'HTTPSamplerProxy':
            domain_prop = element.find("./stringProp[@name='HTTPSampler.domain']")
            if domain_prop is not None and domain_prop.text:
                current_http_sampler_domain = domain_prop.text.strip()
            else:
                current_http_sampler_domain = None  # Clear domain if not found or empty for this sampler

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

            # Determine if this extractor is under a "Serenity" data retrieval request
            is_serenity_extractor_source = False
            # Check if the current_http_sampler_domain exists and matches the SERENITY_DATA_DOMAIN
            if current_http_sampler_domain and current_http_sampler_domain == SERENITY_DATA_DOMAIN:
                is_serenity_extractor_source = True

            for variable_name in variable_names_to_check:
                if is_serenity_extractor_source:
                    _validate_parameterization_variable_name(variable_name, element_name, current_thread_group_context,
                                                             module_issues)
                else:
                    _validate_correlation_variable_name(variable_name, element_name, current_thread_group_context,
                                                        module_issues)

    return module_issues