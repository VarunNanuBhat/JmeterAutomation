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
            print(f"Error parsing XML file {file_path}: {e}")
            raise

    def modify_http_headers(self, headers):
        """
        Modifies the values of multiple specified HTTP headers.

        :param headers: A dictionary where keys are header names and values are the new values for the headers.
        """
        modified_headers = set()
        for element_prop in self.root.iter('elementProp'):
            attrib_value = element_prop.get('name')
            if attrib_value in headers:
                for string_prop in element_prop.iter('stringProp'):
                    attrib_value2 = string_prop.get('name')
                    if attrib_value2 == 'Header.value':
                        string_prop.text = headers[attrib_value]
                        modified_headers.add(attrib_value)

        # Check for any headers that weren't found in the file
        not_found_headers = set(headers.keys()) - modified_headers
        if not_found_headers:
            print(f"Headers not found in the file: {', '.join(not_found_headers)}")
            raise ValueError(f"Headers not found in the file: {', '.join(not_found_headers)}")


    def delete_http_header(self, header_name):
        """
        Deletes a specific key-value pair from the HTTP Header Manager.

        :param header_name: Name of the HTTP header to delete.
        """
        deleted = False
        for header_manager in self.root.iter("HeaderManager"):
            for collection_prop in header_manager.iter("collectionProp"):
                for element_prop in list(collection_prop):  # Use list() to avoid runtime modification issues
                    if element_prop.get("name") == header_name:
                        collection_prop.remove(element_prop)
                        deleted = True

        if not deleted:
            print(f"Header '{header_name}' not found or not deleted.")
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
            print(f"No endpoints ending with '{text}' were found to enable.")
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
            print(f"No endpoints ending with '{text}' were found to disable.")
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
            print(f"No endpoints ending with '{text}' were found to enable.")
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
            print(f"No endpoints ending with '{text}' were found to disable.")
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
        print(f"Changes saved to {output_path}")