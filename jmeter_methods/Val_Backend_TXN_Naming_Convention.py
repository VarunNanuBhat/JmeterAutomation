import xml.etree.ElementTree as ET
import re
import os

# Global list to store issues.
issues = []
# Global variable to store the root element of the JMX tree.
root = None

# Define the specific validation option name this module is responsible for
# This will be used to categorize issues in the report.
THIS_VALIDATION_OPTION_NAME = "Naming Convention (TXN_NN_Desc)"


def parse_jmeter_xml(file_path):
    """
    Parses the JMeter JMX XML file.
    Appends parsing errors to the global 'issues' list.
    """
    try:
        tree = ET.parse(file_path)
        parsed_root = tree.getroot()
        return parsed_root
    except ET.ParseError as e:
        issues.append({
            'severity': 'ERROR',
            'validation_option_name': THIS_VALIDATION_OPTION_NAME,
            'type': 'XML Parsing',
            'location': 'JMX File',
            'description': f"Failed to parse JMX file: {e}. Ensure it's a valid XML.",
            'thread_group': 'N/A'
        })
        return None
    except FileNotFoundError:
        issues.append({
            'severity': 'ERROR',
            'validation_option_name': THIS_VALIDATION_OPTION_NAME,
            'type': 'File Not Found',
            'location': 'JMX File',
            'description': f"JMX file not found at: {file_path}",
            'thread_group': 'N/A'
        })
        return None


def validate_transaction_name(transaction_name, thread_group_name):
    """
    Validates if a transaction name follows the 'TXN_NN_Description' format.
    Appends naming convention errors to the global 'issues' list.
    Returns the step number (NN) as an int if valid, otherwise None.
    """
    pattern = r"^TXN_(\d{2})_.*"
    match = re.match(pattern, transaction_name)

    if not match:
        if not transaction_name.startswith("TXN_"):
            issues.append({
                'severity': 'ERROR',
                'validation_option_name': THIS_VALIDATION_OPTION_NAME,
                'type': 'Naming Convention',
                'location': f"Transaction Controller '{transaction_name}'",
                'description': "Transaction Controller name must start with 'TXN_'.",
                'thread_group': thread_group_name
            })
        elif not re.match(r"^TXN_\d{2}_.*", transaction_name):
            issues.append({
                'severity': 'ERROR',
                'validation_option_name': THIS_VALIDATION_OPTION_NAME,
                'type': 'Naming Convention',
                'location': f"Transaction Controller '{transaction_name}'",
                'description': "Transaction Controller name must strictly follow 'TXN_NN_Description' format (NN=exactly two digits, Description must be present).",
                'thread_group': thread_group_name
            })
        return None

    return int(match.group(1))


def validate_transaction_sequence(transactions, thread_group_name):
    """
    Validates the sequence and uniqueness of transaction step numbers within a thread group.
    Appends sequence validation errors to the global 'issues' list.
    """
    if not transactions:
        return

    # Sort transactions by their step number, filtering out those without a valid step number
    valid_txns = sorted([txn for txn in transactions if txn['step_number'] is not None],
                        key=lambda x: x['step_number'])

    seen_steps = set()
    last_step = 0

    for txn_info in valid_txns:
        current_step = txn_info['step_number']
        transaction_name = txn_info['name']

        if current_step in seen_steps:
            original_name = next((t['original_name_for_duplicate'] for t in valid_txns
                                  if t['step_number'] == current_step and t['element'] != txn_info['element']), None)
            if original_name is None:
                original_name = f"TXN_{current_step:02d}_[Unknown]"

            issues.append({
                'severity': 'ERROR',
                'validation_option_name': THIS_VALIDATION_OPTION_NAME,
                'type': 'Sequence Validation',
                'location': f"Transaction Controller '{transaction_name}'",
                'description': f"Duplicate transaction step number 'TXN_{current_step:02d}' found. Already seen as '{original_name}'. Each transaction step number within a Thread Group must be unique.",
                'thread_group': thread_group_name
            })
        else:
            seen_steps.add(current_step)
            txn_info['original_name_for_duplicate'] = transaction_name

        if current_step > last_step + 1 and last_step != 0:
            for missing_step in range(last_step + 1, current_step):
                if missing_step not in seen_steps:
                    issues.append({
                        'severity': 'ERROR',
                        'validation_option_name': THIS_VALIDATION_OPTION_NAME,
                        'type': 'Sequence Validation',
                        'location': f"Thread Group '{thread_group_name}'",
                        'description': f"Missing transaction step 'TXN_{missing_step:02d}'. Steps must be contiguous.",
                        'thread_group': thread_group_name
                    })
        last_step = current_step


def resolve_module_controller_target(module_controller_elem, root_element):
    """
    Resolves the target element of a Module Controller by traversing the JMX structure.
    Returns (resolved_element, its_parent_hashtree, its_index_in_parent) or None.
    """
    collection_prop = module_controller_elem.find(".//collectionProp[@name='ModuleController.node_path']")
    if collection_prop is None:
        return None

    node_path_elements = collection_prop.findall('stringProp')
    if not node_path_elements:
        return None

    path_parts = [s.text for s in node_path_elements if s.text]

    if not path_parts:
        return None

    cleaned_path_parts = [part.strip() for part in path_parts]

    current_container_ht = None
    start_index_for_traversal = 0

    # Step 1: Find the Test Plan and its top-level hashTree if specified in path
    if cleaned_path_parts[0] == 'Test Plan':
        test_plan_name_in_path = cleaned_path_parts[1] if len(cleaned_path_parts) > 1 else None

        jmeter_test_plan_ht = root_element.find('hashTree')
        if jmeter_test_plan_ht is None:
            issues.append({
                'severity': 'ERROR',
                'validation_option_name': THIS_VALIDATION_OPTION_NAME,
                'type': 'Structure',
                'location': 'JMeter Test Plan',
                'description': "Root element has no hashTree child. Invalid JMX.",
                'thread_group': 'N/A'
            })
            return None

        test_plan_elem = None
        children_of_jmeter_test_plan_ht = list(jmeter_test_plan_ht)
        for j, child_elem in enumerate(children_of_jmeter_test_plan_ht):
            if child_elem.tag == 'TestPlan' and (
                    test_plan_name_in_path is None or child_elem.get('testname') == test_plan_name_in_path):
                test_plan_elem = child_elem
                if j + 1 < len(children_of_jmeter_test_plan_ht) and children_of_jmeter_test_plan_ht[
                    j + 1].tag == 'hashTree':
                    current_container_ht = children_of_jmeter_test_plan_ht[j + 1]
                    start_index_for_traversal = 2 if test_plan_name_in_path else 1
                    break
                else:
                    issues.append({
                        'severity': 'ERROR',
                        'validation_option_name': THIS_VALIDATION_OPTION_NAME,
                        'type': 'Structure',
                        'location': 'JMeter Test Plan',
                        'description': "TestPlan element found but not followed by a hashTree for its children (Thread Groups, Test Fragments). Invalid JMX structure.",
                        'thread_group': 'N/A'
                    })
                    return None
        if test_plan_elem is None:
            return None
    else:
        jmeter_test_plan_direct_hashtree = root_element.find('hashTree')
        if jmeter_test_plan_direct_hashtree is None:
            issues.append({
                'severity': 'ERROR',
                'type': 'Structure',
                'location': 'JMeter Test Plan',
                'description': "Root element has no hashTree. Cannot start traversal for Module Controller.",
                'thread_group': 'N/A'
            })
            return None

        temp_top_level_controllers_hashTree = None
        children_of_jmeter_test_plan_direct_hashtree = list(jmeter_test_plan_direct_hashtree)
        for j, elem in enumerate(children_of_jmeter_test_plan_direct_hashtree):
            if elem.tag == 'TestPlan':
                if j + 1 < len(children_of_jmeter_test_plan_direct_hashtree) and \
                        children_of_jmeter_test_plan_direct_hashtree[j + 1].tag == 'hashTree':
                    temp_top_level_controllers_hashTree = children_of_jmeter_test_plan_direct_hashtree[j + 1]
                    break
        current_container_ht = temp_top_level_controllers_hashTree

    if current_container_ht is None:
        return None

    target_elem_at_current_level = None
    parent_of_target = None
    index_of_target_in_parent = -1

    remaining_path_parts = cleaned_path_parts[start_index_for_traversal:]

    # Step 2: Traverse the remaining path parts
    for i, part_name in enumerate(remaining_path_parts):
        found_part = False

        children_of_current_container = list(current_container_ht)
        for j, elem in enumerate(children_of_current_container):
            if elem.get('testname') == part_name:
                target_elem_at_current_level = elem
                parent_of_target = current_container_ht
                index_of_target_in_parent = j
                found_part = True

                if i < len(remaining_path_parts) - 1:
                    if j + 1 < len(children_of_current_container) and children_of_current_container[
                        j + 1].tag == 'hashTree':
                        current_container_ht = children_of_current_container[j + 1]
                    else:
                        return None
                break

        if not found_part:
            return None

    return (target_elem_at_current_level, parent_of_target, index_of_target_in_parent)


def collect_logical_txns(element_or_hashtree, tg_name_for_report, collected_list, visited_elements):
    """
    Recursively collects Transaction Controllers and their nested children for validation.
    Also handles Module Controllers by resolving their targets.
    visited_elements set is used to prevent infinite loops in case of circular references.
    """

    if element_or_hashtree.tag == 'hashTree':
        children_of_current_hashtree = list(element_or_hashtree)
        idx = 0
        while idx < len(children_of_current_hashtree):
            current_elem = children_of_current_hashtree[idx]

            if current_elem in visited_elements:
                idx += 1
                continue

            is_transaction_controller = (current_elem.tag == 'TransactionController' or \
                                         (current_elem.get(
                                             'testclass') == 'org.apache.jmeter.control.TransactionController'))

            is_module_controller = (current_elem.tag == 'ModuleController' or \
                                    (current_elem.get('testclass') == 'org.apache.jmeter.control.ModuleController'))

            container_controller_tags = ['TestFragmentController', 'ThreadGroup', 'LoopController', 'SimpleController',
                                         'IfController', 'WhileController', 'OnceOnlyController',
                                         'ThroughputController', 'RandomController', 'SwitchController',
                                         'CriticalSectionController', 'InterleaveController', 'RandomOrderController',
                                         'ForEachController', 'TransactionController']

            if is_transaction_controller:
                txn_name = current_elem.get('testname')
                if txn_name:
                    step_number = validate_transaction_name(txn_name, tg_name_for_report)
                    collected_list.append({
                        'name': txn_name,
                        'element': current_elem,
                        'step_number': step_number,
                        'source_type': 'direct',
                        'original_name_for_duplicate': txn_name
                    })
                    visited_elements.add(current_elem)

                if idx + 1 < len(children_of_current_hashtree) and children_of_current_hashtree[
                    idx + 1].tag == 'hashTree':
                    collect_logical_txns(children_of_current_hashtree[idx + 1], tg_name_for_report, collected_list,
                                         visited_elements)
                    idx += 1

            elif is_module_controller:
                resolved_target_info = resolve_module_controller_target(current_elem, globals()['root'])

                if resolved_target_info is not None:
                    resolved_target_elem, parent_of_resolved_target, idx_of_resolved_target = resolved_target_info

                    visited_elements.add(current_elem)

                    is_resolved_txn_controller = (resolved_target_elem.tag == 'TransactionController' or \
                                                  (resolved_target_elem.get(
                                                      'testclass') == 'org.apache.jmeter.control.TransactionController'))

                    children_hashtree_of_resolved_target = None
                    if idx_of_resolved_target != -1 and \
                            idx_of_resolved_target + 1 < len(list(parent_of_resolved_target)) and \
                            list(parent_of_resolved_target)[idx_of_resolved_target + 1].tag == 'hashTree':
                        children_hashtree_of_resolved_target = list(parent_of_resolved_target)[
                            idx_of_resolved_target + 1]

                    if is_resolved_txn_controller:
                        if resolved_target_elem not in [tc['element'] for tc in collected_list]:
                            txn_name = resolved_target_elem.get('testname')
                            step_number = validate_transaction_name(txn_name, tg_name_for_report)
                            collected_list.append({'element': resolved_target_elem, 'source_type': 'module',
                                                   'module_name': current_elem.get('testname'),
                                                   'source_name': tg_name_for_report,
                                                   'name': txn_name,
                                                   'step_number': step_number,
                                                   'original_name_for_duplicate': txn_name})
                            visited_elements.add(resolved_target_elem)

                        if children_hashtree_of_resolved_target is not None:
                            collect_logical_txns(children_hashtree_of_resolved_target, tg_name_for_report,
                                                 collected_list, visited_elements)

                    elif resolved_target_elem.tag in container_controller_tags:
                        if children_hashtree_of_resolved_target is not None:
                            temp_collected_from_module = []
                            collect_logical_txns(children_hashtree_of_resolved_target, tg_name_for_report,
                                                 temp_collected_from_module, visited_elements)
                            collected_list.extend(temp_collected_from_module)
                            visited_elements.add(resolved_target_elem)
                        else:
                            issues.append({
                                'severity': 'WARNING',
                                'validation_option_name': THIS_VALIDATION_OPTION_NAME,
                                'type': 'Module Controller',
                                'location': f"Module Controller '{current_elem.get('testname')}' in Thread Group '{tg_name_for_report}'",
                                'description': f"Module Controller points to a container element '{resolved_target_elem.get('testname')}' ({resolved_target_elem.tag}) which has no inner elements (no sibling hashTree). No transactions collected from this target.",
                                'thread_group': tg_name_for_report
                            })

                    else:
                        issues.append({
                            'severity': 'WARNING',
                            'validation_option_name': THIS_VALIDATION_OPTION_NAME,
                            'type': 'Module Controller',
                            'location': f"Module Controller '{current_elem.get('testname')}' in Thread Group '{tg_name_for_report}'",
                            'description': f"Module Controller points to an element '{resolved_target_elem.get('testname')}' ({resolved_target_elem.tag}) that is not a Transaction Controller and does not contain transaction elements. It will not be included in transaction sequence validation.",
                            'thread_group': tg_name_for_report
                        })
                else:
                    issues.append({
                        'severity': 'WARNING',
                        'validation_option_name': THIS_VALIDATION_OPTION_NAME,
                        'type': 'Module Controller',
                        'location': f"Module Controller '{current_elem.get('testname')}' in Thread Group '{tg_name_for_report}'",
                        'description': "Could not resolve target for Module Controller. Sequence validation for this TG might be incomplete (Target not found).",
                        'thread_group': tg_name_for_report
                    })
                idx += 1

            elif current_elem.tag in container_controller_tags and current_elem not in visited_elements:
                visited_elements.add(current_elem)
                if idx + 1 < len(children_of_current_hashtree) and children_of_current_hashtree[
                    idx + 1].tag == 'hashTree':
                    collect_logical_txns(children_of_current_hashtree[idx + 1], tg_name_for_report, collected_list,
                                         visited_elements)
                    idx += 1
                idx += 1
            else:
                idx += 1
    else:
        pass


def analyze_jmeter_script(root_element, selected_validations_list):
    """
    Main function to analyze the JMeter script for naming and sequence conventions.
    Populates the global 'issues' list based on whether 'Naming Convention (TXN_NN_Desc)' is selected.
    """
    global root
    root = root_element

    # Master toggle check for this module's validations
    if THIS_VALIDATION_OPTION_NAME not in selected_validations_list:
        global issues
        issues = []
        return

    jmeter_test_plan_direct_hashtree = root_element.find('hashTree')
    if jmeter_test_plan_direct_hashtree is None:
        issues.append({
            'severity': 'ERROR',
            'validation_option_name': THIS_VALIDATION_OPTION_NAME,
            'type': 'Structure',
            'location': 'JMeter Test Plan',
            'description': "Root 'jmeterTestPlan' has no child 'hashTree'. Invalid JMX structure.",
            'thread_group': 'N/A'
        })
        return

    top_level_controllers_hashTree = None
    test_plan_found_and_processed = False

    children_of_jmeter_test_plan_direct_hashtree = list(jmeter_test_plan_direct_hashtree)
    for i, elem in enumerate(children_of_jmeter_test_plan_direct_hashtree):
        if elem.tag == 'TestPlan':
            if i + 1 < len(children_of_jmeter_test_plan_direct_hashtree) and \
                    children_of_jmeter_test_plan_direct_hashtree[i + 1].tag == 'hashTree':
                top_level_controllers_hashTree = children_of_jmeter_test_plan_direct_hashtree[i + 1]
                test_plan_found_and_processed = True
                break
            else:
                issues.append({
                    'severity': 'ERROR',
                    'validation_option_name': THIS_VALIDATION_OPTION_NAME,
                    'type': 'Structure',
                    'location': 'JMeter Test Plan',
                    'description': "TestPlan element found but not followed by a hashTree for its children (Thread Groups, Test Fragments). Invalid JMX structure.",
                    'thread_group': 'N/A'
                })
                return

    if not test_plan_found_and_processed or top_level_controllers_hashTree is None:
        issues.append({
            'severity': 'ERROR',
            'validation_option_name': THIS_VALIDATION_OPTION_NAME,
            'type': 'Structure',
            'location': 'JMeter Test Plan',
            'description': "Could not locate the primary hashTree containing Thread Groups or Test Fragments. JMX structure might be unexpected.",
            'thread_group': 'N/A'
        })
        return

    thread_groups_data = {}

    children_of_top_level_controllers_hashTree = list(top_level_controllers_hashTree)
    idx = 0
    while idx < len(children_of_top_level_controllers_hashTree):
        top_level_elem = children_of_top_level_controllers_hashTree[idx]

        if top_level_elem.tag in ['ThreadGroup', 'SetupThreadGroup', 'PostThreadGroup', 'TestFragmentController']:
            tg_name = top_level_elem.get('testname')
            if tg_name is None:
                tg_name = f"Unnamed {top_level_elem.tag}"

            thread_groups_data[tg_name] = []
            visited_elements_in_tg = set()

            tg_children_hashtree = None
            if idx + 1 < len(children_of_top_level_controllers_hashTree) and children_of_top_level_controllers_hashTree[
                idx + 1].tag == 'hashTree':
                tg_children_hashtree = children_of_top_level_controllers_hashTree[idx + 1]
                collect_logical_txns(tg_children_hashtree, tg_name, thread_groups_data[tg_name], visited_elements_in_tg)
                idx += 1
            else:
                issues.append({
                    'severity': 'WARNING',
                    'validation_option_name': THIS_VALIDATION_OPTION_NAME,
                    'type': 'Structure',
                    'location': f"Thread Group/Test Fragment '{tg_name}'",
                    'description': f"Expected a sibling 'hashTree' for {top_level_elem.tag} '{tg_name}' to contain its elements, but none was found. No elements will be validated within this container.",
                    'thread_group': tg_name
                })
        else:
            # For other top-level elements that are not Thread Groups/Test Fragments,
            # we still want to ensure they are processed for naming if they are controllers
            # and their children are recursively validated.

            # Re-using the logic from collect_logical_txns for non-Transaction Controllers
            # that might appear at the top level (e.g. a LoopController directly under Test Plan hashTree)
            txn_naming_pattern = r"^TXN_(\d{2})_.*"
            # List of tags for other common container controllers (excluding TransactionController itself)
            other_container_controller_tags = ['LoopController', 'SimpleController', 'IfController', 'WhileController',
                                               'OnceOnlyController', 'ThroughputController', 'RandomController',
                                               'SwitchController', 'CriticalSectionController', 'InterleaveController',
                                               'RandomOrderController', 'ForEachController']

            if top_level_elem.tag in other_container_controller_tags:
                controller_name = top_level_elem.get('testname')
                if controller_name and re.match(txn_naming_pattern, controller_name):
                    issues.append({
                        'severity': 'WARNING',
                        'validation_option_name': THIS_VALIDATION_OPTION_NAME,
                        'type': 'Naming Convention',
                        'location': f"Top-level Controller '{controller_name}' ({top_level_elem.tag})",
                        'description': f"Non-Transaction Controller names (e.g., Loop, Simple, While) should not follow the 'TXN_NN_Description' format. This format is reserved exclusively for Transaction Controllers.",
                        'thread_group': 'N/A'  # Top-level controllers might not have an immediate TG
                    })
                # Recursively process children of top-level non-TG controllers
                if idx + 1 < len(children_of_top_level_controllers_hashTree) and \
                        children_of_top_level_controllers_hashTree[idx + 1].tag == 'hashTree':
                    # Need a placeholder thread group name for reporting if this is not within a TG
                    temp_tg_name = top_level_elem.get('testname') or f"Top-Level {top_level_elem.tag}"
                    temp_collected_list = []  # Don't need to add to thread_groups_data, just collect errors
                    temp_visited_elements = set()
                    collect_logical_txns(children_of_top_level_controllers_hashTree[idx + 1], temp_tg_name,
                                         temp_collected_list, temp_visited_elements)
                    idx += 1  # Advance past the hashTree

            # Advance for all other elements not specifically handled above
            if idx + 1 < len(children_of_top_level_controllers_hashTree) and children_of_top_level_controllers_hashTree[
                idx + 1].tag == 'hashTree':
                idx += 1  # Advance past hashTree if present for the current element
        idx += 1

    for tg_name, transactions in thread_groups_data.items():
        if transactions:
            validate_transaction_sequence(transactions, tg_name)