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

# Iterate through all the requests and disable the URL's of each tag in sub nodes that end with with certain texts.
for child_element in root.iter("HTTPSamplerProxy"):
    for sub_child_element in child_element.iter("stringProp"):
        if(sub_child_element.get("name") == "HTTPSampler.path"):
            url = sub_child_element.text
            if (url != None and url.endswith("svg")):
                # child_element.set('enabled', 'false')
                pass

# Disable particular sampler:
# if requested sampler contains guiclass, it can be disabled
# Iterate through all the requests and disable the URL's of each tag in sub nodes that end with with certain texts.
for child_element in root.iter("HTTPSamplerProxy"):
    for sub_child_element in child_element.iter("stringProp"):
        if(sub_child_element.get("name") == "HTTPSampler.domain"):
            domain = sub_child_element.text
            print(domain)
            if (domain != None and domain == "play.google.com"):
                child_element.set('enabled', 'false')
                # pass


# change the domain name



# Iterate through all the requests and remove the URL's of each tag in sub nodes that end with certain texts.
for child_element in root.iter("HTTPSamplerProxy"):
    for sub_child_element in child_element.iter("stringProp"):
        if(sub_child_element.get("name") == "HTTPSampler.path"):
            url = sub_child_element.text
            if (url != None and url.endswith("svg")):
                parent = root.find(".//HTTPSamplerProxy/..")  # Find the parent element
                if parent is not None:
                    # parent.remove(child_element)
                    # print(f"Removed HTTPSamplerProxy with URL: {url}")
                    pass


# Delete a node in xml
# Delete a particular header key value pair
for child_element in root.iter("HeaderManager"):
    for sub_child_element in child_element.iter("collectionProp"):
        for sub_child_element2 in list(sub_child_element):
            if(sub_child_element2.get("name") == "Authorization"):
                # sub_child_element.remove(sub_child_element2)
                pass
tree.write('output.xml')