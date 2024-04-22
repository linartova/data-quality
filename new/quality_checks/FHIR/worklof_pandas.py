import pandas as pd
import missingno as msno
import matplotlib.pyplot as plt
import plotly.express as px
import seaborn as sns


def pandas_checks_completeness_and_uniqueness(data_frame):
    missing_figure = msno.matrix(data_frame)

    unique = data_frame.duplicated()
    print(unique)
    unique_id = data_frame["id"].duplicated()
    print(unique_id)

    duplicated_counts = unique.value_counts()
    # Plotting
    duplicates = plt.bar(['Non-Duplicated', 'Duplicated'], duplicated_counts, color=['blue', 'red'], title="Duplicated Data Counts", ylabel="Count")
    # duplicates.write_html("duplicates")

    # Plotting with seaborn
    # sns.countplot(x=data_frame.duplicated(), palette=['blue', 'red'])
    # plt.title('Duplicated Data Counts')
    # plt.xlabel('Duplicated')
    # plt.ylabel('Count')
    # plt.show()

    return missing_figure, duplicates


def pandas_checks_conformance_patient(patient_data_frame):
    # TODO kontrolovat meta data?
    # gender
    gender_check = patient_data_frame["gender"].isin(["male", "female", "other", "unknown"])
    print(gender_check)

    # birth date
    patient_data_frame["birthDate"] = pd.to_datetime(patient_data_frame["birthDate"], errors="coerce")
    birth_date_check = patient_data_frame.isnull()["birthDate"]
    print(birth_date_check)


def pandas_checks_conformance_condition(condition_data_frame):
    # recordedDate
    condition_data_frame["recordedDate"] = pd.to_datetime(condition_data_frame["recordedDate"],
                                                          errors="coerce")
    recorded_date_check = condition_data_frame.isnull()["recordedDate"]
    print(recorded_date_check)

    # onsetDateTime
    condition_data_frame["onsetDateTime"] = pd.to_datetime(condition_data_frame["onsetDateTime"],
                                                           errors="coerce")
    onset_date_time_check = condition_data_frame.isnull()["onsetDateTime"]
    print(onset_date_time_check)

    # clinical Status
    clinical_status_coding_code_check = condition_data_frame[
        "clinicalStatus_coding_code"].isin(
        ["active", "recurrence", "relapse", "inactive",
         "remission", "resolved", "unknown"])
    print(clinical_status_coding_code_check)
    clinical_status_coding_display_check = condition_data_frame[
        "clinicalStatus_coding_display"].isin(
        ["active", "recurrence", "relapse", "inactive",
         "remission", "resolved", "unknown"])
    print(clinical_status_coding_display_check)

    # coding system
    code_coding_code_check = condition_data_frame["code_coding_code"].isin(["C18.0",
               "C18.1", "C18.2", "C18.3", "C18.4", "C18.5", "C18.6",
               "C18.7", "C18.8", "C18.9", "C19", "C20"])
    print(code_coding_code_check)
    code_coding_display_check = condition_data_frame["code_coding_display"].isin([
        "Malignant neoplasm of cecum",
        "Malignant neoplasm of appendix",
        "Malignant neoplasm of ascending colon",
        "Malignant neoplasm of hepatic flexure",
        "Malignant neoplasm of transverse colon",
        "Malignant neoplasm of splenic flexure",
        "Malignant neoplasm of descending colon",
        "Malignant neoplasm of sigmoid colon",
        "Malignant neoplasm of overlapping sites of colon",
        "Malignant neoplasm of colon, unspecified",
        "Malignant neoplasm of rectosigmoid junction",
        "Malignant neoplasm of rectum"])
    print(code_coding_display_check)
    code_text_check = condition_data_frame["code_text"].isin([
        "C18.0 Malignant neoplasm of cecum",
        "C18.1 Malignant neoplasm of appendix",
        "C18.2 Malignant neoplasm of ascending colon",
        "C18.3 Malignant neoplasm of hepatic flexure",
        "C18.4 Malignant neoplasm of transverse colon",
        "C18.5 Malignant neoplasm of splenic flexure",
        "C18.6 Malignant neoplasm of descending colon",
        "C18.7 Malignant neoplasm of sigmoid colon",
        "C18.8 Malignant neoplasm of overlapping sites of colon",
        "C18.9 Malignant neoplasm of colon, unspecified",
        "C19 Malignant neoplasm of rectosigmoid junction",
        "C20 Malignant neoplasm of rectum"
    ])
    print(code_text_check)


def pandas_checks_conformance_specimen(specimen_data_frame):
    # type text
    type_text_check = specimen_data_frame["type_text"].isin(["Tumor", "Other", "Healthy colon tissue"])
    print(type_text_check)

    # collected Date Time
    specimen_data_frame["collection_collectedDateTime"] = \
        pd.to_datetime(specimen_data_frame["collection_collectedDateTime"], errors="coerce")
    collection_collectedDateTime_check = specimen_data_frame.isnull()["collection_collectedDateTime"]
    print(collection_collectedDateTime_check)


def pandas_checks_conformance_relational(data_frame, server):
    print("well")
    for index in data_frame.index:
        link = data_frame['id'][index]
        subject_reference = data_frame['subject_reference'][index]
        resource_type = data_frame["resourceType"][index]
        try:
            server.request_json('http://localhost:8080/fhir/' + subject_reference)
        except:
            print("Invalid subject reference in " + resource_type + "/" + link)
    print("Other problems in subject reference not found.")


def pandas_checks_conformance_computational(patient_data_frame,
                                            specimen_data_frame, condition_data_frame):
    # prostě zobrat od jednoho pacoša všechny datumy a udělat kontrolní výpočty
    pass
    # birthDate patient
    # collection_collectedDateTime specimen
    # onsetDateTime condition
    # recordedDate condition

    # birthDate < onsetDateTime, recordedDate, collection_collectedDateTime

    # Plausibility: temporal, atemporal - checks like too old patients, etc.
    # I can also train some basic AI models to find bs for tempotal
    # atemporal are like the research inspo like - people under 45 usualy dont have colon cancer
    # ty co mi poslala Zdenka plus něco z paperů, 5-10 checků
    # TODO vizualizace


def pandas_checks_plausability():
    pass

    # what checks make sense and where is DQ guaranteed by conversion?
    # think about checks and at the same time, think about simple visualisation
    # kouknout na breast cancer projekt
    # a cizí kaggle projekty


def checks_test_set():
    pass
