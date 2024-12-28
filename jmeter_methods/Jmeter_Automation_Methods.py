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
        Delete endpoints whose URLs end with the specified text.

        :param text: Text to match the endpoint URL.
        """
        modified = False
        for child_element in list(self.root.iter("HTTPSamplerProxy")):
            for sub_child_element in child_element.iter("stringProp"):
                if sub_child_element.get("name") == "HTTPSampler.path":
                    url = sub_child_element.text
                    if url and url.endswith(text):
                        parent = self.root.find(".//HTTPSamplerProxy/..")
                        if parent is not None:
                            parent.remove(child_element)
                            # print(f"Deleted HTTPSamplerProxy with URL: {url}")
                            modified = True

        if not modified:
            print(f"No endpoints ending with '{text}' were found to delete.")
        return modified

    def save_changes(self, output_path):
        """
        Save the modified XML tree to a new file.

        :param output_path: Path to save the modified XML.
        """
        self.tree.write(output_path, encoding="utf-8", xml_declaration=True)
        print(f"Changes saved to {output_path}")

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
