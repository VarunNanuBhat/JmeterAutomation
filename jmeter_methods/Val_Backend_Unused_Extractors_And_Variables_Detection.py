import xml.etree.ElementTree as ET
import re

THIS_VALIDATION_OPTION_NAME = "Unused Extractors/Variables Detection"


def _get_element_name(element):
    return element.get('testname', 'Unnamed Element')


def _create_parent_map(root_element):
    parent_map = {c: p for p in root_element.iter() for c in p}
    return parent_map


def _get_thread_group_context(element, parent_map):
    ancestor = element
    while ancestor is not None and ancestor.tag != 'TestPlan':
        if ancestor.tag in ['ThreadGroup', 'SetupThreadGroup', 'PostThreadGroup', 'TestFragmentController']:
            return _get_element_name(ancestor)
        ancestor = parent_map.get(ancestor)
    return "Global/Unassigned"


def analyze_jmeter_script(root_element, enabled_validations):
    module_issues = []

    if THIS_VALIDATION_OPTION_NAME not in enabled_validations:
        return module_issues, []

    parent_map = _create_parent_map(root_element)

    # Step 1: Identify all variables defined in the script and their source elements
    defined_variables = {}
    duplicate_variables = set()

    def add_variable(var_name, var_type, element_name, thread_group_context, match_no=None):
        if var_name in defined_variables:
            duplicate_variables.add(var_name)
        defined_variables[var_name] = {'type': var_type, 'element_name': element_name,
                                       'thread_group': thread_group_context}
        if match_no:
            defined_variables[var_name]['match_no'] = match_no

    for element in root_element.iter():
        element_name = _get_element_name(element)
        thread_group_context = _get_thread_group_context(element, parent_map)

        # Variables from User-Defined Variables (UDVs)
        if element.tag == 'Arguments' and element.get('testclass') == 'Arguments':
            for arg in element.findall("./collectionProp[@name='Arguments.arguments']/elementProp"):
                var_name_prop = arg.find("./stringProp[@name='Argument.name']")
                if var_name_prop is not None and var_name_prop.text:
                    add_variable(var_name_prop.text, 'User-Defined Variable', element_name, thread_group_context)

        # Variables from Extractors (Post-Processors)
        elif element.tag in ['RegexExtractor', 'JSONPostProcessor', 'XPathExtractor', 'CssSelectorExtractor']:
            var_name_prop = None
            match_no_prop = None
            if element.tag == 'RegexExtractor':
                var_name_prop = element.find("./stringProp[@name='RegexExtractor.refname']")
                match_no_prop = element.find("./stringProp[@name='RegexExtractor.match_no']")
            elif element.tag == 'JSONPostProcessor':
                var_name_prop = element.find("./stringProp[@name='JSONPostProcessor.referenceNames']")
                # Note: Correctly handling 'match_numbers' and 'match_numbers' with an underscore as per user's feedback
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
                    if not var_name:
                        continue

                    match_no_val = match_no_prop.text if match_no_prop is not None else '1'
                    add_variable(var_name, element.tag, element_name, thread_group_context, match_no_val)

                    # Handle multiple matches
                    if match_no_val == '-1':
                        add_variable(f'{var_name}_1', element.tag, element_name, thread_group_context)
                        add_variable(f'{var_name}_matchNr', element.tag, element_name, thread_group_context)

        # Variables from CSV Data Set Config
        elif element.tag == 'CSVDataSet':
            var_names_str_prop = element.find("./stringProp[@name='CSVDataSet.variableNames']")
            if var_names_str_prop is not None and var_names_str_prop.text:
                var_names_str = var_names_str_prop.text
                for var_name in var_names_str.split(','):
                    if var_name:
                        add_variable(var_name.strip(), 'CSV Data Set Config', element_name, thread_group_context)

        # Variables from other elements
        elif element.tag == 'CounterConfig':
            var_name_prop = element.find("./stringProp[@name='CounterConfig.VarName']")
            if var_name_prop is not None and var_name_prop.text:
                add_variable(var_name_prop.text, 'Counter', element_name, thread_group_context)
        elif element.tag == 'RandomVariableConfig':
            var_name_prop = element.find("./stringProp[@name='RandomVariableConfig.variableName']")
            if var_name_prop is not None and var_name_prop.text:
                add_variable(var_name_prop.text, 'Random Variable', element_name, thread_group_context)

    # Step 2: Scan the entire script for variable references
    referenced_variables = set()
    variable_pattern = re.compile(r'\${([^}]+)}')

    for element in root_element.iter():
        if element.tag == 'HTTPSamplerProxy':
            url_prop = element.find("./stringProp[@name='HTTPSampler.path']")
            if url_prop is not None and url_prop.text:
                referenced_variables.update(variable_pattern.findall(url_prop.text))

            payload_prop = element.find("./stringProp[@name='RequestBody.content']")
            if payload_prop is not None and payload_prop.text:
                referenced_variables.update(variable_pattern.findall(payload_prop.text))

        for header in element.findall(
                "./elementProp[@name='HTTPHeaders']/collectionProp[@name='HeaderManager.headers']/elementProp"):
            header_value_prop = header.find("./stringProp[@name='Header.value']")
            if header_value_prop is not None and header_value_prop.text:
                referenced_variables.update(variable_pattern.findall(header_value_prop.text))

        for prop in element.findall(".//stringProp"):
            if prop.text and '${' in prop.text:
                referenced_variables.update(variable_pattern.findall(prop.text))

        for key, value in element.attrib.items():
            matches = variable_pattern.findall(value)
            for match in matches:
                referenced_variables.add(match)

    # Step 3: Compare and report issues

    # Heuristics to group related variables and check for usage
    used_variable_families = set()
    for ref_var in referenced_variables:
        if ref_var.endswith('_matchNr') or re.match(r'.+_\d+$', ref_var):
            base_name = re.sub(r'(_\d+|_matchNr)$', '', ref_var)
            used_variable_families.add(base_name)
        else:
            used_variable_families.add(ref_var)

    for var, details in defined_variables.items():
        if var in duplicate_variables:
            continue

        base_name = re.sub(r'(_\d+|_matchNr)$', '', var)

        # If any member of the family is used, consider all of them used
        if base_name in used_variable_families:
            continue

        issue_location = details['element_name']
        issue_thread_group = details['thread_group']
        var_type = details['type']
        issue_description = f"The variable '{var}' defined by a '{var_type}' is not referenced anywhere else in the script. Consider removing this unused variable."

        issue_type = f'Unused {var_type}' if 'Extractor' in var_type or 'PostProcessor' in var_type or 'PreProcessor' in var_type else 'Unused Variable'

        module_issues.append({
            'severity': 'INFO',
            'validation_option_name': THIS_VALIDATION_OPTION_NAME,
            'type': issue_type,
            'location': issue_location,
            'description': issue_description,
            'thread_group': issue_thread_group,
            'element_name': issue_location
        })

    # 3b. Report duplicate variables
    for var_name in duplicate_variables:
        description = f"The variable '{var_name}' is defined in multiple places. This can lead to unexpected behavior and is a violation of best practices."
        module_issues.append({
            'severity': 'WARNING',
            'validation_option_name': THIS_VALIDATION_OPTION_NAME,
            'type': 'Duplicate Variable',
            'location': var_name,
            'description': description,
            'thread_group': 'Multiple Locations',
            'element_name': var_name
        })

    return module_issues, []