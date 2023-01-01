import xml.etree.ElementTree as ET

tree = ET.parse('Trail.xml')

root = tree.getroot()

for ele in root.iter():
    #print(ele.tag)
    pass

for elementProp in root.iter('elementProp'):
    attrib_value = elementProp.get('name')
    if (attrib_value == "X-CorrelationId"):
        for stringProp in elementProp.iter('stringProp'):
            attrib_value2 = stringProp.get('name')
            if attrib_value2 == 'Header.value':
                new_corr_ID = 'abc'
                stringProp.text = new_corr_ID

tree.write('output2.xml')