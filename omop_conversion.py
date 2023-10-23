import pymysql
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
    def __init__(self, drug_concept_id, drug_exposure_start_date, drug_exposure_end_date):
        self.drug_concept_id = drug_concept_id
        self.drug_exposure_start_date = drug_exposure_start_date
        self.drug_exposure_end_date = drug_exposure_end_date


db_params = {
    'host': 'localhost',
    'port': 3306,
    'user': 'martinamartina',
    'password': 'smrdiminohy',
}

cdm_schema = ["""
CREATE TABLE IF NOT EXISTS person (
    id INT AUTO_INCREMENT PRIMARY KEY,
    gender_concept_id INT,
    year_of_birth INT,
    race_concept_id INT,
    ethnicity_concept_id INT,
    person_source_value VARCHAR(50),
    gender_source_value VARCHAR(50)
);""", """
CREATE TABLE IF NOT EXISTS observation_period (
    observation_id INT AUTO_INCREMENT PRIMARY KEY,
    person_id INT,
    observation_period_start_date DATE,
    observation_period_end_date DATE,
    period_type_concept_id INT,
    FOREIGN KEY (person_id) REFERENCES person(id)
); """, """
CREATE TABLE IF NOT EXISTS condition_occurrence (
    condition_occurrence_id INT AUTO_INCREMENT PRIMARY KEY,
    person_id INT,
    condition_concept_id INT,
    condition_start_date DATE,
    condition_type_concept_id INT,
    condition_source_value VARCHAR(50),
    FOREIGN KEY (person_id) REFERENCES person(id)
);""", """

CREATE TABLE IF NOT EXISTS specimen (
    specimen_id INT AUTO_INCREMENT PRIMARY KEY,
    person_id INT,
    specimen_concept_id INT,
    specimen_type_concept_id INT,
    specimen_date YEAR,
    specimen_source_id VARCHAR(50),
    specimen_source_value VARCHAR(50),
    FOREIGN KEY (person_id) REFERENCES person(id)
);""", """
CREATE TABLE IF NOT EXISTS drug_exposure (
    drug_exposure_id INT,
    person_id INT,
    drug_concept_id INT,
    drug_exposure_start_date DATE,
    drug_exposure_end_date DATE,
    drug_type_concept_id INT,
    FOREIGN KEY (person_id) REFERENCES person(id)
);
"""]


def create_database_and_tables(schema, cursor):
    try:
        cursor.execute("CREATE DATABASE IF NOT EXISTS omop_cdm_database")
        for table in schema:
            cursor.execute(table)
    except Exception as e:
        print(f"Error: {e}")


def read_xml_and_parse():
    tree = ElementTree.parse('import_example 1.xml')
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
            observation_start_date = find_observation_start_date(namespace, events).text
            observation_end_date = form.find(namespace + "Dataelement_6_3").text

            # condition occurrence
            histopathology = find_histopathology(namespace, events).text

            # specimen
            year_of_sample_connection = find_sample(namespace, events).find(namespace + "Dataelement_89_3").text
            sample_material_type = find_sample(namespace, events).find(namespace + "Dataelement_54_2").text
            sample_id = find_sample(namespace, events).find(namespace + "Dataelement_56_2").text

            # drug exposure
            pharmacotherapy = find_pharmacotherapy(namespace, events)
            drug_concept_id = pharmacotherapy.find(namespace + "Dataelement_59_5").text

            start_week = int(pharmacotherapy.find(namespace + "Dataelement_10_2").text)
            end_week = int(pharmacotherapy.find(namespace + "Dataelement_11_2").text)
            diagnosis = datetime.strptime(date_diagnosis, "%Y-%m-%d")

            drug_exposure_start_date = diagnosis + timedelta(weeks=start_week)
            drug_exposure_end_date = diagnosis + timedelta(weeks=end_week)

            # initialize classes
            result.append([Patient(patient_id, sex, year_of_birth),
                           ObservationPeriod(observation_start_date, observation_end_date),
                           ConditionOccurrence(histopathology, date_diagnosis),
                           Specimen(sample_material_type, year_of_sample_connection, sample_id),
                           DrugExposure(drug_concept_id, drug_exposure_start_date, drug_exposure_end_date)])
    return result


def find_histopathology(namespace, events):
    for event in events.findall(namespace + "Event"):
        if event.attrib.get("eventtype") == "Histopathology":
            return event.find(namespace + "LogitudinalData").find(namespace + "Form2").find(
                namespace + "Dataelement_92_1")


def find_sample(namespace, events):
    for event in events.findall(namespace + "Event"):
        if "eventtype" in event.attrib and event.attrib.get("eventtype") == "Sample":
            return event.find(namespace + "LogitudinalData").find(namespace + "Form1")


def find_observation_start_date(namespace, events):
    for event in events:
        if "eventtype" in event.attrib:
            if event.attrib["eventtype"] == "Sample":
                return event.find(namespace + "LogitudinalData").find(namespace + "Form1").find(
                    namespace + "Dataelement_89_3")


def find_pharmacotherapy(namespace, events):
    for event in events:
        if "eventtype" in event.attrib and event.attrib.get("eventtype") == "Pharmacotherapy":
            return event.find(namespace + "LogitudinalData").find(namespace + "Form3")


def put_data_into_right_types(data):
    result = []
    for record in data:
        person = create_person_data(record[0])
        observation_period = create_observation_period_data(record[1])
        condition_occurrence = create_condition_occurrences_data(record[2])
        specimen = create_specimen_data(record[3])
        drug_exposure = create_drug_exposure_data(record[4])
        result.append((person, observation_period, condition_occurrence, specimen, drug_exposure))
    return result


def create_person_data(person: Patient):
    if person.gender_concept_id == "male":
        gender = 8507
    elif person.gender_concept_id == "female":
        gender = 8532
    else:
        gender = 8521
    source_value = person.person_source_value
    return [gender, person.year_of_birth, 0, None, source_value, person.gender_concept_id]


def create_observation_period_data(observation: ObservationPeriod):
    return [datetime(int(observation.start_date), 1, 1).date(), observation.end_date, 32809]


def condition_mapping_codes(condition):
    codes_mapping = {"C 18.0": 432837,
                     "C 18.1": 433143,
                     "C 18.2": 4247719,
                     "C 18.3": 438979,
                     "C 18.4": 432257,
                     "C 18.5": 437798,
                     "C 18.6": 441800,
                     "C 18.7": 436635,
                     "C 19": 438699,
                     "C 20": 74582}
    for code in codes_mapping.keys():
        if condition.find(code) != -1:
            return codes_mapping.get(code)
    return None


def condition_mapping_names(condition):
    codes_mapping = {"C 18.0": "C 18.0 - Caecum",
                     "C 18.1": "C 18.1 - Appendix",
                     "C 18.2": "C 18.2 - Ascending colon",
                     "C 18.3": "C 18.3 - Hepatic flexure",
                     "C 18.4": "C 18.4 - Transverse colon",
                     "C 18.5": "C 18.5 - Splenic flexure",
                     "C 18.6": "C 18.6 - Descending colon",
                     "C 18.7": "C 18.7 - Sigmoid colon",
                     "C 19": "C 19 - Rectosigmoid junction ",
                     "C 20": "C 20 - Rectum"}
    for code in codes_mapping.keys():
        if condition.find(code) != -1:
            return codes_mapping.get(code)
    return None


def create_condition_occurrences_data(condition: ConditionOccurrence):
    return [condition_mapping_codes(condition.condition_concept_id),
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


def create_specimen_data(specimen: Specimen):
    return [specimen_mapping_numbers(specimen.specimen_concept_id), 32809, specimen.specimen_date,
            specimen.specimen_source_id, specimen_mapping_names(specimen.specimen_source_value)]


def drug_exposure_mapping(drug_exposure):
    drug_mapping = {"5-FU 1000 mg/m2 i.v. continuous infusion, day 1-5, weeks1 and 5": 40042274,
                    "5-FU 225 mg/m2 i.v. continuous infusion, 5 days per week": 40042274,
                    "5-FU 325-350 mg/m2 + LV 20 mg/m2 i.v. bolus, day1-5, weeks 1 and 5": 40220867,
                    # TODO není tu typo? má být před week 1 mezera?
                    "5-FU 400 mg/m2 + 100 mg i.v. bolus, d 1,2, 11,12,21,22": 40042274,
                    "Capecitabine 800-825 mg/m2 bid po, day 1-5, together with radiation or continuously untill end "
                    "of radiation": 40095743,
                    "Only preoperatively (no standard): 5-FU 250 mg/m2 i.v. continuous infusion on days 1- 13 nad "
                    "22-35 and oxaliplatin 50mg/m2 i.v. day 1,8,22 and 29": 40042274,
                    "UFT (300-340mg/m2/day) and LV (22.5-90 mg/day) po continuously, 5(-7) days per week, together "
                    "with radiotherapy": 40052183,
                    "Other": 0}
    for drug in drug_mapping.keys():
        if drug_exposure == drug:
            return drug_mapping.get(drug)
    return -1


def create_drug_exposure_data(drug_exposure: DrugExposure):
    return [drug_exposure_mapping(drug_exposure.drug_concept_id),
            drug_exposure.drug_exposure_start_date.date(),
            drug_exposure.drug_exposure_end_date.date(), 32809]


def insert_data(prepared_data, cursor, conn):
    try:
        insert = "INSERT INTO"
        values = "VALUES"
        for record in prepared_data:
            person = record[0]
            command = insert + " person (gender_concept_id, year_of_birth, race_concept_id," \
                               " ethnicity_concept_id, person_source_value, gender_source_value) " + \
                      values + " (%s, %s, %s, %s, %s, %s);"
            cursor.execute(command, person)
            person_id = cursor.lastrowid

            observation = deque(record[1])
            observation.appendleft(person_id)
            observation = list(observation)
            command = insert + " observation_period (person_id, " \
                           "observation_period_start_date, observation_period_end_date, " \
                           "period_type_concept_id) " + values + " (%s, %s, %s, %s);"
            cursor.execute(command, observation)

            condition_occurrence = deque(record[2])
            condition_occurrence.appendleft(person_id)
            condition_occurrence = list(condition_occurrence)
            command = insert + " condition_occurrence (person_id, condition_concept_id, " \
                           "condition_start_date, condition_type_concept_id, " \
                           "condition_source_value) " + values + " (%s, %s, %s, %s, %s);"
            cursor.execute(command, condition_occurrence)

            specimen = deque(record[3])
            specimen.appendleft(person_id)
            specimen = list(specimen)
            command = insert + " specimen (person_id, specimen_concept_id, " \
                           "specimen_type_concept_id, specimen_date, " \
                           "specimen_source_id, specimen_source_value) " + values + " (%s, %s, %s, %s, %s, %s);"
            cursor.execute(command, specimen)

            drug_exposure = deque(record[4])
            drug_exposure.appendleft(person_id)
            drug_exposure = list(drug_exposure)
            command = insert + " drug_exposure (person_id, drug_concept_id, " \
                           "drug_exposure_start_date, drug_exposure_end_date, " \
                           "drug_type_concept_id) " + values + " (%s, %s, %s, %s, %s);"
            cursor.execute(command, drug_exposure)
        conn.commit()
    except Exception as e:
        print(f"Error: {e}")


def print_tables(cursor):
    try:
        tables = ['condition_occurrence', 'drug_exposure', 'observation_period', 'person', 'specimen']
        for table in tables:
            cursor.execute("SELECT * FROM " + table)
            rows = cursor.fetchall()
            for row in rows:
                print(row)
    except Exception as e:
        print(f"Error: {e}")


def drop_tables(cursor):
    try:
        cursor.execute("DROP TABLE IF EXISTS observation_period")
        cursor.execute("DROP TABLE IF EXISTS condition_occurrence")
        cursor.execute("DROP TABLE IF EXISTS specimen")
        cursor.execute("DROP TABLE IF EXISTS drug_exposure")
        cursor.execute("DROP TABLE IF EXISTS person")
    except Exception as e:
        print(f"Error: {e}")


def provide_connection(params):
    try:
        # open connection
        conn = pymysql.connect(**params)
        cursor = conn.cursor()
        cursor.execute("USE omop_cdm_database")

        # work around
        drop_tables(cursor)
        create_database_and_tables(cdm_schema, cursor)
        data = put_data_into_right_types(read_xml_and_parse())
        insert_data(data, cursor, conn)
        print_tables(cursor)

        # close connection
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")


if __name__ == '__main__':
    provide_connection(db_params)

    # TODO refactor and rename code
    # TODO třeba si to znovu projít, postupně protestovat a zkontrolovat mapping pdfka
    # TODO zamyslet se nad kvalitou a návrhem kódu

    # TODO v jakém typu se insertuje DATE a YEAR - můžou být oba stringy?
