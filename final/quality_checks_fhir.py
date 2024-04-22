import pandas as pd
import plotly.express as px


def create_patient_data_frame(ids, server):
    dicts = []
    for id in ids:
        dict = server.request_json('http://localhost:8080/fhir/Patient/' + id)
        meta = dict.pop("meta")
        dict["meta_versionId"] = meta["versionId"]
        dict["meta_lastUpdated"] = meta["lastUpdated"]
        dicts.append(dict)
    return pd.DataFrame(dicts)


def create_specimen_data_frame(ids, server):
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


def create_condition_data_frame(ids, server):
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


def create_df(patients_id, specimens_id, conditions_id, server):
    patients_df = create_patient_data_frame(patients_id, server)
    patients_df = patients_df.drop(columns=["resourceType", "id", "meta_versionId", "meta_lastUpdated"])
    specimen_df = create_specimen_data_frame(specimens_id, server)
    specimen_df = specimen_df.drop(columns=["resourceType", "id", "meta_versionId", "meta_lastUpdated"])
    condition_df = create_condition_data_frame(conditions_id, server)
    condition_df = condition_df.drop(columns=["resourceType", "id", "meta_versionId", "meta_lastUpdated"])

    #return  wf1.completeness(patients_df)
    return patients_df, specimen_df, condition_df



def completeness(df):
    missing_values = pd.isnull(df).sum()
    fig = px.scatter(missing_values)
    fig.update_layout(xaxis_title='count of missing values', yaxis_title='attribute', title="Missing values",
                      showlegend=False)
    return fig


def uniqueness(df):
    count_of_rows = df.shape[0]
    count_of_duplicates = df.duplicated().sum()
    result = {
        "Duplicates": ["Unique rows", "Duplicated"],
        "Count": [count_of_rows - count_of_duplicates, count_of_duplicates]
    }
    dff = pd.DataFrame(result)
    fig = px.pie(dff, values='Count', names='Duplicates', title='Duplicated values')
    return fig


def conformance_patient(df):
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
    # TODO nastavit těm all records jinou barvu
    return fig



def conformance_condition(df):
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
    # TODO nastavit těm all records jinou barvu
    return fig


def conformance_specimen(df):
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
    # TODO je to spíš attributes než records
    # TODO nastavit těm all records jinou barvu
    return fig


def conformance_relational(df, server):
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
    return fig

    # TODO tabulka invalid records


def get_birthDay(pdf, subject_reference):
    subject_reference_split = subject_reference.split()
    patient_id = None
    if len(subject_reference_split) == 2:
        patient_id = subject_reference_split[1]
    birthDay = None
    if patient_id is not None:
        patient = pdf.loc[patient_id]
        birthDay = patient[patient]
    return birthDay


def conformance_computational(pdf, sdf, cdf):
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
    fig.write_image("con_comp_fhir.svg")
    return fig


# TODO original checks
# 4
# age_at_primary_diagnosis < 15

# 8
# !is.na(diag_date) & diag_date > Sys.Date()
