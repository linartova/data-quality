from typing import List

import psycopg2
import xml.etree.ElementTree as ElementTree
from collections import deque
from datetime import datetime, timedelta


class Patient:
    def __init__(self, identifier, sex, year_of_birth):
        self.gender_concept_id = sex
        self.year_of_birth = year_of_birth
        self.person_source_value = identifier


class ObservationPeriod:
    def __init__(self, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date


class ConditionOccurrence:
    def __init__(self, histopathology, date_diagnosis):
        self.condition_concept_id = histopathology
        self.condition_start_date = date_diagnosis
        self.condition_source_value = histopathology


class Specimen:
    def __init__(self, sample_material_type, year_of_sample_connection, sample_id):
        self.specimen_concept_id = sample_material_type
        self.specimen_date = year_of_sample_connection
        self.specimen_source_id = sample_id
        self.specimen_source_value = sample_material_type


class DrugExposure:
    def __init__(self, drug_concept_id, drug_exposure_start_date, drug_exposure_end_date, drug_source_value):
        self.drug_concept_id = drug_concept_id
        self.drug_exposure_start_date = drug_exposure_start_date
        self.drug_exposure_start_datetime = drug_exposure_start_date
        self.drug_exposure_end_date = drug_exposure_end_date
        self.drug_exposure_end_datetime = drug_exposure_end_date
        self.drug_source_value = drug_source_value


class ProcedureOccurrence:
    def __init__(self, procedure_concept_id, procedure_date, procedure_source_value):
        self.procedure_concept_id = procedure_concept_id
        self.procedure_date = procedure_date
        self.procedure_source_value = procedure_source_value



def read_xml_and_parse(file_name):
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
            sex = form.find(namespace + "Dataelement_85_1").text
            date_diagnosis = form.find(namespace + "Dataelement_51_3").text
            age_at_primary_diagnostic = form.find(namespace + "Dataelement_3_1").text
            year_of_birth = int(date_diagnosis[:4]) - int(age_at_primary_diagnostic)

            # observation period
            events = element.find(namespace + "Locations").find(namespace + "Location").find(namespace + "Events")
            observation_start_date = find_observation_start_date(namespace, events)
            observation_end_date = form.find(namespace + "Dataelement_6_3").text

            # condition occurrence
            histopathology = find_histopathology(namespace, events).text

            # specimen
            specimens = find_specimens(namespace, events)

            # drug exposure
            diagnosis = datetime.strptime(date_diagnosis, "%Y-%m-%d")
            drug_exposures = find_drug_exposures(namespace, events, diagnosis)

            # procedure occurrence
            procedures = find_procedures(namespace, events, diagnosis)
            procedures = procedures + find_diagnostic_procedures(namespace, form, date_diagnosis)
            # initialize classes
            result.append([Patient(patient_id, sex, year_of_birth),
                           ObservationPeriod(observation_start_date, observation_end_date),
                           ConditionOccurrence(histopathology, date_diagnosis),
                           specimens,
                           drug_exposures,
                           procedures])
    return result


# todo napsat docs o tom datu diagnoz
def find_diagnostic_procedures(namespace, form, diagnosis):
    result = []
    # liver_imaging
    liver_imaging = form.find(namespace + "Dataelement_61_5").text
    if liver_imaging.find("Liver imaging - Done") != -1:
        result.append(ProcedureOccurrence(4085576, diagnosis, "liver imaging"))

    # ct
    ct = form.find(namespace + "Dataelement_31_3").text
    if ct.find("CT - Done") != -1:
        result.append(ProcedureOccurrence(4019823, diagnosis, "CT"))


    # colonoscopy
    colonoscopy = form.find(namespace + "Dataelement_88_1").text
    if colonoscopy.find("Colonoscopy diagnostic exam - Positive") != -1:
        result.append(ProcedureOccurrence(4249893, diagnosis, "colonoscopy"))


    # lung_imaging
    lung_imaging = form.find(namespace + "Dataelement_63_4").text
    if lung_imaging.find("Lung imaging - Done") != -1:
        result.append(ProcedureOccurrence(4082968, diagnosis, "lung imaging"))

    # mri
    mri = form.find(namespace + "Dataelement_30_3").text
    if mri.find("MRI - Done") != -1:
        result.append(ProcedureOccurrence(4013636, diagnosis, "MRI - Done"))


    return result


def surgery_mapping(primary_surgery, secondary_surgery):
    code_mapping = {"Abdomino-perineal resection": 4144721,
                    "Anterior resection of rectum": 4166855,
                    "Endo-rectal tumor resection": None,
                    "Left hemicolectomy": 4219780,
                    "Low anteroir colon resection": None,
                    "Pan-procto colectomy": None,
                    "Right hemicolectomy": 4233412,
                    "Sigmoid colectomy": 4225427,
                    "Total colectomy": 4096461,
                    "Transverse colectomy": 4097958,
                    "Other": None}
    surgery = primary_surgery if primary_surgery != "Other" else secondary_surgery
    for code in code_mapping.keys():
        if surgery == code:
            return code, code_mapping.get(code)
    return "Other", None


def find_specimens(namespace, events):
    result = []
    for event in events.findall(namespace + "Event"):
        if "eventtype" in event.attrib and event.attrib.get("eventtype") == "Sample":
            sample = event.find(namespace + "LogitudinalData").find(namespace + "Form1")

            year_of_sample_connection = sample.find(namespace + "Dataelement_89_3").text
            sample_material_type = sample.find(namespace + "Dataelement_54_2").text
            sample_id = sample.find(namespace + "Dataelement_56_2").text

            result.append(Specimen(sample_material_type, year_of_sample_connection, sample_id))
    return result


# todo udělat docs o mapování drug_source_value
def find_drug_exposures(namespace, events, diagnosis):
    result = []
    for event in events:
        if "eventtype" in event.attrib and event.attrib.get("eventtype") == "Pharmacotherapy":
            pharmacotherapy = event.find(namespace + "LogitudinalData").find(namespace + "Form3")

            drug_source_value = pharmacotherapy.find(namespace + "Dataelement_59_5").text
            if drug_source_value is None or drug_source_value == "Other":
                drug_source_value = pharmacotherapy.find(namespace + "Dataelement_81_3").text

            drug_concept_id = drug_exposure_mapping(drug_source_value)

            start_week = int(pharmacotherapy.find(namespace + "Dataelement_10_2").text)
            end_week = int(pharmacotherapy.find(namespace + "Dataelement_11_2").text)

            drug_exposure_start_date = diagnosis + timedelta(weeks=start_week)
            drug_exposure_end_date = diagnosis + timedelta(weeks=end_week)

            if len(drug_source_value) > 50:
                drug_source_value = None

            if drug_concept_id is not None:
                result.append(DrugExposure(drug_concept_id, drug_exposure_start_date,
                                       drug_exposure_end_date, drug_source_value))
    return result


# todo to že je kdekoliv v tomto skriptu ".text" aniž bych ověřovala, zda to není None,
# todo je náběh na spoustu errorů
# todo udělat tady docs ohledně targeted therapy
def find_procedures(namespace, events, initial_diagnosis):
    result = []
    for event in events.findall(namespace + "Event"):
        if event.attrib.get("eventtype") == "Diagnostic examination":
            result.append(ProcedureOccurrence(4249893, None, "colonoscopy"))

        elif event.attrib.get("eventtype") == "Surgery":
            primary_surgery = event.find(namespace + "LogitudinalData").find(namespace + "Form").find(
                namespace + "Dataelement_49_1").text
            secondary_surgery_node = event.find(namespace + "LogitudinalData").find(namespace + "Form").find(
                namespace + "Dataelement_67_1")
            secondary_surgery = None if secondary_surgery_node is None else secondary_surgery_node.text
            surgery_name, surgery_code = surgery_mapping(primary_surgery, secondary_surgery)
            start_week = int(event.find(namespace + "LogitudinalData").find(namespace + "Form").find(
                namespace + "Dataelement_8_3").text)
            date = initial_diagnosis + timedelta(weeks=start_week)
            if surgery_code is not None:
                result.append(ProcedureOccurrence(surgery_code, date, surgery_name))

        elif event.attrib.get("eventtype") == "Radiation therapy":
            start_week = int(event.find(namespace + "LogitudinalData").find(namespace + "Form5").find(
                namespace + "Dataelement_12_4").text)
            date = initial_diagnosis + timedelta(weeks=start_week)
            result.append(ProcedureOccurrence(4029715, date, "Radiation therapy"))

        # elif event.attrib.get("eventtype") == "Targeted Therapy":
        #     start_week = int(event.find(namespace + "LogitudinalData").find(namespace + "Form6").find(
        #         namespace + "Dataelement_35_3").text)
        #     date = initial_diagnosis + timedelta(weeks=start_week)
        #     result.append(ProcedureOccurrence(None, date, "Targeted therapy"))
    return result


def find_histopathology(namespace, events):
    for event in events.findall(namespace + "Event"):
        if event.attrib.get("eventtype") == "Histopathology":
            return event.find(namespace + "LogitudinalData").find(namespace + "Form2").find(
                namespace + "Dataelement_92_1")


def find_observation_start_date(namespace, events):
    year_of_sample_collection = []
    for event in events.findall(namespace + "Event"):
        if "eventtype" in event.attrib:
            if event.attrib["eventtype"] == "Sample":
                year_of_sample_collection.append((event.find(namespace + "LogitudinalData").find(namespace + "Form1").find(
                    namespace + "Dataelement_89_3")).text)
    years = [datetime.strptime(year, '%Y') for year in year_of_sample_collection]
    return min(years)


def retrieve_max_ids(cursor, schema, table):
    cursor.execute("SELECT MAX(" + table + "_" + "id) FROM " + schema + "." + table)
    highest_id = cursor.fetchone()[0]
    if highest_id is None:
        ids = 0
    else:
        ids = highest_id + 1
    return ids


def put_data_into_right_types(data, cursor):
    result = []
    person_ids = retrieve_max_ids(cursor, schema, "person")
    observation_ids = retrieve_max_ids(cursor, schema, "observation_period")
    condition_ids = retrieve_max_ids(cursor, schema, "condition_occurrence")
    specimen_ids = retrieve_max_ids(cursor, schema, "specimen")
    drug_ids = retrieve_max_ids(cursor, schema, "drug_exposure")
    procedure_ids = retrieve_max_ids(cursor, schema, "procedure_occurrence")
    for record in data:
        person = create_person_data(record[0], person_ids)
        observation_period = create_observation_period_data(record[1], observation_ids, person_ids)
        condition_occurrence = create_condition_occurrences_data(record[2], condition_ids, person_ids)
        specimen, specimen_ids = create_specimens(record[3], specimen_ids, person_ids)
        drug_exposure, drug_ids = create_drug_exposures(record[4], drug_ids, person_ids)
        procedure_occurrences, procedure_ids = create_procedure_occurrences(record[5], procedure_ids, person_ids)
        result.append(
            (person, observation_period, condition_occurrence, specimen, drug_exposure, procedure_occurrences))
        person_ids += 1
        observation_ids += 1
        condition_ids += 1
    return result


def create_person_data(person: Patient, ids):
    if person.gender_concept_id == "male":
        gender = 8507
    elif person.gender_concept_id == "female":
        gender = 8532
    else:
        gender = 8521
    source_value = person.person_source_value
    return [ids, gender, person.year_of_birth, 0, 0, source_value, person.gender_concept_id]


def create_observation_period_data(observation: ObservationPeriod, ids, person_ids):
    return [ids, person_ids, observation.start_date,
            datetime.strptime(observation.end_date, '%Y-%m-%d').date(), 32809]


def condition_mapping_codes(condition):
    codes_mapping = {"C18.0": 432837,
                     "C18.1": 433143,
                     "C18.2": 4247719,
                     "C18.3": 438979,
                     "C18.4": 432257,
                     "C18.5": 437798,
                     "C18.6": 441800,
                     "C18.7": 436635,
                     "C19": 438699,
                     "C20": 74582}
    for code in codes_mapping.keys():
        if condition.find(code) != -1:
            return codes_mapping.get(code)
    return None


def condition_mapping_names(condition):
    codes_mapping = {"C18.0": "C 18.0 - Caecum",
                     "C18.1": "C 18.1 - Appendix",
                     "C18.2": "C 18.2 - Ascending colon",
                     "C18.3": "C 18.3 - Hepatic flexure",
                     "C18.4": "C 18.4 - Transverse colon",
                     "C18.5": "C 18.5 - Splenic flexure",
                     "C18.6": "C 18.6 - Descending colon",
                     "C18.7": "C 18.7 - Sigmoid colon",
                     "C19": "C 19 - Rectosigmoid junction ",
                     "C20": "C 20 - Rectum"}
    for code in codes_mapping.keys():
        if condition.find(code) != -1:
            return codes_mapping.get(code)
    return None


def create_condition_occurrences_data(condition: ConditionOccurrence, ids, person_ids):
    return [ids, person_ids, condition_mapping_codes(condition.condition_concept_id),
            datetime.strptime(condition.condition_start_date, '%Y-%m-%d').date(), 32809,
            condition_mapping_names(condition.condition_source_value)]


def specimen_mapping_numbers(specimen):
    if specimen == "Healthy colon tissue":
        return 4134449
    elif specimen == "Tumor":
        return 4122248
    else:
        return 4163599


def specimen_mapping_names(specimen):
    if specimen == "Healthy colon tissue":
        return "Healthy colon tissue"
    elif specimen == "Tumor":
        return "Tumor tissue"
    else:
        return "Other"


def create_specimens(specimens: List[Specimen], ids, person_ids):
    result = []
    for specimen in specimens:
        result.append([ids, person_ids, specimen_mapping_numbers(specimen.specimen_concept_id), 32809,
            datetime.strptime(specimen.specimen_date, '%Y').date(),
            specimen.specimen_source_id, specimen_mapping_names(specimen.specimen_source_value)])
        ids += 1
    return result, ids


def drug_exposure_mapping(drug_concept_id):
    drug_mapping = {"5-FU": 40042274,
                    "Capecitabine": 40095743,
                    "Oxaliplatin": 35603923,
                    "UFT": 40052183,
                    "Other": 0}
    for drug in drug_mapping.keys():
        if drug_concept_id.find(drug) != -1:
            return drug_mapping.get(drug)
    return 0


def create_drug_exposures(drug_exposures: List[DrugExposure], ids, person_ids):
    result = []
    for drug_exposure in drug_exposures:
        if drug_exposure.drug_concept_id is not None:
            result.append([ids, person_ids, drug_exposure.drug_concept_id,
            drug_exposure.drug_exposure_start_date.date(),
            drug_exposure.drug_exposure_start_datetime,
            drug_exposure.drug_exposure_end_date.date(),
            drug_exposure.drug_exposure_end_datetime,
            32809,
            drug_exposure.drug_source_value])
            ids += 1
    return result, ids


def create_procedure_occurrences(procedures: List[ProcedureOccurrence], ids, persons_ids):
    result = []
    for procedure in procedures:
        result.append([ids, persons_ids, 32809, procedure.procedure_concept_id, procedure.procedure_date,
                       procedure.procedure_source_value])
        ids += 1
    return result, ids


def insert_specimen(specimens, cursor, insert, values):
    for specimen in specimens:
        specimen = list(specimen)
        command = insert + "specimen (specimen_id, person_id, specimen_concept_id, " \
                       "specimen_type_concept_id, specimen_date, " \
                       "specimen_source_id, specimen_source_value) " + values + " (%s, %s, %s, %s, %s, %s, %s);"
        cursor.execute(command, specimen)

def insert_drug_exposure(drug_exposures, cursor, insert, values):
    for drug_exposure in drug_exposures:
        drug_exposure = list(drug_exposure)
        command = insert + "drug_exposure (drug_exposure_id, person_id, drug_concept_id, " \
                           "drug_exposure_start_date, drug_exposure_start_datetime, " \
                           "drug_exposure_end_date, drug_exposure_end_datetime, " \
                           "drug_type_concept_id, drug_source_value) " + values + " (%s, %s, %s, %s, %s, %s, %s, %s, %s);"
        cursor.execute(command, drug_exposure)


def insert_procedure_occurrence(procedure_occurrences, cursor, insert, values):
    for procedure_occurrence in procedure_occurrences:
        procedure_occurrence = list(procedure_occurrence)
        command = insert + "procedure_occurrence (procedure_occurrence_id, person_id, procedure_type_concept_id, " \
                       "procedure_concept_id, procedure_date, procedure_source_value) " \
              + values + " (%s, %s, %s, %s, %s, %s);"
        cursor.execute(command, procedure_occurrence)


def insert_data(prepared_data, cursor, conn, schema):
    try:
        insert = "INSERT INTO " + schema + "."
        values = "VALUES"
        for record in prepared_data:
            # person
            person = record[0]
            command = insert + "person (person_id, gender_concept_id, year_of_birth, race_concept_id," \
                               " ethnicity_concept_id, person_source_value, gender_source_value)" + \
                      values + " (%s, %s, %s, %s, %s, %s, %s);"
            cursor.execute(command, person)

            # observation
            observation = deque(record[1])
            observation = list(observation)
            command = insert + "observation_period (observation_period_id, person_id, " \
                               "observation_period_start_date, observation_period_end_date, " \
                               "period_type_concept_id) " + values + " (%s, %s, %s, %s, %s);"
            cursor.execute(command, observation)

            # condition
            condition_occurrence = deque(record[2])
            condition_occurrence = list(condition_occurrence)
            command = insert + "condition_occurrence (condition_occurrence_id, person_id, condition_concept_id, " \
                               "condition_start_date, condition_type_concept_id, " \
                               "condition_source_value) " + values + " (%s, %s, %s, %s, %s, %s);"
            cursor.execute(command, condition_occurrence)

            # specimen
            insert_specimen(record[3], cursor, insert, values)

            # drug exposure
            insert_drug_exposure(record[4], cursor, insert, values)

            # procedure occurrence
            insert_procedure_occurrence(record[5], cursor, insert, values)

        conn.commit()
    except Exception as e:
        print(f"Error: {e}")


def load_data(params, input_file, schema):
    try:
        # open connection
        conn = psycopg2.connect(**params)
        cursor = conn.cursor()

        # drop_tables(cursor)

        data = put_data_into_right_types(read_xml_and_parse(input_file), cursor)
        insert_data(data, cursor, conn, schema)
        # print_tables(cursor)

        # close connection
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")