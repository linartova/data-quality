from fhirclient import client
import xml.etree.ElementTree as ElementTree
import fhirclient.models.patient as p
import fhirclient.models.condition as c
import fhirclient.models.specimen as s
from fhirclient.models.fhirdate import FHIRDate
import fhirclient.models.codeableconcept as codeAbleConcept
from fhirclient.models.coding import Coding
from fhirclient.models.fhirreference import FHIRReference
from fhirclient.models.specimen import SpecimenCollection
from fhirclient.models.identifier import Identifier
from datetime import date


class Patient:
    def __init__(self, identifier, sex, age):
        self.identifier = identifier
        self.sex = sex
        self.age = age


class Condition:
    def __init__(self, histopathology, date_diagnosis):
        self.date_diagnosis = date_diagnosis
        self.histopathology = histopathology


class Specimen:
    def __init__(self, sample_material_type, year_of_sample_connection):
        self.year_of_sample_connection = year_of_sample_connection
        self.sample_material_type = sample_material_type


def provide_server_connection(url):
    settings = {
        'app_id': 'my_web_app',
        'api_base': url
    }
    smart = client.FHIRClient(settings=settings)
    assert not smart.ready
    smart.prepare()
    assert smart.ready
    assert smart.authorize_url is None
    return smart


def read_xml_and_create_resources(file_name, smart):
    tree = ElementTree.parse(file_name)
    root = tree.getroot()
    namespace = "{http://registry.samply.de/schemata/import_v1}"
    result = []
    for element in root.iter():
        if element.tag == namespace + "BHPatient":
            # patient
            patient_id = element.find(namespace + "Identifier").text
            form = element.find(namespace +
                                "Locations").find(namespace +
                                                  "Location").find(namespace +
                                                                   "BasicData").find(namespace +
                                                                                     "Form")
            sex = form.find(namespace + "Dataelement_85_1")
            age_at_primary_diagnostic = form.find(namespace + "Dataelement_3_1")

            # condition
            date_diagnosis = form.find(namespace + "Dataelement_51_3")
            events = element.find(namespace + "Locations").find(namespace + "Location").find(namespace + "Events")
            histopathology = find_histopathology(namespace, events)

            # specimen
            specimens = find_specimens(namespace, events)

            result.append([Patient(patient_id, sex.text, age_at_primary_diagnostic.text),
                           Condition(histopathology.text, date_diagnosis.text),
                           specimens])
    create_files(result, smart)


def find_specimens(namespace, events):
    result = []
    for event in events.findall(namespace + "Event"):
        if "eventtype" in event.attrib and event.attrib.get("eventtype") == "Sample":

            sample = event.find(namespace + "LogitudinalData").find(namespace + "Form1")
            year_of_sample_connection = sample.find(namespace + "Dataelement_89_3").text
            sample_material_type = sample.find(namespace + "Dataelement_54_2").text

            result.append(Specimen(sample_material_type, year_of_sample_connection))
    return result


def find_histopathology(namespace, events):
    for event in events.findall(namespace + "Event"):
        if event.attrib.get("eventtype") == "Histopathology":
            return event.find(namespace + "LogitudinalData").find(namespace + "Form2").find(
                namespace + "Dataelement_92_1")


def create_resources(patient, condition, specimens, smart_client):
    patient_url = create_patient(patient, smart_client)
    condition_url = create_condition(condition, patient_url, smart_client)
    specimen_urls = []
    for specimen in specimens:
        specimen_urls.append(create_specimen(patient_url, specimen, smart_client))
    return patient_url, condition_url, specimen_urls


def create_patient(patient_info, smart_client):
    patient = p.Patient()
    year_of_birth = str(date.today().year - int(patient_info.age))
    patient.birthDate = FHIRDate(year_of_birth)
    patient.gender = patient_info.sex
    patient.identifier = [Identifier()]
    patient.identifier[0].value = patient_info.identifier

    response = store_resources(smart_client, patient, "Patient")
    resource_on_server = response.content
    index_id = resource_on_server.rfind(b'"id"') + 6
    return resource_on_server[index_id:index_id+16].decode("utf-8")


def create_condition(condition_info, patient_id, smart_client):
    condition = c.Condition()
    condition.recordedDate = FHIRDate(condition_info.date_diagnosis)

    # Clinical Status
    text = "Unknown"

    coding = Coding()
    coding.code = "unknown"
    coding.display = "Unknown"
    coding.system = "http://terminology.hl7.org/CodeSystem/condition-clinical"

    clinical_status = codeAbleConcept.CodeableConcept()
    clinical_status.coding = [coding]

    condition.clinicalStatus = clinical_status

    # onsetDateTime
    date_time = FHIRDate(condition_info.date_diagnosis)
    condition.onsetDateTime = date_time

    # subject (patient)
    condition.subject = FHIRReference({'reference': "Patient/" + patient_id})

    # code
    mapping = {"C18.0": "Malignant neoplasm of cecum",
               "C18.1": "Malignant neoplasm of appendix",
               "C18.2": "Malignant neoplasm of ascending colon",
               "C18.3": "Malignant neoplasm of hepatic flexure",
               "C18.4": "Malignant neoplasm of transverse colon",
               "C18.5": "Malignant neoplasm of splenic flexure",
               "C18.6": "Malignant neoplasm of descending colon",
               "C18.7": "Malignant neoplasm of sigmoid colon",
               "C18.8": "Malignant neoplasm of overlapping sites of colon",
               "C18.9": "Malignant neoplasm of colon, unspecified",
               "C19": "Malignant neoplasm of rectosigmoid junction",
               "C20": "Malignant neoplasm of rectum"}
    diagnosis_index = condition_info.histopathology.find("C", -5)
    code = condition_info.histopathology[diagnosis_index:]
    coding = Coding()
    coding.code = code
    coding.display = mapping[code]
    coding.system = "http://hl7.org/fhir/sid/icd-10"

    text = code + ": " + mapping[code]

    code_in_json = codeAbleConcept.CodeableConcept()
    code_in_json.text = text
    code_in_json.coding = [coding]

    condition.code = code_in_json

    response = store_resources(smart_client, condition, "Condition")
    resource_on_server = response.content
    index_id = resource_on_server.rfind(b'"id"') + 6
    return resource_on_server[index_id:index_id + 16].decode("utf-8")


def create_specimen(patient_id, specimen_info, smart_client):
    specimen = s.Specimen()

    # collection collected
    collection = SpecimenCollection()
    collection.collectedDateTime = FHIRDate(specimen_info.year_of_sample_connection)
    specimen.collection = collection

    # type
    type = codeAbleConcept.CodeableConcept()
    type.text = specimen_info.sample_material_type
    specimen.type = type

    # subject
    specimen.subject = FHIRReference({'reference': "Patient/" + patient_id})

    response = store_resources(smart_client, specimen, "Specimen")
    resource_on_server = response.content
    index_id = resource_on_server.rfind(b'"id"') + 6
    return resource_on_server[index_id:index_id + 16].decode("utf-8")


def store_resources(smart_client, file, type):
    server = smart_client.server
    resource = file.as_json()
    return server.post_json(path=type, resource_json=resource)


def create_files(data, smart_client):
    # resources
    patients = []
    conditions = []
    specimens = []
    for record in data:
        patient_url, condition_url, specimen_urls = create_resources(record[0], record[1], record[2], smart_client)
        patients.append(patient_url)
        conditions.append(condition_url)
        specimens = specimen_urls
    file_patients_ids = open("patients_ids.txt", "w")
    file_conditions_ids = open("conditions_ids.txt", "w")
    file_specimens_ids = open("specimens_ids.txt", "w")
    for record in patients:
        file_patients_ids.write(record + "\n")
    for record in conditions:
        file_conditions_ids.write(record + "\n")
    for record in specimens:
        file_specimens_ids.write(record + "\n")
    file_patients_ids.close()
    file_conditions_ids.close()
    file_specimens_ids.close()


# todo smazání zbytečných souborů a částí kódu
