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
    debug_messages = []

    if THIS_VALIDATION_OPTION_NAME not in enabled_validations:
        debug_messages.append(f"Validation '{THIS_VALIDATION_OPTION_NAME}' is not enabled. Skipping.")
        for msg in debug_messages:
            print(msg, flush=True)
        return module_issues, debug_messages

    debug_messages.append("\n--- Starting Unused Variable Detection ---")
    parent_map = _create_parent_map(root_element)

    # Step 1: Identify all variables defined in the script
    defined_variables = {}
    debug_messages.append("Step 1: Identifying defined variables...")
    for element in root_element.iter():
        element_name = _get_element_name(element)
        thread_group_context = _get_thread_group_context(element, parent_map)

        # --- Variables from User-Defined Variables (UDVs) ---
        if element.tag == 'Arguments' and element.get('testclass') == 'Arguments':
            debug_messages.append(f"Found 'Arguments' element: {element_name}")
            for arg in element.findall("./collectionProp[@name='Arguments.arguments']/elementProp"):
                var_name_prop = arg.find("./stringProp[@name='Argument.name']")
                if var_name_prop is not None and var_name_prop.text:
                    var_name = var_name_prop.text
                    defined_variables[var_name] = {'type': 'User-Defined Variable', 'element_name': element_name,
                                                   'thread_group': thread_group_context}
                    debug_messages.append(f"  - Defined UDV: {var_name}")

        # --- Variables from Extractors (Post-Processors) ---
        elif element.tag == 'RegexExtractor':
            debug_messages.append(f"Found 'RegexExtractor' element: {element_name}")
            var_name_prop = element.find("./stringProp[@name='RegexExtractor.refname']")
            if var_name_prop is not None and var_name_prop.text:
                var_name = var_name_prop.text
                defined_variables[var_name] = {'type': 'Regex Extractor', 'element_name': element_name,
                                               'thread_group': thread_group_context}
                debug_messages.append(f"  - Defined Regex Extractor variable: {var_name}")
        elif element.tag == 'JSONPostProcessor':
            # Search for JSONPostProcessor elements
            debug_messages.append(f"Found 'JSONPostProcessor' element: {element_name}")
            # Correctly find the reference names string
            var_names_str_prop = element.find("./stringProp[@name='JSONPostProcessor.referenceNames']")
            if var_names_str_prop is not None and var_names_str_prop.text:
                var_names_str = var_names_str_prop.text
                for var_name in var_names_str.split(';'):
                    if var_name:
                        defined_variables[var_name.strip()] = {'type': 'JSON Extractor', 'element_name': element_name,
                                                               'thread_group': thread_group_context}
                        debug_messages.append(f"  - Defined JSON Extractor variable: {var_name.strip()}")
        elif element.tag == 'XPathExtractor':
            debug_messages.append(f"Found 'XPathExtractor' element: {element_name}")
            var_name_prop = element.find("./stringProp[@name='XPathExtractor.refname']")
            if var_name_prop is not None and var_name_prop.text:
                var_name = var_name_prop.text
                defined_variables[var_name] = {'type': 'XPath Extractor', 'element_name': element_name,
                                               'thread_group': thread_group_context}
                debug_messages.append(f"  - Defined XPath Extractor variable: {var_name}")

        # --- Variables from CSV Data Set Config ---
        elif element.tag == 'CSVDataSet':
            debug_messages.append(f"Found 'CSVDataSet' element: {element_name}")
            var_names_str_prop = element.find("./stringProp[@name='CSVDataSet.variableNames']")
            if var_names_str_prop is not None and var_names_str_prop.text:
                var_names_str = var_names_str_prop.text
                for var_name in var_names_str.split(','):
                    if var_name:
                        defined_variables[var_name.strip()] = {'type': 'CSV Data Set Config',
                                                               'element_name': element_name,
                                                               'thread_group': thread_group_context}
                        debug_messages.append(f"  - Defined CSV variable: {var_name.strip()}")

        # --- Variables from other elements (Counter, Random Variable, etc.) ---
        elif element.tag == 'CounterConfig':
            debug_messages.append(f"Found 'CounterConfig' element: {element_name}")
            var_name_prop = element.find("./stringProp[@name='CounterConfig.VarName']")
            if var_name_prop is not None and var_name_prop.text:
                var_name = var_name_prop.text
                defined_variables[var_name] = {'type': 'Counter', 'element_name': element_name,
                                               'thread_group': thread_group_context}
                debug_messages.append(f"  - Defined Counter variable: {var_name}")
        elif element.tag == 'RandomVariableConfig':
            debug_messages.append(f"Found 'RandomVariableConfig' element: {element_name}")
            var_name_prop = element.find("./stringProp[@name='RandomVariableConfig.variableName']")
            if var_name_prop is not None and var_name_prop.text:
                var_name = var_name_prop.text
                defined_variables[var_name] = {'type': 'Random Variable', 'element_name': element_name,
                                               'thread_group': thread_group_context}
                debug_messages.append(f"  - Defined Random Variable: {var_name}")

    debug_messages.append(f"\nTotal variables defined: {len(defined_variables)}")
    debug_messages.append(f"Defined variables list: {list(defined_variables.keys())}")

    # Step 2: Scan the entire script for variable references
    referenced_variables = set()
    debug_messages.append("\nStep 2: Scanning for variable references...")
    variable_pattern = re.compile(r'\${([^}]+)}')

    for element in root_element.iter():
        element_name = _get_element_name(element)
        # Scan all text content within the element
        if element.text:
            matches = variable_pattern.findall(element.text)
            for match in matches:
                referenced_variables.add(match)
                debug_messages.append(f"  - Found reference to: {match} in element '{element_name}' (Text content)")

        # Scan all attribute values within the element
        for key, value in element.attrib.items():
            matches = variable_pattern.findall(value)
            for match in matches:
                referenced_variables.add(match)
                debug_messages.append(f"  - Found reference to: {match} in element '{element_name}' (Attribute: {key})")

        # Scan all stringProp values, as they hold the main content
        for prop in element.findall(".//stringProp"):
            if prop.text and '${' in prop.text:
                matches = variable_pattern.findall(prop.text)
                for match in matches:
                    referenced_variables.add(match)
                    debug_messages.append(f"  - Found reference to: {match} in stringProp in element '{element_name}'")

    debug_messages.append(f"\nTotal variables referenced: {len(referenced_variables)}")
    debug_messages.append(f"Referenced variables list: {list(referenced_variables)}")

    # Step 3: Compare and report unused variables
    debug_messages.append("\nStep 3: Comparing and reporting unused variables...")
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
            debug_messages.append(f"  - Found unused variable: {var}")

    if not module_issues:
        debug_messages.append("No unused variables found.")
    else:
        debug_messages.append(f"Found {len(module_issues)} unused variables.")

    debug_messages.append("--- Unused Variable Detection Finished ---")

    # Print debug messages to the console for easier copy-pasting
    for msg in debug_messages:
        print(msg, flush=True)

    return module_issues, debug_messages