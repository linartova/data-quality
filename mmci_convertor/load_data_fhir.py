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
from datetime import datetime
from fhir_classes import Specimen, Patient, Condition
from quality_checks_fhir import *


def provide_server_connection(url):
    """
    Connects to FHIR server.

    :param url: The url of FHIR server.
    :return:
        FHIR client.
    """
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
    """
    Parse input file, process data, store them on FHIR server.

    :param file_name: The path of input file.
    :param smart: FHIR client.
    :return:
        None
    """
    tree = ElementTree.parse("uploads/" + file_name)
    root = tree.getroot()
    namespace = "{http://registry.samply.de/schemata/import_v1}"
    result = []
    for element in root.iter():
        if element.tag == namespace + "BHPatient":
            # patient
            if element.find(namespace + "Identifier") is not None:
                patient_id = element.find(namespace + "Identifier").text
            else:
                patient_id = None
            form = element.find(namespace +
                                "Locations").find(namespace +
                                                  "Location").find(namespace +
                                                                   "BasicData").find(namespace +
                                                                                     "Form")
            if form.find(namespace + "Dataelement_85_1") is not None:
                sex = form.find(namespace + "Dataelement_85_1").text
            else:
                sex = None

            if form.find(namespace + "Dataelement_3_1") is not None:
                age_at_primary_diagnostic = form.find(namespace + "Dataelement_3_1").text
            else:
                age_at_primary_diagnostic = None

            # condition
            date_diagnosis = form.find(namespace + "Dataelement_51_3")
            if date_diagnosis is not None:
                date_diagnosis = date_diagnosis.text

                # patient
                diagnosis = datetime.strptime(date_diagnosis, "%Y-%m-%d")
                if age_at_primary_diagnostic is not None:
                    birth_date = FHIRDate(str(diagnosis.year - int(age_at_primary_diagnostic)))
                else:
                    birth_date = None
            else:
                date_diagnosis = None
                birth_date = None
            patient = Patient(patient_id, sex, birth_date)
            events = element.find(namespace + "Locations").find(namespace + "Location").find(namespace + "Events")
            if find_histopathology(namespace, events) is not None:
                histopathology = find_histopathology(namespace, events).text
            else:
                histopathology = None

            # specimen
            specimens = find_specimens(namespace, events).copy()

            result.append([patient,
                           Condition(histopathology, date_diagnosis),
                           specimens])
    create_files(result, smart)
    return None


def find_specimens(namespace, events):
    """
    Create a list of all specimens of one patient.

    :param namespace: The namespace of file.
    :param events: XML element, where Specimens can be stored.
    :return:
        List of all specimens.
    """
    result = []
    for event in events.findall(namespace + "Event"):
        if "eventtype" in event.attrib and event.attrib.get("eventtype") == "Sample":

            sample = event.find(namespace + "LogitudinalData").find(namespace + "Form1")
            if sample.find(namespace + "Dataelement_89_3") is not None:
                year_of_sample_connection = int(sample.find(namespace + "Dataelement_89_3").text)
            else:
                year_of_sample_connection = None

            if sample.find(namespace + "Dataelement_54_2") is not None:
                sample_material_type = sample.find(namespace + "Dataelement_54_2").text
            else:
                sample_material_type = None

            if sample.find(namespace + "Dataelement_55_2") is not None:
                preservation_mode = sample.find(namespace + "Dataelement_55_2").text
            else:
                preservation_mode = None

            if sample.find(namespace + "Dataelement_56_2") is not None:
                identifier = sample.find(namespace + "Dataelement_56_2").text
            else:
                identifier = None

            code, display = specimen_mapping(sample_material_type, preservation_mode)

            result.append(Specimen(identifier, code, display, year_of_sample_connection))
    return result


def specimen_mapping(sample_material_type, preservation_mode):
    """
    Map original value of "Material type" dataelement and "Preservation mode" dataelement into FHIR code and display.
    Args:
        sample_material_type: original value of "Material type"
        preservation_mode: original value of "Preservation mode"

    Returns: code and display values based on original value

    """
    if sample_material_type == "Tumor" and preservation_mode == "Cryopreservation":
        return "tumor-tissue-frozen", "Tumor tissue (frozen)"
    if sample_material_type == "Tumor" and preservation_mode == "FFPE":
        return "tumor-tissue-ffpe", "Tumor tissue (FFPE)"
    if sample_material_type == "Tumor" and preservation_mode == "Other":
        return "tissue-other", "Other tissue storage"
    if sample_material_type == "Healthy colon tissue" and preservation_mode == "Cryopreservation":
        return "normal-tissue-frozen", "Normal tissue (frozen)"
    if sample_material_type == "Healthy colon tissue" and preservation_mode == "FFPE":
        return "normal-tissue-ffpe", "Normal tissue (FFPE)"
    if sample_material_type == "Healthy colon tissue" and preservation_mode == "Other":
        return "tissue-other", "Other tissue storage"
    if sample_material_type == "Other" and preservation_mode == "Cryopreservation":
        return "other-tissue-frozen", "Other tissue (frozen)"
    if sample_material_type == "Other" and preservation_mode == "FFPE":
        return "other-tissue-ffpe", "Other tissue (FFPE)"
    if sample_material_type == "Other" and preservation_mode == "Other":
        return "tissue-other", "Other tissue storage"
    return None, None


def find_histopathology(namespace, events):
    """
    Find a localization of primary tumor in form Histopathology.

    :param namespace: The namespace of file.
    :param events: XML element, where Histopathology can be stored.
    :return:
        The element with localization of primary tumor.
    """
    for event in events.findall(namespace + "Event"):
        if event.attrib.get("eventtype") == "Histopathology":
            return event.find(namespace + "LogitudinalData").find(namespace + "Form2").find(
                namespace + "Dataelement_92_1")


def create_resources(patient, condition, specimens, smart_client):
    """
    Create and store resources for one patient on FHIR server.

    :param patient: The instance of class Patient.
    :param condition: The instance of class Condition.
    :param specimens: List of instances of class Specimen.
    :param smart_client: The FHIR client.
    :return:
        patient_url: The url of Resource Patient.
        condition_url: The url of Resource Condition.
        specimen_urls: The urls of Resources Specimen
    """
    patient_url = create_patient(patient, smart_client)
    condition_url = create_condition(condition, patient_url, smart_client)
    specimen_urls = []
    for specimen in specimens:
        specimen_urls.append(create_specimen(patient_url, specimen, smart_client))
    return patient_url, condition_url, specimen_urls


def create_patient(patient_info, smart_client):
    """
    Create and store the Resource Patient on FHIR server.

    :param patient_info: The instance of class Patient.
    :param smart_client: The FHIR client.
    :return:
        The url of Resource Patient.
    """
    patient = p.Patient()
    if patient_info.birth_date is not None:
        patient.birthDate = patient_info.birth_date
    if patient_info.sex is not None:
        patient.gender = patient_info.sex
    patient.identifier = [Identifier()]
    if patient_info.identifier is not None:
        patient.identifier[0].value = patient_info.identifier

    response = store_resources(smart_client, patient, "Patient")
    resource_on_server = response.content
    index_id = resource_on_server.rfind(b'"id"') + 6
    return resource_on_server[index_id:index_id+16].decode("utf-8")


def create_condition(condition_info, patient_id, smart_client):
    """
    Create and store the Resource Condition on FHIR server.

    :param condition_info: The instance of class Condition.
    :param patient_id: The url of relevant Resource Patient.
    :param smart_client: The FHIR client.
    :return:
        The url of Resource Condition.
    """
    condition = c.Condition()
    if condition_info.date_diagnosis is not None:
        condition.recordedDate = FHIRDate(condition_info.date_diagnosis)

    # Clinical Status

    coding = Coding()
    coding.code = "unknown"
    coding.display = "Unknown"
    coding.system = "http://terminology.hl7.org/CodeSystem/condition-clinical"

    clinical_status = codeAbleConcept.CodeableConcept()
    clinical_status.coding = [coding]

    condition.clinicalStatus = clinical_status

    # onsetDateTime
    if condition_info.date_diagnosis is not None:
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
    if condition_info.histopathology is not None:
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
    """
    Create and store the Resource Specimen on FHIR server.

    :param patient_id: The url of relevant Resource Patient.
    :param specimen_info: The instance of class Specimen.
    :param smart_client: The FHIR client.
    :return:
        The url of Resource Specimen.
    """
    specimen = s.Specimen()

    # identifier
    if specimen_info.identifier is not None:
        identifier = s.identifier.Identifier()
        identifier.value = specimen_info.identifier
        specimen.identifier = [identifier]

    # type.coding (code, display, system)
    coding = Coding()
    if specimen_info.sample_material_type_code is not None:
        coding.code = specimen_info.sample_material_type_code
    if specimen_info.sample_material_type_display is not None:
        coding.display = specimen_info.sample_material_type_display
    coding.system = "“https://fhir.bbmri.de/CodeSystem/SampleMaterialType"

    type = codeAbleConcept.CodeableConcept()
    type.coding = [coding]

    specimen.type = type

    # collection collected
    collection = SpecimenCollection()
    if specimen_info.year_of_sample_connection is not None:
        collection.collectedDateTime = FHIRDate(str(specimen_info.year_of_sample_connection))
    specimen.collection = collection

    # type
    # type = codeAbleConcept.CodeableConcept()
    # type.text = specimen_info.sample_material_type
    # specimen.type = type

    # subject
    specimen.subject = FHIRReference({'reference': "Patient/" + patient_id})

    response = store_resources(smart_client, specimen, "Specimen")
    resource_on_server = response.content
    index_id = resource_on_server.rfind(b'"id"') + 6
    return resource_on_server[index_id:index_id + 16].decode("utf-8")


def store_resources(smart_client, file, type):
    """
    Store resources on FHIR server.

    :param smart_client: The FHIR client.
    :param file: FHIR model, precursor of FHIR json.
    :param type: Type of Resource.
    :return:
    """
    server = smart_client.server
    resource = file.as_json()
    return server.post_json(path=type, resource_json=resource)


def create_files(data, smart_client):
    """
    Create files with Resurces IDs for further processing.

    :param data: Data prepared in the list of instances of classes: Patient, Condition, Specimen.
    :param smart_client: The FHIR client.
    :return:
        None
    """
    # resources
    patients = []
    conditions = []
    specimens = []
    for record in data:
        patient_url, condition_url, specimen_urls = create_resources(record[0], record[1], record[2], smart_client)
        patients.append(patient_url)
        conditions.append(condition_url)
        specimens += specimen_urls
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
    return None


def create_graphs(file_name, client):
    """
    Store data from file_name in provided server, then create
    pandas dataframes and run all quality checks from quality_checks_fhir.py

    Args:
        file_name: Name of input file with data.
        client: FHIR client.

    Returns:
        List of figures from data quality checks.

    """
    read_xml_and_create_resources(file_name, client)

    pdf = create_patient_data_frame(client.server)
    sdf = create_specimen_data_frame(client.server)
    cdf = create_condition_data_frame(client.server)

    graphs = []
    p_completeness = completeness(pdf).to_json()
    graphs.append(p_completeness)
    s_completeness = completeness(sdf).to_json()
    graphs.append(s_completeness)
    c_completeness = completeness(cdf).to_json()
    graphs.append(c_completeness)

    p_uniqueness = uniqueness(pdf, "patient").to_json()
    graphs.append(p_uniqueness)
    s_uniqueness = uniqueness(pdf, "specimen").to_json()
    graphs.append(s_uniqueness)
    c_uniqueness = uniqueness(pdf, "condition").to_json()
    graphs.append(c_uniqueness)

    p_conformance = conformance_patient(pdf).to_json()
    graphs.append(p_conformance)
    c_conformance = conformance_condition(cdf).to_json()
    graphs.append(c_conformance)
    s_conformance = conformance_specimen(sdf).to_json()
    graphs.append(s_conformance)

    s_conformance_r = conformance_relational(sdf, client.server).to_json()
    graphs.append(s_conformance_r)
    c_conformance_r = conformance_relational(cdf, client.server).to_json()
    graphs.append(c_conformance_r)
    conformance_c = conformance_computational(pdf, sdf, cdf).to_json()
    graphs.append(conformance_c)

    age = age_at_primary_diagnosis(pdf, cdf).to_json()
    graphs.append(age)
    diagnosis = diagnosis_in_future(cdf).to_json()
    graphs.append(diagnosis)
    missing = missing_collection_collectedDateTime(pdf, sdf).to_json()
    graphs.append(missing)
    patients_without_specimen = patients_without_specimen_type_text(pdf, sdf).to_json()
    graphs.append(patients_without_specimen)

    patients = patients_without_condition_values(pdf, cdf).to_json()
    graphs.append(patients)

    return graphs