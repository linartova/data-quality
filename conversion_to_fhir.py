import xml.etree.ElementTree as ElementTree


class Patient:
    def __init__(self, identifier, sex, birth):
        self.identifier = identifier
        self.sex = sex
        self.birth = birth


class Condition:
    def __init__(self, histopathology, age_at_primary_diagnosis, date_diagnosis):
        self.age_at_primary_diagnosis = age_at_primary_diagnosis
        self.date_diagnosis = date_diagnosis
        self.histopathology = histopathology


class Specimen:
    def __init__(self, sample_material_type, year_of_sample_connection):
        self.year_of_sample_connection = year_of_sample_connection
        self.sample_material_type = sample_material_type


def read_xml_and_feed_the_classes():
    tree = ElementTree.parse('import_example 1.xml')
    root = tree.getroot()
    namespace = "{http://registry.samply.de/schemata/import_v1}"
    result = []
    for element in root.iter():
        if element.tag == namespace + "BHPatient":
            patient_id = element.find(namespace + "Identifier").text
            form = element.find(namespace +
                               "Locations").find(namespace +
                                                 "Location").find(namespace +
                                                                  "BasicData").find(namespace +
                                                                                    "Form")
            sex = form.find(namespace + "Dataelement_85_1")
            age_at_primary_diagnostic = form.find(namespace + "Dataelement_3_1")
            date_diagnosis = form.find(namespace + "Dataelement_51_3")
            events = element.find(namespace + "Locations").find(namespace + "Location").find(namespace + "Events")
            histopathology = find_histopathology(namespace, events)
            year_of_sample_connection = find_sample(namespace, events)
            sample_material_type = find_sample_material(namespace, events)
            age = 30
            result.append([Patient(patient_id, sex.text, age),
                           Condition(histopathology.text, age_at_primary_diagnostic.text, date_diagnosis.text),
                           Specimen(sample_material_type.text, year_of_sample_connection.text)])
    return result


def find_histopathology(namespace, events):
    for event in events.findall(namespace + "Event"):
        if event.attrib.get("eventtype") == "Histopathology":
            return event.find(namespace + "LogitudinalData").find(namespace + "Form2").find(namespace + "Dataelement_92_1")


def find_sample(namespace, events):
    for event in events.findall(namespace + "Event"):
        if event.attrib.get("eventtype") == "Sample":
            return event.find(namespace + "LogitudinalData").find(namespace + "Form1").find(namespace + "Dataelement_89_3")


def find_sample_material(namespace, events):
    for event in events.findall(namespace + "Event"):
        if event.attrib.get("eventtype") == "Sample":
            return event.find(namespace + "LogitudinalData").find(namespace + "Form1").find(namespace + "Dataelement_54_2")


def create_outputs(patient, condition, specimen, number):
    create_patient(patient, number)
    create_condition(patient.identifier, condition, number)
    create_specimen(patient.identifier, specimen, number)


def create_patient(patient, number):
    root = ElementTree.Element("Patient")
    root.set("xmlns", "http://hl7.org/fhir")

    id = ElementTree.SubElement(root, "id")
    id.set("value", patient.identifier)

    sex = ElementTree.SubElement(root, "gender")
    sex.set("value", patient.sex)

    tree = ElementTree.ElementTree(root)
    xml_file_path = "patient_" + number + ".fhir.xml"
    tree.write(xml_file_path)


def create_condition(identifier, condition, number):
    root = ElementTree.Element("Condition")
    root.set("xmlns", "http://hl7.org/fhir")

    id = ElementTree.SubElement(root, "id")
    id.set("value", identifier + "-condition")

    clinical_status = ElementTree.SubElement(root, "clinicalStatus")
    verification_status = ElementTree.SubElement(root, "verificationStatus")
    code = ElementTree.SubElement(root, "code")
    subject = ElementTree.SubElement(root, "subject")
    onsetDateTime = ElementTree.SubElement(root, "onsetDateTime")
    onsetDateTime.set("value", condition.date_diagnosis)

    # clinical_status
    coding = ElementTree.SubElement(clinical_status, "coding")
    system = ElementTree.SubElement(coding, "system")
    system.set("value", 'http://terminology.hl7.org/CodeSystem/condition-clinical')
    code_clinical = ElementTree.SubElement(coding, "code")
    code_clinical.set("value", "active")

    # verification_status
    coding_ver = ElementTree.SubElement(verification_status, "coding")
    system_ver = ElementTree.SubElement(coding_ver, "system")
    system_ver.set("value", 'http://terminology.hl7.org/CodeSystem/condition-ver-status')
    code_ver = ElementTree.SubElement(coding_ver, "code")
    code_ver.set("value", "confirmed")

    # code
    coding_code = ElementTree.SubElement(code, "coding")
    system_code = ElementTree.SubElement(coding_code, "system")
    system_code.set("value", 'http://fhir.de/CodeSystem/bfarm/icd-10-gm')
    code_code = ElementTree.SubElement(coding_code, "code")
    code_code.set("value", "active")

    # display
    display = ElementTree.SubElement(coding_code, "display")
    display.set("value", condition.histopathology)

    # text
    text = ElementTree.SubElement(code, "text")
    text.set("value", condition.histopathology)

    reference = ElementTree.SubElement(subject, "reference")
    reference.set("value", "Patient" + "_" + number)

    tree = ElementTree.ElementTree(root)
    xml_file_path = "condition_" + number + ".fhir.xml"
    tree.write(xml_file_path)


def create_specimen(identifier, specimen, number):
    root = ElementTree.Element("Specimen")
    root.set("xmlns", "http://hl7.org/fhir")

    id = ElementTree.SubElement(root, "id")
    id.set("value", identifier + "-specimen")

    type = ElementTree.SubElement(root, "type")
    collection = ElementTree.SubElement(root, "collection")

    coding = ElementTree.SubElement(type, "coding")
    system = ElementTree.SubElement(coding, "system")
    system.set("value", 'http://fhir.de/StructureDefinition/CodingICD10GM')
    code_clinical = ElementTree.SubElement(coding, "code")
    code_clinical.set("value", "active")
    display = ElementTree.SubElement(coding, "display")
    display.set("value", specimen.sample_material_type)

    collected_date_time = ElementTree.SubElement(collection, "collectedDateTime")
    collected_date_time.set("value", specimen.year_of_sample_connection)

    tree = ElementTree.ElementTree(root)
    xml_file_path = "specimen_" + number + ".fhir.xml"
    tree.write(xml_file_path)


# not my code below
# source: https://www.tutorialspoint.com/pretty-printing-xml-in-python
def indent(elem, level=0):
    # Add indentation
    indent_size = "  "
    i = "\n" + level * indent_size
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + indent_size
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def pretty_print_xml_elementtree(xml_string):
    # Parse the XML string
    root = ElementTree.fromstring(xml_string)

    # Indent the XML
    indent(root)

    # Convert the XML element back to a string
    pretty_xml = ElementTree.tostring(root, encoding="unicode")

    # Print the pretty XML
    print(pretty_xml)


if __name__ == '__main__':
    data = read_xml_and_feed_the_classes()
    i = 0
    for record in data:
        i += 1
        create_outputs(record[0], record[1], record[2], str(i))
