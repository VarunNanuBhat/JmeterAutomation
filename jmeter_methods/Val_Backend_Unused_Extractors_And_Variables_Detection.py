import xml.etree.ElementTree as ET
import re

THIS_VALIDATION_OPTION_NAME = "Unused Extractors/Variables Detection"


def _get_element_name(element):
    return element.get('testname', 'Unnamed Element')


def analyze_jmeter_script(root_element, enabled_validations):
    module_issues = []

    if THIS_VALIDATION_OPTION_NAME not in enabled_validations:
        return module_issues, []

    defined_variables = {}

    # PASS 1: Find all DEFINED variables with their correct location
    last_controller_name = "Global/Unassigned"

    for element in root_element.iter():
        element_tag = element.tag
        element_name = _get_element_name(element)

        if element_tag in ['ThreadGroup', 'SetupThreadGroup', 'PostThreadGroup', 'TestFragmentController',
                           'TransactionController']:
            last_controller_name = element_name
            continue

        thread_group_context = last_controller_name

        if element_tag == 'Arguments' and element.get('testclass') == 'Arguments':
            for arg in element.findall("./collectionProp[@name='Arguments.arguments']/elementProp"):
                var_name_prop = arg.find("./stringProp[@name='Argument.name']")
                if var_name_prop is not None and var_name_prop.text:
                    var_name = var_name_prop.text.strip()
                    if var_name:
                        defined_variables[var_name] = {'type': 'User-Defined Variable', 'element_name': element_name,
                                                       'thread_group': thread_group_context}

        elif element.tag in ['RegexExtractor', 'JSONPostProcessor', 'XPathExtractor', 'CssSelectorExtractor']:
            var_name_prop = None
            match_no_prop = None
            if element.tag == 'RegexExtractor':
                var_name_prop = element.find("./stringProp[@name='RegexExtractor.refname']")
                match_no_prop = element.find("./stringProp[@name='RegexExtractor.match_no']")
            elif element.tag == 'JSONPostProcessor':
                var_name_prop = element.find("./stringProp[@name='JSONPostProcessor.referenceNames']")
                match_no_prop = element.find("./stringProp[@name='JSONPostProcessor.matchNumbers']") or element.find(
                    "./stringProp[@name='JSONPostProcessor.match_numbers']")
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
                        defined_variables[var_name] = {'type': element.tag, 'element_name': element_name,
                                                       'thread_group': thread_group_context}
                        match_no_val = match_no_prop.text if match_no_prop is not None else '1'
                        if match_no_val == '-1':
                            defined_variables[f'{var_name}_1'] = {'type': element.tag, 'element_name': element_name,
                                                                  'thread_group': thread_group_context}
                            defined_variables[f'{var_name}_matchNr'] = {'type': element.tag,
                                                                        'element_name': element_name,
                                                                        'thread_group': thread_group_context}

        elif element.tag == 'CSVDataSet':
            var_names_str_prop = element.find("./stringProp[@name='CSVDataSet.variableNames']")
            if var_names_str_prop is not None and var_names_str_prop.text:
                for var_name in var_names_str_prop.text.split(','):
                    var_name = var_name.strip()
                    if var_name:
                        defined_variables[var_name] = {'type': 'CSV Data Set Config', 'element_name': element_name,
                                                       'thread_group': thread_group_context}

        elif element.tag == 'CounterConfig':
            var_name_prop = element.find("./stringProp[@name='CounterConfig.VarName']")
            if var_name_prop is not None and var_name_prop.text:
                var_name = var_name_prop.text.strip()
                if var_name:
                    defined_variables[var_name] = {'type': 'Counter', 'element_name': element_name,
                                                   'thread_group': thread_group_context}

        elif element.tag == 'RandomVariableConfig':
            var_name_prop = element.find("./stringProp[@name='RandomVariableConfig.variableName']")
            if var_name_prop is not None and var_name_prop.text:
                var_name = var_name_prop.text.strip()
                if var_name:
                    defined_variables[var_name] = {'type': 'Random Variable', 'element_name': element_name,
                                                   'thread_group': thread_group_context}

    # PASS 2: Find all REFERENCED variables across the entire script
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

    # FINAL STEP: Compare defined vs. referenced variables
    used_variable_families = set()
    for ref_var in referenced_variables:
        if ref_var.endswith('_matchNr') or re.match(r'.+_\d+$', ref_var):
            base_name = re.sub(r'(_\d+|_matchNr)$', '', ref_var)
            used_variable_families.add(base_name)
        else:
            used_variable_families.add(ref_var)

    for var, details in defined_variables.items():
        base_name = re.sub(r'(_\d+|_matchNr)$', '', var)

        is_used = base_name in used_variable_families or var in referenced_variables

        if not is_used:
            issue_location = details['element_name']
            issue_thread_group = details['thread_group']
            var_type = details['type']
            issue_description = f"The variable '{var}' defined by a '{var_type}' is not referenced anywhere else in the script. Consider removing this unused variable."

            issue_type = f'Unused {var_type}' if 'Extractor' in var_type or 'PostProcessor' in var_type else 'Unused Variable'

            module_issues.append({
                'severity': 'INFO',
                'validation_option_name': THIS_VALIDATION_OPTION_NAME,
                'type': issue_type,
                'location': issue_location,
                'description': issue_description,
                'thread_group': issue_thread_group,
                'element_name': issue_location
            })

    return module_issues, []