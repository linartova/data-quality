from typing import List
import psycopg2
import xml.etree.ElementTree as ElementTree
from collections import deque
from datetime import datetime, timedelta
from ohdsi_classes import *
from quality_checks_ohdsi import  *


def read_xml_and_parse(file_name):
    """
    Parse input file and proccess data.

    :param file_name: The path of input file.
    :return:
        Data prepared in the list of instances of classes from ohdsi_classes.py
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
            condition_start_date = None
            if form.find(namespace + "Dataelement_51_3") is not None:
                date_diagnosis = form.find(namespace + "Dataelement_51_3").text
                condition_start_date = datetime.strptime(date_diagnosis, '%Y-%m-%d').date()
            else:
                date_diagnosis = None
            if form.find(namespace + "Dataelement_3_1") is not None:
                age_at_primary_diagnostic = form.find(namespace + "Dataelement_3_1").text
            else:
                age_at_primary_diagnostic = None
            if date_diagnosis is not None and age_at_primary_diagnostic is not None:
                year_of_birth = int(date_diagnosis[:4]) - int(age_at_primary_diagnostic)
            else:
                year_of_birth = None

            # observation period
            events = element.find(namespace + "Locations").find(namespace + "Location").find(namespace + "Events")
            observation_start_date = find_observation_start_date(namespace, events)
            if observation_start_date is None:
                observation_start_date = condition_start_date
            if form.find(namespace + "Dataelement_6_3") is not None:
                observation_end_date = form.find(namespace + "Dataelement_6_3").text
                observation_end_date = datetime.strptime(observation_end_date, '%Y-%m-%d').date()
            else:
                observation_end_date = observation_start_date

            # condition occurrence
            if find_histopathology(namespace, events) is not None:
                histopathology = find_histopathology(namespace, events).text
            else:
                histopathology = None

            # specimen
            specimens = find_specimens(namespace, events)

            # drug exposure
            if date_diagnosis is not None:
                diagnosis = datetime.strptime(date_diagnosis, "%Y-%m-%d")
                drug_exposures = find_drug_exposures(namespace, events, diagnosis)
            else:
                diagnosis = None
                drug_exposures = find_drug_exposures(namespace, events, None)

            # procedure occurrence
            procedures = find_procedures(namespace, events, diagnosis)
            procedures = procedures + find_diagnostic_procedures(namespace, form, date_diagnosis)
            # initialize classes
            result.append([Patient(patient_id, sex, year_of_birth),
                           ObservationPeriod(observation_start_date, observation_end_date),
                           ConditionOccurrence(histopathology, condition_start_date),
                           specimens,
                           drug_exposures,
                           procedures])
    return result


def find_diagnostic_procedures(namespace, form, diagnosis):
    """
    Find a values of diagnostic procedures.

    :param namespace: The namespace of file.
    :param form: XML element, where Diagnosis procedure can be stored.
    :param diagnosis: Date of diagnosis used as diagnostic procedure.
    :return:
        List of instances of class ProcedureOccurrence representing diagnostic procedures.
    """
    result = []
    # liver_imaging
    if form.find(namespace + "Dataelement_61_5") is not None:
        liver_imaging = form.find(namespace + "Dataelement_61_5").text
        if liver_imaging.find("Liver imaging - Done") != -1:
            result.append(ProcedureOccurrence(4085576, diagnosis, "liver imaging"))

    # ct
    if form.find(namespace + "Dataelement_31_3") is not None:
        ct = form.find(namespace + "Dataelement_31_3").text
        if ct.find("CT - Done") != -1:
            result.append(ProcedureOccurrence(4019823, diagnosis, "CT"))


    # colonoscopy
    if form.find(namespace + "Dataelement_88_1") is not None:
        colonoscopy = form.find(namespace + "Dataelement_88_1").text
        if colonoscopy.find("Colonoscopy diagnostic exam - Positive") != -1:
            result.append(ProcedureOccurrence(4249893, diagnosis, "colonoscopy"))


    # lung_imaging
    if form.find(namespace + "Dataelement_63_4") is not None:
        lung_imaging = form.find(namespace + "Dataelement_63_4").text
        if lung_imaging.find("Lung imaging - Done") != -1:
            result.append(ProcedureOccurrence(4082968, diagnosis, "lung imaging"))

    # mri
    if form.find(namespace + "Dataelement_30_3") is not None:
        mri = form.find(namespace + "Dataelement_30_3").text
        if mri.find("MRI - Done") != -1:
            result.append(ProcedureOccurrence(4013636, diagnosis, "MRI"))


    return result


def surgery_mapping(primary_surgery, secondary_surgery):
    """
    Map a values of surgery.

    :param primary_surgery: Surgery attribute.
    :param secondary_surgery: Another surgery attribute.
    :return:
        Values which could be stored in OMOP CDM.
    """
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
                year_of_sample_connection = sample.find(namespace + "Dataelement_89_3").text
                year_of_sample_connection = datetime.strptime(year_of_sample_connection, '%Y').date()
            else:
                year_of_sample_connection = None
            if sample.find(namespace + "Dataelement_54_2") is not None:
                sample_material_type = sample.find(namespace + "Dataelement_54_2").text
            else:
                sample_material_type = None
            if sample.find(namespace + "Dataelement_56_2") is not None:
                sample_id = sample.find(namespace + "Dataelement_56_2").text
            else:
                sample_id = None

            result.append(Specimen(sample_material_type, year_of_sample_connection, sample_id))
    return result


def find_drug_exposures(namespace, events, diagnosis):
    """
    Create a list of all Drug Exposures of one patient.

    :param namespace: The namespace of file.
    :param events: XML element, where Specimens can be stored.
    :param diagnosis: Date of diagnosis.
    :return:
        List of all Drug Exposures.
    """
    result = []
    for event in events:
        if "eventtype" in event.attrib and event.attrib.get("eventtype") == "Pharmacotherapy":
            pharmacotherapy = event.find(namespace + "LogitudinalData").find(namespace + "Form3")

            if pharmacotherapy.find(namespace + "Dataelement_59_5") is not None:
                drug_source_value = pharmacotherapy.find(namespace + "Dataelement_59_5").text
            else:
                drug_source_value = None
            if drug_source_value is None or drug_source_value == "Other":
                if pharmacotherapy.find(namespace + "Dataelement_81_3") is not None:
                    drug_source_value = pharmacotherapy.find(namespace + "Dataelement_81_3").text
                else:
                    drug_source_value = None

            drug_concept_id = drug_exposure_mapping(drug_source_value)

            if pharmacotherapy.find(namespace + "Dataelement_10_2") is not None:
                start_week = int(pharmacotherapy.find(namespace + "Dataelement_10_2").text)
            else:
                start_week = None
            if pharmacotherapy.find(namespace + "Dataelement_11_2") is not None:
                end_week = int(pharmacotherapy.find(namespace + "Dataelement_11_2").text)
            else:
                end_week = None

            drug_exposure_end_date = None
            drug_exposure_start_date = None
            if diagnosis is not None:
                if start_week is not None:
                    drug_exposure_start_date = (diagnosis + timedelta(weeks=start_week)).date()
                if end_week is not None:
                    drug_exposure_end_date = (diagnosis + timedelta(weeks=end_week)).date()

            if drug_source_value is None or len(drug_source_value) > 50:
                drug_source_value = None

            if drug_concept_id is not None:
                result.append(DrugExposure(drug_concept_id, drug_exposure_start_date,
                                       drug_exposure_end_date, drug_source_value))
    return result


def find_procedures(namespace, events, initial_diagnosis):
    """
    Create a list of all Drug Exposures of one patient.

    :param namespace: The namespace of file.
    :param events: XML element, where Specimens can be stored.
    :param initial_diagnosis: Date of initial diagnosis.
    :return:
        List of all Procedures.
    """
    result = []
    for event in events.findall(namespace + "Event"):

        if event.attrib.get("eventtype") == "Surgery":
            if event.find(namespace + "LogitudinalData").find(namespace + "Form").find(
                namespace + "Dataelement_49_1") is not None:
                primary_surgery = event.find(namespace + "LogitudinalData").find(namespace + "Form").find(
                namespace + "Dataelement_49_1").text
                secondary_surgery_node = event.find(namespace + "LogitudinalData").find(namespace + "Form").find(
                namespace + "Dataelement_67_1")
                secondary_surgery = None if secondary_surgery_node is None else secondary_surgery_node.text

                surgery_name, surgery_code = surgery_mapping(primary_surgery, secondary_surgery)
            else:
                secondary_surgery_node = event.find(namespace + "LogitudinalData").find(namespace + "Form").find(
                    namespace + "Dataelement_67_1")
                secondary_surgery = None if secondary_surgery_node is None else secondary_surgery_node.text
                surgery_name, surgery_code = surgery_mapping(None, secondary_surgery)

            start_week = event.find(namespace + "LogitudinalData").find(namespace + "Form").find(
                namespace + "Dataelement_8_3")
            if start_week is not None:
                start_week = int(start_week.text)
                date = initial_diagnosis + timedelta(weeks=start_week)
            else:
                date = None
            if surgery_code is not None:
                result.append(ProcedureOccurrence(surgery_code, date, surgery_name))

        elif event.attrib.get("eventtype") == "Radiation therapy":
            date = None
            if event.find(namespace + "LogitudinalData").find(namespace + "Form5").find(
                namespace + "Dataelement_12_4") is not None:
                start_week = event.find(namespace + "LogitudinalData").find(namespace + "Form5").find(
                namespace + "Dataelement_12_4")
                if start_week is not None:
                    start_week = int(start_week.text)
                    date = initial_diagnosis + timedelta(weeks=start_week)
            result.append(ProcedureOccurrence(4029715, date, "Radiation therapy"))

        # elif event.attrib.get("eventtype") == "Targeted Therapy":
        #     start_week = int(event.find(namespace + "LogitudinalData").find(namespace + "Form6").find(
        #         namespace + "Dataelement_35_3").text)
        #     date = initial_diagnosis + timedelta(weeks=start_week)
        #     result.append(ProcedureOccurrence(None, date, "Targeted therapy"))
    return result


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


def find_observation_start_date(namespace, events):
    """
    Find an Observation Start Date as the date of oldest sample.

    :param namespace: The namespace of file.
    :param events: XML element, where Histopathology can be stored.
    :return:
        The observation_start_date.
    """
    year_of_sample_collection = []
    for event in events.findall(namespace + "Event"):
        if "eventtype" in event.attrib:
            if event.attrib["eventtype"] == "Sample":
                if event.find(namespace + "LogitudinalData").find(namespace + "Form1").find(
                    namespace + "Dataelement_89_3") is not None:
                    year_of_sample_collection.append((event.find(namespace + "LogitudinalData").find(namespace + "Form1").find(
                    namespace + "Dataelement_89_3")).text)
    years = [datetime.strptime(year, '%Y') for year in year_of_sample_collection]
    if years:
        return min(years)
    return None


def retrieve_max_ids(cursor, schema, table):
    """
    Find max id in database.

    :param cursor: Cursor of database connection.
    :param schema: Used schema.
    :param table: In which table are we looking for an ID.
    :return:
        The max ID.
    """
    cursor.execute("SELECT MAX(" + table + "_" + "id) FROM " + schema + "." + table)
    highest_id = cursor.fetchone()[0]
    if highest_id is None:
        ids = 0
    else:
        ids = highest_id + 1
    return ids


def put_data_into_right_types(data, schema, cursor):
    """
    Modify data to be prepared in the INSERT command.

    :param data: Data prepared in the list of instances of classes from ohdsi_classes.py
    :param schema: Used schema.
    :param cursor: Cursor of database connection.
    :return:
        The data.
    """
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
    """
    Helper function for put_data_into_right_types function.

    :param person: Person data.
    :param ids: ID in database.
    :return:
        Person data prepared for INSERT command.
    """
    if person.gender_concept_id == "male":
        gender = 8507
    elif person.gender_concept_id == "female":
        gender = 8532
    else:
        gender = 8521
    source_value = person.person_source_value
    return [ids, gender, person.year_of_birth, 0, 0, source_value, person.gender_concept_id]


def create_observation_period_data(observation: ObservationPeriod, ids, person_ids):
    """
    Helper function for put_data_into_right_types function.

    :param observation: Observation Period data.
    :param ids: ID in database.
    :return:
        Observation Period data prepared for INSERT command.
    """
    return [ids, person_ids, observation.start_date,
            observation.end_date, 32809]


def condition_mapping_codes(condition):
    """
    Map a values of condition codes.

    :param condition: Condition values.
    :return:
        Values which could be stored in OMOP CDM.
    """
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
    """
    Map a values of condition names.

    :param condition: Condition values.
    :return:
        Values which could be stored in OMOP CDM.
    """
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
    """
    Helper function for put_data_into_right_types function.

    :param condition: Condition Occurrence data.
    :param ids: ID in database.
    :return:
        Condition Occurrence data prepared for INSERT command.
    """
    return [ids, person_ids, condition_mapping_codes(condition.condition_concept_id),
            condition.condition_start_date, 32809,
            condition_mapping_names(condition.condition_source_value)]


def specimen_mapping_numbers(specimen):
    """
    Map a values of specimen numbers.

    :param specimen: Specimen values.
    :return:
        Values which could be stored in OMOP CDM.
    """
    if specimen == "Healthy colon tissue":
        return 4134449
    elif specimen == "Tumor":
        return 4122248
    else:
        return 4163599


def specimen_mapping_names(specimen):
    """
    Map a values of specimen names.

    :param specimen: Specimen values.
    :return:
        Values which could be stored in OMOP CDM.
    """
    if specimen == "Healthy colon tissue":
        return "Healthy colon tissue"
    elif specimen == "Tumor":
        return "Tumor tissue"
    else:
        return "Other"


def create_specimens(specimens: List[Specimen], ids, person_ids):
    """
    Helper function for put_data_into_right_types function.

    :param specimens: Specimen data.
    :param ids: ID in database.
    :param person_ids: Foreign key of Person.
    :return:
        Specimen data prepared for INSERT command.
    """
    result = []
    for specimen in specimens:
        result.append([ids, person_ids, specimen_mapping_numbers(specimen.specimen_concept_id), 32809,
            specimen.specimen_date,
            specimen.specimen_source_id, specimen_mapping_names(specimen.specimen_source_value)])
        ids += 1
    return result, ids


def drug_exposure_mapping(drug_concept_id):
    """
    Map a values of drug exposure

    :param drug_concept_id: drug concept id
    :return:
        Values which could be stored in OMOP CDM.
    """
    drug_mapping = {"5-FU": 40042274,
                    "Capecitabine": 40095743,
                    "Oxaliplatin": 35603923,
                    "UFT": 40052183,
                    "Other": 0}
    if drug_concept_id is None:
        return 0
    for drug in drug_mapping.keys():
        if drug_concept_id.find(drug) != -1:
            return drug_mapping.get(drug)
    return 0


def create_drug_exposures(drug_exposures: List[DrugExposure], ids, person_ids):
    """
    Helper function for put_data_into_right_types function.

    :param drug_exposures: Drug Exposure data.
    :param ids: ID in database.
    :param person_ids: Foreign key of Person.
    :return:
        Drug exposure data prepared for INSERT command.
    """
    result = []
    for drug_exposure in drug_exposures:
        if drug_exposure.drug_concept_id is not None:
            result.append([ids, person_ids, drug_exposure.drug_concept_id,
            drug_exposure.drug_exposure_start_date,
            drug_exposure.drug_exposure_start_datetime,
            drug_exposure.drug_exposure_end_date,
            drug_exposure.drug_exposure_end_datetime,
            32809,
            drug_exposure.drug_source_value])
            ids += 1
    return result, ids


def create_procedure_occurrences(procedures: List[ProcedureOccurrence], ids, persons_ids):
    """
    Helper function for put_data_into_right_types function.

    :param procedures: Procedure Occurrence data.
    :param ids: ID in database.
    :param persons_ids: Foreign key of Person.
    :return:
        Procedure occurrence data prepared for INSERT command.
    """
    result = []
    for procedure in procedures:
        result.append([ids, persons_ids, 32809, procedure.procedure_concept_id, procedure.procedure_date,
                       procedure.procedure_source_value])
        ids += 1
    return result, ids


def insert_specimen(specimens, cursor, insert, values):
    """
    Helper function for insert_data.

    :param specimens: The data in form ready for insert into OMOP CDM.
    :param cursor: Cursor of database connection.
    :param insert: Part of insert command.
    :param values: Part of insert command.
    :return:
        None.
    """
    for specimen in specimens:
        specimen = list(specimen)
        command = insert + "specimen (specimen_id, person_id, specimen_concept_id, " \
                       "specimen_type_concept_id, specimen_date, " \
                       "specimen_source_id, specimen_source_value) " + values + " (%s, %s, %s, %s, %s, %s, %s);"
        cursor.execute(command, specimen)

def insert_drug_exposure(drug_exposures, cursor, insert, values):
    """
    Helper function for insert_data.

    :param drug_exposures: The data in form ready for insert into OMOP CDM.
    :param cursor: Cursor of database connection.
    :param insert: Part of insert command.
    :param values: Part of insert command.
    :return:
        None.
    """
    for drug_exposure in drug_exposures:
        drug_exposure = list(drug_exposure)
        command = insert + "drug_exposure (drug_exposure_id, person_id, drug_concept_id, " \
                           "drug_exposure_start_date, drug_exposure_start_datetime, " \
                           "drug_exposure_end_date, drug_exposure_end_datetime, " \
                           "drug_type_concept_id, drug_source_value) " + values + " (%s, %s, %s, %s, %s, %s, %s, %s, %s);"
        cursor.execute(command, drug_exposure)


def insert_procedure_occurrence(procedure_occurrences, cursor, insert, values):
    """
    Helper function for insert_data.

    :param procedure_occurrences: The data in form ready for insert into OMOP CDM.
    :param cursor: Cursor of database connection.
    :param insert: Part of insert command.
    :param values: Part of insert command.
    :return:
        None
    """
    for procedure_occurrence in procedure_occurrences:
        procedure_occurrence = list(procedure_occurrence)
        command = insert + "procedure_occurrence (procedure_occurrence_id, person_id, procedure_type_concept_id, " \
                       "procedure_concept_id, procedure_date, procedure_source_value) " \
              + values + " (%s, %s, %s, %s, %s, %s);"
        cursor.execute(command, procedure_occurrence)


def insert_data(prepared_data, cursor, conn, schema):
    """
    Insert data into database.

    :param prepared_data: The data in form ready for insert into OMOP CDM.
    :param cursor: Cursor of database connection.
    :param conn: Database connection.
    :param schema: Used schema.
    :return:
        None
    """
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
    """
    Load data from input_file into database with attached params.

    :param params: Params of database.
    :param input_file: The path of input file.
    :param schema: The schema we are working with.
    :return:
        None
    """
    try:
        # open connection
        conn = psycopg2.connect(**params)
        cursor = conn.cursor()

        data = put_data_into_right_types(read_xml_and_parse(input_file), schema, cursor)
        insert_data(data, cursor, conn, schema)

        # close connection
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

def create_graphs_omop(ohdsi, input_file):
    """
    Run OMOP loading data and quality checks.

    Args:
        ohdsi: Connection information for OMOP database.
        input_file: Name of file with input data.

    Returns:
        List of generated graphs in json format.
    """
    schema = ohdsi.pop("schema")
    load_data(ohdsi, input_file, schema)

    # dashboard viz
    con = psycopg2.connect(**ohdsi)
    graphs = []

    pdf = create_df_omop(con, "person", schema)
    odf = create_df_omop(con, "observation_period", schema)
    cdf = create_df_omop(con, "condition_occurrence", schema)
    sdf = create_df_omop(con, "specimen", schema)
    ddf = create_df_omop(con, "drug_exposure", schema)
    prdf = create_df_omop(con, "procedure_occurrence", schema)

    graphs.append(completeness(pdf).to_json())
    graphs.append(completeness(odf).to_json())
    graphs.append(completeness(cdf).to_json())
    graphs.append(completeness(sdf).to_json())
    graphs.append(completeness(ddf).to_json())
    graphs.append(completeness(prdf).to_json())

    graphs.append(uniqueness(pdf).to_json())
    graphs.append(uniqueness(pdf).to_json())
    graphs.append(uniqueness(pdf).to_json())
    graphs.append(uniqueness(pdf).to_json())
    graphs.append(uniqueness(pdf).to_json())
    graphs.append(uniqueness(pdf).to_json())

    # warnings
    graphs.append(observation_end_precedes_condition_start(cdf, odf).to_json())
    graphs.append(observation_end_equals_condition_start(cdf, odf).to_json())
    graphs.append(too_young_person(pdf, cdf).to_json())
    graphs.append(observation_end_in_the_future(odf).to_json())
    graphs.append(condition_start_in_the_future(cdf).to_json())
    graphs.append(missing_drug_exposure_info(ddf).to_json())
    graphs.append(sus_pharma(ddf).to_json())
    graphs.append(sus_pharma_other(ddf).to_json())
    graphs.append(drug_end_before_start(ddf).to_json())

    fig_1, fig_2 = therapy_start_before_diagnosis(cdf, ddf, prdf)
    fig_3, fig_4 = treatment_start_in_the_future(ddf, prdf)

    graphs.append(fig_1.to_json())
    graphs.append(fig_2.to_json())
    graphs.append(fig_3.to_json())
    graphs.append(fig_4.to_json())

    graphs.append(drug_exposure_end_in_the_future(ddf).to_json())
    graphs.append(sus_early_pharma(cdf, ddf).to_json())
    graphs.append(sus_short_pharma(cdf, ddf).to_json())

    # reports
    graphs.append(missing_specimen_date(pdf, sdf).to_json())
    graphs.append(patients_without_specimen_source_id(pdf, sdf).to_json())
    graphs.append(patients_without_specimen_source_value_concept_id(pdf, sdf).to_json())
    graphs.append(patients_without_condition_values(pdf, cdf).to_json())
    graphs.append(patients_without_surgery_values(pdf, prdf).to_json())
    graphs.append(missing_patient_and_diagnostic_values(pdf, prdf).to_json())
    graphs.append(missing_targeted_therapy_values(pdf, prdf).to_json())
    graphs.append(missing_pharmacotherapy_value(pdf, ddf).to_json())
    graphs.append(missing_radiation_therapy_values(pdf, prdf).to_json())
    graphs.append(counts_of_records(pdf, odf, cdf, sdf, ddf, prdf).to_json())
    graphs.append(get_patients_without_surgery(pdf, prdf).to_json())

    return graphs