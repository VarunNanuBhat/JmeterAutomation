import xml.etree.ElementTree as ET
import re
import os

# Define the specific validation option name this module is responsible for
THIS_VALIDATION_OPTION_NAME = "Naming Convention (TXN_NN_Desc)"


# --- IMPORTANT: The parse_jmeter_xml function is removed, as validator_report_page.py handles parsing centrally. ---

def validate_transaction_name(transaction_name, thread_group_name, module_issues_list):
    """
    Validates if a transaction name follows the 'TXN_NN_Description' format.
    Appends naming convention errors to the passed module_issues_list.
    Returns the step number (NN) as an int if valid, otherwise None.
    """
    pattern = r"^TXN_(\d{2})_.*"
    match = re.match(pattern, transaction_name)

    if not match:
        if not transaction_name.startswith("TXN_"):
            module_issues_list.append({
                'severity': 'ERROR',
                'validation_option_name': THIS_VALIDATION_OPTION_NAME,
                'type': 'Naming Convention',
                'location': f"Transaction Controller '{transaction_name}'",
                'description': "Transaction Controller name must start with 'TXN_'.",
                'thread_group': thread_group_name
            })
        elif not re.match(r"^TXN_\d{2}_.*", transaction_name):
            module_issues_list.append({
                'severity': 'ERROR',
                'validation_option_name': THIS_VALIDATION_OPTION_NAME,
                'type': 'Naming Convention',
                'location': f"Transaction Controller '{transaction_name}'",
                'description': "Transaction Controller name must strictly follow 'TXN_NN_Description' format (NN=exactly two digits, Description must be present).",
                'thread_group': thread_group_name
            })
        return None

    return int(match.group(1))


def validate_transaction_sequence(transactions, thread_group_name, module_issues_list):
    """
    Validates the sequence and uniqueness of transaction step numbers within a thread group.
    Appends sequence validation errors to the passed module_issues_list.
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

            module_issues_list.append({
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
                    module_issues_list.append({
                        'severity': 'ERROR',
                        'validation_option_name': THIS_VALIDATION_OPTION_NAME,
                        'type': 'Sequence Validation',
                        'location': f"Thread Group '{thread_group_name}'",
                        'description': f"Missing transaction step 'TXN_{missing_step:02d}'. Steps must be contiguous.",
                        'thread_group': thread_group_name
                    })
        last_step = current_step


# Modified signature to accept root_element
def resolve_module_controller_target(module_controller_elem, root_element_for_traversal, module_issues_list):
    """
    Resolves the target element of a Module Controller by traversing the JMX structure.
    Returns (resolved_element, its_parent_hashtree, its_index_in_parent) or None.
    Appends structure errors related to module resolution to module_issues_list.
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

        jmeter_test_plan_ht = root_element_for_traversal.find('hashTree')  # Use passed root_element
        if jmeter_test_plan_ht is None:
            module_issues_list.append({
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
                    module_issues_list.append({
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
        jmeter_test_plan_direct_hashtree = root_element_for_traversal.find('hashTree')  # Use passed root_element
        if jmeter_test_plan_direct_hashtree is None:
            module_issues_list.append({
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


# Modified signature to accept root_element
def collect_logical_txns(element_or_hashtree, tg_name_for_report, collected_list, visited_elements, module_issues_list,
                         root_element_for_traversal):
    """
    Recursively collects Transaction Controllers and their nested children for validation.
    Also handles Module Controllers by resolving their targets.
    visited_elements set is used to prevent infinite loops in case of circular references.
    Appends issues to module_issues_list.
    root_element_for_traversal is used for resolving Module Controllers.
    """

    # Define the pattern here for easier use within the function
    txn_naming_pattern = r"^TXN_(\d{2})_.*"

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

            # Any other controller type that can contain children
            container_controller_tags = ['TestFragmentController', 'ThreadGroup', 'LoopController', 'SimpleController',
                                         'IfController', 'WhileController', 'OnceOnlyController',
                                         'ThroughputController', 'RandomController', 'SwitchController',
                                         'CriticalSectionController', 'InterleaveController', 'RandomOrderController',
                                         'ForEachController']

            if is_transaction_controller:
                txn_name = current_elem.get('testname')
                if txn_name:
                    step_number = validate_transaction_name(txn_name, tg_name_for_report, module_issues_list)
                    collected_list.append({
                        'name': txn_name,
                        'element': current_elem,
                        'step_number': step_number,
                        'source_type': 'direct',
                        'original_name_for_duplicate': txn_name
                    })
                    visited_elements.add(current_elem)

                # Always process children of a Transaction Controller
                if idx + 1 < len(children_of_current_hashtree) and children_of_current_hashtree[
                    idx + 1].tag == 'hashTree':
                    collect_logical_txns(children_of_current_hashtree[idx + 1], tg_name_for_report, collected_list,
                                         visited_elements, module_issues_list,
                                         root_element_for_traversal)  # Pass root_element_for_traversal
                    idx += 1

            elif is_module_controller:
                # Pass root_element_for_traversal to resolve_module_controller_target
                resolved_target_info = resolve_module_controller_target(current_elem, root_element_for_traversal,
                                                                        module_issues_list)

                if resolved_target_info is not None:
                    resolved_target_elem, parent_of_resolved_target, idx_of_resolved_target = resolved_target_info

                    visited_elements.add(current_elem)  # Mark module controller itself as visited

                    is_resolved_txn_controller = (resolved_target_elem.tag == 'TransactionController' or \
                                                  (resolved_target_elem.get(
                                                      'testclass') == 'org.apache.jmeter.control.TransactionController'))

                    # Check naming convention for the resolved target if it's NOT a TransactionController
                    if not is_resolved_txn_controller:
                        resolved_target_name = resolved_target_elem.get('testname')
                        if resolved_target_name and re.match(txn_naming_pattern, resolved_target_name):
                            module_issues_list.append({
                                'severity': 'WARNING',
                                'validation_option_name': THIS_VALIDATION_OPTION_NAME,
                                'type': 'Naming Convention',
                                'location': f"Module Controller '{current_elem.get('testname')}' resolves to non-Transaction Controller '{resolved_target_name}' ({resolved_target_elem.tag})",
                                'description': f"Non-Transaction Controller names (e.g., Loop, Simple, While, If) should not follow the 'TXN_NN_Description' format. This format is reserved exclusively for Transaction Controllers.",
                                'thread_group': tg_name_for_report
                            })

                    children_hashtree_of_resolved_target = None
                    if idx_of_resolved_target != -1 and \
                            idx_of_resolved_target + 1 < len(list(parent_of_resolved_target)) and \
                            list(parent_of_resolved_target)[idx_of_resolved_target + 1].tag == 'hashTree':
                        children_hashtree_of_resolved_target = list(parent_of_resolved_target)[
                            idx_of_resolved_target + 1]

                    if is_resolved_txn_controller:
                        # Only add to collected_list if it's a TransactionController
                        if resolved_target_elem not in [tc['element'] for tc in collected_list]:
                            txn_name = resolved_target_elem.get('testname')
                            step_number = validate_transaction_name(txn_name, tg_name_for_report, module_issues_list)
                            collected_list.append({'element': resolved_target_elem, 'source_type': 'module',
                                                   'module_name': current_elem.get('testname'),
                                                   'source_name': tg_name_for_report,
                                                   'name': txn_name,
                                                   'step_number': step_number,
                                                   'original_name_for_duplicate': txn_name})
                            visited_elements.add(
                                resolved_target_elem)  # Mark the resolved transaction controller as visited

                        # Recursively collect from its children if it has a hashTree
                        if children_hashtree_of_resolved_target is not None:
                            collect_logical_txns(children_hashtree_of_resolved_target, tg_name_for_report,
                                                 collected_list, visited_elements, module_issues_list,
                                                 root_element_for_traversal)  # Pass root_element_for_traversal

                    elif resolved_target_elem.tag in container_controller_tags:
                        # If it's another type of container controller, just traverse its children
                        if children_hashtree_of_resolved_target is not None:
                            collect_logical_txns(children_hashtree_of_resolved_target, tg_name_for_report,
                                                 collected_list, visited_elements, module_issues_list,
                                                 root_element_for_traversal)  # Pass root_element_for_traversal
                            visited_elements.add(resolved_target_elem)  # Mark the resolved container as visited
                        else:
                            module_issues_list.append({
                                'severity': 'WARNING',
                                'validation_option_name': THIS_VALIDATION_OPTION_NAME,
                                'type': 'Module Controller',
                                'location': f"Module Controller '{current_elem.get('testname')}' in Thread Group '{tg_name_for_report}'",
                                'description': f"Module Controller points to a container element '{resolved_target_elem.get('testname')}' ({resolved_target_elem.tag}) which has no inner elements (no sibling hashTree). No transactions collected from this target.",
                                'thread_group': tg_name_for_report
                            })
                    else:
                        # This covers samplers, listeners, etc., that a Module Controller might point to
                        module_issues_list.append({
                            'severity': 'WARNING',
                            'validation_option_name': THIS_VALIDATION_OPTION_NAME,
                            'type': 'Module Controller',
                            'location': f"Module Controller '{current_elem.get('testname')}' in Thread Group '{tg_name_for_report}'",
                            'description': f"Module Controller points to an element '{resolved_target_elem.get('testname')}' ({resolved_target_elem.tag}) that is not a Transaction Controller and does not contain transaction elements. It will not be included in transaction sequence validation.",
                            'thread_group': tg_name_for_report
                        })
                else:
                    module_issues_list.append({
                        'severity': 'WARNING',
                        'validation_option_name': THIS_VALIDATION_OPTION_NAME,
                        'type': 'Module Controller',
                        'location': f"Module Controller '{current_elem.get('testname')}' in Thread Group '{tg_name_for_report}'",
                        'description': "Could not resolve target for Module Controller. Sequence validation for this TG might be incomplete (Target not found).",
                        'thread_group': tg_name_for_report
                    })
                idx += 1

            # Handle other container controllers (Loop, If, Simple, etc.)
            elif current_elem.tag in container_controller_tags and current_elem not in visited_elements:
                controller_name = current_elem.get('testname')
                if controller_name and re.match(txn_naming_pattern, controller_name):
                    module_issues_list.append({
                        'severity': 'WARNING',
                        'validation_option_name': THIS_VALIDATION_OPTION_NAME,
                        'type': 'Naming Convention',
                        'location': f"Controller '{controller_name}' ({current_elem.tag})",
                        'description': f"Non-Transaction Controller names (e.g., Loop, Simple, While, If) should not follow the 'TXN_NN_Description' format. This format is reserved exclusively for Transaction Controllers.",
                        'thread_group': tg_name_for_report
                    })

                visited_elements.add(current_elem)
                # Recurse into children of this container controller
                if idx + 1 < len(children_of_current_hashtree) and children_of_current_hashtree[
                    idx + 1].tag == 'hashTree':
                    collect_logical_txns(children_of_current_hashtree[idx + 1], tg_name_for_report, collected_list,
                                         visited_elements, module_issues_list,
                                         root_element_for_traversal)  # Pass root_element_for_traversal
                    idx += 1  # Advance past the hashTree
                idx += 1  # Advance past the current element

            else:
                # If it's not a transaction controller, module controller, or known container,
                # we don't need to specifically process its children for *transaction* related validations.
                # However, it might still have its own hashTree, which we should skip over.
                if idx + 1 < len(children_of_current_hashtree) and children_of_current_hashtree[
                    idx + 1].tag == 'hashTree':
                    idx += 1  # Skip over the hashTree if present
                idx += 1
    else:
        # This case handles when an element_or_hashtree is a single element, not a hashTree
        # (e.g., direct target of a Module Controller that is not a hashTree)
        pass


def analyze_jmeter_script(root_element, selected_validations_list):
    """
    Main function to analyze the JMeter script for naming and sequence conventions.
    Returns a list of dictionaries, where each dictionary represents an issue.
    """
    module_issues = []

    if THIS_VALIDATION_OPTION_NAME not in selected_validations_list:
        return []

    jmeter_test_plan_direct_hashtree = root_element.find('hashTree')
    if jmeter_test_plan_direct_hashtree is None:
        module_issues.append({
            'severity': 'ERROR',
            'validation_option_name': THIS_VALIDATION_OPTION_NAME,
            'type': 'Structure',
            'location': 'JMeter Test Plan',
            'description': "Root 'jmeterTestPlan' has no child 'hashTree'. Invalid JMX structure.",
            'thread_group': 'N/A'
        })
        return module_issues

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
                module_issues.append({
                    'severity': 'ERROR',
                    'validation_option_name': THIS_VALIDATION_OPTION_NAME,
                    'type': 'Structure',
                    'location': 'JMeter Test Plan',
                    'description': "TestPlan element found but not followed by a hashTree for its children (Thread Groups, Test Fragments). Invalid JMX structure.",
                    'thread_group': 'N/A'
                })
                return module_issues

    if not test_plan_found_and_processed or top_level_controllers_hashTree is None:
        module_issues.append({
            'severity': 'ERROR',
            'validation_option_name': THIS_VALIDATION_OPTION_NAME,
            'type': 'Structure',
            'location': 'JMeter Test Plan',
            'description': "Could not locate the primary hashTree containing Thread Groups or Test Fragments. JMX structure might be unexpected.",
            'thread_group': 'N/A'
        })
        return module_issues

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

                # Pass root_element to collect_logical_txns
                collect_logical_txns(tg_children_hashtree, tg_name, thread_groups_data[tg_name], visited_elements_in_tg,
                                     module_issues, root_element)
                idx += 1
            else:
                module_issues.append({
                    'severity': 'WARNING',
                    'validation_option_name': THIS_VALIDATION_OPTION_NAME,
                    'type': 'Structure',
                    'location': f"Thread Group/Test Fragment '{tg_name}'",
                    'description': f"Expected a sibling 'hashTree' for {top_level_elem.tag} '{tg_name}' to contain its elements, but none was found. No elements will be validated within this container.",
                    'thread_group': tg_name
                })
        else:
            if idx + 1 < len(children_of_top_level_controllers_hashTree) and \
                    children_of_top_level_controllers_hashTree[idx + 1].tag == 'hashTree':
                temp_tg_name = top_level_elem.get('testname') or f"Top-Level {top_level_elem.tag}"
                temp_collected_list = []
                temp_visited_elements = set()
                # Pass root_element to collect_logical_txns
                collect_logical_txns(children_of_top_level_controllers_hashTree[idx + 1], temp_tg_name,
                                     temp_collected_list, temp_visited_elements, module_issues, root_element)
                idx += 1
        idx += 1

    for tg_name, transactions in thread_groups_data.items():
        if transactions:
            validate_transaction_sequence(transactions, tg_name, module_issues)

    return module_issues, []


# --- Local testing block for this module ---
if __name__ == "__main__":
    jmx_file_to_test = r"D:\Projects\Python\JmeterAutomation\output.jmx"  # Replace with your test JMX

    print(f"--- Running TXN Naming Convention Validation for: {jmx_file_to_test} ---")

    selected_validations = [THIS_VALIDATION_OPTION_NAME]  # Enable this validation for local test

    root_element_for_test = None
    # Simulate parsing as done in validator_report_page.py
    try:
        tree = ET.parse(jmx_file_to_test)
        root_element_for_test = tree.getroot()
        print("JMX file parsed successfully for local test.")
    except ET.ParseError as e:
        print(f"ERROR: Failed to parse JMX file for test: {e}")
    except FileNotFoundError:
        print(f"ERROR: JMX file not found for test: {jmx_file_to_test}")

    all_txn_issues = []
    if root_element_for_test is not None:
        print(f"Applying validation: '{THIS_VALIDATION_OPTION_NAME}'...")
        all_txn_issues = analyze_jmeter_script(root_element_for_test, selected_validations)
        print("Validation complete.")
    else:
        print("Skipping validation due to JMX parsing errors.")

    if all_txn_issues:
        print("\n--- Validation Results ---")
        for issue in all_txn_issues:
            print(f"Severity: {issue.get('severity', 'N/A')}")
            print(f"  Validation: {issue.get('validation_option_name', 'N/A')}")
            print(f"  Type: {issue.get('type', 'N/A')}")
            print(f"  Location: {issue.get('location', 'N/A')}")
            print(f"  Description: {issue.get('description', 'N/A')}")
            print(f"  Thread Group: {issue.get('thread_group', 'N/A')}")
            print("-" * 20)
    else:
        print("\n--- Validation Results ---")
        print(f"🥳 No issues found for '{THIS_VALIDATION_OPTION_NAME}' in {jmx_file_to_test}!")

    print(f"\n--- End of Validation for {jmx_file_to_test} ---")