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
            raise  # Re-raise exception to notify front-end about the error

    def modify_http_header(self, header_name, new_value):
        """
        Modifies the value of a specified HTTP header.

        :param header_name: Name of the HTTP header to modify.
        :param new_value: New value to assign to the header.
        """
        modified = False
        for element_prop in self.root.iter('elementProp'):
            attrib_value = element_prop.get('name')
            if attrib_value == header_name:
                for string_prop in element_prop.iter('stringProp'):
                    attrib_value2 = string_prop.get('name')
                    if attrib_value2 == 'Header.value':
                        string_prop.text = new_value
                        modified = True

        if not modified:
            print(f"Header '{header_name}' not found in the file.")
            raise ValueError(f"Header '{header_name}' not found in the file.")

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

    def save_changes(self, output_path):
        """
        Save the modified XML tree to a new file.

        :param output_path: Path to save the modified XML.
        """
        self.tree.write(output_path, encoding="utf-8", xml_declaration=True)
        print(f"Changes saved to {output_path}")
