import xml.etree.ElementTree as ElementTree
from create_fhir_resources.fhir_conversion_classes import Patient, Specimen, Condition


def read_xml_and_create_classes(file_name):
    tree = ElementTree.parse(file_name)
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
            result.append([Patient(patient_id, sex.text, age_at_primary_diagnostic.text),
                           Condition(histopathology.text, date_diagnosis.text),
                           Specimen(sample_material_type.text, year_of_sample_connection.text)])
    return result


def find_histopathology(namespace, events):
    for event in events.findall(namespace + "Event"):
        if event.attrib.get("eventtype") == "Histopathology":
            return event.find(namespace + "LogitudinalData").find(namespace + "Form2").find(
                namespace + "Dataelement_92_1")


def find_sample(namespace, events):
    for event in events.findall(namespace + "Event"):
        if event.attrib.get("eventtype") == "Sample":
            return event.find(namespace + "LogitudinalData").find(namespace + "Form1").find(
                namespace + "Dataelement_89_3")


def find_sample_material(namespace, events):
    for event in events.findall(namespace + "Event"):
        if event.attrib.get("eventtype") == "Sample":
            return event.find(namespace + "LogitudinalData").find(namespace + "Form1").find(
                namespace + "Dataelement_54_2")
