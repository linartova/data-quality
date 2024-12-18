import pandas as pd
import plotly.express as px
from _datetime import datetime


def create_patient_data_frame(server):
    """
    Create data frame from Resource Patient.

    :param server: FHIR server.
    :return:
        Patient data frame.
    """
    dicts = []
    with open('patients_ids.txt', 'r') as ids:
        for id in ids:
            id = id[:-1]
            dict = server.request_json('http://localhost:8080/fhir/Patient/' + id)
            meta = dict.get("meta")
            if meta is not None:
                dict.pop("meta")
                dict["meta_versionId"] = meta.get("versionId")
                dict["meta_lastUpdated"] = meta.get("lastUpdated")
            else:
                dict["meta_versionId"] = None
                dict["meta_lastUpdated"] = None

            identifier = dict.get("identifier")
            if identifier is not None:
                dict.pop("identifier")
                identifier = identifier[0]
            else:
                identifier = None
            dict["identifier_value"] = identifier.get("value")
            dicts.append(dict)

    return pd.DataFrame(dicts)


def create_specimen_data_frame(server):
    """
    Create data frame from Resource Specimen.

    :param server: FHIR server.
    :return:
        Specimen data frame.
    """
    dicts = []
    with open('specimens_ids.txt', 'r') as ids:
        for id in ids:
            id = id[:-1]
            dict = server.request_json('http://localhost:8080/fhir/Specimen/' + id)

            meta = dict.get("meta")
            if meta is not None:
                dict.pop("meta")
                dict["meta_versionId"] = meta.get("versionId")
                dict["meta_lastUpdated"] = meta.get("lastUpdated")
            else:
                dict["meta_versionId"] = None
                dict["meta_lastUpdated"] = None

            # type
            type = dict.get("type")
            if type is not None:
                dict.pop("type")
                type_coding = type.get("coding")
                if type_coding is not None:
                    type_coding = type_coding.pop()

                if type_coding is not None:
                    type_display = type_coding.get("display")
                    dict["type_text"] = type_display
                    type_code = type_coding.get("code")
                    dict["type_text_code"] = type_code

                collection = dict.get("collection")
                if collection is not None:
                    dict["collection_collectedDateTime"] = collection.get("collectedDateTime")
                else:
                    dict["collection_collectedDateTime"] = None
            else:
                dict["type_text"] = None
                dict["collection_collectedDateTime"] = None

            subject = dict.get("subject")
            if subject is not None:
                dict.pop("subject")
                dict["subject_reference"] = subject.get("reference")

            dicts.append(dict)
    return pd.DataFrame(dicts)


def create_condition_data_frame(server):
    """
    Create data frame from Resource Condition.

    :param server: FHIR server.
    :return:
        Condition data frame.
    """
    dicts = []
    with open('conditions_ids.txt', 'r') as ids:
        for id in ids:
            id = id[:-1]
            dict = server.request_json('http://localhost:8080/fhir/Condition/' + id)

            meta = dict.get("meta")
            if meta is not None:
                dict.pop("meta")
                dict["meta_versionId"] = meta.get("versionId")
                dict["meta_lastUpdated"] = meta.get("lastUpdated")
            else:
                dict["meta_versionId"] = None
                dict["meta_lastUpdated"] = None

            dict["code_coding_system"] = None
            dict["code_coding_code"] = None
            dict["code_coding_display"] = None
            dict["code_text"] = None
            code = dict.get("code")
            if code is not None:
                dict.pop("code")
                coding = code.get("coding")
                if coding is not None:
                    coding = coding.pop()
                    dict["code_coding_system"] = coding.get("system")
                    dict["code_coding_code"] = coding.get("code")
                    dict["code_coding_display"] = coding.get("display")
                    dict["code_text"] = code.get("text")

            subject = dict.get("subject")
            if subject is not None:
                dict.pop("subject")
                dict["subject_reference"] = subject.get("reference")
            else:
                dict["subject_reference"] = None

            clinicalStatus = dict.get("clinicalStatus")
            if clinicalStatus is not None:
                dict.pop("clinicalStatus")
                clinicalStatus_coding = clinicalStatus.get("coding")
                if clinicalStatus_coding is not None:
                    clinicalStatus_coding = clinicalStatus_coding[0]
                    dict["clinicalStatus_coding_system"] = clinicalStatus_coding.get("system")
                    dict["clinicalStatus_coding_code"] = clinicalStatus_coding.get("code")
                    dict["clinicalStatus_coding_display"] = clinicalStatus_coding.get("display")
                else:
                    dict["clinicalStatus_coding_system"] = None
                    dict["clinicalStatus_coding_code"] = None
                    dict["clinicalStatus_coding_display"] = None
            dicts.append(dict)
    return pd.DataFrame(dicts)


def completeness(df):
    """
    Data quality check for completeness.

    :param df: Input data frame
    :return:
        Graph of completeness.
    """
    missing_values = pd.isnull(df).sum()
    fig = px.scatter(missing_values)
    fig.update_layout(xaxis_title='count of missing values', yaxis_title='attribute', title="Missing values",
                      showlegend=False)
    return fig


def uniqueness(df, name):
    """
    Data quality check for uniqueness.

    :param df: Input data frame
    :param name: Name of processed data frame.
    :return:
        Graph of uniqueness.
    """
    df = df.copy()
    count_of_rows = df.shape[0]
    df.drop(columns="meta_versionId", inplace=True)
    df.drop(columns="meta_lastUpdated", inplace=True)
    df.drop(columns="id", inplace=True)

    count_of_duplicates = df.duplicated().sum()
    result = {
        "Duplicates": ["Unique rows", "Duplicated"],
        "Count": [count_of_rows - count_of_duplicates, count_of_duplicates]
    }
    dff = pd.DataFrame(result)
    fig = px.pie(dff, values='Count', names='Duplicates', title=('Duplicated values' + name))

    df.to_csv("reports/fhir/uniqueness" + name + ".csv", index=False)
    return fig


def conformance_patient(df):
    """
    Data quality check for conformance of Resource Patient.

    :param df: Patient data frame.
    :return:
        Graph of conformance.
    """
    # gender
    count_of_rows = df.shape[0]
    gender_check_count = df["gender"].isin(["male", "female", "other", "unknown"]).sum()

    # birthDate
    df["birthDate"] = pd.to_datetime(df["birthDate"], errors="coerce")
    birth_date_check = df.isnull()["birthDate"].sum()

    result = {
        "Records": ["Number of records", "Invalid gender", "Invalid birth date"],
        "Count": [count_of_rows, count_of_rows - gender_check_count, birth_date_check]
    }

    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    fig.update_layout(title="Conformance patient")
    return fig


def conformance_condition(df):
    """
    Data quality check for conformance of Resource Conformance.

    :param df: Conformance data frame.
    :return:
        Graph of conformance.
    """
    count_of_rows = df.shape[0]

    # recordedDate
    df["recordedDate"] = pd.to_datetime(df["recordedDate"],
                                        errors="coerce")
    recorded_date_check = df.isnull()["recordedDate"].sum()

    # onsetDateTime
    df["onsetDateTime"] = pd.to_datetime(df["onsetDateTime"],
                                         errors="coerce")
    onset_date_time_check = df.isnull()["onsetDateTime"].sum()

    # clinical Status
    clinical_status_coding_code_check = df[
        "clinicalStatus_coding_code"].isin(
        ["active", "recurrence", "relapse", "inactive",
         "remission", "resolved", "unknown"]).sum()

    clinical_status_coding_display_check = df[
        "clinicalStatus_coding_display"].isin(
        ["active", "recurrence", "relapse", "inactive",
         "remission", "resolved", "unknown"]).sum()

    # coding system
    code_coding_code_check = df["code_coding_code"].isin(["C18.0",
               "C18.1", "C18.2", "C18.3", "C18.4", "C18.5", "C18.6",
               "C18.7", "C18.8", "C18.9", "C19", "C20"]).sum()

    code_coding_display_check = df["code_coding_display"].isin([
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
        "Malignant neoplasm of rectum"]).sum()

    code_text_check = df["code_text"].isin([
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
    ]).sum()

    result = {
        "Records": ["Number of records", "recorded_date_check",
                    "onset_date_time_check", "clinical_status_coding_code_check",
                    "clinical_status_coding_display_check", "code_coding_code_check",
                    "code_coding_display_check", "code_text_check"],
        "Count": [count_of_rows, recorded_date_check,
                  onset_date_time_check, count_of_rows - clinical_status_coding_code_check,
                  clinical_status_coding_display_check, count_of_rows - code_coding_code_check,
                  count_of_rows - code_coding_display_check, code_text_check]
    }

    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    fig.update_layout(title="Conformance condition")
    return fig


def conformance_specimen(df):
    """
    Data quality check for conformance of Resource Specimen.

    :param df: Specimen data frame.
    :return:
        Graph of conformance.
    """
    count_of_rows = df.shape[0]

    # type text
    type_text_check = df["type_text"].isin(["Tumor", "Other", "Healthy colon tissue"]).sum()

    # collected Date Time
    df["collection_collectedDateTime"] = \
        pd.to_datetime(df["collection_collectedDateTime"], errors="coerce")
    collection_collectedDateTime_check = df.isnull()["collection_collectedDateTime"].sum()

    result = {
        "Records": ["Number of records", "type_text_check", "collection_collectedDateTime_check"],
        "Count": [count_of_rows, count_of_rows - type_text_check, collection_collectedDateTime_check]
    }

    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    fig.update_layout(title="Conformance specimen")
    return fig


def conformance_relational(df, server):
    """
    Data quality check for relational conformance of Resource.

    :param df: Data frame.
    :param server: FHIR server.
    :return:
        Graph of relational conformance.
    """
    count_of_rows = df.shape[0]
    count_of_invalid_references = 0

    for index in df.index:
        link = df['id'][index]
        subject_reference = df['subject_reference'][index]
        resource_type = df["resourceType"][index]
        try:
            server.request_json('http://localhost:8080/fhir/' + subject_reference)
        except:
            count_of_invalid_references += 1
    result = {
        "Records": ["Number of records", "Invalid references"],
        "Count": [count_of_rows, count_of_invalid_references]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    fig.update_layout(title="Conformance relational")
    return fig


def get_birthDay(pdf, subject_reference):
    """
    Helper function for conformance_computational.

    :param pdf: Patient data frame.
    :param subject_reference: Patient id.
    :return:
        Birthday of Patient.
    """
    subject_reference_split = subject_reference.split("/")
    patient_id = None
    if len(subject_reference_split) == 2:
        patient_id = subject_reference_split[1]
    birthDate = None
    if patient_id is not None:
        patient = pdf.loc[pdf['id'] == patient_id]
        if not patient.empty:
            patient = patient.iloc[0]
            birthDate = patient['birthDate']
    return birthDate


def conformance_computational(pdf, sdf, cdf):
    """
    Data quality check for computational conformance

    :param pdf: Patient data frame.
    :param sdf: Specimen data frame.
    :param cdf: Condition data frame.
    :return:
        Graph of computational conformance.
    """
    count_invalid_collection_collectedDateTime = 0
    for index in sdf.index:
        collection_collectedDateTime = sdf["collection_collectedDateTime"][index]
        subject_reference = sdf['subject_reference'][index]
        birthDay = get_birthDay(pdf, subject_reference)
        if birthDay is not None:
            if birthDay > collection_collectedDateTime:
                count_invalid_collection_collectedDateTime += 1

    onsetDateTime_count = 0
    recordedDate_count = 0
    for index in cdf.index:
        onsetDateTime = cdf["onsetDateTime"][index]
        recordedDate = cdf["recordedDate"][index]

        if index < len(sdf.index):
            subject_reference = sdf['subject_reference'][index]
            birthDay = get_birthDay(pdf, subject_reference)
        if birthDay is not None:
            if birthDay > onsetDateTime:
                onsetDateTime_count += 1
            if birthDay > recordedDate:
                recordedDate_count += 1

    result = {
        "Records": ["Number of records in specimens",
                    "Invalid collection_collectedDateTime",
                    "Number of records in conditions",
                    "Invalid onsetDateTime", "Invalid recordedDate"],
        "Count": [sdf.shape[0], count_invalid_collection_collectedDateTime,
                  cdf.shape[0], onsetDateTime_count, recordedDate_count]
    }
    dff = pd.DataFrame(result)
    fig = px.scatter(dff, x='Records', y='Count')
    fig.update_layout(title="Conformance computational")
    return fig


# original checks
# warnings
# 4
def age_at_primary_diagnosis(pdf, cdf):
    """
    Warning # 4
    Original warning type: "Suspiciously young patient"

    :param pdf: Patient data frame.
    :param cdf: Condition data frame.
    :return:
        Graph of result.
    """
    cdf_copy = cdf.copy()
    cdf_copy["patient_id"] = cdf_copy["subject_reference"].apply(lambda x: x.split("/")[1])
    pdf_copy = pdf.copy()
    pdf_copy["patient_id"] = pdf_copy["id"]
    merged_df = pd.merge(pdf_copy, cdf_copy, how="left", on="patient_id")
    count_of_rows = merged_df.shape[0]
    merged_df["age_at_diagnosis"] = pd.to_datetime(merged_df["onsetDateTime"]) - pd.to_datetime(merged_df["birthDate"])
    incorrect_df = merged_df.loc[merged_df['age_at_diagnosis'] < pd.Timedelta(days=15*365.25)]
    incorrect_count = incorrect_df.shape[0]

    incorrect_df.to_csv('reports/fhir/too_young_patients.csv', index=False)
    result = {
        "Records": ["Number of records", "too_young_patient"],
        "Count": [count_of_rows, incorrect_count]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    fig.update_layout(title="Warning # 4: Suspiciously young patient")
    return fig


# 8
def diagnosis_in_future(cdf):
    """
    Warning # 8
    Original warning type: "Initial diagnosis date is in the future"

    :param cdf: Condition data frame.
    :return:
        Graph of result.
    """
    now = datetime.now()
    cdf_copy = cdf.copy()
    count_of_rows = cdf_copy.shape[0]
    cdf_copy["recordedDate"] = pd.to_datetime(cdf_copy["recordedDate"])
    cdf_copy["diagnosis_in_future"] = cdf_copy["recordedDate"] > now
    incorrect_count = cdf_copy["diagnosis_in_future"].sum()

    filter_ddf = cdf_copy[cdf_copy['diagnosis_in_future'] == True]
    filter_ddf.to_csv('reports/fhir/diagnosis_in_future.csv', index=False)
    result = {
        "Records": ["Number of records", "diagnosis_in_future"],
        "Count": [count_of_rows, incorrect_count]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    fig.update_layout(title="Warning # 8: Initial diagnosis date is in the future")
    return fig


# reports
# 1+2
def missing_collection_collectedDateTime(pdf, sdf):
    """
    Report # 1 + 2

    :param pdf: Patient data frame.
    :param sdf: Specimen data frame.
    :return:
        Graphs of result.
    """
    sdf_copy = sdf.copy()
    sdf_copy["patient_id"] = sdf_copy["subject_reference"].apply(lambda x: x.split("/")[1])
    pdf_copy = pdf.copy()
    pdf_copy["patient_id"] = pdf_copy["id"]
    merged_ddf = pd.merge(pdf_copy, sdf_copy, how="left", on="patient_id")
    count_of_rows = merged_ddf.shape[0]

    merged_ddf["missing_collection_collectedDateTime"] = merged_ddf["collection_collectedDateTime"].isna()
    incorrect_count = merged_ddf["missing_collection_collectedDateTime"].sum()

    filter_ddf = merged_ddf[merged_ddf['missing_collection_collectedDateTime'] == True]
    filter_ddf.to_csv('reports/fhir/patients_without_collection_collectedDateTime.csv', index=False)

    filter_ddf = merged_ddf[merged_ddf['missing_collection_collectedDateTime'] == False]
    filter_ddf.to_csv('reports/fhir/patients_with_collection_collectedDateTime.csv', index=False)

    result = {
        "Records": ["Number of records",
                    "patients_without_missing_specimen_collection_collectedDateTime",
                    "patients_with_missing_specimen_collection_collectedDateTime"],
        "Count": [count_of_rows, count_of_rows - incorrect_count, incorrect_count]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    fig.update_layout(title="Report # 1 + 2")
    return fig


# 3
def patients_without_specimen_type_text(pdf, sdf):
    """
    Report # 3

    :param pdf: Person data frame.
    :param sdf: Specimen data frame.
    :return:
        Graphs of result.
    """
    sdf_copy = sdf.copy()
    sdf_copy["patient_id"] = sdf_copy["subject_reference"].apply(lambda x: x.split("/")[1])
    pdf_copy = pdf.copy()
    pdf_copy["patient_id"] = pdf_copy["id"]
    merged_ddf = pd.merge(pdf_copy, sdf_copy, how="left", on="patient_id")
    count_of_rows = merged_ddf.shape[0]

    merged_ddf["missing_specimen_type_text"] = merged_ddf["type_text"].isnull()
    incorrect_count_source = merged_ddf["missing_specimen_type_text"].sum()

    filter_ddf = merged_ddf[merged_ddf['missing_specimen_type_text'] == True]
    filter_ddf.to_csv('reports/fhir/patients_without_specimen_type_text.csv', index=False)

    result = {
        "Records": ["Number of records",
                    "patients_without_specimen_type_text"],
        "Count": [count_of_rows, incorrect_count_source]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    fig.update_layout(title="Report # 3: createPlotWithoutSampleID")
    return fig


# 6
def patients_without_condition_values(pdf, cdf):
    """
    Report # 6

    :param pdf: Person data frame.
    :param cdf: Condition Occurrence data frame.
    :return:
        Graphs of result.
    """

    cdf_copy = cdf.copy()
    cdf_copy["patient_id"] = cdf_copy["subject_reference"].apply(lambda x: x.split("/")[1])
    pdf_copy = pdf.copy()
    pdf_copy["patient_id"] = pdf_copy["id"]
    merged_ddf = pd.merge(pdf_copy, cdf_copy, how="left", on="patient_id")
    count_of_rows = merged_ddf.shape[0]

    # code_coding_system
    merged_ddf["missing_code_coding_system"] = merged_ddf["code_coding_system"].isnull()
    incorrect_count_system = merged_ddf["missing_code_coding_system"].sum()

    filter_ddf = merged_ddf[merged_ddf['missing_code_coding_system'] == True]
    filter_ddf.to_csv('reports/fhir/patients_without_code_coding_system.csv', index=False)

    # code_coding_code
    merged_ddf["missing_code_coding_code"] = merged_ddf["code_coding_code"].isnull()
    incorrect_count_code = merged_ddf["missing_code_coding_code"].sum()

    filter_ddf = merged_ddf[merged_ddf['missing_code_coding_code'] == True]
    filter_ddf.to_csv('reports/fhir/patients_without_ccode_coding_code.csv', index=False)

    # code_coding_display
    merged_ddf["missing_code_coding_display"] = merged_ddf["code_coding_display"].isnull()
    incorrect_count_display = merged_ddf["missing_code_coding_display"].sum()

    filter_ddf = merged_ddf[merged_ddf['missing_code_coding_display'] == True]
    filter_ddf.to_csv('reports/fhir/patients_without_code_coding_display.csv', index=False)

    # code_text
    merged_ddf["missing_code_text"] = merged_ddf["code_text"].isnull()
    incorrect_count_text = merged_ddf["missing_code_text"].sum()

    filter_ddf = merged_ddf[merged_ddf['missing_code_text'] == True]
    filter_ddf.to_csv('reports/fhir/patients_without_code_text.csv', index=False)

    # subject_reference
    merged_ddf["missing_subject_reference"] = merged_ddf["subject_reference"].isnull()
    incorrect_count_subject = merged_ddf["missing_subject_reference"].sum()

    filter_ddf = merged_ddf[merged_ddf['missing_subject_reference'] == True]
    filter_ddf.to_csv('reports/fhir/patients_without_subject_reference.csv', index=False)

    # clinicalStatus_coding_system
    merged_ddf["missing_clinicalStatus_coding_system"] = merged_ddf["clinicalStatus_coding_system"].isnull()
    incorrect_count_status_system = merged_ddf["missing_clinicalStatus_coding_system"].sum()

    filter_ddf = merged_ddf[merged_ddf['missing_clinicalStatus_coding_system'] == True]
    filter_ddf.to_csv('reports/fhir/patients_without_clinicalStatus_coding_system.csv', index=False)

    # clinicalStatus_coding_code
    merged_ddf["missing_clinicalStatus_coding_code"] = merged_ddf["clinicalStatus_coding_code"].isnull()
    incorrect_count_status_code = merged_ddf["missing_clinicalStatus_coding_code"].sum()

    filter_ddf = merged_ddf[merged_ddf['missing_clinicalStatus_coding_code'] == True]
    filter_ddf.to_csv('reports/fhir/patients_without_clinicalStatus_coding_code.csv', index=False)

    # clinicalStatus_coding_display
    merged_ddf["missing_clinicalStatus_coding_display"] = merged_ddf["clinicalStatus_coding_display"].isnull()
    incorrect_count_status_display = merged_ddf["missing_clinicalStatus_coding_display"].sum()

    filter_ddf = merged_ddf[merged_ddf['missing_clinicalStatus_coding_display'] == True]
    filter_ddf.to_csv('reports/fhir/patients_without_clinicalStatus_coding_display.csv', index=False)

    result = {
        "Records": ["Number of records",
                    "patients_without_code_coding_system",
                    "patient_without_code_coding_code",
                    "patients_without_code_coding_display",
                    "patients_without_code_text",
                    "patient_without_subject_reference",
                    "patients_without_clinicalStatus_coding_system",
                    "patient_without_clinicalStatus_coding_code",
                    "patients_without_clinicalStatus_coding_display"],
        "Count": [count_of_rows,
                  incorrect_count_system,
                  incorrect_count_code,
                  incorrect_count_display,
                  incorrect_count_text,
                  incorrect_count_subject,
                  incorrect_count_status_system,
                  incorrect_count_status_code,
                  incorrect_count_status_display]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    fig.update_layout(title="Report # 6: createPlotsWithoutHistoValues")
    return fig
