# HTTPSamplerProxy node contains the request details.







import xml.etree.ElementTree as ET
#tree = ET.parse('output_modified.jmx')

tree = ET.parse('output2.jmx')

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

# Extract unique header values texts from subelements of an element
header_name_array = []
for child_element in root.iter("HeaderManager"):
    for sub_child_element in child_element.iter("stringProp"):
        if sub_child_element.get("name") == "Header.name":
            if sub_child_element.text not in header_name_array:
                header_name_array.append(sub_child_element.text)
                # print(sub_child_element.text)
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


# Replace particular strings in request URL
for child_element in root.iter("HTTPSamplerProxy"):
    for sub_child_element in child_element.iter("stringProp"):
        if(sub_child_element.get("name") == "HTTPSampler.path"):
            url = sub_child_element.text
            if (url != None and "hash-check" in url):
                url = url.replace("hash-check","new-text")
                # sub_child_element.text = url
                # print(url)

# replace particular string in body data and parameters
for child_element in root.iter("collectionProp"):
    for sub_child_element in child_element.iter("stringProp"):
        # print(sub_child_element.tag, sub_child_element.attrib)
        # print(sub_child_element.attrib.get("name"))
        if sub_child_element.attrib.get("name") == "Argument.value":
            text = sub_child_element.text
            if (text != None and "11223344" in text):
                text = text.replace("11223344", "replaced")
                # sub_child_element.text = text
                # print(text)



# Disable particular sampler:
# if requested sampler contains guiclass, it can be disabled
# Iterate through all the requests and disable the URL's of each tag in sub nodes that end with with certain texts.
for child_element in root.iter("HTTPSamplerProxy"):
    for sub_child_element in child_element.iter("stringProp"):
        if(sub_child_element.get("name") == "HTTPSampler.domain"):
            domain = sub_child_element.text
            # print(domain)
            if (domain != None and domain == "play.google.com"):
                child_element.set('enabled', 'false')
                # pass


# change the domain name
for child_element in root.iter("HTTPSamplerProxy"):
    for sub_child_element in child_element.iter("stringProp"):
        if sub_child_element.get("name") == "HTTPSampler.domain":
            domain = sub_child_element.text
            if domain != None and domain == "play.google.com":
                # print(domain)
                # sub_child_element.text = "new domain value"
                # print(f"Domain updated to: {sub_child_element.text}")
                pass


# List all unique domain names
domain_array = []
for child_element in root.iter("HTTPSamplerProxy"):
    for sub_child_element in child_element.iter("stringProp"):
        if sub_child_element.get("name") == "HTTPSampler.domain":
            if sub_child_element.text not in domain_array:
                domain_array.append(sub_child_element.text)
                # print(sub_child_element.text)


# Iterate through all the requests and remove the URL's of each tag in sub nodes that end with certain texts.
# This is half implementation. We should also remove the associated samplers for the corresponding HTTP request
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


# List out all unique samplers
sampler_array = []
for child_element in root.iter():
    child_element.get("testname") and child_element.get("testclass")
    if child_element.get("testname") != None and child_element.get("testclass") != None :
        if (child_element.get("testclass") != "HTTPSamplerProxy"):
            if (child_element.get("testname") not in sampler_array):
                sampler_array.append(child_element.get("testname"))
                # print(child_element.get("testname"))
                pass


# enable/disable samplers
for child_element in root.iter():
    if child_element.get("testname") == "Uniform Random Timer":
        child_element.set("enabled","false")
        # print("done")
        pass





tree.write('Trail.xml')




'''
Validate user input fields in the Tkinter forms (e.g., ensure non-empty values for headers or endpoints).
3. Feature Expansion
a. Batch Processing of JMX Files
Allow users to upload multiple JMX files and apply modifications to all of them.
b. Dynamic Parameter Replacement
Implement regex-based search and replace for more flexible content modification.
c. Custom Actions
Let users define custom actions through the UI, such as combining multiple modifications into a single workflow.
d. Version Control
Save backup copies of the original JMX file before applying changes.
Implement a "Revert to Last State" feature.

4. Advanced UI Features
Preview Changes: Add a button that shows a diff of changes before saving.
Navigation Pane: Provide a tree view of the JMX structure in the UI to allow users to visualize and navigate the file.
Search Bar: Let users search for specific elements (e.g., endpoints or headers) within the JMX file.
Status Indicators: Show indicators (e.g., a progress bar or success/error icon) for each operation.

5. Integration Features
a. Integration with Version Control
Enable Git integration to commit changes to a repository.
Provide a history log of changes for each JMX file.
b. REST API Interface
Expose the functionalities through a REST API for remote use.
Build an accompanying CLI for scripting.
c. Export/Import
Add support to export configurations for reusability or import them to modify another file.

7. Documentation and Tutorials
Add in-app tooltips or a help section explaining each functionality.
Create a step-by-step tutorial or user guide accessible from the app.
Include FAQs for common issues users might face.

9. AI-Assisted Features (Optional)
Implement basic AI to suggest common fixes or optimizations for JMX files.
Add natural language input for tasks (e.g., "disable all endpoints with domain example.com").
'''


'''
recommended fixes: 
1. Add checkbox for list sampler -> sampler modifier checkout similar to delete header. Do the same thing for modify selected domains
2. Provide clear option for all pages
3. Rebuild/structure string replace in url/body
5. Add icons for every buttons. 
6. Add a canvas frame for delete selected header from header list page, checkout page for modify endpoints based on domains (refer modify sampler).  
7. In sampler modify, even I dont select action and click on apply changes for selected samplers, it does not throw a error message
8. Check for button order in all the pages
9. Check if appy changes of confirm button executes only if actions are selected. 
10. Checkout for header modify and replace domain page needs to updated to support multiple files. 
'''



'''
Things that can be considered: 
1. In HTTP header modify checkout, i have added a small delay and then landed back in file upload page. 
2. Images are added in list header page buttons. Follow the same one. 
3. List header button alignment is good. 
'''