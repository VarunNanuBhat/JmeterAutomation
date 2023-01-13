import xml.etree.ElementTree as ET

tree = ET.parse('Trail.xml')

root = tree.getroot()

for eachCall in root.iter('HTTPSamplerProxy'):
    # print(eachCall.attrib)
    if (eachCall.items()[2][1].endswith("443")):
        eachCall.set('enabled', 'false')

tree.write('output.xml')