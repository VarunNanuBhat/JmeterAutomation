import xml.etree.ElementTree as ET

tree = ET.parse('Trail.xml')

# Get the root and print
root = tree.getroot()
print(root)

# Get the attributes for root element
print(root.attrib)

# Iterating through every child elements of root
for child_element in root.iter():
    # print(child_element.tag, child_element.attrib)
    pass

# The root.iter() method helps us find particular interest elements.
# This method will give all the subelements under the root matching the specified element.
for child_element in root.iter("stringProp"):
    # print(child_element.tag, child_element.attrib)
    pass
# Print the text associated with elements (tags)
for child_element in root.iter("stringProp"):
    # print(child_element.tag, child_element.text)
    pass

# Extract texts from subelements of an element
for child_element in root.iter("HeaderManager"):
    for sub_child_element in child_element.iter("stringProp"):
        # print(sub_child_element.tag, sub_child_element.text)
        pass

