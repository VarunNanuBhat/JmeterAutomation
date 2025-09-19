import xml.etree.ElementTree as ET
import re

THIS_VALIDATION_OPTION_NAME = "Unextracted Variables Detection"

def _get_element_name(element):
    """
    Retrieves the 'testname' attribute of a JMeter element, or returns 'Unnamed Element'.
    """
    return element.get('testname', 'Unnamed Element')

def _create_parent_map(root_element):
    """
    Creates a dictionary mapping each child element to its parent for easy traversal.
    """
    parent_map = {c: p for p in root_element.iter() for c in p}
    return parent_map

def _get_thread_group_context(element, parent_map):
    """
    Traverses up the XML tree to find the name of the parent Thread Group.
    """
    ancestor = element
    while ancestor is not None and ancestor.tag != 'TestPlan':
        if ancestor.tag in ['ThreadGroup', 'SetupThreadGroup', 'PostThreadGroup', 'TestFragmentController']:
            return _get_element_name(ancestor)
        ancestor = parent_map.get(ancestor)
    return "Global/Unassigned"

def analyze_jmeter_script(root_element, enabled_validations):
    """
    Analyzes a JMX script to find variables that are referenced but not extracted or defined.
    Returns a list of issues found.
    """
    module_issues = []

    # If this validation is not enabled, return an empty list immediately.
    if THIS_VALIDATION_OPTION_NAME not in enabled_validations:
        return module_issues

    parent_map = _create_parent_map(root_element)

    # Step 1: Identify all variables defined in the script
    defined_variables = set()

    for element in root_element.iter():
        # Variables from User-Defined Variables (UDVs)
        if element.tag == 'Arguments' and element.get('testclass') == 'Arguments':
            for arg in element.findall("./collectionProp[@name='Arguments.arguments']/elementProp"):
                var_name_prop = arg.find("./stringProp[@name='Argument.name']")
                if var_name_prop is not None and var_name_prop.text:
                    defined_variables.add(var_name_prop.text.strip())

        # Variables from Extractors (Post-Processors)
        elif element.tag in ['RegexExtractor', 'JSONPostProcessor', 'XPathExtractor', 'CssSelectorExtractor']:
            var_name_prop = None
            match_no_prop = None
            if element.tag == 'RegexExtractor':
                var_name_prop = element.find("./stringProp[@name='RegexExtractor.refname']")
                match_no_prop = element.find("./stringProp[@name='RegexExtractor.match_no']")
            elif element.tag == 'JSONPostProcessor':
                var_name_prop = element.find("./stringProp[@name='JSONPostProcessor.referenceNames']")
                match_no_prop = element.find("./stringProp[@name='JSONPostProcessor.match_numbers']") or element.find(
                    "./stringProp[@name='JSONPostProcessor.matchNumbers']")
            elif element.tag == 'XPathExtractor':
                var_name_prop = element.find("./stringProp[@name='XPathExtractor.refname']")
                match_no_prop = element.find("./stringProp[@name='XPathExtractor.match_number']")
            elif element.tag == 'CssSelectorExtractor':
                var_name_prop = element.find("./stringProp[@name='CssSelectorExtractor.refname']")
                match_no_prop = element.find("./stringProp[@name='CssSelectorExtractor.match_number']")

            if var_name_prop is not None and var_name_prop.text:
                var_names_str = var_name_prop.text
                separator = ',' if element.tag == 'CssSelectorExtractor' else ';'
                for var_name in var_names_str.split(separator):
                    var_name = var_name.strip()
                    if var_name:
                        defined_variables.add(var_name)
                        match_no_val = match_no_prop.text if match_no_prop is not None else '1'
                        if match_no_val == '-1':
                            defined_variables.add(f'{var_name}_1')
                            defined_variables.add(f'{var_name}_matchNr')

        # Variables from CSV Data Set Config
        elif element.tag == 'CSVDataSet':
            var_names_str_prop = element.find("./stringProp[@name='CSVDataSet.variableNames']")
            if var_names_str_prop is not None and var_names_str_prop.text:
                var_names_str = var_names_str_prop.text
                for var_name in var_names_str.split(','):
                    if var_name:
                        defined_variables.add(var_name.strip())

        # Variables from other elements (e.g., Counters, Random Variables)
        elif element.tag == 'CounterConfig':
            var_name_prop = element.find("./stringProp[@name='CounterConfig.VarName']")
            if var_name_prop is not None and var_name_prop.text:
                defined_variables.add(var_name_prop.text.strip())
        elif element.tag == 'RandomVariableConfig':
            var_name_prop = element.find("./stringProp[@name='RandomVariableConfig.variableName']")
            if var_name_prop is not None and var_name_prop.text:
                defined_variables.add(var_name_prop.text.strip())

    # Step 2: Scan the entire script for variable references
    referenced_variables = set()
    variable_pattern = re.compile(r'\${([^}]+)}')

    for element in root_element.iter():
        # Check element attributes for variable references
        for key, value in element.attrib.items():
            referenced_variables.update(variable_pattern.findall(value))

        # Check all string properties for variable references
        for prop in element.findall(".//stringProp"):
            if prop.text and '${' in prop.text:
                referenced_variables.update(variable_pattern.findall(prop.text))

    # Step 3: Compare and report issues
    unextracted_variables = referenced_variables - defined_variables

    # Filter out references to numbered variables (e.g., `myVar_1`) if their base variable (`myVar`) is defined.
    filtered_unextracted = set()
    for var in unextracted_variables:
        if re.match(r'.*_\d+$', var) and re.sub(r'_\d+$', '', var) in defined_variables:
            continue
        filtered_unextracted.add(var)

    for var in sorted(list(filtered_unextracted)): # Sorting for consistent output
        issue_description = f"The variable '{var}' is used in the script but has not been defined or extracted. This could cause a runtime error."

        # Find the first element where the variable is used for a more specific location in the report.
        element_where_used = None
        for element in root_element.iter():
            # Use ET.tostring for a comprehensive check of the element's content
            if f'${{{var}}}'.encode('utf-8') in ET.tostring(element, encoding='utf-8', method='xml'):
                element_where_used = element
                break

        element_name = _get_element_name(element_where_used) if element_where_used is not None else "Unknown"
        thread_group = _get_thread_group_context(element_where_used, parent_map) if element_where_used is not None else "Unknown"

        module_issues.append({
            'severity': 'ERROR',
            'validation_option_name': THIS_VALIDATION_OPTION_NAME,
            'type': 'Unextracted Variable',
            'location': element_name,
            'description': issue_description,
            'thread_group': thread_group,
            'element_name': element_name,
            'key_name': '',  # No specific key name for this issue type
            'hardcoded_value': var,
            'hardcoded_segment': var,
            'element_obj': element_where_used
        })

    # The function now returns a list of issues directly, without a debug log.
    return module_issues, []