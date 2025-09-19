import xml.etree.ElementTree as ET
import re

THIS_VALIDATION_OPTION_NAME = "Duplicate Extractors/Variable Conflicts"


def _get_element_name(element):
    """Retrieves the 'testname' attribute of a JMeter element."""
    return element.get('testname', 'Unnamed Element')


def _create_parent_map(root_element):
    """Creates a dictionary mapping each child element to its parent."""
    parent_map = {c: p for p in root_element.iter() for c in p}
    return parent_map


def _get_thread_group_context(element, parent_map):
    """Traverses up the XML tree to find the name of the parent Thread Group."""
    ancestor = element
    while ancestor is not None and ancestor.tag != 'TestPlan':
        if ancestor.tag in ['ThreadGroup', 'SetupThreadGroup', 'PostThreadGroup', 'TestFragmentController']:
            return _get_element_name(ancestor)
        ancestor = parent_map.get(ancestor)
    return "Global/Unassigned"


def analyze_jmeter_script(root_element, enabled_validations):
    """
    Analyzes a JMX script for duplicate variable definitions and redundant extractors.
    """
    module_issues = []

    if THIS_VALIDATION_OPTION_NAME not in enabled_validations:
        return module_issues, []

    parent_map = _create_parent_map(root_element)

    # Dictionary to track all variable definitions
    defined_variables = {}

    # Dictionary to track unique extractor signatures (for duplicate extractor check)
    extractor_signatures = {}

    for element in root_element.iter():
        element_name = _get_element_name(element)
        thread_group_context = _get_thread_group_context(element, parent_map)

        # --- Check for all variable definitions across the script ---
        variable_names = []
        element_type = element.tag

        # User Defined Variables
        if element.tag == 'Arguments' and element.get('testclass') == 'Arguments':
            element_type = 'User Defined Variables'
            for arg in element.findall("./collectionProp[@name='Arguments.arguments']/elementProp"):
                var_name_prop = arg.find("./stringProp[@name='Argument.name']")
                if var_name_prop is not None and var_name_prop.text:
                    variable_names.append(var_name_prop.text.strip())

        # Extractors (Post-Processors)
        elif element.tag in ['RegexExtractor', 'JSONPostProcessor', 'XPathExtractor', 'CssSelectorExtractor']:
            var_name_prop = None
            if element.tag == 'RegexExtractor':
                var_name_prop = element.find("./stringProp[@name='RegexExtractor.refname']")
            elif element.tag == 'JSONPostProcessor':
                var_name_prop = element.find("./stringProp[@name='JSONPostProcessor.referenceNames']")
            elif element.tag == 'XPathExtractor':
                var_name_prop = element.find("./stringProp[@name='XPathExtractor.refname']")
            elif element.tag == 'CssSelectorExtractor':
                var_name_prop = element.find("./stringProp[@name='CssSelectorExtractor.refname']")

            if var_name_prop is not None and var_name_prop.text:
                for var_name in re.split(';|,', var_name_prop.text):
                    if var_name:
                        variable_names.append(var_name.strip())

        # CSV Data Set Config
        elif element.tag == 'CSVDataSet':
            element_type = 'CSV Data Set Config'
            var_names_str_prop = element.find("./stringProp[@name='CSVDataSet.variableNames']")
            if var_names_str_prop is not None and var_names_str_prop.text:
                for var_name in var_names_str_prop.text.split(','):
                    if var_name:
                        variable_names.append(var_name.strip())

        # Counter and Random Variable
        elif element.tag == 'CounterConfig':
            element_type = 'Counter'
            var_name_prop = element.find("./stringProp[@name='CounterConfig.VarName']")
            if var_name_prop is not None and var_name_prop.text:
                variable_names.append(var_name_prop.text.strip())
        elif element.tag == 'RandomVariableConfig':
            element_type = 'Random Variable'
            var_name_prop = element.find("./stringProp[@name='RandomVariableConfig.variableName']")
            if var_name_prop is not None and var_name_prop.text:
                variable_names.append(var_name_prop.text.strip())

        # Store all found variable definitions
        for var_name in variable_names:
            if var_name not in defined_variables:
                defined_variables[var_name] = []
            defined_variables[var_name].append({
                'element_name': element_name,
                'element_type': element_type,
                'thread_group': thread_group_context
            })

        # --- Check for duplicate extractors (same path/pattern) ---
        if element.tag in ['RegexExtractor', 'JSONPostProcessor', 'XPathExtractor', 'CssSelectorExtractor']:
            extractor_path = None
            if element.tag == 'RegexExtractor':
                extractor_path = element.findtext("./stringProp[@name='RegexExtractor.regex']")
            elif element.tag == 'JSONPostProcessor':
                extractor_path = element.findtext("./stringProp[@name='JSONPostProcessor.jsonPathExpr']")
            elif element.tag == 'XPathExtractor':
                extractor_path = element.findtext("./stringProp[@name='XPathExtractor.xpathQuery']")
            elif element.tag == 'CssSelectorExtractor':
                extractor_path = element.findtext("./stringProp[@name='CssSelectorExtractor.selector']")

            if extractor_path:
                # Get parent sampler/controller for more specific context
                parent_element = _get_thread_group_context(element, parent_map)

                # Create a unique signature for the extractor
                signature = f"{element.tag}_{extractor_path}_{parent_element}"

                if signature not in extractor_signatures:
                    extractor_signatures[signature] = []
                extractor_signatures[signature].append(element_name)

    # --- Generate Issues from the collected data ---

    # 1. Report duplicate variable name conflicts
    for var_name, sources in defined_variables.items():
        if len(sources) > 1:
            source_info = "\n".join(
                [f"- '{s['element_name']}' ({s['element_type']}) in '{s['thread_group']}'" for s in sources])
            issue_description = (
                f"The variable **'{var_name}'** is defined multiple times. "
                f"This can lead to values being overwritten and cause runtime errors. "
                f"Sources found:\n{source_info}"
            )
            module_issues.append({
                'severity': 'ERROR',
                'validation_option_name': THIS_VALIDATION_OPTION_NAME,
                'type': 'Duplicate Variable Definition',
                'location': ', '.join([s['element_name'] for s in sources]),
                'description': issue_description,
                'thread_group': sources[0]['thread_group'] if sources else 'N/A',
                'element_name': var_name
            })

    # 2. Report duplicate extractor paths/signatures
    for signature, elements in extractor_signatures.items():
        if len(elements) > 1:
            extractor_type, extractor_path, _ = signature.split('_', 2)
            issue_description = (
                f"Multiple identical `{extractor_type}` extractors were found. "
                f"They all use the same path/pattern: `{extractor_path}`. "
                f"This is redundant and may indicate a copy-paste error. "
                f"Found in elements: {', '.join(elements)}"
            )
            module_issues.append({
                'severity': 'WARNING',
                'validation_option_name': THIS_VALIDATION_OPTION_NAME,
                'type': 'Duplicate Extractor',
                'location': ', '.join(elements),
                'description': issue_description,
                'thread_group': 'N/A',
                'element_name': f"Duplicate {extractor_type}"
            })

    return module_issues, []