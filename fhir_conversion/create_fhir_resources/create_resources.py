import fhirclient.models.patient as p
import fhirclient.models.condition as c
import fhirclient.models.specimen as s
from fhirclient.models.fhirdate import FHIRDate
import fhirclient.models.codeableconcept as codeAbleConcept
from fhirclient.models.coding import Coding
from fhirclient.models.fhirreference import FHIRReference
from fhirclient.models.age import Age
from fhirclient.models.specimen import SpecimenCollection
from datetime import date


def create_resources(patient, condition, specimen, smart_client):
    patient_json = create_patient(patient, smart_client)
    create_condition(condition, patient_json, smart_client)
    create_specimen(patient_json, specimen, smart_client)


def create_patient(patient_info, smart_client):
    patient = p.Patient()
    year_of_birth = str(date.today().year - int(patient_info.age))
    patient.birthDate = FHIRDate(year_of_birth)
    patient.gender = patient_info.sex
    # TODO zeptat se, co s identifierem
    # patient.identifier = patient_info.identifier

    response = store_resources(smart_client, patient, "Patient")
    resource_on_server = response.content
    index_id = resource_on_server.rfind(b"id") + 5
    return resource_on_server[index_id:index_id+16].decode("utf-8")


def create_condition(condition_info, patient_id, smart_client):
    condition = c.Condition()
    # TODO má date ve správném pořadí měsíce a dny?
    condition.recordedDate = FHIRDate(condition_info.date_diagnosis)

    # Clinical Status
    text = "Unknown"

    coding = Coding()
    coding.code = "unknown"
    coding.display = "Unknown"
    coding.system = "http://terminology.hl7.org/CodeSystem/condition-clinical"

    clinicalStatus = codeAbleConcept.CodeableConcept()
    clinicalStatus.coding = coding
    clinicalStatus.text = text

    # onset
    age = Age()
    age.value = int(condition_info.age_at_primary_diagnosis)
    condition.onsetAge = age

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
    coding.system = "http://hl7.org/fhir/us/central-cancer-registry-reporting/ValueSet/cancer-core-reportability-codes"

    text = code + ": " + mapping[code]

    code_in_json = codeAbleConcept.CodeableConcept()
    code_in_json.text = text
    code_in_json.coding = [coding]

    condition.code = code_in_json

    store_resources(smart_client, condition, "Condition")


def create_specimen(patient_id, specimen_info, smart_client):
    specimen = s.Specimen()

    # collection collected
    collection = SpecimenCollection()
    collection.collectedDateTime = FHIRDate(specimen_info.year_of_sample_connection)
    specimen.collection = collection

    # type
    type = codeAbleConcept.CodeableConcept()
    # TODO I don't know, which code system I should use
    type.text = specimen_info.sample_material_type
    specimen.type = type

    # subject
    specimen.subject = FHIRReference({'reference': "Patient/" + patient_id})

    store_resources(smart_client, specimen, "Specimen")


def store_resources(smart_client, file, type):
    server = smart_client.server
    resource = file.as_json()
    return server.post_json(path=type, resource_json=resource)


# http://hl7.org/fhir
# http://terminology.hl7.org/CodeSystem/condition-clinical
# http://terminology.hl7.org/CodeSystem/condition-ver-status
# http://fhir.de/CodeSystem/bfarm/icd-10-gm
# http://fhir.de/StructureDefinition/CodingICD10GM
