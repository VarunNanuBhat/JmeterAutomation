import xml.etree.ElementTree as ET
import re

THIS_VALIDATION_OPTION_NAME = "Unextracted Variables Detection"


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

    # Step 1: Identify all variables defined in the script
    defined_variables = set()

    for element in root_element.iter():
        element_name = _get_element_name(element)
        thread_group_context = _get_thread_group_context(element, parent_map)

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

        # Variables from other elements
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
            referenced_variables.update(matches)

    # Step 3: Compare and report issues
    unextracted_variables = referenced_variables - defined_variables

    # Heuristic to filter out references to numbered variables that are part of a defined multiple-match variable
    filtered_unextracted = set()
    for var in unextracted_variables:
        if re.match(r'.*_\d+$', var) and re.sub(r'_\d+$', '', var) in defined_variables:
            continue
        filtered_unextracted.add(var)

    for var in filtered_unextracted:
        issue_description = f"The variable '{var}' is used in the script but has not been defined or extracted. This could cause a runtime error."

        # Find the element where the variable is used for a more specific location
        element_where_used = None
        for element in root_element.iter():
            text_content = ET.tostring(element, encoding='unicode')
            if f'${{{var}}}' in text_content:
                element_where_used = element
                break

        element_name = _get_element_name(element_where_used) if element_where_used is not None else "Unknown"
        thread_group = _get_thread_group_context(element_where_used,
                                                 parent_map) if element_where_used is not None else "Unknown"

        module_issues.append({
            'severity': 'ERROR',
            'validation_option_name': THIS_VALIDATION_OPTION_NAME,
            'type': 'Unextracted Variable',
            'location': element_name,
            'description': issue_description,
            'thread_group': thread_group,
            'element_name': element_name
        })

    return module_issues, []