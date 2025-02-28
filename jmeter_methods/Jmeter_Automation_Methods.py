import xml.etree.ElementTree as ET


class JMXModifier:
    def __init__(self, file_path):
        """
        Initialize the JMXModifier with a file path.
        """
        self.file_path = file_path
        try:
            self.tree = ET.parse(file_path)
            self.root = self.tree.getroot()
        except ET.ParseError as e:
            #print(f"Error parsing XML file {file_path}: {e}")
            raise

    def modify_http_headers(self, headers):
        """
        Modifies the values of multiple specified HTTP headers.
        Handles case-insensitive header name matching.

        :param headers: A dictionary where keys are header names and values are the new values for the headers.
        """
        modified_headers = set()
        header_keys_lower = {key.lower(): value for key, value in headers.items()}  # Normalize input keys

        for element_prop in self.root.iter("elementProp"):
            header_name = None  # Store header name found in elementProp

            # Extract header name inside <stringProp>
            for string_prop in element_prop.iter("stringProp"):
                if string_prop.get("name", "").strip().lower() == "header.name":
                    header_name = string_prop.text.strip().lower() if string_prop.text else None
                    break

            if header_name and header_name in header_keys_lower:
                # Modify only if the header name matches
                for string_prop in element_prop.iter("stringProp"):
                    if string_prop.get("name", "").strip().lower() == "header.value":
                        string_prop.text = header_keys_lower[header_name]
                        modified_headers.add(header_name)
                        break  # Stop modifying once found

        # Identify headers that were not found and modified
        not_found_headers = set(header_keys_lower.keys()) - modified_headers
        if not_found_headers:
            raise ValueError(f"Headers not found in the file: {', '.join(not_found_headers)}")

    def list_header_names(self):
        """
        Collects unique HTTP header names from the JMX file.
        """
        header_name_array = set()  # Use a set to ensure uniqueness

        for child_element in self.root.iter("HeaderManager"):
            for sub_child_element in child_element.iter("stringProp"):
                if sub_child_element.get("name") == "Header.name":
                    header_name_array.add(sub_child_element.text)
                    #print(sub_child_element.text)

        return list(header_name_array)

    def delete_http_header(self, header_name):
        """
        Deletes a specific key-value pair from the HTTP Header Manager.
        Handles case-insensitive matching.

        :param header_name: Name of the HTTP header to delete.
        """
        deleted = False
        header_name_lower = header_name.lower()

        for header_manager in self.root.iter("HeaderManager"):
            for collection_prop in header_manager.iter("collectionProp"):
                elements_to_remove = []

                for element_prop in collection_prop.findall("elementProp"):
                    for sub_prop in element_prop.findall("stringProp"):
                        if sub_prop.get("name", "").lower() == "header.name" and (
                                sub_prop.text or "").strip().lower() == header_name_lower:
                            elements_to_remove.append(element_prop)
                            break

                for element in elements_to_remove:
                    collection_prop.remove(element)
                    deleted = True

        if not deleted:
            raise ValueError(f"Header '{header_name}' not found or not deleted.")

    def enable_endpoints(self, text):
        """
        Enable endpoints whose URLs end with the specified text.

        :param text: Text to match the endpoint URL.
        """
        modified = False
        for child_element in self.root.iter("HTTPSamplerProxy"):
            for sub_child_element in child_element.iter("stringProp"):
                if sub_child_element.get("name") == "HTTPSampler.path":
                    url = sub_child_element.text
                    if url and url.endswith(text):
                        child_element.set('enabled', 'true')
                        # print(f"Enabled HTTPSamplerProxy with URL: {url}")
                        modified = True

        if not modified:
            #print(f"No endpoints ending with '{text}' were found to enable.")
            pass
        return modified

    def disable_endpoints(self, text):
        """
        Disable endpoints whose URLs end with the specified text.

        :param text: Text to match the endpoint URL.
        """
        modified = False
        for child_element in self.root.iter("HTTPSamplerProxy"):
            for sub_child_element in child_element.iter("stringProp"):
                if sub_child_element.get("name") == "HTTPSampler.path":
                    url = sub_child_element.text
                    if url and url.endswith(text):
                        child_element.set('enabled', 'false')
                        # print(f"Disabled HTTPSamplerProxy with URL: {url}")
                        modified = True

        if not modified:
            #print(f"No endpoints ending with '{text}' were found to disable.")
            pass
        return modified

    def delete_endpoints(self, text):
        """
        Delete endpoints whose URLs end with the specified text,
        along with their associated <hashtree> node.

        :param text: Text to match the endpoint URL.
        """
        modified = False

        # Iterate over all <hashTree> elements
        for parent in self.root.findall(".//hashTree"):  # Iterate through all <hashTree> nodes
            children = list(parent)  # Get the direct children of <hashTree>

            for i, child_element in enumerate(children):
                if child_element.tag == "HTTPSamplerProxy":  # Match the HTTPSamplerProxy
                    # Check if the HTTPSamplerProxy has a stringProp with name 'HTTPSampler.path'
                    for sub_child_element in child_element.iter("stringProp"):
                        if sub_child_element.get("name") == "HTTPSampler.path":
                            url = sub_child_element.text
                            if url and url.endswith(text):  # Match the URL
                                # Remove the HTTPSamplerProxy
                                parent.remove(child_element)
                                # print(f"Deleted HTTPSamplerProxy with URL: {url}")

                                # Also remove the <hashtree> node if it's the next element
                                if i + 1 < len(children) and children[i + 1].tag == "hashTree":
                                    parent.remove(children[i + 1])
                                    # print("Deleted associated <hashtree> node.")

                                modified = True

        return modified

    def enable_domain_endpoints(self, text):
        """
        Enable endpoints with specific domain name.

        :param text: Text to match the domain name
        """
        modified = False
        for child_element in self.root.iter("HTTPSamplerProxy"):
            for sub_child_element in child_element.iter("stringProp"):
                if sub_child_element.get("name") == "HTTPSampler.domain":
                    domain = sub_child_element.text
                    if domain != None and domain == text:
                        child_element.set('enabled', 'true')
                        # print(f"Enabled HTTPSamplerProxy with URL: {url}")
                        modified = True

        if not modified:
            #print(f"No endpoints ending with '{text}' were found to enable.")
            pass
        return modified

    def disable_domain_endpoints(self, text):
        """
        Disable eendpoints with specific domain name.

        :param text: Text to match the domain name.
        """
        modified = False
        for child_element in self.root.iter("HTTPSamplerProxy"):
            for sub_child_element in child_element.iter("stringProp"):
                if sub_child_element.get("name") == "HTTPSampler.domain":
                    domain = sub_child_element.text
                    if domain != None and domain == text:
                        child_element.set('enabled', 'false')
                        # print(f"Disabled HTTPSamplerProxy with URL: {url}")
                        modified = True

        if not modified:
            #print(f"No endpoints ending with '{text}' were found to disable.")
            pass
        return modified

    def delete_domain_endpoints(self, text):
        """
        Delete endpoints with specific domain name,
        along with their associated <hashtree> node.

        :param text: Text to match the domain name.
        """
        modified = False

        # Iterate over all <hashTree> elements
        for parent in self.root.findall(".//hashTree"):  # Iterate through all <hashTree> nodes
            children = list(parent)  # Get the direct children of <hashTree>

            for i, child_element in enumerate(children):
                if child_element.tag == "HTTPSamplerProxy":  # Match the HTTPSamplerProxy
                    # Check if the HTTPSamplerProxy has a stringProp with name 'HTTPSampler.path'
                    for sub_child_element in child_element.iter("stringProp"):
                        if sub_child_element.get("name") == "HTTPSampler.domain":
                            domain = sub_child_element.text
                            if domain != None and domain == text: # Match the URL
                                # Remove the HTTPSamplerProxy
                                parent.remove(child_element)
                                # print(f"Deleted HTTPSamplerProxy with URL: {url}")

                                # Also remove the <hashtree> node if it's the next element
                                if i + 1 < len(children) and children[i + 1].tag == "hashTree":
                                    parent.remove(children[i + 1])
                                    # print("Deleted associated <hashtree> node.")

                                modified = True

        return modified

    def list_unique_domain_names(self):
        """
        Collects unique domain names from the HTTPSamplerProxy elements in the JMX file.
        """
        domain_array = set()  # Use a set to ensure uniqueness

        for child_element in self.root.iter("HTTPSamplerProxy"):
            for sub_child_element in child_element.iter("stringProp"):
                if sub_child_element.get("name") == "HTTPSampler.domain":
                    domain_value = sub_child_element.text
                    if domain_value and domain_value.strip():  # Filter out None and empty strings
                        domain_array.add(domain_value.strip())
        # print(list(sorted(domain_array)))
        return list(domain_array)  # Convert set back to list for consistency


    def enable_samplers_by_name(self, name):
        """
        Enable samplers whose 'testname' attribute matches the specified name.

        :param name: Name to match the sampler's 'testname' attribute.
        :return: True if at least one sampler was modified; otherwise, False.
        """
        modified = False
        for child_element in self.root.iter():
            if child_element.get("testname") == name:
                child_element.set("enabled", "true")
                modified = True

        if not modified:
            #print(f"No samplers with testname '{name}' were found to enable.")
            pass
        return modified


    def disable_samplers_by_name(self, name):
        """
        Disable samplers whose 'testname' attribute matches the specified name.

        :param name: Name to match the sampler's 'testname' attribute.
        :return: True if at least one sampler was modified; otherwise, False.
        """
        modified = False
        for child_element in self.root.iter():
            if child_element.get("testname") == name:
                child_element.set("enabled", "false")
                modified = True

        if not modified:
            #print(f"No samplers with testname '{name}' were found to disable.")
            pass
        return modified

    def delete_samplers_by_name(self, name):
        """
        Delete samplers with a specific 'testname' attribute,
        along with their associated <hashTree> node.

        :param name: Name to match the sampler's 'testname' attribute.
        :return: True if at least one sampler was deleted; otherwise, False.
        """
        modified = False

        # Iterate over all <hashTree> elements
        for parent in self.root.findall(".//hashTree"):  # Find all <hashTree> nodes
            children = list(parent)  # Get the direct children of <hashTree>

            for i, child_element in enumerate(children):
                if child_element.get("testname") == name:  # Match 'testname' attribute
                    # Remove the sampler
                    parent.remove(child_element)

                    # Also remove the associated <hashTree> node if it is the next sibling
                    if i + 1 < len(children) and children[i + 1].tag == "hashTree":
                        parent.remove(children[i + 1])

                    modified = True

        if not modified:
            #print(f"No samplers with testname '{name}' were found to delete.")
            pass
        return modified

    def list_unique_sampler_names(self):
        """
        Collects unique sampler names from the JMX file, excluding HTTPSamplerProxy.
        """
        sampler_names = set()  # Use a set to store unique values

        for child_element in self.root.iter():
            test_name = child_element.get("testname")
            test_class = child_element.get("testclass")

            if test_name and test_class and test_class != "HTTPSamplerProxy":
                sampler_names.add(test_name)

        return list(sampler_names)



    def update_endpoints(self, text, action):
        """
        Update endpoints by calling the appropriate method.

        :param text: Text to match the endpoint URL.
        :param action: Action to perform - "enable", "disable", or "delete".
        """
        if action == "enable":
            return self.enable_endpoints(text)
        elif action == "disable":
            return self.disable_endpoints(text)
        elif action == "delete":
            return self.delete_endpoints(text)
        else:
            raise ValueError(f"Invalid action '{action}'. Please choose 'enable', 'disable', or 'delete'.")

    def update_domain_endpoints(self, text, action):
        """
        Update endpoints by calling the appropriate method.

        :param text: Text to match the endpoint URL.
        :param action: Action to perform - "enable", "disable", or "delete".
        """
        if action == "enable":
            return self.enable_domain_endpoints(text)
        elif action == "disable":
            return self.disable_domain_endpoints(text)
        elif action == "delete":
            return self.delete_domain_endpoints(text)
        else:
            raise ValueError(f"Invalid action '{action}'. Please choose 'enable', 'disable', or 'delete'.")

    def replace_domain_name(self, old_domain, new_domain):
        """
        Replace domain names in the request URL.

        :param old_domain: The domain name to be replaced.
        :param new_domain: The new domain name to replace with.
        """
        modified = False
        for child_element in self.root.iter("HTTPSamplerProxy"):
            for sub_child_element in child_element.iter("stringProp"):
                if sub_child_element.get("name") == "HTTPSampler.domain":
                    domain = sub_child_element.text
                    if domain and domain == old_domain:
                        sub_child_element.text = new_domain
                        modified = True
                        # print(f"Replaced domain '{old_domain}' with '{new_domain}' in HTTPSamplerProxy.")

        if not modified:
            # print(f"No domain '{old_domain}' found in the file to replace.")
            pass
        return modified

    def replace_string_in_url(self, old_string, new_string):
        """
        Replace a specific substring in the URLs of all HTTP Samplers.

        :param old_string: The substring to replace in the URL.
        :param new_string: The substring to replace it with.
        """
        modified = False
        for child_element in self.root.iter("HTTPSamplerProxy"):
            for sub_child_element in child_element.iter("stringProp"):
                if sub_child_element.get("name") == "HTTPSampler.path":
                    url = sub_child_element.text
                    if url and old_string in url:
                        sub_child_element.text = url.replace(old_string, new_string)
                        modified = True
                        # print(f"Replaced '{old_string}' with '{new_string}' in URL: {url}")

        if not modified:
            # print(f"No URLs containing '{old_string}' were found to replace.")
            pass
        return modified


    def replace_string_in_body_and_params(self, old_string, new_string):
        """
        Replace a specific substring in the body data and parameters.

        :param old_string: The substring to replace.
        :param new_string: The substring to replace it with.
        """
        modified = False
        for collection_prop in self.root.iter("collectionProp"):
            for string_prop in collection_prop.iter("stringProp"):
                if string_prop.get("name") == "Argument.value":
                    text = string_prop.text
                    if text and old_string in text:
                        string_prop.text = text.replace(old_string, new_string)
                        modified = True
                        # print(f"Replaced '{old_string}' with '{new_string}' in body data/parameters: {text}")

        if not modified:
            # print(f"No body data or parameters containing '{old_string}' were found to replace.")
            pass
        return modified



    def save_changes(self, output_path):
        """
        Save the modified XML tree to a new file.

        :param output_path: Path to save the modified XML.
        """
        self.tree.write(output_path, encoding="utf-8", xml_declaration=True)
        #print(f"Changes saved to {output_path}")