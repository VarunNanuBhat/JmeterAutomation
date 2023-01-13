import xml.etree.ElementTree as ET

# path of xml doc
tree = ET.parse('Trail.xml')

# root tag of xml doc
root = tree.getroot()
# print(root.tag)

# iterate over subelements of tree
for child in root:
#    print(child.tag, child.attrib)
    pass


# iterate through all the elements of the tee
for ele in root.iter():
    #print(ele.tag)
    pass

# printing the whole doc using ET
#print(ET.tostring(root, encoding='utf8').decode('utf8'))


# getting specific element of xml tree
# test class is considered
for UniformRandomTimer in root.iter('UniformRandomTimer'):
    # print(UniformRandomTimer.attrib)
    # print(UniformRandomTimer.get('enabled'))
    UniformRandomTimer.set('enabled', 'false')
    #print(UniformRandomTimer.attrib)


tree.write('output.xml')







