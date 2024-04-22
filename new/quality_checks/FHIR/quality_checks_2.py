import os
from fhirclient import client
import pandas as pd
import fhir_quality_checks.worklof_pandas as wf1
import matplotlib.pyplot as plt
import seaborn as sns


def server_establishing():
    settings = {
        'app_id': 'my_web_app',
        'api_base': 'http://localhost:8080/fhir'
    }
    smart = client.FHIRClient(settings=settings)
    return smart


# https://www.geeksforgeeks.org/python-read-file-from-sibling-directory/
def create_ids_lists():
    # gives the path of demo.py
    path = os.path.realpath(__file__)

    # gives the directory where demo.py exists
    dir = os.path.dirname(path)

    # replaces folder name
    dir = dir.replace('fhir_quality_checks', 'fhir_conversion')

    # changes the current directory to conversion folder
    os.chdir(dir)

    patients_file = open('patients_ids.txt')
    patients_ids = []
    for id in patients_file.read().splitlines():
        patients_ids.append(id)
    patients_file.close()

    specimens_file = open('specimens_ids.txt')
    specimens_ids = []
    for id in specimens_file.read().splitlines():
        specimens_ids.append(id)
    specimens_file.close()

    conditions_file = open('conditions_ids.txt')
    conditions_ids = []
    for id in conditions_file.read().splitlines():
        conditions_ids.append(id)
    conditions_file.close()

    return patients_ids, specimens_ids, conditions_ids


def create_patient_data_frame(ids):
    dicts = []
    for id in ids:
        dict = server.request_json('http://localhost:8080/fhir/Patient/' + id)
        meta = dict.pop("meta")
        dict["meta_versionId"] = meta["versionId"]
        dict["meta_lastUpdated"] = meta["lastUpdated"]
        dicts.append(dict)
    return pd.DataFrame(dicts)


def create_specimen_data_frame(ids):
    dicts = []
    for id in ids:
        dict = server.request_json('http://localhost:8080/fhir/Specimen/' + id)

        meta = dict.pop("meta")
        dict["meta_versionId"] = meta["versionId"]
        dict["meta_lastUpdated"] = meta["lastUpdated"]

        type_ = dict.pop("type")
        dict["type_text"] = type_["text"]

        collection = dict.pop("collection")
        dict["collection_collectedDateTime"] = collection["collectedDateTime"]

        subject = dict.pop("subject")
        dict["subject_reference"] = subject["reference"]

        dicts.append(dict)
    return pd.DataFrame(dicts)


def create_condition_data_frame(ids):
    dicts = []
    for id in ids:
        dict = server.request_json('http://localhost:8080/fhir/Condition/' + id)

        meta = dict.pop("meta")
        dict["meta_versionId"] = meta["versionId"]
        dict["meta_lastUpdated"] = meta["lastUpdated"]

        code = dict.pop("code")
        coding = code.pop("coding").pop()
        dict["code_coding_system"] = coding["system"]
        dict["code_coding_code"] = coding["code"]
        dict["code_coding_display"] = coding["display"]
        dict["code_text"] = code["text"]

        subject = dict.pop("subject")
        dict["subject_reference"] = subject["reference"]

        clinicalStatus = dict.pop("clinicalStatus")
        clinicalStatus_coding = clinicalStatus.pop("coding").pop()
        dict["clinicalStatus_coding_system"] = clinicalStatus_coding.pop("system")
        dict["clinicalStatus_coding_code"] = clinicalStatus_coding.pop("code")
        dict["clinicalStatus_coding_display"] = clinicalStatus_coding.pop("display")

        dicts.append(dict)
    return pd.DataFrame(dicts)


if __name__ == '__main__':
    smart_client = server_establishing()
    server = smart_client.server

    patients_id, specimens_id, conditions_id = create_ids_lists()

    patients_df = create_patient_data_frame(patients_id)
    specimen_df = create_specimen_data_frame(specimens_id)
    condition_df = create_condition_data_frame(conditions_id)

    missing_figure_p, duplicates_p = wf1.pandas_checks_completeness_and_uniqueness(patients_df)
    missing_figure_s, duplicates_s = wf1.pandas_checks_completeness_and_uniqueness(specimen_df)
    missing_figure_c, duplicates_c = wf1.pandas_checks_completeness_and_uniqueness(condition_df)

    # wf1.pandas_checks_conformance_patient(patients_df)
    # wf1.pandas_checks_conformance_specimen(specimen_df)
    # wf1.pandas_checks_conformance_condition(condition_df)
    #
    # wf1.pandas_checks_conformance_relational(specimen_df, server)
    # wf1.pandas_checks_conformance_relational(condition_df, server)
    # wf1.pandas_checks_conformance_computational(patients_df, specimen_df, condition_df)
