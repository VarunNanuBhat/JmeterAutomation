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
        return module_issues

    parent_map = _create_parent_map(root_element)

    # Step 1: Identify all variables defined in the script
    defined_variables = {}
    for element in root_element.iter():
        element_name = _get_element_name(element)
        thread_group_context = _get_thread_group_context(element, parent_map)

        # --- Variables from User-Defined Variables (UDVs) ---
        if element.tag == 'Arguments' and element.get('testclass') == 'Arguments':
            for arg in element.findall("./collectionProp[@name='Arguments.arguments']/elementProp"):
                var_name = arg.findtext("./stringProp[@name='Argument.name']")
                if var_name:
                    defined_variables[var_name] = {
                        'type': 'User-Defined Variable',
                        'element_name': element_name,
                        'thread_group': thread_group_context
                    }

        # --- Variables from Extractors (Post-Processors) ---
        elif element.tag == 'RegexExtractor':
            var_name = element.findtext("./stringProp[@name='RegexExtractor.refname']")
            if var_name:
                defined_variables[var_name] = {
                    'type': 'Regex Extractor',
                    'element_name': element_name,
                    'thread_group': thread_group_context
                }
        elif element.tag == 'JSONPostProcessor':
            var_names_str = element.findtext("./stringProp[@name='JSONPostProcessor.referenceNames']")
            if var_names_str:
                for var_name in var_names_str.split(';'):
                    if var_name:
                        defined_variables[var_name.strip()] = {
                            'type': 'JSON Extractor',
                            'element_name': element_name,
                            'thread_group': thread_group_context
                        }
        elif element.tag == 'XPathExtractor':
            var_name = element.findtext("./stringProp[@name='XPathExtractor.refname']")
            if var_name:
                defined_variables[var_name] = {
                    'type': 'XPath Extractor',
                    'element_name': element_name,
                    'thread_group': thread_group_context
                }

        # --- Variables from CSV Data Set Config ---
        elif element.tag == 'CSVDataSet':
            var_names_str = element.findtext("./stringProp[@name='CSVDataSet.variableNames']")
            if var_names_str:
                for var_name in var_names_str.split(','):
                    if var_name:
                        defined_variables[var_name.strip()] = {
                            'type': 'CSV Data Set Config',
                            'element_name': element_name,
                            'thread_group': thread_group_context
                        }

        # --- Variables from other elements (Counter, Random Variable, etc.) ---
        elif element.tag in ['CounterConfig', 'RandomVariableConfig']:
            var_name = element.findtext("./stringProp[@name='CounterConfig.VarName']") or \
                       element.findtext("./stringProp[@name='RandomVariableConfig.variableName']")
            if var_name:
                defined_variables[var_name] = {
                    'type': element.tag.replace('Config', ''),
                    'element_name': element_name,
                    'thread_group': thread_group_context
                }

    # Step 2: Scan the entire script for variable references
    referenced_variables = set()
    for element in root_element.iter():
        for prop in element.iter('stringProp'):
            if prop.text and '${' in prop.text:
                matches = re.findall(r'\${([^}]+)}', prop.text)
                for match in matches:
                    referenced_variables.add(match)

        # Check for variables in raw post bodies
        if element.tag == 'HTTPSamplerProxy':
            args_prop = element.find("./elementProp[@name='HTTPsampler.Arguments']")
            if args_prop is not None and element.findtext("./boolProp[@name='HTTPSampler.postBodyRaw']") == 'true':
                raw_body = args_prop.findtext("./collectionProp/elementProp/stringProp[@name='Argument.value']")
                if raw_body and '${' in raw_body:
                    matches = re.findall(r'\${([^}]+)}', raw_body)
                    for match in matches:
                        referenced_variables.add(match)

    # Step 3: Compare and report unused variables
    for var, details in defined_variables.items():
        if var not in referenced_variables:
            issue_location = details['element_name']
            issue_thread_group = details['thread_group']
            var_type = details['type']
            issue_description = f"The variable '{var}' defined by a '{var_type}' is not referenced anywhere else in the script. Consider removing this unused variable."

            module_issues.append({
                'severity': 'INFO',
                'validation_option_name': THIS_VALIDATION_OPTION_NAME,
                'type': f'Unused {var_type}',
                'location': issue_location,
                'description': issue_description,
                'thread_group': issue_thread_group,
                'element_name': issue_location
            })

    return module_issues