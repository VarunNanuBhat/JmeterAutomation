# HTTPSamplerProxy node contains the request details.







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

# List all items of a node in key value pair.
for child_element in root.iter("HeaderManager"):
    # print(child_element.items())
    pass


# Iterate through all the requests and get the names of each tag in sub nodes.
for child_element in root.iter("HTTPSamplerProxy"):
    for sub_child_element in child_element.iter("stringProp"):
        # print(sub_child_element.get("name"))
        pass

# Iterate through all the requests and get the URL's of each tag in sub nodes.
for child_element in root.iter("HTTPSamplerProxy"):
    for sub_child_element in child_element.iter("stringProp"):
        if(sub_child_element.get("name") == "HTTPSampler.path"):
            # print(sub_child_element.text)
            pass

# Delete a node in xml
# Delete a particular header key value pair
for child_element in root.iter("HeaderManager"):
    for sub_child_element in child_element.iter("collectionProp"):
        for sub_child_element2 in list(sub_child_element):
            if(sub_child_element2.get("name") == "Authorization"):
                sub_child_element.remove(sub_child_element2)

tree.write('output.xml')